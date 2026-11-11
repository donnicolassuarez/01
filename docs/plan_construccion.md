# Plan de construcción

Cada pieza se escribe, se prueba con un caso real y recién entonces
se marca. Los scripts van en
`skills/niveles-academicos/scripts/`.

## Capa 1 — herramientas propias
- [ ] 1. `buscar_academico.py`: consulta OpenAlex, Crossref, Semantic
      Scholar y SciELO; devuelve título, autores, año, DOI, citas y
      enlace de acceso abierto, en JSON y en tabla.
- [ ] 2. `descargar_abierto.py`: dado un DOI o una lista, localiza la
      versión de acceso abierto y la guarda en `fuentes/`.
- [ ] 3. `extraer_texto.py`: PDF a texto con número de página
      (PyMuPDF), un `.txt` por fuente, para buscar pasajes.
- [ ] 4. `zotero_apa.py`: lee la biblioteca Zotero local (copia de
      solo lectura del sqlite) y emite referencias en APA 7.

## Capa 2 — controles que no dependen del modelo
- [x] `verificar_referencias.py`: existencia en Crossref y OpenAlex.
- [ ] 5. `cruzar_citas.py`: toda cita del texto está en referencias y
      toda referencia está citada; autor y año coinciden.
- [ ] 6. `similitud_fuentes.py`: detecta frases del texto casi
      idénticas a las de los PDF de `fuentes/`.
- [ ] 7. `construir_docx.py`: constructor único con el formato del
      usuario; renderiza a PDF con LibreOffice y cuenta páginas.
- [ ] 8. Hook de bloqueo: sin `entrega/informe_verificacion.md` con
      dictamen APROBADO no se cierra el encargo. Mostrar al usuario
      el cambio a `settings.json` antes de aplicarlo.
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
