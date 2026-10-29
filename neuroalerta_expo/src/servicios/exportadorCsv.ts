import type { FilaExportacion } from '../data/repositorio';

/** Áreas que pueden aparecer en cualquiera de los protocolos, en orden fijo de columnas. */
export const AREAS_EXPORTADAS = ['comunicacion', 'interaccion', 'conductas', 'atencion', 'hiperactividad'] as const;

export const COLUMNAS_CSV = [
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
] as const;

const dos = (n: number) => String(n).padStart(2, '0');
const fecha = (d: Date) => `${String(d.getFullYear()).padStart(4, '0')}-${dos(d.getMonth() + 1)}-${dos(d.getDate())}`;

/** Código seudónimo: prefijo de la instalación + número interno. No se exporta el alias que escribió la familia. */
export function codigoInterno(instalacionId: string, ninoId: number): string {
  return `${instalacionId}-N${String(ninoId).padStart(4, '0')}`;
}

/** Escapa un campo según RFC 4180. */
export function campoCsv(valor: string): string {
  return /[",\r\n]/.test(valor) ? `"${valor.replace(/"/g, '""')}"` : valor;
}

function puntajeArea(a: FilaExportacion['puntajesPorArea'][string] | undefined): string {
  return a ? `${a.puntos}/${a.maximo}` : '';
}

/** Genera el CSV. Sin nombres, sin fecha de nacimiento y sin fotos. */
export function generarCsv(filas: FilaExportacion[], opciones: { instalacionId: string }): string {
  const lineas: string[][] = [[...COLUMNAS_CSV]];
  for (const f of filas) {
    lineas.push([
      codigoInterno(opciones.instalacionId, f.ninoId),
      f.tramo,
      fecha(f.fechaSesion),
      f.versionProtocolo,
      f.estadoProtocolo,
      f.itemId,
      f.opcion,
      ...AREAS_EXPORTADAS.map((a) => puntajeArea(f.puntajesPorArea[a])),
      f.nivel,
      f.focosRojos.join(';'),
    ]);
  }
  return lineas.map((l) => l.map(campoCsv).join(',')).join('\r\n') + '\r\n';
}
