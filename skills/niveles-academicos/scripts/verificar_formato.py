# -*- coding: utf-8 -*-
"""Control de formato independiente sobre el .docx FINAL real.

Uso:
  python verificar_formato.py <archivo.docx>
         [--tipo ensayo|monografia|informe|articulo|perfil|tesis|otro]
         [--variante NOMBRE] [--portada blanca|datos|ninguna]
         [--min-paginas N] [--max-paginas N] [--max-paginas-referencias 1.5] [--json]

No reutiliza nada del constructor: abre el archivo, lee su XML y resuelve
la herencia de formato (run -> estilo de carácter -> estilo de párrafo ->
basado en -> estilo de tabla -> docDefaults). Cada comprobación da OK,
ERROR (bloquea la entrega) o AVISO, con el lugar: número de párrafo (§N,
contando todos los párrafos del cuerpo en orden, también los de tablas)
y sus primeras palabras.

Comprobaciones: a) integridad; b) tamaño carta y márgenes; c) tipografía
efectiva; d) interlineado; e) alineación y sangrías; f) títulos con
estilos reales y jerarquía; g) espaciado uniforme; h) saltos de página;
i) párrafos vacíos seguidos; j) marcadores prohibidos; k) autonomía;
l) referencias; m) restos de Markdown; n) páginas en el PDF (LibreOffice);
o) portada y secciones según el tipo.

o) lee la definición del tipo en skills/tipos-de-trabajo/tipos.json
(../../tipos-de-trabajo/tipos.json desde este script; si no está, la ruta
de la variable TIPOS_TRABAJO): portada por defecto del tipo (o --portada),
secciones obligatorias presentes, con el nivel pedido y en orden, y
resumen y palabras clave cuando el tipo los exige (índice: solo AVISO).
`--variante` elige una variante del tipo (p. ej. `capitulos` en
monografía); sin ella rige la estructura por defecto. Sin tipos.json rige
la regla anterior (solo ensayo y monografía) con un AVISO en o); con
tipos.json corrupto sale con 2.

Heurística de marcadores (j), para no confundir palabras comunes:
- "por verificar", "lorem ipsum", "[cita...]", "[]", "¿?" -> siempre.
- "pendiente" y "completar" solo con forma de marcador: entre corchetes
  o paréntesis, en MAYÚSCULAS, o seguidos de dos puntos ("Pendiente:").
  "La pendiente del terreno" o "falta completar el censo" no cuentan.
- "TODO" (y "PENDIENTE"/"COMPLETAR" en mayúsculas) solo aislado: no
  cuenta si la palabra vecina también va en mayúsculas ("TODO EL PAÍS"
  o "LA PENDIENTE DEL TERRENO" en un título); "TODO:" sí.
- "XXX" no cuenta tras "siglo", "capítulo", "congreso", etc. (romano).
- "[...]" o "[…]" es elisión legítima dentro de una cita; solo es
  ERROR si el párrafo es casi solo eso (relleno) y AVISO si aparece
  fuera de comillas o de una cita en bloque.

Códigos de salida: 0 conforme; 1 hay algún ERROR; 2 no se pudo ejecutar.
"""
import argparse
import importlib.util
import json
import os
import re
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun  # noqa: E402

try:
    from docx import Document
    from docx.oxml.ns import qn
except ImportError:
    Document = None

FUENTE = "calibri"
TAMANO = 11.0
LINEA_115 = (272, 280)          # w:line en 240avos (1,15 = 276)
CARTA = (12240, 15840)          # twips
TOLERANCIA_PAGINA = 20
MARGEN_UAP = 1440               # 2,54 cm
TWIP_CM = 567.0
NIVELES = ("ERROR", "AVISO", "OK")
NOMBRES = {
    "a": "integridad del archivo", "b": "tamaño de página y márgenes",
    "c": "tipografía", "d": "interlineado", "e": "alineación y sangrías",
    "f": "títulos y jerarquía", "g": "espaciado", "h": "saltos de página",
    "i": "párrafos vacíos", "j": "marcadores prohibidos", "k": "autonomía",
    "l": "referencias", "m": "restos de Markdown", "n": "páginas (PDF)",
    "o": "portada y encabezados del tipo",
}
MAX_LUGARES = 12
TIPOS_ANTERIORES = ("ensayo", "monografia", "informe", "articulo", "otro")
TIPOS_SIN_DEFINICION = ("perfil", "tesis")  # sin tipos.json: «no aplica»


def localizar_tipos():
    """(módulo, ruta de tipos.json, aviso). Sin archivo: (None, None, aviso)."""
    base = Path(__file__).resolve().parent.parent.parent / "tipos-de-trabajo"
    candidatos = [base / "tipos.json"]
    variable = os.environ.get("TIPOS_TRABAJO", "").strip()
    if variable:
        candidatos.append(Path(variable))
    ruta = next((c for c in candidatos if c.is_file()), None)
    if ruta is None:
        return None, None, ("no se encontró tipos.json (ni en la skill tipos-de-trabajo ni en "
                            "TIPOS_TRABAJO): rige la regla anterior, solo para ensayo y monografía")
    modulo_ruta = next((c / "tipos_trabajo.py" for c in (ruta.parent, base)
                        if (c / "tipos_trabajo.py").is_file()), None)
    if modulo_ruta is None:
        return None, None, f"falta tipos_trabajo.py junto a {ruta}: rige la regla anterior"
    spec = importlib.util.spec_from_file_location("tipos_trabajo", modulo_ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo, ruta, None


# ---------------------------------------------------------------------------
# Utilidades XML

def es_verdadero(nodo):
    """Interruptor OOXML (w:b, w:keepNext...) presente y no desactivado."""
    if nodo is None:
        return None
    return nodo.get(qn("w:val"), "true").lower() not in ("0", "false", "off", "none")


def texto_de(elemento):
    partes = []
    for nodo in elemento.iter(qn("w:t"), qn("w:tab")):
        partes.append(nodo.text or "" if nodo.tag == qn("w:t") else " ")
    return "".join(partes)


def resumen(parrafo):
    palabras = parrafo["texto"].split()
    corto = " ".join(palabras[:8])
    if len(corto) > 60:
        corto = corto[:57] + "..."
    if not palabras:
        return f"§{parrafo['n']} (vacío)"
    return f"§{parrafo['n']} «{corto}{'…' if len(palabras) > 8 else ''}»"


class Resolutor:
    """Resuelve propiedades efectivas siguiendo la herencia de estilos."""

    def __init__(self, documento, paquete):
        raiz = documento.styles.element
        self.estilos = {e.get(qn("w:styleId")): e for e in raiz.findall(qn("w:style"))}
        self.defecto = {}
        for estilo in raiz.findall(qn("w:style")):
            if es_verdadero(estilo.find(qn("w:default"))) or estilo.get(qn("w:default")) in ("1", "true"):
                self.defecto.setdefault(estilo.get(qn("w:type")), estilo.get(qn("w:styleId")))
        defectos = raiz.find(qn("w:docDefaults"))
        self.ppr_defecto = self.rpr_defecto = None
        if defectos is not None:
            nodo = defectos.find(qn("w:pPrDefault"))
            self.ppr_defecto = nodo.find(qn("w:pPr")) if nodo is not None else None
            nodo = defectos.find(qn("w:rPrDefault"))
            self.rpr_defecto = nodo.find(qn("w:rPr")) if nodo is not None else None
        self.tema = {}
        for nombre in paquete.namelist():
            if nombre.startswith("word/theme/") and nombre.endswith(".xml"):
                xml = paquete.read(nombre).decode("utf-8", "replace")
                for clase in ("major", "minor"):
                    hallado = re.search(rf"<a:{clase}Font>\s*<a:latin typeface=\"([^\"]*)\"", xml)
                    if hallado:
                        self.tema[clase] = hallado.group(1)
                break

    def cadena(self, estilo_id, tipo="paragraph"):
        """Elementos de estilo desde el propio hasta la raíz de basedOn."""
        if estilo_id is None:
            estilo_id = self.defecto.get(tipo)
        resultado, vistos = [], set()
        while estilo_id and estilo_id in self.estilos and estilo_id not in vistos:
            vistos.add(estilo_id)
            estilo = self.estilos[estilo_id]
            resultado.append(estilo)
            base = estilo.find(qn("w:basedOn"))
            estilo_id = base.get(qn("w:val")) if base is not None else None
        return resultado

    def nombre(self, estilo_id):
        estilo = self.estilos.get(estilo_id or self.defecto.get("paragraph"))
        if estilo is None:
            return estilo_id or ""
        nodo = estilo.find(qn("w:name"))
        return nodo.get(qn("w:val")) if nodo is not None else estilo_id

    def niveles_ppr(self, p, tabla_estilo):
        ppr = p.find(qn("w:pPr"))
        estilo = None
        if ppr is not None and ppr.find(qn("w:pStyle")) is not None:
            estilo = ppr.find(qn("w:pStyle")).get(qn("w:val"))
        lista = [ppr]
        lista += [e.find(qn("w:pPr")) for e in self.cadena(estilo)]
        if tabla_estilo is not None:
            lista += [e.find(qn("w:pPr")) for e in self.cadena(tabla_estilo, "table")]
        lista.append(self.ppr_defecto)
        return [n for n in lista if n is not None], estilo

    def niveles_rpr(self, r, p_estilo, tabla_estilo):
        rpr = r.find(qn("w:rPr"))
        lista = [rpr]
        if rpr is not None and rpr.find(qn("w:rStyle")) is not None:
            lista += [e.find(qn("w:rPr")) for e in self.cadena(
                rpr.find(qn("w:rStyle")).get(qn("w:val")), "character")]
        lista += [e.find(qn("w:rPr")) for e in self.cadena(p_estilo)]
        if tabla_estilo is not None:
            lista += [e.find(qn("w:rPr")) for e in self.cadena(tabla_estilo, "table")]
        lista.append(self.rpr_defecto)
        return [n for n in lista if n is not None]

    @staticmethod
    def atributo(niveles, etiqueta, *atributos):
        """Primer valor de cualquiera de `atributos` en `etiqueta`, con su atributo."""
        for nivel in niveles:
            nodo = nivel.find(qn(etiqueta))
            if nodo is None:
                continue
            for atributo in atributos:
                valor = nodo.get(qn(atributo))
                if valor is not None:
                    return atributo, valor, nodo
        return None, None, None

    @staticmethod
    def interruptor(niveles, etiqueta):
        for nivel in niveles:
            valor = es_verdadero(nivel.find(qn(etiqueta)))
            if valor is not None:
                return valor
        return False

    def fuente(self, niveles):
        for nivel in niveles:
            nodo = nivel.find(qn("w:rFonts"))
            if nodo is None:
                continue
            tema = nodo.get(qn("w:asciiTheme")) or nodo.get(qn("w:hAnsiTheme"))
            if tema:
                return self.tema.get("major" if tema.startswith("major") else "minor", f"tema:{tema}")
            directa = nodo.get(qn("w:ascii")) or nodo.get(qn("w:hAnsi"))
            if directa:
                return directa
        return "Times New Roman"  # valor de Word sin ninguna definición

    def tamano(self, niveles):
        _, valor, _ = self.atributo(niveles, "w:sz", "w:val")
        return float(valor) / 2 if valor else 10.0


# ---------------------------------------------------------------------------
# Análisis del documento

def analizar(documento, resolutor):
    """Lista de párrafos del cuerpo (también en tablas) con sus propiedades."""
    cuerpo = documento.element.body
    parrafos = []
    for numero, p in enumerate(cuerpo.iter(qn("w:p")), start=1):
        tabla = None
        ancestro = p.getparent()
        while ancestro is not None and ancestro is not cuerpo:
            if ancestro.tag == qn("w:tbl"):
                tabla = ancestro
                break
            ancestro = ancestro.getparent()
        tabla_estilo = None
        if tabla is not None:
            tbl_pr = tabla.find(qn("w:tblPr"))
            nodo = tbl_pr.find(qn("w:tblStyle")) if tbl_pr is not None else None
            tabla_estilo = nodo.get(qn("w:val")) if nodo is not None else resolutor.defecto.get("table")
        niveles, estilo = resolutor.niveles_ppr(p, tabla_estilo)
        nombre = resolutor.nombre(estilo)
        # Título real: estilo integrado "heading N" (Word guarda ese nombre
        # en inglés aunque la interfaz diga "Título N"). Un estilo propio
        # con nivel de esquema también es título, pero se marca.
        nivel, personalizado = None, False
        hallado = re.match(r"^heading\s*([1-9])$", nombre.strip(), re.I)
        if hallado:
            nivel = int(hallado.group(1))
        else:
            _, valor, _ = Resolutor.atributo(niveles, "w:outlineLvl", "w:val")
            if valor is not None and valor.isdigit() and int(valor) < 9:
                nivel, personalizado = int(valor) + 1, True
        tabulaciones = [t for nivel_ppr in niveles[:1] for t in nivel_ppr.iter(qn("w:tab"))
                        if t.get(qn("w:val")) in ("right", "end") and t.get(qn("w:leader"))
                        not in (None, "none")]
        texto = texto_de(p)
        runs = []
        for r in p.iter(qn("w:r")):
            texto_run = "".join(t.text or "" for t in r.findall(qn("w:t")))
            if not texto_run.strip():
                continue
            rniveles = resolutor.niveles_rpr(r, estilo, tabla_estilo)
            runs.append({"texto": texto_run, "fuente": resolutor.fuente(rniveles),
                         "tamano": resolutor.tamano(rniveles),
                         "negrita": Resolutor.interruptor(rniveles, "w:b")})
        saltos = sum(1 for br in p.iter(qn("w:br")) if br.get(qn("w:type")) == "page")
        ppr = p.find(qn("w:pPr"))
        seccion = ppr.find(qn("w:sectPr")) if ppr is not None else None
        tipo_seccion = None
        if seccion is not None:
            nodo = seccion.find(qn("w:type"))
            tipo_seccion = nodo.get(qn("w:val")) if nodo is not None else "nextPage"
        _, linea, nodo_linea = Resolutor.atributo(niveles, "w:spacing", "w:line")
        regla = nodo_linea.get(qn("w:lineRule"), "auto") if nodo_linea is not None else "auto"
        _, antes, nodo_antes = Resolutor.atributo(niveles, "w:spacing", "w:before", "w:beforeAutospacing")
        _, despues, _ = Resolutor.atributo(niveles, "w:spacing", "w:after", "w:afterAutospacing")
        if nodo_antes is not None and nodo_antes.get(qn("w:beforeAutospacing")) in ("1", "true"):
            antes = "auto"
        clave, valor, _ = Resolutor.atributo(niveles, "w:ind", "w:firstLine", "w:hanging")
        primera = 0
        if valor is not None:
            primera = int(float(valor)) * (-1 if clave == "w:hanging" else 1)
        _, izquierda, _ = Resolutor.atributo(niveles, "w:ind", "w:left", "w:start")
        _, alineacion, _ = Resolutor.atributo(niveles, "w:jc", "w:val")
        num_id = None
        for nivel_ppr in niveles:
            num_pr = nivel_ppr.find(qn("w:numPr"))
            if num_pr is not None and num_pr.find(qn("w:numId")) is not None:
                num_id = num_pr.find(qn("w:numId")).get(qn("w:val"))
                break
        parrafos.append({
            "n": numero, "p": p, "texto": texto.strip(), "estilo": nombre,
            "nivel": nivel, "personalizado": personalizado,
            "en_tabla": tabla is not None, "runs": runs,
            "indice": nombre.lower().startswith("toc") or (
                bool(tabulaciones) and re.search(r"\d+\s*$", texto.strip()) is not None),
            "pagina_renderizada": any(True for _ in p.iter(qn("w:lastRenderedPageBreak"))),
            "estilo_titulo": re.search(r"t[ií]tulo|heading|title", nombre, re.I) is not None,
            "saltos": saltos, "salto_antes": Resolutor.interruptor(niveles, "w:pageBreakBefore"),
            "seccion": tipo_seccion,
            "linea": (int(float(linea)) if linea else 240, regla),
            "antes": antes if antes == "auto" else int(float(antes or 0)),
            "despues": despues if despues in ("auto",) else int(float(despues or 0)),
            "primera": primera, "izquierda": int(float(izquierda or 0)),
            "alineacion": alineacion or "left",
            "lista": (num_id not in (None, "0")) or nombre.lower().startswith("list"),
            "dibujo": any(True for _ in p.iter(qn("w:drawing"))) or any(True for _ in p.iter(qn("w:pict"))),
            "tras_tabla": (p.getprevious() is not None and p.getprevious().tag == qn("w:tbl")),
        })
    return parrafos


def zona_portada(parrafos):
    """(fin, explícita): índice exclusivo del final de la portada y si
    termina en un salto real. (0, True) si no hay portada.

    Portada = párrafos anteriores al primer salto de página o de sección,
    si ese salto llega antes de cualquier título y dentro de los primeros
    40 párrafos. Si no hay salto pero Word dejó la marca de página
    renderizada (lastRenderedPageBreak) antes del primer título, la
    portada termina ahí y se separa con relleno: explícita = False.
    """
    for i, parrafo in enumerate(parrafos[:40]):
        if parrafo["salto_antes"] and i > 0:
            return i, True
        if parrafo["nivel"] is not None:
            break
        if parrafo["saltos"] or parrafo["seccion"] in ("nextPage", "oddPage", "evenPage"):
            return i + 1, True
    for i, parrafo in enumerate(parrafos[:40]):
        if parrafo["nivel"] is not None:
            break
        if i > 0 and parrafo["pagina_renderizada"] and any(p["texto"] for p in parrafos[:i]):
            return i, False
    return 0, True


def zona_referencias(parrafos):
    """(índice del encabezado, [índices de entradas]) o (None, [])."""
    inicio = None
    for i, parrafo in enumerate(parrafos):
        if parrafo["texto"] and comun.es_encabezado_referencias(parrafo["texto"]) \
                and (parrafo["nivel"] is not None or all(r["negrita"] for r in parrafo["runs"])):
            inicio = i
    if inicio is None:
        return None, []
    entradas = []
    for i in range(inicio + 1, len(parrafos)):
        parrafo = parrafos[i]
        if parrafo["nivel"] is not None:
            break
        if parrafo["texto"] and not parrafo["en_tabla"]:
            entradas.append(i)
    return inicio, entradas


# ---------------------------------------------------------------------------
# Comprobaciones

class Informe:
    def __init__(self):
        self.hallazgos = []

    def agregar(self, clave, nivel, mensaje, lugares=()):
        lugares = list(lugares)
        self.hallazgos.append({
            "comprobacion": clave, "nombre": NOMBRES[clave], "nivel": nivel,
            "mensaje": mensaje, "lugares": lugares[:MAX_LUGARES],
            "total_lugares": len(lugares)})

    def cerrar(self, clave, nota_ok="sin hallazgos"):
        if not any(h["comprobacion"] == clave for h in self.hallazgos):
            self.agregar(clave, "OK", nota_ok)


def comprobar_pagina(documento, informe):
    for numero, seccion in enumerate(documento.sections, start=1):
        sect = seccion._sectPr
        tamano = sect.find(qn("w:pgSz"))
        ancho = int(tamano.get(qn("w:w"), 0)) if tamano is not None else 0
        alto = int(tamano.get(qn("w:h"), 0)) if tamano is not None else 0
        if abs(ancho - CARTA[0]) > TOLERANCIA_PAGINA or abs(alto - CARTA[1]) > TOLERANCIA_PAGINA:
            informe.agregar("b", "ERROR", f"sección {numero}: página de {ancho / TWIP_CM:.2f} × "
                            f"{alto / TWIP_CM:.2f} cm, no carta (21,59 × 27,94)")
        margenes = sect.find(qn("w:pgMar"))
        if margenes is not None:
            valores = {lado: int(float(margenes.get(qn(f"w:{lado}"), 0)))
                       for lado in ("top", "bottom", "left", "right")}
            raros = {k: v for k, v in valores.items() if abs(v - MARGEN_UAP) > 30}
            if raros:
                detalle = ", ".join(f"{k} {v / TWIP_CM:.2f} cm" for k, v in raros.items())
                nivel = "ERROR" if any(v < 1.9 * TWIP_CM or v > 4 * TWIP_CM for v in raros.values()) else "AVISO"
                informe.agregar("b", nivel, f"sección {numero}: márgenes distintos de 2,54 cm ({detalle})")
    informe.cerrar("b", "carta y márgenes de 2,54 cm")


def comprobar_tipografia(parrafos, portada_fin, informe):
    fuentes, tamanos_cuerpo, tamanos_secundarios = [], [], []
    por_nivel = defaultdict(lambda: defaultdict(list))
    for i, parrafo in enumerate(parrafos):
        for run in parrafo["runs"]:
            if run["fuente"].strip().lower() != FUENTE:
                fuentes.append((run["fuente"], resumen(parrafo)))
            if parrafo["nivel"] is not None:
                por_nivel[parrafo["nivel"]][run["tamano"]].append(resumen(parrafo))
            elif abs(run["tamano"] - TAMANO) > 0.01:
                secundario = parrafo["en_tabla"] or i < portada_fin or parrafo.get("clase") in ("leyenda", "formula")
                destino = tamanos_secundarios if secundario else tamanos_cuerpo
                destino.append((run["tamano"], resumen(parrafo)))
    if fuentes:
        agrupadas = Counter(f for f, _ in fuentes)
        lugares = list(dict.fromkeys(lugar for _, lugar in fuentes))
        informe.agregar("c", "ERROR", "texto que no está en Calibri: " +
                        ", ".join(f"{f} ({n} fragmentos)" for f, n in agrupadas.items()), lugares)
    if tamanos_cuerpo:
        lugares = list(dict.fromkeys(lugar for _, lugar in tamanos_cuerpo))
        valores = sorted({t for t, _ in tamanos_cuerpo})
        informe.agregar("c", "ERROR", f"texto en tamaño distinto de 11 pt: {valores}", lugares)
    if tamanos_secundarios:
        lugares = list(dict.fromkeys(lugar for _, lugar in tamanos_secundarios))
        valores = sorted({t for t, _ in tamanos_secundarios})
        informe.agregar("c", "AVISO", f"tablas, portada o pies de figura en tamaño distinto de 11 pt: {valores}", lugares)
    for nivel, tamanos in sorted(por_nivel.items()):
        if len(tamanos) > 1:
            mayoritario = max(tamanos, key=lambda t: len(tamanos[t]))
            lugares = [l for t, ls in tamanos.items() if t != mayoritario for l in ls]
            informe.agregar("c", "ERROR", f"títulos de nivel {nivel} con tamaños distintos: "
                            f"{sorted(tamanos)} pt (lo más común: {mayoritario})", list(dict.fromkeys(lugares)))
        else:
            tamano = next(iter(tamanos))
            if abs(tamano - TAMANO) > 0.01:
                informe.agregar("c", "AVISO", f"títulos de nivel {nivel} en {tamano:g} pt "
                                "(uniforme; la norma pide Calibri 11 en todo)")
    informe.cerrar("c", "todo el texto en Calibri 11")


def clasificar(parrafos, portada_fin, refs_indices):
    """Asigna a cada párrafo una clase: vacio, portada, titulo, tabla,
    referencia, leyenda, figura, lista, cita, cuerpo."""
    refs = set(refs_indices)
    for i, parrafo in enumerate(parrafos):
        texto = parrafo["texto"]
        if not texto and not parrafo["dibujo"]:
            clase = "vacio"
        elif i < portada_fin:
            clase = "portada"
        elif parrafo["nivel"] is not None:
            clase = "titulo"
        elif parrafo["indice"]:
            clase = "indice"
        elif parrafo["estilo_titulo"] and not parrafo["en_tabla"]:
            clase = "titulo_sin_nivel"
        elif parrafo["en_tabla"]:
            clase = "tabla"
        elif i in refs:
            clase = "referencia"
        elif parrafo["dibujo"]:
            clase = "figura"
        elif re.match(r"^(Tabla|Figura|Gráfico|Cuadro|Mapa)\s*\d+", texto) or \
                re.match(r"^(Nota|Fuente)[.:]", texto) or parrafo["estilo"].lower() == "caption" or \
                re.match(r"^Elaboraci[oó]n propia", texto):
            clase = "leyenda"
        elif (i > 0 and parrafos[i - 1].get("clase") == "leyenda" and len(texto.split()) <= 50
              and parrafo["primera"] <= 0.1 * TWIP_CM):
            # Línea de fuente o nota pegada al pie de una tabla o figura.
            clase = "leyenda"
        elif (parrafo["alineacion"] == "center" and len(texto.split()) <= 25
              and re.search(r"[=→⇌⟶+]", texto)):
            clase = "formula"
        elif parrafo["lista"]:
            clase = "lista"
        elif parrafo["izquierda"] >= 0.9 * TWIP_CM and parrafo["primera"] <= 0.1 * TWIP_CM:
            clase = "cita"
        else:
            clase = "cuerpo"
        parrafo["clase"] = clase


def titulo_falso(parrafo):
    """Párrafo corto, todo en negrita, sin estilo de título."""
    if parrafo["clase"] not in ("cuerpo", "cita") or not parrafo["runs"]:
        return False
    texto = parrafo["texto"]
    return (all(r["negrita"] for r in parrafo["runs"]) and len(texto.split()) <= 15
            and len(texto) <= 120 and not texto.endswith((".", ";", ",")))


def comprobar_parrafos(parrafos, informe):
    """d) interlineado, e) alineación, f) títulos, g) espaciado."""
    linea_mal, linea_aviso = [], []
    alineacion_cuerpo, sangria_cuerpo, titulos_mal = [], [], []
    for parrafo in parrafos:
        clase = parrafo["clase"]
        if clase == "vacio":
            continue
        valor, regla = parrafo["linea"]
        if regla != "auto" or not (LINEA_115[0] <= valor <= LINEA_115[1]):
            descripcion = f"{valor / 240:.2f}" if regla == "auto" else f"{regla} {valor / 20:g} pt"
            (linea_aviso if clase in ("tabla", "portada", "figura") else linea_mal).append(
                f"{resumen(parrafo)}: {descripcion}")
        if clase == "cuerpo" and not titulo_falso(parrafo):
            if parrafo["alineacion"] not in ("both", "distribute"):
                alineacion_cuerpo.append(f"{resumen(parrafo)}: {parrafo['alineacion']}")
            if parrafo["primera"] <= 0.1 * TWIP_CM:
                sangria_cuerpo.append(resumen(parrafo))
        if clase == "titulo":
            if parrafo["alineacion"] not in ("left", "start", "both"):
                titulos_mal.append(f"{resumen(parrafo)}: alineado {parrafo['alineacion']}")
            elif parrafo["primera"] > 0.1 * TWIP_CM or parrafo["izquierda"] > 0.1 * TWIP_CM:
                titulos_mal.append(f"{resumen(parrafo)}: con sangría")
    if linea_mal:
        informe.agregar("d", "ERROR", "interlineado distinto de 1,15", linea_mal)
    if linea_aviso:
        informe.agregar("d", "AVISO", "interlineado distinto de 1,15 en tablas, figuras o portada", linea_aviso)
    informe.cerrar("d", "1,15 en todo el texto")
    if alineacion_cuerpo:
        informe.agregar("e", "ERROR", "párrafos de cuerpo sin justificar", alineacion_cuerpo)
    if sangria_cuerpo:
        informe.agregar("e", "ERROR", "párrafos de cuerpo sin sangría de primera línea", sangria_cuerpo)
    if titulos_mal:
        informe.agregar("e", "ERROR", "títulos que no están a la izquierda sin sangría", titulos_mal)
    informe.cerrar("e", "cuerpo justificado con sangría; títulos a la izquierda")

    # f) títulos reales y jerarquía
    falsos = [resumen(p) for p in parrafos if titulo_falso(p)]
    if falsos:
        informe.agregar("f", "ERROR", "títulos falsos: párrafo corto en negrita sin estilo "
                        "Título 1/2/3", falsos)
    sin_nivel = [f"{resumen(p)}: estilo «{p['estilo']}»" for p in parrafos
                 if p["clase"] == "titulo_sin_nivel"]
    if sin_nivel:
        informe.agregar("f", "AVISO", "párrafos con estilo de título que no es título (sin nivel "
                        "de esquema: no salen en el índice ni en el panel de navegación)", sin_nivel)
    propios = Counter(p["estilo"] for p in parrafos if p["clase"] == "titulo" and p["personalizado"])
    if propios:
        informe.agregar("f", "AVISO", "títulos con estilos propios con nivel de esquema, no los "
                        "integrados Título 1/2/3: " + ", ".join(f"«{e}» ({n})" for e, n in propios.items()))
    anterior, saltos_jerarquia = 1, []
    titulos = [p for p in parrafos if p["clase"] == "titulo"]
    for parrafo in titulos:
        if parrafo["nivel"] - anterior > 1:
            saltos_jerarquia.append(f"{resumen(parrafo)}: nivel {parrafo['nivel']} tras nivel {anterior}")
        anterior = parrafo["nivel"]
    if saltos_jerarquia:
        informe.agregar("f", "ERROR", "jerarquía de títulos con saltos", saltos_jerarquia)
    if not titulos:
        informe.agregar("f", "AVISO", "el documento no usa ningún estilo de título")
    informe.cerrar("f", f"{len(titulos)} títulos con estilos reales; jerarquía sin saltos")

    # g) espaciado
    por_nivel = defaultdict(lambda: defaultdict(list))
    for parrafo in titulos:
        por_nivel[parrafo["nivel"]][(parrafo["antes"], parrafo["despues"])].append(resumen(parrafo))
    for nivel, valores in sorted(por_nivel.items()):
        if len(valores) > 1:
            mayoritario = max(valores, key=lambda v: len(valores[v]))
            lugares = [f"{l}: antes {fmt_pt(v[0])}, después {fmt_pt(v[1])}"
                       for v, ls in valores.items() if v != mayoritario for l in ls]
            informe.agregar("g", "ERROR", f"espaciado desigual en títulos de nivel {nivel} "
                            f"(lo común: antes {fmt_pt(mayoritario[0])}, después "
                            f"{fmt_pt(mayoritario[1])})", lugares)
    # El primer párrafo tras una tabla, figura o nota puede llevar aire
    # propio; no cuenta para la uniformidad del cuerpo.
    cuerpo = defaultdict(list)
    previa = None
    for parrafo in parrafos:
        if parrafo["clase"] == "vacio" or parrafo["en_tabla"]:
            continue
        tras_bloque = parrafo["tras_tabla"] or previa in ("leyenda", "figura", "formula")
        if parrafo["clase"] == "cuerpo" and not tras_bloque and not titulo_falso(parrafo) \
                and parrafo["primera"] > 0.1 * TWIP_CM:
            cuerpo[(parrafo["antes"], parrafo["despues"])].append(resumen(parrafo))
        previa = parrafo["clase"]
    if len(cuerpo) > 1:
        mayoritario = max(cuerpo, key=lambda v: len(cuerpo[v]))
        lugares = [f"{l}: antes {fmt_pt(v[0])}, después {fmt_pt(v[1])}"
                   for v, ls in cuerpo.items() if v != mayoritario for l in ls]
        informe.agregar("g", "AVISO", "párrafos de cuerpo con espaciado distinto del común "
                        f"(antes {fmt_pt(mayoritario[0])}, después {fmt_pt(mayoritario[1])})", lugares)
    resumen_niveles = "; ".join(
        f"nivel {n}: antes {fmt_pt(next(iter(v))[0])}, después {fmt_pt(next(iter(v))[1])}"
        for n, v in sorted(por_nivel.items()) if len(v) == 1)
    informe.cerrar("g", f"uniforme ({resumen_niveles})" if resumen_niveles else "sin hallazgos")


def fmt_pt(valor):
    return "auto" if valor == "auto" else f"{valor / 20:g} pt"


def comprobar_saltos(parrafos, portada_fin, informe, portada_explicita=True):
    escondidos, otros, estructurales = [], [], []
    if portada_fin and not portada_explicita:
        informe.agregar("h", "AVISO", "la portada no termina en un salto de página: la página "
                        "siguiente empieza por relleno (párrafos vacíos)",
                        [resumen(parrafos[portada_fin])])
    for i, parrafo in enumerate(parrafos):
        texto = parrafo["texto"]
        if parrafo["saltos"]:
            if texto:
                escondidos.append(f"{resumen(parrafo)}: {parrafo['saltos']} salto(s) dentro del párrafo")
            elif portada_fin and i == portada_fin - 1:
                estructurales.append(f"{resumen(parrafo)}: fin de portada")
            else:
                otros.append(f"{resumen(parrafo)}: salto de página en párrafo propio")
        if parrafo["salto_antes"]:
            if portada_fin and i == portada_fin:
                estructurales.append(f"{resumen(parrafo)}: salto antes (fin de portada)")
            else:
                otros.append(f"{resumen(parrafo)}: «salto de página anterior»")
        if parrafo["seccion"] in ("nextPage", "oddPage", "evenPage"):
            if portada_fin and i == portada_fin - 1:
                estructurales.append(f"{resumen(parrafo)}: salto de sección (fin de portada)")
            else:
                otros.append(f"{resumen(parrafo)}: salto de sección ({parrafo['seccion']})")
    if escondidos:
        informe.agregar("h", "ERROR", "saltos de página escondidos en párrafos con texto", escondidos)
    if otros:
        informe.agregar("h", "AVISO", f"{len(otros)} salto(s) no estructurales: comprobar que "
                        "cada uno haga falta", otros)
    informe.cerrar("h", f"{len(estructurales)} salto estructural (portada)" if estructurales
                   else "sin saltos forzados")


def comprobar_vacios(parrafos, portada_fin, informe):
    grupos, actual = [], []
    for i, parrafo in enumerate(parrafos):
        vacio = (parrafo["clase"] == "vacio" and not parrafo["saltos"] and not parrafo["seccion"]
                 and not parrafo["en_tabla"])
        if vacio:
            actual.append(i)
        else:
            if len(actual) >= 2:
                grupos.append(actual)
            actual = []
    if len(actual) >= 2:
        grupos.append(actual)
    if grupos:
        lugares = [f"§{parrafos[g[0]]['n']}–§{parrafos[g[-1]]['n']} ({len(g)} vacíos"
                   f"{', portada' if g[0] < portada_fin else ''})" for g in grupos]
        informe.agregar("i", "AVISO", "párrafos vacíos seguidos usados como espaciado", lugares)
    informe.cerrar("i")


PALABRAS_ROMANO = ("siglo", "capitulo", "articulo", "tomo", "volumen", "congreso",
                   "reunion", "edicion", "encuentro", "legislatura", "jornadas", "seminario")


def marcadores(texto, en_cita=False):
    """Lista de (nivel, descripción) de marcadores prohibidos en un texto."""
    hallados = []
    reglas = [
        (r"\bpor\s+verificar\b", re.I, "«por verificar»"),
        (r"\bpor\s+completar\b", re.I, "«por completar»"),
        (r"[\[\(]\s*(pendiente|completar)[^\]\)]*[\]\)]", re.I, "marcador entre corchetes/paréntesis"),
        (r"\b(pendiente|completar)\s*:", re.I, "marcador seguido de dos puntos"),
        (r"\[\s*(cita|citation|fuente|referencia|ref)\b[^\]]*\]", re.I, "«[cita]»"),
        (r"\blorem\s+ipsum\b", re.I, "«lorem ipsum»"),
        (r"\[\s*\]", 0, "corchetes vacíos"),
        (r"¿\s*\?", 0, "«¿?» suelto"),
        (r"\?\?+", 0, "«??»"),
    ]
    for patron, banderas, descripcion in reglas:
        for hallado in re.finditer(patron, texto, banderas):
            if comun.normalizar(hallado.group(0)) in comun.normalizar(descripcion):
                hallados.append(("ERROR", descripcion))
            else:
                hallados.append(("ERROR", f"{descripcion}: «{hallado.group(0)}»"))
    for hallado in re.finditer(r"\b(?:TODO|PENDIENTE|COMPLETAR)\b(:?)", texto):
        antes = re.findall(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü]+", texto[:hallado.start()])
        despues = re.findall(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü]+", texto[hallado.end():])
        vecinas = ([antes[-1]] if antes else []) + ([despues[0]] if despues else [])
        if hallado.group(1) or not any(v.isupper() and len(v) > 1 for v in vecinas):
            hallados.append(("ERROR", f"«{hallado.group(0).rstrip(':')}» de marcador"))
    for hallado in re.finditer(r"\bX{3,}\b", texto):
        previa = re.findall(r"\w+", texto[:hallado.start()])
        siguiente = re.findall(r"\w+", texto[hallado.end():])
        contexto = {comun.normalizar(w) for w in (previa[-1:] + siguiente[:1])}
        if len(hallado.group(0)) > 3 or not contexto & set(PALABRAS_ROMANO):
            hallados.append(("ERROR", f"«{hallado.group(0)}» de relleno"))
    for hallado in re.finditer(r"\[\s*(\.\.\.|…)\s*\]", texto):
        resto = (texto[:hallado.start()] + texto[hallado.end():]).split()
        if len(resto) < 4:
            hallados.append(("ERROR", "«[...]» de relleno"))
        elif not en_cita and not dentro_de_comillas(texto, hallado.start()):
            hallados.append(("AVISO", "«[...]» fuera de una cita: comprobar que sea una elisión"))
    return hallados


def dentro_de_comillas(texto, posicion):
    previo = texto[:posicion]
    for abre, cierra in (("“", "”"), ("«", "»"), ("‘", "’")):
        if previo.count(abre) > previo.count(cierra):
            return True
    return previo.count('"') % 2 == 1


def textos_secundarios(paquete):
    """Texto de notas al pie, notas finales, encabezados y pies: [(lugar, texto)]."""
    resultado = []
    for nombre in paquete.namelist():
        hallado = re.match(r"word/(footnotes|endnotes|header\d*|footer\d*)\.xml$", nombre)
        if not hallado:
            continue
        xml = paquete.read(nombre).decode("utf-8", "replace")
        for numero, parrafo in enumerate(re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S), start=1):
            texto = "".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", parrafo, flags=re.S))
            texto = (texto.replace("&lt;", "<").replace("&gt;", ">")
                     .replace("&quot;", '"').replace("&amp;", "&")).strip()
            if texto:
                resultado.append((f"{hallado.group(1)} ¶{numero} «{' '.join(texto.split()[:8])}»", texto))
    return resultado


def comprobar_marcadores(parrafos, secundarios, informe):
    por_nivel = defaultdict(list)
    lugares = [(resumen(p), p["texto"], p["clase"] == "cita") for p in parrafos if p["texto"]]
    lugares += [(lugar, texto, False) for lugar, texto in secundarios]
    for lugar, texto, en_cita in lugares:
        for nivel, descripcion in marcadores(texto, en_cita):
            por_nivel[nivel].append(f"{lugar}: {descripcion}")
    if por_nivel["ERROR"]:
        informe.agregar("j", "ERROR", "marcadores prohibidos", por_nivel["ERROR"])
    if por_nivel["AVISO"]:
        informe.agregar("j", "AVISO", "posibles marcadores", por_nivel["AVISO"])
    informe.cerrar("j")


def comprobar_autonomia(parrafos, refs, secundarios, informe):
    errores, avisos = [], []
    reglas_error = [
        (r"\bv\d+(\.\d+)?\b", re.I, "número de versión"),
        (r"\bversi[oó]n\s+(corregida|anterior|nueva|final|previa)\b", re.I, "mención a versiones"),
        (r"\bcambios\s+(realizados|respecto|introducidos|aplicados)\b", re.I, "notas de cambios"),
        (r"\b[\w\-]+\.(docx?|md|py|js|xlsx|pptx|txt|json)\b", re.I, "nombre de archivo"),
    ]
    reglas_aviso = [
        (r"\bversi[oó]n\s+\d+\b", re.I, "«versión N»: comprobar que no hable del propio trabajo"),
        (r"\bcorregid[oa]s?\b", re.I, "«corregido»: comprobar que no hable del propio trabajo"),
        (r"\bqu[Éé]\s+cambi[oó]\b", re.I, "«qué cambió»: comprobar que no hable del propio trabajo"),
        (r"\bborrador\b", re.I, "«borrador»: comprobar que no hable del propio trabajo"),
    ]
    candidatos = [(resumen(p), p["texto"]) for i, p in enumerate(parrafos)
                  if p["texto"] and i not in refs]
    candidatos += secundarios
    for lugar, texto in candidatos:
        sin_urls = re.sub(r"(https?://|www\.)\S+", " ", texto)
        for patron, banderas, descripcion in reglas_error:
            for hallado in re.finditer(patron, sin_urls, banderas):
                errores.append(f"{lugar}: {descripcion} «{hallado.group(0)}»")
        for patron, banderas, descripcion in reglas_aviso:
            for hallado in re.finditer(patron, sin_urls, banderas):
                avisos.append(f"{lugar}: {descripcion} «{hallado.group(0)}»")
    if errores:
        informe.agregar("k", "ERROR", "el entregable no es autónomo", errores)
    if avisos:
        informe.agregar("k", "AVISO", "posibles menciones al proceso", avisos)
    informe.cerrar("k")


def comprobar_referencias(parrafos, inicio, entradas, informe):
    if inicio is None:
        informe.agregar("l", "AVISO", "no se encontró la sección de referencias")
        return
    sin_francesa, vinetas, alineadas = [], [], []
    for i in entradas:
        parrafo = parrafos[i]
        if parrafo["lista"] or re.match(r"^([-•·*▪–]|\d+[.)])\s", parrafo["texto"]):
            vinetas.append(resumen(parrafo))
        if parrafo["primera"] > -0.5 * TWIP_CM or parrafo["izquierda"] < 0.5 * TWIP_CM:
            sin_francesa.append(f"{resumen(parrafo)}: primera línea {parrafo['primera'] / TWIP_CM:.2f} cm, "
                                f"izquierda {parrafo['izquierda'] / TWIP_CM:.2f} cm")
        if parrafo["alineacion"] not in ("left", "start", "both"):
            alineadas.append(f"{resumen(parrafo)}: {parrafo['alineacion']}")
    if sin_francesa:
        informe.agregar("l", "ERROR", "referencias sin sangría francesa", sin_francesa)
    if vinetas:
        informe.agregar("l", "ERROR", "referencias con viñetas o numeración", vinetas)
    if alineadas:
        informe.agregar("l", "ERROR", "referencias centradas o a la derecha", alineadas)
    claves = [comun.normalizar(parrafos[i]["texto"]) for i in entradas]
    desordenadas = [f"{resumen(parrafos[entradas[k + 1]])} va después de "
                    f"{resumen(parrafos[entradas[k]])}"
                    for k in range(len(claves) - 1) if claves[k] > claves[k + 1]]
    if desordenadas:
        informe.agregar("l", "ERROR", "referencias fuera de orden alfabético", desordenadas)
    if not entradas:
        informe.agregar("l", "ERROR", "la sección de referencias está vacía")
    informe.cerrar("l", f"{len(entradas)} referencias con sangría francesa y en orden")


def comprobar_markdown(parrafos, informe):
    errores, avisos = [], []
    reglas = [
        (r"\*\*", "«**»"),
        (r"(?<![\w*])\*[^\s*][^*]{0,200}?\*(?![\w*])", "«*cursiva*» sin convertir"),
        (r"^#{1,6}\s", "«#» de título"),
        (r"\|\s*:?-{3,}", "separador de tabla «|---|»"),
        (r"^\|.*\|.*\|", "fila de tabla sin convertir"),
        (r"!\[[^\]]*\]\([^)]*\)", "imagen Markdown"),
        (r"\[[^\]]+\]\([^)\s]+\)", "enlace Markdown"),
        (r"^>\s", "«>» de cita"),
        (r"\\pagebreak|\\newpage", "salto LaTeX"),
        (r"(?<!\w)__[^_]+__(?!\w)", "«__»"),
    ]
    for parrafo in parrafos:
        texto = parrafo["texto"]
        if not texto:
            continue
        for patron, descripcion in reglas:
            if re.search(patron, texto):
                errores.append(f"{resumen(parrafo)}: {descripcion}")
        if "`" in texto:
            avisos.append(f"{resumen(parrafo)}: acento grave «`»")
        if parrafo["clase"] == "cuerpo" and re.match(r"^[-*+]\s", texto):
            avisos.append(f"{resumen(parrafo)}: viñeta escrita a mano")
    if errores:
        informe.agregar("m", "ERROR", "restos de Markdown sin convertir", errores)
    if avisos:
        informe.agregar("m", "AVISO", "posibles restos de Markdown", avisos)
    informe.cerrar("m")


def comprobar_paginas(ruta, documento, parrafos, refs_inicio, args, informe, portada_fin):
    resultado = {"paginas": None, "paginas_referencias": None}
    seccion = documento.sections[-1]
    margen_sup = (seccion.top_margin or 0) / 360000 if seccion.top_margin else 2.54
    margen_inf = (seccion.bottom_margin or 0) / 360000 if seccion.bottom_margin else 2.54
    siguiente = None
    if refs_inicio is not None:
        for parrafo in parrafos[refs_inicio + 1:]:
            if parrafo["nivel"] is not None and parrafo["texto"]:
                siguiente = parrafo["texto"]
                break
    with tempfile.TemporaryDirectory(prefix="agac_verif_") as temporal:
        try:
            pdf = comun.renderizar_pdf(ruta, temporal)
            paginas = comun.medir_pdf(pdf)
            refs = None
            if refs_inicio is not None:
                refs = comun.paginas_seccion_pdf(
                    pdf, encabezados=(parrafos[refs_inicio]["texto"],),
                    margen_sup_cm=margen_sup, margen_inf_cm=margen_inf, siguiente=siguiente)
        except comun.ErrorRender as error:
            informe.agregar("n", "ERROR", f"páginas no medidas: {error}. No se da por bueno.")
            return resultado
        except ImportError:
            informe.agregar("n", "ERROR", "páginas no medidas: falta PyMuPDF (pip install pymupdf)")
            return resultado
    total = len(paginas)
    resultado.update(paginas=total, paginas_referencias=refs,
                     primera_vacia=not paginas[0]["texto"].strip())
    no_carta = [str(i + 1) for i, p in enumerate(paginas)
                if abs(p["ancho_cm"] - 21.59) > 0.1 or abs(p["alto_cm"] - 27.94) > 0.1]
    if no_carta:
        informe.agregar("n", "ERROR", f"páginas del PDF que no son carta: {', '.join(no_carta[:10])}"
                        f" ({paginas[int(no_carta[0]) - 1]['ancho_cm']} × "
                        f"{paginas[int(no_carta[0]) - 1]['alto_cm']} cm)")
    if args.min_paginas and total < args.min_paginas:
        informe.agregar("n", "ERROR", f"{total} páginas: por debajo del mínimo ({args.min_paginas})")
    if args.max_paginas and total > args.max_paginas:
        informe.agregar("n", "ERROR", f"{total} páginas: por encima del máximo ({args.max_paginas})")
    if refs is not None and args.max_paginas_referencias and refs > args.max_paginas_referencias:
        informe.agregar("n", "ERROR", f"las referencias ocupan {refs} páginas (máximo "
                        f"{args.max_paginas_referencias})")
    if refs_inicio is not None and refs is None:
        informe.agregar("n", "AVISO", "no se pudo ubicar la sección de referencias en el PDF")
    detalle = f"{total} páginas carta" + (f"; referencias {refs} páginas" if refs is not None else "")
    informe.cerrar("n", detalle)
    return resultado


def comprobar_tipo(parrafos, portada_fin, args, medida, informe, tt=None, est=None, aviso=None):
    if aviso:
        informe.agregar("o", "AVISO", aviso)
    if est is None:
        comprobar_tipo_anterior(parrafos, portada_fin, args, medida, informe)
        return
    if not est["secciones"] and est["portada"] == "ninguna" and not args.portada:
        informe.cerrar("o", "no aplica a este tipo")
        return
    portada = args.portada or est["portada"]
    if portada == "blanca":
        if not portada_fin:
            informe.agregar("o", "ERROR", "falta la portada: la primera página debe ir en blanco "
                            "(no hay salto de página antes del primer título)")
        else:
            con_texto = [resumen(p) for p in parrafos[:portada_fin] if p["texto"]]
            if con_texto:
                informe.agregar("o", "ERROR", "la primera página no está en blanco", con_texto)
        if medida.get("primera_vacia") is False and portada_fin and \
                not any(p["texto"] for p in parrafos[:portada_fin]):
            informe.agregar("o", "ERROR", "en el PDF la primera página tiene texto")
    elif portada == "datos":
        if not portada_fin:
            informe.agregar("o", "ERROR", "falta la portada con datos")
        elif not any(p["texto"] for p in parrafos[:portada_fin]):
            informe.agregar("o", "ERROR", "la portada está en blanco: el tipo pide portada con datos")

    titulos = [{"pos": i, "nivel": p["nivel"], "texto": p["texto"]}
               for i, p in enumerate(parrafos) if p["clase"] == "titulo"]
    hallado = tt.buscar_secciones(est, titulos)
    nombres = []
    for fila in hallado["secciones"]:
        seccion = fila["seccion"]
        nombre = seccion["nombre"]
        nombres.append(f"{nombre} ({fila['cantidad']})" if seccion.get("capitulos") else nombre)
        if fila["estado"] == "nivel":
            informe.agregar("o", "ERROR", f"«{nombre}» debe ser título de nivel {seccion['nivel']}; "
                            f"está en nivel {fila['nivel']}", [resumen(parrafos[fila["pos"]])])
        elif fila["estado"] == "falta":
            if seccion.get("capitulos"):
                informe.agregar("o", "ERROR", f"faltan los «{nombre}»: al menos "
                                f"{seccion.get('minimo', 1)} título de nivel 1 «Capítulo I. …»")
                continue
            parecidos = [resumen(p) for p in parrafos
                         if tt.parecido(p["texto"], seccion) and len(p["texto"]) < 150]
            if parecidos:
                solo = " solo" if seccion.get("solo", True) else ""
                informe.agregar("o", "ERROR", f"«{nombre}» no aparece como encabezado{solo} con "
                                "estilo de título", parecidos)
            else:
                informe.agregar("o", "ERROR", f"falta el encabezado «{nombre}»")
    for seccion, titulo, previa, titulo_previo in hallado["fuera_de_orden"]:
        informe.agregar("o", "ERROR", f"«{seccion['nombre']}» está fuera de orden: aparece antes de "
                        f"«{previa['nombre']}» (orden: {tt.orden_esperado(est)})",
                        [resumen(parrafos[titulo["pos"]]), resumen(parrafos[titulo_previo["pos"]])])

    inicio_cuerpo = min((f["pos"] for f in hallado["secciones"] if f["pos"] is not None), default=None)
    candidatos = []
    for i, p in enumerate(parrafos):
        if i < portada_fin or not p["texto"]:
            continue
        toc = any("TOC" in (nodo.text or "") for nodo in p["p"].iter(qn("w:instrText")))
        candidatos.append({"pos": i, "texto": p["texto"], "indice": p["clase"] == "indice" or toc,
                           "titulo": p["clase"] in ("titulo", "titulo_sin_nivel")})
    for clave, previo in tt.buscar_previos(est, candidatos).items():
        if previo["estado"] == "no":
            continue
        if previo["pos"] is None:
            if previo["estado"] != "obligatorio":
                continue
            if clave == "indice":
                informe.agregar("o", "AVISO", "el tipo lleva índice y no se encontró "
                                "(construir_docx.py no lo genera)")
            else:
                informe.agregar("o", "ERROR", f"falta «{previo['nombre']}»: el tipo lo exige "
                                "antes del cuerpo")
        elif clave != "indice" and inicio_cuerpo is not None and previo["pos"] > inicio_cuerpo:
            primera = next(f["seccion"]["nombre"] for f in hallado["secciones"] if f["pos"] == inicio_cuerpo)
            informe.agregar("o", "ERROR", f"«{previo['nombre']}» está fuera de orden: debe ir antes "
                            f"de «{primera}»", [resumen(parrafos[previo["pos"]])])
    variante = f" (variante {est['variante']})" if est["variante"] else ""
    if portada == "ninguna":
        informe.cerrar("o", f"{est['nombre']}{variante}: {tt.lista_nombres(nombres)} presentes")
    else:
        informe.cerrar("o", f"portada {portada} e {tt.lista_nombres(nombres)} presentes{variante}")


def comprobar_tipo_anterior(parrafos, portada_fin, args, medida, informe):
    """Regla anterior a tipos.json: solo ensayo y monografía."""
    if args.tipo not in ("ensayo", "monografia"):
        informe.cerrar("o", "no aplica a este tipo")
        return
    portada = args.portada or "blanca"
    if portada == "blanca":
        if not portada_fin:
            informe.agregar("o", "ERROR", "falta la portada: la primera página debe ir en blanco "
                            "(no hay salto de página antes del primer título)")
        else:
            con_texto = [resumen(p) for p in parrafos[:portada_fin] if p["texto"]]
            if con_texto:
                informe.agregar("o", "ERROR", "la primera página no está en blanco", con_texto)
        if medida.get("primera_vacia") is False and portada_fin and \
                not any(p["texto"] for p in parrafos[:portada_fin]):
            informe.agregar("o", "ERROR", "en el PDF la primera página tiene texto")
    elif portada == "datos" and not portada_fin:
        informe.agregar("o", "ERROR", "falta la portada con datos")
    requeridos = {"introduccion": "Introducción", "desarrollo": "Desarrollo",
                  "conclusiones": "Conclusiones"}
    titulos = {comun.normalizar(p["texto"]): p for p in parrafos if p["clase"] == "titulo"}
    for clave, nombre in requeridos.items():
        presentes = [t for t in titulos if t == clave or (clave == "conclusiones" and t == "conclusion")]
        if presentes:
            continue
        parecidos = [resumen(p) for p in parrafos
                     if comun.normalizar(p["texto"]).startswith(clave[:10]) and len(p["texto"]) < 150]
        if parecidos:
            informe.agregar("o", "ERROR", f"«{nombre}» no aparece como encabezado solo con "
                            "estilo de título", parecidos)
        else:
            informe.agregar("o", "ERROR", f"falta el encabezado «{nombre}»")
    informe.cerrar("o", f"portada {portada} e Introducción, Desarrollo y Conclusiones presentes")


# ---------------------------------------------------------------------------

def main():
    comun.salida_utf8()
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("docx")
    analizador.add_argument("--tipo", help="ensayo, monografia, informe, articulo, perfil, "
                            "tesis u otro (o un sinónimo de tipos.json)")
    analizador.add_argument("--variante", help="variante del tipo en tipos.json (p. ej. capitulos)")
    analizador.add_argument("--portada", choices=("blanca", "datos", "ninguna"))
    analizador.add_argument("--min-paginas", type=int)
    analizador.add_argument("--max-paginas", type=int)
    analizador.add_argument("--max-paginas-referencias", type=float, default=1.5)
    analizador.add_argument("--json", action="store_true")
    args = analizador.parse_args()
    ruta = Path(args.docx)
    informe = Informe()

    def salir_sin_poder(mensaje):
        if args.json:
            print(json.dumps({"archivo": str(ruta), "conforme": False, "error": mensaje},
                             ensure_ascii=False, indent=2))
        else:
            print(f"No se pudo verificar: {mensaje}", file=sys.stderr)
        sys.exit(2)

    tt, ruta_tipos, aviso_tipos = localizar_tipos()
    est = None
    if tt is not None:
        try:
            definiciones = tt.cargar(ruta_tipos)
        except tt.ErrorTipos as error:
            salir_sin_poder(f"tipos.json no es válido: {error}")
        if args.tipo:
            clave = tt.resolver(definiciones, args.tipo)
            if clave is None:
                salir_sin_poder(f"tipo «{args.tipo}» desconocido; tipos: "
                                f"{', '.join(tt.tipos_disponibles(definiciones))}")
            try:
                est = tt.estructura(definiciones, clave, args.variante)
            except tt.ErrorTipos as error:
                salir_sin_poder(str(error))
            args.tipo = clave
        elif args.variante:
            salir_sin_poder("--variante necesita --tipo")
    else:
        if args.tipo:
            args.tipo = comun.normalizar(args.tipo)
            if args.tipo not in TIPOS_ANTERIORES + TIPOS_SIN_DEFINICION:
                salir_sin_poder(f"tipo «{args.tipo}» desconocido; tipos: "
                                f"{', '.join(TIPOS_ANTERIORES + TIPOS_SIN_DEFINICION)}")
        if args.variante:
            aviso_tipos += f"; la variante «{args.variante}» no se aplica"

    if Document is None:
        salir_sin_poder("falta python-docx (pip install python-docx)")
    if not ruta.is_file():
        salir_sin_poder(f"no existe {ruta}")

    # a) integridad
    try:
        paquete = zipfile.ZipFile(ruta)
    except (zipfile.BadZipFile, OSError) as error:
        salir_sin_poder(f"no es un zip válido: {error}")
    with paquete:
        dañado = paquete.testzip()
        if dañado:
            informe.agregar("a", "ERROR", f"entrada dañada en el zip: {dañado}")
        ilegibles = []
        for nombre in paquete.namelist():
            if nombre.endswith((".xml", ".rels")):
                try:
                    ElementTree.fromstring(paquete.read(nombre))
                except ElementTree.ParseError as error:
                    ilegibles.append(f"{nombre}: {error}")
        if ilegibles:
            informe.agregar("a", "ERROR", "XML ilegible", ilegibles)
        if "word/document.xml" not in paquete.namelist():
            salir_sin_poder("falta word/document.xml")
        try:
            documento = Document(str(ruta))
        except Exception as error:  # noqa: BLE001
            salir_sin_poder(f"python-docx no lo abre: {error}")
        informe.cerrar("a", "zip íntegro y XML legible")
        resolutor = Resolutor(documento, paquete)
        secundarios = textos_secundarios(paquete)

    parrafos = analizar(documento, resolutor)
    portada_fin, portada_explicita = zona_portada(parrafos)
    refs_inicio, refs_entradas = zona_referencias(parrafos)
    clasificar(parrafos, portada_fin, refs_entradas)

    comprobar_pagina(documento, informe)
    comprobar_tipografia(parrafos, portada_fin, informe)
    comprobar_parrafos(parrafos, informe)
    comprobar_saltos(parrafos, portada_fin, informe, portada_explicita)
    comprobar_vacios(parrafos, portada_fin, informe)
    comprobar_marcadores(parrafos, secundarios, informe)
    excluidos = set(refs_entradas) | ({refs_inicio} if refs_inicio is not None else set())
    comprobar_autonomia(parrafos, excluidos, secundarios, informe)
    comprobar_referencias(parrafos, refs_inicio, refs_entradas, informe)
    comprobar_markdown(parrafos, informe)
    medida = comprobar_paginas(ruta, documento, parrafos, refs_inicio, args, informe, portada_fin)
    comprobar_tipo(parrafos, portada_fin, args, medida, informe, tt, est, aviso_tipos)

    orden = {clave: i for i, clave in enumerate(NOMBRES)}
    hallazgos = sorted(informe.hallazgos, key=lambda h: (orden[h["comprobacion"]], NIVELES.index(h["nivel"])))
    errores = sum(1 for h in hallazgos if h["nivel"] == "ERROR")
    avisos = sum(1 for h in hallazgos if h["nivel"] == "AVISO")
    conforme = errores == 0
    if conforme:
        veredicto = "FORMATO: CONFORME" + (f" ({avisos} avisos)" if avisos else "")
    else:
        veredicto = f"FORMATO: NO CONFORME ({errores} errores, {avisos} avisos)"
    if args.json:
        print(json.dumps({"archivo": str(ruta), "conforme": conforme, "errores": errores,
                          "tipo": args.tipo, "variante": est["variante"] if est else None,
                          "avisos": avisos, "paginas": medida.get("paginas"),
                          "paginas_referencias": medida.get("paginas_referencias"),
                          "parrafos": len(parrafos), "hallazgos": hallazgos,
                          "veredicto": veredicto}, ensure_ascii=False, indent=2))
    else:
        print(f"Archivo: {ruta}")
        print(f"Párrafos: {len(parrafos)} | páginas: {medida.get('paginas', 'no medidas')}")
        for hallazgo in hallazgos:
            print(f"[{hallazgo['nivel']}] {hallazgo['comprobacion']}) {hallazgo['nombre']}: "
                  f"{hallazgo['mensaje']}")
            for lugar in hallazgo["lugares"]:
                print(f"      - {lugar}")
            if hallazgo["total_lugares"] > len(hallazgo["lugares"]):
                print(f"      ... y {hallazgo['total_lugares'] - len(hallazgo['lugares'])} más")
        print(veredicto)
    sys.exit(0 if conforme else 1)


if __name__ == "__main__":
    main()
