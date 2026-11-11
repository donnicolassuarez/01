# -*- coding: utf-8 -*-
"""Constructor único de documentos Word con el formato UAP.

Uso:
  python construir_docx.py <borrador/texto.md> --salida <entrega/nombre.docx>
         [--tipo ensayo|monografia|informe|articulo|otro]
         [--portada blanca|datos|ninguna] [--min-paginas N] [--max-paginas N]
         [--sin-pdf] [--conservar-pdf] [--json]

Lee un Markdown sencillo y produce un .docx con estilos reales de Word.
Después lo convierte a PDF con LibreOffice para contar páginas (el PDF
solo se guarda con --conservar-pdf).

Metadatos opcionales al inicio, entre dos líneas `---`:
  titulo, autor, institucion, carrera, materia, docente, lugar, fecha,
  tipo, portada  (formato `clave: valor`, una por línea)

Markdown admitido: `#`, `##`, `###` (Título 1/2/3); párrafos; **negrita**,
*cursiva*; listas `-` y `1.`; tablas de tubería con fila de encabezado
(el párrafo "Tabla N. ..." justo antes es su título; un párrafo "Nota. ..."
justo después es su nota); imágenes `![pie](ruta)`; citas en bloque `>`;
`\\pagebreak` en una línea sola; comentarios HTML `<!-- -->` (se eliminan).

Códigos de salida: 0 bien; 1 hay avisos (páginas fuera de rango o no
medidas, guardado con otro nombre, encabezados que faltan...); 2 no se
pudo construir.
"""
import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun  # noqa: E402

try:
    from docx import Document
    from docx.enum.section import WD_SECTION
    from docx.enum.style import WD_STYLE_TYPE
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor
except ImportError:  # se informa en main()
    Document = None

# --- Decisiones de formato (las reglas fijan fuente, interlineado,
# justificado y sangría; el resto se decide aquí y se aplica SOLO en los
# estilos, nunca párrafo por párrafo).
FUENTE = "Calibri"
TAMANO = 11                 # puntos, también en títulos
IDIOMA = "es-BO"
ANCHO_PAGINA_CM = 21.59     # carta
ALTO_PAGINA_CM = 27.94
MARGEN_CM = 2.54
INTERLINEADO = 1.15
SANGRIA_PRIMERA_CM = 1.25
SANGRIA_FRANCESA_CM = 1.27
SANGRIA_CITA_CM = 1.27
DESPUES_PARRAFO_PT = 6      # espacio único entre párrafos del cuerpo
ESPACIO_TITULOS = {         # nivel: (antes, después) en puntos
    1: (18, 6),
    2: (12, 6),
    3: (12, 6),
}
SOMBRA_ENCABEZADO_TABLA = "E7E6E6"
TIPOS = ("ensayo", "monografia", "informe", "articulo", "otro")
CLAVES_META = ("titulo", "autor", "institucion", "carrera", "materia",
               "docente", "lugar", "fecha", "tipo", "portada")
ENCABEZADOS_ENSAYO = ("Introducción", "Desarrollo", "Conclusiones")

PATRON_TITULO = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
PATRON_IMAGEN = re.compile(r"^!\[(.*?)\]\((.+?)\)\s*$")
PATRON_LISTA = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
PATRON_SEPARADOR_TABLA = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
PATRON_TITULO_TABLA = re.compile(r"^[*_]*Tabla\s*(\d+)?\s*[.:]?[*_]*\s*(.*)$", re.I)
PATRON_NOTA = re.compile(r"^[*_]*Nota[.:][*_]*\s*(.*)$")
PATRON_INLINE = re.compile(
    r"(\\\*)"                                 # asterisco escapado
    r"|\*\*\*(.+?)\*\*\*"                     # negrita y cursiva
    r"|\*\*(.+?)\*\*"                         # negrita
    r"|(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])"  # cursiva
    r"|\[([^\]]+)\]\(([^)\s]+)\)"            # enlace: queda el texto
)


# ---------------------------------------------------------------------------
# Lectura del Markdown

def separar_metadatos(texto):
    """Quita comentarios HTML y el bloque `---` inicial. Devuelve (meta, texto)."""
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    lineas = texto.lstrip("﻿").splitlines()
    while lineas and not lineas[0].strip():
        lineas.pop(0)
    meta = {}
    if lineas and lineas[0].strip() == "---":
        for i in range(1, len(lineas)):
            if lineas[i].strip() in ("---", "..."):
                for linea in lineas[1:i]:
                    if ":" in linea and not linea.lstrip().startswith("#"):
                        clave, valor = linea.split(":", 1)
                        clave = comun.normalizar(clave).replace(" ", "_")
                        valor = valor.strip().strip("\"'")
                        if clave in CLAVES_META and valor:
                            meta[clave] = valor
                lineas = lineas[i + 1:]
                break
    return meta, lineas


def partir_fila(linea):
    linea = linea.strip()
    if linea.startswith("|"):
        linea = linea[1:]
    if linea.endswith("|") and not linea.endswith("\\|"):
        linea = linea[:-1]
    celdas = re.split(r"(?<!\\)\|", linea)
    return [c.strip().replace("\\|", "|") for c in celdas]


def analizar_bloques(lineas):
    """Convierte las líneas en una lista de bloques (dicts con 'tipo')."""
    bloques, i, avisos = [], 0, []
    en_referencias = False
    while i < len(lineas):
        linea = lineas[i]
        limpia = linea.strip()
        if not limpia:
            i += 1
            continue
        if limpia in ("\\pagebreak", "\\newpage"):
            bloques.append({"tipo": "salto"})
            i += 1
            continue
        titulo = PATRON_TITULO.match(limpia)
        if titulo:
            nivel = len(titulo.group(1))
            if nivel > 3:
                avisos.append(f"título de nivel {nivel} tratado como nivel 3: "
                              f"«{titulo.group(2)[:50]}»")
                nivel = 3
            texto = titulo.group(2).strip().strip("*_").strip()
            en_referencias = comun.es_encabezado_referencias(texto)
            bloques.append({"tipo": "titulo", "nivel": nivel, "texto": texto,
                            "referencias": en_referencias})
            i += 1
            continue
        if en_referencias:
            # Cada línea no vacía es una referencia; una línea con sangría
            # continúa la anterior.
            entrada = re.sub(r"^([-*+]|\d+[.)])\s+", "", limpia)
            if linea[:1] in (" ", "\t") and bloques and bloques[-1]["tipo"] == "referencia":
                bloques[-1]["texto"] += " " + entrada
            else:
                bloques.append({"tipo": "referencia", "texto": entrada})
            i += 1
            continue
        imagen = PATRON_IMAGEN.match(limpia)
        if imagen:
            bloques.append({"tipo": "imagen", "pie": imagen.group(1).strip(),
                            "ruta": imagen.group(2).strip().strip("<>")})
            i += 1
            continue
        if limpia.startswith("|") and i + 1 < len(lineas) \
                and PATRON_SEPARADOR_TABLA.match(lineas[i + 1]):
            filas = [partir_fila(limpia)]
            i += 2
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                filas.append(partir_fila(lineas[i]))
                i += 1
            ancho = max(len(f) for f in filas)
            filas = [f + [""] * (ancho - len(f)) for f in filas]
            bloques.append({"tipo": "tabla", "filas": filas})
            continue
        if limpia.startswith(">"):
            parrafos, actual = [], []
            while i < len(lineas) and lineas[i].strip().startswith(">"):
                contenido = lineas[i].strip()[1:].strip()
                if contenido:
                    actual.append(contenido)
                elif actual:
                    parrafos.append(" ".join(actual))
                    actual = []
                i += 1
            if actual:
                parrafos.append(" ".join(actual))
            for parrafo in parrafos:
                bloques.append({"tipo": "cita", "texto": parrafo})
            continue
        lista = PATRON_LISTA.match(linea)
        if lista and not re.match(r"^\d+[.)]\s", limpia) or \
                (lista and re.match(r"^\d+[.)]\s", limpia)):
            ordenada = lista.group(2)[0].isdigit()
            elementos = []
            while i < len(lineas):
                actual = PATRON_LISTA.match(lineas[i])
                if actual and (actual.group(2)[0].isdigit() == ordenada
                               or len(actual.group(1)) >= 2):
                    if len(actual.group(1)) >= 2:
                        avisos.append("lista anidada aplanada a un nivel: "
                                      f"«{actual.group(3)[:50]}»")
                    elementos.append(actual.group(3).strip())
                elif lineas[i].strip() and lineas[i][:1] in (" ", "\t") and elementos:
                    elementos[-1] += " " + lineas[i].strip()
                else:
                    break
                i += 1
            bloques.append({"tipo": "lista", "ordenada": ordenada,
                            "elementos": elementos})
            continue
        # Párrafo: líneas seguidas hasta una vacía o un bloque distinto.
        partes = [limpia]
        i += 1
        while i < len(lineas):
            siguiente = lineas[i].strip()
            if (not siguiente or PATRON_TITULO.match(siguiente)
                    or siguiente.startswith((">", "|")) or PATRON_IMAGEN.match(siguiente)
                    or PATRON_LISTA.match(lineas[i]) or siguiente in ("\\pagebreak", "\\newpage")):
                break
            partes.append(siguiente)
            i += 1
        bloques.append({"tipo": "parrafo", "texto": " ".join(partes)})
    # Títulos de tabla y notas: el párrafo "Tabla N." justo antes y el
    # párrafo "Nota." justo después de una tabla.
    for indice, bloque in enumerate(bloques):
        if bloque["tipo"] != "tabla":
            continue
        if indice > 0 and bloques[indice - 1]["tipo"] == "parrafo":
            hallado = PATRON_TITULO_TABLA.match(bloques[indice - 1]["texto"])
            if hallado:
                bloques[indice - 1]["tipo"] = "titulo_tabla"
                bloques[indice - 1]["texto"] = hallado.group(2).strip().strip("*_")
                bloque["numero_fuente"] = hallado.group(1)
        if indice + 1 < len(bloques) and bloques[indice + 1]["tipo"] == "parrafo":
            hallado = PATRON_NOTA.match(bloques[indice + 1]["texto"])
            if hallado:
                bloques[indice + 1]["tipo"] = "nota_tabla"
                bloques[indice + 1]["texto"] = hallado.group(1).strip()
    return bloques, avisos


def trozos_inline(texto):
    """Divide un texto con **negrita**, *cursiva* y enlaces en (texto, b, i)."""
    resultado, posicion = [], 0
    for hallado in PATRON_INLINE.finditer(texto):
        if hallado.start() > posicion:
            resultado.append((texto[posicion:hallado.start()], False, False))
        if hallado.group(1):
            resultado.append(("*", False, False))
        elif hallado.group(2):
            resultado.append((hallado.group(2), True, True))
        elif hallado.group(3):
            for parte, _, cursiva in trozos_inline(hallado.group(3)):
                resultado.append((parte, True, cursiva))
        elif hallado.group(4):
            for parte, negrita, _ in trozos_inline(hallado.group(4)):
                resultado.append((parte, negrita, True))
        else:
            resultado.append((hallado.group(5), False, False))
        posicion = hallado.end()
    if posicion < len(texto):
        resultado.append((texto[posicion:], False, False))
    return [t for t in resultado if t[0]]


# ---------------------------------------------------------------------------
# Estilos

def fijar_fuente_rpr(rpr, tamano=TAMANO, negrita=None, cursiva=None):
    """Calibri en las cuatro ranuras, sin fuentes de tema, tamaño y color."""
    fuentes = rpr.find(qn("w:rFonts"))
    if fuentes is None:
        fuentes = OxmlElement("w:rFonts")
        rpr.insert(0, fuentes)
    for atributo in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if fuentes.get(qn(atributo)) is not None:
            del fuentes.attrib[qn(atributo)]
    for atributo in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        fuentes.set(qn(atributo), FUENTE)
    for etiqueta, valor in (("w:sz", tamano * 2), ("w:szCs", tamano * 2)):
        nodo = rpr.find(qn(etiqueta))
        if nodo is None:
            nodo = OxmlElement(etiqueta)
            rpr.append(nodo)
        nodo.set(qn("w:val"), str(valor))
    color = rpr.find(qn("w:color"))
    if color is not None:
        rpr.remove(color)
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "000000")
    rpr.append(color)
    for etiquetas, valor in ((("w:b", "w:bCs"), negrita), (("w:i", "w:iCs"), cursiva)):
        if valor is None:
            continue
        for etiqueta in etiquetas:
            nodo = rpr.find(qn(etiqueta))
            if nodo is not None:
                rpr.remove(nodo)
            nodo = OxmlElement(etiqueta)
            if not valor:
                nodo.set(qn("w:val"), "0")
            rpr.append(nodo)


def rpr_de_estilo(estilo):
    return estilo.element.get_or_add_rPr()


def configurar_parrafo(estilo, alineacion, primera=0.0, izquierda=0.0,
                       antes=0, despues=DESPUES_PARRAFO_PT, con_siguiente=False):
    formato = estilo.paragraph_format
    formato.alignment = alineacion
    formato.first_line_indent = Cm(primera)
    formato.left_indent = Cm(izquierda)
    formato.right_indent = Cm(0)
    formato.space_before = Pt(antes)
    formato.space_after = Pt(despues)
    formato.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    formato.line_spacing = INTERLINEADO
    formato.widow_control = True
    formato.keep_with_next = con_siguiente
    ppr = estilo.element.get_or_add_pPr()
    for etiqueta in ("w:contextualSpacing", "w:numPr"):
        nodo = ppr.find(qn(etiqueta))
        if nodo is not None:
            ppr.remove(nodo)


def estilo_parrafo(documento, nombre, base="Normal"):
    try:
        estilo = documento.styles[nombre]
    except KeyError:
        estilo = documento.styles.add_style(nombre, WD_STYLE_TYPE.PARAGRAPH)
    estilo.base_style = documento.styles[base] if base else None
    estilo.quick_style = True
    return estilo


def preparar_estilos(documento):
    estilos = documento.styles
    # Valores por defecto del documento.
    defectos = estilos.element.find(qn("w:docDefaults"))
    rpr = defectos.find(qn("w:rPrDefault")).find(qn("w:rPr"))
    fijar_fuente_rpr(rpr)
    idioma = rpr.find(qn("w:lang"))
    if idioma is None:
        idioma = OxmlElement("w:lang")
        rpr.append(idioma)
    idioma.set(qn("w:val"), IDIOMA)
    idioma.set(qn("w:eastAsia"), IDIOMA)
    ppr = defectos.find(qn("w:pPrDefault")).find(qn("w:pPr"))
    espaciado = ppr.find(qn("w:spacing"))
    espaciado.set(qn("w:before"), "0")
    espaciado.set(qn("w:after"), "0")
    espaciado.set(qn("w:line"), str(round(240 * INTERLINEADO)))
    espaciado.set(qn("w:lineRule"), "auto")

    normal = estilos["Normal"]
    fijar_fuente_rpr(rpr_de_estilo(normal))
    configurar_parrafo(normal, WD_ALIGN_PARAGRAPH.JUSTIFY, primera=SANGRIA_PRIMERA_CM)

    for nivel, (antes, despues) in ESPACIO_TITULOS.items():
        titulo = estilos[f"Heading {nivel}"]
        fijar_fuente_rpr(rpr_de_estilo(titulo), negrita=True, cursiva=(nivel == 3))
        configurar_parrafo(titulo, WD_ALIGN_PARAGRAPH.LEFT, antes=antes,
                           despues=despues, con_siguiente=True)
        titulo.paragraph_format.keep_together = True
        titulo.paragraph_format.page_break_before = False

    for nombre in ("List Bullet", "List Number"):
        lista = estilos[nombre]
        fijar_fuente_rpr(rpr_de_estilo(lista))
        configurar_parrafo(lista, WD_ALIGN_PARAGRAPH.JUSTIFY, primera=-0.63,
                           izquierda=1.27, despues=3)

    cita = estilo_parrafo(documento, "Cita en bloque")
    fijar_fuente_rpr(rpr_de_estilo(cita))
    configurar_parrafo(cita, WD_ALIGN_PARAGRAPH.JUSTIFY, izquierda=SANGRIA_CITA_CM)

    referencia = estilo_parrafo(documento, "Referencia")
    fijar_fuente_rpr(rpr_de_estilo(referencia))
    configurar_parrafo(referencia, WD_ALIGN_PARAGRAPH.LEFT,
                       primera=-SANGRIA_FRANCESA_CM, izquierda=SANGRIA_FRANCESA_CM)

    leyenda = estilos["Caption"]
    fijar_fuente_rpr(rpr_de_estilo(leyenda), negrita=False)
    configurar_parrafo(leyenda, WD_ALIGN_PARAGRAPH.LEFT, antes=6, despues=6)

    figura = estilo_parrafo(documento, "Figura")
    fijar_fuente_rpr(rpr_de_estilo(figura))
    configurar_parrafo(figura, WD_ALIGN_PARAGRAPH.CENTER, antes=6, despues=0,
                       con_siguiente=True)

    tabla = estilo_parrafo(documento, "Texto de tabla")
    fijar_fuente_rpr(rpr_de_estilo(tabla))
    configurar_parrafo(tabla, WD_ALIGN_PARAGRAPH.LEFT, despues=0)

    # Primer párrafo tras una tabla: igual que Normal, con aire antes.
    tras_tabla = estilo_parrafo(documento, "Texto tras tabla")
    configurar_parrafo(tras_tabla, WD_ALIGN_PARAGRAPH.JUSTIFY,
                       primera=SANGRIA_PRIMERA_CM, antes=12)

    nota = estilo_parrafo(documento, "Nota de tabla")
    fijar_fuente_rpr(rpr_de_estilo(nota))
    configurar_parrafo(nota, WD_ALIGN_PARAGRAPH.LEFT, antes=3)

    portada = estilo_parrafo(documento, "Portada")
    fijar_fuente_rpr(rpr_de_estilo(portada))
    configurar_parrafo(portada, WD_ALIGN_PARAGRAPH.CENTER, despues=12)
    portada_titulo = estilo_parrafo(documento, "Portada título", base="Portada")
    fijar_fuente_rpr(rpr_de_estilo(portada_titulo), negrita=True)
    configurar_parrafo(portada_titulo, WD_ALIGN_PARAGRAPH.CENTER, antes=96, despues=96)

    pie = estilos["Footer"]
    fijar_fuente_rpr(rpr_de_estilo(pie))
    configurar_parrafo(pie, WD_ALIGN_PARAGRAPH.CENTER, despues=0)

    # Estilos de carácter enlazados a los títulos: sin fuentes de tema ni color.
    for estilo in estilos:
        if estilo.type == WD_STYLE_TYPE.CHARACTER and estilo.element.rPr is not None:
            fuentes = estilo.element.rPr.find(qn("w:rFonts"))
            if fuentes is not None:
                fijar_fuente_rpr(estilo.element.rPr, tamano=TAMANO)


# ---------------------------------------------------------------------------
# Numeración de listas

def preparar_numeracion(documento):
    """Crea dos definiciones abstractas (viñeta y número) y devuelve una
    función que da un numId nuevo para cada lista (los números reinician)."""
    numeracion = documento.part.numbering_part.element
    ids = [int(n.get(qn("w:abstractNumId"))) for n in numeracion.findall(qn("w:abstractNum"))]
    siguiente_abstracto = max(ids, default=0) + 1
    abstractos = {}
    for ordenada in (False, True):
        abstracto = OxmlElement("w:abstractNum")
        abstracto.set(qn("w:abstractNumId"), str(siguiente_abstracto))
        multinivel = OxmlElement("w:multiLevelType")
        multinivel.set(qn("w:val"), "singleLevel")
        abstracto.append(multinivel)
        nivel = OxmlElement("w:lvl")
        nivel.set(qn("w:ilvl"), "0")
        for etiqueta, valor in (("w:start", "1"),
                                ("w:numFmt", "decimal" if ordenada else "bullet"),
                                ("w:lvlText", "%1." if ordenada else "•"),
                                ("w:lvlJc", "left")):
            nodo = OxmlElement(etiqueta)
            nodo.set(qn("w:val"), valor)
            nivel.append(nodo)
        ppr = OxmlElement("w:pPr")
        sangria = OxmlElement("w:ind")
        sangria.set(qn("w:left"), str(round(1.27 * 567)))
        sangria.set(qn("w:hanging"), str(round(0.63 * 567)))
        ppr.append(sangria)
        nivel.append(ppr)
        rpr = OxmlElement("w:rPr")
        fijar_fuente_rpr(rpr)
        nivel.append(rpr)
        abstracto.append(nivel)
        primero_num = numeracion.find(qn("w:num"))
        if primero_num is not None:
            primero_num.addprevious(abstracto)
        else:
            numeracion.append(abstracto)
        abstractos[ordenada] = siguiente_abstracto
        siguiente_abstracto += 1

    def nueva_lista(ordenada):
        existentes = [int(n.get(qn("w:numId"))) for n in numeracion.findall(qn("w:num"))]
        num_id = max(existentes, default=0) + 1
        num = OxmlElement("w:num")
        num.set(qn("w:numId"), str(num_id))
        referencia = OxmlElement("w:abstractNumId")
        referencia.set(qn("w:val"), str(abstractos[ordenada]))
        num.append(referencia)
        reinicio = OxmlElement("w:lvlOverride")
        reinicio.set(qn("w:ilvl"), "0")
        inicio = OxmlElement("w:startOverride")
        inicio.set(qn("w:val"), "1")
        reinicio.append(inicio)
        num.append(reinicio)
        numeracion.append(num)
        return num_id

    return nueva_lista


def asignar_numeracion(parrafo, num_id):
    ppr = parrafo._p.get_or_add_pPr()
    num_pr = OxmlElement("w:numPr")
    nivel = OxmlElement("w:ilvl")
    nivel.set(qn("w:val"), "0")
    numero = OxmlElement("w:numId")
    numero.set(qn("w:val"), str(num_id))
    num_pr.append(nivel)
    num_pr.append(numero)
    ppr.append(num_pr)


# ---------------------------------------------------------------------------
# Construcción

def agregar_texto(parrafo, texto, negrita=False, cursiva=False):
    for parte, b, i in trozos_inline(texto):
        run = parrafo.add_run(parte)
        if b or negrita:
            run.bold = True
        if i or cursiva:
            run.italic = True


def campo_pagina(parrafo):
    """Inserta el campo PAGE (número de página) en el párrafo."""
    for tipo, instruccion in (("begin", None), (None, " PAGE "), ("separate", None),
                              (None, None), ("end", None)):
        run = parrafo.add_run()
        if tipo:
            caracter = OxmlElement("w:fldChar")
            caracter.set(qn("w:fldCharType"), tipo)
            run._r.append(caracter)
        elif instruccion:
            nodo = OxmlElement("w:instrText")
            nodo.set(qn("xml:space"), "preserve")
            nodo.text = instruccion
            run._r.append(nodo)
        else:
            run.text = "1"


def bordes_tabla(tabla):
    propiedades = tabla._tbl.tblPr
    bordes = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        borde = OxmlElement(f"w:{lado}")
        borde.set(qn("w:val"), "single")
        borde.set(qn("w:sz"), "4")
        borde.set(qn("w:space"), "0")
        borde.set(qn("w:color"), "000000")
        bordes.append(borde)
    propiedades.append(bordes)
    disposicion = OxmlElement("w:tblLayout")
    disposicion.set(qn("w:type"), "fixed")
    propiedades.append(disposicion)


def anchos_columnas(filas, total_cm):
    """Ancho de cada columna proporcional a su texto (raíz), mínimo 2 cm."""
    pesos = []
    for columna in range(len(filas[0])):
        largo = max(len(fila[columna]) for fila in filas)
        palabra = max((len(p) for fila in filas for p in fila[columna].split()), default=1)
        pesos.append(max(largo ** 0.5, palabra * 0.35, 1.0))
    suma = sum(pesos)
    anchos = [max(2.0, total_cm * p / suma) for p in pesos]
    escala = total_cm / sum(anchos)
    return [a * escala for a in anchos]


def construir_tabla(documento, filas, util_cm):
    tabla = documento.add_table(rows=len(filas), cols=len(filas[0]))
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabla.autofit = False
    bordes_tabla(tabla)
    anchos = anchos_columnas(filas, util_cm)
    for indice, ancho in enumerate(anchos):
        tabla.columns[indice].width = Cm(ancho)
    for numero_fila, fila in enumerate(filas):
        fila_docx = tabla.rows[numero_fila]
        propiedades = fila_docx._tr.get_or_add_trPr()
        no_partir = OxmlElement("w:cantSplit")
        propiedades.append(no_partir)
        if numero_fila == 0:
            repetir = OxmlElement("w:tblHeader")
            propiedades.append(repetir)
        for numero_celda, texto in enumerate(fila):
            celda = fila_docx.cells[numero_celda]
            celda.width = Cm(anchos[numero_celda])
            parrafo = celda.paragraphs[0]
            parrafo.style = documento.styles["Texto de tabla"]
            agregar_texto(parrafo, texto, negrita=(numero_fila == 0))
            if numero_fila == 0:
                sombra = OxmlElement("w:shd")
                sombra.set(qn("w:val"), "clear")
                sombra.set(qn("w:color"), "auto")
                sombra.set(qn("w:fill"), SOMBRA_ENCABEZADO_TABLA)
                celda._tc.get_or_add_tcPr().append(sombra)
    return tabla


def portada_datos(documento, meta):
    lineas = [(meta.get(c, ""), "Portada") for c in ("institucion", "carrera", "materia")]
    lineas.append((meta.get("titulo", ""), "Portada título"))
    lineas.append((meta.get("autor", ""), "Portada"))
    if meta.get("docente"):
        lineas.append(("Docente: " + meta["docente"], "Portada"))
    lugar_fecha = ", ".join(v for v in (meta.get("lugar"), meta.get("fecha")) if v)
    lineas.append((lugar_fecha, "Portada"))
    escritas = 0
    for texto, estilo in lineas:
        if texto:
            parrafo = documento.add_paragraph(style=estilo)
            agregar_texto(parrafo, texto)
            escritas += 1
    return escritas


def construir(bloques, meta, opciones, carpeta_md, avisos, notas):
    documento = Document()
    preparar_estilos(documento)
    nueva_lista = preparar_numeracion(documento)
    seccion = documento.sections[0]
    seccion.page_width = Cm(ANCHO_PAGINA_CM)
    seccion.page_height = Cm(ALTO_PAGINA_CM)
    for lado in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(seccion, lado, Cm(MARGEN_CM))
    seccion.header_distance = Cm(1.27)
    seccion.footer_distance = Cm(1.27)
    util_cm = ANCHO_PAGINA_CM - 2 * MARGEN_CM
    # El documento nuevo trae un párrafo vacío: se reutiliza o se elimina.
    for parrafo in list(documento.paragraphs):
        parrafo._p.getparent().remove(parrafo._p)

    propiedades = documento.core_properties
    propiedades.title = meta.get("titulo", "")
    propiedades.author = meta.get("autor", "")
    propiedades.language = IDIOMA

    portada = opciones["portada"]
    if portada != "ninguna":
        if portada == "datos":
            if not meta.get("titulo"):
                avisos.append("portada «datos» sin título en los metadatos")
            if not portada_datos(documento, meta):
                documento.add_paragraph(style="Portada")
        else:
            documento.add_paragraph()
        # Único salto estructural: salto de sección a página nueva. La
        # sección de la portada no tiene pie, así que no muestra número.
        nueva = documento.add_section(WD_SECTION.NEW_PAGE)
        seccion_pie = nueva
    else:
        seccion_pie = seccion
    seccion_pie.footer.is_linked_to_previous = False
    pie = seccion_pie.footer.paragraphs[0]
    pie.style = documento.styles["Footer"]
    campo_pagina(pie)

    cuenta = {"titulos": 0, "tablas": 0, "figuras": 0}
    referencias = []
    titulo_tabla_pendiente = None
    anterior = None
    for bloque in bloques:
        tipo = bloque["tipo"]
        anterior, previo = tipo, anterior
        if tipo == "titulo":
            parrafo = documento.add_paragraph(style=f"Heading {bloque['nivel']}")
            agregar_texto(parrafo, bloque["texto"])
            cuenta["titulos"] += 1
        elif tipo == "parrafo":
            estilo = "Texto tras tabla" if previo in ("tabla", "nota_tabla") else "Normal"
            parrafo = documento.add_paragraph(style=estilo)
            agregar_texto(parrafo, bloque["texto"])
        elif tipo == "cita":
            texto = bloque["texto"].strip()
            if len(texto) > 1 and texto[0] in "\"“«" and texto[-1] in "\"”»":
                texto = texto[1:-1].strip()
            parrafo = documento.add_paragraph(style="Cita en bloque")
            agregar_texto(parrafo, texto)
        elif tipo == "lista":
            num_id = nueva_lista(bloque["ordenada"])
            estilo = "List Number" if bloque["ordenada"] else "List Bullet"
            for elemento in bloque["elementos"]:
                parrafo = documento.add_paragraph(style=estilo)
                asignar_numeracion(parrafo, num_id)
                agregar_texto(parrafo, elemento)
        elif tipo == "titulo_tabla":
            titulo_tabla_pendiente = bloque["texto"]
        elif tipo == "tabla":
            cuenta["tablas"] += 1
            parrafo = documento.add_paragraph(style="Caption")
            if bloque.get("numero_fuente") and int(bloque["numero_fuente"]) != cuenta["tablas"]:
                avisos.append(f"la «Tabla {bloque['numero_fuente']}» del texto se numeró "
                              f"{cuenta['tablas']}: revisar las menciones en el cuerpo")
            run = parrafo.add_run(f"Tabla {cuenta['tablas']}.")
            run.bold = True
            if titulo_tabla_pendiente:
                parrafo.add_run(" ")
                agregar_texto(parrafo, titulo_tabla_pendiente, cursiva=True)
            else:
                avisos.append(f"la tabla {cuenta['tablas']} no tiene título "
                              "(párrafo «Tabla N. ...» antes de la tabla)")
            # El título debe quedar con la tabla.
            parrafo.paragraph_format.keep_with_next = True
            titulo_tabla_pendiente = None
            construir_tabla(documento, bloque["filas"], util_cm)
        elif tipo == "nota_tabla":
            parrafo = documento.add_paragraph(style="Nota de tabla")
            run = parrafo.add_run("Nota.")
            run.italic = True
            parrafo.add_run(" ")
            agregar_texto(parrafo, bloque["texto"])
        elif tipo == "imagen":
            ruta = Path(bloque["ruta"])
            if not ruta.is_absolute():
                ruta = carpeta_md / ruta
            if not ruta.exists():
                avisos.append(f"imagen no encontrada: {bloque['ruta']}")
                continue
            cuenta["figuras"] += 1
            parrafo = documento.add_paragraph(style="Figura")
            run = parrafo.add_run()
            imagen = run.add_picture(str(ruta))
            maximo_ancho, maximo_alto = Cm(util_cm), Cm(18)
            escala = min(1.0, maximo_ancho / imagen.width, maximo_alto / imagen.height)
            imagen.width = int(imagen.width * escala)
            imagen.height = int(imagen.height * escala)
            pie_figura = documento.add_paragraph(style="Caption")
            pie_figura.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = pie_figura.add_run(f"Figura {cuenta['figuras']}.")
            run.bold = True
            if bloque["pie"]:
                pie_figura.add_run(" ")
                agregar_texto(pie_figura, re.sub(r"^Figura\s*\d*\.?\s*", "", bloque["pie"]),
                              cursiva=True)
            else:
                avisos.append(f"la figura {cuenta['figuras']} no tiene pie")
        elif tipo == "salto":
            parrafo = documento.add_paragraph()
            parrafo.add_run().add_break(WD_BREAK.PAGE)
        elif tipo == "referencia":
            referencias.append(bloque["texto"])
            continue
        # Al cerrar el bloque de referencias (siguiente título o fin), se
        # escriben ordenadas; aquí no hace falta nada más.
        if tipo == "titulo" and bloque.get("referencias"):
            bloque["_ancla"] = parrafo
    # Las referencias se escriben al final de su sección, ordenadas.
    return documento, cuenta, referencias


def escribir_referencias(documento, bloques, notas):
    """Coloca cada grupo de referencias tras su encabezado, en orden alfabético."""
    grupos, actual = [], None
    for bloque in bloques:
        if bloque["tipo"] == "titulo":
            actual = {"ancla": bloque.get("_ancla"), "entradas": []} if bloque.get("referencias") else None
            if actual:
                grupos.append(actual)
        elif bloque["tipo"] == "referencia" and actual is not None:
            actual["entradas"].append(bloque["texto"])
    total = 0
    for grupo in grupos:
        entradas = grupo["entradas"]
        ordenadas = sorted(entradas, key=lambda r: comun.normalizar(r.lstrip("*_")))
        if ordenadas != entradas:
            notas.append("referencias reordenadas alfabéticamente "
                         f"({len(entradas)} entradas)")
        ancla = grupo["ancla"]._p
        for entrada in reversed(ordenadas):
            parrafo = documento.add_paragraph(style="Referencia")
            agregar_texto(parrafo, entrada)
            ancla.addnext(parrafo._p)
        total += len(entradas)
    return total


# ---------------------------------------------------------------------------
# Guardado y medición

def guardar_seguro(documento, destino, avisos):
    """Guarda en temporal, comprueba y copia al destino. Devuelve la ruta final."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="agac_docx_") as temporal:
        provisional = Path(temporal) / "documento.docx"
        documento.save(str(provisional))
        Document(str(provisional))  # se puede volver a abrir
        candidatos = [destino] + [destino.with_name(f"{destino.stem}_nuevo{'' if n == 1 else n}{destino.suffix}")
                                  for n in range(1, 6)]
        for candidato in candidatos:
            parcial = candidato.with_name(f".{candidato.name}.parcial")
            try:
                shutil.copyfile(provisional, parcial)
                os.replace(parcial, candidato)
            except PermissionError:
                try:
                    parcial.unlink()
                except OSError:
                    pass
                continue
            if candidato != destino:
                avisos.append(f"el destino {destino.name} está bloqueado (¿abierto en Word?); "
                              f"se guardó como {candidato.name}")
            return candidato
    raise PermissionError(f"no se pudo escribir en {destino.parent}")


def contar_palabras(documento):
    total = cuerpo = 0
    en_referencias = False
    for parrafo in documento.paragraphs:
        texto = parrafo.text.strip()
        if parrafo.style.name.lower().startswith("heading"):
            en_referencias = comun.es_encabezado_referencias(texto)
        palabras = len(texto.split())
        total += palabras
        if not en_referencias:
            cuerpo += palabras
    for tabla in documento.tables:
        for fila in tabla.rows:
            for celda in fila.cells:
                n = len(celda.text.split())
                total += n
                cuerpo += n
    return total, cuerpo


def medir(ruta_docx, conservar, siguiente_tras_referencias):
    """Renderiza y mide. Devuelve dict con páginas o con 'error'."""
    with tempfile.TemporaryDirectory(prefix="agac_pdf_") as temporal:
        try:
            pdf = comun.renderizar_pdf(ruta_docx, temporal)
            paginas = comun.medir_pdf(pdf)
            referencias = comun.paginas_seccion_pdf(
                pdf, margen_sup_cm=MARGEN_CM, margen_inf_cm=MARGEN_CM,
                siguiente=siguiente_tras_referencias)
        except comun.ErrorRender as error:
            return {"error": str(error)}
        except ImportError:
            return {"error": "PyMuPDF no está instalado (pip install pymupdf)"}
        resultado = {"paginas": len(paginas), "paginas_referencias": referencias,
                     "carta": all(abs(p["ancho_cm"] - ANCHO_PAGINA_CM) < 0.1
                                  and abs(p["alto_cm"] - ALTO_PAGINA_CM) < 0.1
                                  for p in paginas)}
        if conservar:
            destino = Path(ruta_docx).with_suffix(".pdf")
            try:
                shutil.copyfile(pdf, destino)
                resultado["pdf"] = str(destino)
            except PermissionError:
                resultado["pdf_error"] = f"no se pudo guardar {destino.name} (bloqueado)"
        return resultado


# ---------------------------------------------------------------------------

def main():
    comun.salida_utf8()
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("markdown")
    analizador.add_argument("--salida", required=True)
    analizador.add_argument("--tipo", choices=TIPOS)
    analizador.add_argument("--portada", choices=("blanca", "datos", "ninguna"))
    analizador.add_argument("--min-paginas", type=int)
    analizador.add_argument("--max-paginas", type=int)
    analizador.add_argument("--sin-pdf", action="store_true",
                            help="no renderiza ni cuenta páginas")
    analizador.add_argument("--conservar-pdf", action="store_true",
                            help="guarda el PDF de medición junto al docx")
    analizador.add_argument("--json", action="store_true")
    args = analizador.parse_args()

    def fallar(mensaje):
        if args.json:
            print(json.dumps({"ok": False, "error": mensaje}, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR: {mensaje}", file=sys.stderr)
        sys.exit(2)

    if Document is None:
        fallar("falta python-docx (pip install python-docx)")
    origen = Path(args.markdown)
    if not origen.is_file():
        fallar(f"no existe {origen}")
    if Path(args.salida).suffix.lower() != ".docx":
        fallar("--salida debe terminar en .docx")
    try:
        texto = origen.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        fallar(f"{origen} no está en UTF-8")

    avisos, notas = [], []
    meta, lineas = separar_metadatos(texto)
    tipo = args.tipo or comun.normalizar(meta.get("tipo", "")) or "otro"
    if tipo not in TIPOS:
        avisos.append(f"tipo «{tipo}» desconocido; se usa «otro»")
        tipo = "otro"
    portada = args.portada or comun.normalizar(meta.get("portada", "")) or \
        ("blanca" if tipo in ("ensayo", "monografia") else "ninguna")
    if portada not in ("blanca", "datos", "ninguna"):
        avisos.append(f"portada «{portada}» desconocida; se usa «blanca»")
        portada = "blanca"

    bloques, avisos_md = analizar_bloques(lineas)
    avisos.extend(avisos_md)
    if not any(b["tipo"] in ("parrafo", "titulo") for b in bloques):
        fallar("el Markdown no tiene contenido")
    if tipo in ("ensayo", "monografia"):
        titulos = [comun.normalizar(b["texto"]) for b in bloques if b["tipo"] == "titulo"]
        for nombre in ENCABEZADOS_ENSAYO:
            if comun.normalizar(nombre) not in titulos:
                avisos.append(f"falta el encabezado «{nombre}» (solo, como título)")
    for bloque in bloques:
        textos = [bloque.get("texto", "")] + bloque.get("elementos", []) + \
            [c for fila in bloque.get("filas", []) for c in fila]
        convertido = " | ".join("".join(t for t, _, _ in trozos_inline(x)) for x in textos)
        contenido = convertido
        if re.search(r"\*\*|__|`|^#+\s|!\[|\]\(", contenido):
            avisos.append(f"posible Markdown sin convertir: «{contenido[:60]}»")

    try:
        documento, cuenta, _ = construir(bloques, meta, {"portada": portada},
                                         origen.parent, avisos, notas)
        n_referencias = escribir_referencias(documento, bloques, notas)
    except Exception as error:  # noqa: BLE001 - se informa la causa
        fallar(f"no se pudo construir el documento: {type(error).__name__}: {error}")
    if n_referencias == 0:
        avisos.append("no hay sección de referencias")

    try:
        final = guardar_seguro(documento, args.salida, avisos)
    except Exception as error:  # noqa: BLE001
        fallar(f"no se pudo guardar: {error}")

    total, cuerpo = contar_palabras(documento)
    # Encabezado que sigue a las referencias (para saber dónde terminan).
    siguiente = None
    vistos = False
    for bloque in bloques:
        if bloque["tipo"] == "titulo":
            if vistos:
                siguiente = bloque["texto"]
                break
            vistos = bloque.get("referencias", False)
    medida = {}
    if args.sin_pdf:
        avisos.append("páginas no medidas (--sin-pdf)")
    else:
        medida = medir(final, args.conservar_pdf, siguiente)
        if "error" in medida:
            avisos.append(f"páginas no medidas: {medida['error']}")
        else:
            paginas = medida["paginas"]
            if args.min_paginas and paginas < args.min_paginas:
                avisos.append(f"{paginas} páginas: por debajo del mínimo ({args.min_paginas})")
            if args.max_paginas and paginas > args.max_paginas:
                avisos.append(f"{paginas} páginas: por encima del máximo ({args.max_paginas})")
            if not medida["carta"]:
                avisos.append("el PDF no salió en tamaño carta")
            if medida.get("paginas_referencias") and medida["paginas_referencias"] > 1.5:
                notas.append(f"las referencias ocupan {medida['paginas_referencias']} páginas "
                             "(más de 1,5: límite de pregrado)")
            if medida.get("pdf_error"):
                avisos.append(medida["pdf_error"])

    informe = {
        "ok": not avisos,
        "archivo": str(final),
        "tipo": tipo,
        "portada": portada,
        "paginas": medida.get("paginas"),
        "paginas_referencias": medida.get("paginas_referencias"),
        "pdf": medida.get("pdf"),
        "palabras_total": total,
        "palabras_sin_referencias": cuerpo,
        "titulos": cuenta["titulos"],
        "tablas": cuenta["tablas"],
        "figuras": cuenta["figuras"],
        "referencias": n_referencias,
        "avisos": avisos,
        "notas": notas,
    }
    if args.json:
        print(json.dumps(informe, ensure_ascii=False, indent=2))
    else:
        print(f"Archivo: {final}")
        print(f"Tipo: {tipo} | portada: {portada}")
        if informe["paginas"] is not None:
            linea = f"Páginas (PDF, carta): {informe['paginas']}"
            if informe["paginas_referencias"] is not None:
                linea += f" | referencias: {informe['paginas_referencias']}"
            print(linea)
        else:
            print("Páginas: NO MEDIDAS")
        print(f"Palabras: {total} (sin referencias: {cuerpo})")
        print(f"Títulos: {cuenta['titulos']} | tablas: {cuenta['tablas']} | "
              f"figuras: {cuenta['figuras']} | referencias: {n_referencias}")
        if informe["pdf"]:
            print(f"PDF: {informe['pdf']}")
        for nota in notas:
            print(f"NOTA: {nota}")
        for aviso in avisos:
            print(f"AVISO: {aviso}")
    sys.exit(0 if not avisos else 1)


if __name__ == "__main__":
    main()
