import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:neuroalerta_kids/domain/protocolo.dart';
import 'package:neuroalerta_kids/ui/app.dart';

import 'ayudas.dart';

const aviso =
    'Esta orientación no reemplaza la evaluación de un profesional de salud.';
final prohibidas = RegExp(
  r'diagn[oó]stic|autis|\bTEA\b|\bTDAH\b',
  caseSensitive: false,
);

Future<void> atras(WidgetTester tester) async {
  await tester.tap(find.byType(BackButton));
  await tester.pumpAndSettle();
}

Future<Entorno> entornoConNino(
  WidgetTester tester, {
  DateTime? nacimiento,
}) async {
  final e = (await tester.runAsync(Entorno.crear))!;
  await e.repo.registrarConsentimiento('1.0');
  await e.repo.crearNino(
    codigo: 'Ana',
    fechaNacimiento: nacimiento ?? DateTime(2022, 1, 1),
  );
  addTearDown(e.cerrar);
  return e;
}

Future<void> abrirCuestionario(WidgetTester tester, Entorno e) async {
  await tester.pumpWidget(NeuroAlertaApp(servicios: e.servicios));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Ana'));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Responder el cuestionario'));
  await tester.pumpAndSettle();
}

Future<void> responder(WidgetTester tester, String opcion, [int? veces]) async {
  var n = 0;
  while (find.byKey(const Key('texto_pregunta')).evaluate().isNotEmpty &&
      (veces == null || n < veces)) {
    await tester.tap(find.byKey(Key('opcion_$opcion')));
    await tester.pumpAndSettle();
    n++;
  }
}

void main() {
  testWidgets(
    'foco rojo grave: muestra la recomendación sin esperar el puntaje',
    (tester) async {
      final e = await entornoConNino(tester);
      await abrirCuestionario(tester, e);

      await tester.tap(find.byKey(const Key('foco_f01')));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Continuar'));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('aviso_foco_grave')), findsOneWidget);
      expect(find.text('Conviene consultar pronto'), findsOneWidget);
      await tester.tap(find.text('Ver la orientación'));
      await tester.pumpAndSettle();

      // Sin responder ninguna pregunta: nivel máximo, aviso y foco listado.
      expect(
        find.text('Conviene consultar pronto con un especialista'),
        findsOneWidget,
      );
      expect(find.text(aviso), findsOneWidget);
      expect(
        find.textContaining('Perdió palabras', skipOffstage: false),
        findsOneWidget,
      );
      expect(
        find.textContaining('pocas preguntas', skipOffstage: false),
        findsOneWidget,
      );
      final r = await e.repo.resultadoDe(1);
      expect(r!.nivel, 'consultar_pronto');
      expect(r.focosRojos, 'f01');
      expect(r.versionProtocolo, '0.1.0-provisional');
    },
  );

  testWidgets('foco grave: se puede seguir con las preguntas', (tester) async {
    final e = await entornoConNino(tester);
    await abrirCuestionario(tester, e);
    await tester.tap(find.byKey(const Key('foco_f01')));
    await tester.tap(find.text('Continuar'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Seguir con las preguntas'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('texto_pregunta')), findsOneWidget);
    expect(find.text('Pregunta 1 de 19'), findsOneWidget);
  });

  testWidgets('guarda el avance, se puede volver atrás y retomar', (
    tester,
  ) async {
    final e = await entornoConNino(tester);
    await abrirCuestionario(tester, e);
    await tester.tap(find.text('Continuar'));
    await tester.pumpAndSettle();

    await responder(tester, 'a_veces', 3);
    expect(find.text('Pregunta 4 de 19'), findsOneWidget);

    await tester.tap(find.byKey(const Key('anterior')));
    await tester.pumpAndSettle();
    expect(find.text('Pregunta 3 de 19'), findsOneWidget);
    await tester.tap(find.byKey(const Key('opcion_no_se')));
    await tester.pumpAndSettle();
    expect(find.text('Pregunta 4 de 19'), findsOneWidget);

    // Sale del cuestionario y vuelve: retoma en la primera sin responder.
    await atras(tester);
    await tester.tap(find.text('Responder el cuestionario'));
    await tester.pumpAndSettle();
    expect(find.text('Pregunta 4 de 19'), findsOneWidget);
    final guardadas = await e.repo.respuestasDe(1);
    expect(guardadas.length, 3);
    expect(guardadas.values.last, Opcion.noSe);
  });

  for (final caso in [
    ('casi_nunca', 'Sin señales para consultar ahora'),
    ('casi_siempre', 'Conviene consultar pronto con un especialista'),
  ]) {
    testWidgets('resultado ${caso.$1}: título, aviso y lenguaje suave', (
      tester,
    ) async {
      final e = await entornoConNino(tester);
      await abrirCuestionario(tester, e);
      await tester.tap(find.text('Continuar'));
      await tester.pumpAndSettle();
      await responder(tester, caso.$1);

      expect(find.text(caso.$2), findsOneWidget);
      expect(find.text(aviso), findsOneWidget);
      for (final t in tester.widgetList<Text>(find.byType(Text))) {
        expect(prohibidas.hasMatch(t.data ?? ''), isFalse, reason: t.data);
      }
    });
  }

  testWidgets(
    'nivel intermedio: comentar con el pediatra en el próximo control',
    (tester) async {
      final e = await entornoConNino(tester);
      await abrirCuestionario(tester, e);
      await tester.tap(find.text('Continuar'));
      await tester.pumpAndSettle();
      // 10 de 19 preguntas con "a veces" (10 de 38 puntos, ~26 %) sin llegar a la regla de área más alta.
      await responder(tester, 'a_veces', 10);
      await responder(tester, 'casi_nunca');
      expect(
        find.text('Conviene comentar con el pediatra en el próximo control'),
        findsOneWidget,
      );
      expect(find.text(aviso), findsOneWidget);
    },
  );

  testWidgets('alta: no acepta un nombre completo ni una edad fuera de rango', (
    tester,
  ) async {
    final e = (await tester.runAsync(Entorno.crear))!;
    await e.repo.registrarConsentimiento('1.0');
    addTearDown(e.cerrar);
    await tester.pumpWidget(NeuroAlertaApp(servicios: e.servicios));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('agregar_nino')));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('campo_codigo')),
      'Juan Carlos Pérez Rojas',
    );
    await tester.tap(find.text('Guardar'));
    await tester.pumpAndSettle();
    expect(find.textContaining('no el nombre completo'), findsOneWidget);
    expect(find.text('Elija la fecha de nacimiento'), findsOneWidget);
    expect(await e.repo.listarNinos(), isEmpty);
  });

  testWidgets('fotos: ver, confirmar y eliminar', (tester) async {
    final e = await entornoConNino(tester);
    await e.repo.agregarFoto(
      ninoId: 1,
      ruta: '/privado/fotos_privadas/f_1.jpg',
      fecha: DateTime(2026, 6, 1),
      nota: 'Se balancea',
    );
    await tester.pumpWidget(NeuroAlertaApp(servicios: e.servicios));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Ana'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Fotos de conductas'));
    await tester.pumpAndSettle();
    expect(find.text('Se balancea'), findsOneWidget);

    await tester.tap(find.text('Se balancea'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('eliminar_foto')));
    await tester.pumpAndSettle();
    expect(find.text('¿Eliminar esta foto?'), findsOneWidget);
    await tester.tap(find.byKey(const Key('confirmar_eliminar')));
    await tester.pumpAndSettle();

    expect(e.almacen.eliminadas, ['/privado/fotos_privadas/f_1.jpg']);
    expect(await e.repo.fotosDe(1), isEmpty);
    expect(find.text('Todavía no hay fotos.'), findsOneWidget);
  });

  testWidgets('niño de 12 meses: no ve preguntas ni focos de edades mayores', (
    tester,
  ) async {
    final e = await entornoConNino(tester, nacimiento: DateTime(2025, 6, 10));
    await abrirCuestionario(tester, e);
    expect(find.byKey(const Key('foco_f01')), findsOneWidget);
    expect(find.byKey(const Key('foco_f02')), findsOneWidget);
    expect(find.byKey(const Key('foco_f03')), findsNothing);
    expect(find.byKey(const Key('foco_f04')), findsNothing);
  });
}
