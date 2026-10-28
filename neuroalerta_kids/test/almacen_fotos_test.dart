import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:neuroalerta_kids/data/repositorio.dart';
import 'package:neuroalerta_kids/servicios/exportador_csv.dart';
import 'package:neuroalerta_kids/servicios/fotos_servicio.dart';

void main() {
  late Directory tmp;
  setUp(() => tmp = Directory.systemTemp.createTempSync('neuro_fotos'));
  tearDown(() => tmp.deleteSync(recursive: true));

  group('almacén privado de fotos', () {
    test('copia a la carpeta privada, marca la carpeta .nomedia y borra el temporal', () async {
      final almacen = AlmacenFotosArchivos(
        carpeta: Directory('${tmp.path}/privado'),
      );
      final origen = File('${tmp.path}/camara.jpg')
        ..writeAsBytesSync([1, 2, 3]);
      final ruta = await almacen.guardar(origen.path);

      expect(ruta, startsWith('${tmp.path}/privado/fotos_privadas/'));
      expect(File(ruta).readAsBytesSync(), [1, 2, 3]);
      expect(origen.existsSync(), isFalse);
      expect(
        File('${tmp.path}/privado/fotos_privadas/.nomedia').existsSync(),
        isTrue,
      );
    });

    test('eliminar borra el archivo y tolera uno que ya no existe', () async {
      final almacen = AlmacenFotosArchivos(
        carpeta: Directory('${tmp.path}/privado'),
      );
      final origen = File('${tmp.path}/a.png')..writeAsBytesSync([9]);
      final ruta = await almacen.guardar(origen.path);
      await almacen.eliminar(ruta);
      expect(File(ruta).existsSync(), isFalse);
      await almacen.eliminar(ruta);
    });
  });

  group('CSV', () {
    final fila = FilaExportacion(
      ninoId: 7,
      tramo: '3_6',
      fechaSesion: DateTime(2026, 3, 5, 14, 30),
      versionProtocolo: '0.1.0-provisional',
      estadoProtocolo: 'provisional',
      itemId: 'c01',
      opcion: 'a_veces',
      puntajesPorArea: {
        'comunicacion': {'puntos': 3, 'maximo': 8},
        'atencion': {'puntos': 0, 'maximo': 6},
      },
      nivel: 'comentar_control',
      focosRojos: 'f02,f03',
    );

    test(
      'columnas y valores, con prefijo de instalación y sin identificadores',
      () {
        final lineas = generarCsv([
          fila,
        ], instalacionId: 'A1B2C3').trim().split(RegExp(r'\r?\n'));
        expect(lineas, hasLength(2));
        expect(lineas.first.split(',').length, columnasCsv.length);
        expect(
          lineas[1],
          'A1B2C3-N0007,3_6,2026-03-05,0.1.0-provisional,provisional,c01,a_veces,3/8,,,0/6,,comentar_control,f02;f03',
        );
      },
    );

    test('las columnas no incluyen nombre, nacimiento, alias ni fotos', () {
      for (final c in columnasCsv) {
        expect(c, isNot(matches(RegExp('nombre|alias|nacimiento|foto'))));
      }
    });
  });
}
