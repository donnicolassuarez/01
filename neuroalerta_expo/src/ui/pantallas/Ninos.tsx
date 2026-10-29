import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import type { Nino } from '../../data/repositorio';
import { edadEnMeses, ETIQUETA_TRAMO, tramoDesdeEdadMeses } from '../../domain/tramo';
import { useServicios } from '../../servicios/contexto';
import { AvisoOrientacion, Boton, Pantalla, Parrafo, Titulo } from '../comunes';
import { colores } from '../tema';

export function Ninos() {
  const router = useRouter();
  const { repo, ahora } = useServicios();
  const [ninos, setNinos] = useState<Nino[] | null>(null);

  useFocusEffect(
    useCallback(() => {
      let vigente = true;
      repo.listarNinos().then((l) => vigente && setNinos(l));
      return () => {
        vigente = false;
      };
    }, [repo]),
  );

  return (
    <Pantalla pie={<Boton etiqueta="Agregar niño o niña" onPress={() => router.push('/alta')} testID="agregar_nino" />}>
      <Titulo>Mis niños y niñas</Titulo>
      {ninos === null ? (
        <Parrafo suave>Cargando…</Parrafo>
      ) : ninos.length === 0 ? (
        <Parrafo suave>Todavía no hay niños ni niñas registrados. Toque «Agregar niño o niña» para empezar.</Parrafo>
      ) : (
        ninos.map((n) => {
          const t = tramoDesdeEdadMeses(edadEnMeses(n.fechaNacimiento, ahora()));
          return (
            <Pressable
              key={n.id}
              testID={`nino_${n.id}`}
              accessibilityRole="button"
              onPress={() => router.push(`/nino/${n.id}`)}
              style={{ backgroundColor: colores.superficie, borderRadius: 12, padding: 16, borderWidth: 1, borderColor: colores.borde, minHeight: 64, justifyContent: 'center' }}
            >
              <Text style={{ fontSize: 18, fontWeight: '600', color: colores.texto }}>{n.codigo}</Text>
              <Text style={{ fontSize: 15, color: colores.textoSuave }}>{t ? ETIQUETA_TRAMO[t] : 'Fuera del rango de edad'}</Text>
            </Pressable>
          );
        })
      )}
      <View style={{ height: 8 }} />
      <AvisoOrientacion />
      <Boton etiqueta="Exportación (uso del equipo)" variante="texto" onPress={() => router.push('/exportacion')} testID="ir_exportacion" />
    </Pantalla>
  );
}
