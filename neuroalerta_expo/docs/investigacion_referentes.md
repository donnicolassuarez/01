# Referentes, código analizado y evaluación de decisiones — NeuroAlerta Kids

Búsqueda del 28/10/2026: 2 rondas web (≈32 consultas), verificación en fuente primaria donde fue posible y análisis estático
de 3 repositorios abiertos. Cada hallazgo lleva confianza: **A** = fuente primaria o código leído por mí; **B** = resumen
secundario creíble; **C** = blog, prensa o comercial.

**Límites de acceso en este entorno:** no pude abrir `arxiv.org`, `mchatscreen.com`, `drexel.edu`, `hhs.iowa.gov` ni
`calmed.tricare.mil` (fuera de los dominios permitidos). Por eso **no leí el texto del M-CHAT-R/F ni el estudio de ETH en la
fuente**; lo que digo de ellos viene de resultados de búsqueda y está señalado.

## Actualización del 29/10/2026: cambio de plataforma a Expo / React Native

El equipo decidió pasar de Flutter a **Expo (React Native + TypeScript)**. Las referencias a Flutter, drift o Dart en este
informe describen la versión anterior, que se retiró del repositorio (queda en su historial). Lo que cambia:

- **El cifrado de la base ya no es verificable en las pruebas automáticas.** En Flutter una prueba abría el archivo cifrado y
  comprobaba que no se leía sin clave. Con `expo-sqlite` el cifrado (SQLCipher) lo aporta el código nativo, que Jest no carga:
  se prueba la lógica (formato de clave, falla si no hay cifrado, clave incorrecta) y **el cifrado real debe comprobarse en un
  teléfono**.
- **SQLCipher exige una compilación nativa propia**: no corre en Expo Go. La ventaja de «ver la app con un código QR» solo vale
  para la interfaz, con una bandera de desarrollo explícita y una banda roja; para probar el cifrado hay que usar
  `expo run:android` o EAS.
- **Este entorno** tiene bloqueados `docs.expo.dev`, los servidores de Expo y `dl.google.com`: la API se leyó en los tipos de
  los paquetes instalados y no se pudo compilar el APK. Sí se verificó que Metro empaqueta la app para Android y que los
  plugins nativos generan lo esperado (`useSQLCipher=true`, copia de seguridad desactivada, permisos removidos).
- **Backlog aplicado** al rehacer la interfaz: esquema versionado con pruebas de migración (§10.3, parcial: faltan la versión
  del motor y el diccionario del CSV), color calmado para «consultar pronto» y contraste ≥ 7:1 (§10.4).

## 1. Criterios y plan

Frentes: (A) instrumentos y apps de cribado, (B) evidencia general, regulación y ética, (C) base técnica y código,
(D) metodología con agentes, (E) pilotos y herramientas para médicos, (F) ciclo de vida, datos y estilo gráfico.
Criterios de adopción: 1) evidencia de validez; 2) licencia y costo; 3) encaje con las reglas del encargo (orienta, no
diagnostica; sin internet; datos locales); 4) esfuerzo frente a construir; 5) riesgo si falla.

## 2. Instrumentos y apps de cribado

| Referente | Hallazgo clave | Conf. | Correspondencia |
| --- | --- | --- | --- |
| CDC Milestone Tracker | Gratuita, 2 meses–5 años, resumen compartible con el médico; monitoreo, no diagnóstico. CDC evalúa su uso con encuestas (2026); sin estudio revisado por pares | B | Alta como modelo de producto y lenguaje |
| M-CHAT-R/F web | Versión web validada (n=17 900); la precisión del seguimiento depende de entrevista clínica. **Derechos de autor**: gratis para uso clínico, de investigación y formación; incorporarlo a software exige permiso y se usa completo | A/B | Alta para 16–30 meses; ver §6 |
| EDI (México) | Semáforo verde/amarillo/rojo; aplicada por profesionales; concordancia 86,1 % con supervisor | B | Alta para justificar 3 niveles |
| ASQ-3 en español | Validado en Chile, México (α .77–.88) y Perú; la licencia limita el uso | B | Metodología (cortes por edad) |
| GSED (OMS/UNICEF) | Paquete abierto hasta 36 meses: forma corta (cuidador), larga (directa) y psicosocial; app de captura; validación en 7 países (n=8 736 planeado) | B | **Alta**: instrumento abierto para 0–36 meses |
| DM-SWYC, PEDS móvil | Concordancia adecuada; PEDS móvil la usó un agente comunitario, no los padres | B | Media |
| SNAP-IV / Vanderbilt | No diagnostican solos; el estándar usa varios informantes | B | Alta para atención e hiperactividad |
| Guías mexicanas del proyecto (según la conversación previa del equipo): Guía Clínica de Trastornos Generalizados del Desarrollo (Hospital Psiquiátrico Infantil Juan N. Navarro, 2018), Guía del INPRF para TDAH (2010), Guía de Veracruz sobre TEA (2020) y NOM-031-SSA2-1999 | Conozco sus resúmenes por la conversación del equipo; **yo no las abrí** (dominios `gob.mx`, `inprf.gob.mx` y `ssaver.gob.mx` fuera de la red permitida). La del INPRF usa criterios del DSM-IV y solo cubre bien hasta los 6–7 años de inicio; ninguna fija 12 años | B (de segunda mano) | Crítica: mis preguntas parten de conocimiento general, no de la lectura de estas guías; falta trazar cada pregunta a su signo y página |
| Canvas Dx (FDA) | 81 %/98 % pero 68 % indeterminados; solo niños de alto riesgo | B/C | Advertencia regulatoria, no modelo |

## 3. Pilotos similares (padres y médicos)

| Piloto | Quién lo usa | Resultado | Lección para nosotros |
| --- | --- | --- | --- |
| SenseToKnow (Duke) | Tableta en consulta de atención primaria | n=475, sensibilidad 87,8 %, especificidad 80,8 %; su valor predictivo mejora al sumar el cuestionario M-CHAT; ensayo en casa con padres en curso | Combinar fuentes mejora; fuera de nuestro alcance (video/IA) |
| Autism & Beyond (Duke) | Padres, iPhone, ResearchKit | 1 756 familias, 5 618 encuestas, 87,6 % de videos usables; estudio de **factibilidad** | Un piloto honesto reporta factibilidad y aceptación |
| Cribado electrónico en EHR (red de 14 sitios) | Médicos de atención primaria | Tamizaje a los 24 meses 79 %→94 %; derivación tras positivo 10 %→45 %; completar la evaluación sigue abierto | La derivación es el eslabón débil: el «paso recomendado» debe ser claro |
| ASQ-3 electrónico en FQHC | Médicos y familias | Tamizaje 62,7 %→73,6 %; exige licencia anual y costo por prueba | El costo de licencia es una barrera real |
| Afinidata (UNICEF, Bolivia) | Padres, chatbot | Bolivia lo adoptó y escaló (informe de dic. 2025); conectividad desigual | Precedente nacional de orientación digital a padres; nuestro diferencial es funcionar sin internet |
| Revisión de apps parentales (MARS) | Evaluadores | 16 apps de Google Play, puntajes 4,2–4,4/5; otra revisión de 16 apps, media 3,42 | MARS sirve para evaluar nuestra app y las de referencia |

No hay evidencia revisada por pares sobre la precisión de una app operada solo por padres en español (revisión de 2025,
12 estudios, y protocolo de revisión de 2026). **El piloto debe afirmar factibilidad y aceptación, no precisión.**

## 4. Código analizado (solo lectura, sin ejecutar nada descargado)

No existe un repositorio abierto de app de cribado del desarrollo o M-CHAT que valga la pena reutilizar (búsquedas sin
resultados; solo plantillas y proyectos personales sin licencia verificable). Se analizaron tres proyectos de infraestructura.

| Repositorio | Licencia | Qué es | Lección aplicable | Evitar |
| --- | --- | --- | --- | --- |
| `d-score/dscore` (R, GSED) | Apache 2.0 | Calcula el D-score a partir de ítems pasa/falla; ≈3 200 líneas, 28 bloques de prueba | El **algoritmo tiene versión** (`algorithm = "current"` o `"1.8.7"`) además de los datos; tablas de referencia como datos; tratamiento explícito de ítems faltantes | Su modelo estadístico (IRT) no corresponde a un piloto con cortes provisionales |
| `google/android-fhir` (módulo `datacapture`) | Apache 2.0 | Renderiza cuestionarios FHIR sin conexión; 95 archivos Kotlin | Condiciones de aparición con `enableWhen` (operadores y comportamiento TODAS/ALGUNA); módulo propio de validación | Adoptar FHIR completo: sobredimensionado para 3 protocolos |
| `getodk/collect` | Apache 2.0 | Recolección Android sin conexión con XLSForm; módulos `forms`, `entities`, `db` | Formularios como **datos versionados**; pruebas de migración de base de datos (8 casos); política de seguridad publicada; cifrado de envíos por el destinatario | Su cifrado usa AES/CFB y MD5: anticuado, no copiarlo |

Paquetes Flutter para FHIR (`fhir_questionnaire_r4`, `fhir_renderer_questionnaire`, B): existen, pero ninguno garantiza el
estándar completo; no los adoptamos. **ODK/KoBo como alternativa a construir:** cubrirían formularios, fotos y trabajo sin
conexión, pero no el perfil del niño, el consentimiento obligatorio previo, el semáforo ni el historial, y están pensados
para sincronizar datos; se descarta, aunque XLSForm sirve de modelo para nuestros JSON.

## 5. Ciclo de vida de una app de salud y dónde estamos

| Etapa | Estado en el proyecto | Vacío | Referencia |
| --- | --- | --- | --- |
| 1. Descubrimiento y revisión de literatura | Hecha (este documento) | Guías mexicanas del proyecto sin leer en el original | — |
| 2. Requisitos y especificación | El encargo | Trazabilidad requisito→prueba parcial | Práctica SDD (C) |
| 3. Riesgo, ética y regulación | Reglas no negociables, consentimiento | Sin análisis formal de riesgos ni consulta a la regulación boliviana | OMS 2019; marco IMDRF/FDA (B) |
| 4. Contenido clínico | Preguntas provisionales | Panel de expertos; licencias | ASQ/M-CHAT |
| 5. Diseño (UX, texto, estilo) | Material 3 con color semilla | Guía visual, pruebas con padres | §7 |
| 6. Arquitectura y construcción | Hecha | Pruebas de migración de esquema | ODK |
| 7. Pruebas | 43 pruebas | Dispositivo real, accesibilidad, usabilidad | MARS, SUS |
| 8. Seguridad y privacidad | Cifrado, sin red, sin copias | Revisión externa | ISO/TS 82304-2 (B) |
| 9. Piloto de campo | Pendiente | Protocolo del piloto y consentimiento institucional | Autism & Beyond (factibilidad) |
| 10. Distribución y mantenimiento | APK de depuración | Firma de release, versionado | — |
| 11. Evaluación posterior | Pendiente | Qué se mide y cuándo | MARS, SUS |

ISO/TS 82304-2 cubre el ciclo de vida de apps de salud (B); IEC 62304 y 62366 aparecen solo como estándares relacionados
(no verificados); NHS DTAC no se pudo verificar.

## 6. Datos, M-CHAT y decisión sobre los ítems

- **Qué se hizo:** el protocolo 0–36 meses pasó a `0.2.0-provisional` con 22 preguntas, 16 alineadas **por constructo** con
  el M-CHAT-R/F (respuesta al nombre, señalar para pedir y para compartir, seguir el señalamiento, imitación, juego
  simbólico, referencia social, etc.) y redacción propia. **No** reproduce su texto, su puntuación ni su entrevista y **no
  hereda su validez**. Los constructos los fijé de mi conocimiento del instrumento, sin poder contrastarlos con su texto
  (dominio bloqueado): conviene que el equipo los revise contra la versión oficial en español.
- **Camino sólido:** pedir permiso a los autores (borrador en `docs/solicitud_permiso_mchat.md`) o basarse en GSED (abierto).
- **Recolección y exportación (ODK, dscore):** añadir un diccionario de datos del CSV y la versión del motor junto a la
  del protocolo; versionar el esquema con pruebas de migración. La exportación del equipo podría cifrarse para el
  destinatario (patrón de ODK, con algoritmos modernos).

## 7. Estilo gráfico y de voz

| Aspecto | Medición o evidencia | Decisión propuesta |
| --- | --- | --- |
| Legibilidad del texto | Escala INFLESZ (>55 recomendado, B); estimación propia con silabeo aproximado: preguntas y niveles entre 70 y 80, «bastante fácil»; el aviso obligatorio 54,2 | Mantener el aviso literal (regla 2); medir todo texto nuevo; validar con padres reales |
| Contraste | Color semilla 2A7F8E sobre blanco: 4,64 (AA exige 4,5) | Oscurecer a ≈1B5E6B (7,34) para texto y botones |
| Color de «consultar pronto» | Hoy usa el rojo de error | Cambiar a un tono cálido y calmado con icono; el rojo de alarma aumenta la ansiedad (guías de diseño calmado, C) |
| Sistema de diseño | NHS (derivado de GOV.UK, guía WCAG 2.2 AA, B) y Material 3 | Seguir Material 3 con tokens propios; tomar de NHS las reglas de foco y de texto |
| Tamaños táctiles y texto | Botones de 50–56 dp, texto escalable | Probar con texto al 200 % y lector de pantalla |
| Voz | Tono tranquilo, sin jerga, sin culpa (C) | Guía de redacción con palabras permitidas y prohibidas |
| Identidad (firma) | Nombre provisional | Decidir nombre, ícono y lema; no usar marcas de organismos de salud |

Son propuestas de diseño apoyadas en mediciones y en fuentes de menor peso, no hallazgos clínicos.

## 8. Metodología con agentes (resumen)

- **Harness (A):** publicación de Anthropic del 26/11/2025: lista de funciones en JSON, archivo de progreso, una función por
  sesión, commits y prueba de extremo a extremo. El `CLAUDE.md` del proyecto aplica lo que corresponde.
- **Archivos de instrucciones (B):** resúmenes del estudio de ETH indican que los generados automáticamente perjudican y los
  escritos a mano ayudan; por eso el `CLAUDE.md` es manual y corto. No lo verifiqué en la fuente.
- **TDD y SDD (C):** sin estudios controlados; práctica sin herramienta adicional. En esta sesión las pruebas detectaron
  cuatro errores reales (upsert, `setState`, botón oculto, aviso fuera de vista).
- **Multiagente (C):** solo como revisor aparte; no sustituye a expertos clínicos.

## 9. Decisiones

| Decisión | Elección | Razón |
| --- | --- | --- |
| Origen de las preguntas | Alineación por constructo hoy; M-CHAT con permiso o GSED después | Sin licencia no se puede incorporar el instrumento |
| Qué afirma el piloto | Factibilidad y aceptación | No hay evidencia de precisión para apps de padres |
| Construir o usar ODK/FHIR | Construir | Requisitos de consentimiento, semáforo e historial; datos locales |
| Cortes | Provisionales, marcados | No hay base para validarlos aún |
| Estilo | Material 3 con tokens propios, contraste AA, tono calmado | Medido y de bajo costo |

## 10. Backlog priorizado

1. (Equipo) Pedir permiso a los autores del M-CHAT-R/F; leer en el original las cuatro guías mexicanas del proyecto (ver §2) y trazar cada pregunta a su signo y página; confirmar constructos con la versión oficial.
2. Panel de expertos y prueba de usabilidad (SUS) con padres en teléfonos reales.
3. Esquema versionado con pruebas de migración; versión del motor en el resultado; diccionario de datos del CSV.
4. Color calmado para «consultar pronto» y contraste ≥ 7:1; pruebas con texto al 200 %.
5. Resumen compartible para el médico (modelo CDC) sin datos identificables.
6. Comprobación de legibilidad INFLESZ como prueba automática.
7. Exportación cifrada para el destinatario; opcional: QuestionnaireResponse de FHIR.

## Fuentes

- CDC: [Milestone Tracker](https://cdc.gov/act-early/families/milestones-matter.html) · [lanzamiento](https://archive.cdc.gov/www_cdc_gov/media/releases/2017/p1024-app-development-milestones.html) · [aviso de evaluación 2026](https://public-inspection.federalregister.gov/2023-02951.pdf)
- M-CHAT-R/F: [validación web](https://pmc.ncbi.nlm.nih.gov/articles/PMC8536796) · [ensayo](https://pmc.ncbi.nlm.nih.gov/articles/PMC5397992) · [traducciones y permisos](https://mchatscreen.com/mchat-rf/translations/) · [versión España](https://mchatscreen.com/wp-content/uploads/2015/05/M-CHAT-R_F_Spanish_Spain.pdf) · [permisos](https://hipaa.jotform.com/211646680007048)
- EDI: [confiabilidad](https://www.scielo.org.mx/pdf/bmim/v71n5/v71n5a4.pdf) · [grupo 15](https://www.scielo.org.mx/pdf/bmim/v72n6/1665-1146-bmim-72-06-00385.pdf)
- ASQ-3: [Chile](https://andespediatrica.cl/index.php/rchped/article/download/5849/5520/53197) · [Argentina](https://scholarsbank.uoregon.edu/items/f6f4f420-0d3c-4172-beb7-f7c288cbaddd/full) · [comparativo](https://agesandstages.com/wp-content/uploads/2026/01/ASQ-Parent-Report-Tools-Comparison-Chart-2025.pdf)
- GSED: [paquete OMS](https://www.covid.comesa.int/publications/i/item/WHO-MSD-GSED-package-v1.0-2023.1) · [forma corta](https://www.paho.org/en/documents/global-scales-early-development-v10-short-form-caregiver-reported) · [protocolo BMJ Open](https://bmjopen.bmj.com/content/13/1/e062562) · [paquete dscore](https://rdrr.io/cran/dscore/man/dscore-package.html)
- Pilotos: [SenseToKnow (NIMH)](https://www.nimh.nih.gov/news/science-news/2024/digital-autism-screening-tool-could-enhance-early-identification) · [Autism & Beyond](https://neurosciencenews.com/autism-app-data-9219/) · [EHR red de 14 sitios](https://pediatricsnationwide.org/2025/07/23/streamlining-autism-diagnosis-how-electronic-health-record-tools-increased-early-identification-and-referrals-in-a-primary-care-network/) · [ASQ en FQHC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11420335/) · [Afinidata (UNICEF)](https://www.unicef.org/innovation/stories/artificial-intelligence-early-childhood-innovation)
- Apps y evaluación: [revisión 2025](https://doaj.org/article/9bd8350001ff4cdd97f8ed8524ba735d) · [PEDS móvil](https://repository.up.ac.za/bitstreams/fcce895e-07c2-464c-88f4-4ef27e5c964d/download) · [MARS, apps parentales](https://mhealth.amegroups.org/article/view/29870) · [MARS, 2023](https://doaj.org/article/9ab0c51de12643678189f7bb24b44656)
- Regulación y ética: [OMS 2019](https://www.who.int/news-room/detail/17-04-2019-who-releases-first-guideline-on-digital-health-interventions) · [software de apoyo a decisiones (FDA)](https://www.thefdalawblog.com/2019/10/fda-issues-a-second-draft-guidance-for-clinical-decision-support-software/) · [Canvas Dx](https://hcplive.com/view/fda-grants-de-novo-clearance-to-ai-based-autism-diagnosis-aid) · [ISO/TS 82304-2](https://www.evs.ee/en/iso-ts-82304-2-2021) · [WHO SMART](https://smart.who.int/index.html)
- Escalas TDAH y guías: [SNAP-IV y Vanderbilt](https://novopsych.com/es-us/alternatives-to-the-conners-for-child-adhd-assessment-snap-iv-swan-and-vanderbilt/) · [guía mexicana de TEA (resumen)](https://www.actuamed.com.mx/node/885206)
- Técnica: [drift, cifrado](https://drift.simonbinder.eu/platforms/encryption) · [SDC de Android FHIR](https://developers.google.com/open-health-stack/android-fhir/data-capture) · [paquetes Flutter FHIR](https://pub.dev/packages/fhir_questionnaire_r4) · [ODK/CommCare en Malawi](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4216812/) · [XLSForm](https://www.casrai.org/guides/kobotoolbox-mobile-field-data-collection) · repositorios [dscore](https://github.com/d-score/dscore), [android-fhir](https://github.com/google/android-fhir), [ODK Collect](https://github.com/getodk/collect)
- Diseño y texto: [sistema de diseño NHS](https://service-manual.nhs.uk/design-system) · [escala INFLESZ](https://recyt.fecyt.es/index.php/ASSN/article/view/1953) · [diseño calmado](https://www.uxmatters.com/mt/archives/2025/05/designing-calm-ux-principles-for-reducing-users-anxiety.php)
- Agentes: [Anthropic, harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) · [resumen del estudio ETH](https://arxiviq.substack.com/p/evaluating-agentsmd-are-repository) · [Spec Kit, Kiro, OpenSpec](https://ssojet.com/blog/best-spec-driven-development-tools) · [TDD con agentes](https://circleci.com/blog/test-hooks-ai-development)
