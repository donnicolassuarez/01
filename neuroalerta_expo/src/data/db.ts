/**
 * Contrato mínimo de base de datos. Coincide con la parte de `SQLiteDatabase` de expo-sqlite que usa la app,
 * de modo que el repositorio se prueba con otra implementación (node:sqlite) sin abrir el teléfono.
 */
export type Param = string | number | null;

export interface RunResult {
  lastInsertRowId: number;
  changes: number;
}

export interface Db {
  execAsync(sql: string): Promise<void>;
  runAsync(sql: string, params?: Param[]): Promise<RunResult>;
  getAllAsync<T>(sql: string, params?: Param[]): Promise<T[]>;
  getFirstAsync<T>(sql: string, params?: Param[]): Promise<T | null>;
  withTransactionAsync(tarea: () => Promise<void>): Promise<void>;
}
