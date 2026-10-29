import { useCallback, useEffect, useState } from 'react';
import { Image, Modal, Pressable, Text, TextInput, View } from 'react-native';

import type { Foto } from '../../data/repositorio';
import { useServicios } from '../../servicios/contexto';
import { Boton, fechaCorta, Pantalla, Parrafo, Titulo } from '../comunes';
import { CampoFecha, camposDesdeFecha, fechaDesdeCampos, type FechaCampos } from '../CampoFecha';
import { colores } from '../tema';

type Paso =
  | { tipo: 'inactivo' }
  | { tipo: 'origen' }
  | { tipo: 'detalle'; rutaTemporal: string }
  | { tipo: 'ver'; foto: Foto }
  | { tipo: 'confirmar'; foto: Foto };

export function Fotos({ ninoId }: { ninoId: number }) {
  const { repo, selectorFotos, almacenFotos, ahora } = useServicios();
  const [fotos, setFotos] = useState<Foto[] | null>(null);
  const [paso, setPaso] = useState<Paso>({ tipo: 'inactivo' });
  const [fecha, setFecha] = useState<FechaCampos>(camposDesdeFecha(ahora()));
  const [nota, setNota] = useState('');

  const recargar = useCallback(async () => setFotos(await repo.fotosDe(ninoId)), [repo, ninoId]);
  useEffect(() => {
    let vigente = true;
    repo.fotosDe(ninoId).then((l) => vigente && setFotos(l));
    return () => {
      vigente = false;
    };
  }, [repo, ninoId]);

  async function elegir(camara: boolean) {
    setPaso({ tipo: 'inactivo' });
    const ruta = await selectorFotos.elegir({ camara });
    if (!ruta) return;
    setFecha(camposDesdeFecha(ahora()));
    setNota('');
    setPaso({ tipo: 'detalle', rutaTemporal: ruta });
  }

  async function guardar(rutaTemporal: string) {
    const f = fechaDesdeCampos(fecha, ahora());
    if (!f) return;
    const ruta = await almacenFotos.guardar(rutaTemporal);
    await repo.agregarFoto({ ninoId, ruta, fecha: f, nota });
    setPaso({ tipo: 'inactivo' });
    await recargar();
  }

  async function eliminar(foto: Foto) {
    await almacenFotos.eliminar(foto.ruta);
    await repo.eliminarFoto(foto.id);
    setPaso({ tipo: 'inactivo' });
    await recargar();
  }

  const fechaValida = fechaDesdeCampos(fecha, ahora()) !== null;

  return (
    <>
      <Pantalla pie={<Boton etiqueta="Agregar foto" onPress={() => setPaso({ tipo: 'origen' })} testID="agregar_foto" />}>
        <Titulo>Fotos de conductas</Titulo>
        <Parrafo suave>
          Las fotos quedan solo en este teléfono y no aparecen en la galería. Pueden ayudar a mostrar una conducta al profesional de salud.
        </Parrafo>
        {fotos !== null && fotos.length === 0 && <Parrafo>Todavía no hay fotos.</Parrafo>}
        {fotos?.map((f) => (
          <Pressable
            key={f.id}
            testID={`foto_${f.id}`}
            accessibilityRole="button"
            onPress={() => setPaso({ tipo: 'ver', foto: f })}
            style={{ flexDirection: 'row', gap: 12, backgroundColor: colores.superficie, borderRadius: 12, padding: 10, borderWidth: 1, borderColor: colores.borde, alignItems: 'center' }}
          >
            <Image source={{ uri: f.ruta }} style={{ width: 64, height: 64, borderRadius: 8, backgroundColor: colores.borde }} accessibilityIgnoresInvertColors />
            <View style={{ flex: 1 }}>
              <Text style={{ fontSize: 17, fontWeight: '600', color: colores.texto }}>{fechaCorta(f.fecha)}</Text>
              <Text numberOfLines={2} style={{ fontSize: 15, color: colores.textoSuave }}>
                {f.nota === '' ? 'Sin nota' : f.nota}
              </Text>
            </View>
          </Pressable>
        ))}
      </Pantalla>

      <Modal visible={paso.tipo !== 'inactivo'} transparent animationType="fade" onRequestClose={() => setPaso({ tipo: 'inactivo' })}>
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.45)', justifyContent: 'center', padding: 20 }}>
          <View style={{ backgroundColor: colores.superficie, borderRadius: 16, padding: 20, gap: 12 }}>
            {paso.tipo === 'origen' && (
              <>
                <Titulo nivel={2}>Agregar foto</Titulo>
                <Boton etiqueta="Tomar una foto" onPress={() => void elegir(true)} testID="foto_camara" />
                <Boton etiqueta="Elegir una foto del teléfono" variante="secundario" onPress={() => void elegir(false)} testID="foto_galeria" />
                <Boton etiqueta="Cancelar" variante="texto" onPress={() => setPaso({ tipo: 'inactivo' })} />
              </>
            )}
            {paso.tipo === 'detalle' && (
              <>
                <Titulo nivel={2}>Detalles de la foto</Titulo>
                <CampoFecha etiqueta="Fecha" valor={fecha} onCambio={setFecha} prefijoId="foto_fecha" />
                <TextInput
                  testID="nota_foto"
                  accessibilityLabel="Nota"
                  placeholder="Nota (qué se ve, cuándo ocurre)"
                  multiline
                  value={nota}
                  onChangeText={setNota}
                  style={{ minHeight: 80, borderWidth: 1.5, borderColor: colores.borde, borderRadius: 10, padding: 12, fontSize: 17, color: colores.texto, textAlignVertical: 'top' }}
                />
                <Boton etiqueta="Guardar" deshabilitado={!fechaValida} onPress={() => void guardar(paso.rutaTemporal)} testID="guardar_foto" />
                <Boton
                  etiqueta="Cancelar"
                  variante="texto"
                  onPress={() => {
                    void almacenFotos.eliminar(paso.rutaTemporal).catch(() => undefined);
                    setPaso({ tipo: 'inactivo' });
                  }}
                />
              </>
            )}
            {paso.tipo === 'ver' && (
              <>
                <Titulo nivel={2}>{fechaCorta(paso.foto.fecha)}</Titulo>
                <Image source={{ uri: paso.foto.ruta }} style={{ width: '100%', height: 280, borderRadius: 8, backgroundColor: colores.borde }} resizeMode="contain" accessibilityIgnoresInvertColors />
                <Parrafo>{paso.foto.nota === '' ? 'Sin nota' : paso.foto.nota}</Parrafo>
                <Boton etiqueta="Eliminar" variante="secundario" onPress={() => setPaso({ tipo: 'confirmar', foto: paso.foto })} testID="eliminar_foto" />
                <Boton etiqueta="Cerrar" onPress={() => setPaso({ tipo: 'inactivo' })} />
              </>
            )}
            {paso.tipo === 'confirmar' && (
              <>
                <Titulo nivel={2}>¿Eliminar esta foto?</Titulo>
                <Parrafo>Se borrará del teléfono y no se podrá recuperar.</Parrafo>
                <Boton etiqueta="Eliminar" onPress={() => void eliminar(paso.foto)} testID="confirmar_eliminar" />
                <Boton etiqueta="Cancelar" variante="texto" onPress={() => setPaso({ tipo: 'ver', foto: paso.foto })} />
              </>
            )}
          </View>
        </View>
      </Modal>
    </>
  );
}
