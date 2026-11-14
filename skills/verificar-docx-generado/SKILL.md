---
name: verificar-docx-generado
description: Usar SIEMPRE antes de entregar cualquier archivo .docx generado o editado con construir_docx.py, python-docx, docx (npm) o manipulación directa de XML. Verifica saltos de página forzados y espaciado de títulos/subtítulos en el XML real antes de decir que algo está corregido.
---

# Verificar .docx antes de entregar

## Por qué existe esta skill

El 26/07/2026 se pidió, en la misma sesión, eliminar un espacio de más
entre títulos/capítulos **cinco veces**. Cada vez se "arregló" editando
el script generador (`build_monografia.js`) y regenerando UN archivo,
pero:

1. Nunca se verificó el XML resultante línea por línea antes de decir
   "listo, corregido".
2. Cuando el usuario señaló el mismo archivo de una versión anterior
   (`v2`), se asumió que ya tenía la corrección por haberla aplicado
   al script en general — pero ese `.docx` específico se había
   generado ANTES del fix y nunca se regeneró. El espaciado viejo
   seguía grabado en cada párrafo de título de ESE archivo.
3. Resultado: cinco rondas de frustración por no verificar el
   artefacto final, solo el código que lo genera.

**Regla:** el código fuente que genera el documento no es el
documento. Cada `.docx` es un artefacto propio que hay que verificar
por separado, siempre.

## Checklist obligatorio antes de decir "está corregido" o entregar un .docx

Primero, sobre el archivo `.docx` REAL que se va a entregar (no sobre
el script, no de memoria), correr el verificador de formato:

```bash
python "C:\Users\Usuario\.claude\skills\niveles-academicos\scripts\verificar_formato.py" ARCHIVO.docx
```

Sus comprobaciones g) y h) son las de esta skill: espaciado de títulos
uniforme por nivel y saltos de página, incluidos los escondidos dentro
de un párrafo con texto. Resuelve el espaciado tanto si está escrito
en cada párrafo como si viene del estilo. Un ERROR en g) o h) significa
que el archivo NO está corregido.

El chequeo manual que sigue sirve para mirar el XML directamente o
cuando el verificador no está instalado. Solo ve el espaciado escrito
párrafo por párrafo (docx de npm o XML manipulado). En los docx de
`construir_docx.py` el espaciado está en `word/styles.xml`, así que el
conjunto del punto 2 sale vacío: eso no es un fallo ni una
confirmación, y hay que usar el verificador.

```bash
python -c "
import zipfile, re, html
z = zipfile.ZipFile('ARCHIVO.docx')
x = z.read('word/document.xml').decode('utf-8')

# 1. Saltos de página: contar y decidir si cada uno tiene justificación
print('saltos de pagina:', x.count('<w:br w:type=\"page\"/>'))

# 2. Espaciado de TODOS los títulos/subtítulos (Heading1/Heading2),
#    no asumir que un fix aplicado antes sigue vigente en este archivo
h1 = re.findall(r'<w:pStyle w:val=\"[^\"]+\"/><w:keepNext/><w:spacing w:before=\"(\d+)\" w:after=\"(\d+)\"/>', x)
print('valores de espaciado antes/despues encontrados (deben ser uniformes):', set(h1))

# 3. Integridad del zip
print('zip ok:', z.testzip() is None)
"
```

Si `set(h1)` muestra **más de un valor distinto**, o un valor que no es
el acordado con el usuario, el archivo NO está corregido, sin importar
qué diga el script fuente.

Si `set(h1)` sale **vacío**, el chequeo manual no comprobó nada: correr
`verificar_formato.py`.

## Regla para saltos de página forzados

- Cada `<w:br w:type="page"/>` deja espacio en blanco al final de la
  página anterior si el contenido no llena la hoja exactamente.
- Antes de forzar un salto de página, preguntarse: ¿esto es
  estructuralmente necesario (portada sola, índice separado) o es
  solo costumbre de "cada capítulo en página nueva"? Si es lo segundo
  y el usuario se queja de espacios en blanco, eliminarlo.
- Los saltos de página pueden estar **escondidos dentro de un párrafo
  de texto** (ej. pegados al final del run de un pie de foto), no solo
  como párrafo propio. Buscar `<w:br w:type="page"/>` en todo el XML,
  no solo en párrafos vacíos.

## Regla general (aplica más allá de docx)

Cuando el usuario señala un archivo específico y dice "este archivo
tiene el problema", **no asumir que una corrección hecha en otra
versión/generación ya se propagó ahí**. Verificar ESE archivo
puntual con una herramienta (grep, unzip+grep, script de lectura),
nunca por inferencia de "ya lo arreglé antes en el código".

## Antes de decir "listo" al usuario

No declarar un fix terminado hasta correr el checklist de arriba
sobre el archivo final y mostrar (al menos internamente) que los
valores son los esperados. Si no se puede verificar (ej. no hay forma
de generar PDF de vista previa), decirlo explícitamente en vez de dar
por buena la corrección.
