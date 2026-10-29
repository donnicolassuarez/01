import { File, Paths } from 'expo-file-system';
import * as Sharing from 'expo-sharing';

/** Comparte un archivo con el selector de Android. */
export async function compartirConSelector(ruta: string, asunto: string): Promise<void> {
  if (!(await Sharing.isAvailableAsync())) throw new Error('Este teléfono no permite compartir archivos.');
  await Sharing.shareAsync(ruta, { mimeType: 'text/csv', dialogTitle: asunto });
}

/** Escribe el archivo en la carpeta de caché de la app (privada) y devuelve su ruta. */
export async function escribirEnTemporal(nombre: string, contenido: string): Promise<string> {
  const archivo = new File(Paths.cache, nombre);
  archivo.create({ overwrite: true });
  archivo.write(contenido);
  return archivo.uri;
}
