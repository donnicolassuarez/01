import { migrar, MIGRACIONES, VERSION_ESQUEMA } from '../src/data/esquema';
import { ConsentimientoRequerido, EdadFueraDeRango, Repositorio } from '../src/data/repositorio';
import { evaluar } from '../src/domain/motor';
import { PROTOCOLOS } from '../src/domain/protocolos';
import { abrirDbNode } from './ayudas/dbNode';

const hoy = new Date(2026, 5, 10);
const p36 = PROTOCOLOS['3_6'];

async function nuevoRepo() {
  const db = abrirDbNode();
  await migrar(db);
  return { db, repo: new Repositorio(db, () => hoy) };
}

describe('consentimiento', () => {
  it('sin consentimiento no se guarda ningún dato', async () => {
    const { repo } = await nuevoRepo();
    await expect(repo.crearNino({ codigo: 'luz', fechaNacimiento: new Date(2022, 0, 1) })).rejects.toBeInstanceOf(
      ConsentimientoRequerido,
    );
    expect(await repo.listarNinos()).toEqual([]);
  });

  it('registra versión y fecha de aceptación', async () => {
    const { repo } = await nuevoRepo();
    expect(await repo.consentimientoVigente('1.0')).toBeNull();
    await repo.registrarConsentimiento('1.0');
    const c = await repo.consentimientoVigente('1.0');
    expect(c?.aceptadoEn).toEqual(hoy);
    expect(await repo.consentimientoVigente('2.0')).toBeNull();
  });

  it('las fotos y las respuestas tampoco se guardan sin consentimiento', async () => {
    const { repo } = await nuevoRepo();
    await expect(repo.agregarFoto({ ninoId: 1, ruta: '/x.jpg', fecha: hoy })).rejects.toBeInstanceOf(ConsentimientoRequerido);
    await expect(repo.guardarRespuesta({ sesionId: 1, item: p36.items[0], opcion: 'a_veces' })).rejects.toBeInstanceOf(
      ConsentimientoRequerido,
    );
  });
});

describe('niños', () => {
  it('calcula el tramo según la edad', async () => {
    const { repo } = await nuevoRepo();
    await repo.registrarConsentimiento('1.0');
    const a = await repo.crearNino({ codigo: 'A', fechaNacimiento: new Date(2025, 5, 10) });
    const b = await repo.crearNino({ codigo: 'B', fechaNacimiento: new Date(2022, 0, 1) });
    const c = await repo.crearNino({ codigo: 'C', fechaNacimiento: new Date(2017, 2, 1) });
    expect([a.tramo, b.tramo, c.tramo]).toEqual(['0_36', '3_6', '7_12']);
  });

  it('rechaza edades fuera de rango y recorta el código', async () => {
    const { repo } = await nuevoRepo();
    await repo.registrarConsentimiento('1.0');
    await expect(repo.crearNino({ codigo: 'M', fechaNacimiento: new Date(2010, 0, 1) })).rejects.toBeInstanceOf(EdadFueraDeRango);
    await expect(repo.crearNino({ codigo: 'F', fechaNacimiento: new Date(2027, 0, 1) })).rejects.toBeInstanceOf(EdadFueraDeRango);
    const n = await repo.crearNino({ codigo: '  Peque 1  ', fechaNacimiento: new Date(2022, 0, 1) });
    expect(n.codigo).toBe('Peque 1');
  });
});

describe('sesión completa', () => {
  it('guarda avance, retoma la sesión y cierra con resultado versionado', async () => {
    const { repo } = await nuevoRepo();
    await repo.registrarConsentimiento('1.0');
    const nino = await repo.crearNino({ codigo: 'Luz', fechaNacimiento: new Date(2022, 0, 1) });

    const s = await repo.iniciarOReanudarSesion({ nino, protocolo: p36 });
    expect(s.versionProtocolo).toBe(p36.version);
    await repo.guardarRespuesta({ sesionId: s.id, item: p36.items[0], opcion: 'casi_siempre' });
    await repo.guardarRespuesta({ sesionId: s.id, item: p36.items[1], opcion: 'no_se' });
    await repo.guardarRespuesta({ sesionId: s.id, item: p36.items[0], opcion: 'a_veces' });
    await repo.guardarFocos(s.id, ['f03', 'f02', 'f02']);

    const otra = await repo.iniciarOReanudarSesion({ nino, protocolo: p36 });
    expect(otra.id).toBe(s.id);
    const resp = await repo.respuestasDe(s.id);
    expect(resp).toEqual({ [p36.items[0].id]: 'a_veces', [p36.items[1].id]: 'no_se' });
    const abierta = await repo.sesion(s.id);
    expect(abierta.focosMarcados).toEqual(['f02', 'f03']);

    const r = evaluar({ protocolo: p36, edadMeses: s.edadMeses, respuestas: resp, focosMarcados: abierta.focosMarcados });
    const guardado = await repo.cerrarSesion(s.id, r);
    expect(guardado.versionProtocolo).toBe(p36.version);
    expect(guardado.estadoProtocolo).toBe('provisional');
    expect(guardado.nivel).toBe(r.nivel);
    expect(guardado.focosRojos).toEqual(r.focosRojos);

    const h = await repo.historial(nino.id);
    expect(h).toHaveLength(1);
    expect(h[0].resultado?.sesionId).toBe(s.id);
    expect(h[0].sesion.cerradaEn).toEqual(hoy);

    const nueva = await repo.iniciarOReanudarSesion({ nino, protocolo: p36 });
    expect(nueva.id).not.toBe(s.id);
  });

  it('el puntaje de cada respuesta se guarda; "No sé" queda sin puntos', async () => {
    const { db, repo } = await nuevoRepo();
    await repo.registrarConsentimiento('1.0');
    const nino = await repo.crearNino({ codigo: 'Luz', fechaNacimiento: new Date(2022, 0, 1) });
    const s = await repo.iniciarOReanudarSesion({ nino, protocolo: p36 });
    await repo.guardarRespuesta({ sesionId: s.id, item: p36.items[0], opcion: 'a_veces' });
    await repo.guardarRespuesta({ sesionId: s.id, item: p36.items[1], opcion: 'no_se' });
    const filas = await db.getAllAsync<{ item_id: string; puntos: number | null }>('SELECT item_id, puntos FROM respuestas ORDER BY id');
    expect(filas).toEqual([
      { item_id: p36.items[0].id, puntos: 1 },
      { item_id: p36.items[1].id, puntos: null },
    ]);
  });

  it('fotos: agregar, listar y eliminar', async () => {
    const { repo } = await nuevoRepo();
    await repo.registrarConsentimiento('1.0');
    const nino = await repo.crearNino({ codigo: 'Luz', fechaNacimiento: new Date(2022, 0, 1) });
    const f = await repo.agregarFoto({ ninoId: nino.id, ruta: '/privado/a.jpg', fecha: hoy, nota: ' juego ' });
    expect(f.nota).toBe('juego');
    expect(await repo.fotosDe(nino.id)).toHaveLength(1);
    await repo.eliminarFoto(f.id);
    expect(await repo.fotosDe(nino.id)).toEqual([]);
  });

  it('las claves foráneas están activas', async () => {
    const { db } = await nuevoRepo();
    await expect(
      db.runAsync('INSERT INTO fotos (nino_id, ruta, fecha) VALUES (?, ?, ?)', [999, '/x.jpg', 0]),
    ).rejects.toThrow(/FOREIGN KEY/i);
  });
});

describe('migraciones del esquema', () => {
  it('una base nueva queda en la versión actual y migrar es idempotente', async () => {
    const db = abrirDbNode();
    await migrar(db);
    await migrar(db);
    const v = await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version');
    expect(v?.user_version).toBe(VERSION_ESQUEMA);
    const tablas = await db.getAllAsync<{ name: string }>("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name");
    expect(tablas.map((t) => t.name)).toEqual(['consentimientos', 'fotos', 'ninos', 'respuestas', 'resultados', 'sesiones']);
  });

  it('una migración nueva conserva los datos existentes', async () => {
    const db = abrirDbNode();
    await migrar(db);
    await db.runAsync('INSERT INTO ninos (codigo, fecha_nacimiento, tramo, creado_en) VALUES (?, ?, ?, ?)', ['A', 0, '3_6', 0]);
    const v2 = [...MIGRACIONES, 'ALTER TABLE ninos ADD COLUMN apodo TEXT;'];
    await migrar(db, v2);
    const fila = await db.getFirstAsync<{ codigo: string; apodo: string | null }>('SELECT codigo, apodo FROM ninos');
    expect(fila).toEqual({ codigo: 'A', apodo: null });
    expect((await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))?.user_version).toBe(2);
  });

  it('una migración que falla no deja la base a medias', async () => {
    const db = abrirDbNode();
    await migrar(db);
    const rota = [...MIGRACIONES, 'ALTER TABLE ninos ADD COLUMN x TEXT; ALTER TABLE tabla_inexistente ADD COLUMN y TEXT;'];
    await expect(migrar(db, rota)).rejects.toThrow();
    const cols = await db.getAllAsync<{ name: string }>('PRAGMA table_info(ninos)');
    expect(cols.map((c) => c.name)).not.toContain('x');
    expect((await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version'))?.user_version).toBe(1);
  });

  it('rechaza una base de versión más nueva que la de la app', async () => {
    const db = abrirDbNode();
    await db.execAsync('PRAGMA user_version = 9;');
    await expect(migrar(db)).rejects.toThrow(/más nueva/);
  });
});
