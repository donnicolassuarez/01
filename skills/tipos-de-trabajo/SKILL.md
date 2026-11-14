---
name: tipos-de-trabajo
description: Estructura de cada tipo de trabajo académico (ensayo, monografía, informe, artículo, perfil de tesis, tesis): portada, secciones obligatorias y su orden, elementos previos y finales, extensión habitual por nivel. Usar al planificar, redactar, producir o revisar un trabajo, junto con niveles-academicos.
---

# Tipos de trabajo

El tipo lo fija el encargo (`tipo:` en `encargo.md`). Esta skill dice
qué partes lleva cada tipo; niveles-academicos dice con qué exigencia
se escriben. Son independientes: un ensayo de maestría tiene la
estructura de un ensayo y la exigencia de maestría.

La definición que usan las herramientas está en `tipos.json`, en esta
misma carpeta. `construir_docx.py` toma de ahí la portada por defecto
y avisa si falta una sección o va fuera de orden; `verificar_formato.py`
lo controla en la comprobación o) y bloquea la entrega. Si este texto y
`tipos.json` dijeran cosas distintas, manda `tipos.json` y hay que
corregir este texto (`pruebas/probar_tipos.py` comprueba que coincidan).

**Qué es norma y qué no.** Ensayo y monografía siguen las reglas
escritas del usuario (portada en blanco; Introducción, Desarrollo y
Conclusiones como encabezados solos). Todo lo demás —informe,
artículo, perfil, tesis, las variantes y las extensiones— es
convención académica general; confirmar con el reglamento de la
carrera. Si el encargo, el docente o el reglamento piden otra
estructura, manda lo que pidan: se usa `--tipo otro` o se informa al
director para ajustar `tipos.json`.

## Cómo se usa
- **Redactor:** antes del esquema, lee la sección del tipo. Usa los
  encabezados obligatorios con su nombre (o una variante aceptada) y
  en su orden. Los títulos del trabajo los fija el usuario; esta skill
  no inventa títulos de contenido.
- **Productor:** `construir_docx.py ... --tipo <tipo> [--variante X]`.
  La portada sale del tipo salvo `--portada`. El índice se genera solo
  cuando el tipo lo exige; en los demás, solo si el texto lo pide (línea
  `\indice` o metadato `indice: si`); `--sin-indice` lo quita. Todo AVISO de sección
  que falta o fuera de orden vuelve al director, no se arregla
  cambiando el texto.
- **Revisor:** además de la rúbrica, mira lo que se indica en «Qué mira
  el revisor» de cada tipo.
- **Verificador:** `verificar_formato.py <docx> --tipo <tipo>
  [--variante X]` (lo corre `control_final.py` con el tipo de
  `encargo.md`).

Encabezados: se comparan sin tildes ni mayúsculas. «Solo» quiere decir
que el encabezado es exactamente ese texto («Introducción», no
«Introducción al problema»). Donde no se exige «solo», se acepta la
numeración delante («Capítulo II. Marco teórico», «2. Metodología») y
texto detrás («Conclusiones y recomendaciones»). La extensión es
orientativa: la fija el encargo y nunca bloquea.

## Tipos

### Ensayo (`ensayo`)
- **Propósito:** defender una tesis propia con argumentos y fuentes.
- **Estructura:** portada blanca (hoja en blanco). Introducción,
  Desarrollo y Conclusiones, como encabezados solos y en ese orden.
  Sin índice, resumen ni anexos. Referencias al final.
- **Qué va:** Introducción: tema, tesis y recorrido. Desarrollo:
  argumentos con su evidencia; subtítulos de nivel 2 si ayudan.
  Conclusiones: respuesta a la tesis, sin material nuevo.
- **Extensión orientativa:** pregrado 3–10 páginas; maestría 8–15;
  doctorado 10–20; postdoctorado, la de la revista.
- **Errores típicos:** tesis ausente o enunciada al final; resumen de
  autores en lugar de argumento; conclusiones que traen datos nuevos;
  encabezados con título propio («Introducción: el problema»).
- **Qué mira el revisor:** que haya tesis y que cada parte del
  Desarrollo la sostenga; objeciones atendidas desde maestría.

### Monografía (`monografia`)
- **Propósito:** exponer con orden lo que se sabe sobre un tema
  delimitado, a partir de fuentes.
- **Estructura por defecto:** portada blanca. Introducción,
  Desarrollo y Conclusiones, como encabezados solos y en ese orden;
  el Desarrollo se divide en subtítulos de nivel 2. Índice opcional
  (solo si se pide: `\indice` o `indice: si`); anexos opcionales;
  referencias al final.
- **Variante `capitulos`** (convención general; no se activa sola):
  portada datos, Introducción, Capítulos numerados («Capítulo I. …»,
  al menos uno, de nivel 1) y Conclusiones; Recomendaciones opcional;
  índice obligatorio (lo genera el constructor). Se elige con `--variante capitulos` o con
  `estructura: capitulos` en los metadatos del Markdown. Si la regla
  de portada en blanco y encabezados solos vale para monografías con
  capítulos es una **decisión abierta del usuario** (`PROYECTO.md`,
  «Sin resolver»): no elegir la variante sin que el encargo lo diga.
- **Qué va:** Introducción: tema, objetivo, enfoque y orden.
  Desarrollo o capítulos: la exposición con la evidencia citada.
  Conclusiones: síntesis y respuesta al objetivo.
- **Extensión orientativa:** pregrado 10–30 páginas; maestría 20–50.
- **Errores típicos:** capítulos que copian el orden de las fuentes;
  marco teórico que no se usa después; párrafos vacíos como espaciado.
- **Qué mira el revisor:** delimitación del tema, hilo entre partes y
  que las conclusiones salgan de lo expuesto.

### Informe (`informe`)
- **Propósito:** dar cuenta de un trabajo hecho (investigación,
  laboratorio, práctica) y de sus resultados.
- **Estructura:** portada datos. Introducción, Metodología,
  Resultados y Conclusiones, en ese orden y de nivel 1. Opcionales:
  Objetivos, Discusión, Recomendaciones. Resumen e índice opcionales;
  anexos opcionales; referencias al final.
- **Variante `simple`:** informe de lectura, visita o actividad, sin
  método propio: Introducción, Desarrollo y Conclusiones (portada
  datos).
- **Qué va:** Metodología: qué se hizo, con qué y cómo. Resultados:
  lo obtenido, con tablas y figuras numeradas. Conclusiones:
  respuesta a los objetivos.
- **Extensión orientativa:** pregrado 5–15 páginas; maestría 10–25;
  doctorado 10–30.
- **Errores típicos:** resultados mezclados con opinión; método que
  no permite saber qué se hizo; cifras sin fuente ni script.
- **Qué mira el revisor:** que cada resultado se pueda rastrear al
  método y a los datos; que las conclusiones no excedan los resultados.

### Artículo (`articulo`)
- **Propósito:** comunicar un hallazgo a pares, en formato publicable.
- **Estructura (IMRyD):** portada ninguna (el título encabeza la
  primera página). Resumen y Palabras clave antes del cuerpo
  (obligatorios). Introducción, Método, Resultados y Discusión, en ese
  orden; «Resultados y discusión» juntos valen por las dos.
  Opcionales: Conclusiones, Agradecimientos. Referencias al final.
- **Variante `revision`:** artículo de revisión o teórico: Resumen,
  Palabras clave, Introducción, el desarrollo con títulos propios y
  Conclusiones (o «Consideraciones finales»).
- **Qué va:** Introducción: problema, vacío y objetivo. Método:
  detalle suficiente para repetirlo. Resultados: hallazgos sin
  interpretar. Discusión: significado, límites y aporte.
- **Extensión orientativa:** maestría 12–20 páginas; doctorado 15–25;
  postdoctorado 15–30. En postdoctorado mandan las normas de la
  revista sobre esta estructura y sobre el formato UAP.
- **Errores típicos:** resumen que no dice resultados; discusión que
  repite resultados; aporte exagerado.
- **Qué mira el revisor:** vacío real en la literatura, método
  adecuado a la pregunta, discusión frente a los trabajos más cercanos.

### Perfil de tesis (`perfil`)
- **Propósito:** proponer una investigación y mostrar que es viable.
- **Estructura:** portada datos. Introducción (o Antecedentes),
  Planteamiento del problema, Objetivos, Justificación, Marco teórico,
  Metodología y Cronograma. El orden se controla en todas menos la
  Justificación, cuya posición cambia según el reglamento. Pueden ser
  de cualquier nivel (Objetivos suele ir como subtítulo). Opcionales:
  Hipótesis, Presupuesto, Índice tentativo. Referencias al final.
- **Qué va:** Planteamiento: situación, delimitación y pregunta.
  Objetivos: general y específicos, verificables. Metodología:
  enfoque, diseño, población o fuentes, técnicas, instrumentos y plan
  de análisis. Cronograma: actividades y plazos en tabla.
- **Extensión orientativa:** pregrado 10–20 páginas; maestría 15–30;
  doctorado 20–40.
- **Errores típicos:** pregunta que no se responde con el método;
  objetivos que son actividades; hipótesis en un estudio descriptivo
  que no la necesita; datos de campo dados por obtenidos.
- **Qué mira el revisor:** coherencia pregunta–objetivos–método y
  viabilidad con el tiempo y las fuentes disponibles.

### Tesis (`tesis`)
- **Propósito:** responder una pregunta de investigación con método
  propio y aporte acorde al nivel.
- **Estructura:** portada datos. Índice (lo genera el constructor, con
  los números de página medidos) y Resumen (obligatorio) antes del
  cuerpo; Palabras clave opcional. Introducción, Marco teórico,
  Metodología, Resultados y Conclusiones, de nivel 1 y en ese orden,
  normalmente como capítulos numerados. Opcionales: Planteamiento del
  problema, Discusión, Recomendaciones, Propuesta. Anexos opcionales;
  referencias al final.
- **Qué va:** Introducción: problema, pregunta, objetivos y
  estructura. Marco teórico: categorías que luego se usan. Metodología:
  diseño, instrumentos, análisis y límites. Resultados: por objetivo.
  Conclusiones: respuesta a cada objetivo; aporte y límites.
- **Extensión orientativa:** pregrado 60–120 páginas; maestría
  80–150; doctorado 150–300.
- **Errores típicos:** marco teórico enciclopédico; metodología
  genérica copiada de un manual; conclusiones que no responden los
  objetivos; datos que no se pueden rehacer.
- **Qué mira el revisor:** rúbrica completa del nivel, con atención al
  aporte y a la trazabilidad de los datos.

### Otro (`otro`)
Sin estructura controlada ni portada por defecto. Para trabajos que no
encajan en los anteriores o cuyo reglamento pide otra cosa.

## El archivo tipos.json
Un objeto por tipo en `tipos` (clave en minúsculas sin tildes):
- `nombre`, `sinonimos`: lo que se acepta en `--tipo` y en `tipo:`.
- `fuente`: `usuario` (regla escrita) o `convencion` (sin confirmar).
- `portada`: `blanca`, `datos` o `ninguna`.
- `capitulos`: si el tipo admite capítulos numerados.
- `secciones`: obligatorias, en orden. Cada una: `clave`, `nombre`,
  `variantes` (encabezados aceptados), `solo` (encabezado exacto),
  `nivel` (1, 2, 3 o null = cualquiera), `orden` (false = no entra en
  el control de orden), `contenido`. Una sección con `capitulos: true`
  y `minimo` se cumple con títulos «Capítulo I», «1.», «I.».
- `opcionales`: secciones que pueden ir; no se controlan.
- `previos` (`indice`, `resumen`, `palabras_clave`) y `finales`
  (`referencias`, `anexos`): `obligatorio`, `opcional` o `no`. Resumen
  y palabras clave obligatorios se controlan en o); las referencias, en
  l). Índice: con `obligatorio`, `construir_docx.py` lo genera (campo
  TOC de Word con los números medidos en el PDF); con `opcional` o
  `no`, solo si el texto lo pide. Va en su propia página inmediatamente
  después de la portada: `tipos.json` no fija si va antes o después del
  resumen. Si falta, o) da AVISO; p) comprueba que cada número coincida
  con la página real del título.
- `extension`: `[mínimo, máximo]` de páginas por nivel o null; solo
  informativo. `por_nivel`: qué cambia según el nivel.
- `variantes`: objetos con los campos que cambian (`portada`,
  `secciones`, `opcionales`, `previos`, `capitulos`...).

El archivo se valida al cargarse: si está mal, los dos scripts salen
con código 2 y dicen qué campo falla. Si no se encuentra (ni aquí ni
en la ruta de la variable `TIPOS_TRABAJO`), rige la regla anterior
(solo ensayo y monografía) con un aviso. Después de cambiarlo, correr
`python pruebas/probar_tipos.py`.
