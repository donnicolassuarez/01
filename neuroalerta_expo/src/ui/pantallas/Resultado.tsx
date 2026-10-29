import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import type { Resultado as ResultadoGuardado, Sesion } from '../../data/repositorio';
import { areaDe, ETIQUETA_OPCION, itemsPara, type Opcion } from '../../domain/protocolo';
import { useServicios } from '../../servicios/contexto';
import { AvisoOrientacion, Pantalla, Boton, Parrafo, Punto, Titulo } from '../comunes';
import { colores } from '../tema';

interface Datos {
  sesion: Sesion;
  resultado: ResultadoGuardado;
  respuestas: Record<string, Opcion>;
}

export function Resultado({ sesionId }: { sesionId: number }) {
  const router = useRouter();
  const { repo, protocolos, textos } = useServicios();
  const [datos, setDatos] = useState<Datos | null>(null);

  useEffect(() => {
    (async () => {
      const sesion = await repo.sesion(sesionId);
      const resultado = await repo.resultadoDe(sesionId);
      if (!resultado) throw new Error('La sesión no tiene resultado');
      setDatos({ sesion, resultado, respuestas: await repo.respuestasDe(sesionId) });
    })();
  }, [repo, sesionId]);

  if (!datos) return <Pantalla>{null}</Pantalla>;
  const { sesion, resultado, respuestas } = datos;
  const protocolo = protocolos[sesion.tramo];
  const texto = textos.niveles[resultado.nivel];
  const colorNivel = colores.nivel[resultado.nivel];

  const observados: Record<string, string[]> = {};
  for (const item of protocolo.items) {
    const r = respuestas[item.id];
    if (r === 'casi_siempre' || r === 'a_veces') {
      (observados[item.areaId] ??= []).push(`${item.texto} (${ETIQUETA_OPCION[r].toLowerCase()})`);
    }
  }
  const focosTexto = protocolo.focosRojos.filter((f) => resultado.focosRojos.includes(f.id)).map((f) => f.texto);
  const aplicables = itemsPara(protocolo, sesion.edadMeses).length;
  const muchosNoSe = aplicables > 0 && resultado.noSe / aplicables >= protocolo.umbralNoSe;
  const pocas = Object.keys(respuestas).length - resultado.noSe < protocolo.minimoRespondidas;

  return (
    <Pantalla
      pie={
        <>
          <AvisoOrientacion />
          <Text testID="version_protocolo" style={{ color: colores.textoSuave, fontSize: 13 }}>
            Versión del protocolo: {resultado.versionProtocolo}
          </Text>
          <Boton etiqueta="Volver al inicio" onPress={() => router.dismissAll()} testID="volver_inicio" />
        </>
      }
    >
      <View
        testID="nivel_orientacion"
        style={{ backgroundColor: colorNivel.fondo, borderColor: colorNivel.borde, borderWidth: 1.5, borderRadius: 14, padding: 16, gap: 8 }}
      >
        <Titulo nivel={2}>{texto.titulo}</Titulo>
        <Parrafo>{texto.resumen}</Parrafo>
      </View>

      {focosTexto.length > 0 && (
        <>
          <Titulo nivel={3}>Situaciones que usted marcó</Titulo>
          {focosTexto.map((t) => (
            <Punto key={t}>{t}</Punto>
          ))}
        </>
      )}

      <Titulo nivel={3}>Lo que usted observó</Titulo>
      {Object.keys(observados).length === 0 ? (
        <Parrafo>No marcó señales en las preguntas respondidas.</Parrafo>
      ) : (
        Object.entries(observados).map(([areaId, lista]) => (
          <View key={areaId}>
            <Text style={{ fontWeight: '600', color: colores.texto, fontSize: 16, marginTop: 8 }}>{areaDe(protocolo, areaId).nombre}</Text>
            {lista.map((t) => (
              <Punto key={t}>{t}</Punto>
            ))}
          </View>
        ))
      )}

      {muchosNoSe && <Parrafo>{textos.notaNoSe}</Parrafo>}
      {pocas && <Parrafo>{textos.notaPocasRespuestas}</Parrafo>}

      <Titulo nivel={3}>Paso recomendado</Titulo>
      <Parrafo>{texto.paso}</Parrafo>
    </Pantalla>
  );
}
