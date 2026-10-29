import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { abrirBaseCifrada, obtenerInstalacionId } from '../data/abrirBase';
import { Repositorio } from '../data/repositorio';
import { PROTOCOLOS } from '../domain/protocolos';
import { ServiciosContext, type Servicios } from '../servicios/contexto';
import { AlmacenFotosArchivos, SelectorFotosExpo } from '../servicios/fotos';
import { compartirConSelector, escribirEnTemporal } from '../servicios/sistema';
import { TEXTOS } from '../servicios/textos';
import { colores } from '../ui/tema';

// Solo en desarrollo: permite correr en Expo Go (sin SQLCipher). En una compilación final se ignora.
const PERMITIR_SIN_CIFRAR = process.env.EXPO_PUBLIC_PERMITIR_BD_SIN_CIFRAR === '1';

async function crearServicios(): Promise<Servicios> {
  const { db, cifrada } = await abrirBaseCifrada(PERMITIR_SIN_CIFRAR);
  return {
    repo: new Repositorio(db),
    protocolos: PROTOCOLOS,
    textos: TEXTOS,
    selectorFotos: new SelectorFotosExpo(),
    almacenFotos: new AlmacenFotosArchivos(),
    instalacionId: await obtenerInstalacionId(),
    compartir: compartirConSelector,
    escribirArchivo: escribirEnTemporal,
    ahora: () => new Date(),
    cifrada,
  };
}

export default function Raiz() {
  const [servicios, setServicios] = useState<Servicios | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    crearServicios().then(setServicios, (e: unknown) => setError(e instanceof Error ? e.message : 'Error desconocido'));
  }, []);

  if (error) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', padding: 24, gap: 12, backgroundColor: colores.fondo }}>
        <Text style={{ fontSize: 22, fontWeight: '700', color: colores.texto }}>No se pudo abrir la aplicación</Text>
        <Text style={{ fontSize: 17, color: colores.texto }}>
          Los datos no se pudieron abrir de forma segura, así que la aplicación no los mostrará. Cierre y vuelva a abrirla. Si
          el problema sigue, avise al equipo del proyecto.
        </Text>
        <Text style={{ fontSize: 13, color: colores.textoSuave }}>{error}</Text>
      </View>
    );
  }
  if (!servicios) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', backgroundColor: colores.fondo }}>
        <ActivityIndicator size="large" color={colores.primario} />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <ServiciosContext.Provider value={servicios}>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerStyle: { backgroundColor: colores.fondo },
            headerTintColor: colores.primario,
            headerTitleStyle: { color: colores.texto },
            headerShadowVisible: false,
            contentStyle: { backgroundColor: colores.fondo },
          }}
        >
          <Stack.Screen name="index" options={{ headerShown: false }} />
          <Stack.Screen name="bienvenida" options={{ headerShown: false }} />
          <Stack.Screen name="consentimiento" options={{ title: 'Consentimiento informado' }} />
          <Stack.Screen name="ninos" options={{ title: 'NeuroAlerta Kids', headerBackVisible: false }} />
          <Stack.Screen name="alta" options={{ title: 'Agregar niño o niña' }} />
          <Stack.Screen name="nino/[id]" options={{ title: 'Ficha' }} />
          <Stack.Screen name="cuestionario/[id]" options={{ title: 'Cuestionario' }} />
          <Stack.Screen name="resultado/[sesionId]" options={{ title: 'Orientación', headerBackVisible: false }} />
          <Stack.Screen name="historial/[id]" options={{ title: 'Historial' }} />
          <Stack.Screen name="fotos/[id]" options={{ title: 'Fotos de conductas' }} />
          <Stack.Screen name="exportacion" options={{ title: 'Exportación' }} />
        </Stack>
      </ServiciosContext.Provider>
    </SafeAreaProvider>
  );
}
