import 'dart:convert';

import 'package:flutter/services.dart';

import '../domain/protocolo.dart';
import '../domain/tramo.dart';

class TextoNivel {
  const TextoNivel({
    required this.titulo,
    required this.resumen,
    required this.paso,
  });
  final String titulo;
  final String resumen;
  final String paso;
}

class Consentimiento {
  const Consentimiento({
    required this.version,
    required this.titulo,
    required this.texto,
    required this.seGuarda,
    required this.privacidad,
    required this.aceptacion,
  });

  final String version;
  final String titulo;
  final List<String> texto;
  final List<String> seGuarda;
  final List<String> privacidad;
  final String aceptacion;
}

/// Textos editables (niveles de orientación y consentimiento), leídos de assets.
class TextosApp {
  const TextosApp({
    required this.aviso,
    required this.niveles,
    required this.focoGrave,
    required this.notaNoSe,
    required this.notaPocasRespuestas,
    required this.consentimiento,
  });

  final String aviso;
  final Map<NivelOrientacion, TextoNivel> niveles;
  final String focoGrave;
  final String notaNoSe;
  final String notaPocasRespuestas;
  final Consentimiento consentimiento;

  static TextosApp desdeJson(String nivelesJson, String consentimientoJson) {
    final n = jsonDecode(nivelesJson) as Map<String, dynamic>;
    final c = jsonDecode(consentimientoJson) as Map<String, dynamic>;
    List<String> lista(String k) => (c[k] as List).cast<String>();
    return TextosApp(
      aviso: n['aviso'] as String,
      niveles: {
        for (final nivel in NivelOrientacion.values)
          nivel: TextoNivel(
            titulo: (n['niveles'][nivel.id] as Map)['titulo'] as String,
            resumen: (n['niveles'][nivel.id] as Map)['resumen'] as String,
            paso: (n['niveles'][nivel.id] as Map)['paso'] as String,
          ),
      },
      focoGrave: n['foco_grave'] as String,
      notaNoSe: n['nota_no_se'] as String,
      notaPocasRespuestas: n['nota_pocas_respuestas'] as String,
      consentimiento: Consentimiento(
        version: c['version'] as String,
        titulo: c['titulo'] as String,
        texto: lista('texto'),
        seGuarda: lista('se_guarda'),
        privacidad: lista('privacidad'),
        aceptacion: c['aceptacion'] as String,
      ),
    );
  }

  static Future<TextosApp> cargar(AssetBundle bundle) async => desdeJson(
    await bundle.loadString('assets/textos/niveles.json'),
    await bundle.loadString('assets/textos/consentimiento.json'),
  );
}

Future<Map<Tramo, Protocolo>> cargarProtocolos(AssetBundle bundle) async {
  const archivos = {
    Tramo.meses0a36: 'assets/protocolos/protocolo_0_36.json',
    Tramo.anios3a6: 'assets/protocolos/protocolo_3_6.json',
    Tramo.anios7a12: 'assets/protocolos/protocolo_7_12.json',
  };
  return {
    for (final e in archivos.entries)
      e.key: Protocolo.desdeJson(await bundle.loadString(e.value)),
  };
}
