---
name: niveles-academicos
description: Perfiles de exigencia por nivel académico (pregrado, maestría, doctorado, postdoctorado) y rúbrica de revisión. Usar al iniciar, redactar, revisar o verificar cualquier trabajo académico para ajustar fuentes, teoría, método, extensión y criterios de calidad al nivel del encargo.
---

# Niveles académicos

El nivel lo fija el encargo. Si no se indica, es pregrado de 2.º año.
El nivel describe a quien firma el trabajo: no se sube para "mejorar"
un trabajo de pregrado ni se baja para ahorrar esfuerzo.

## Perfiles

### Pregrado
- **Propósito:** mostrar comprensión del tema y orden al exponerlo.
- **Fuentes:** 5 a 12, en su mayoría en español y accesibles:
  manuales, artículos de revisión, normas y datos oficiales.
- **Teoría:** uno o dos conceptos o autores bien explicados y
  aplicados al caso. Sin triangulaciones ni jerga.
- **Método:** descriptivo o documental, dicho en pocas líneas.
- **Aporte:** una lectura ordenada del caso y una opinión razonada.
- **Referencias:** máximo página y media.
- **Riesgo a evitar:** un texto demasiado sofisticado delata que no
  lo escribió el estudiante.

### Maestría
- **Propósito:** aplicar teoría y método a un problema delimitado.
- **Fuentes:** 25 a 50, con mayoría de artículos arbitrados y
  literatura en inglés cuando el tema lo requiera.
- **Teoría:** marco teórico articulado, con las categorías que luego
  se usan en el análisis.
- **Método:** diseño justificado (enfoque, técnica, fuentes o
  muestra, procedimiento de análisis) y límites reconocidos.
- **Aporte:** aplicación rigurosa a un caso; hallazgos propios.
- **Revisión:** pasa por el revisor.

### Doctorado
- **Propósito:** aporte original al conocimiento del campo.
- **Fuentes:** estado del arte amplio (80 o más en una tesis; 40 a
  70 en un artículo), con las obras fundacionales y la producción
  de los últimos cinco años.
- **Teoría:** posición propia frente a los debates; las categorías
  se discuten, no solo se adoptan.
- **Método:** replicable, con criterios de validez o confiabilidad
  y tratamiento de sesgos. Datos y procedimientos trazables.
- **Aporte:** vacío identificado en la literatura y contribución
  delimitada (teórica, empírica o metodológica).
- **Revisión:** revisor obligatorio, con al menos una vuelta.

### Postdoctorado
- **Propósito:** intervenir en la frontera del debate; texto
  publicable en revista indexada.
- **Fuentes:** literatura de frontera y preprints recientes, además
  del canon del área.
- **Teoría y método:** como doctorado, con comparación explícita
  frente a los trabajos más cercanos.
- **Aporte:** qué cambia en el debate después de este trabajo.
- **Formato:** el de la revista o convocatoria de destino, que
  manda sobre el formato UAP.
- **Revisión:** revisor obligatorio, dos vueltas si hay cambios
  mayores.

## Rúbrica de revisión

Cada criterio se puntúa de 1 a 5. Mínimo para aprobar: promedio 3,5
en pregrado, 4 en maestría, 4,3 en doctorado y postdoctorado, sin
ningún criterio por debajo de 3.

| Criterio | Pregrado | Maestría | Doctorado y postdoc |
|---|---|---|---|
| Pregunta o tesis | Clara | Delimitada | Original y relevante |
| Marco teórico | Conceptos bien usados | Articulado | Posición propia |
| Método | Enunciado | Justificado | Replicable y válido |
| Evidencia | Suficiente | Arbitrada | Exhaustiva y reciente |
| Argumento | Ordenado | Coherente | Resiste objeciones |
| Aporte | Opinión razonada | Hallazgos propios | Contribución al campo |
| Escritura | Correcta | Precisa | De publicación |

## Dónde buscar
- OpenAlex (api.openalex.org): exige clave gratuita desde 2026
  (variable `OPENALEX_API_KEY`). Crossref (api.crossref.org): libre;
  con `AGENTE_ACADEMICO_CORREO` entra en el grupo de cortesía.
  Semantic Scholar para citas y trabajos relacionados (sin
  `S2_API_KEY` limita las consultas). `buscar_academico.py` consulta
  las tres y arXiv.
- En español: SciELO, Redalyc, Dialnet, La Referencia y repositorios
  de universidades bolivianas. `search.scielo.org` tiene control
  antibots y no se fuerza: SciELO se cubre con Crossref y OpenAlex
  (`--scielo`); lo que no se pueda descargar lo consigue el usuario.
- Bolivia: Gaceta Oficial, INE, UDAPE, ministerios, Tribunal
  Constitucional, gobernaciones y municipios.

## Límites que se informan, no se disimulan
- Solo se usa lo que se pudo abrir y leer. Si una obra clave es de
  pago, se informa al usuario para que la consiga.
- No se generan datos de campo. Se diseñan instrumentos y se
  analizan los datos que el usuario entregue.
- El aporte original se propone; lo decide quien firma.

## Herramientas
En `scripts/` (instaladas en
`C:\Users\Usuario\.claude\skills\niveles-academicos\scripts\`).
Todas aceptan `--json` y salen con 0 (sin problemas), 1 (hay
hallazgos) o 2 (no se pudo ejecutar). `--help` da el uso completo.

- `buscar_academico.py "consulta" [--desde AAAA] [--idioma es] [--solo-abierto] [--scielo] [--salida archivo.json]`:
  OpenAlex, Crossref, Semantic Scholar y arXiv, sin duplicados.
- `zotero_apa.py --doi <DOI> | --buscar "texto" | --coleccion "nombre"`:
  busca en la biblioteca Zotero local y da la referencia APA 7.
- `descargar_abierto.py <DOI | archivo de DOI> --carpeta <trabajo>/fuentes`:
  baja el PDF abierto, actualiza `fuentes/indice.json` y anota los
  fallos en `fuentes/descartadas.md`.
- `extraer_texto.py <trabajo>/fuentes`: texto con número de página en
  `fuentes/texto/`. Con `--buscar "frase"` localiza un pasaje y su página.
- `cruzar_citas.py <texto .md o .docx>`: citas sin referencia,
  referencias no citadas, autor o año que no coinciden.
- `similitud_fuentes.py <texto> <trabajo>/fuentes`: oraciones copiadas
  o casi idénticas a las fuentes, con archivo y página.
- `construir_docx.py <borrador/texto.md> --salida <entrega/x.docx> --tipo <tipo>`:
  constructor único con el formato UAP; cuenta páginas.
- `verificar_formato.py <x.docx> [--tipo] [--min-paginas] [--max-paginas]`:
  control de formato del archivo final, independiente del constructor.
- `verificar_referencias.py <archivo .txt, .md o .docx>`: busca cada
  referencia en Crossref y OpenAlex (ENCONTRADA, DUDOSA o NO
  ENCONTRADA). Libros, leyes y documentos oficiales suelen salir NO
  ENCONTRADA y se comprueban contra el archivo guardado en `fuentes/`.
- `control_final.py <carpeta del trabajo> [--archivo entrega/x.docx] [--sin-red]`:
  corre los controles sobre el entregable y escribe
  `entrega/controles.json` (lo lee el hook de cierre) y
  `entrega/controles.md` (lo lee el verificador).
