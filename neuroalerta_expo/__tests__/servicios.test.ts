import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';

import { aBytesHex, configurarCifrado, obtenerOCrearSecreto, type AlmacenSecretos } from '../src/data/cifrado';
import type { Db } from '../src/data/db';
import type { FilaExportacion } from '../src/data/repositorio';
import { AlmacenFotosArchivos } from '../src/servicios/fotos';
import { campoCsv, codigoInterno, COLUMNAS_CSV, generarCsv } from '../src/servicios/exportadorCsv';

jest.mock('expo-file-system', () => require('./ayudas/fsFalso'));
jest.mock('expo-image-picker', () => ({}));

const CLAVE = 'ab'.repeat(32);

function dbFalsa(opciones: { cipherVersion?: string | null; falla?: boolean }) {
  const sentencias: string[] = [];
  const db: Db = {
    execAsync: async (sql) => void sentencias.push(sql),
    runAsync: async () => ({ lastInsertRowId: 0, changes: 0 }),
    getAllAsync: async () => [],
    getFirstAsync: async <T,>(sql: string) => {
      sentencias.push(sql);
      if (sql.includes('cipher_version')) {
        return (opciones.cipherVersion ? ({ cipher_version: opciones.cipherVersion } as T) : null);
      }
      if (opciones.falla) throw new Error('file is not a database');
      return null;
    },
    withTransactionAsync: async (t) => t(),
  };
  return { db, sentencias };
}

describe('cifrado de la base', () => {
  it('envía la clave en bruto, comprueba que hay cifrado y lee el archivo', async () => {
    const { db, sentencias } = dbFalsa({ cipherVersion: '4.6.0' });
    await configurarCifrado(db, CLAVE);
    expect(sentencias[0]).toBe(`PRAGMA key = "x'${CLAVE}'";`);
    expect(sentencias.some((s) => s.includes('cipher_version'))).toBe(true);
    expect(sentencias.some((s) => s.includes('sqlite_master'))).toBe(true);
  });

  it('falla si la compilación no tiene SQLCipher, para no guardar datos en claro', async () => {
    const { db } = dbFalsa({ cipherVersion: null });
    await expect(configurarCifrado(db, CLAVE)).rejects.toThrow(/no tiene cifrado/);
  });

  it('falla si la clave es incorrecta', async () => {
    const { db } = dbFalsa({ cipherVersion: '4.6.0', falla: true });
    await expect(configurarCifrado(db, CLAVE)).rejects.toThrow(/not a database/);
  });

  it.each(['', 'abc', `${CLAVE}0`, `${CLAVE.slice(0, 63)}"`, `x'; DROP TABLE ninos; --`])(
    'rechaza una clave con formato inválido: %p',
    async (clave) => {
      const { db, sentencias } = dbFalsa({ cipherVersion: '4.6.0' });
      await expect(configurarCifrado(db, clave)).rejects.toThrow(/formato/);
      expect(sentencias).toEqual([]);
    },
  );

  it('el secreto se crea una vez y se reutiliza', async () => {
    const guardado = new Map<string, string>();
    const almacen: AlmacenSecretos = {
      getItemAsync: async (k) => guardado.get(k) ?? null,
      setItemAsync: async (k, v) => void guardado.set(k, v),
    };
    let llamadas = 0;
    const aleatorio = (n: number) => new Uint8Array(n).fill(++llamadas);
    const a = await obtenerOCrearSecreto(almacen, 'k', 32, aleatorio);
    const b = await obtenerOCrearSecreto(almacen, 'k', 32, aleatorio);
    expect(a).toBe(b);
    expect(a).toMatch(/^[0-9a-f]{64}$/);
    expect(llamadas).toBe(1);
    expect(aBytesHex(new Uint8Array([0, 15, 255]))).toBe('000fff');
  });
});

describe('almacén privado de fotos', () => {
  let tmp: string;
  beforeEach(() => {
    tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'neuro_fotos_'));
  });
  afterEach(() => fs.rmSync(tmp, { recursive: true, force: true }));

   
  const nuevoAlmacen = (base: string) => new AlmacenFotosArchivos(new (require('expo-file-system').Directory)(base), () => 1700000000000);

  it('copia a la carpeta privada, marca la carpeta .nomedia y borra el temporal', async () => {
    const almacen = nuevoAlmacen(path.join(tmp, 'privado'));
    const origen = path.join(tmp, 'camara.JPG');
    fs.writeFileSync(origen, Buffer.from([1, 2, 3]));
    const ruta = await almacen.guardar(origen);

    expect(ruta).toBe(path.join(tmp, 'privado', 'fotos_privadas', 'f_1700000000000.jpg'));
    expect([...fs.readFileSync(ruta)]).toEqual([1, 2, 3]);
    expect(fs.existsSync(origen)).toBe(false);
    expect(fs.existsSync(path.join(tmp, 'privado', 'fotos_privadas', '.nomedia'))).toBe(true);
  });

  it('eliminar borra el archivo y tolera uno que ya no existe', async () => {
    const almacen = nuevoAlmacen(path.join(tmp, 'privado'));
    const origen = path.join(tmp, 'a.png');
    fs.writeFileSync(origen, Buffer.from([9]));
    const ruta = await almacen.guardar(origen);
    await almacen.eliminar(ruta);
    expect(fs.existsSync(ruta)).toBe(false);
    await expect(almacen.eliminar(ruta)).resolves.toBeUndefined();
  });
});

describe('CSV', () => {
  const fila: FilaExportacion = {
    ninoId: 7,
    tramo: '3_6',
    fechaSesion: new Date(2026, 2, 5, 14, 30),
    versionProtocolo: '0.1.0-provisional',
    estadoProtocolo: 'provisional',
    itemId: 'c01',
    opcion: 'a_veces',
    puntajesPorArea: {
      comunicacion: { puntos: 3, maximo: 8, respondidas: 4, no_se: 0 },
      atencion: { puntos: 0, maximo: 6, respondidas: 3, no_se: 0 },
    },
    nivel: 'comentar_control',
    focosRojos: ['f02', 'f03'],
  };

  it('columnas y valores, con prefijo de instalación y sin identificadores', () => {
    const lineas = generarCsv([fila], { instalacionId: 'A1B2C3' }).trim().split('\r\n');
    expect(lineas).toHaveLength(2);
    expect(lineas[0].split(',')).toHaveLength(COLUMNAS_CSV.length);
    expect(lineas[1]).toBe(
      'A1B2C3-N0007,3_6,2026-03-05,0.1.0-provisional,provisional,c01,a_veces,3/8,,,0/6,,comentar_control,f02;f03',
    );
  });

  it('las columnas no incluyen nombre, nacimiento, alias ni fotos', () => {
    for (const c of COLUMNAS_CSV) expect(c).not.toMatch(/nombre|alias|nacimiento|foto/);
  });

  it('escapa comas, comillas y saltos de línea', () => {
    expect(campoCsv('a,b')).toBe('"a,b"');
    expect(campoCsv('di "hola"')).toBe('"di ""hola"""');
    expect(campoCsv('uno\ndos')).toBe('"uno\ndos"');
    expect(campoCsv('simple')).toBe('simple');
  });

  it('el código seudónimo no deja ver el alias', () => {
    expect(codigoInterno('ABC123', 1)).toBe('ABC123-N0001');
    expect(generarCsv([], { instalacionId: 'X' })).toBe(`${COLUMNAS_CSV.join(',')}\r\n`);
  });
});
