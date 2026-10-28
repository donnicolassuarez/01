import 'dart:convert';

import 'tramo.dart';

/// Opciones de respuesta del cuestionario.
enum Opcion {
  casiSiempre('casi_siempre', 'Casi siempre'),
  aVeces('a_veces', 'A veces'),
  casiNunca('casi_nunca', 'Casi nunca'),
  noSe('no_se', 'No sé');

  const Opcion(this.id, this.etiqueta);

  final String id;
  final String etiqueta;

  static Opcion desdeId(String id) => Opcion.values.firstWhere(
    (o) => o.id == id,
    orElse: () => throw ArgumentError('Opción desconocida: $id'),
  );
}

enum NivelOrientacion {
  sinSenales('sin_senales', 0),
  comentarControl('comentar_control', 1),
  consultarPronto('consultar_pronto', 2);

  const NivelOrientacion(this.id, this.gravedad);

  final String id;
  final int gravedad;

  static NivelOrientacion desdeId(String id) =>
      NivelOrientacion.values.firstWhere(
        (n) => n.id == id,
        orElse: () => throw ArgumentError('Nivel desconocido: $id'),
      );
}

class Area {
  const Area(this.id, this.nombre);
  final String id;
  final String nombre;
}

class ItemProtocolo {
  const ItemProtocolo({
    required this.id,
    required this.areaId,
    required this.texto,
    required this.signoReferencia,
    required this.puntos,
    this.edadMinMeses,
  });

  final String id;
  final String areaId;
  final String texto;
  final String signoReferencia;

  /// Puntos por opción; "No sé" nunca suma y no figura aquí.
  final Map<Opcion, int> puntos;
  final int? edadMinMeses;

  int get maximo => puntos.values.reduce((a, b) => a > b ? a : b);

  bool aplicaA(int edadMeses) =>
      edadMinMeses == null || edadMeses >= edadMinMeses!;
}

class FocoRojo {
  const FocoRojo({
    required this.id,
    required this.texto,
    required this.signoReferencia,
    required this.grave,
    this.edadMinMeses,
  });

  final String id;
  final String texto;
  final String signoReferencia;
  final bool grave;
  final int? edadMinMeses;

  bool aplicaA(int edadMeses) =>
      edadMinMeses == null || edadMeses >= edadMinMeses!;
}

/// Regla de nivel: se cumple si se cumple cualquiera de sus condiciones.
class ReglaNivel {
  const ReglaNivel({
    required this.nivel,
    this.proporcionTotalMin,
    this.proporcionAreaMin,
    this.areaMinItems = 2,
    this.focosRojosMin,
    this.focoGrave = false,
  });

  final NivelOrientacion nivel;
  final double? proporcionTotalMin;
  final double? proporcionAreaMin;
  final int areaMinItems;
  final int? focosRojosMin;
  final bool focoGrave;
}

class Protocolo {
  const Protocolo({
    required this.tramo,
    required this.version,
    required this.estado,
    required this.fuente,
    required this.minimoRespondidas,
    required this.umbralNoSe,
    required this.areas,
    required this.items,
    required this.focosRojos,
    required this.reglas,
  });

  final Tramo tramo;
  final String version;
  final String estado;
  final String fuente;
  final int minimoRespondidas;
  final double umbralNoSe;
  final List<Area> areas;
  final List<ItemProtocolo> items;
  final List<FocoRojo> focosRojos;
  final List<ReglaNivel> reglas;

  bool get esProvisional => estado == 'provisional';

  List<ItemProtocolo> itemsPara(int edadMeses) =>
      items.where((i) => i.aplicaA(edadMeses)).toList();

  List<FocoRojo> focosPara(int edadMeses) =>
      focosRojos.where((f) => f.aplicaA(edadMeses)).toList();

  Area area(String id) => areas.firstWhere((a) => a.id == id);

  factory Protocolo.desdeJson(String fuenteJson) {
    final m = jsonDecode(fuenteJson) as Map<String, dynamic>;
    final reglas = (m['reglas_nivel'] as List).map((r) {
      final x = r as Map<String, dynamic>;
      return ReglaNivel(
        nivel: NivelOrientacion.desdeId(x['nivel'] as String),
        proporcionTotalMin: (x['proporcion_total_min'] as num?)?.toDouble(),
        proporcionAreaMin: (x['proporcion_area_min'] as num?)?.toDouble(),
        areaMinItems: (x['area_min_items'] as num?)?.toInt() ?? 2,
        focosRojosMin: (x['focos_rojos_min'] as num?)?.toInt(),
        focoGrave: x['foco_grave'] as bool? ?? false,
      );
    }).toList()..sort((a, b) => b.nivel.gravedad.compareTo(a.nivel.gravedad));

    return Protocolo(
      tramo: Tramo.desdeId(m['tramo'] as String),
      version: m['version'] as String,
      estado: m['estado'] as String,
      fuente: m['fuente'] as String,
      minimoRespondidas: (m['minimo_respondidas'] as num).toInt(),
      umbralNoSe: (m['umbral_no_se'] as num).toDouble(),
      areas: (m['areas'] as List)
          .map((a) => Area((a as Map)['id'] as String, a['nombre'] as String))
          .toList(),
      items: (m['items'] as List).map((i) {
        final x = i as Map<String, dynamic>;
        final valores = (x['valores'] as Map<String, dynamic>).map(
          (k, v) => MapEntry(Opcion.desdeId(k), (v as num).toInt()),
        );
        return ItemProtocolo(
          id: x['id'] as String,
          areaId: x['area'] as String,
          texto: x['texto'] as String,
          signoReferencia: x['signo_referencia'] as String,
          puntos: valores,
          edadMinMeses: (x['edad_min_meses'] as num?)?.toInt(),
        );
      }).toList(),
      focosRojos: (m['focos_rojos'] as List).map((f) {
        final x = f as Map<String, dynamic>;
        return FocoRojo(
          id: x['id'] as String,
          texto: x['texto'] as String,
          signoReferencia: x['signo_referencia'] as String,
          grave: x['grave'] as bool? ?? false,
          edadMinMeses: (x['edad_min_meses'] as num?)?.toInt(),
        );
      }).toList(),
      reglas: reglas,
    );
  }
}
