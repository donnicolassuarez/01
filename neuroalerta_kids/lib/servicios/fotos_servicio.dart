import 'dart:io';

import 'package:image_picker/image_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

/// Origen de una foto: devuelve la ruta temporal del archivo elegido, o null si se canceló.
abstract class SelectorFotos {
  Future<String?> elegir({required bool camara});
}

class SelectorFotosImagePicker implements SelectorFotos {
  final _picker = ImagePicker();

  @override
  Future<String?> elegir({required bool camara}) async {
    final x = await _picker.pickImage(
      source: camara ? ImageSource.camera : ImageSource.gallery,
      maxWidth: 1920,
      imageQuality: 85,
    );
    return x?.path;
  }
}

/// Guarda las fotos solo en el almacenamiento privado de la aplicación.
abstract class AlmacenFotos {
  /// Copia el archivo al almacenamiento privado, borra el temporal y devuelve la ruta nueva.
  Future<String> guardar(String rutaOrigen);

  Future<void> eliminar(String ruta);
}

/// Usa una carpeta dentro del directorio privado de la aplicación.
/// Ese directorio no es escaneado por la galería del teléfono.
class AlmacenFotosArchivos implements AlmacenFotos {
  AlmacenFotosArchivos({
    this._carpeta,
    Future<Directory> Function()? ubicarCarpeta,
  }) : _ubicar = ubicarCarpeta ?? getApplicationSupportDirectory;

  Directory? _carpeta;
  final Future<Directory> Function() _ubicar;

  Future<Directory> _dir() async {
    final base = _carpeta ?? await _ubicar();
    final dir = Directory(p.join(base.path, 'fotos_privadas'));
    await dir.create(recursive: true);
    // Evita que cualquier visor de medios indexe la carpeta.
    final marca = File(p.join(dir.path, '.nomedia'));
    if (!await marca.exists()) await marca.create();
    _carpeta = base;
    return dir;
  }

  @override
  Future<String> guardar(String rutaOrigen) async {
    final dir = await _dir();
    final ext = p.extension(rutaOrigen).isEmpty
        ? '.jpg'
        : p.extension(rutaOrigen).toLowerCase();
    final destino = p.join(
      dir.path,
      'f_${DateTime.now().microsecondsSinceEpoch}$ext',
    );
    await File(rutaOrigen).copy(destino);
    try {
      await File(rutaOrigen).delete();
    } on FileSystemException {
      // Si el temporal no se puede borrar, la copia privada ya está a salvo.
    }
    return destino;
  }

  @override
  Future<void> eliminar(String ruta) async {
    final f = File(ruta);
    if (await f.exists()) await f.delete();
  }
}
