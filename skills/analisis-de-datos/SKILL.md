---
name: analisis-de-datos
description: Análisis descriptivo reproducible de datos cuantitativos (csv o xlsx) para trabajos académicos. Usar cuando un trabajo tiene datos entregados por el usuario o de una fuente fichada y lleva cifras, tablas, figuras o un xlsx; también para que el verificador compruebe que las cifras del texto salen del análisis.
---

# Análisis de datos

Toda cifra del trabajo debe poder rehacerse desde los datos de origen
con lo guardado en `<carpeta del trabajo>/analisis/`. Los scripts están
en `scripts/` de esta skill y necesitan pandas y openpyxl; matplotlib
para figuras; scipy es opcional (pruebas).

## Reglas duras
- Solo datos que el usuario entregó o de una fuente fichada en
  `fuentes/`. Nunca completar, imputar, simular ni "limpiar" en
  silencio: cada decisión (faltantes, recodificación, filtro) se
  declara en el plan y queda en los metadatos.
- Lo que no se puede calcular se dice: los avisos de `analizar.py`
  pasan al texto o al director, no se esconden.
- Los significados de los códigos (0/1, 1–7) salen del libro de
  códigos o del artículo de origen, nunca de una suposición.
- No hace inferencia causal, modelos (regresión, factorial, SEM) ni
  genera datos de campo. Las pruebas que trae son descriptivas de
  apoyo: chi cuadrado, t de Welch, Mann-Whitney, ANOVA, Kruskal-Wallis.

## Flujo
1. Copiar los datos a `analisis/datos/` sin tocarlos.
2. **Perfilar** (obligatorio): `python perfilar_datos.py analisis/datos/x.csv`
   (`--hoja` en xlsx, `--json`). Describe codificación, separador,
   decimal, tipos, faltantes, duplicados, rangos, atípicos, columnas
   mixtas, fechas mal formadas y categorías que difieren solo por
   mayúsculas, tildes o espacios. No corrige nada. Código 1 = hay
   problemas que decidir.
3. **Plan**: escribir `analisis/plan_analisis.json` (plantilla abajo)
   con las decisiones tomadas a partir del perfil.
4. **Analizar**: `python analizar.py analisis/plan_analisis.json`.
   Escribe `analisis/resultados/resultados.json` (precisión completa,
   sha256 de datos y plan, filtros, métodos, versiones),
   `resultados.md` (tablas redondeadas para el redactor) y
   `figuras/*.png`. Código 1 = hubo avisos; 2 = no corrió.
5. **Exportar** (si hay entregable xlsx):
   `python exportar_xlsx.py analisis/resultados/resultados.json --salida entrega/x.xlsx [--formulas] --comprobar`.
   Valores fijos por defecto; `--formulas` si el usuario va a editar.
   `--comprobar` recalcula con LibreOffice y exige cero celdas de error
   y cifras iguales a resultados.json.
6. **Redactar** con `resultados.md`: copiar las cifras tal como están.
7. **Verificar**: `python cifras_texto.py entrega/x.docx analisis/resultados/resultados.json`.
   Código 1 si alguna cifra DISCREPA (bloquea); las NO HALLADAS se
   comprueban contra su fuente citada; sin cita, se retiran o se
   justifican.

## Plantilla de plan_analisis.json
Los comentarios `//` son explicación: no van en el archivo real.

```
{
  "titulo": "Encuesta de hogares, Cobija 2026",
  "datos": {
    "archivo": "datos/encuesta.csv",        // relativo a analisis/
    "hoja": null,                            // xlsx: nombre de la hoja
    "separador": null,                       // null = detectar; "\t", ";"
    "codificacion": null,                    // null = detectar; "latin-1"
    "decimal": null,                         // null = detectar; ","
    "faltantes": ["NA", "s/d", "99"],        // además de celdas en blanco
    "fuente": "Referencia APA o ficha de la fuente"
  },
  "recodificar": {"sexo": {"1": "Mujer", "2": "Hombre"}},  // según libro de códigos
  "orden": {"nivel": ["Primaria", "Secundaria", "Superior"]},
  "filtros": [{"columna": "edad", "op": ">=", "valor": 18}],
      // op: == != en no_en > >= < <= no_faltante; sobre valores ya recodificados
  "redondeo": {"porcentaje": 1, "estadistico": 2, "prueba": 2, "p_valor": 3},
  "formato": {"miles": "espacio"},           // espacio (RAE), punto o ninguno
  "tablas": [
    {"id": "t1", "tipo": "frecuencias", "variable": "nivel", "titulo": "Nivel educativo", "figura": true},
    {"id": "t2", "tipo": "cruzada", "filas": "sexo", "columnas": "nivel",
     "porcentajes": ["fila", "columna"], "prueba": "chi2"},     // fila | columna | total
    {"id": "t3", "tipo": "resumen", "variables": ["ingreso", "edad"]},
    {"id": "t4", "tipo": "resumen", "variables": ["ingreso"], "por": "sexo",
     "prueba": "t", "figura": true},         // t | mann-whitney | anova | kruskal
    {"id": "t5", "tipo": "serie", "fecha": "fecha_encuesta", "periodo": "mes",
     "formato_fecha": "%d/%m/%Y", "variable": null, "estadistico": "conteo"}
      // periodo: hora dia semana mes trimestre año; estadistico: conteo media suma
  ]
}
```

Opciones por tabla: `"redondeo"` propio, `"mostrar_por_100": true` en
resumen (proporciones 0–1 leídas como %), `"etiqueta_x"`/`"etiqueta_y"`
en figuras.

## Métodos fijos
Desviación estándar muestral (n − 1); cuartiles por interpolación
lineal (como CUARTIL.INCLUYE); porcentajes sobre válidos (frecuencias
también sobre el total); redondeo mitad hacia arriba; chi cuadrado sin
corrección de Yates (avisa si más del 20 % de esperadas < 5); t de
Welch. Figuras sobrias de 16 cm de ancho, en grises, con coma decimal.

## Límites
`cifras_texto.py` sabe si un número existe en el análisis, no a qué
variable se refiere; no lee números escritos con letras; toma 1900–2100
como años. Las fórmulas del xlsx se comprobaron con LibreOffice; en
Excel las fórmulas matriciales por grupo dependen de la versión.
