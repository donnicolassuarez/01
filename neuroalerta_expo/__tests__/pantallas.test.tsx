import { fireEvent, screen } from '@testing-library/react-native';

import { itemsPara } from '../src/domain/protocolo';
import { Alta } from '../src/ui/pantallas/Alta';
import { Bienvenida } from '../src/ui/pantallas/Bienvenida';
import { Consentimiento } from '../src/ui/pantallas/Consentimiento';
import { Cuestionario } from '../src/ui/pantallas/Cuestionario';
import { Exportacion } from '../src/ui/pantallas/Exportacion';
import { Fotos } from '../src/ui/pantallas/Fotos';
import { Historial } from '../src/ui/pantallas/Historial';
import { Ninos } from '../src/ui/pantallas/Ninos';
import { Resultado } from '../src/ui/pantallas/Resultado';
import { crearEntorno, mostrar, type Entorno } from './ayudas/entorno';

jest.mock('expo-router', () => require('./ayudas/mocks').mockExpoRouter());
jest.mock('react-native-safe-area-context', () => require('react-native-safe-area-context/jest/mock').default);

const AVISO = 'Esta orientación no reemplaza la evaluación de un profesional de salud.';
const PROHIBIDAS = /diagn[oó]stic|autis|\bTEA\b|\bTDAH\b/i;

let e: Entorno;
beforeEach(async () => {
  e = await crearEntorno();
});

async function conNino(nacimiento = new Date(2022, 0, 1)) {
  await e.repo.registrarConsentimiento('1.0');
  return e.repo.crearNino({ codigo: 'Ana', fechaNacimiento: nacimiento });
}

/** Responde `veces` preguntas (por defecto las 19 del tramo de 3 a 6 años). El enrutador es falso, así que la pantalla no se reemplaza sola. */
async function responderTodo(opcion: string, veces = 19) {
  for (let n = 0; n < veces; n += 1) {
    await fireEvent.press(screen.getByTestId(`opcion_${opcion}`));
  }
}

describe('bienvenida y consentimiento', () => {
  it('la bienvenida muestra el aviso y lleva al consentimiento', async () => {
    await mostrar(e, <Bienvenida />);
    expect(screen.getByTestId('aviso_orientacion')).toBeOnTheScreen();
    expect(screen.getByText(AVISO)).toBeOnTheScreen();
    await fireEvent.press(screen.getByTestId('comenzar'));
    expect(e.router.push).toHaveBeenCalledWith('/consentimiento');
  });

  it('no se avanza sin aceptar y no se guarda nada', async () => {
    await mostrar(e, <Consentimiento />);
    const boton = screen.getByTestId('aceptar_consentimiento');
    expect(boton).toBeDisabled();
    await fireEvent.press(boton);
    expect(await e.repo.consentimientoVigente('1.0')).toBeNull();
    expect(e.router.replace).not.toHaveBeenCalled();
  });

  it('al aceptar registra versión y fecha, y pasa a la lista', async () => {
    await mostrar(e, <Consentimiento />);
    await fireEvent.press(screen.getByTestId('casilla_consentimiento'));
    await fireEvent.press(screen.getByTestId('aceptar_consentimiento'));
    expect((await e.repo.consentimientoVigente('1.0'))?.aceptadoEn).toEqual(new Date(2026, 5, 10));
    expect(e.router.replace).toHaveBeenCalledWith('/ninos');
  });
});

describe('alta de niño', () => {
  it('no acepta un nombre completo ni una fecha ausente', async () => {
    await e.repo.registrarConsentimiento('1.0');
    await mostrar(e, <Alta />);
    await fireEvent.changeText(screen.getByTestId('campo_codigo'), 'Juan Carlos Pérez Rojas');
    await fireEvent.press(screen.getByTestId('guardar_nino'));
    expect(screen.getByTestId('error_alias')).toHaveTextContent(/no el nombre completo/);
    expect(screen.getByTestId('error_fecha')).toHaveTextContent(/fecha de nacimiento válida/);
    expect(await e.repo.listarNinos()).toEqual([]);
  });

  it('rechaza una fecha que no existe o una edad fuera de rango', async () => {
    await e.repo.registrarConsentimiento('1.0');
    await mostrar(e, <Alta />);
    await fireEvent.changeText(screen.getByTestId('campo_codigo'), 'Peque 1');
    for (const [d, m, a, texto] of [
      ['31', '02', '2022', /válida/],
      ['01', '01', '2010', /entre 0 y 12/],
      ['01', '01', '2030', /válida/],
    ] as const) {
      await fireEvent.changeText(screen.getByTestId('nacimiento_dia'), d);
      await fireEvent.changeText(screen.getByTestId('nacimiento_mes'), m);
      await fireEvent.changeText(screen.getByTestId('nacimiento_anio'), a);
      await fireEvent.press(screen.getByTestId('guardar_nino'));
      expect(screen.getByTestId('error_fecha')).toHaveTextContent(texto);
    }
    expect(await e.repo.listarNinos()).toEqual([]);
  });

  it('con datos válidos muestra el grupo de edad y guarda', async () => {
    await e.repo.registrarConsentimiento('1.0');
    await mostrar(e, <Alta />);
    await fireEvent.changeText(screen.getByTestId('campo_codigo'), 'Peque 1');
    await fireEvent.changeText(screen.getByTestId('nacimiento_dia'), '15');
    await fireEvent.changeText(screen.getByTestId('nacimiento_mes'), '3');
    await fireEvent.changeText(screen.getByTestId('nacimiento_anio'), '2022');
    expect(screen.getByText('Grupo de edad: 3 a 6 años')).toBeOnTheScreen();
    await fireEvent.press(screen.getByTestId('guardar_nino'));
    const ninos = await e.repo.listarNinos();
    expect(ninos).toHaveLength(1);
    expect(ninos[0]).toMatchObject({ codigo: 'Peque 1', tramo: '3_6' });
    expect(e.router.back).toHaveBeenCalled();
  });
});

describe('lista de niños', () => {
  it('muestra los niños y lleva a la ficha y a la exportación', async () => {
    const nino = await conNino();
    await mostrar(e, <Ninos />);
    expect(await screen.findByText('Ana')).toBeOnTheScreen();
    expect(screen.getByText('3 a 6 años')).toBeOnTheScreen();
    await fireEvent.press(screen.getByTestId(`nino_${nino.id}`));
    expect(e.router.push).toHaveBeenCalledWith(`/nino/${nino.id}`);
    await fireEvent.press(screen.getByTestId('ir_exportacion'));
    expect(e.router.push).toHaveBeenCalledWith('/exportacion');
  });
});

describe('cuestionario', () => {
  it('foco rojo grave: ofrece la orientación de inmediato, sin esperar el puntaje', async () => {
    const nino = await conNino();
    await mostrar(e, <Cuestionario ninoId={nino.id} />);
    await fireEvent.press(await screen.findByTestId('foco_f01'));
    await fireEvent.press(screen.getByTestId('continuar_focos'));
    expect(screen.getByTestId('aviso_foco_grave')).toBeOnTheScreen();
    await fireEvent.press(screen.getByTestId('ver_orientacion'));

    const r = await e.repo.resultadoDe(1);
    expect(r).toMatchObject({ nivel: 'consultar_pronto', focosRojos: ['f01'], versionProtocolo: '0.1.0-provisional' });
    expect(e.router.replace).toHaveBeenCalledWith('/resultado/1');
  });

  it('foco grave: se puede seguir con las preguntas', async () => {
    const nino = await conNino();
    await mostrar(e, <Cuestionario ninoId={nino.id} />);
    await fireEvent.press(await screen.findByTestId('foco_f01'));
    await fireEvent.press(screen.getByTestId('continuar_focos'));
    await fireEvent.press(screen.getByTestId('seguir_preguntas'));
    expect(screen.getByTestId('texto_pregunta')).toBeOnTheScreen();
    expect(screen.getByText('Pregunta 1 de 19')).toBeOnTheScreen();
  });

  it('guarda el avance, se puede volver atrás y retomar', async () => {
    const nino = await conNino();
    const vista = await mostrar(e, <Cuestionario ninoId={nino.id} />);
    await fireEvent.press(await screen.findByTestId('continuar_focos'));
    await responderTodo('a_veces', 3);
    expect(screen.getByText('Pregunta 4 de 19')).toBeOnTheScreen();

    await fireEvent.press(screen.getByTestId('anterior'));
    expect(screen.getByText('Pregunta 3 de 19')).toBeOnTheScreen();
    await fireEvent.press(screen.getByTestId('opcion_no_se'));
    expect(screen.getByText('Pregunta 4 de 19')).toBeOnTheScreen();

    // Sale y vuelve: retoma en la primera sin responder.
    await vista.unmount();
    await mostrar(e, <Cuestionario ninoId={nino.id} />);
    expect(await screen.findByText('Pregunta 4 de 19')).toBeOnTheScreen();
    const guardadas = await e.repo.respuestasDe(1);
    expect(Object.keys(guardadas)).toHaveLength(3);
    expect(Object.values(guardadas).at(-1)).toBe('no_se');
  });

  it.each([
    ['casi_nunca', 'sin_senales'],
    ['casi_siempre', 'consultar_pronto'],
  ] as const)('respuestas «%s» producen el nivel %s', async (opcion, nivel) => {
    const nino = await conNino();
    await mostrar(e, <Cuestionario ninoId={nino.id} />);
    await fireEvent.press(await screen.findByTestId('continuar_focos'));
    await responderTodo(opcion);
    expect((await e.repo.resultadoDe(1))?.nivel).toBe(nivel);
    expect(e.router.replace).toHaveBeenCalledWith('/resultado/1');
  });

  it('nivel intermedio: comentar con el pediatra en el próximo control', async () => {
    const nino = await conNino();
    await mostrar(e, <Cuestionario ninoId={nino.id} />);
    await fireEvent.press(await screen.findByTestId('continuar_focos'));
    await responderTodo('a_veces', 10); // 10 de 38 puntos, sin llegar a la regla de área más alta
    await responderTodo('casi_nunca', 9);
    expect((await e.repo.resultadoDe(1))?.nivel).toBe('comentar_control');
  });

  it('un niño de 12 meses no ve preguntas ni focos de edades mayores', async () => {
    const nino = await conNino(new Date(2025, 5, 10));
    await mostrar(e, <Cuestionario ninoId={nino.id} />);
    expect(await screen.findByTestId('foco_f01')).toBeOnTheScreen();
    expect(screen.getByTestId('foco_f02')).toBeOnTheScreen();
    expect(screen.queryByTestId('foco_f03')).toBeNull();
    expect(screen.queryByTestId('foco_f04')).toBeNull();
  });
});

describe('resultado', () => {
  it.each([
    ['casi_nunca', 'Sin señales para consultar ahora'],
    ['casi_siempre', 'Conviene consultar pronto con un especialista'],
  ] as const)('«%s»: título, aviso fijo, versión y lenguaje suave', async (opcion, titulo) => {
    const nino = await conNino();
    const vista = await mostrar(e, <Cuestionario ninoId={nino.id} />);
    await fireEvent.press(await screen.findByTestId('continuar_focos'));
    await responderTodo(opcion);
    await vista.unmount();

    await mostrar(e, <Resultado sesionId={1} />);
    expect(await screen.findByText(titulo)).toBeOnTheScreen();
    expect(screen.getByText(AVISO)).toBeOnTheScreen();
    expect(screen.getByTestId('version_protocolo')).toHaveTextContent(/Versión del protocolo: 0\.1\.0-provisional/);
    const textos = screen.root ? JSON.stringify(screen.toJSON()) : '';
    expect(PROHIBIDAS.test(textos)).toBe(false);
    await fireEvent.press(screen.getByTestId('volver_inicio'));
    expect(e.router.dismissAll).toHaveBeenCalled();
  });

  it('con un foco grave lista la situación marcada y avisa que se respondieron pocas preguntas', async () => {
    const nino = await conNino();
    await mostrar(e, <Cuestionario ninoId={nino.id} />);
    await fireEvent.press(await screen.findByTestId('foco_f01'));
    await fireEvent.press(screen.getByTestId('continuar_focos'));
    await fireEvent.press(screen.getByTestId('ver_orientacion'));

    await mostrar(e, <Resultado sesionId={1} />);
    expect(await screen.findByText(/Perdió palabras/)).toBeOnTheScreen();
    expect(screen.getByText(/pocas preguntas/)).toBeOnTheScreen();
  });
});

describe('historial', () => {
  it('lista los cuestionarios completados y abre el resultado', async () => {
    const nino = await conNino();
    const vista = await mostrar(e, <Cuestionario ninoId={nino.id} />);
    await fireEvent.press(await screen.findByTestId('continuar_focos'));
    await responderTodo('casi_nunca');
    await vista.unmount();

    await mostrar(e, <Historial ninoId={nino.id} />);
    expect(await screen.findByText(/Protocolo 0\.1\.0-provisional/)).toBeOnTheScreen();
    await fireEvent.press(screen.getByTestId('sesion_1'));
    expect(e.router.push).toHaveBeenCalledWith('/resultado/1');
  });

  it('sin cuestionarios completados lo dice', async () => {
    const nino = await conNino();
    await mostrar(e, <Historial ninoId={nino.id} />);
    expect(await screen.findByText('Todavía no hay cuestionarios completados.')).toBeOnTheScreen();
  });
});

describe('fotos', () => {
  it('agregar con cámara: pasa por el almacén privado y queda registrada con su nota', async () => {
    const nino = await conNino();
    e.selector.ruta = '/cache/camara_temporal.jpg';
    await mostrar(e, <Fotos ninoId={nino.id} />);
    await fireEvent.press(await screen.findByTestId('agregar_foto'));
    await fireEvent.press(screen.getByTestId('foto_camara'));
    await fireEvent.changeText(await screen.findByTestId('nota_foto'), 'Aletea al emocionarse');
    await fireEvent.press(screen.getByTestId('guardar_foto'));

    expect(e.selector.ultimaCamara).toBe(true);
    expect(e.almacen.guardadas).toEqual(['/cache/camara_temporal.jpg']);
    const fotos = await e.repo.fotosDe(nino.id);
    expect(fotos).toHaveLength(1);
    expect(fotos[0]).toMatchObject({ ruta: '/privado/fotos_privadas/f_1.jpg', nota: 'Aletea al emocionarse' });
    expect(await screen.findByText('Aletea al emocionarse')).toBeOnTheScreen();
  });

  it('si se cancela la cámara no se guarda nada', async () => {
    const nino = await conNino();
    e.selector.ruta = null;
    await mostrar(e, <Fotos ninoId={nino.id} />);
    await fireEvent.press(await screen.findByTestId('agregar_foto'));
    await fireEvent.press(screen.getByTestId('foto_galeria'));
    expect(e.selector.ultimaCamara).toBe(false);
    expect(await e.repo.fotosDe(nino.id)).toEqual([]);
    expect(e.almacen.guardadas).toEqual([]);
  });

  it('ver, confirmar y eliminar borra el archivo y el registro', async () => {
    const nino = await conNino();
    const foto = await e.repo.agregarFoto({ ninoId: nino.id, ruta: '/privado/fotos_privadas/f_1.jpg', fecha: new Date(2026, 5, 1), nota: 'Se balancea' });
    await mostrar(e, <Fotos ninoId={nino.id} />);
    await fireEvent.press(await screen.findByTestId(`foto_${foto.id}`));
    await fireEvent.press(screen.getByTestId('eliminar_foto'));
    expect(screen.getByText('¿Eliminar esta foto?')).toBeOnTheScreen();
    await fireEvent.press(screen.getByTestId('confirmar_eliminar'));

    expect(e.almacen.eliminadas).toEqual(['/privado/fotos_privadas/f_1.jpg']);
    expect(await e.repo.fotosDe(nino.id)).toEqual([]);
    expect(await screen.findByText('Todavía no hay fotos.')).toBeOnTheScreen();
  });
});

describe('recorrido completo y exportación', () => {
  it('del consentimiento al CSV, sin identificadores', async () => {
    await mostrar(e, <Consentimiento />);
    await fireEvent.press(screen.getByTestId('casilla_consentimiento'));
    await fireEvent.press(screen.getByTestId('aceptar_consentimiento'));

    const alta = await mostrar(e, <Alta />);
    await fireEvent.changeText(screen.getByTestId('campo_codigo'), 'Peque 1');
    await fireEvent.changeText(screen.getByTestId('nacimiento_dia'), '15');
    await fireEvent.changeText(screen.getByTestId('nacimiento_mes'), '3');
    await fireEvent.changeText(screen.getByTestId('nacimiento_anio'), '2022');
    await fireEvent.press(screen.getByTestId('guardar_nino'));
    await alta.unmount();

    const q = await mostrar(e, <Cuestionario ninoId={1} />);
    await fireEvent.press(await screen.findByTestId('continuar_focos'));
    await responderTodo('casi_siempre');
    await q.unmount();

    await mostrar(e, <Exportacion />);
    await fireEvent.press(screen.getByTestId('exportar_csv'));
    expect(await screen.findByTestId('exportar_csv')).toBeOnTheScreen();

    expect(e.compartidos).toEqual(['/tmp/neuroalerta_provisional_20260610.csv']);
    const csv = e.archivos['/tmp/neuroalerta_provisional_20260610.csv'];
    const lineas = csv.trim().split('\r\n');
    expect(lineas[0]).toMatch(/^codigo_interno,tramo_edad,fecha_sesion,version_protocolo,estado_protocolo,item/);
    expect(lineas).toHaveLength(1 + itemsPara(e.servicios.protocolos['3_6'], 50).length);
    expect(lineas[1]).toMatch(/^ABC123-N0001,3_6,2026-06-10,0\.1\.0-provisional,provisional,/);
    expect(csv).not.toContain('Peque');
    expect(csv).not.toContain('2022');
    expect(csv).not.toContain('.jpg');
  });

  it('si no se puede compartir, lo avisa sin romper la pantalla', async () => {
    e.servicios.compartir = async () => {
      throw new Error('sin selector');
    };
    await mostrar(e, <Exportacion />);
    await fireEvent.press(screen.getByTestId('exportar_csv'));
    expect(await screen.findByTestId('mensaje_exportacion')).toHaveTextContent(/No se pudo generar/);
  });
});
