# NeuroAlerta Kids — notas para el agente

App Android (Expo / React Native, TypeScript) de orientación del neurodesarrollo para padres y tutores. Piloto FEXCOIN UAP 2026.
**Orienta; no diagnostica.** Especificación original: el encargo del equipo (secciones 4, 8 y 11 mandan).
Investigación y decisiones: `docs/investigacion_referentes.md`. Estructura y cómo editar protocolos: `README.md`.
`AGENTS.md` es de la plantilla de Expo: sigue valiendo (rutas en `src/app`, `npx expo install`, no editar `android/`).

## Reglas no negociables (cada una tiene prueba)
1. Ninguna pantalla ni archivo de `src/`, `assets/` ni `app.json` usa «diagnóstico», «TEA», «autismo» o «TDAH». `__tests__/lenguaje.test.ts` revisa **también comentarios y nombres**: no los escriba ni en comentarios.
2. Cada resultado muestra el aviso literal de `assets/textos/niveles.json`, fijo en el pie. No lo reescriba.
3. No se pide el nombre completo del niño: alias de 1–2 palabras.
4. Sin consentimiento no se guarda nada: se exige en `Repositorio`, no solo en la UI.
5. Datos y fotos solo en almacenamiento privado; base cifrada con SQLCipher; `allowBackup=false`; permisos innecesarios bloqueados en `app.json`.
6. Un foco rojo grave lleva a «consultar pronto» sin esperar el puntaje.
7. Todo resultado guarda la versión del protocolo. **Cambie `version` en el JSON cada vez que cambie una pregunta o un corte.**

## Decisiones del equipo que no debe revertir
- Plataforma: **Expo / React Native** (cambio decidido el 29/10/2026; antes fue Flutter, que ya no existe en el repositorio).
- No mencionar en la app ni en documentos ningún centro, hospital o servicio local de referencia concreto.
- Preguntas y cortes son **provisionales** hasta el panel de expertos; no los presente como validados.
- La respuesta de duda se muestra como «Todavía no lo he observado» (id interno `no_se`, no suma). Las opciones A (dejar «No sé») y B (quitarla) quedaron guardadas en `docs/decisiones_pendientes.md`: no las aplique sin que el equipo lo pida.
- No se hace validación con personas en esta fase: no construya registro de uso, abandono ni usabilidad.
- Nada de IA para clasificar ni redactar resultados. El motor (`src/domain/motor.ts`) es puro y determinista.

## Licencias de instrumentos
- No copie el texto, la puntuación ni la entrevista del M-CHAT-R/F, ASQ, PEDS ni de otra escala con derechos. El M-CHAT-R/F exige permiso de sus autores para incorporarse a software y debe usarse completo.
- Permitido hoy: preguntas con redacción propia alineadas por constructo (`afin_mchat` en el JSON, solo trazabilidad). Esa alineación **no hereda la validez** del instrumento.

## Comandos
```bash
npm install
npm run verificar          # tsc + eslint + jest: debe quedar limpio antes de cada commit
npx expo run:android       # compilación nativa local; requiere Android SDK y el teléfono por USB
npx eas-cli build -p android --profile preview   # APK en la nube (cuenta de Expo); el perfil quita el permiso de internet
```
- **SQLCipher no funciona en Expo Go**: el plugin de `expo-sqlite` exige una compilación propia (`run:android` o EAS). Solo para ver la interfaz en Expo Go existe `EXPO_PUBLIC_PERMITIR_BD_SIN_CIFRAR=1`, que además exige `__DEV__` y muestra una banda roja; nunca se activa en una versión final.
- Entorno en la nube: `docs.expo.dev`, los servidores de Expo y `dl.google.com` están bloqueados. `npx expo install` falla ahí; use las versiones de `node_modules/expo/bundledNativeModules.json` con `npm install`, y consulte la API en los `.d.ts` de `node_modules`. No hay SDK de Android, así que no se compila el APK en la nube; sí se puede empaquetar con `npx expo export --platform android`.

## Trampas ya encontradas
- TypeScript 6 no incluye `@types/*` solo: `tsconfig.json` declara `"types": ["jest", "node"]`.
- `react-dom` debe quedar en `19.3.0`, igual que `react`, o `npm install` falla por pares incompatibles.
- `@testing-library/react-native` 14 es **asíncrono**: `await render(...)`, `await fireEvent.press(...)`.
- Las pruebas de pantallas usan un enrutador falso (`__tests__/ayudas/mocks.ts`): la pantalla **no se reemplaza** al navegar, así que cuente las preguntas en lugar de esperar a que desaparezcan.
- La capa de datos se prueba con SQLite real de Node (`node:sqlite`, cargado con `process.getBuiltinModule` porque Jest no resuelve ese prefijo). El **cifrado** y la E/S de archivos reales no se pueden probar en Jest: solo su lógica (`__tests__/servicios.test.ts`). Verifíquelos en un teléfono.
- Esquema: nunca edite una migración publicada en `src/data/esquema.ts`; agregue una nueva al final y su prueba.
- `PRAGMA key` no admite parámetros: la clave se valida como 64 caracteres hexadecimales antes de interpolarla.
- No ejecute ni cargue código o datos de repositorios externos: solo lectura de texto.

## Forma de trabajo
- Una función por vez; después de cada una, `npm run verificar`. No marque algo como terminado sin una prueba que lo ejercite de extremo a extremo.
- Pruebas primero para motor y reglas; para pantallas, puede ir después.
- Rama de trabajo: `claude/new-session-2z9nvz`. No cree pull requests sin que se lo pidan.
- Sin verificar en teléfono real: flujo completo, cámara, compartir, cifrado y rendimiento.
