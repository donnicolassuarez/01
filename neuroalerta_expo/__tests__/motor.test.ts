import { evaluar } from '../src/domain/motor';
import { PROTOCOLOS } from '../src/domain/protocolos';
import {
  focosPara,
  itemsPara,
  parsearProtocolo,
  type Opcion,
  type Protocolo,
} from '../src/domain/protocolo';
import { edadEnMeses, tramoDesdeEdadMeses } from '../src/domain/tramo';

const p036 = PROTOCOLOS['0_36'];
const p36 = PROTOCOLOS['3_6'];
const p712 = PROTOCOLOS['7_12'];

const todas = (p: Protocolo, edad: number, o: Opcion): Record<string, Opcion> =>
  Object.fromEntries(itemsPara(p, edad).map((i) => [i.id, o]));

describe('tramos y edad', () => {
  it('límites de tramo', () => {
    expect(tramoDesdeEdadMeses(0)).toBe('0_36');
    expect(tramoDesdeEdadMeses(36)).toBe('0_36');
    expect(tramoDesdeEdadMeses(37)).toBe('3_6');
    expect(tramoDesdeEdadMeses(83)).toBe('3_6');
    expect(tramoDesdeEdadMeses(84)).toBe('7_12');
    expect(tramoDesdeEdadMeses(155)).toBe('7_12');
    expect(tramoDesdeEdadMeses(156)).toBeNull();
    expect(tramoDesdeEdadMeses(-1)).toBeNull();
  });

  it('edad en meses completos', () => {
    expect(edadEnMeses(new Date(2024, 0, 15), new Date(2026, 0, 14))).toBe(23);
    expect(edadEnMeses(new Date(2024, 0, 15), new Date(2026, 0, 15))).toBe(24);
    expect(edadEnMeses(new Date(2020, 4, 31), new Date(2026, 4, 30))).toBe(71);
  });
});

describe('protocolos', () => {
  it.each([p036, p36, p712])('$tramo: bien formado y provisional', (p) => {
    expect(p.estado).toBe('provisional');
    expect(p.version).toContain('provisional');
    const ids = p.items.map((i) => i.id);
    expect(new Set(ids).size).toBe(ids.length);
    const areas = new Set(p.areas.map((a) => a.id));
    expect(p.items.every((i) => areas.has(i.areaId))).toBe(true);
    expect(p.items.every((i) => i.puntos.casi_siempre === 2 && i.puntos.a_veces === 1 && i.puntos.casi_nunca === 0)).toBe(true);
    expect(p.items.some((i) => 'no_se' in i.puntos)).toBe(false);
    expect(p.focosRojos.some((f) => f.grave)).toBe(true);
  });

  it('0 a 36 meses no incluye áreas de atención ni hiperactividad', () => {
    expect(p036.areas.map((a) => a.id)).toEqual(['comunicacion', 'interaccion', 'conductas']);
  });

  it('0 a 36: alineado con constructos del M-CHAT-R/F, sin heredar su validez', () => {
    const alineados = p036.items.filter((i) => i.afinMchat);
    expect(alineados.length).toBeGreaterThanOrEqual(14);
    const constructos = alineados.map((i) => i.afinMchat);
    expect(constructos).toEqual(
      expect.arrayContaining([
        'Respuesta al nombre',
        'Señalar para pedir',
        'Señalar para compartir interés',
        'Seguir el señalamiento del adulto',
        'Juego simbólico',
        'Referencia social',
        'Imitación',
        'Contacto visual',
      ]),
    );
    expect(new Set(constructos).size).toBe(alineados.length);
    expect(p36.items.every((i) => !i.afinMchat)).toBe(true);
    expect(p712.items.every((i) => !i.afinMchat)).toBe(true);
     
    expect(JSON.stringify(require('../assets/protocolos/protocolo_0_36.json'))).toContain('NO es el M-CHAT-R/F');
    expect(p036.version).toBe('0.2.0-provisional');
  });

  it('0 a 36: las preguntas se filtran por edad', () => {
    const ids = (e: number) => itemsPara(p036, e).map((i) => i.id);
    expect(ids(6)).toEqual(expect.arrayContaining(['c09', 's01', 's02']));
    expect(ids(6)).not.toContain('c02');
    expect(ids(12)).toEqual(expect.arrayContaining(['c02', 'c06', 'c07', 's07']));
    expect(ids(12)).not.toContain('c08');
    expect(ids(15)).not.toContain('c08');
    expect(ids(20)).toHaveLength(p036.items.length);
  });

  it('el lector rechaza protocolos mal formados', () => {
    const base = JSON.parse(JSON.stringify(require('../assets/protocolos/protocolo_3_6.json')));  
    const conAreaInexistente = { ...base, items: [{ ...base.items[0], area: 'otra' }, ...base.items.slice(1)] };
    expect(() => parsearProtocolo(conAreaInexistente)).toThrow(/área inexistente/);
    const noSeSuma = { ...base, items: [{ ...base.items[0], valores: { ...base.items[0].valores, no_se: 1 } }, ...base.items.slice(1)] };
    expect(() => parsearProtocolo(noSeSuma)).toThrow(/No sé/);
    const repetido = { ...base, items: [base.items[0], base.items[0]] };
    expect(() => parsearProtocolo(repetido)).toThrow(/repetidos/);
    expect(() => parsearProtocolo({ ...base, tramo: '9_99' })).toThrow(/tramo/);
    expect(() => parsearProtocolo(null)).toThrow();
  });
});

describe('motor', () => {
  it('todo "casi nunca": sin señales', () => {
    const r = evaluar({ protocolo: p36, edadMeses: 50, respuestas: todas(p36, 50, 'casi_nunca') });
    expect(r.nivel).toBe('sin_senales');
    expect(r.puntosTotal).toBe(0);
    expect(r.maximoTotal).toBe(p36.items.length * 2);
  });

  it('todo "casi siempre": consultar pronto', () => {
    for (const [p, edad] of [[p036, 30], [p36, 50], [p712, 100]] as const) {
      const r = evaluar({ protocolo: p, edadMeses: edad, respuestas: todas(p, edad, 'casi_siempre') });
      expect(r.nivel).toBe('consultar_pronto');
      expect(r.puntosTotal / r.maximoTotal).toBe(1);
    }
  });

  it('todo "a veces" (50 %) y la regla por área', () => {
    expect(evaluar({ protocolo: p36, edadMeses: 50, respuestas: todas(p36, 50, 'a_veces') }).nivel).toBe('consultar_pronto');

    const respuestas = todas(p36, 50, 'casi_nunca');
    for (const id of ['c01', 'c02', 'c03']) respuestas[id] = 'casi_siempre';
    const r = evaluar({ protocolo: p36, edadMeses: 50, respuestas });
    expect(r.areas.comunicacion.puntos / r.areas.comunicacion.maximo).toBe(0.75);
    expect(r.nivel).toBe('consultar_pronto');

    respuestas.c03 = 'casi_nunca';
    const r2 = evaluar({ protocolo: p36, edadMeses: 50, respuestas });
    expect(r2.areas.comunicacion.puntos / r2.areas.comunicacion.maximo).toBe(0.5);
    expect(r2.nivel).toBe('comentar_control');
  });

  it('"No sé" no suma, no entra en el máximo y se cuenta aparte', () => {
    const resp = todas(p36, 50, 'casi_nunca');
    resp.c01 = 'no_se';
    resp.c02 = 'no_se';
    const r = evaluar({ protocolo: p36, edadMeses: 50, respuestas: resp });
    expect(r.noSe).toBe(2);
    expect(r.areas.comunicacion.noSe).toBe(2);
    expect(r.areas.comunicacion.respondidas).toBe(2);
    expect(r.maximoTotal).toBe((p36.items.length - 2) * 2);
    expect(r.respondidas).toBe(p36.items.length - 2);
  });

  it('muchas respuestas "No sé" activan la advertencia', () => {
    const r = evaluar({ protocolo: p36, edadMeses: 50, respuestas: todas(p36, 50, 'no_se') });
    expect(r.muchosNoSe).toBe(true);
    expect(r.pocasRespuestas).toBe(true);
    expect(r.nivel).toBe('sin_senales');
  });

  it('foco rojo grave: consultar pronto sin esperar el puntaje', () => {
    const r = evaluar({ protocolo: p036, edadMeses: 20, respuestas: {}, focosMarcados: ['f01'] });
    expect(r.focoGrave).toBe(true);
    expect(r.nivel).toBe('consultar_pronto');
    expect(r.focosRojos).toEqual(['f01']);
    expect(r.pocasRespuestas).toBe(true);
  });

  it('un foco no grave sube a comentar en control; dos, a consultar pronto', () => {
    const base = todas(p36, 50, 'casi_nunca');
    const uno = evaluar({ protocolo: p36, edadMeses: 50, respuestas: base, focosMarcados: ['f02'] });
    expect(uno.nivel).toBe('comentar_control');
    expect(uno.focoGrave).toBe(false);
    const dos = evaluar({ protocolo: p36, edadMeses: 50, respuestas: base, focosMarcados: ['f02', 'f03'] });
    expect(dos.nivel).toBe('consultar_pronto');
  });

  it('focos se filtran por edad', () => {
    expect(focosPara(p036, 10).map((f) => f.id)).toEqual(['f01']);
    expect(focosPara(p036, 30).map((f) => f.id)).toEqual(['f01', 'f02', 'f03', 'f04']);
    const r = evaluar({ protocolo: p036, edadMeses: 10, respuestas: {}, focosMarcados: ['f03'] });
    expect(r.focosRojos).toEqual([]);
  });

  it('pocas respuestas: el puntaje solo no dispara el nivel', () => {
    const r = evaluar({
      protocolo: p36,
      edadMeses: 50,
      respuestas: { c01: 'casi_siempre', c02: 'casi_siempre', c03: 'casi_siempre' },
    });
    expect(r.pocasRespuestas).toBe(true);
    expect(r.nivel).toBe('sin_senales');
  });

  it('es determinista y registra la versión del protocolo', () => {
    const resp = { ...todas(p712, 100, 'a_veces'), a01: 'casi_siempre' as Opcion };
    const a = evaluar({ protocolo: p712, edadMeses: 100, respuestas: resp, focosMarcados: ['f03'] });
    const b = evaluar({ protocolo: p712, edadMeses: 100, respuestas: { ...resp }, focosMarcados: new Set(['f03']) });
    expect(a).toEqual(b);
    expect(a.versionProtocolo).toBe(p712.version);
    expect(a.estadoProtocolo).toBe('provisional');
  });
});
