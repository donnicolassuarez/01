import 'dart:convert';

import 'package:drift/drift.dart';

import '../domain/motor_puntuacion.dart';
import '../domain/protocolo.dart';
import '../domain/tramo.dart';
import 'base_datos.dart';

class ConsentimientoRequerido implements Exception {
  const ConsentimientoRequerido();
  @override
  String toString() =>
      'Se necesita aceptar el consentimiento informado antes de guardar datos.';
}

class EdadFueraDeRango implements Exception {
  const EdadFueraDeRango();
  @override
  String toString() =>
      'La edad queda fuera del rango de la aplicación (0 a 12 años).';
}

class SesionConResultado {
  const SesionConResultado(this.sesion, this.resultado);
  final Sesion sesion;
  final Resultado? resultado;
}

class FilaExportacion {
  const FilaExportacion({
    required this.ninoId,
    required this.tramo,
    required this.fechaSesion,
    required this.versionProtocolo,
    required this.estadoProtocolo,
    required this.itemId,
    required this.opcion,
    required this.puntajesPorArea,
    required this.nivel,
    required this.focosRojos,
  });

  final int ninoId;
  final String tramo;
  final DateTime fechaSesion;
  final String versionProtocolo;
  final String estadoProtocolo;
  final String itemId;
  final String opcion;
  final Map<String, dynamic> puntajesPorArea;
  final String nivel;
  final String focosRojos;
}

class Repositorio {
  Repositorio(this.db, {DateTime Function()? ahora})
    : _ahora = ahora ?? DateTime.now;

  final BaseDatos db;
  final DateTime Function() _ahora;

  // Consentimiento

  Future<Consentimiento?> consentimientoVigente(String versionTexto) {
    return (db.select(db.consentimientos)
          ..where((c) => c.versionTexto.equals(versionTexto))
          ..limit(1))
        .getSingleOrNull();
  }

  Future<void> registrarConsentimiento(String versionTexto) async {
    await db
        .into(db.consentimientos)
        .insert(
          ConsentimientosCompanion.insert(
            versionTexto: versionTexto,
            aceptadoEn: _ahora(),
          ),
        );
  }

  Future<void> _exigirConsentimiento() async {
    final n = await db.consentimientos.count().getSingle();
    if (n == 0) throw const ConsentimientoRequerido();
  }

  // Niños

  Future<Nino> crearNino({
    required String codigo,
    required DateTime fechaNacimiento,
  }) async {
    await _exigirConsentimiento();
    final ahora = _ahora();
    final tramo = Tramo.desdeEdadMeses(edadEnMeses(fechaNacimiento, ahora));
    if (tramo == null) throw const EdadFueraDeRango();
    final id = await db
        .into(db.ninos)
        .insert(
          NinosCompanion.insert(
            codigo: codigo.trim(),
            fechaNacimiento: fechaNacimiento,
            tramo: tramo.id,
            creadoEn: ahora,
          ),
        );
    return (db.select(db.ninos)..where((n) => n.id.equals(id))).getSingle();
  }

  Future<List<Nino>> listarNinos() => (db.select(
    db.ninos,
  )..orderBy([(n) => OrderingTerm.asc(n.creadoEn)])).get();

  Future<Nino> nino(int id) =>
      (db.select(db.ninos)..where((n) => n.id.equals(id))).getSingle();

  // Sesiones y respuestas

  /// Abre una sesión para el niño o retoma la que quedó sin cerrar, para no perder el avance.
  Future<Sesion> iniciarOReanudarSesion({
    required Nino nino,
    required Protocolo protocolo,
  }) async {
    await _exigirConsentimiento();
    final ahora = _ahora();
    final edad = edadEnMeses(nino.fechaNacimiento, ahora);
    final abierta =
        await (db.select(db.sesiones)
              ..where(
                (s) =>
                    s.ninoId.equals(nino.id) &
                    s.cerradaEn.isNull() &
                    s.tramo.equals(protocolo.tramo.id) &
                    s.versionProtocolo.equals(protocolo.version),
              )
              ..orderBy([(s) => OrderingTerm.desc(s.iniciadaEn)])
              ..limit(1))
            .getSingleOrNull();
    if (abierta != null) return abierta;
    final id = await db
        .into(db.sesiones)
        .insert(
          SesionesCompanion.insert(
            ninoId: nino.id,
            tramo: protocolo.tramo.id,
            edadMeses: edad,
            versionProtocolo: protocolo.version,
            iniciadaEn: ahora,
          ),
        );
    return (db.select(db.sesiones)..where((s) => s.id.equals(id))).getSingle();
  }

  Future<Sesion> sesion(int id) =>
      (db.select(db.sesiones)..where((s) => s.id.equals(id))).getSingle();

  Future<void> guardarRespuesta({
    required int sesionId,
    required ItemProtocolo item,
    required Opcion opcion,
  }) async {
    await _exigirConsentimiento();
    await db
        .into(db.respuestas)
        .insert(
          RespuestasCompanion.insert(
            sesionId: sesionId,
            itemId: item.id,
            opcion: opcion.id,
            puntos: Value(opcion == Opcion.noSe ? null : item.puntos[opcion]),
          ),
          onConflict: DoUpdate(
            (_) => RespuestasCompanion(
              opcion: Value(opcion.id),
              puntos: Value(opcion == Opcion.noSe ? null : item.puntos[opcion]),
            ),
            target: [db.respuestas.sesionId, db.respuestas.itemId],
          ),
        );
  }

  Future<Map<String, Opcion>> respuestasDe(int sesionId) async {
    final filas = await (db.select(
      db.respuestas,
    )..where((r) => r.sesionId.equals(sesionId))).get();
    return {for (final r in filas) r.itemId: Opcion.desdeId(r.opcion)};
  }

  Future<void> guardarFocos(int sesionId, Set<String> focos) async {
    await (db.update(db.sesiones)..where((s) => s.id.equals(sesionId))).write(
      SesionesCompanion(
        focosMarcados: Value((focos.toList()..sort()).join(',')),
      ),
    );
  }

  Set<String> focosDe(Sesion s) =>
      s.focosMarcados.isEmpty ? {} : s.focosMarcados.split(',').toSet();

  /// Guarda el resultado y cierra la sesión.
  Future<Resultado> cerrarSesion(int sesionId, ResultadoOrientacion r) async {
    await _exigirConsentimiento();
    final ahora = _ahora();
    final areas = {
      for (final e in r.areas.entries)
        e.key: {
          'puntos': e.value.puntos,
          'maximo': e.value.maximo,
          'respondidas': e.value.respondidas,
          'no_se': e.value.noSe,
        },
    };
    await db.transaction(() async {
      final nuevo = ResultadosCompanion.insert(
        sesionId: sesionId,
        puntajesPorArea: jsonEncode(areas),
        puntosTotal: r.puntosTotal,
        maximoTotal: r.maximoTotal,
        noSe: r.noSe,
        nivel: r.nivel.id,
        focosRojos: Value(r.focosRojos.join(',')),
        versionProtocolo: r.versionProtocolo,
        estadoProtocolo: r.estadoProtocolo,
        creadoEn: ahora,
      );
      await db
          .into(db.resultados)
          .insert(
            nuevo,
            onConflict: DoUpdate(
              (_) => nuevo,
              target: [db.resultados.sesionId],
            ),
          );
      await (db.update(db.sesiones)..where((s) => s.id.equals(sesionId))).write(
        SesionesCompanion(cerradaEn: Value(ahora)),
      );
    });
    return (db.select(
      db.resultados,
    )..where((x) => x.sesionId.equals(sesionId))).getSingle();
  }

  Future<Resultado?> resultadoDe(int sesionId) => (db.select(
    db.resultados,
  )..where((x) => x.sesionId.equals(sesionId))).getSingleOrNull();

  Future<List<SesionConResultado>> historial(int ninoId) async {
    final sesiones =
        await (db.select(db.sesiones)
              ..where((s) => s.ninoId.equals(ninoId) & s.cerradaEn.isNotNull())
              ..orderBy([(s) => OrderingTerm.desc(s.iniciadaEn)]))
            .get();
    final salida = <SesionConResultado>[];
    for (final s in sesiones) {
      final r = await (db.select(
        db.resultados,
      )..where((x) => x.sesionId.equals(s.id))).getSingleOrNull();
      salida.add(SesionConResultado(s, r));
    }
    return salida;
  }

  // Fotos

  Future<Foto> agregarFoto({
    required int ninoId,
    required String ruta,
    required DateTime fecha,
    String nota = '',
  }) async {
    await _exigirConsentimiento();
    final id = await db
        .into(db.fotos)
        .insert(
          FotosCompanion.insert(
            ninoId: ninoId,
            ruta: ruta,
            fecha: fecha,
            nota: Value(nota.trim()),
          ),
        );
    return (db.select(db.fotos)..where((f) => f.id.equals(id))).getSingle();
  }

  Future<List<Foto>> fotosDe(int ninoId) =>
      (db.select(db.fotos)
            ..where((f) => f.ninoId.equals(ninoId))
            ..orderBy([(f) => OrderingTerm.desc(f.fecha)]))
          .get();

  Future<void> eliminarFoto(int id) =>
      (db.delete(db.fotos)..where((f) => f.id.equals(id))).go();

  // Exportación

  /// Una fila por respuesta de cada sesión cerrada, con el resultado de esa sesión.
  Future<List<FilaExportacion>> filasParaExportar() async {
    final cerradas =
        await (db.select(db.sesiones)
              ..where((s) => s.cerradaEn.isNotNull())
              ..orderBy([(s) => OrderingTerm.asc(s.iniciadaEn)]))
            .get();
    final filas = <FilaExportacion>[];
    for (final s in cerradas) {
      final res = await (db.select(
        db.resultados,
      )..where((x) => x.sesionId.equals(s.id))).getSingleOrNull();
      if (res == null) continue;
      final resp =
          await (db.select(db.respuestas)
                ..where((r) => r.sesionId.equals(s.id))
                ..orderBy([(r) => OrderingTerm.asc(r.itemId)]))
              .get();
      for (final r in resp) {
        filas.add(
          FilaExportacion(
            ninoId: s.ninoId,
            tramo: s.tramo,
            fechaSesion: s.iniciadaEn,
            versionProtocolo: res.versionProtocolo,
            estadoProtocolo: res.estadoProtocolo,
            itemId: r.itemId,
            opcion: r.opcion,
            puntajesPorArea:
                jsonDecode(res.puntajesPorArea) as Map<String, dynamic>,
            nivel: res.nivel,
            focosRojos: res.focosRojos,
          ),
        );
      }
    }
    return filas;
  }
}
