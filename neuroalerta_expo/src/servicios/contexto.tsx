import { createContext, useContext } from 'react';

import type { Repositorio } from '../data/repositorio';
import type { Protocolo } from '../domain/protocolo';
import type { TramoId } from '../domain/tramo';
import { generarCsv } from './exportadorCsv';
import type { AlmacenFotos, SelectorFotos } from './fotos';
import type { TextosApp } from './textos';

/** Todo lo que las pantallas necesitan del exterior. En las pruebas se reemplaza por versiones falsas. */
export interface Servicios {
  repo: Repositorio;
  protocolos: Record<TramoId, Protocolo>;
  textos: TextosApp;
  selectorFotos: SelectorFotos;
  almacenFotos: AlmacenFotos;
  instalacionId: string;
  /** Comparte un archivo con el selector del sistema. */
  compartir(ruta: string, asunto: string): Promise<void>;
  /** Escribe un archivo de texto temporal y devuelve su ruta. */
  escribirArchivo(nombre: string, contenido: string): Promise<string>;
  ahora(): Date;
  /** Falso solo en desarrollo, cuando se pidió trabajar sin cifrado. */
  cifrada: boolean;
}

export const ServiciosContext = createContext<Servicios | null>(null);

export function useServicios(): Servicios {
  const s = useContext(ServiciosContext);
  if (!s) throw new Error('Falta el proveedor de servicios');
  return s;
}

const dos = (n: number) => String(n).padStart(2, '0');

/** Genera el CSV del equipo y lo comparte. Devuelve la ruta del archivo. */
export async function exportarCsv(s: Servicios): Promise<string> {
  const filas = await s.repo.filasParaExportar();
  const contenido = generarCsv(filas, { instalacionId: s.instalacionId });
  const d = s.ahora();
  const marca = `${d.getFullYear()}${dos(d.getMonth() + 1)}${dos(d.getDate())}`;
  const ruta = await s.escribirArchivo(`neuroalerta_provisional_${marca}.csv`, contenido);
  await s.compartir(ruta, 'Exportación provisional del piloto');
  return ruta;
}
