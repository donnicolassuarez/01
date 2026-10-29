import { Directory, File, Paths } from 'expo-file-system';
import * as ImagePicker from 'expo-image-picker';

/** Origen de una foto: devuelve la ruta temporal del archivo elegido, o null si se canceló o se negó el permiso. */
export interface SelectorFotos {
  elegir(opciones: { camara: boolean }): Promise<string | null>;
}

export class SelectorFotosExpo implements SelectorFotos {
  async elegir({ camara }: { camara: boolean }): Promise<string | null> {
    if (camara) {
      const permiso = await ImagePicker.requestCameraPermissionsAsync();
      if (!permiso.granted) return null;
    }
    const resultado = camara
      ? await ImagePicker.launchCameraAsync({ mediaTypes: ['images'], quality: 0.85 })
      : await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.85 });
    if (resultado.canceled || resultado.assets.length === 0) return null;
    return resultado.assets[0].uri;
  }
}

/** Guarda las fotos solo en el almacenamiento privado de la aplicación. */
export interface AlmacenFotos {
  /** Copia el archivo al almacenamiento privado, borra el temporal y devuelve la ruta nueva. */
  guardar(rutaOrigen: string): Promise<string>;
  eliminar(ruta: string): Promise<void>;
}

/**
 * Usa una carpeta dentro del directorio de documentos de la aplicación, que es privado y no lo ve la galería.
 * Se agrega `.nomedia` por si algún visor de medios intentara indexarlo.
 */
export class AlmacenFotosArchivos implements AlmacenFotos {
  constructor(
    private readonly base: Directory = Paths.document,
    private readonly ahora: () => number = Date.now,
  ) {}

  private carpeta(): Directory {
    const dir = new Directory(this.base, 'fotos_privadas');
    dir.create({ intermediates: true, idempotent: true });
    const marca = new File(dir, '.nomedia');
    if (!marca.exists) marca.create();
    return dir;
  }

  async guardar(rutaOrigen: string): Promise<string> {
    const dir = this.carpeta();
    const origen = new File(rutaOrigen);
    const ext = origen.extension || '.jpg';
    const destino = new File(dir, `f_${this.ahora()}${ext.toLowerCase()}`);
    await origen.copy(destino);
    try {
      origen.delete();
    } catch {
      // Si el temporal no se puede borrar, la copia privada ya está a salvo.
    }
    return destino.uri;
  }

  async eliminar(ruta: string): Promise<void> {
    const f = new File(ruta);
    if (f.exists) f.delete();
  }
}
