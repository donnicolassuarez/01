import 'dart:io';

import 'package:drift/drift.dart' show driftRuntimeOptions;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:neuroalerta_kids/data/abrir_base.dart';
import 'package:neuroalerta_kids/data/base_datos.dart';
import 'package:neuroalerta_kids/data/repositorio.dart';
import 'package:neuroalerta_kids/domain/motor_puntuacion.dart';
import 'package:neuroalerta_kids/domain/protocolo.dart';

void main() {
  driftRuntimeOptions.dontWarnAboutMultipleDatabases = true;
  late BaseDatos db;
  late Repositorio repo;
  late Protocolo p36;
  final hoy = DateTime(2026, 6, 10);

  setUp(() {
    db = BaseDatos(NativeDatabase.memory());
    repo = Repositorio(db, ahora: () => hoy);
    p36 = Protocolo.desdeJson(
      File('assets/protocolos/protocolo_3_6.json').readAsStringSync(),
    );
  });
  tearDown(() => db.close());

  group('consentimiento', () {
    test('sin consentimiento no se guarda ningún dato', () async {
      await expectLater(
        repo.crearNino(codigo: 'luz', fechaNacimiento: DateTime(2022, 1, 1)),
        throwsA(isA<ConsentimientoRequerido>()),
      );
      expect(await repo.listarNinos(), isEmpty);
    });

    test('registra versión y fecha de aceptación', () async {
      expect(await repo.consentimientoVigente('1.0'), isNull);
      await repo.registrarConsentimiento('1.0');
      final c = await repo.consentimientoVigente('1.0');
      expect(c, isNotNull);
      expect(c!.aceptadoEn, hoy);
      expect(await repo.consentimientoVigente('2.0'), isNull);
    });

    test('las fotos tampoco se guardan sin consentimiento', () async {
      await expectLater(
        repo.agregarFoto(ninoId: 1, ruta: '/x.jpg', fecha: hoy),
        throwsA(isA<ConsentimientoRequerido>()),
      );
    });
  });

  group('niños', () {
    setUp(() => repo.registrarConsentimiento('1.0'));

    test('calcula el tramo según la edad', () async {
      final a = await repo.crearNino(
        codigo: 'A',
        fechaNacimiento: DateTime(2025, 6, 10),
      );
      final b = await repo.crearNino(
        codigo: 'B',
        fechaNacimiento: DateTime(2022, 1, 1),
      );
      final c = await repo.crearNino(
        codigo: 'C',
        fechaNacimiento: DateTime(2017, 3, 1),
      );
      expect([a.tramo, b.tramo, c.tramo], ['0_36', '3_6', '7_12']);
    });

    test('rechaza edades fuera de rango', () async {
      await expectLater(
        repo.crearNino(codigo: 'M', fechaNacimiento: DateTime(2010, 1, 1)),
        throwsA(isA<EdadFueraDeRango>()),
      );
      await expectLater(
        repo.crearNino(codigo: 'F', fechaNacimiento: DateTime(2027, 1, 1)),
        throwsA(isA<EdadFueraDeRango>()),
      );
    });
  });

  group('sesión completa', () {
    late Nino nino;
    setUp(() async {
      await repo.registrarConsentimiento('1.0');
      nino = await repo.crearNino(
        codigo: 'Luz',
        fechaNacimiento: DateTime(2022, 1, 1),
      );
    });

    test(
      'guarda avance, retoma la sesión y cierra con resultado versionado',
      () async {
        final s = await repo.iniciarOReanudarSesion(nino: nino, protocolo: p36);
        expect(s.versionProtocolo, p36.version);
        await repo.guardarRespuesta(
          sesionId: s.id,
          item: p36.items[0],
          opcion: Opcion.casiSiempre,
        );
        await repo.guardarRespuesta(
          sesionId: s.id,
          item: p36.items[1],
          opcion: Opcion.noSe,
        );
        await repo.guardarRespuesta(
          sesionId: s.id,
          item: p36.items[0],
          opcion: Opcion.aVeces,
        );
        await repo.guardarFocos(s.id, {'f02'});

        final otra = await repo.iniciarOReanudarSesion(
          nino: nino,
          protocolo: p36,
        );
        expect(otra.id, s.id, reason: 'retoma la sesión abierta');
        final resp = await repo.respuestasDe(s.id);
        expect(resp, {
          p36.items[0].id: Opcion.aVeces,
          p36.items[1].id: Opcion.noSe,
        });
        expect(repo.focosDe(await repo.sesion(s.id)), {'f02'});

        final filas = await db.select(db.respuestas).get();
        expect(filas.firstWhere((r) => r.itemId == p36.items[0].id).puntos, 1);
        expect(
          filas.firstWhere((r) => r.itemId == p36.items[1].id).puntos,
          isNull,
        );

        final r = const MotorPuntuacion().evaluar(
          protocolo: p36,
          edadMeses: s.edadMeses,
          respuestas: resp,
          focosMarcados: repo.focosDe(s),
        );
        final guardado = await repo.cerrarSesion(s.id, r);
        expect(guardado.versionProtocolo, p36.version);
        expect(guardado.estadoProtocolo, 'provisional');
        expect(guardado.nivel, r.nivel.id);

        final h = await repo.historial(nino.id);
        expect(h, hasLength(1));
        expect(h.single.resultado!.sesionId, s.id);
        expect(h.single.sesion.cerradaEn, hoy);

        final nueva = await repo.iniciarOReanudarSesion(
          nino: nino,
          protocolo: p36,
        );
        expect(nueva.id, isNot(s.id), reason: 'tras cerrar se abre una nueva');
      },
    );

    test('fotos: agregar, listar y eliminar', () async {
      final f = await repo.agregarFoto(
        ninoId: nino.id,
        ruta: '/privado/a.jpg',
        fecha: hoy,
        nota: ' juego ',
      );
      expect(f.nota, 'juego');
      expect(await repo.fotosDe(nino.id), hasLength(1));
      await repo.eliminarFoto(f.id);
      expect(await repo.fotosDe(nino.id), isEmpty);
    });
  });

  group('cifrado en disco', () {
    late Directory tmp;
    setUp(() => tmp = Directory.systemTemp.createTempSync('neuro_test'));
    tearDown(() => tmp.deleteSync(recursive: true));

    test('el archivo no es SQLite en claro y exige la clave', () async {
      final archivo = File('${tmp.path}/prueba.db');
      final cifrada = BaseDatos(
        NativeDatabase(
          archivo,
          setup: (d) => configurarCifrado(d, 'clave-de-prueba-123'),
        ),
      );
      final r = Repositorio(cifrada, ahora: () => hoy);
      await r.registrarConsentimiento('1.0');
      await r.crearNino(
        codigo: 'Secreto',
        fechaNacimiento: DateTime(2022, 1, 1),
      );
      await cifrada.close();

      final bytes = archivo.readAsBytesSync();
      expect(String.fromCharCodes(bytes.take(15)), isNot('SQLite format 3'));
      expect(String.fromCharCodes(bytes).contains('Secreto'), isFalse);

      final sinClave = BaseDatos(NativeDatabase(archivo));
      await expectLater(
        sinClave.select(sinClave.ninos).get(),
        throwsA(anything),
      );
      await sinClave.close();

      final conClave = BaseDatos(
        NativeDatabase(
          archivo,
          setup: (d) => configurarCifrado(d, 'clave-de-prueba-123'),
        ),
      );
      expect(
        (await conClave.select(conClave.ninos).get()).single.codigo,
        'Secreto',
      );
      await conClave.close();
    });
  });
}
