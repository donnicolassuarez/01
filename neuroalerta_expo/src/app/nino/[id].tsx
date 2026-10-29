import { useLocalSearchParams } from 'expo-router';

import { NinoFicha } from '../../ui/pantallas/NinoFicha';

export default function Ruta() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <NinoFicha ninoId={Number(id)} />;
}
