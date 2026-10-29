import {
  GRAVEDAD_NIVEL,
  focosPara,
  itemsPara,
  maximoItem,
  type NivelOrientacion,
  type Opcion,
  type Protocolo,
} from './protocolo';

export interface PuntajeArea {
  areaId: string;
  /** Suma de puntos de las preguntas respondidas. */
  puntos: number;
  /** Puntos máximos posibles de las preguntas respondidas (sin contar la opción `no_se`). */
  maximo: number;
  respondidas: number;
  noSe: number;
}

export interface ResultadoOrientacion {
  versionProtocolo: string;
  estadoProtocolo: string;
  nivel: NivelOrientacion;
  areas: Record<string, PuntajeArea>;
  puntosTotal: number;
  maximoTotal: number;
  respondidas: number;
  noSe: number;
  sinResponder: number;
  focosRojos: string[];
  focoGrave: boolean;
  muchosNoSe: boolean;
  pocasRespuestas: boolean;
}

export function proporcionArea(a: PuntajeArea): number {
  return a.maximo === 0 ? 0 : a.puntos / a.maximo;
}

export interface EntradaMotor {
  protocolo: Protocolo;
  edadMeses: number;
  respuestas: Readonly<Record<string, Opcion>>;
  focosMarcados?: Iterable<string>;
}

/** Motor determinista: la misma entrada y el mismo protocolo dan siempre el mismo resultado. */
export function evaluar({ protocolo, edadMeses, respuestas, focosMarcados = [] }: EntradaMotor): ResultadoOrientacion {
  const items = itemsPara(protocolo, edadMeses);

  const areas: Record<string, PuntajeArea> = {};
  for (const a of protocolo.areas) areas[a.id] = { areaId: a.id, puntos: 0, maximo: 0, respondidas: 0, noSe: 0 };

  let sinResponder = 0;
  for (const item of items) {
    const r = respuestas[item.id];
    const area = areas[item.areaId];
    if (r === undefined) {
      sinResponder += 1;
    } else if (r === 'no_se') {
      area.noSe += 1;
    } else {
      area.puntos += item.puntos[r] ?? 0;
      area.maximo += maximoItem(item);
      area.respondidas += 1;
    }
  }

  const lista = Object.values(areas);
  const puntosTotal = lista.reduce((s, a) => s + a.puntos, 0);
  const maximoTotal = lista.reduce((s, a) => s + a.maximo, 0);
  const respondidas = lista.reduce((s, a) => s + a.respondidas, 0);
  const noSe = lista.reduce((s, a) => s + a.noSe, 0);

  const marcados = new Set(focosMarcados);
  const activados = focosPara(protocolo, edadMeses).filter((f) => marcados.has(f.id));
  const focoGrave = activados.some((f) => f.grave);

  const suficiente = respondidas >= protocolo.minimoRespondidas;
  const proporcionTotal = maximoTotal === 0 ? 0 : puntosTotal / maximoTotal;

  let nivel: NivelOrientacion = 'sin_senales';
  for (const regla of protocolo.reglas) {
    let cumple = false;
    if (regla.focoGrave && focoGrave) cumple = true;
    if (regla.focosRojosMin !== undefined && activados.length >= regla.focosRojosMin) cumple = true;
    if (suficiente) {
      if (regla.proporcionTotalMin !== undefined && proporcionTotal >= regla.proporcionTotalMin) cumple = true;
      if (
        regla.proporcionAreaMin !== undefined &&
        lista.some((a) => a.respondidas >= regla.areaMinItems && proporcionArea(a) >= regla.proporcionAreaMin!)
      ) {
        cumple = true;
      }
    }
    if (cumple) {
      nivel = regla.nivel;
      break;
    }
  }

  return {
    versionProtocolo: protocolo.version,
    estadoProtocolo: protocolo.estado,
    nivel,
    areas,
    puntosTotal,
    maximoTotal,
    respondidas,
    noSe,
    sinResponder,
    focosRojos: activados.map((f) => f.id),
    focoGrave,
    muchosNoSe: items.length > 0 && noSe / items.length >= protocolo.umbralNoSe,
    pocasRespuestas: !suficiente,
  };
}

export function esMasGrave(a: NivelOrientacion, b: NivelOrientacion): boolean {
  return GRAVEDAD_NIVEL[a] > GRAVEDAD_NIVEL[b];
}
