# NeuroAlerta Kids — notas para el agente

App Android (Flutter) de orientación del neurodesarrollo para padres y tutores. Piloto FEXCOIN UAP 2026.
**Orienta; no diagnostica.** Especificación original: el encargo del equipo (secciones 4, 8 y 11 mandan).
Investigación y decisiones: `docs/investigacion_referentes.md`. Mapa y decisiones de implementación: `README.md`.

## Reglas no negociables (cada una tiene prueba)
1. Ninguna pantalla ni archivo de `lib/` ni texto de `assets/` usa «diagnóstico», «TEA», «autismo» o «TDAH» (la prueba revisa **también comentarios y nombres en `lib/`**: no los escriba ni en comentarios).
2. Cada resultado muestra el aviso literal de `assets/textos/niveles.json`. No lo reescriba.
3. No se pide el nombre completo del niño: alias de 1–2 palabras.
4. Sin consentimiento no se guarda nada: se exige en `Repositorio`, no solo en la UI.
5. Datos y fotos solo en almacenamiento privado; base cifrada (SQLite3MultipleCiphers); `allowBackup=false`.
6. Un foco rojo grave lleva a «consultar pronto» sin esperar el puntaje.
7. Todo resultado guarda la versión del protocolo. **Cambie `version` en el JSON cada vez que cambie una pregunta o un corte.**

## Decisiones del equipo que no debe revertir
- No mencionar en la app ni en documentos ningún centro, hospital o servicio local de referencia concreto.
- Preguntas y cortes son **provisionales** hasta el panel de expertos; no los presente como validados.
- Nada de IA para clasificar ni redactar resultados. El motor (`lib/domain/motor_puntuacion.dart`) es determinista.

## Licencias de instrumentos
- No copie el texto, la puntuación ni la entrevista del M-CHAT-R/F, ASQ, PEDS ni de otra escala con derechos. El M-CHAT-R/F exige permiso de sus autores para incorporarse a software y debe usarse completo.
- Lo permitido hoy: preguntas con redacción propia alineadas por constructo (`afin_mchat` en el JSON, solo trazabilidad). Esa alineación **no hereda la validez** del instrumento.

## Comandos
```bash
flutter pub get
dart run build_runner build   # tras cambiar tablas drift (genera base_datos.g.dart, que sí se versiona)
dart analyze && flutter test  # ambos deben quedar limpios antes de cada commit
```
Entorno en la nube: `dl.google.com` está bloqueado, así que no hay SDK de Android ni `flutter build apk` ahí; el APK se compila en una máquina con el SDK.

## Trampas ya encontradas
- **E/S de archivos dentro de `testWidgets` se cuelga.** Los servicios con disco (`AlmacenFotos`, `escribirArchivo`) se inyectan y se falsean en `test/ayudas.dart`; las implementaciones reales se prueban en `test/almacen_fotos_test.dart`. Cargar assets en un test: `tester.runAsync(Entorno.crear)`.
- `setState(() => _x = unFuture)` lanza error: calcule el `Future` fuera y asigne en un bloque.
- `ON CONFLICT` de drift: el *upsert* sobre una clave única necesita `target:` explícito.
- Los botones de respuesta del cuestionario van en el pie fijo; en pantallas pequeñas un botón dentro de la lista queda oculto.
- `dart format` reflúa el código: si va a editar con reemplazo de texto, lea primero el texto actual.
- El botón de confirmar del selector de fecha en español es `ACEPTAR`.
- No ejecute ni cargue código o datos de repositorios externos (por ejemplo `.rda`): solo lectura de texto.

## Forma de trabajo
- Una función por vez; después de cada una, `dart analyze` y `flutter test`. No marque algo como terminado sin prueba que lo ejercite de extremo a extremo.
- Pruebas primero para motor y reglas; para pantallas, puede ir después.
- Rama de trabajo: `claude/new-session-2z9nvz`. No cree pull requests sin que se lo pidan.
- Pendiente sin verificar en teléfono real: flujo completo, cámara y compartir de Android.
