import type { TramoId } from './tramo';

export type Opcion = 'casi_siempre' | 'a_veces' | 'casi_nunca' | 'no_se';

export const OPCIONES: readonly Opcion[] = ['casi_siempre', 'a_veces', 'casi_nunca', 'no_se'];

export const ETIQUETA_OPCION: Record<Opcion, string> = {
  casi_siempre: 'Casi siempre',
  a_veces: 'A veces',
  casi_nunca: 'Casi nunca',
  no_se: 'Todavía no lo he observado',
};

export type NivelOrientacion = 'sin_senales' | 'comentar_control' | 'consultar_pronto';

export const GRAVEDAD_NIVEL: Record<NivelOrientacion, number> = {
  sin_senales: 0,
  comentar_control: 1,
  consultar_pronto: 2,
};

export interface Area {
  id: string;
  nombre: string;
}

export interface ItemProtocolo {
  id: string;
  areaId: string;
  texto: string;
  signoReferencia: string;
  /** Puntos por opción; la opción `no_se` («Todavía no lo he observado») nunca suma y no figura aquí. */
  puntos: Partial<Record<Opcion, number>>;
  edadMinMeses?: number;
  /** Constructo del M-CHAT-R/F con el que se alineó la pregunta (solo trazabilidad interna). */
  afinMchat?: string;
}

export interface FocoRojo {
  id: string;
  texto: string;
  signoReferencia: string;
  grave: boolean;
  edadMinMeses?: number;
}

/** Regla de nivel: se cumple si se cumple cualquiera de sus condiciones. */
export interface ReglaNivel {
  nivel: NivelOrientacion;
  proporcionTotalMin?: number;
  proporcionAreaMin?: number;
  areaMinItems: number;
  focosRojosMin?: number;
  focoGrave: boolean;
}

export interface Protocolo {
  tramo: TramoId;
  version: string;
  estado: string;
  fuente: string;
  minimoRespondidas: number;
  umbralNoSe: number;
  areas: Area[];
  items: ItemProtocolo[];
  focosRojos: FocoRojo[];
  reglas: ReglaNivel[];
}

export function maximoItem(item: ItemProtocolo): number {
  return Math.max(...Object.values(item.puntos).map((v) => v ?? 0));
}

export function esProvisional(p: Protocolo): boolean {
  return p.estado === 'provisional';
}

export function itemsPara(p: Protocolo, edadMeses: number): ItemProtocolo[] {
  return p.items.filter((i) => i.edadMinMeses === undefined || edadMeses >= i.edadMinMeses);
}

export function focosPara(p: Protocolo, edadMeses: number): FocoRojo[] {
  return p.focosRojos.filter((f) => f.edadMinMeses === undefined || edadMeses >= f.edadMinMeses);
}

export function areaDe(p: Protocolo, id: string): Area {
  const a = p.areas.find((x) => x.id === id);
  if (!a) throw new Error(`Área desconocida: ${id}`);
  return a;
}

// --- Lectura del JSON, con validación ---

type Json = Record<string, unknown>;

function req<T>(valor: unknown, que: string, ok: (v: unknown) => v is T): T {
  if (!ok(valor)) throw new Error(`Protocolo inválido: ${que}`);
  return valor;
}
const esTexto = (v: unknown): v is string => typeof v === 'string' && v.length > 0;
const esNumero = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
const esObjeto = (v: unknown): v is Json => typeof v === 'object' && v !== null && !Array.isArray(v);
const esLista = (v: unknown): v is unknown[] => Array.isArray(v);

function opcionDe(id: string): Opcion {
  if (!(OPCIONES as readonly string[]).includes(id)) throw new Error(`Protocolo inválido: opción desconocida ${id}`);
  return id as Opcion;
}
function nivelDe(id: string): NivelOrientacion {
  if (!(id in GRAVEDAD_NIVEL)) throw new Error(`Protocolo inválido: nivel desconocido ${id}`);
  return id as NivelOrientacion;
}
function tramoDe(id: string): TramoId {
  if (id !== '0_36' && id !== '3_6' && id !== '7_12') throw new Error(`Protocolo inválido: tramo desconocido ${id}`);
  return id;
}
function opcionalNum(v: unknown): number | undefined {
  return esNumero(v) ? v : undefined;
}

/** Convierte el JSON de un protocolo en un objeto tipado, o falla con un mensaje claro. */
export function parsearProtocolo(fuente: unknown): Protocolo {
  const m = req(fuente, 'raíz', esObjeto);
  const reglas = req(m.reglas_nivel, 'reglas_nivel', esLista)
    .map((r) => {
      const x = req(r, 'regla', esObjeto);
      return {
        nivel: nivelDe(req(x.nivel, 'regla.nivel', esTexto)),
        proporcionTotalMin: opcionalNum(x.proporcion_total_min),
        proporcionAreaMin: opcionalNum(x.proporcion_area_min),
        areaMinItems: opcionalNum(x.area_min_items) ?? 2,
        focosRojosMin: opcionalNum(x.focos_rojos_min),
        focoGrave: x.foco_grave === true,
      } satisfies ReglaNivel;
    })
    .sort((a, b) => GRAVEDAD_NIVEL[b.nivel] - GRAVEDAD_NIVEL[a.nivel]);

  const areas = req(m.areas, 'areas', esLista).map((a) => {
    const x = req(a, 'área', esObjeto);
    return { id: req(x.id, 'área.id', esTexto), nombre: req(x.nombre, 'área.nombre', esTexto) };
  });
  const idsAreas = new Set(areas.map((a) => a.id));

  const items = req(m.items, 'items', esLista).map((i) => {
    const x = req(i, 'ítem', esObjeto);
    const valores = req(x.valores, 'ítem.valores', esObjeto);
    const puntos: Partial<Record<Opcion, number>> = {};
    for (const [k, v] of Object.entries(valores)) {
      const op = opcionDe(k);
      if (op === 'no_se') throw new Error('Protocolo inválido: la opción «no_se» no puede sumar puntos');
      puntos[op] = req(v, 'ítem.valores', esNumero);
    }
    const areaId = req(x.area, 'ítem.area', esTexto);
    if (!idsAreas.has(areaId)) throw new Error(`Protocolo inválido: ítem con área inexistente ${areaId}`);
    return {
      id: req(x.id, 'ítem.id', esTexto),
      areaId,
      texto: req(x.texto, 'ítem.texto', esTexto),
      signoReferencia: req(x.signo_referencia, 'ítem.signo_referencia', esTexto),
      puntos,
      edadMinMeses: opcionalNum(x.edad_min_meses),
      afinMchat: typeof x.afin_mchat === 'string' ? x.afin_mchat : undefined,
    } satisfies ItemProtocolo;
  });
  if (new Set(items.map((i) => i.id)).size !== items.length) throw new Error('Protocolo inválido: ítems repetidos');

  const focosRojos = req(m.focos_rojos, 'focos_rojos', esLista).map((f) => {
    const x = req(f, 'foco', esObjeto);
    return {
      id: req(x.id, 'foco.id', esTexto),
      texto: req(x.texto, 'foco.texto', esTexto),
      signoReferencia: req(x.signo_referencia, 'foco.signo_referencia', esTexto),
      grave: x.grave === true,
      edadMinMeses: opcionalNum(x.edad_min_meses),
    } satisfies FocoRojo;
  });

  return {
    tramo: tramoDe(req(m.tramo, 'tramo', esTexto)),
    version: req(m.version, 'version', esTexto),
    estado: req(m.estado, 'estado', esTexto),
    fuente: req(m.fuente, 'fuente', esTexto),
    minimoRespondidas: req(m.minimo_respondidas, 'minimo_respondidas', esNumero),
    umbralNoSe: req(m.umbral_no_se, 'umbral_no_se', esNumero),
    areas,
    items,
    focosRojos,
    reglas,
  };
}
