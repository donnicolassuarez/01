import { useRouter } from 'expo-router';
import { Text } from 'react-native';

import { AvisoOrientacion, Boton, NOMBRE_APP, Pantalla, Parrafo, Titulo } from '../comunes';

export function Bienvenida() {
  const router = useRouter();
  return (
    <Pantalla pie={<Boton etiqueta="Comenzar" onPress={() => router.push('/consentimiento')} testID="comenzar" />}>
      <Text style={{ fontSize: 64, textAlign: 'center' }} accessibilityElementsHidden>
        🌱
      </Text>
      <Titulo>{NOMBRE_APP}</Titulo>
      <Parrafo>
        Anote lo que observa en el desarrollo de su hijo o hija, responda unas preguntas sencillas y reciba una
        orientación sobre qué hacer después.
      </Parrafo>
      <AvisoOrientacion />
      <Parrafo suave>Es un piloto. Funciona sin internet y los datos se quedan en este teléfono.</Parrafo>
    </Pantalla>
  );
}
