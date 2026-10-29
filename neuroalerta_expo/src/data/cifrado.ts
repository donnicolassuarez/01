import type { Db } from './db';

const CLAVE_VALIDA = /^[0-9a-f]{64}$/;

/** Almacén de secretos del sistema (en el teléfono: expo-secure-store). */
export interface AlmacenSecretos {
  getItemAsync(clave: string): Promise<string | null>;
  setItemAsync(clave: string, valor: string): Promise<void>;
}

export function aBytesHex(bytes: Uint8Array): string {
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

/** Lee un secreto del almacén seguro; si no existe, genera uno aleatorio y lo guarda. */
export async function obtenerOCrearSecreto(
  almacen: AlmacenSecretos,
  nombre: string,
  bytes: number,
  aleatorio: (n: number) => Uint8Array,
): Promise<string> {
  const existente = await almacen.getItemAsync(nombre);
  if (existente) return existente;
  const nuevo = aBytesHex(aleatorio(bytes));
  await almacen.setItemAsync(nombre, nuevo);
  return nuevo;
}

/**
 * Activa el cifrado de la conexión con una clave en bruto de 256 bits (64 caracteres hexadecimales).
 * Debe llamarse justo después de abrir la base y antes de leer o migrar nada.
 * Falla si la biblioteca de SQLite no tiene cifrado, para no guardar datos en claro sin darse cuenta.
 */
export async function configurarCifrado(db: Db, claveHex: string): Promise<void> {
  if (!CLAVE_VALIDA.test(claveHex)) throw new Error('La clave de cifrado no tiene el formato esperado.');
  // PRAGMA no admite parámetros enlazados; la clave ya se validó como hexadecimal, así que no hay inyección posible.
  await db.execAsync(`PRAGMA key = "x'${claveHex}'";`);
  const cifrado = await db.getFirstAsync<{ cipher_version: string }>('PRAGMA cipher_version;');
  if (!cifrado?.cipher_version) {
    throw new Error('La biblioteca de SQLite de esta compilación no tiene cifrado disponible.');
  }
  // Fuerza a leer el archivo: con una clave incorrecta falla aquí y no más adelante.
  await db.getFirstAsync('SELECT COUNT(*) FROM sqlite_master;');
}
