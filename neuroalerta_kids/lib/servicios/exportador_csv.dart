import 'package:csv/csv.dart';

import '../data/repositorio.dart';

/// Áreas que pueden aparecer en cualquiera de los protocolos, en orden fijo de columnas.
const areasExportadas = [
  'comunicacion',
  'interaccion',
  'conductas',
  'atencion',
  'hiperactividad',
];

const columnasCsv = [
  'codigo_interno',
  'tramo_edad',
  'fecha_sesion',
  'version_protocolo',
  'estado_protocolo',
  'item',
  'respuesta',
  'puntaje_comunicacion',
  'puntaje_interaccion',
  'puntaje_conductas',
  'puntaje_atencion',
  'puntaje_hiperactividad',
  'nivel_orientacion',
  'focos_rojos',
];

String _fecha(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

/// Código seudónimo: prefijo de la instalación + número interno. No se exporta el alias que escribió la familia.
String codigoInterno(String instalacionId, int ninoId) =>
    '$instalacionId-N${ninoId.toString().padLeft(4, '0')}';

/// Genera el CSV. Sin nombres, sin fecha de nacimiento y sin fotos.
String generarCsv(
  List<FilaExportacion> filas, {
  required String instalacionId,
}) {
  final filasCsv = <List<Object?>>[
    columnasCsv,
    for (final f in filas)
      [
        codigoInterno(instalacionId, f.ninoId),
        f.tramo,
        _fecha(f.fechaSesion),
        f.versionProtocolo,
        f.estadoProtocolo,
        f.itemId,
        f.opcion,
        for (final a in areasExportadas) _puntajeArea(f.puntajesPorArea[a]),
        f.nivel,
        f.focosRojos.replaceAll(',', ';'),
      ],
  ];
  return csv.encode(filasCsv);
}

String _puntajeArea(Object? area) {
  if (area is! Map) return '';
  return '${area['puntos']}/${area['maximo']}';
}
