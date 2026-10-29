import type { Db } from './db';
import type { ResultadoOrientacion } from '../domain/motor';
import type { ItemProtocolo, NivelOrientacion, Opcion, Protocolo } from '../domain/protocolo';
import { edadEnMeses, tramoDesdeEdadMeses, type TramoId } from '../domain/tramo';

export class ConsentimientoRequerido extends Error {
  constructor() {
    super('Se necesita aceptar el consentimiento informado antes de guardar datos.');
    this.name = 'ConsentimientoRequerido';
  }
}

export class EdadFueraDeRango extends Error {
  constructor() {
    super('La edad queda fuera del rango de la aplicación (0 a 12 años).');
    this.name = 'EdadFueraDeRango';
  }
}

export interface Nino {
  id: number;
  codigo: string;
  fechaNacimiento: Date;
  tramo: TramoId;
  creadoEn: Date;
}

export interface Sesion {
  id: number;
  ninoId: number;
  tramo: TramoId;
  edadMeses: number;
  versionProtocolo: string;
  iniciadaEn: Date;
  cerradaEn: Date | null;
  focosMarcados: string[];
}

export interface Resultado {
  id: number;
  sesionId: number;
  puntajesPorArea: Record<string, { puntos: number; maximo: number; respondidas: number; no_se: number }>;
  puntosTotal: number;
  maximoTotal: number;
  noSe: number;
  nivel: NivelOrientacion;
  focosRojos: string[];
  versionProtocolo: string;
  estadoProtocolo: string;
  creadoEn: Date;
}

export interface Foto {
  id: number;
  ninoId: number;
  ruta: string;
  fecha: Date;
  nota: string;
}

export interface SesionConResultado {
  sesion: Sesion;
  resultado: Resultado | null;
}

export interface FilaExportacion {
  ninoId: number;
  tramo: TramoId;
  fechaSesion: Date;
  versionProtocolo: string;
  estadoProtocolo: string;
  itemId: string;
  opcion: Opcion;
  puntajesPorArea: Resultado['puntajesPorArea'];
  nivel: NivelOrientacion;
  focosRojos: string[];
}

const lista = (s: string): string[] => (s === '' ? [] : s.split(','));

 
const aNino = (r: any): Nino => ({
  id: r.id,
  codigo: r.codigo,
  fechaNacimiento: new Date(r.fecha_nacimiento),
  tramo: r.tramo,
  creadoEn: new Date(r.creado_en),
});
const aSesion = (r: any): Sesion => ({
  id: r.id,
  ninoId: r.nino_id,
  tramo: r.tramo,
  edadMeses: r.edad_meses,
  versionProtocolo: r.version_protocolo,
  iniciadaEn: new Date(r.iniciada_en),
  cerradaEn: r.cerrada_en === null ? null : new Date(r.cerrada_en),
  focosMarcados: lista(r.focos_marcados),
});
const aResultado = (r: any): Resultado => ({
  id: r.id,
  sesionId: r.sesion_id,
  puntajesPorArea: JSON.parse(r.puntajes_por_area),
  puntosTotal: r.puntos_total,
  maximoTotal: r.maximo_total,
  noSe: r.no_se,
  nivel: r.nivel,
  focosRojos: lista(r.focos_rojos),
  versionProtocolo: r.version_protocolo,
  estadoProtocolo: r.estado_protocolo,
  creadoEn: new Date(r.creado_en),
});
const aFoto = (r: any): Foto => ({
  id: r.id,
  ninoId: r.nino_id,
  ruta: r.ruta,
  fecha: new Date(r.fecha),
  nota: r.nota,
});
 

export class Repositorio {
  constructor(
    private readonly db: Db,
    private readonly ahora: () => Date = () => new Date(),
  ) {}

  // Consentimiento

  async consentimientoVigente(versionTexto: string): Promise<{ versionTexto: string; aceptadoEn: Date } | null> {
    const r = await this.db.getFirstAsync<{ version_texto: string; aceptado_en: number }>(
      'SELECT version_texto, aceptado_en FROM consentimientos WHERE version_texto = ? LIMIT 1',
      [versionTexto],
    );
    return r ? { versionTexto: r.version_texto, aceptadoEn: new Date(r.aceptado_en) } : null;
  }

  async registrarConsentimiento(versionTexto: string): Promise<void> {
    await this.db.runAsync('INSERT INTO consentimientos (version_texto, aceptado_en) VALUES (?, ?)', [
      versionTexto,
      this.ahora().getTime(),
    ]);
  }

  private async exigirConsentimiento(): Promise<void> {
    const r = await this.db.getFirstAsync<{ n: number }>('SELECT COUNT(*) AS n FROM consentimientos');
    if (!r || r.n === 0) throw new ConsentimientoRequerido();
  }

  // Niños

  async crearNino(datos: { codigo: string; fechaNacimiento: Date }): Promise<Nino> {
    await this.exigirConsentimiento();
    const ahora = this.ahora();
    const tramo = tramoDesdeEdadMeses(edadEnMeses(datos.fechaNacimiento, ahora));
    if (tramo === null) throw new EdadFueraDeRango();
    const r = await this.db.runAsync(
      'INSERT INTO ninos (codigo, fecha_nacimiento, tramo, creado_en) VALUES (?, ?, ?, ?)',
      [datos.codigo.trim(), datos.fechaNacimiento.getTime(), tramo, ahora.getTime()],
    );
    return this.nino(r.lastInsertRowId);
  }

  async listarNinos(): Promise<Nino[]> {
    return (await this.db.getAllAsync<unknown>('SELECT * FROM ninos ORDER BY creado_en ASC, id ASC')).map(aNino);
  }

  async nino(id: number): Promise<Nino> {
    const r = await this.db.getFirstAsync<unknown>('SELECT * FROM ninos WHERE id = ?', [id]);
    if (!r) throw new Error(`No existe el niño ${id}`);
    return aNino(r);
  }

  // Sesiones y respuestas

  /** Abre una sesión para el niño o retoma la que quedó sin cerrar, para no perder el avance. */
  async iniciarOReanudarSesion(args: { nino: Nino; protocolo: Protocolo }): Promise<Sesion> {
    await this.exigirConsentimiento();
    const { nino, protocolo } = args;
    const ahora = this.ahora();
    const abierta = await this.db.getFirstAsync<unknown>(
      `SELECT * FROM sesiones
       WHERE nino_id = ? AND cerrada_en IS NULL AND tramo = ? AND version_protocolo = ?
       ORDER BY iniciada_en DESC, id DESC LIMIT 1`,
      [nino.id, protocolo.tramo, protocolo.version],
    );
    if (abierta) return aSesion(abierta);
    const r = await this.db.runAsync(
      `INSERT INTO sesiones (nino_id, tramo, edad_meses, version_protocolo, iniciada_en)
       VALUES (?, ?, ?, ?, ?)`,
      [nino.id, protocolo.tramo, edadEnMeses(nino.fechaNacimiento, ahora), protocolo.version, ahora.getTime()],
    );
    return this.sesion(r.lastInsertRowId);
  }

  async sesion(id: number): Promise<Sesion> {
    const r = await this.db.getFirstAsync<unknown>('SELECT * FROM sesiones WHERE id = ?', [id]);
    if (!r) throw new Error(`No existe la sesión ${id}`);
    return aSesion(r);
  }

  async guardarRespuesta(args: { sesionId: number; item: ItemProtocolo; opcion: Opcion }): Promise<void> {
    await this.exigirConsentimiento();
    const puntos = args.opcion === 'no_se' ? null : (args.item.puntos[args.opcion] ?? null);
    await this.db.runAsync(
      `INSERT INTO respuestas (sesion_id, item_id, opcion, puntos) VALUES (?, ?, ?, ?)
       ON CONFLICT (sesion_id, item_id) DO UPDATE SET opcion = excluded.opcion, puntos = excluded.puntos`,
      [args.sesionId, args.item.id, args.opcion, puntos],
    );
  }

  async respuestasDe(sesionId: number): Promise<Record<string, Opcion>> {
    const filas = await this.db.getAllAsync<{ item_id: string; opcion: Opcion }>(
      'SELECT item_id, opcion FROM respuestas WHERE sesion_id = ? ORDER BY id ASC',
      [sesionId],
    );
    return Object.fromEntries(filas.map((f) => [f.item_id, f.opcion]));
  }

  async guardarFocos(sesionId: number, focos: Iterable<string>): Promise<void> {
    const texto = [...new Set(focos)].sort().join(',');
    await this.db.runAsync('UPDATE sesiones SET focos_marcados = ? WHERE id = ?', [texto, sesionId]);
  }

  /** Guarda el resultado y cierra la sesión. */
  async cerrarSesion(sesionId: number, r: ResultadoOrientacion): Promise<Resultado> {
    await this.exigirConsentimiento();
    const ahora = this.ahora().getTime();
    const areas = Object.fromEntries(
      Object.entries(r.areas).map(([id, a]) => [
        id,
        { puntos: a.puntos, maximo: a.maximo, respondidas: a.respondidas, no_se: a.noSe },
      ]),
    );
    await this.db.withTransactionAsync(async () => {
      await this.db.runAsync(
        `INSERT INTO resultados
           (sesion_id, puntajes_por_area, puntos_total, maximo_total, no_se, nivel, focos_rojos,
            version_protocolo, estado_protocolo, creado_en)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
         ON CONFLICT (sesion_id) DO UPDATE SET
           puntajes_por_area = excluded.puntajes_por_area, puntos_total = excluded.puntos_total,
           maximo_total = excluded.maximo_total, no_se = excluded.no_se, nivel = excluded.nivel,
           focos_rojos = excluded.focos_rojos, version_protocolo = excluded.version_protocolo,
           estado_protocolo = excluded.estado_protocolo, creado_en = excluded.creado_en`,
        [
          sesionId,
          JSON.stringify(areas),
          r.puntosTotal,
          r.maximoTotal,
          r.noSe,
          r.nivel,
          r.focosRojos.join(','),
          r.versionProtocolo,
          r.estadoProtocolo,
          ahora,
        ],
      );
      await this.db.runAsync('UPDATE sesiones SET cerrada_en = ? WHERE id = ?', [ahora, sesionId]);
    });
    const res = await this.resultadoDe(sesionId);
    if (!res) throw new Error('No se pudo guardar el resultado');
    return res;
  }

  async resultadoDe(sesionId: number): Promise<Resultado | null> {
    const r = await this.db.getFirstAsync<unknown>('SELECT * FROM resultados WHERE sesion_id = ?', [sesionId]);
    return r ? aResultado(r) : null;
  }

  async historial(ninoId: number): Promise<SesionConResultado[]> {
    const sesiones = (
      await this.db.getAllAsync<unknown>(
        'SELECT * FROM sesiones WHERE nino_id = ? AND cerrada_en IS NOT NULL ORDER BY iniciada_en DESC, id DESC',
        [ninoId],
      )
    ).map(aSesion);
    return Promise.all(sesiones.map(async (sesion) => ({ sesion, resultado: await this.resultadoDe(sesion.id) })));
  }

  // Fotos

  async agregarFoto(args: { ninoId: number; ruta: string; fecha: Date; nota?: string }): Promise<Foto> {
    await this.exigirConsentimiento();
    const r = await this.db.runAsync('INSERT INTO fotos (nino_id, ruta, fecha, nota) VALUES (?, ?, ?, ?)', [
      args.ninoId,
      args.ruta,
      args.fecha.getTime(),
      (args.nota ?? '').trim(),
    ]);
    const f = await this.db.getFirstAsync<unknown>('SELECT * FROM fotos WHERE id = ?', [r.lastInsertRowId]);
    return aFoto(f);
  }

  async fotosDe(ninoId: number): Promise<Foto[]> {
    return (
      await this.db.getAllAsync<unknown>('SELECT * FROM fotos WHERE nino_id = ? ORDER BY fecha DESC, id DESC', [ninoId])
    ).map(aFoto);
  }

  async eliminarFoto(id: number): Promise<void> {
    await this.db.runAsync('DELETE FROM fotos WHERE id = ?', [id]);
  }

  // Exportación

  /** Una fila por respuesta de cada sesión cerrada, con el resultado de esa sesión. */
  async filasParaExportar(): Promise<FilaExportacion[]> {
    const cerradas = (
      await this.db.getAllAsync<unknown>('SELECT * FROM sesiones WHERE cerrada_en IS NOT NULL ORDER BY iniciada_en ASC, id ASC')
    ).map(aSesion);
    const filas: FilaExportacion[] = [];
    for (const s of cerradas) {
      const res = await this.resultadoDe(s.id);
      if (!res) continue;
      const resp = await this.db.getAllAsync<{ item_id: string; opcion: Opcion }>(
        'SELECT item_id, opcion FROM respuestas WHERE sesion_id = ? ORDER BY item_id ASC',
        [s.id],
      );
      for (const r of resp) {
        filas.push({
          ninoId: s.ninoId,
          tramo: s.tramo,
          fechaSesion: s.iniciadaEn,
          versionProtocolo: res.versionProtocolo,
          estadoProtocolo: res.estadoProtocolo,
          itemId: r.item_id,
          opcion: r.opcion,
          puntajesPorArea: res.puntajesPorArea,
          nivel: res.nivel,
          focosRojos: res.focosRojos,
        });
      }
    }
    return filas;
  }
}
