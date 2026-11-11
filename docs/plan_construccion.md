# Plan de construcción

Cada pieza se escribe, se prueba con un caso real y recién entonces
se marca. Los scripts van en `skills/niveles-academicos/scripts/` y
el resultado de cada prueba se anota en `docs/pruebas_capas_1_2.md`.

## Revisión del plan (2026-11-11)

Cambios frente al plan original y su motivo:

- **Módulo común (`comun.py`).** Red con reintentos, normalización de
  texto, lectura de docx/md y localización de LibreOffice se escriben
  una vez. Las rutas de Windows dejan de estar fijas en cada script.
- **Claves y cortesía con las bases.** OpenAlex exige clave gratuita
  desde 2026 y Semantic Scholar limita sin clave. El buscador las lee
  de variables de entorno y, si una base falla, sigue con las demás e
  informa cuál falló. No se detiene por una base caída.
- **SciELO.** `search.scielo.org` tiene control antibots y no se
  fuerza. SciELO se cubre con Crossref y OpenAlex, marcando los
  resultados alojados en dominios `scielo`.
- **Índice de fuentes.** `descargar_abierto.py` deja `fuentes/indice.json`
  (DOI, archivo, origen, sha256). Los controles posteriores leen ese
  índice en lugar de adivinar qué hay en la carpeta.
- **Búsqueda de pasajes.** `extraer_texto.py` también localiza una
  frase y devuelve fuente y página. Es lo que el verificador necesita
  para "cita contra pasaje".
- **Control de formato separado del constructor (7b).** Quien fabrica
  el docx no puede ser quien lo da por bueno: `verificar_formato.py`
  revisa el archivo final real.
- **Control final único (7c).** `control_final.py` corre todos los
  controles mecánicos y escribe `entrega/controles.json` con la huella
  del entregable.
- **Hook más estricto (8).** El plan original bastaba con que el
  modelo escribiera "APROBADO". Ahora exige además que los controles
  mecánicos hayan pasado y que el informe corresponda al archivo que
  se entrega (misma huella). Un informe viejo no vale para un docx
  nuevo.

## Convenciones que comparten todas las piezas

Carpeta de un encargo:

```
<trabajo>/
  encargo.md                 tema, nivel, formato, extensión, estado
  fuentes/                   PDF y páginas guardadas
    indice.json              una entrada por fuente descargada
    texto/<fuente>.txt       texto con marcas "=== [p. N] ==="
    fichas.md, matriz_evidencia.md, descartadas.md
  borrador/texto.md          texto en Markdown
  entrega/                   archivo final
    controles.json           resultado de control_final.py
    informe_verificacion.md  dictamen del verificador
```

Todos los scripts: Python 3, UTF-8, sin rutas fijas, `--json` para
salida legible por máquina y código de salida 0 (sin problemas),
1 (hay hallazgos) o 2 (no se pudo ejecutar).

`encargo.md` lleva una línea `estado:` con uno de: `en curso`,
`en verificación`, `aprobado`, `no aprobado`, `suspendido`.

## Capa 1 — herramientas propias
- [ ] 0. `comun.py`: funciones compartidas.
- [ ] 1. `buscar_academico.py`: consulta OpenAlex, Crossref, Semantic
      Scholar y arXiv; marca SciELO; une duplicados por DOI o título;
      devuelve título, autores, año, DOI, citas, tipo, idioma y enlace
      de acceso abierto, en JSON y en tabla. Filtros de año, idioma y
      solo acceso abierto.
- [ ] 2. `descargar_abierto.py`: dado un DOI, una lista o el JSON del
      buscador, localiza la versión de acceso abierto (Unpaywall,
      OpenAlex, Crossref, arXiv y la etiqueta `citation_pdf_url` de la
      página), comprueba que sea un PDF real, lo guarda en `fuentes/`,
      actualiza `indice.json` y anota los fallos en `descartadas.md`.
- [ ] 3. `extraer_texto.py`: PDF a texto con número de página
      (PyMuPDF), un `.txt` por fuente; avisa si el PDF es escaneado;
      opción `--buscar` para localizar un pasaje con su página.
- [ ] 4. `zotero_apa.py`: lee la biblioteca Zotero local (copia de
      solo lectura del sqlite), emite referencias en APA 7 y permite
      buscar por título o DOI para no descargar dos veces.

## Capa 2 — controles que no dependen del modelo
- [x] `verificar_referencias.py`: existencia en Crossref y OpenAlex.
- [ ] 5. `cruzar_citas.py`: toda cita del texto está en referencias y
      toda referencia está citada; autor y año coinciden.
- [ ] 6. `similitud_fuentes.py`: detecta frases del texto casi
      idénticas a las de `fuentes/texto/`, con fuente y página.
- [ ] 7. `construir_docx.py`: constructor único con el formato del
      usuario; renderiza a PDF con LibreOffice y cuenta páginas.
- [ ] 7b. `verificar_formato.py`: sobre el docx final revisa tamaño
      carta, tipografía, interlineado, justificado, títulos, saltos
      de página, marcadores prohibidos, menciones a versiones y
      número de páginas.
- [ ] 7c. `control_final.py`: corre 5, 6, 7b y `verificar_referencias`
      sobre la carpeta del encargo y escribe `entrega/controles.json`.
- [ ] 8. Hook de bloqueo (`hooks/bloqueo_entrega.py`): sin
      `entrega/informe_verificacion.md` con dictamen APROBADO,
      controles mecánicos en regla y huella vigente no se cierra el
      encargo. Mostrar al usuario el cambio a `settings.json` antes
      de aplicarlo.
- [ ] 9. Actualizar los cinco agentes para que usen estas
      herramientas y reinstalar con `instalar.ps1`.

## Capa 3 — profundidad académica
- [ ] 10. Skills por tipo de trabajo: ensayo, monografía, perfil de
       tesis, tesis, artículo, informe.
- [ ] 11. Skills por método: documental, cualitativo, cuantitativo,
       jurídico. Insumo pendiente: libros de metodología del usuario
       y su ubicación.
- [ ] 12. Plantillas de análisis de datos (requiere instalar pandas).
- [ ] 13. Comando de inicio de encargo: crea carpeta, `encargo.md` y
       permite retomar en otra sesión.

## Capa 4 — medición
- [ ] 14. Banco de pruebas con tres a cinco trabajos ya calificados.
       Insumo pendiente: el usuario elige cuáles.

## Prueba de aceptación de las capas 1 y 2
Correr un encargo real de pregrado de punta a punta y revisar el
`informe_verificacion.md`. Registrar el resultado en `PROYECTO.md`.
