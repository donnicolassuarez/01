import 'dart:io';
import 'dart:math';

import 'package:drift/native.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:sqlite3/sqlite3.dart';

import 'base_datos.dart';

const _claveAlmacen = 'clave_base_datos';
const _instalacionAlmacen = 'instalacion_id';

String _aleatorioHex(int bytes) {
  final r = Random.secure();
  return List.generate(
    bytes,
    (_) => r.nextInt(256).toRadixString(16).padLeft(2, '0'),
  ).join();
}

/// Lee la clave de cifrado del almacén seguro del sistema; la crea la primera vez.
Future<String> obtenerOCrearSecreto(
  FlutterSecureStorage almacen,
  String nombre,
  int bytes,
) async {
  final existente = await almacen.read(key: nombre);
  if (existente != null && existente.isNotEmpty) return existente;
  final nuevo = _aleatorioHex(bytes);
  await almacen.write(key: nombre, value: nuevo);
  return nuevo;
}

/// Configura el cifrado de una conexión. Falla si la biblioteca no soporta cifrado,
/// para no guardar datos en claro sin darse cuenta.
void configurarCifrado(Database db, String clave) {
  final cifrado = db.select('PRAGMA cipher;');
  if (cifrado.isEmpty) {
    throw StateError('La biblioteca de SQLite no tiene cifrado disponible.');
  }
  db.execute("PRAGMA key = '$clave';");
}

/// Abre la base cifrada dentro del almacenamiento privado de la aplicación.
Future<BaseDatos> abrirBaseCifrada({
  FlutterSecureStorage? almacen,
  Directory? carpeta,
}) async {
  final seguro = almacen ?? const FlutterSecureStorage();
  final clave = await obtenerOCrearSecreto(seguro, _claveAlmacen, 32);
  final dir = carpeta ?? await getApplicationSupportDirectory();
  final archivo = File(p.join(dir.path, 'neuroalerta.db'));
  return BaseDatos(
    NativeDatabase.createInBackground(
      archivo,
      setup: (db) => configurarCifrado(db, clave),
    ),
  );
}

/// Identificador anónimo de esta instalación; sirve de prefijo en los códigos exportados.
Future<String> obtenerInstalacionId([FlutterSecureStorage? almacen]) async {
  final id = await obtenerOCrearSecreto(
    almacen ?? const FlutterSecureStorage(),
    _instalacionAlmacen,
    3,
  );
  return id.toUpperCase();
}
