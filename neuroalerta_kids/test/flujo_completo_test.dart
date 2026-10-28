import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:neuroalerta_kids/ui/app.dart';

import 'ayudas.dart';

Future<void> responderTodo(WidgetTester tester, String opcion) async {
  while (find.byKey(const Key('texto_pregunta')).evaluate().isNotEmpty) {
    await tester.tap(find.byKey(Key('opcion_$opcion')));
    await tester.pumpAndSettle();
  }
}

Future<void> atras(WidgetTester tester) async {
  await tester.tap(find.byType(BackButton));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'flujo completo: consentimiento, alta, cuestionario, resultado, foto y exportación',
    (tester) async {
      final e = await tester.runAsync(Entorno.crear) as Entorno;
      addTearDown(() => tester.runAsync(e.cerrar));

      await tester.pumpWidget(NeuroAlertaApp(servicios: e.servicios));
      await tester.pumpAndSettle();

      // Bienvenida con aviso.
      expect(find.text('Comenzar'), findsOneWidget);
      expect(find.byKey(const Key('aviso_orientacion')), findsOneWidget);
      await tester.tap(find.text('Comenzar'));
      await tester.pumpAndSettle();

      // Consentimiento: no se avanza sin aceptar y no se guarda nada.
      final aceptar = find.widgetWithText(
        FilledButton,
        'Acepto y deseo continuar',
      );
      expect(tester.widget<FilledButton>(aceptar).onPressed, isNull);
      expect(await e.base.select(e.base.consentimientos).get(), isEmpty);
      await tester.tap(find.byKey(const Key('casilla_consentimiento')));
      await tester.pumpAndSettle();
      await tester.tap(aceptar);
      await tester.pumpAndSettle();
      final c = (await e.repo.consentimientoVigente('1.0'))!;
      expect(c.aceptadoEn, DateTime(2026, 6, 10));
      expect(find.text('Mis niños y niñas'), findsOneWidget);

      // Alta.
      await tester.tap(find.byKey(const Key('agregar_nino')));
      await tester.pumpAndSettle();
      await tester.enterText(find.byKey(const Key('campo_codigo')), 'Peque 1');
      await tester.tap(find.byKey(const Key('elegir_fecha')));
      await tester.pumpAndSettle();
      await tester.tap(find.text('ACEPTAR'));
      await tester.pumpAndSettle();
      expect(find.text('Grupo de edad: 3 a 6 años'), findsOneWidget);
      await tester.tap(find.text('Guardar'));
      await tester.pumpAndSettle();
      expect(find.text('Peque 1'), findsOneWidget);

      // Cuestionario.
      await tester.tap(find.text('Peque 1'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Responder el cuestionario'));
      await tester.pumpAndSettle();
      expect(find.text('Antes de empezar'), findsOneWidget);
      await tester.tap(find.text('Continuar'));
      await tester.pumpAndSettle();
      await responderTodo(tester, 'casi_siempre');

      // Resultado.
      expect(
        find.text('Conviene consultar pronto con un especialista'),
        findsOneWidget,
      );
      expect(
        find.text(
          'Esta orientación no reemplaza la evaluación de un profesional de salud.',
        ),
        findsOneWidget,
      );
      expect(find.textContaining('0.1.0-provisional'), findsOneWidget);
      await tester.tap(find.text('Volver al inicio'));
      await tester.pumpAndSettle();

      // Historial.
      await tester.tap(find.text('Peque 1'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Historial'));
      await tester.pumpAndSettle();
      expect(
        find.textContaining('Protocolo 0.1.0-provisional'),
        findsOneWidget,
      );
      await atras(tester);

      // Foto: se entrega al almacén privado (que copia y borra el temporal).
      e.selector.ruta = '/cache/camara_temporal.jpg';
      await tester.tap(find.text('Fotos de conductas'));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('agregar_foto')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('foto_camara')));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const Key('nota_foto')),
        'Aletea al emocionarse',
      );
      await tester.tap(find.byKey(const Key('guardar_foto')));
      await tester.pumpAndSettle();
      expect(e.selector.ultimaCamara, isTrue);
      expect(find.text('Aletea al emocionarse'), findsOneWidget);
      final fotos = await e.repo.fotosDe(1);
      expect(fotos, hasLength(1));
      expect(fotos.single.ruta, startsWith('/privado/fotos_privadas/'));
      expect(e.almacen.guardadas, ['/cache/camara_temporal.jpg']);
      await atras(tester);
      await atras(tester);

      // Exportación.
      await tester.tap(find.byType(PopupMenuButton<String>));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Exportación (uso del equipo)').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Generar y compartir CSV'));
      await tester.pumpAndSettle();
      expect(e.compartidos, hasLength(1));
      final csv = e.csvEscritos[e.compartidos.single]!;
      final lineas = csv.trim().split(RegExp(r'\r?\n'));
      expect(
        lineas.first,
        startsWith(
          'codigo_interno,tramo_edad,fecha_sesion,version_protocolo,estado_protocolo,item',
        ),
      );
      expect(
        lineas.length - 1,
        e.servicios.protocolos.values
            .firstWhere((p) => p.tramo.id == '3_6')
            .items
            .length,
      );
      expect(
        lineas[1],
        startsWith(
          'ABC123-N0001,3_6,2026-06-10,0.1.0-provisional,provisional,',
        ),
      );
      expect(csv.contains('Peque'), isFalse);
      expect(csv.contains('2022'), isFalse, reason: 'sin fecha de nacimiento');
      expect(csv.contains('.jpg'), isFalse, reason: 'sin fotos');
      expect(csv.contains('Aletea'), isFalse, reason: 'sin notas de fotos');
      expect(e.compartidos.single, contains('provisional'));
    },
  );
}
