import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'data/abrir_base.dart';
import 'data/repositorio.dart';
import 'servicios/fotos_servicio.dart';
import 'servicios/servicios.dart';
import 'servicios/textos_app.dart';
import 'ui/app.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final base = await abrirBaseCifrada();
  final servicios = Servicios(
    repo: Repositorio(base),
    protocolos: await cargarProtocolos(rootBundle),
    textos: await TextosApp.cargar(rootBundle),
    selectorFotos: SelectorFotosImagePicker(),
    almacenFotos: AlmacenFotosArchivos(),
    instalacionId: await obtenerInstalacionId(),
  );
  runApp(NeuroAlertaApp(servicios: servicios));
}
