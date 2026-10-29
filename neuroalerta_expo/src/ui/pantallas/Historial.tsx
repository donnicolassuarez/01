import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { Pressable, Text } from 'react-native';

import type { SesionConResultado } from '../../data/repositorio';
import { ETIQUETA_TRAMO } from '../../domain/tramo';
import { useServicios } from '../../servicios/contexto';
import { fechaCorta, Pantalla, Parrafo, Titulo } from '../comunes';
import { colores } from '../tema';

export function Historial({ ninoId }: { ninoId: number }) {
  const router = useRouter();
  const { repo, textos } = useServicios();
  const [filas, setFilas] = useState<SesionConResultado[] | null>(null);

  useEffect(() => {
    repo.historial(ninoId).then((h) => setFilas(h.filter((f) => f.resultado !== null)));
  }, [repo, ninoId]);

  return (
    <Pantalla>
      <Titulo>Historial</Titulo>
      {filas === null ? null : filas.length === 0 ? (
        <Parrafo suave>Todavía no hay cuestionarios completados.</Parrafo>
      ) : (
        filas.map(({ sesion, resultado }) => (
          <Pressable
            key={sesion.id}
            testID={`sesion_${sesion.id}`}
            accessibilityRole="button"
            onPress={() => router.push(`/resultado/${sesion.id}`)}
            style={{ backgroundColor: colores.superficie, borderRadius: 12, padding: 16, borderWidth: 1, borderColor: colores.borde, gap: 4 }}
          >
            <Text style={{ fontSize: 17, fontWeight: '600', color: colores.texto }}>{textos.niveles[resultado!.nivel].titulo}</Text>
            <Text style={{ fontSize: 15, color: colores.textoSuave }}>
              {fechaCorta(sesion.iniciadaEn)} · {ETIQUETA_TRAMO[sesion.tramo]}
            </Text>
            <Text style={{ fontSize: 13, color: colores.textoSuave }}>Protocolo {resultado!.versionProtocolo}</Text>
          </Pressable>
        ))
      )}
    </Pantalla>
  );
}
