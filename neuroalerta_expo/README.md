# NeuroAlerta Kids (nombre provisional)

Aplicación Android en español, hecha con Expo (React Native + TypeScript), para que madres, padres y tutores registren
observaciones del neurodesarrollo de un niño o niña, respondan un cuestionario por tramo de edad y reciban una orientación.
Piloto de la Feria FEXCOIN UAP 2026. **Orienta; no diagnostica.** Funciona sin internet y los datos no salen del teléfono.

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `src/domain` | Tramos de edad, modelo y lector de protocolos (con validación) y motor de puntuación puro y determinista. |
| `src/data` | Contrato `Db`, esquema con migraciones versionadas, repositorio (exige el consentimiento) y apertura de la base cifrada. |
| `src/servicios` | Textos editables, fotos en almacenamiento privado, exportación CSV y el contexto de servicios. |
| `src/ui` | Tema, componentes y pantallas. `src/app` solo contiene las rutas de expo-router. |
| `assets/protocolos` | `protocolo_0_36.json`, `protocolo_3_6.json`, `protocolo_7_12.json` (todos **provisionales**). |
| `assets/textos` | `niveles.json` (textos de cada nivel y aviso) y `consentimiento.json`. Se editan sin tocar el código. |
| `__tests__` | Pruebas de motor, datos, servicios, pantallas y lenguaje. |

## Cómo editar un protocolo

Cada archivo trae `version`, `estado`, `areas`, `items`, `focos_rojos` y `reglas_nivel`. Cambie la `version` cada vez que
cambie una pregunta o un corte: cada resultado guarda la versión con la que se calculó. El lector (`parsearProtocolo`)
rechaza protocolos mal formados y las pruebas fallan si falta algo esencial.

- Cada ítem se redacta como una **señal observada**: «Casi siempre» = 2, «A veces» = 1, «Casi nunca» = 0 (`valores`). «No sé» no suma.
- `edad_min_meses` (opcional) oculta ítems o focos que no corresponden a niños más pequeños.
- Los cortes usan proporciones sobre lo respondido (`proporcion_total_min`, `proporcion_area_min`); `minimo_respondidas` evita decidir con muy pocas respuestas.
- Un foco con `"grave": true` lleva directamente a «consultar pronto» sin esperar el puntaje.

## Desarrollo

```bash
npm install
npm run verificar     # tipos + lint + pruebas
```

**Probar en el teléfono.** El cifrado de la base (SQLCipher) exige una compilación nativa propia, no funciona en Expo Go:

```bash
npx expo run:android                                  # con Android Studio instalado y el teléfono por USB
npx eas-cli build -p android --profile preview        # alternativa en la nube (cuenta gratuita de Expo)
```

El perfil `preview` define `SIN_INTERNET=1`, que `app.config.js` convierte en el bloqueo del permiso de internet. Para ver
solo la interfaz en Expo Go: `EXPO_PUBLIC_PERMITIR_BD_SIN_CIFRAR=1 npx expo start` (solo en desarrollo, con una banda roja
visible; nunca en una versión final).

## Decisiones tomadas en la implementación

- Se guarda la fecha de nacimiento (cifrada, solo en el teléfono) para recalcular el tramo en cada sesión; nunca se exporta.
- El CSV usa un código seudónimo `<id de instalación>-N0001`, no el alias que escribió la familia.
- El alias admite como máximo dos palabras para evitar nombres completos.
- La fecha de nacimiento se escribe en tres casillas (día, mes, año): sin componentes nativos adicionales.
- Los focos rojos se piden antes de las preguntas; si se marca uno grave, se ofrece ver la orientación de inmediato.
- Los campos `signo_referencia` y `fuente` son internos y no se muestran a las familias.
- `allowBackup=false` evita que Android copie la base de datos a la nube.
- «Consultar pronto» usa un tono cálido y no el rojo de error, para no aumentar la ansiedad de las familias.

## Pendientes (no bloquean)

Redacción final de preguntas y textos; revisión de cortes por el panel de expertos; confirmar el nombre; leer en el original
las guías mexicanas del proyecto; permiso de los autores del M-CHAT-R/F; probar el flujo completo, la cámara, compartir y el
cifrado en un teléfono Android real.
