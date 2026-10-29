import type { ReactElement } from 'react';
import { render } from '@testing-library/react-native';

import { migrar } from '../../src/data/esquema';
import { Repositorio } from '../../src/data/repositorio';
import { PROTOCOLOS } from '../../src/domain/protocolos';
import { ServiciosContext, type Servicios } from '../../src/servicios/contexto';
import type { AlmacenFotos, SelectorFotos } from '../../src/servicios/fotos';
import { TEXTOS } from '../../src/servicios/textos';
import { abrirDbNode } from './dbNode';

export class SelectorFalso implements SelectorFotos {
  ruta: string | null = null;
  ultimaCamara: boolean | null = null;
  async elegir({ camara }: { camara: boolean }) {
    this.ultimaCamara = camara;
    return this.ruta;
  }
}

/** Almacén sin disco: el acceso real a archivos se prueba en servicios.test.ts. */
export class AlmacenFalso implements AlmacenFotos {
  guardadas: string[] = [];
  eliminadas: string[] = [];
  async guardar(origen: string) {
    this.guardadas.push(origen);
    return `/privado/fotos_privadas/f_${this.guardadas.length}.jpg`;
  }
  async eliminar(ruta: string) {
    this.eliminadas.push(ruta);
  }
}

export interface Entorno {
  servicios: Servicios;
  selector: SelectorFalso;
  almacen: AlmacenFalso;
  compartidos: string[];
  archivos: Record<string, string>;
  repo: Repositorio;
  router: Record<'push' | 'replace' | 'back' | 'dismissAll', jest.Mock>;
}

export async function crearEntorno(hoy = new Date(2026, 5, 10)): Promise<Entorno> {
  const db = abrirDbNode();
  await migrar(db);
  const repo = new Repositorio(db, () => hoy);
  const selector = new SelectorFalso();
  const almacen = new AlmacenFalso();
  const compartidos: string[] = [];
  const archivos: Record<string, string> = {};
  const servicios: Servicios = {
    repo,
    protocolos: PROTOCOLOS,
    textos: TEXTOS,
    selectorFotos: selector,
    almacenFotos: almacen,
    instalacionId: 'ABC123',
    compartir: async (ruta) => void compartidos.push(ruta),
    escribirArchivo: async (nombre, contenido) => {
      archivos[`/tmp/${nombre}`] = contenido;
      return `/tmp/${nombre}`;
    },
    ahora: () => hoy,
    cifrada: true,
  };
   
  const router = require('expo-router').__router;
  Object.values(router as Record<string, jest.Mock>).forEach((f) => f.mockClear());
  return { servicios, selector, almacen, compartidos, archivos, repo, router };
}

export async function mostrar(e: Entorno, pantalla: ReactElement) {
  return render(<ServiciosContext.Provider value={e.servicios}>{pantalla}</ServiciosContext.Provider>);
}
