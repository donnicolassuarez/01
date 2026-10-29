import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Text, TextInput } from 'react-native';

import { EdadFueraDeRango } from '../../data/repositorio';
import { edadEnMeses, ETIQUETA_TRAMO, tramoDesdeEdadMeses } from '../../domain/tramo';
import { useServicios } from '../../servicios/contexto';
import { Boton, Pantalla, Parrafo, Titulo } from '../comunes';
import { CampoFecha, fechaDesdeCampos, FECHA_VACIA } from '../CampoFecha';
import { colores } from '../tema';

/** Valida el alias: corto y de una o dos palabras, para no pedir el nombre completo. */
export function validarAlias(valor: string): string | null {
  const t = valor.trim();
  if (t === '') return 'Escriba un código o alias';
  if (t.length > 24) return 'Use como máximo 24 letras';
  if (t.split(/\s+/).length > 2) return 'Use un código o alias corto, no el nombre completo';
  return null;
}

export function Alta() {
  const router = useRouter();
  const { repo, ahora } = useServicios();
  const [alias, setAlias] = useState('');
  const [fecha, setFecha] = useState(FECHA_VACIA);
  const [errorAlias, setErrorAlias] = useState<string | null>(null);
  const [errorFecha, setErrorFecha] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);

  const nacimiento = fechaDesdeCampos(fecha, ahora());
  const tramo = nacimiento ? tramoDesdeEdadMeses(edadEnMeses(nacimiento, ahora())) : null;

  async function guardar() {
    const eAlias = validarAlias(alias);
    setErrorAlias(eAlias);
    let eFecha: string | null = null;
    if (!nacimiento) eFecha = 'Escriba una fecha de nacimiento válida';
    else if (!tramo) eFecha = 'La edad debe estar entre 0 y 12 años';
    setErrorFecha(eFecha);
    if (eAlias || eFecha || !nacimiento) return;

    setGuardando(true);
    try {
      await repo.crearNino({ codigo: alias, fechaNacimiento: nacimiento });
      router.back();
    } catch (e) {
      if (e instanceof EdadFueraDeRango) setErrorFecha('La edad debe estar entre 0 y 12 años');
      else throw e;
    } finally {
      setGuardando(false);
    }
  }

  return (
    <Pantalla pie={<Boton etiqueta="Guardar" onPress={guardar} deshabilitado={guardando} testID="guardar_nino" />}>
      <Titulo>Agregar niño o niña</Titulo>
      <Text style={{ fontSize: 17, fontWeight: '600', color: colores.texto }}>Código o alias</Text>
      <TextInput
        testID="campo_codigo"
        accessibilityLabel="Código o alias"
        value={alias}
        onChangeText={setAlias}
        autoCapitalize="sentences"
        maxLength={40}
        style={{ minHeight: 52, borderWidth: 1.5, borderColor: colores.borde, borderRadius: 10, paddingHorizontal: 12, fontSize: 18, color: colores.texto, backgroundColor: colores.superficie }}
      />
      <Parrafo suave>No escriba el nombre completo. Por ejemplo: «Peque 1».</Parrafo>
      {errorAlias ? <Text testID="error_alias" style={{ color: colores.error, fontSize: 15 }}>{errorAlias}</Text> : null}

      <CampoFecha etiqueta="Fecha de nacimiento" valor={fecha} onCambio={setFecha} prefijoId="nacimiento" />
      {errorFecha ? <Text testID="error_fecha" style={{ color: colores.error, fontSize: 15 }}>{errorFecha}</Text> : null}
      {tramo ? <Titulo nivel={3}>Grupo de edad: {ETIQUETA_TRAMO[tramo]}</Titulo> : null}
    </Pantalla>
  );
}
