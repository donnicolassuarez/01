import 'protocolo.dart';

class PuntajeArea {
  const PuntajeArea({
    required this.areaId,
    required this.puntos,
    required this.maximo,
    required this.respondidas,
    required this.noSe,
  });

  final String areaId;

  /// Suma de puntos de las preguntas respondidas.
  final int puntos;

  /// Puntos máximos posibles de las preguntas respondidas (sin contar "No sé").
  final int maximo;
  final int respondidas;
  final int noSe;

  double get proporcion => maximo == 0 ? 0 : puntos / maximo;
}

class ResultadoOrientacion {
  const ResultadoOrientacion({
    required this.versionProtocolo,
    required this.estadoProtocolo,
    required this.nivel,
    required this.areas,
    required this.puntosTotal,
    required this.maximoTotal,
    required this.respondidas,
    required this.noSe,
    required this.sinResponder,
    required this.focosRojos,
    required this.focoGrave,
    required this.muchosNoSe,
    required this.pocasRespuestas,
  });

  final String versionProtocolo;
  final String estadoProtocolo;
  final NivelOrientacion nivel;
  final Map<String, PuntajeArea> areas;
  final int puntosTotal;
  final int maximoTotal;
  final int respondidas;
  final int noSe;
  final int sinResponder;
  final List<String> focosRojos;
  final bool focoGrave;
  final bool muchosNoSe;
  final bool pocasRespuestas;

  double get proporcionTotal =>
      maximoTotal == 0 ? 0 : puntosTotal / maximoTotal;
}

/// Motor determinista: la misma entrada y el mismo protocolo dan siempre el mismo resultado.
class MotorPuntuacion {
  const MotorPuntuacion();

  ResultadoOrientacion evaluar({
    required Protocolo protocolo,
    required int edadMeses,
    required Map<String, Opcion> respuestas,
    Set<String> focosMarcados = const {},
  }) {
    final items = protocolo.itemsPara(edadMeses);

    final puntos = <String, int>{};
    final maximos = <String, int>{};
    final respondidasPorArea = <String, int>{};
    final noSePorArea = <String, int>{};
    for (final a in protocolo.areas) {
      puntos[a.id] = 0;
      maximos[a.id] = 0;
      respondidasPorArea[a.id] = 0;
      noSePorArea[a.id] = 0;
    }

    var sinResponder = 0;
    for (final item in items) {
      final r = respuestas[item.id];
      if (r == null) {
        sinResponder++;
      } else if (r == Opcion.noSe) {
        noSePorArea[item.areaId] = noSePorArea[item.areaId]! + 1;
      } else {
        puntos[item.areaId] = puntos[item.areaId]! + (item.puntos[r] ?? 0);
        maximos[item.areaId] = maximos[item.areaId]! + item.maximo;
        respondidasPorArea[item.areaId] = respondidasPorArea[item.areaId]! + 1;
      }
    }

    final areas = {
      for (final a in protocolo.areas)
        a.id: PuntajeArea(
          areaId: a.id,
          puntos: puntos[a.id]!,
          maximo: maximos[a.id]!,
          respondidas: respondidasPorArea[a.id]!,
          noSe: noSePorArea[a.id]!,
        ),
    };

    final puntosTotal = puntos.values.fold<int>(0, (s, v) => s + v);
    final maximoTotal = maximos.values.fold<int>(0, (s, v) => s + v);
    final respondidas = respondidasPorArea.values.fold<int>(0, (s, v) => s + v);
    final noSe = noSePorArea.values.fold<int>(0, (s, v) => s + v);

    final focosAplicables = protocolo.focosPara(edadMeses);
    final activados = [
      for (final f in focosAplicables)
        if (focosMarcados.contains(f.id)) f,
    ];
    final focoGrave = activados.any((f) => f.grave);

    final suficiente = respondidas >= protocolo.minimoRespondidas;
    final proporcionTotal = maximoTotal == 0 ? 0.0 : puntosTotal / maximoTotal;

    var nivel = NivelOrientacion.sinSenales;
    for (final regla in protocolo.reglas) {
      var cumple = false;
      if (regla.focoGrave && focoGrave) cumple = true;
      if (regla.focosRojosMin != null &&
          activados.length >= regla.focosRojosMin!) {
        cumple = true;
      }
      if (suficiente) {
        if (regla.proporcionTotalMin != null &&
            proporcionTotal >= regla.proporcionTotalMin!) {
          cumple = true;
        }
        if (regla.proporcionAreaMin != null &&
            areas.values.any(
              (a) =>
                  a.respondidas >= regla.areaMinItems &&
                  a.proporcion >= regla.proporcionAreaMin!,
            )) {
          cumple = true;
        }
      }
      if (cumple) {
        nivel = regla.nivel;
        break;
      }
    }

    return ResultadoOrientacion(
      versionProtocolo: protocolo.version,
      estadoProtocolo: protocolo.estado,
      nivel: nivel,
      areas: areas,
      puntosTotal: puntosTotal,
      maximoTotal: maximoTotal,
      respondidas: respondidas,
      noSe: noSe,
      sinResponder: sinResponder,
      focosRojos: [for (final f in activados) f.id],
      focoGrave: focoGrave,
      muchosNoSe:
          items.isNotEmpty && noSe / items.length >= protocolo.umbralNoSe,
      pocasRespuestas: !suficiente,
    );
  }
}
