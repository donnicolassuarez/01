**Dictamen: APROBADO**

Archivo verificado: `entrega/Los_incendios_en_Pando_y_su_costo_climatico.docx`
sha256 `7a345917c7e589cc46c73f47b047dbdd920f5b81bb9aaa1306321e9884b2eda9`.
Es la huella de `entrega/controles.json` (`aprobado_mecanico: true`) y la del
archivo que verifiqué (recalculada con `sha256sum`).
Encargo: ensayo, pregrado, 5 páginas en total (portada en blanco y referencias
incluidas), formato UAP.

No queda ningún error material. El ensayo es un trabajo de pregrado bien
acotado: dice lo que no pudo medir y no atribuye a Pando lo que se midió en
otro sitio. Las observaciones de abajo no bloquean.

## Errores materiales (bloquean)

Ninguno.

## Observaciones (no bloquean)

1. Tesis de la Introducción ("en Pando el fuego es sobre todo una herramienta
   humana para desmontar, favorecida por normas permisivas"). La parte de las
   normas tiene apoyo directo en Ferreira et al. (2023) sobre Pando (p. 13:
   "regulations that stimulate the use of fire to expand the agricultural
   frontier such as in the case of Pando"; p. 10, Ley 1171). La parte "sobre
   todo para desmontar" se apoya en el resultado regional de MAP (pp. 7 y 9) y
   en los estudios de Brasil. Ningún pasaje mide los motivos del fuego en
   Pando solo. Es una tesis razonada y el propio texto delimita la evidencia,
   pero no es un hallazgo sobre Pando.
2. Ke et al. (2024): "región del planeta con mayor pérdida anómala de
   carbono" resume bien el resumen (p. 2: "largest abnormal carbon loss in
   the Amazon"). Esa misma frase cita aparte 0,58 GtC/año de emisión por
   fuego extremo en Canadá, otra magnitud (emisión, no anomalía neta). El
   texto aclara que el estudio no está publicado en revista y no separa fuego
   de sequía.
3. Song et al. (2015): "la deforestación crecía en Bolivia" es lo que dice el
   resumen (p. 1). En el cuerpo (p. 4) la deforestación boliviana bajó
   ligeramente después de 2006. Matiz menor.
4. Nelson y Chomitz (2011): "las áreas de uso múltiple funcionan incluso
   mejor" es el resumen (p. 1) para América Latina y Asia. En el análisis
   regional (p. 8) dicen para América Latina "as effective or more
   effective". Matiz menor.
5. Nivel (niveles-academicos, pregrado): 7 fuentes, dentro del rango de 5 a
   12. El perfil pide mayoría en español y menciona normas y datos oficiales.
   Aquí las 7 están en inglés, ninguna es norma ni dato oficial boliviano (la
   Ley 1171 se cita por Ferreira y el texto lo declara) y no hay un concepto
   teórico explicado. Referencias: 0,66 páginas, dentro de página y media.
6. Zhou et al.: la cita impresa en el PDF dice "(2020)", pero se publicó el
   18 de febrero de 2021 (Crossref también da 2021). El año 2021 de la
   referencia es correcto.
7. Las multas (0,20 US$ por hectárea) son un dato de Cauthin (2022) que
   Ferreira recoge (p. 14). El texto dice "los mismos autores recogen", lo
   que es correcto.

## Cambios respecto de la versión anterior y su comprobación

Comparé el texto del docx, párrafo por párrafo, con `borrador/texto.md`: 33
de 33 párrafos idénticos. Frente a la revisión anterior solo cambiaron cuatro
frases. El resto del texto, las referencias y el formato no cambiaron.

| Frase que cambió | Fuente y página | Resultado |
|---|---|---|
| "Son datos de Brasil; para Pando, Ferreira et al. (2023) registran una baja de la deforestación y los bordes, pero también normas que estimulan quemar para ampliar la frontera agropecuaria." (último párrafo de "Un fuego que encienden las personas") | Ferreira p. 9 ("a decrease for Pando", en deforestación y bordes de bosque); p. 13 ("regulations that stimulate the use of fire ... such as in the case of Pando"); p. 10 (Ley 1171) | Respalda. Corrige el error material anterior |
| Introducción: la tesis ya no dice "y agravada por la sequía" | Sin cita. Ver observación 1 | Sin problema. Quita lo que ninguna fuente medía para Pando |
| "Zhou et al. (2021), apoyándose en estudios anteriores, señalan que entre 1997 y 2009 los incendios liberaron en el mundo unos 2.000 millones de toneladas de carbono al año y que Sudamérica aportó cerca del 15 %" | Zhou p. 2: "van der Werf et al. (2010) estimated for the period between 1997 and 2009 that, globally, the annual average carbon emissions caused by fire is 2.0 Pg C year-1, with South America contributing 15%" | Respalda. Período y cifras coinciden |
| Conclusiones: "que se concentra en la temporada seca y que en la región esta se alarga en los años secos" | Ferreira p. 3: temporada de julio a septiembre; "during extreme dry years, fires can start in June and prolong until October" | Respalda |

## Citas contra pasaje (18 de 18 revisadas)

Las 14 citas que no cambiaron las verifiqué en la primera vuelta contra su
pasaje y su texto es idéntico. Las 4 de arriba (la de Ferreira sobre Pando, la
de Zhou, la de Ferreira sobre la temporada y, por la tesis, la ausencia de
cita) las volví a comprobar contra `fuentes/texto/` con `extraer_texto.py
--buscar`. Páginas = páginas del PDF fuente.

| # | Afirmación | Fuente y página | Resultado |
|---|---|---|---|
| 1 | Quemas de julio a septiembre; junio a octubre en años secos | Ferreira p. 3 | Respalda |
| 2 | Emisiones de fuego con máximo en agosto y septiembre, con menos lluvia y más calor | Zhou p. 4 | Respalda |
| 3 | Modelo MAP: deforestación, tierras productivas y bordes explican el fuego más que el clima | Ferreira pp. 7 y 9 | Respalda (es regional y el texto lo dice así) |
| 4 | Auge del desmonte ilegal trajo más quemas; clima cálido y seco más deforestación aumentan fuegos intencionales y de sotobosque | Kruid p. 2 | Respalda |
| 5 | Fuegos de deforestación bajan al alejarse de los caminos y son más frecuentes con El Niño | Adeney p. 1 | Respalda |
| 6 | Para Pando: baja de deforestación y bordes, y normas que estimulan quemar | Ferreira pp. 9, 10 y 13 | Respalda |
| 7 | Pando 15,5 % de los focos; 13 % en 2020; cerca de 19 % del área propensa; Acre mayoría | Ferreira p. 6 y p. 8 | Respalda. El texto aclara que son focos, no hectáreas |
| 8 | Casi toda la castaña de Bolivia sale de Pando | Ferreira p. 14 | Respalda |
| 9 | Arco de deforestación podría extenderse al norte de Bolivia tras la interoceánica (advertencia, no medición) | Song p. 11 | Respalda |
| 10 | Desde la pavimentación crecieron deforestación y minería de oro ilegales | Ferreira p. 13 | Respalda |
| 11 | Desde 2013 ocho leyes; Ley 1171 autoriza el fuego con permisos de varios años; multas bajas | Ferreira p. 10 y p. 14 | Respalda. Nombre y número de la norma coinciden con la lista de referencias de Ferreira |
| 12 | Pérdida de bosque tropical explica entre la quinta y la cuarta parte de la contribución humana | Nelson p. 1 | Respalda |
| 13 | Bolivia, segundo país en deforestación (12 %); 10 % de emisiones, 18 millones de t C/año | Song p. 4 y p. 7 | Respalda (ver observación 3) |
| 14 | Incendios liberaron ~2.000 millones de t C/año (1997-2009); Sudamérica 15 % | Zhou p. 2 | Respalda |
| 15 | Degradación y perturbaciones, entre ellas el fuego, 44 % de las pérdidas de carbono 2003-2019 en la Amazonía brasileña | Kruid p. 1 y p. 4; el fuego como causa de degradación, p. 3 | Respalda |
| 16 | 2023: sequía extrema, Amazonía con mayor pérdida anómala; sumidero más débil desde 2003 | Ke p. 2 y p. 3 | Respalda (ver observación 2) |
| 17 | Áreas protegidas de Brasil con menos fuegos de deforestación, sobre todo cerca de caminos | Adeney p. 1 | Respalda |
| 18 | Territorios indígenas reducen el fuego 16 puntos porcentuales en América Latina; uso múltiple incluso mejor | Nelson p. 1 (y p. 7) | Respalda (ver observación 4) |

Total: 18 respaldan, 0 respaldan en parte, 0 no respaldan.

## Comprobaciones del procedimiento

- **0. Control mecánico**: `controles.md` dice superado. Citas ok (18 citas, 7
  referencias, sin discordancias); similitud ok (copia 0); formato ok (0
  errores, 0 avisos, 5 páginas); fuentes ok (7 de 7 con archivo y ficha);
  referencias con aviso (5 encontradas, 2 no encontradas). Nada en "Qué
  bloquea".
- **1. Referencias reales**, los dos pendientes del control:
  - Zhou et al. (2021): salió "no encontrada" porque Crossref respondió 429
    en esa corrida. La consulté de nuevo y respondió HTTP 200: título
    "Impacts of Amazon Fire Aerosols on the Subseasonal Circulations of the
    Mid-High Latitudes", Frontiers in Earth Science, vol. 8, artículo 609554,
    2021, autores Zhou Yu, Yan Huiping, Luo Jing-Jia. `doi.org` redirige a
    frontiersin.org. La primera página del PDF trae el mismo DOI, título,
    autores y la fecha de publicación del 18/02/2021. Existe y es la obra
    citada.
  - Ke et al. (2024): preprint de arXiv, no está en Crossref (404, normal en
    un preprint). Comprobada en `arxiv.org/abs/2407.12447` (título, 16
    autores en el mismo orden y fecha del 17/07/2024 coinciden), y
    `doi.org/10.48550/arXiv.2407.12447` redirige a esa página. La primera
    página del PDF no trae número de arXiv ni DOI, y se comprobó por título,
    autores y resumen. OpenAlex no se pudo usar (401, clave no activa).
  - Las otras 5 (Adeney, Ferreira, Kruid, Nelson, Song) las encontró
    Crossref y coinciden en autores, año, revista, volumen y número. En la
    primera vuelta las había comprobado también contra la primera página de
    cada PDF.
- **2. Fuente en carpeta**: 7 de 7 obras con PDF, texto extraído y ficha.
- **4. Correspondencia**: sin citas huérfanas ni referencias sin citar;
  autor y año coinciden.
- **5. Cifras**: todas coinciden con las fuentes (tabla). No hay script de
  análisis en este encargo.
- **6. Marcadores**: sin "por verificar", "pendiente", "TODO", "XXX" ni
  corchetes vacíos.
- **7. Formato y extensión**: renderizado con LibreOffice a PDF en una
  carpeta temporal fuera de `entrega/`: 5 páginas, carta (612 × 792 pt). La
  página 1 es la portada en blanco; Introducción, Desarrollo y Conclusiones
  presentes; referencias en las páginas 4 y 5, unos dos tercios de página.
  `verificar_formato.py`: 15 comprobaciones OK (Calibri 11, 1,15, justificado
  con sangría, títulos a la izquierda, espaciado uniforme de 18/6 pt en nivel
  1 y 12/6 pt en nivel 2, sin párrafos vacíos, sin restos de Markdown). La
  fuente del render fue Carlito, equivalente en métricas a Calibri. No pude
  abrir el docx en Word; el conteo de páginas es el de LibreOffice.
- **8. Ortografía**: texto leído completo; sin faltas de tildes, puntuación
  ni concordancia. Los títulos no llevan dos puntos ni tono de plantilla.
- **9. Autonomía**: sin menciones a versiones, correcciones ni otros
  archivos. Las frases en primera persona ("No pude revisar el texto de la
  ley", "no encontré datos") son límites del trabajo.
- **10. Nivel**: ver observación 5.

## Citas revisadas / citas totales

18 / 18 citas revisadas contra su pasaje. 7 / 7 referencias comprobadas contra
su PDF y contra Crossref (6) o arXiv (Ke).
