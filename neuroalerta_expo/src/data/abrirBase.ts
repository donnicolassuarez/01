import { getRandomBytes } from 'expo-crypto';
import * as SecureStore from 'expo-secure-store';
import * as SQLite from 'expo-sqlite';

import { configurarCifrado, obtenerOCrearSecreto } from './cifrado';
import type { Db, Param } from './db';
import { migrar } from './esquema';

const NOMBRE_BASE = 'neuroalerta.db';
const SECRETO_BASE = 'clave_base_datos';
const SECRETO_INSTALACION = 'instalacion_id';

export interface BaseAbierta {
  db: Db;
  /** Falso solo en desarrollo, cuando se pidió expresamente trabajar sin cifrado (por ejemplo en Expo Go). */
  cifrada: boolean;
}

/** Adapta la base de expo-sqlite al contrato mínimo `Db` que usa el resto de la app. */
function comoDb(base: SQLite.SQLiteDatabase): Db {
  return {
    execAsync: (sql) => base.execAsync(sql),
    runAsync: (sql, params?: Param[]) => base.runAsync(sql, params ?? []),
    getAllAsync: <T>(sql: string, params?: Param[]) => base.getAllAsync<T>(sql, params ?? []),
    getFirstAsync: <T>(sql: string, params?: Param[]) => base.getFirstAsync<T>(sql, params ?? []),
    withTransactionAsync: (tarea) => base.withTransactionAsync(tarea),
  };
}

const almacen = {
  getItemAsync: (k: string) => SecureStore.getItemAsync(k),
  setItemAsync: (k: string, v: string) => SecureStore.setItemAsync(k, v),
};

/**
 * Abre la base cifrada. En una compilación de producción nunca se admite una base sin cifrar:
 * `permitirSinCifrar` solo tiene efecto si además es una compilación de desarrollo.
 */
export async function abrirBaseCifrada(permitirSinCifrar = false): Promise<BaseAbierta> {
  const base = await SQLite.openDatabaseAsync(NOMBRE_BASE);
  const db = comoDb(base);
  let cifrada = true;
  try {
    const clave = await obtenerOCrearSecreto(almacen, SECRETO_BASE, 32, getRandomBytes);
    await configurarCifrado(db, clave);
  } catch (e) {
    if (!(__DEV__ && permitirSinCifrar)) {
      await base.closeAsync();
      throw e;
    }
    cifrada = false;
  }
  await migrar(db);
  return { db, cifrada };
}

/** Identificador anónimo de esta instalación; sirve de prefijo en los códigos exportados. */
export async function obtenerInstalacionId(): Promise<string> {
  return (await obtenerOCrearSecreto(almacen, SECRETO_INSTALACION, 3, getRandomBytes)).toUpperCase();
}
