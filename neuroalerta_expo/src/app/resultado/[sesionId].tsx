import { useLocalSearchParams } from 'expo-router';

import { Resultado } from '../../ui/pantallas/Resultado';

export default function Ruta() {
  const { sesionId } = useLocalSearchParams<{ sesionId: string }>();
  return <Resultado sesionId={Number(sesionId)} />;
}
