import type { Db } from './db';

/**
 * Migraciones en orden. Cada una lleva la base de la versión `n-1` a la `n`.
 * Nunca se edita una migración ya publicada: se agrega una nueva al final.
 */
export const MIGRACIONES: readonly string[] = [
  `
  CREATE TABLE ninos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    fecha_nacimiento INTEGER NOT NULL,
    tramo TEXT NOT NULL,
    creado_en INTEGER NOT NULL
  );
  CREATE TABLE consentimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_texto TEXT NOT NULL,
    aceptado_en INTEGER NOT NULL
  );
  CREATE TABLE sesiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nino_id INTEGER NOT NULL REFERENCES ninos(id),
    tramo TEXT NOT NULL,
    edad_meses INTEGER NOT NULL,
    version_protocolo TEXT NOT NULL,
    iniciada_en INTEGER NOT NULL,
    cerrada_en INTEGER,
    focos_marcados TEXT NOT NULL DEFAULT ''
  );
  CREATE TABLE respuestas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id INTEGER NOT NULL REFERENCES sesiones(id),
    item_id TEXT NOT NULL,
    opcion TEXT NOT NULL,
    puntos INTEGER,
    UNIQUE (sesion_id, item_id)
  );
  CREATE TABLE resultados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id INTEGER NOT NULL UNIQUE REFERENCES sesiones(id),
    puntajes_por_area TEXT NOT NULL,
    puntos_total INTEGER NOT NULL,
    maximo_total INTEGER NOT NULL,
    no_se INTEGER NOT NULL,
    nivel TEXT NOT NULL,
    focos_rojos TEXT NOT NULL DEFAULT '',
    version_protocolo TEXT NOT NULL,
    estado_protocolo TEXT NOT NULL,
    creado_en INTEGER NOT NULL
  );
  CREATE TABLE fotos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nino_id INTEGER NOT NULL REFERENCES ninos(id),
    ruta TEXT NOT NULL,
    fecha INTEGER NOT NULL,
    nota TEXT NOT NULL DEFAULT ''
  );
  `,
];

export const VERSION_ESQUEMA = MIGRACIONES.length;

/** Lleva la base a la versión actual del esquema. Es seguro llamarla en cada arranque. */
export async function migrar(db: Db, migraciones: readonly string[] = MIGRACIONES): Promise<void> {
  await db.execAsync('PRAGMA foreign_keys = ON;');
  const fila = await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version;');
  const actual = fila?.user_version ?? 0;
  if (actual > migraciones.length) {
    throw new Error(`La base es de una versión más nueva (${actual}) que la de la app (${migraciones.length}).`);
  }
  for (let v = actual; v < migraciones.length; v += 1) {
    await db.withTransactionAsync(async () => {
      await db.execAsync(migraciones[v]);
      await db.execAsync(`PRAGMA user_version = ${v + 1};`);
    });
  }
}
