import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:neuroalerta_kids/domain/motor_puntuacion.dart';
import 'package:neuroalerta_kids/domain/protocolo.dart';
import 'package:neuroalerta_kids/domain/tramo.dart';

Protocolo cargar(String archivo) =>
    Protocolo.desdeJson(File('assets/protocolos/$archivo').readAsStringSync());

Map<String, Opcion> todas(Protocolo p, int edad, Opcion o) => {
  for (final i in p.itemsPara(edad)) i.id: o,
};

void main() {
  const motor = MotorPuntuacion();
  final p036 = cargar('protocolo_0_36.json');
  final p36 = cargar('protocolo_3_6.json');
  final p712 = cargar('protocolo_7_12.json');

  group('tramos y edad', () {
    test('límites de tramo', () {
      expect(Tramo.desdeEdadMeses(0), Tramo.meses0a36);
      expect(Tramo.desdeEdadMeses(36), Tramo.meses0a36);
      expect(Tramo.desdeEdadMeses(37), Tramo.anios3a6);
      expect(Tramo.desdeEdadMeses(83), Tramo.anios3a6);
      expect(Tramo.desdeEdadMeses(84), Tramo.anios7a12);
      expect(Tramo.desdeEdadMeses(155), Tramo.anios7a12);
      expect(Tramo.desdeEdadMeses(156), isNull);
      expect(Tramo.desdeEdadMeses(-1), isNull);
    });

    test('edad en meses completos', () {
      expect(edadEnMeses(DateTime(2024, 1, 15), DateTime(2026, 1, 14)), 23);
      expect(edadEnMeses(DateTime(2024, 1, 15), DateTime(2026, 1, 15)), 24);
      expect(edadEnMeses(DateTime(2020, 5, 31), DateTime(2026, 5, 30)), 71);
    });
  });

  group('protocolos', () {
    for (final p in [p036, p36, p712]) {
      test('${p.tramo.id}: bien formado y provisional', () {
        expect(p.esProvisional, isTrue);
        expect(p.version, contains('provisional'));
        final ids = p.items.map((i) => i.id).toList();
        expect(ids.toSet().length, ids.length);
        final areas = p.areas.map((a) => a.id).toSet();
        expect(p.items.every((i) => areas.contains(i.areaId)), isTrue);
        expect(
          p.items.every(
            (i) =>
                i.puntos[Opcion.casiSiempre] == 2 &&
                i.puntos[Opcion.aVeces] == 1 &&
                i.puntos[Opcion.casiNunca] == 0,
          ),
          isTrue,
        );
        expect(p.items.any((i) => i.puntos.containsKey(Opcion.noSe)), isFalse);
        expect(p.focosRojos.any((f) => f.grave), isTrue);
      });
    }

    test('0 a 36 meses no incluye áreas de atención ni hiperactividad', () {
      expect(p036.areas.map((a) => a.id), [
        'comunicacion',
        'interaccion',
        'conductas',
      ]);
    });
  });

  group('motor', () {
    test('todo "casi nunca": sin señales', () {
      final r = motor.evaluar(
        protocolo: p36,
        edadMeses: 50,
        respuestas: todas(p36, 50, Opcion.casiNunca),
      );
      expect(r.nivel, NivelOrientacion.sinSenales);
      expect(r.puntosTotal, 0);
      expect(r.maximoTotal, p36.items.length * 2);
    });

    test('todo "casi siempre": consultar pronto', () {
      for (final (p, edad) in [(p036, 30), (p36, 50), (p712, 100)]) {
        final r = motor.evaluar(
          protocolo: p,
          edadMeses: edad,
          respuestas: todas(p, edad, Opcion.casiSiempre),
        );
        expect(r.nivel, NivelOrientacion.consultarPronto, reason: p.tramo.id);
        expect(r.proporcionTotal, 1.0);
      }
    });

    test(
      'todo "a veces" (50 %): consultar pronto; un tercio: comentar en control',
      () {
        final aVeces = motor.evaluar(
          protocolo: p36,
          edadMeses: 50,
          respuestas: todas(p36, 50, Opcion.aVeces),
        );
        expect(aVeces.nivel, NivelOrientacion.consultarPronto);

        // 19 ítems en 3-6: 4 con "casi siempre" = 8/38 = 21 % total pero 4/4 en una sola área.
        final respuestas = todas(p36, 50, Opcion.casiNunca);
        for (final id in ['c01', 'c02', 'c03']) {
          respuestas[id] = Opcion.casiSiempre;
        }
        final r = motor.evaluar(
          protocolo: p36,
          edadMeses: 50,
          respuestas: respuestas,
        );
        expect(r.areas['comunicacion']!.proporcion, 0.75);
        expect(r.nivel, NivelOrientacion.consultarPronto);

        respuestas['c03'] = Opcion.casiNunca;
        final r2 = motor.evaluar(
          protocolo: p36,
          edadMeses: 50,
          respuestas: respuestas,
        );
        expect(r2.areas['comunicacion']!.proporcion, 0.5);
        expect(r2.nivel, NivelOrientacion.comentarControl);
      },
    );

    test('"No sé" no suma, no entra en el máximo y se cuenta aparte', () {
      final resp = todas(p36, 50, Opcion.casiNunca);
      resp['c01'] = Opcion.noSe;
      resp['c02'] = Opcion.noSe;
      final r = motor.evaluar(protocolo: p36, edadMeses: 50, respuestas: resp);
      expect(r.noSe, 2);
      expect(r.areas['comunicacion']!.noSe, 2);
      expect(r.areas['comunicacion']!.respondidas, 2);
      expect(r.maximoTotal, (p36.items.length - 2) * 2);
      expect(r.respondidas, p36.items.length - 2);
    });

    test('muchas respuestas "No sé" activan la advertencia', () {
      final resp = todas(p36, 50, Opcion.noSe);
      final r = motor.evaluar(protocolo: p36, edadMeses: 50, respuestas: resp);
      expect(r.muchosNoSe, isTrue);
      expect(r.pocasRespuestas, isTrue);
      expect(r.nivel, NivelOrientacion.sinSenales);
    });

    test('foco rojo grave: consultar pronto sin esperar el puntaje', () {
      final r = motor.evaluar(
        protocolo: p036,
        edadMeses: 20,
        respuestas: const {},
        focosMarcados: {'f01'},
      );
      expect(r.focoGrave, isTrue);
      expect(r.nivel, NivelOrientacion.consultarPronto);
      expect(r.focosRojos, ['f01']);
      expect(r.pocasRespuestas, isTrue);
    });

    test(
      'un foco no grave sube a comentar en control; dos, a consultar pronto',
      () {
        final uno = motor.evaluar(
          protocolo: p36,
          edadMeses: 50,
          respuestas: todas(p36, 50, Opcion.casiNunca),
          focosMarcados: {'f02'},
        );
        expect(uno.nivel, NivelOrientacion.comentarControl);
        expect(uno.focoGrave, isFalse);
        final dos = motor.evaluar(
          protocolo: p36,
          edadMeses: 50,
          respuestas: todas(p36, 50, Opcion.casiNunca),
          focosMarcados: {'f02', 'f03'},
        );
        expect(dos.nivel, NivelOrientacion.consultarPronto);
      },
    );

    test('ítems y focos se filtran por edad', () {
      expect(p036.itemsPara(8).length, lessThan(p036.itemsPara(30).length));
      expect(p036.focosPara(10).map((f) => f.id), ['f01']);
      expect(p036.focosPara(30).map((f) => f.id), ['f01', 'f02', 'f03', 'f04']);
      final r = motor.evaluar(
        protocolo: p036,
        edadMeses: 10,
        respuestas: const {},
        focosMarcados: {'f03'},
      );
      expect(r.focosRojos, isEmpty, reason: 'f03 no aplica a 10 meses');
    });

    test('pocas respuestas: el puntaje solo no dispara el nivel', () {
      final r = motor.evaluar(
        protocolo: p36,
        edadMeses: 50,
        respuestas: {
          'c01': Opcion.casiSiempre,
          'c02': Opcion.casiSiempre,
          'c03': Opcion.casiSiempre,
        },
      );
      expect(r.pocasRespuestas, isTrue);
      expect(r.nivel, NivelOrientacion.sinSenales);
    });

    test('es determinista y registra la versión del protocolo', () {
      final resp = todas(p712, 100, Opcion.aVeces)
        ..['a01'] = Opcion.casiSiempre;
      final a = motor.evaluar(
        protocolo: p712,
        edadMeses: 100,
        respuestas: resp,
        focosMarcados: {'f03'},
      );
      final b = motor.evaluar(
        protocolo: p712,
        edadMeses: 100,
        respuestas: Map.of(resp),
        focosMarcados: {'f03'},
      );
      expect(a.nivel, b.nivel);
      expect(a.puntosTotal, b.puntosTotal);
      expect(a.versionProtocolo, p712.version);
      expect(a.estadoProtocolo, 'provisional');
    });
  });

  group('lenguaje para las familias', () {
    final prohibidas = RegExp(
      r'diagn[oó]stic|autis|\bTEA\b|\bTDAH\b',
      caseSensitive: false,
    );

    test('protocolos y textos no usan palabras de conclusión clínica', () {
      final textos = <String>[];
      for (final p in [p036, p36, p712]) {
        textos.addAll(p.items.map((i) => i.texto));
        textos.addAll(p.focosRojos.map((f) => f.texto));
        textos.addAll(p.areas.map((a) => a.nombre));
      }
      for (final archivo in ['niveles.json', 'consentimiento.json']) {
        textos.add(File('assets/textos/$archivo').readAsStringSync());
      }
      for (final t in textos) {
        expect(prohibidas.hasMatch(t), isFalse, reason: t);
      }
    });

    test('el código de la interfaz tampoco las contiene', () {
      for (final f
          in Directory('lib')
              .listSync(recursive: true)
              .whereType<File>()
              .where((f) => f.path.endsWith('.dart'))) {
        if (f.path.endsWith('.g.dart')) continue;
        expect(
          prohibidas.hasMatch(f.readAsStringSync()),
          isFalse,
          reason: f.path,
        );
      }
    });

    test('niveles.json trae el aviso obligatorio y los tres niveles', () {
      final m = jsonDecode(
        File('assets/textos/niveles.json').readAsStringSync(),
      ) as Map<String, dynamic>;
      expect(
        m['aviso'],
        'Esta orientación no reemplaza la evaluación de un profesional de salud.',
      );
      for (final n in NivelOrientacion.values) {
        expect((m['niveles'] as Map).containsKey(n.id), isTrue);
      }
    });
  });
}
