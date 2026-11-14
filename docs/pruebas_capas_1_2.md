# Pruebas de las capas 1 y 2 (2026-11-11)

Hechas en un contenedor Linux con Python 3.13, LibreOffice y la
fuente Carlito (mismas métricas que Calibri). Nada se probó en
Windows ni con Python 3.14. Las salidas quedaron en
`pruebas/salida/`, que no se versiona; los casos de entrada y los
scripts de prueba están en `pruebas/`.

## Resultado por pieza

| Pieza | Caso | Resultado |
|---|---|---|
| `buscar_academico.py` | Dos consultas reales sobre incendios y emisiones en la Amazonía boliviana | Crossref y Semantic Scholar: 29 resultados únicos de 30 por consulta. Una base caída no detiene a las demás |
| `descargar_abierto.py` | 8 entradas reales | 5 PDF obtenidos (PLOS, SciELO Bolivia, arXiv, Frontiers, Zenodo) con huella verificada; el resto en `descartadas.md` con motivo |
| `extraer_texto.py` | Los 4 PDF descargados | Páginas iguales a las del PDF (12, 13, 35 y 9). Frase copiada hallada en su página; frase inventada no hallada |
| `zotero_apa.py` | Biblioteca sintética con el esquema real y 9 ítems | Referencias APA 7 revisadas a mano. **No es prueba con caso real** |
| `cruzar_citas.py` | Monografía real del usuario y caso con errores sembrados | 30 citas revisadas a mano, sin falsos positivos. Detecta todos los errores sembrados y nada más |
| `similitud_fuentes.py` | Texto con tres oraciones sembradas contra PDF reales | Marca las tres con su página y ninguna paráfrasis. 30 fuentes en 0,84 s |
| `construir_docx.py` | `pruebas/casos/ensayo_prueba.md` | 4 páginas carta, revisadas página por página en imagen |
| `verificar_formato.py` | Ensayo de prueba, 9 docx con un defecto cada uno y la monografía real | Conforme; 9 de 9 defectos en su párrafo; monografía con 10 errores confirmados a mano |
| `control_final.py` | Encargo bueno, encargo malo y monografía real | Bueno aprueba; malo no aprueba y señala cita sin referencia, copia literal y marcador |
| `hooks/bloqueo_entrega.py` | `pruebas/probar_hook.py` y los tres encargos anteriores | 24 casos sin fallos. Bloquea por falta de informe, por controles y por huella |

Para repetir las pruebas automáticas:

```
python pruebas/probar_hook.py
python pruebas/crear_docx_defectuosos.py --comprobar
python skills/niveles-academicos/scripts/cruzar_citas.py pruebas/casos/citas_prueba.md
```

## Sin probar

- **Windows y Python 3.14:** rutas instaladas, `soffice.exe`, archivo
  abierto en Word, consola cp1252 e `instalar.ps1`.
- **OpenAlex:** la clave respondió "API key not found". El buscador y
  el descargador lo informan como base con error y siguen.
- **Unpaywall:** exige un correo en `AGENTE_ACADEMICO_CORREO`; no se
  definió.
- **Semantic Scholar sin clave:** funcionó dos veces y luego dio
  límite de uso. `S2_API_KEY` no se probó.
- **Zotero real:** falta correr `zotero_apa.py` sobre
  `C:\Users\Usuario\Zotero`, también con Zotero abierto.
- **Calibri y paginación de Word:** el conteo se midió con
  LibreOffice y Carlito; puede variar en una línea.
- **Hook en una sesión real de Claude Code** y la fusión del
  fragmento en `settings.json`.
- **Los cinco agentes actualizados**, con un encargo real.
- **Prueba de aceptación en el equipo del usuario:** se corrió en la
  nube el 2026-11-14 (resultado en `PROYECTO.md`), con agentes
  genéricos que siguieron las definiciones de `agents/`, no con los
  agentes instalados.

## Límites conocidos

- MDPI y SciELO Brasil responden con control antibots; no se fuerza.
  Esas fuentes van a `descartadas.md` y el usuario las consigue.
- Las revistas de SciELO Bolivia registran su DOI por cuenta propia:
  salen en la búsqueda normal pero sin la marca SciELO.
- Los apellidos compuestos sin partícula no se adivinan en Semantic
  Scholar ni OpenAlex ("A. García Sánchez" sale "Sánchez, A. G.");
  con partícula sí ("de Souza", "van der Werf"), y si el trabajo
  también viene de Crossref mandan sus autores.
- `cruzar_citas.py` no empareja un apellido compuesto sin apellido en
  común ("Linera" frente a "García Linera") ni trata como
  discordancia una referencia de igual apellido y otro año.
- `verificar_referencias.py` puede tardar minutos si arXiv limita las
  peticiones; en ese caso marca "sin comprobar".
- `similitud_fuentes.py` no detecta paráfrasis ni traducciones.
- `control_final.py` controla `.docx` y `.xlsx`, no `.pptx` ni `.pdf`.
  En un xlsx solo ve valores guardados, no fórmulas sin calcular.
- `cifras_texto.py` sabe si un número existe en el análisis, no a qué
  variable se refiere; los enteros pequeños coinciden por azar.
- Los números del índice se miden con la paginación de LibreOffice;
  si Word pagina distinto en un caso límite, pueden diferir en una
  página hasta que se actualice el índice en Word.
- El hook bloquea una vez por turno y confía en el contenido de
  `controles.json` y del informe; sí exige que la huella coincida
  con el archivo real.
- El hook no ve un encargo cuya ruta no aparezca en la transcripción
  ni en la carpeta de trabajo.

## Pruebas del 2026-11-14 (capa 3 y límites)

| Pieza | Prueba | Resultado |
|---|---|---|
| `encargo.py` y `/encargo` | `pruebas/probar_encargo.py` | 51 casos sin fallos |
| Tipos de trabajo | `pruebas/probar_tipos.py` | 50 casos sin fallos; regresiones idénticas |
| Límites de las capas 1 y 2 | `pruebas/probar_limites.py` | 37 casos sin fallos (3 necesitan red) |
| Análisis de datos | `pruebas/probar_datos.py` | 51 casos sin fallos; fórmulas recalculadas con LibreOffice sin diferencias |
| Índice automático | `pruebas/probar_indice.py` | 25 casos sin fallos; 24 entradas de un caso de 13 páginas coinciden con la página real |
| Control final con variante de capítulos | Monografía real con `estructura: capitulos` | Los errores de estructura bajan de 3 a 1 |
| Control final con cifras | Texto con dos cifras alteradas | Bloquea y nombra las dos |

Datos reales usados en el análisis, versionados en
`pruebas/casos/datos/` con su procedencia: Cotner, Salehi y Ballen
(2018), doi:10.5061/dryad.53t31, CC0; y Espinoza Mina (2024),
doi:10.5281/zenodo.12702201, CC BY 4.0.

## Decisiones de formato que las reglas no fijaban

Márgenes de 2,54 cm; sangría de primera línea de 1,25 cm; sangría
francesa y cita en bloque de 1,27 cm; 6 pt después de cada párrafo;
títulos en Calibri 11 negrita a la izquierda (nivel 3 además en
cursiva), con 18/6 pt en el nivel 1 y 12/6 pt en los niveles 2 y 3;
número de página centrado desde la segunda página. Todo está
definido en los estilos de `construir_docx.py`.

## Hallazgos en la monografía de gases de efecto invernadero

Salieron al usarla como caso real. No se modificó el archivo.

- La referencia de OPS/OMS (2024) no está citada en el texto.
- "Los Tiempos" va después de las dos entradas del IPCC.
- La nota de la Figura 3 lleva "(p. 7)" y "(p. 10)".
- "IPCC" se usa sin presentar el nombre completo; "IBIF" se usa
  antes de presentarlo.
- Texto en Times New Roman 12 con interlineado doble; 44 párrafos sin
  justificar; títulos de capítulo centrados.
- La portada conserva "[Completar con el nombre completo del
  estudiante]".
- Hasta 21 párrafos vacíos seguidos usados como espaciado.
