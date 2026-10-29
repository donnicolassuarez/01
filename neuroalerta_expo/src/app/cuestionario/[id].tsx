import { useLocalSearchParams } from 'expo-router';

import { Cuestionario } from '../../ui/pantallas/Cuestionario';

export default function Ruta() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <Cuestionario ninoId={Number(id)} />;
}
