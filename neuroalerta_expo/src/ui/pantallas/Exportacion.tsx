import { useState } from 'react';
import { Text } from 'react-native';

import { exportarCsv, useServicios } from '../../servicios/contexto';
import { Boton, Pantalla, Parrafo, Titulo } from '../comunes';
import { colores } from '../tema';

/** Pantalla de uso del equipo del proyecto: genera un CSV sin datos de identificación y lo comparte. */
export function Exportacion() {
  const servicios = useServicios();
  const [trabajando, setTrabajando] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);

  async function exportar() {
    setTrabajando(true);
    setMensaje(null);
    try {
      await exportarCsv(servicios);
    } catch {
      setMensaje('No se pudo generar el archivo. Intente de nuevo.');
    } finally {
      setTrabajando(false);
    }
  }

  return (
    <Pantalla pie={<Boton etiqueta="Generar y compartir CSV" onPress={exportar} deshabilitado={trabajando} testID="exportar_csv" />}>
      <Titulo>Exportación (uso del equipo)</Titulo>
      <Parrafo>
        Genera un archivo CSV con las respuestas y orientaciones de los cuestionarios completados. Se comparte con el selector de
        Android: usted elige a dónde enviarlo.
      </Parrafo>
      <Parrafo>El archivo no incluye nombres, alias, fecha de nacimiento exacta ni fotos.</Parrafo>
      <Parrafo>Los cortes y preguntas son provisionales, y el archivo lo indica en cada fila.</Parrafo>
      {mensaje ? <Text testID="mensaje_exportacion" style={{ color: colores.error, fontSize: 16 }}>{mensaje}</Text> : null}
    </Pantalla>
  );
}
