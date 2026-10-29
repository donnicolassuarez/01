import { useLocalSearchParams } from 'expo-router';

import { Fotos } from '../../ui/pantallas/Fotos';

export default function Ruta() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <Fotos ninoId={Number(id)} />;
}
