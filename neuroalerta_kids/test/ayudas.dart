import 'package:drift/drift.dart' show driftRuntimeOptions;
import 'package:drift/native.dart';
import 'package:flutter/services.dart';
import 'package:neuroalerta_kids/data/base_datos.dart';
import 'package:neuroalerta_kids/data/repositorio.dart';
import 'package:neuroalerta_kids/servicios/fotos_servicio.dart';
import 'package:neuroalerta_kids/servicios/servicios.dart';
import 'package:neuroalerta_kids/servicios/textos_app.dart';

class SelectorFalso implements SelectorFotos {
  String? ruta;
  bool? ultimaCamara;

  @override
  Future<String?> elegir({required bool camara}) async {
    ultimaCamara = camara;
    return ruta;
  }
}

/// Almacén sin disco: el acceso real a archivos se prueba en almacen_fotos_test.dart.
class AlmacenFalso implements AlmacenFotos {
  final guardadas = <String>[];
  final eliminadas = <String>[];

  @override
  Future<String> guardar(String rutaOrigen) async {
    guardadas.add(rutaOrigen);
    return '/privado/fotos_privadas/f_${guardadas.length}.jpg';
  }

  @override
  Future<void> eliminar(String ruta) async => eliminadas.add(ruta);
}

class Entorno {
  Entorno._(
    this.base,
    this.servicios,
    this.selector,
    this.almacen,
    this.compartidos,
    this.csvEscritos,
  );

  final BaseDatos base;
  final Servicios servicios;
  final SelectorFalso selector;
  final AlmacenFalso almacen;
  final List<String> compartidos;
  final Map<String, String> csvEscritos;

  Repositorio get repo => servicios.repo;

  static Future<Entorno> crear({DateTime? hoy}) async {
    driftRuntimeOptions.dontWarnAboutMultipleDatabases = true;
    final ahora = hoy ?? DateTime(2026, 6, 10);
    final base = BaseDatos(NativeDatabase.memory());
    final almacen = AlmacenFalso();
    final csvEscritos = <String, String>{};
    final selector = SelectorFalso();
    final compartidos = <String>[];
    final servicios = Servicios(
      repo: Repositorio(base, ahora: () => ahora),
      protocolos: await cargarProtocolos(rootBundle),
      textos: await TextosApp.cargar(rootBundle),
      selectorFotos: selector,
      almacenFotos: almacen,
      instalacionId: 'ABC123',
      compartir: (ruta, asunto) async => compartidos.add(ruta),
      escribirArchivo: (nombre, contenido) async {
        csvEscritos['/tmp/$nombre'] = contenido;
        return '/tmp/$nombre';
      },
      ahora: () => ahora,
    );
    return Entorno._(
      base,
      servicios,
      selector,
      almacen,
      compartidos,
      csvEscritos,
    );
  }

  Future<void> cerrar() async {
    await base.close();
  }
}
