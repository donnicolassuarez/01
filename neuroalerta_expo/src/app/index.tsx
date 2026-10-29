import { Redirect } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';

import { useServicios } from '../servicios/contexto';
import { colores } from '../ui/tema';

/** Decide si se muestra la bienvenida con el consentimiento o la lista de niños. */
export default function Puerta() {
  const { repo, textos } = useServicios();
  const [destino, setDestino] = useState<'/ninos' | '/bienvenida' | null>(null);

  useEffect(() => {
    repo.consentimientoVigente(textos.consentimiento.version).then((c) => setDestino(c ? '/ninos' : '/bienvenida'));
  }, [repo, textos]);

  if (!destino) {
    return (
      <View style={{ flex: 1, justifyContent: 'center' }}>
        <ActivityIndicator size="large" color={colores.primario} />
      </View>
    );
  }
  return <Redirect href={destino} />;
}
