import type { Db, Param, RunResult } from '../../src/data/db';

/**
 * Implementa `Db` sobre SQLite real de Node (`node:sqlite`) para probar el repositorio y las migraciones.
 * Se carga con getBuiltinModule porque el resolvedor de Jest no conoce los módulos que solo existen con prefijo `node:`.
 */
export function abrirDbNode(archivo = ':memory:'): Db & { cerrar(): void } {
  const { DatabaseSync } = (process as unknown as { getBuiltinModule(n: string): typeof import('node:sqlite') }).getBuiltinModule(
    'node:sqlite',
  );
  const db = new DatabaseSync(archivo);
  const valores = (p?: Param[]) => (p ?? []) as (string | number | null)[];
  return {
    async execAsync(sql) {
      db.exec(sql);
    },
    async runAsync(sql, params): Promise<RunResult> {
      const r = db.prepare(sql).run(...valores(params));
      return { lastInsertRowId: Number(r.lastInsertRowid), changes: Number(r.changes) };
    },
    async getAllAsync<T>(sql: string, params?: Param[]) {
      return db.prepare(sql).all(...valores(params)) as T[];
    },
    async getFirstAsync<T>(sql: string, params?: Param[]) {
      return (db.prepare(sql).get(...valores(params)) as T | undefined) ?? null;
    },
    async withTransactionAsync(tarea) {
      db.exec('BEGIN');
      try {
        await tarea();
        db.exec('COMMIT');
      } catch (e) {
        db.exec('ROLLBACK');
        throw e;
      }
    },
    cerrar() {
      db.close();
    },
  };
}
