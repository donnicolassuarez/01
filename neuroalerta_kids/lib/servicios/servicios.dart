import 'dart:io';

import 'package:flutter/widgets.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;
import 'package:share_plus/share_plus.dart';

import '../data/repositorio.dart';
import '../domain/motor_puntuacion.dart';
import '../domain/protocolo.dart';
import '../domain/tramo.dart';
import 'exportador_csv.dart';
import 'fotos_servicio.dart';
import 'textos_app.dart';

/// Comparte un archivo con el selector de Android.
typedef CompartirArchivo = Future<void> Function(String ruta, String asunto);

Future<void> compartirConSelector(String ruta, String asunto) async {
  await SharePlus.instance.share(
    ShareParams(files: [XFile(ruta)], subject: asunto),
  );
}

/// Escribe un archivo de texto en una carpeta temporal y devuelve su ruta.
typedef EscribirArchivo = Future<String> Function(
  String nombre,
  String contenido,
);

Future<String> escribirEnTemporal(String nombre, String contenido) async {
  final dir = await getTemporaryDirectory();
  final archivo = File(p.join(dir.path, nombre));
  await archivo.writeAsString(contenido);
  return archivo.path;
}

class Servicios {
  Servicios({
    required this.repo,
    required this.protocolos,
    required this.textos,
    required this.selectorFotos,
    required this.almacenFotos,
    required this.instalacionId,
    this.compartir = compartirConSelector,
    this.escribirArchivo = escribirEnTemporal,
    DateTime Function()? ahora,
  }) : ahora = ahora ?? DateTime.now;

  final Repositorio repo;
  final Map<Tramo, Protocolo> protocolos;
  final TextosApp textos;
  final SelectorFotos selectorFotos;
  final AlmacenFotos almacenFotos;
  final String instalacionId;
  final CompartirArchivo compartir;
  final EscribirArchivo escribirArchivo;
  final DateTime Function() ahora;
  final motor = const MotorPuntuacion();

  /// Genera el CSV en la carpeta temporal y lo comparte. Devuelve la ruta del archivo.
  Future<String> exportarCsv() async {
    final filas = await repo.filasParaExportar();
    final contenido = generarCsv(filas, instalacionId: instalacionId);
    final d = ahora();
    final marca =
        '${d.year}${d.month.toString().padLeft(2, '0')}${d.day.toString().padLeft(2, '0')}';
    final ruta = await escribirArchivo(
      'neuroalerta_provisional_$marca.csv',
      contenido,
    );
    await compartir(ruta, 'Exportación provisional del piloto');
    return ruta;
  }
}

class ServiciosScope extends InheritedWidget {
  const ServiciosScope({
    super.key,
    required this.servicios,
    required super.child,
  });

  final Servicios servicios;

  static Servicios of(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<ServiciosScope>()!.servicios;

  @override
  bool updateShouldNotify(ServiciosScope old) => servicios != old.servicios;
}
