# Datos reales para las pruebas de la skill analisis-de-datos

Copias sin modificar (mismos bytes que el original) de dos conjuntos de
datos abiertos. Las usa `pruebas/probar_datos.py`.

## PLoSOneData_ExamsDisWomen.csv
- Cotner, S., Salehi, S. y Ballen, C. J. (2018). *Data from: Exams
  disadvantage women in introductory biology* [Conjunto de datos].
  Dryad. https://doi.org/10.5061/dryad.53t31 (copia en Zenodo,
  registro 4947590).
- Artículo: Ballen, C. J., Salehi, S. y Cotner, S. (2017). Exams
  disadvantage women in introductory biology. *PLOS ONE, 12*(10),
  e0186419. https://doi.org/10.1371/journal.pone.0186419
- Licencia: CC0 1.0 (dominio público).
- Descarga: https://zenodo.org/api/records/4947590/files/PLoSOneData_ExamsDisWomen.csv/content
  (2026-11-14). 215 638 bytes; md5 236c38983d349f4f23bcde48e55e08bd;
  sha256 6e3110679ff00f82e9ff0b4b2aed2f8c160e22a3cbec2a887b4a517e6360a892.
- 1561 filas, 34 columnas; separado por tabuladores, UTF-8 con BOM,
  finales de línea CR; faltantes escritos como un espacio.
- Código de `Gender`: el depósito no trae libro de códigos. La Tabla 2
  del artículo informa 868 mujeres y 692 hombres; en los datos
  `Gender = 0` tiene 868 casos y `Gender = 1` 693. Por eso el plan de
  prueba lee 0 = Mujer, 1 = Hombre (inferencia documentada, no dato del
  depósito). `URM`: 1 = minoría subrepresentada (Tabla 2: URM 180).

## Respuestas_Encuesta.csv
- Espinoza Mina, M. A. (2024). *Respuestas a la encuesta para el
  estudio de noticias falsas* [Conjunto de datos]. Zenodo.
  https://doi.org/10.5281/zenodo.12702201
- Encuesta a estudiantes de una universidad privada de Ecuador
  (enero–febrero de 2024).
- Licencia: CC BY 4.0 (redistribución con atribución, que es este
  archivo).
- Descarga: https://zenodo.org/api/records/12702201/files/Respuestas_Encuesta.csv/content
  (2026-11-14). 288 823 bytes; md5 6444dea8d87c4529be8e04bc41466101;
  sha256 ef23f50659278139fd8bb07ca247fd6c8a7f88fe230102e0370bed16c3ff0cc0.
- 640 filas, 22 columnas (marca temporal, edad en tramos, género,
  facultad, año y 17 preguntas cerradas con algunas respuestas abiertas).

## Planes de prueba
- `plan_examenes.json`: frecuencias, cruzada con chi cuadrado, resumen
  global y por grupos con t de Welch.
- `plan_noticias.json`: frecuencias, cruzada y serie semanal.

Ambos esperan los datos en `datos/` junto al plan (así los copia
`probar_datos.py` a `pruebas/salida/caso_datos/`).
