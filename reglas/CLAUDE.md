@RTK.md

# Reglas de trabajo de Don Nico

Estas reglas mandan sobre cualquier nota de memoria anterior que diga
otra cosa. Las notas de proyecto (REMO, CAFE_PANDO, CONSTITUBOT)
siguen vigentes para su proyecto.

## 1. Alcance y ritmo
- Pedido concreto: ejecutar directo, sin preguntar.
- Pedido abierto o con versión chica y versión grande: UNA sola
  pregunta de alcance antes de usar herramientas. Después, ninguna
  pregunta sobre detalles menores.
- Entregar solo lo pedido. No sumar secciones, extras ni
  "complementos". No rehacer lo ya entregado: modificar.
- Cada pedido es independiente; no asumir continuidad.
- Si rechazo una solución, no repetirla. Tras dos intentos fallidos,
  cambiar de estrategia o preguntar.
- "Para", "no hagas nada": detenerse por completo.

## 2. Aprobación antes de cambiar
- Todo cambio, edición o movimiento sobre un documento o entregable
  existente se explica primero en el chat y espera mi aprobación.
- Si señalo que falta algo que debía venir desde la primera entrega,
  agregarlo de inmediato sin preguntar.
- Si pido solo una explicación, explicar sin modificar nada.

## 3. Completar y verificar
- Dentro de lo pedido, terminar todo en el mismo turno. No dejar
  "puedo hacerlo después" ni pendientes.
- Si algo no se puede hacer, decirlo al inicio con la causa.
- Nunca entregar citas, fuentes o partes "por verificar". Lo que no
  se pudo verificar se retira y se informa en el chat cuál fue.
- No declarar "listo" sin haber revisado el archivo final real, no el
  script que lo genera.

## 4. Fuentes y citas
- APA 7. Citas simples, sin página ni párrafo. Referencias sin
  localizadores.
- Citar solo obras descargadas y leídas. Si solo se accedió a una
  fuente secundaria, se cita la secundaria.
- Los libros académicos de referencia y sus PDF descargables son
  válidos; no cuestionar su uso.
- Nivel según el encargo: pregrado, maestría, doctorado o
  postdoctorado. Si no se indica, pregrado de 2.º año: teoría y
  bibliografía moderadas, referencias de máximo página y media.
- Las exigencias de cada nivel están en la skill niveles-academicos.
- Nunca inventar datos, resultados, entrevistas ni fuentes.

## 5. Documentos
- Formato por defecto: DOCX. PDF solo si lo pido. Idioma: español,
  con tildes y puntuación revisadas. Año en curso: 2026.
- Formato UAP: Calibri 11, interlineado 1,15, texto justificado con
  sangría de primera línea, títulos alineados a la izquierda.
- Ensayos y monografías: portada como hoja en blanco; encabezados
  Introducción, Desarrollo y Conclusiones solos, a la izquierda.
- Extensión: el número de páginas pedido es el total. Medirlo sobre
  el PDF renderizado, en tamaño carta. No entregar bajo el mínimo.
- Generar el docx por código (Python), con estilos Título 1/2/3
  desde el inicio. Guardar primero en temporal y luego copiar. Dar
  pasos manuales de Word solo si los pido.
- Antes de entregar un docx, aplicar la skill verificar-docx-generado.
- Títulos y planteamientos con voz de estudiante universitario: sin
  dos mitades separadas por dos puntos ni tono de plantilla. No
  inventar títulos; usar los del trabajo o preguntar.
- Entregables para el docente: autónomos. Sin versiones, "qué
  cambió" ni referencias a otros archivos.
- Documentos hermanos para distintos clientes: variar formato,
  tipografía y tono, no solo el color.

## 6. Diapositivas e imágenes
- Entregar el prompt para Claude Design, no el archivo, salvo pedido
  explícito.
- El prompt debe exigir: lienzo 1920×1080 con tamaños en píxeles;
  texto repartido en toda el área útil, centrado verticalmente,
  vacío máximo 15 %; tres o cuatro bloques por diapositiva; títulos
  iguales al índice del trabajo; sin etiquetas de escuela ni autor.
- Imágenes: primero fotografía real del hecho, lugar o sujeto; si no
  existe por antigüedad, pintura o grabado de época.

## 7. Guardado
- Mis trabajos: Desktop\JP\ACADEMIA_CLAUDE\08_PRODUCCION_ACADEMICA\
  don_nico\trabajos\<categoría>\<carpeta del trabajo>\
- Trabajos "para jota": misma raíz, carpeta jota, con las
  especificaciones que se indiquen para ese trabajo.
- Al cerrar: intermedios agrupados o eliminados, README de la
  carpeta y catálogos de JP actualizados.
- Paquetes finales: un zip por entidad.

## 8. Modelos y subagentes
- Un modelo por sesión, con el nivel de esfuerzo indicado.
- Decisiones y redacción: Opus, esfuerzo medio. Implementación:
  Sonnet. Tareas mecánicas en lote: subagentes Haiku o Sonnet.

## 9. Encargos de investigación y documentos
- Cadena: investigador → redactor → productor → verificador. De
  maestría hacia arriba, o si lo pido, se suma el revisor antes del
  productor.
- Cada trabajo vive en su carpeta con: `encargo.md` (tema, nivel,
  formato, extensión, estado), `fuentes/`, `borrador/` y `entrega/`.
  Actualizar el estado en `encargo.md` al cerrar cada etapa, para
  poder retomar en otra sesión sin repetir trabajo.
- La línea `estado:` de `encargo.md` toma uno de estos valores: en
  curso, en verificación, aprobado, no aprobado, suspendido. Para
  cerrar como aprobado hacen falta `control_final.py` sin bloqueos y
  el dictamen APROBADO del verificador sobre el mismo archivo.
- Nada se entrega sin el visto bueno del verificador. Máximo tres
  vueltas de corrección; si no pasa, informar qué falla y por qué.
- El director coordina y decide; no redacta ni verifica él mismo.
- Los encargos se inician y se retoman con `/encargo`.
