/** Grupos de edad que cubre el piloto. */
export type TramoId = '0_36' | '3_6' | '7_12';

export const ETIQUETA_TRAMO: Record<TramoId, string> = {
  '0_36': '0 a 36 meses',
  '3_6': '3 a 6 años',
  '7_12': '7 a 12 años',
};

/** Devuelve el tramo para una edad en meses, o null si queda fuera del piloto. */
export function tramoDesdeEdadMeses(meses: number): TramoId | null {
  if (meses < 0) return null;
  if (meses <= 36) return '0_36';
  if (meses < 84) return '3_6';
  if (meses < 156) return '7_12';
  return null;
}

/** Edad completa en meses entre `nacimiento` y `hoy`. */
export function edadEnMeses(nacimiento: Date, hoy: Date): number {
  let meses = (hoy.getFullYear() - nacimiento.getFullYear()) * 12 + (hoy.getMonth() - nacimiento.getMonth());
  if (hoy.getDate() < nacimiento.getDate()) meses -= 1;
  return meses;
}
