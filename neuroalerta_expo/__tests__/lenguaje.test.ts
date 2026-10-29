import * as fs from 'node:fs';
import * as path from 'node:path';

import { PROTOCOLOS } from '../src/domain/protocolos';
import { TEXTOS } from '../src/servicios/textos';

// Regla 1 del encargo: ninguna pantalla presenta estas palabras como conclusión. Se revisa también el código y los comentarios.
const PROHIBIDAS = /diagn[oó]stic|autis|\bTEA\b|\bTDAH\b/i;

function archivos(dir: string, ext: RegExp): string[] {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((d) => {
    const ruta = path.join(dir, d.name);
    return d.isDirectory() ? archivos(ruta, ext) : ext.test(d.name) ? [ruta] : [];
  });
}

describe('lenguaje para las familias', () => {
  it('protocolos y textos no usan palabras de conclusión clínica', () => {
    const textos: string[] = [];
    for (const p of Object.values(PROTOCOLOS)) {
      textos.push(...p.items.map((i) => i.texto), ...p.focosRojos.map((f) => f.texto), ...p.areas.map((a) => a.nombre));
    }
    textos.push(JSON.stringify(TEXTOS));
    for (const t of textos) expect({ t, ok: PROHIBIDAS.test(t) }).toEqual({ t, ok: false });
  });

  it('el código de la aplicación y los archivos de textos tampoco las contienen', () => {
    const lista = [
      ...archivos('src', /\.(ts|tsx)$/),
      ...archivos('assets/textos', /\.json$/),
      ...archivos('assets/protocolos', /\.json$/).filter((f) => !f.endsWith('.json')), // los protocolos se revisan arriba
      'app.json',
      'app.config.js',
    ];
    for (const f of lista) {
      expect({ f, ok: PROHIBIDAS.test(fs.readFileSync(f, 'utf8')) }).toEqual({ f, ok: false });
    }
  });

  it('el aviso obligatorio está tal cual en los textos editables', () => {
    expect(TEXTOS.aviso).toBe('Esta orientación no reemplaza la evaluación de un profesional de salud.');
    for (const n of ['sin_senales', 'comentar_control', 'consultar_pronto'] as const) {
      expect(TEXTOS.niveles[n].titulo.length).toBeGreaterThan(0);
    }
  });
});

describe('configuración de privacidad de Android', () => {
  const app = JSON.parse(fs.readFileSync('app.json', 'utf8')).expo;

  it('desactiva la copia de seguridad, bloquea permisos innecesarios y pide SQLCipher', () => {
    expect(app.android.allowBackup).toBe(false);
    expect(app.android.blockedPermissions).toEqual(
      expect.arrayContaining(['android.permission.RECORD_AUDIO', 'android.permission.READ_EXTERNAL_STORAGE', 'android.permission.WRITE_EXTERNAL_STORAGE']),
    );
    const sqlite = app.plugins.find((p: unknown) => Array.isArray(p) && p[0] === 'expo-sqlite');
    expect(sqlite?.[1]).toEqual({ useSQLCipher: true });
    const picker = app.plugins.find((p: unknown) => Array.isArray(p) && p[0] === 'expo-image-picker');
    expect(picker?.[1].microphonePermission).toBe(false);
  });

  it('la versión sin internet quita el permiso de red', () => {
     
    const configurar = require('../app.config.js');
    process.env.SIN_INTERNET = '1';
    try {
      expect(configurar({ config: app }).android.blockedPermissions).toContain('android.permission.INTERNET');
    } finally {
      delete process.env.SIN_INTERNET;
    }
    expect(configurar({ config: app }).android.blockedPermissions).not.toContain('android.permission.INTERNET');
  });
});
