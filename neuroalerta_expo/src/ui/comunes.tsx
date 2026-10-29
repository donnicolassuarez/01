import type { ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View, type ViewStyle } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useServicios } from '../servicios/contexto';
import { colores, espacio, MIN_TOQUE } from './tema';

export const NOMBRE_APP = 'NeuroAlerta Kids';

/** Recuadro con el aviso de orientación, presente en bienvenida y resultados. */
export function AvisoOrientacion() {
  const { textos } = useServicios();
  return (
    <View testID="aviso_orientacion" style={estilos.aviso} accessibilityRole="summary">
      <Text style={estilos.avisoTexto}>{textos.aviso}</Text>
    </View>
  );
}

/** Pantalla con zona desplazable y un pie fijo opcional (para botones y avisos que no deben quedar ocultos). */
export function Pantalla({ children, pie }: { children: ReactNode; pie?: ReactNode }) {
  const { cifrada } = useServicios();
  return (
    <SafeAreaView style={estilos.fondo} edges={['bottom', 'left', 'right']}>
      {!cifrada && (
        <Text style={estilos.banda} testID="banda_sin_cifrar">
          Modo de desarrollo: la base no está cifrada
        </Text>
      )}
      <ScrollView contentContainerStyle={estilos.contenido} keyboardShouldPersistTaps="handled">
        {children}
      </ScrollView>
      {pie ? <View style={estilos.pie}>{pie}</View> : null}
    </SafeAreaView>
  );
}

export function Titulo({ children, nivel = 1 }: { children: ReactNode; nivel?: 1 | 2 | 3 }) {
  return (
    <Text accessibilityRole="header" style={[estilos.tituloBase, nivel === 1 ? estilos.t1 : nivel === 2 ? estilos.t2 : estilos.t3]}>
      {children}
    </Text>
  );
}

export function Parrafo({ children, suave, centrado }: { children: ReactNode; suave?: boolean; centrado?: boolean }) {
  return <Text style={[estilos.parrafo, suave && { color: colores.textoSuave }, centrado && { textAlign: 'center' }]}>{children}</Text>;
}

export function Punto({ children }: { children: ReactNode }) {
  return (
    <View style={estilos.punto}>
      <Text style={estilos.parrafo}>{'•  '}</Text>
      <Text style={[estilos.parrafo, { flex: 1 }]}>{children}</Text>
    </View>
  );
}

interface PropsBoton {
  etiqueta: string;
  onPress?: () => void;
  deshabilitado?: boolean;
  /** `principal` = relleno, `secundario` = con borde, `texto` = sin marco. */
  variante?: 'principal' | 'secundario' | 'texto';
  testID?: string;
  estilo?: ViewStyle;
}

export function Boton({ etiqueta, onPress, deshabilitado, variante = 'principal', testID, estilo }: PropsBoton) {
  const principal = variante === 'principal';
  return (
    <Pressable
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={etiqueta}
      accessibilityState={{ disabled: !!deshabilitado }}
      disabled={deshabilitado}
      onPress={onPress}
      style={({ pressed }) => [
        estilos.boton,
        principal && estilos.botonPrincipal,
        variante === 'secundario' && estilos.botonSecundario,
        variante === 'texto' && { borderWidth: 0, minHeight: 44 },
        deshabilitado && { opacity: 0.45 },
        pressed && { opacity: 0.8 },
        estilo,
      ]}
    >
      <Text style={[estilos.botonTexto, principal && { color: colores.sobrePrimario }]}>{etiqueta}</Text>
    </Pressable>
  );
}

export function Casilla({
  marcada,
  onCambio,
  etiqueta,
  testID,
  deshabilitada,
}: {
  marcada: boolean;
  onCambio: (v: boolean) => void;
  etiqueta: string;
  testID?: string;
  deshabilitada?: boolean;
}) {
  return (
    <Pressable
      testID={testID}
      accessibilityRole="checkbox"
      accessibilityState={{ checked: marcada, disabled: !!deshabilitada }}
      disabled={deshabilitada}
      onPress={() => onCambio(!marcada)}
      style={estilos.casilla}
    >
      <View style={[estilos.cajaCasilla, marcada && { backgroundColor: colores.primario }]}>
        {marcada ? <Text style={estilos.marca}>✓</Text> : null}
      </View>
      <Text style={[estilos.parrafo, { flex: 1 }]}>{etiqueta}</Text>
    </Pressable>
  );
}

export function fechaCorta(d: Date): string {
  const dos = (n: number) => String(n).padStart(2, '0');
  return `${dos(d.getDate())}/${dos(d.getMonth() + 1)}/${d.getFullYear()}`;
}

const estilos = StyleSheet.create({
  fondo: { flex: 1, backgroundColor: colores.fondo },
  contenido: { padding: espacio.xl, paddingBottom: espacio.xl, gap: espacio.m },
  pie: { padding: espacio.l, gap: espacio.s, borderTopWidth: 1, borderTopColor: colores.borde, backgroundColor: colores.superficie },
  banda: { backgroundColor: colores.error, color: '#FFFFFF', textAlign: 'center', padding: espacio.xs, fontSize: 13 },
  aviso: { backgroundColor: colores.aviso, borderRadius: 12, padding: espacio.l },
  avisoTexto: { color: colores.sobreAviso, fontSize: 15, lineHeight: 21 },
  tituloBase: { color: colores.texto, fontWeight: '700' },
  t1: { fontSize: 26, lineHeight: 32 },
  t2: { fontSize: 21, lineHeight: 27 },
  t3: { fontSize: 17, lineHeight: 23 },
  parrafo: { color: colores.texto, fontSize: 17, lineHeight: 24 },
  punto: { flexDirection: 'row', paddingVertical: 2 },
  boton: {
    minHeight: MIN_TOQUE,
    borderRadius: 12,
    paddingHorizontal: espacio.l,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colores.primario,
    backgroundColor: colores.superficie,
  },
  botonPrincipal: { backgroundColor: colores.primario },
  botonSecundario: { backgroundColor: colores.superficie },
  botonTexto: { color: colores.primario, fontSize: 17, fontWeight: '600', textAlign: 'center' },
  casilla: { flexDirection: 'row', alignItems: 'center', gap: espacio.m, minHeight: MIN_TOQUE, paddingVertical: espacio.xs },
  cajaCasilla: {
    width: 28,
    height: 28,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: colores.primario,
    alignItems: 'center',
    justifyContent: 'center',
  },
  marca: { color: '#FFFFFF', fontSize: 18, fontWeight: '700' },
});
