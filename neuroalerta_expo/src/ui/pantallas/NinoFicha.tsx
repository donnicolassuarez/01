import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';

import type { Nino } from '../../data/repositorio';
import { edadEnMeses, ETIQUETA_TRAMO, tramoDesdeEdadMeses } from '../../domain/tramo';
import { useServicios } from '../../servicios/contexto';
import { AvisoOrientacion, Boton, Pantalla, Parrafo, Titulo } from '../comunes';

export function NinoFicha({ ninoId }: { ninoId: number }) {
  const router = useRouter();
  const { repo, ahora } = useServicios();
  const [nino, setNino] = useState<Nino | null>(null);

  useEffect(() => {
    repo.nino(ninoId).then(setNino);
  }, [repo, ninoId]);

  if (!nino) return <Pantalla>{null}</Pantalla>;
  const tramo = tramoDesdeEdadMeses(edadEnMeses(nino.fechaNacimiento, ahora()));

  return (
    <Pantalla>
      <Titulo>{nino.codigo}</Titulo>
      <Titulo nivel={3}>{tramo ? ETIQUETA_TRAMO[tramo] : 'Fuera del rango de edad'}</Titulo>
      {tramo ? (
        <Boton etiqueta="Responder el cuestionario" onPress={() => router.push(`/cuestionario/${nino.id}`)} testID="ir_cuestionario" />
      ) : (
        <Parrafo>Este niño o niña ya no está en el rango de edad de la aplicación (0 a 12 años).</Parrafo>
      )}
      <Boton etiqueta="Historial" variante="secundario" onPress={() => router.push(`/historial/${nino.id}`)} testID="ir_historial" />
      <Boton etiqueta="Fotos de conductas" variante="secundario" onPress={() => router.push(`/fotos/${nino.id}`)} testID="ir_fotos" />
      <AvisoOrientacion />
    </Pantalla>
  );
}
