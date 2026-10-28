# NeuroAlerta Kids (nombre provisional)

Aplicación Android en español, hecha con Flutter, para que madres, padres y tutores registren observaciones del
neurodesarrollo de un niño o niña, respondan un cuestionario por tramo de edad y reciban una orientación.
Piloto de la Feria FEXCOIN UAP 2026. **Orienta; no diagnostica.** Todo funciona sin internet y los datos no salen del teléfono.

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `lib/domain` | Tramos de edad, modelo de protocolo y motor de puntuación (determinista, sin IA). |
| `lib/data` | Base de datos drift (SQLite cifrado con SQLite3MultipleCiphers) y repositorio. El repositorio exige el consentimiento. |
| `lib/servicios` | Textos editables, fotos en almacenamiento privado, exportación CSV, inyección de dependencias. |
| `lib/ui` | Pantallas: bienvenida, consentimiento, niños, cuestionario, resultado, historial, fotos, exportación. |
| `assets/protocolos` | `protocolo_0_36.json`, `protocolo_3_6.json`, `protocolo_7_12.json` (todos **provisionales**). |
| `assets/textos` | `niveles.json` (textos de cada nivel y aviso) y `consentimiento.json`. Se editan sin tocar el código. |

## Cómo editar un protocolo

Cada archivo trae `version`, `estado`, `areas`, `items`, `focos_rojos` y `reglas_nivel`. Cambie la `version` cada vez que
cambie una pregunta o un corte: cada resultado guarda la versión con la que se calculó.

- Cada ítem se redacta como una **señal observada**, de modo que «Casi siempre» = 2, «A veces» = 1, «Casi nunca» = 0
  (`valores`). «No sé» no suma y se cuenta aparte.
- `edad_min_meses` (opcional) oculta ítems o focos que no corresponden a niños más pequeños.
- Los cortes usan proporciones (`proporcion_total_min`, `proporcion_area_min`) sobre lo respondido, para que «No sé»
  no baje artificialmente el puntaje. `minimo_respondidas` evita decidir con muy pocas respuestas.
- Un foco con `"grave": true` lleva directamente a «consultar pronto» sin esperar el puntaje.

## Desarrollo

```bash
flutter pub get
dart run build_runner build      # regenera lib/data/base_datos.g.dart si cambia el esquema
flutter analyze
flutter test
flutter build apk --debug        # requiere el SDK de Android
```

`pubspec.yaml` selecciona SQLite3MultipleCiphers con `hooks: user_defines: sqlite3: source: sqlite3mc`. La primera
compilación descarga la biblioteca prebuilt desde GitHub.

## Decisiones tomadas en la implementación

- Se guarda la fecha de nacimiento (cifrada, solo en el teléfono) para recalcular el tramo en cada sesión; nunca se exporta.
- El CSV usa un código seudónimo `<id de instalación>-N0001`, no el alias que escribió la familia.
- El alias admite como máximo dos palabras para evitar nombres completos.
- Los focos rojos se piden antes de las preguntas; si se marca uno grave, se ofrece ver la orientación de inmediato.
- Los campos `signo_referencia` y `fuente` son internos y no se muestran a las familias.
- `allowBackup=false` evita que Android copie la base de datos a la nube.

## Pendientes (no bloquean)

Redacción final de preguntas y de los textos de nivel; revisión de cortes por el panel de expertos; confirmar el nombre;
probar el flujo completo en un teléfono Android real.
