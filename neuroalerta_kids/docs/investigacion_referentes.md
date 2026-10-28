# Referentes y evaluación previa a definir el modelo — NeuroAlerta Kids

Fecha de la búsqueda: 28/10/2026. Método: 2 rondas de búsqueda web (16 consultas) más 2 verificaciones en fuente primaria.
Cada hallazgo lleva un grado de confianza: **A** = fuente primaria o revisión revisada por pares leída por mí;
**B** = resumen secundario creíble; **C** = blog, prensa o fuente comercial. Donde no pude acceder a la fuente, lo digo.

## 1. Plan y criterios

Cuatro frentes: (A) instrumentos y apps específicos de cribado del desarrollo; (B) evidencia general sobre apps para
padres, regulación y ética; (C) base técnica y plantillas; (D) metodología de desarrollo con agentes (harness, TDD, SDD).

Criterios para decidir si algo se adopta: 1) evidencia de validez en la población y edad; 2) licencia y costo;
3) encaje con las reglas no negociables del encargo (orienta, no diagnostica; sin internet; sin datos que salgan);
4) esfuerzo de adopción frente a construir; 5) riesgo si está mal.

## 2. Frente A — Modelos específicos

| Referente | Qué es | Hallazgo clave | Conf. | Correspondencia |
| --- | --- | --- | --- | --- |
| CDC Milestone Tracker | App gratuita para padres, 2 meses a 5 años, listas ilustradas, resumen para compartir con el médico, recordatorios | Es de **monitoreo**, no diagnóstica; guía cuándo actuar y a quién llamar | B | Alta como modelo de producto y de lenguaje. No cubre 6–12 años |
| M-CHAT-R/F (versión web) | 20 preguntas a padres, 16–30 meses, con entrevista de seguimiento | Versión web validada en un ensayo no aleatorizado (n=17 900), sensibilidad y especificidad altas; la precisión del seguimiento depende de una entrevista clínica. Evidencia de sus propios desarrolladores | A/B | Alta para el tramo 0–36 meses |
| EDI (México) | Prueba de tamizaje mexicana <5 años con semáforo verde/amarillo/rojo | La aplican profesionales; estudios de confiabilidad (concordancia 86,1 % con supervisor) y validación de grupos de edad. **Ningún estudio con aplicación por padres** | B | Alta como referente nacional y para el semáforo; no es transferible tal cual |
| ASQ-3 en español | Cuestionario a padres con puntos de corte por edad | Validaciones en Chile, México (α .77–.88) y Perú urbano; el costo de licencia limita su uso | B | Alta como referencia metodológica |
| DM-SWYC (Chile) | Cuestionario breve a padres, comparado con ASQ-3 | Correlación adecuada; los autores recomiendan complementarlo para no sobre-derivar | B | Media; no verifiqué licencia |
| PEDS en teléfono | Versión móvil de PEDS | 207 cuidadores, concordancia 100 %/96 % con papel, pero la usó un agente comunitario, no los padres | B | Media |
| Canvas Dx (Cognoa) | Ayuda diagnóstica con IA, autorizada por la FDA | 81 %/98 % frente a panel clínico, pero 68 % de casos "indeterminados"; solo niños de alto riesgo; sin utilidad clínica demostrada | B/C | Baja como modelo; alta como advertencia regulatoria y de validación |
| SNAP-IV / Vanderbilt | Escalas de atención e hiperactividad (18 ítems DSM-5 / normas 5–12 años) | No diagnostican por sí solas; el estándar usa varios informantes (casa y escuela) | B | Alta para los tramos 3–6 y 7–12 |
| Guías CENETEC (México) | Guía de práctica clínica de TEA; la de TDAH no la encontré | Solo conseguí un resumen; **no leí el texto ni sus signos de alarma** | B (parcial) | Crítica: el encargo dice que las preguntas se basan en ellas |

## 3. Frente B — Evidencia general, regulación y ética

- **No hay evidencia de precisión para apps operadas por los propios padres.** Una revisión sistemática de 2025 (12 estudios,
  PRISMA) señala vacíos de validez externa, diversidad cultural y privacidad; un protocolo de revisión de 2026 confirma que
  no existe una revisión de apps de tamizaje neurológico en 0–24 meses (B). Consecuencia: el piloto puede afirmar
  **factibilidad, usabilidad y aceptación**, no precisión.
- **WHO 2019:** exige proteger la privacidad, consentimiento y permitir salir del servicio; los resultados dependen del contexto (B).
- **Regulación:** el marco FDA/IMDRF clasifica según la importancia de la información y la gravedad de la condición; las
  funciones para pacientes que orientan el manejo de condiciones graves quedan fuera de la discreción de no regulación (B,
  documentos de 2019 que pueden estar desactualizados). **No investigué la regulación boliviana (AGEMED).** Mientras la app
  se distribuya solo como piloto y sin Google Play, la exposición es baja, pero la redacción "orienta, no diagnostica" es
  decisiva.
- **Su propio estudio** (monografía sobre médicos de primer nivel de Cobija) aporta lo más específico del contexto: el
  primer nivel decide si un niño avanza a evaluación; la ruta local existente es la **Sala de Desarrollo Infantil Temprano
  del Hospital Roberto Galindo Terán** y el **Centro de Educación Especial Cobija B**; y cita los hitos redefinidos al 75 %
  (Zubler 2022), el M-CHAT-R/F (Robins 2014), Hyman 2020 y Wolraich 2019.

## 4. Frente C — Base técnica

- No encontré una plantilla abierta Flutter + drift + cifrado orientada a salud; hay piezas sueltas (ejemplos oficiales de
  drift). **Construir a medida está justificado**, reutilizando esas piezas (B).
- La documentación de drift ofrece dos rutas de cifrado que se contradicen entre páginas: SQLite3MultipleCiphers
  (drift ≥ 2.32 y sqlite3 3.x) y `sqlcipher_flutter_libs`, que ya figura como fin de vida. Elegí la primera y una prueba
  confirma que el archivo no se puede leer sin clave. La documentación advierte además de las copias de seguridad de
  Android, por eso `allowBackup=false`.

## 5. Frente D — Metodología con agentes

**Harness (A, verificado).** La publicación de Anthropic del 26/11/2025 describe los fallos de agentes de larga duración:
intentar todo de una vez, declarar la victoria antes de tiempo, traspasos desordenados y marcar funciones como
terminadas sin prueba de extremo a extremo. Prácticas: lista de funciones en JSON con estado pasa/falla, archivo de
progreso, script de arranque, una función por sesión con commit, y prueba de extremo a extremo antes de seguir.

**Archivos de instrucciones (B).** Un estudio de ETH Zurich (arXiv 2602.11988) se conoce solo por resúmenes: los archivos
generados automáticamente reducen el éxito y suben el costo más de 20 %; los escritos por personas ayudan cuando traen
información que no está ya en el repositorio. **No pude abrir arXiv desde este entorno** (dominio no permitido); la cifra
no está verificada en la fuente.

**TDD con agentes (C).** Hay consenso entre practicantes y ningún estudio controlado. En esta sesión las pruebas
detectaron tres errores reales (conflicto del *upsert*, `setState` devolviendo un `Future`, botón «No sé» oculto en
pantallas pequeñas): es una anécdota, no evidencia.

**SDD (C).** Spec Kit (MIT, independiente del agente), Kiro (IDE propio, orden especificación→diseño→tareas, riesgo de
dependencia) y OpenSpec (ligero, versionado en el repositorio). Todas las comparaciones son de sitios afines a los
proveedores; no hay una evaluación independiente de si mejoran el código.

**Instancias y agentes (C).** Separar los agentes de pruebas y de implementación es un patrón con pocos datos; hay
indicios de que un agente tiende a elogiar su propio trabajo.

## 6. Evaluación de decisiones

| Decisión | Opciones | Elección | Razón | Riesgo residual |
| --- | --- | --- | --- | --- |
| Origen de las preguntas | (1) redactarlas a partir de signos [actual]; (2) adaptar instrumentos abiertos; (3) licenciar ASQ-3 | **(2) híbrida, con (1) como respaldo** | Hay evidencia de validez en instrumentos conocidos; (1) no tiene ninguna. (3) tiene costo | Verificar licencias; el M-CHAT-R/F exige seguimiento clínico |
| Alcance de lo que afirma el piloto | Precisión / factibilidad | **Factibilidad y aceptación** | No hay evidencia de precisión para apps de padres | Jurado esperando "detecta" |
| Cortes de puntuación | Propios / de cada instrumento | **Los del instrumento donde exista; propios solo marcados provisionales** | Los cortes inventados no son defendibles | Mezclar escalas complica el motor |
| Semáforo de 3 niveles | Mantener / otro | **Mantener** | Coincide con la EDI de México | Etiquetas por revisar con expertos |
| SDD | Adoptar herramienta / adoptar práctica | **Práctica, sin herramienta** | `encargo` ya es la especificación; falta trazabilidad | Menos disciplina si el equipo crece |
| TDD | Estricto / mixto | **Mixto**: pruebas primero en motor y reglas; después en interfaz | El motor es determinista y barato de probar | — |
| Harness | Mínimo / completo | **Ligero**: CLAUDE.md escrito a mano, `feature_list.json`, prueba antes de cada commit | Respaldo directo de Anthropic; el estudio ETH desaconseja generarlo | Mantenerlo corto |
| Multiagente | Sí / no | **No** para código; **sí** como revisor aparte | Escala pequeña; el elogio propio sesga | Un revisor no sustituye a expertos clínicos |

## 7. Qué investigaciones previas corresponden

**Usar ya:** hitos CDC 2022 al 75 % (Zubler) y M-CHAT-R/F (ambos ya citados en su monografía) para el tramo 0–36;
Vanderbilt/SNAP-IV como referencia para atención e hiperactividad; la publicación de harness de Anthropic; el semáforo EDI
como justificación de los tres niveles; su monografía como contexto local.
**Usar con cautela:** ASQ-3 (licencia), DM-SWYC, PEDS móvil, SDD (evidencia débil).
**No aplica como modelo:** Canvas Dx (diagnóstico con IA, otro tipo de producto).

## 8. Vacíos que no pude cerrar

1. Texto de las guías CENETEC (TEA y TDAH): sin él, "basadas en guías mexicanas" no es verificable.
2. Licencias de M-CHAT-R/F, SNAP-IV, Vanderbilt y DM-SWYC.
3. Regulación boliviana de software de salud.
4. Estudio de ETH en fuente primaria (arXiv bloqueado).
5. Ninguna fuente demuestra precisión de una app de padres en español.

## 9. Acciones propuestas, en orden

1. Obtener los documentos CENETEC y revisar licencias (el equipo, no el agente: son decisiones de acceso y legales).
2. Reemplazar o alinear los ítems del tramo 0–36 con M-CHAT-R/F y los hitos CDC 2022; actualizar `fuente` y `version`.
3. Añadir al resultado la ruta local (Sala de Desarrollo Infantil Temprano; Centro Cobija B) como "paso recomendado".
4. Redactar `CLAUDE.md` corto y `feature_list.json` con los 6 criterios de aceptación y su estado.
5. Panel de expertos sobre cortes y preguntas; incluir a los médicos del estudio de Cobija.
6. Prueba con teléfonos reales y medición de usabilidad (SUS) como único resultado de eficacia del piloto.

## Fuentes

- [CDC Milestone Tracker (CDC)](https://cdc.gov/act-early/families/milestones-matter.html) · [lanzamiento 2017](https://archive.cdc.gov/www_cdc_gov/media/releases/2017/p1024-app-development-milestones.html)
- [M-CHAT-R/F web, validación](https://pmc.ncbi.nlm.nih.gov/articles/PMC8536796) · [ensayo en atención primaria](https://pmc.ncbi.nlm.nih.gov/articles/PMC5397992)
- [EDI México, confiabilidad del semáforo](https://www.scielo.org.mx/pdf/bmim/v71n5/v71n5a4.pdf) · [EDI, validación de grupo 15](https://www.scielo.org.mx/pdf/bmim/v72n6/1665-1146-bmim-72-06-00385.pdf)
- [ASQ-3 en Chile](https://andespediatrica.cl/index.php/rchped/article/download/5849/5520/53197) · [ASQ-3 en Argentina](https://scholarsbank.uoregon.edu/items/f6f4f420-0d3c-4172-beb7-f7c288cbaddd/full) · [comparativo ASQ 2025](https://agesandstages.com/wp-content/uploads/2026/01/ASQ-Parent-Report-Tools-Comparison-Chart-2025.pdf)
- [Revisión de apps en atención temprana, 2025](https://doaj.org/article/9bd8350001ff4cdd97f8ed8524ba735d) · [PEDS en teléfono](https://repository.up.ac.za/bitstreams/fcce895e-07c2-464c-88f4-4ef27e5c964d/download)
- [Canvas Dx, FDA De Novo](https://hcplive.com/view/fda-grants-de-novo-clearance-to-ai-based-autism-diagnosis-aid) · [revisión de un asegurador](https://www.southcarolinablues.com/web/public/brands/medicalpolicy/external/external-policies/digital-health-technologies-diagnostic-applications)
- [Guía mexicana de TEA (resumen)](https://www.actuamed.com.mx/node/885206) · [SNAP-IV, Vanderbilt y alternativas](https://novopsych.com/es-us/alternatives-to-the-conners-for-child-adhd-assessment-snap-iv-swan-and-vanderbilt/)
- [OMS 2019, intervenciones digitales](https://www.who.int/news-room/detail/17-04-2019-who-releases-first-guideline-on-digital-health-interventions) · [software de apoyo a decisiones clínicas (FDA)](https://www.thefdalawblog.com/2019/10/fda-issues-a-second-draft-guidance-for-clinical-decision-support-software/)
- [drift: cifrado](https://drift.simonbinder.eu/platforms/encryption) · [drift: ejemplos](https://drift.simonbinder.eu/docs/examples/)
- [Anthropic: harnesses para agentes de larga duración](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Resumen del estudio de ETH sobre AGENTS.md](https://arxiviq.substack.com/p/evaluating-agentsmd-are-repository) · [crítica](https://codex.danielvaughan.com/2026/04/13/what-eth-zurich-paper-gets-wrong-right-about-agents-md/)
- [Spec Kit vs Kiro vs OpenSpec](https://ssojet.com/blog/best-spec-driven-development-tools) · [Spec Kit y Kiro](https://codemyspec.com/blog/spec-kit-vs-kiro)
- [TDD con agentes (CircleCI)](https://circleci.com/blog/test-hooks-ai-development) · [pruebas frente a instrucciones](https://caimito.net/en/blog/2026/04/17/tests-beat-instructions-for-ai-coding-agents.html)
