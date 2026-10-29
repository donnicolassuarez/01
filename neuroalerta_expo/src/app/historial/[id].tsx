import { useLocalSearchParams } from 'expo-router';

import { Historial } from '../../ui/pantallas/Historial';

export default function Ruta() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <Historial ninoId={Number(id)} />;
}
