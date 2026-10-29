import { StyleSheet, Text, TextInput, View } from 'react-native';

import { colores, espacio } from './tema';

export interface FechaCampos {
  dia: string;
  mes: string;
  anio: string;
}

export const FECHA_VACIA: FechaCampos = { dia: '', mes: '', anio: '' };

export function camposDesdeFecha(d: Date): FechaCampos {
  return { dia: String(d.getDate()), mes: String(d.getMonth() + 1), anio: String(d.getFullYear()) };
}

/** Devuelve la fecha si los campos forman una fecha real que no es futura; si no, null. */
export function fechaDesdeCampos(c: FechaCampos, hoy: Date): Date | null {
  if (!/^\d{1,2}$/.test(c.dia) || !/^\d{1,2}$/.test(c.mes) || !/^\d{4}$/.test(c.anio)) return null;
  const d = Number(c.dia);
  const m = Number(c.mes);
  const a = Number(c.anio);
  const fecha = new Date(a, m - 1, d);
  if (fecha.getFullYear() !== a || fecha.getMonth() !== m - 1 || fecha.getDate() !== d) return null;
  const finDeHoy = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate(), 23, 59, 59);
  return fecha.getTime() > finDeHoy.getTime() ? null : fecha;
}

/** Tres casillas numéricas (día, mes, año): simple, accesible y sin componentes nativos adicionales. */
export function CampoFecha({
  valor,
  onCambio,
  etiqueta,
  prefijoId,
}: {
  valor: FechaCampos;
  onCambio: (v: FechaCampos) => void;
  etiqueta: string;
  prefijoId: string;
}) {
  const campo = (k: keyof FechaCampos, nombre: string, largo: number, ancho: number) => (
    <View style={{ width: ancho }}>
      <Text style={estilos.sub}>{nombre}</Text>
      <TextInput
        testID={`${prefijoId}_${k}`}
        accessibilityLabel={`${etiqueta}: ${nombre}`}
        keyboardType="number-pad"
        maxLength={largo}
        value={valor[k]}
        onChangeText={(t) => onCambio({ ...valor, [k]: t.replace(/\D/g, '') })}
        style={estilos.entrada}
      />
    </View>
  );
  return (
    <View>
      <Text style={estilos.etiqueta}>{etiqueta}</Text>
      <View style={estilos.fila}>
        {campo('dia', 'Día', 2, 72)}
        {campo('mes', 'Mes', 2, 72)}
        {campo('anio', 'Año', 4, 110)}
      </View>
    </View>
  );
}

const estilos = StyleSheet.create({
  etiqueta: { color: colores.texto, fontSize: 17, fontWeight: '600', marginBottom: espacio.xs },
  sub: { color: colores.textoSuave, fontSize: 14, marginBottom: 2 },
  fila: { flexDirection: 'row', gap: espacio.m },
  entrada: {
    minHeight: 52,
    borderWidth: 1.5,
    borderColor: colores.borde,
    borderRadius: 10,
    paddingHorizontal: espacio.m,
    fontSize: 18,
    color: colores.texto,
    backgroundColor: colores.superficie,
  },
});
