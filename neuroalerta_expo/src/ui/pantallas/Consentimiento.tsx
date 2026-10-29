import { useRouter } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';

import { useServicios } from '../../servicios/contexto';
import { Boton, Casilla, Pantalla, Parrafo, Punto, Titulo } from '../comunes';

export function Consentimiento() {
  const router = useRouter();
  const { repo, textos } = useServicios();
  const c = textos.consentimiento;
  const [acepto, setAcepto] = useState(false);
  const [guardando, setGuardando] = useState(false);

  async function aceptar() {
    setGuardando(true);
    try {
      await repo.registrarConsentimiento(c.version);
      router.dismissAll();
      router.replace('/ninos');
    } finally {
      setGuardando(false);
    }
  }

  return (
    <Pantalla
      pie={
        <View style={{ gap: 8 }}>
          <Casilla testID="casilla_consentimiento" marcada={acepto} onCambio={setAcepto} etiqueta="He leído y estoy de acuerdo" deshabilitada={guardando} />
          <Boton etiqueta={c.aceptacion} onPress={aceptar} deshabilitado={!acepto || guardando} testID="aceptar_consentimiento" />
        </View>
      }
    >
      <Titulo>{c.titulo}</Titulo>
      {c.texto.map((t) => (
        <Parrafo key={t}>{t}</Parrafo>
      ))}
      <Titulo nivel={3}>Qué se guarda</Titulo>
      {c.seGuarda.map((t) => (
        <Punto key={t}>{t}</Punto>
      ))}
      <Titulo nivel={3}>Cómo se protege</Titulo>
      {c.privacidad.map((t) => (
        <Punto key={t}>{t}</Punto>
      ))}
      <Parrafo suave>Versión del texto: {c.version}</Parrafo>
    </Pantalla>
  );
}
