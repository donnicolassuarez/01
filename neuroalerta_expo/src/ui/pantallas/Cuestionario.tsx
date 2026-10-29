import { useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { Modal, StyleSheet, Text, View } from 'react-native';

import type { Sesion } from '../../data/repositorio';
import { evaluar } from '../../domain/motor';
import {
  areaDe,
  ETIQUETA_OPCION,
  focosPara,
  itemsPara,
  OPCIONES,
  type FocoRojo,
  type ItemProtocolo,
  type Opcion,
  type Protocolo,
} from '../../domain/protocolo';
import { edadEnMeses, tramoDesdeEdadMeses } from '../../domain/tramo';
import { useServicios } from '../../servicios/contexto';
import { Boton, Casilla, Pantalla, Parrafo, Titulo } from '../comunes';
import { colores } from '../tema';

const PAGINA_FOCOS = -1;

interface Estado {
  protocolo: Protocolo;
  sesion: Sesion;
  items: ItemProtocolo[];
  focos: FocoRojo[];
}

/**
 * Una pregunta por pantalla. Antes de las preguntas se muestra la lista de situaciones de atención.
 * Cada respuesta se guarda al momento, así que se puede salir y retomar.
 */
export function Cuestionario({ ninoId }: { ninoId: number }) {
  const router = useRouter();
  const servicios = useServicios();
  const { repo, protocolos, textos, ahora } = servicios;

  const [estado, setEstado] = useState<Estado | null>(null);
  const [respuestas, setRespuestas] = useState<Record<string, Opcion>>({});
  const [marcados, setMarcados] = useState<string[]>([]);
  const [pagina, setPagina] = useState(PAGINA_FOCOS);
  const [avisoGrave, setAvisoGrave] = useState(false);
  const avisoMostrado = useRef(false);
  const ocupado = useRef(false);

  useEffect(() => {
    let vigente = true;
    (async () => {
      const nino = await repo.nino(ninoId);
      const tramo = tramoDesdeEdadMeses(edadEnMeses(nino.fechaNacimiento, ahora()));
      if (!tramo) return;
      const protocolo = protocolos[tramo];
      const sesion = await repo.iniciarOReanudarSesion({ nino, protocolo });
      const guardadas = await repo.respuestasDe(sesion.id);
      const items = itemsPara(protocolo, sesion.edadMeses);
      const primera = items.findIndex((i) => !(i.id in guardadas));
      if (!vigente) return;
      setEstado({ protocolo, sesion, items, focos: focosPara(protocolo, sesion.edadMeses) });
      setRespuestas(guardadas);
      setMarcados(sesion.focosMarcados);
      setPagina(Object.keys(guardadas).length === 0 ? PAGINA_FOCOS : primera === -1 ? items.length - 1 : primera);
    })();
    return () => {
      vigente = false;
    };
  }, [repo, protocolos, ninoId, ahora]);

  if (!estado) return <Pantalla>{null}</Pantalla>;
  const { protocolo, sesion, items, focos } = estado;

  async function finalizar(resp: Record<string, Opcion>, focosMarcados: string[]) {
    const resultado = evaluar({ protocolo, edadMeses: sesion.edadMeses, respuestas: resp, focosMarcados });
    await repo.cerrarSesion(sesion.id, resultado);
    router.replace(`/resultado/${sesion.id}`);
  }

  async function continuarDesdeFocos() {
    await repo.guardarFocos(sesion.id, marcados);
    const grave = focos.some((f) => f.grave && marcados.includes(f.id));
    if (grave && !avisoMostrado.current) {
      avisoMostrado.current = true;
      setAvisoGrave(true);
      return;
    }
    setPagina(0);
  }

  async function responder(opcion: Opcion) {
    if (ocupado.current) return;
    ocupado.current = true;
    try {
      const item = items[pagina];
      await repo.guardarRespuesta({ sesionId: sesion.id, item, opcion });
      const nuevas = { ...respuestas, [item.id]: opcion };
      setRespuestas(nuevas);
      if (pagina === items.length - 1) await finalizar(nuevas, marcados);
      else setPagina(pagina + 1);
    } finally {
      ocupado.current = false;
    }
  }

  const modalGrave = (
    <Modal visible={avisoGrave} transparent animationType="fade" onRequestClose={() => setAvisoGrave(false)}>
      <View style={estilos.fondoModal}>
        <View style={estilos.tarjeta} testID="aviso_foco_grave">
          <Titulo nivel={2}>Conviene consultar pronto</Titulo>
          <Parrafo>{textos.focoGrave}</Parrafo>
          <Boton
            etiqueta="Ver la orientación"
            testID="ver_orientacion"
            onPress={() => {
              setAvisoGrave(false);
              void finalizar(respuestas, marcados);
            }}
          />
          <Boton
            etiqueta="Seguir con las preguntas"
            variante="secundario"
            testID="seguir_preguntas"
            onPress={() => {
              setAvisoGrave(false);
              setPagina(0);
            }}
          />
        </View>
      </View>
    </Modal>
  );

  if (pagina === PAGINA_FOCOS) {
    return (
      <>
        <Pantalla pie={<Boton etiqueta="Continuar" onPress={continuarDesdeFocos} testID="continuar_focos" />}>
          <Titulo>Antes de empezar</Titulo>
          <Parrafo>Marque si ha notado alguna de estas situaciones. Si no ha notado ninguna, deje todo sin marcar.</Parrafo>
          {focos.map((f) => (
            <Casilla
              key={f.id}
              testID={`foco_${f.id}`}
              marcada={marcados.includes(f.id)}
              onCambio={(v) => setMarcados(v ? [...marcados, f.id] : marcados.filter((x) => x !== f.id))}
              etiqueta={f.texto}
            />
          ))}
        </Pantalla>
        {modalGrave}
      </>
    );
  }

  const item = items[pagina];
  const actual = respuestas[item.id];
  return (
    <>
      <Pantalla
        pie={
          <View style={{ gap: 6 }}>
            {OPCIONES.map((o) => (
              <Boton
                key={o}
                testID={`opcion_${o}`}
                etiqueta={ETIQUETA_OPCION[o]}
                variante={o === actual ? 'principal' : 'secundario'}
                onPress={() => void responder(o)}
              />
            ))}
            <View style={estilos.navegacion}>
              <Boton testID="anterior" etiqueta="‹ Anterior" variante="texto" onPress={() => setPagina(pagina - 1)} />
              <Text style={estilos.contador}>
                Pregunta {pagina + 1} de {items.length}
              </Text>
            </View>
          </View>
        }
      >
        <View style={estilos.barra} accessibilityRole="progressbar" accessibilityValue={{ min: 0, max: items.length, now: pagina + 1 }}>
          <View style={[estilos.barraRelleno, { width: `${((pagina + 1) / items.length) * 100}%` }]} />
        </View>
        <Text style={estilos.area}>{areaDe(protocolo, item.areaId).nombre}</Text>
        <Text style={estilos.subtitulo}>¿Con qué frecuencia pasa esto?</Text>
        <Text testID="texto_pregunta" style={estilos.pregunta}>
          {item.texto}
        </Text>
      </Pantalla>
      {modalGrave}
    </>
  );
}

const estilos = StyleSheet.create({
  barra: { height: 8, borderRadius: 4, backgroundColor: colores.borde, overflow: 'hidden' },
  barraRelleno: { height: 8, backgroundColor: colores.primario },
  area: {
    alignSelf: 'flex-start',
    backgroundColor: colores.aviso,
    color: colores.sobreAviso,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 16,
    fontSize: 14,
    overflow: 'hidden',
  },
  subtitulo: { color: colores.textoSuave, fontSize: 15 },
  pregunta: { color: colores.texto, fontSize: 23, lineHeight: 31, fontWeight: '600' },
  navegacion: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  contador: { color: colores.textoSuave, fontSize: 15 },
  fondoModal: { flex: 1, backgroundColor: 'rgba(0,0,0,0.45)', justifyContent: 'center', padding: 24 },
  tarjeta: { backgroundColor: colores.superficie, borderRadius: 16, padding: 20, gap: 12 },
});
