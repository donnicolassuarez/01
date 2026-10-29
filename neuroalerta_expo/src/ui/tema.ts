/**
 * Paleta con contraste AA (relación ≥ 4,5:1 para texto normal). El tono de «consultar pronto» es cálido y
 * sobrio a propósito: el rojo de alarma aumenta la ansiedad de las familias.
 */
export const colores = {
  primario: '#1B5E6B', // 7,3:1 sobre blanco
  sobrePrimario: '#FFFFFF',
  fondo: '#F7FAFA',
  superficie: '#FFFFFF',
  texto: '#1D2B2E',
  textoSuave: '#4A5C60',
  borde: '#C5D3D6',
  aviso: '#E3EEF0',
  sobreAviso: '#16363D',
  error: '#9A1C1C',
  nivel: {
    sin_senales: { fondo: '#E3F2EC', borde: '#8CC4AE' },
    comentar_control: { fondo: '#FFF3D1', borde: '#E3C063' },
    consultar_pronto: { fondo: '#FCE3D3', borde: '#E09A6E' },
  },
} as const;

export const espacio = { xs: 4, s: 8, m: 12, l: 16, xl: 24 } as const;
export const MIN_TOQUE = 52; // alto mínimo de los botones, en dp
