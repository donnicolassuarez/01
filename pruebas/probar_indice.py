# -*- coding: utf-8 -*-
"""Pruebas del índice automático de construir_docx.py y de la comprobación
p) de verificar_formato.py.

Uso:
  python pruebas/probar_indice.py [--salida carpeta] [--sin-regresion]

Por defecto escribe en pruebas/salida/caso_indice/ (no versionada).

Casos:
  a) Regresión: probar_tipos.py (50/50), crear_docx_defectuosos.py
     --comprobar (9/9), probar_limites.py --sin-red, probar_encargo.py;
     ensayo_prueba.md da 4 páginas CONFORME y sin índice; el ensayo de
     aceptación sigue CONFORME con 5 páginas. (--sin-regresion lo omite.)
  b) Caso largo (pruebas/casos/indice_largo.md, tesis): se construye con
     índice; cada número del índice se compara con la página real por un
     método independiente del constructor (los enlaces del PDF: destino de
     cada entrada, número que imprime el pie de esa página y texto del
     título en ella); el campo TOC está bien formado (fldChar equilibrados,
     instrucción, marcadores únicos, enlaces y PAGEREF a marcadores
     existentes); se dejan PNG de la página del índice y de dos interiores
     para mirarlas. El verificador da CONFORME con p) OK.
     Más: cuándo se genera (ensayo sin pedirlo no; con `\\indice` sí;
     monografía con `indice: si`; tesis con --sin-indice no; sin portada).
  c) LibreOffice actualiza el índice (UNO, sin interfaz): mismas entradas
     y páginas; y sobre un índice con un número alterado, la actualización
     lo corrige (prueba de que LibreOffice recalcula y no solo copia).
  d) Negativos del verificador: número alterado (ERROR con título, página
     en el índice y página real) y título añadido después del índice
     (ERROR: falta en el índice).
  e) Sin LibreOffice (SOFFICE=ninguno): índice con entradas y sin números,
     w:updateFields activado, código 1 con aviso claro. Con números medidos
     no se activa w:updateFields.
  f) Tiempo de construcción con índice y sin él.

Imprime una tabla caso -> esperado / obtenido. Sale con 1 si algo falla.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPTS = RAIZ / "skills" / "niveles-academicos" / "scripts"
CASOS = RAIZ / "pruebas" / "casos"
ACEPTACION = RAIZ / "pruebas" / "aceptacion" / "ensayo_incendios" / "entrega"
sys.path.insert(0, str(SCRIPTS))
import comun  # noqa: E402

from docx import Document  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

filas = []
tabla_paginas = []


def anotar(caso, esperado, obtenido, bien):
    filas.append((caso, esperado, obtenido, bool(bien)))


def correr(script, *argumentos, env=None):
    entorno = dict(os.environ)
    entorno.pop("TIPOS_TRABAJO", None)
    entorno.update(env or {})
    r = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, argumentos)],
                       capture_output=True, text=True, encoding="utf-8", env=entorno)
    try:
        datos = json.loads(r.stdout)
    except json.JSONDecodeError:
        datos = None
    return r.returncode, datos, r.stdout + r.stderr


def construir(md, docx, *extra, env=None):
    return correr("construir_docx.py", md, "--salida", docx, "--json", *extra, env=env)


def verificar(docx, tipo=None, *extra, env=None):
    args = [docx, "--json"] + (["--tipo", tipo] if tipo else [])
    return correr("verificar_formato.py", *args, *extra, env=env)


def hallazgos(datos, clave, nivel=None):
    return [h for h in (datos or {}).get("hallazgos", [])
            if h["comprobacion"] == clave and (nivel is None or h["nivel"] == nivel)]


def tiene_toc(docx):
    xml = zipfile.ZipFile(docx).read("word/document.xml").decode("utf-8")
    return "TOC \\o" in xml


# ------------------------------------------------------------ métodos propios

def numero_pie(pagina):
    """Número del pie (texto de dígitos en los 2,54 cm inferiores) o None."""
    limite = pagina.rect.height - 2.54 * 72 / 2.54
    numeros = [t for x0, y0, x1, y1, t, *_ in pagina.get_text("words")
               if y0 >= limite and t.isdigit()]
    return int(numeros[-1]) if numeros else None


def entradas_por_enlaces(ruta_pdf):
    """Lee el índice del PDF por sus enlaces internos (método independiente
    del constructor, que usa el esquema de marcadores del PDF).

    Devuelve [(título, número impreso en el índice, página destino física,
    número del pie de la página destino, título presente en esa página)].
    """
    pymupdf = comun.importar_pymupdf()
    resultado = []
    with pymupdf.open(str(ruta_pdf)) as pdf:
        pies = [numero_pie(p) for p in pdf]
        textos = [comun.normalizar(p.get_text()) for p in pdf]
        for pagina in pdf:
            enlaces = [e for e in pagina.get_links() if e.get("kind") == pymupdf.LINK_GOTO]
            enlaces.sort(key=lambda e: (e["from"].y0, e["from"].x0))
            pendiente = ""
            for enlace in enlaces:
                texto = pagina.get_textbox(enlace["from"]).strip()
                hallado = re.match(r"^(.*?)[\s.…]*?(\d+)$", texto)
                if not hallado:          # primera línea de una entrada partida
                    pendiente += texto + " "
                    continue
                titulo = (pendiente + hallado.group(1)).rstrip(" .")
                pendiente = ""
                destino = enlace["page"]
                resultado.append((titulo, int(hallado.group(2)), destino + 1, pies[destino],
                                  comun.normalizar(titulo) in textos[destino]))
    return resultado


def revisar_campo_toc(docx):
    """Problemas de forma del campo TOC (lista vacía si está bien)."""
    problemas = []
    documento = Document(str(docx))
    cuerpo = documento.element.body
    pila, campos = [], []
    for nodo in cuerpo.iter(qn("w:fldChar"), qn("w:instrText")):
        if nodo.tag == qn("w:instrText"):
            if pila:
                pila[-1]["instr"] += nodo.text or ""
            continue
        tipo = nodo.get(qn("w:fldCharType"))
        if tipo == "begin":
            pila.append({"instr": "", "separate": False})
        elif tipo == "separate":
            if not pila or pila[-1]["separate"]:
                problemas.append("separate sin begin o repetido")
            else:
                pila[-1]["separate"] = True
        elif tipo == "end":
            if not pila:
                problemas.append("end sin begin")
            else:
                campo = pila.pop()
                if not campo["separate"]:
                    problemas.append(f"campo sin separate: {campo['instr']!r}")
                campos.append(campo["instr"].strip())
    if pila:
        problemas.append(f"{len(pila)} campo(s) sin end")
    tocs = [c for c in campos if c.startswith("TOC")]
    if tocs != ['TOC \\o "1-3" \\h \\z \\u']:
        problemas.append(f"instrucción TOC inesperada: {tocs}")
    marcadores = [b.get(qn("w:name")) for b in cuerpo.iter(qn("w:bookmarkStart"))]
    ids = [b.get(qn("w:id")) for b in cuerpo.iter(qn("w:bookmarkStart"))]
    ids_fin = [b.get(qn("w:id")) for b in cuerpo.iter(qn("w:bookmarkEnd"))]
    if len(set(marcadores)) != len(marcadores) or len(set(ids)) != len(ids):
        problemas.append("marcadores o ids repetidos")
    if sorted(ids) != sorted(ids_fin):
        problemas.append("bookmarkStart y bookmarkEnd no se corresponden")
    anclas = [h.get(qn("w:anchor")) for h in cuerpo.iter(qn("w:hyperlink"))]
    faltan = [a for a in anclas if a not in marcadores]
    if faltan:
        problemas.append(f"enlaces a marcadores inexistentes: {faltan}")
    pagerefs = [re.match(r"PAGEREF (\S+)", c).group(1) for c in campos if c.startswith("PAGEREF")]
    if pagerefs != anclas:
        problemas.append("los PAGEREF no apuntan a los mismos marcadores que los enlaces")
    titulos = [p for p in documento.paragraphs if p.style.name.startswith("Heading")]
    sin_marcador = [p.text for p in titulos if not p._p.findall(qn("w:bookmarkStart"))]
    if sin_marcador:
        problemas.append(f"títulos sin marcador: {sin_marcador[:3]}")
    return problemas, len(anclas), len(titulos)


def entradas_docx(docx):
    """[(título, número)] del resultado guardado del campo TOC."""
    documento = Document(str(docx))
    resultado = []
    for p in documento.paragraphs:
        if p.style.name.startswith("toc ") and "\t" in p.text:
            titulo, _, numero = p.text.rpartition("\t")
            resultado.append((titulo, numero))
    return resultado


def ajustes(docx):
    return zipfile.ZipFile(docx).read("word/settings.xml").decode("utf-8")


# ------------------------------------------------------------ LibreOffice UNO

PROGRAMA_UNO = r'''
import subprocess, sys, time, tempfile, socket
from pathlib import Path
import uno
from com.sun.star.beans import PropertyValue
def pv(n, v):
    p = PropertyValue(); p.Name = n; p.Value = v; return p
soffice, origen, destino = sys.argv[1], Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
perfil = Path(tempfile.mkdtemp(prefix="agac_uno_"))
s = socket.socket(); s.bind(("127.0.0.1", 0)); puerto = s.getsockname()[1]; s.close()
proc = subprocess.Popen([soffice, "-env:UserInstallation=" + perfil.as_uri(), "--headless",
                         "--invisible", "--norestore", "--nolockcheck",
                         f"--accept=socket,host=127.0.0.1,port={puerto};urp;"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    ctx = uno.getComponentContext()
    res = ctx.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", ctx)
    for _ in range(120):
        try:
            rctx = res.resolve(f"uno:socket,host=127.0.0.1,port={puerto};urp;StarOffice.ComponentContext")
            break
        except Exception:
            time.sleep(0.5)
    escritorio = rctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", rctx)
    doc = escritorio.loadComponentFromURL(origen.as_uri(), "_blank", 0, (pv("Hidden", True),))
    indices = doc.getDocumentIndexes()
    cuantos = indices.getCount()
    for i in range(cuantos):
        indices.getByIndex(i).update()
    doc.storeToURL(destino.with_suffix(".docx").as_uri(), (pv("FilterName", "MS Word 2007 XML"),))
    doc.storeToURL(destino.with_suffix(".pdf").as_uri(), (pv("FilterName", "writer_pdf_Export"),))
    doc.close(True)
    print("INDICES", cuantos)
    try:
        escritorio.terminate()
    except Exception:
        pass
finally:
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
'''


def actualizar_con_libreoffice(docx, destino):
    """Abre el docx en LibreOffice (UNO), actualiza todos sus índices y lo
    guarda como docx y PDF. Devuelve (número de índices, motivo si falló)."""
    soffice = comun.ruta_soffice()
    if not soffice:
        return None, "sin LibreOffice"
    with tempfile.TemporaryDirectory() as temporal:
        programa = Path(temporal) / "actualizar.py"
        programa.write_text(PROGRAMA_UNO, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(programa), soffice, str(docx), str(destino)],
                               capture_output=True, text=True, timeout=240)
        except subprocess.TimeoutExpired:
            return None, "UNO no terminó en 240 s"
    hallado = re.search(r"INDICES (\d+)", r.stdout)
    if not hallado or not Path(destino).with_suffix(".pdf").exists():
        return None, (r.stderr or r.stdout).strip()[-300:] or f"código {r.returncode}"
    return int(hallado.group(1)), None


# ------------------------------------------------------------ casos

def probar_regresion(salida):
    for etiqueta, orden, patron in (
            ("probar_tipos.py", ["pruebas/probar_tipos.py"], r"^50/50 casos bien"),
            ("crear_docx_defectuosos.py --comprobar", ["pruebas/crear_docx_defectuosos.py", "--comprobar"],
             r"^9/9 defectos"),
            ("probar_limites.py --sin-red", ["pruebas/probar_limites.py", "--sin-red"], r", 0 fallos"),
            ("probar_encargo.py", ["pruebas/probar_encargo.py"], r", 0 fallos")):
        r = subprocess.run([sys.executable, *orden], cwd=RAIZ, capture_output=True, text=True,
                           encoding="utf-8")
        ultima = (r.stdout.strip().splitlines() or [""])[-1]
        anotar(f"a) {etiqueta}", "todo bien (código 0)", f"código {r.returncode}: {ultima}",
               r.returncode == 0 and re.search(patron, ultima))
    carpeta = salida / "regresion"
    carpeta.mkdir(parents=True, exist_ok=True)
    docx = carpeta / "ensayo_prueba.docx"
    cc, dc, _ = construir(CASOS / "ensayo_prueba.md", docx, "--tipo", "ensayo")
    cv, dv, _ = verificar(docx, "ensayo")
    anotar("a) ensayo_prueba.md", "4 pág., CONFORME sin avisos, sin índice",
           f"construir {cc}, {(dc or {}).get('paginas')} pág.; {(dv or {}).get('veredicto')}; "
           f"campo TOC: {tiene_toc(docx)}",
           cc == 0 and (dc or {}).get("paginas") == 4 and cv == 0 and (dv or {}).get("avisos") == 0
           and not tiene_toc(docx))
    entregables = sorted(ACEPTACION.glob("*.docx"))
    if entregables:
        cv, dv, _ = verificar(entregables[0], "ensayo", "--min-paginas", 5, "--max-paginas", 5)
        anotar("a) ensayo de aceptación", "CONFORME, 5 pág.",
               f"{(dv or {}).get('veredicto')}; {(dv or {}).get('paginas')} pág.",
               cv == 0 and (dv or {}).get("paginas") == 5)
    else:
        anotar("a) ensayo de aceptación", "CONFORME, 5 pág.", "no está el docx", False)


def probar_largo(salida):
    """b) y f). Devuelve la ruta del docx con índice."""
    md = CASOS / "indice_largo.md"
    docx = salida / "indice_largo.docx"
    inicio = time.perf_counter()
    cc, dc, texto_c = construir(md, docx, "--conservar-pdf")
    t_con = time.perf_counter() - inicio
    inicio = time.perf_counter()
    cs, ds, _ = construir(md, salida / "indice_largo_sin_indice.docx", "--sin-indice")
    t_sin = time.perf_counter() - inicio
    indice = (dc or {}).get("indice") or {}
    anotar("b) construir indice_largo.md", "código 0, 12+ pág., índice con números medidos",
           f"código {cc}, {(dc or {}).get('paginas')} pág., índice {indice}, avisos "
           f"{(dc or {}).get('avisos')}",
           cc == 0 and ((dc or {}).get("paginas") or 0) >= 12 and indice.get("numeros") == "medidos")
    anotar("f) tiempo de construcción", "informativo",
           f"con índice {t_con:.1f} s ({indice.get('renders')} renders + medición reutilizada); "
           f"--sin-indice {t_sin:.1f} s (1 render); código sin índice {cs}", True)

    # (1) números del índice frente a la página real, por los enlaces del PDF
    with tempfile.TemporaryDirectory() as temporal:
        pdf = comun.renderizar_pdf(docx, temporal)
        entradas = entradas_por_enlaces(pdf)
        shutil.copyfile(pdf, salida / "indice_largo_control.pdf")
    malas = [e for e in entradas if e[1] != e[3] or not e[4]]
    tabla_paginas.extend(entradas)
    n_titulos = (dc or {}).get("titulos")
    anotar("b1) cada número = página real (enlaces del PDF)",
           f"{n_titulos} entradas; número = pie de la página destino; título en esa página",
           f"{len(entradas)} entradas; discrepancias: {malas or 'ninguna'}",
           entradas and len(entradas) == n_titulos and not malas)
    # Títulos repetidos: dos «Conclusiones parciales» con páginas distintas
    repetidas = [e for e in entradas if e[0].endswith("Conclusiones parciales")]
    anotar("b1) título repetido «Conclusiones parciales»", "2 entradas, cada una con su página",
           f"{[(e[0], e[1], e[3]) for e in repetidas]}",
           len(repetidas) == 2 and all(e[1] == e[3] for e in repetidas) and repetidas[0][1] != repetidas[1][1])

    # (2) imágenes para mirarlas
    pymupdf = comun.importar_pymupdf()
    with pymupdf.open(str(salida / "indice_largo_control.pdf")) as documento:
        destinos = {e[0]: e[2] for e in entradas}
        paginas = {"indice": 2,
                   "interior_titulo_largo": destinos.get(next((t for t in destinos if t.startswith("2.2.2.")), ""), 6),
                   "interior_tabla": next((i + 1 for i, pg in enumerate(documento)
                                           if "Tabla 1." in pg.get_text()), 9)}
        for nombre, numero in paginas.items():
            documento[numero - 1].get_pixmap(dpi=110).save(str(salida / f"pagina_{nombre}.png"))
    anotar("b2) PNG para revisión visual", "índice y dos páginas interiores",
           ", ".join(f"pagina_{n}.png (pág. {p})" for n, p in paginas.items()), True)

    # (3) forma del campo TOC
    problemas, n_enlaces, n_titulos_docx = revisar_campo_toc(docx)
    anotar("b3) campo TOC bien formado (python-docx)",
           "fldChar equilibrados, instrucción TOC, marcadores únicos, enlaces y PAGEREF válidos",
           f"{n_enlaces} enlaces, {n_titulos_docx} títulos; problemas: {problemas or 'ninguno'}",
           not problemas and n_enlaces == n_titulos_docx)
    anotar("b3) sin w:updateFields con números medidos", "settings.xml sin updateFields",
           f"updateFields presente: {'updateFields' in ajustes(docx)}", "updateFields" not in ajustes(docx))

    cv, dv, salida_v = verificar(docx, "tesis")
    p = hallazgos(dv, "p")
    h = hallazgos(dv, "h")
    anotar("b) verificador sobre indice_largo.docx",
           "CONFORME; p) OK; o) sin aviso de índice; h) solo el \\pagebreak del caso",
           f"{(dv or {}).get('veredicto')}; p) {[x['nivel'] + ' ' + x['mensaje'] for x in p]}; "
           f"h) {[x['nivel'] + ' ' + x['mensaje'] + ' ' + str(x['lugares']) for x in h]}",
           cv == 0 and p and p[0]["nivel"] == "OK" and not hallazgos(dv, "o", "AVISO")
           and all(x["total_lugares"] == 1 for x in h if x["nivel"] == "AVISO"))
    return docx


def probar_cuando(salida):
    """b) cuándo se genera el índice."""
    carpeta = salida / "cuando"
    carpeta.mkdir(parents=True, exist_ok=True)
    texto_ensayo = (CASOS / "ensayo_prueba.md").read_text(encoding="utf-8")
    # ensayo con \indice
    md = carpeta / "ensayo_con_pedido.md"
    md.write_text(texto_ensayo.rstrip() + "\n\n\\indice\n", encoding="utf-8")
    docx = md.with_suffix(".docx")
    cc, dc, _ = construir(md, docx, "--tipo", "ensayo")
    cv, dv, _ = verificar(docx, "ensayo")
    anotar("b) ensayo con línea \\indice", "índice generado (petición explícita), CONFORME, p) OK",
           f"construir {cc}, índice {(dc or {}).get('indice')}, notas {(dc or {}).get('notas')}; "
           f"{(dv or {}).get('veredicto')}; p) {[x['nivel'] for x in hallazgos(dv, 'p')]}",
           tiene_toc(docx) and cv == 0 and [x["nivel"] for x in hallazgos(dv, "p")] == ["OK"])
    # monografía por defecto (opcional): sin pedirlo no; con indice: si sí
    md = CASOS / "tipo_monografia.md"
    docx = carpeta / "monografia_sin_pedido.docx"
    construir(md, docx)
    sin = tiene_toc(docx)
    md2 = carpeta / "monografia_con_meta.md"
    # el metadato va dentro del bloque ---: se inserta tras la primera línea ---
    lineas = md.read_text(encoding="utf-8").splitlines(keepends=True)
    primera = next(i for i, l in enumerate(lineas) if l.strip() == "---")
    lineas.insert(primera + 1, "indice: si\n")
    md2.write_text("".join(lineas), encoding="utf-8")
    docx2 = md2.with_suffix(".docx")
    cc, dc, _ = construir(md2, docx2)
    cv, dv, _ = verificar(docx2, "monografia")
    anotar("b) monografía (índice opcional)", "sin pedirlo: no; con «indice: si»: sí y CONFORME",
           f"sin pedido TOC={sin}; con metadato TOC={tiene_toc(docx2)}, {(dv or {}).get('veredicto')}",
           not sin and tiene_toc(docx2) and cv == 0)
    # tesis con --sin-indice
    docx = carpeta / "tesis_sin_indice.docx"
    cc, dc, _ = construir(CASOS / "tipo_tesis.md", docx, "--sin-indice")
    cv, dv, _ = verificar(docx, "tesis")
    o = [x["mensaje"] for x in hallazgos(dv, "o", "AVISO")]
    anotar("b) tesis con --sin-indice", "sin índice, NOTA del constructor, AVISO de índice en o)",
           f"TOC={tiene_toc(docx)}; notas {(dc or {}).get('notas')}; o) {o}",
           not tiene_toc(docx) and any("índice" in n for n in (dc or {}).get("notas", []))
           and any("índice" in m for m in o))
    # sin portada: el índice abre el documento y no se toma por portada
    md = carpeta / "otro_sin_portada.md"
    md.write_text((CASOS / "tipo_tesis.md").read_text(encoding="utf-8")
                  .replace("tipo: tesis", "tipo: otro") + "\n\\indice\n", encoding="utf-8")
    docx = md.with_suffix(".docx")
    cc, dc, _ = construir(md, docx)
    cv, dv, _ = verificar(docx, "otro")
    h = hallazgos(dv, "h")
    anotar("b) tipo otro, sin portada, con \\indice", "índice en la pág. 1, CONFORME, h) salto del índice estructural",
           f"construir {cc}, portada {(dc or {}).get('portada')}; {(dv or {}).get('veredicto')}; "
           f"h) {[x['nivel'] + ' ' + x['mensaje'] for x in h]}; p) {[x['nivel'] for x in hallazgos(dv, 'p')]}",
           cv == 0 and h and h[0]["nivel"] == "OK" and "índice" in h[0]["mensaje"]
           and [x["nivel"] for x in hallazgos(dv, "p")] == ["OK"])


def alterar_numero(origen, destino, sufijo_titulo, delta):
    """Cambia a mano el número de la ÚLTIMA entrada cuyo texto termina en
    `sufijo_titulo`. Devuelve (título, número viejo, número nuevo)."""
    documento = Document(str(origen))
    elegido = None
    for p in documento.paragraphs:
        if p.style.name.startswith("toc ") and p.text.rpartition("\t")[0].endswith(sufijo_titulo):
            elegido = p
    nodo = [t for t in elegido._p.iter(qn("w:t"))][-1]
    viejo = int(nodo.text)
    nodo.text = str(viejo + delta)
    documento.save(str(destino))
    return elegido.text.rpartition("\t")[0], viejo, viejo + delta


def agregar_titulo(origen, destino, antes_de, texto):
    """Inserta un Título 3 nuevo antes del título `antes_de`, sin tocar el índice."""
    documento = Document(str(origen))
    for p in documento.paragraphs:
        if p.style.name == "Heading 2" and p.text == antes_de:
            nuevo = OxmlElement("w:p")
            p._p.addprevious(nuevo)
            from docx.text.paragraph import Paragraph
            parrafo = Paragraph(nuevo, p._parent)
            parrafo.style = documento.styles["Heading 3"]
            parrafo.add_run(texto)
            cuerpo = OxmlElement("w:p")
            p._p.addprevious(cuerpo)
            parrafo = Paragraph(cuerpo, p._parent)
            parrafo.add_run("Párrafo neutro añadido junto con el título nuevo, para el caso negativo.")
            break
    documento.save(str(destino))


def probar_negativos(salida, docx):
    """d)"""
    alterado = salida / "negativo_numero_alterado.docx"
    titulo, viejo, nuevo = alterar_numero(docx, alterado, "4.3. Conclusiones parciales", 3)
    cv, dv, _ = verificar(alterado, "tesis")
    errores = hallazgos(dv, "p", "ERROR")
    lugares = [l for e in errores for l in e["lugares"]]
    esperado_lugar = f"«{titulo}»: el índice dice página {nuevo}; está en la página {viejo}"
    anotar("d) número del índice alterado a mano", f"ERROR en p): {esperado_lugar}",
           f"código {cv}; {[e['mensaje'] for e in errores]}; {lugares}; otros ERROR: "
           f"{[h['comprobacion'] for h in (dv or {}).get('hallazgos', []) if h['nivel'] == 'ERROR' and h['comprobacion'] != 'p']}",
           cv == 1 and lugares == [esperado_lugar]
           and all(h["comprobacion"] == "p" for h in (dv or {}).get("hallazgos", []) if h["nivel"] == "ERROR"))

    agregado = salida / "negativo_titulo_agregado.docx"
    nuevo_titulo = "4.2.1. Apartado añadido después de generar el índice"
    agregar_titulo(docx, agregado, "4.3. Conclusiones parciales", nuevo_titulo)
    cv, dv, _ = verificar(agregado, "tesis")
    errores = hallazgos(dv, "p", "ERROR")
    faltan = [e for e in errores if "no están en el índice" in e["mensaje"]]
    anotar("d) título añadido después del índice", "ERROR en p): el título falta en el índice",
           f"código {cv}; {[(e['mensaje'], e['lugares']) for e in errores]}",
           cv == 1 and faltan and any(nuevo_titulo[:30] in l for l in faltan[0]["lugares"]))
    return alterado


def probar_libreoffice(salida, docx, alterado):
    """c)"""
    destino = salida / "actualizado_libreoffice"
    cuantos, motivo = actualizar_con_libreoffice(docx, destino)
    if cuantos is None:
        anotar("c) LibreOffice actualiza el índice", "mismas entradas y páginas",
               f"NO PROBADO: {motivo}", False)
        return
    antes = [(e[0], e[1]) for e in entradas_por_enlaces(salida / "indice_largo_control.pdf")]
    despues_lista = entradas_por_enlaces(destino.with_suffix(".pdf"))
    despues = [(e[0], e[1]) for e in despues_lista]
    sin_enlace = []
    if not despues:  # si la actualización quitó los enlaces, se lee el texto del docx
        despues = [(t, int(n)) for t, n in entradas_docx(destino.with_suffix(".docx")) if n.isdigit()]
        sin_enlace = ["(sin enlaces en el PDF actualizado: leído del docx)"]
    distintas = [(a, b) for a, b in zip(antes, despues) if a != b]
    anotar("c) LibreOffice actualiza el índice (UNO)",
           "1 índice; mismas entradas y páginas que el generado",
           f"{cuantos} índice(s); {len(despues)} entradas tras actualizar; diferencias: "
           f"{distintas or 'ninguna'} {' '.join(sin_enlace)}",
           cuantos == 1 and len(antes) == len(despues) and not distintas)
    destino2 = salida / "alterado_actualizado_libreoffice"
    cuantos, motivo = actualizar_con_libreoffice(alterado, destino2)
    if cuantos is None:
        anotar("c) LibreOffice corrige un número alterado", "número restaurado", f"NO PROBADO: {motivo}", False)
        return
    corregido = [(e[0], e[1]) for e in entradas_por_enlaces(destino2.with_suffix(".pdf"))]
    anotar("c) LibreOffice recalcula (no copia): índice con número alterado",
           "tras actualizar, las entradas vuelven a las páginas reales",
           f"diferencias con el original: {[(a, b) for a, b in zip(antes, corregido) if a != b] or 'ninguna'}",
           corregido == antes)


def probar_sin_libreoffice(salida):
    """e)"""
    docx = salida / "sin_libreoffice.docx"
    cc, dc, texto = construir(CASOS / "indice_largo.md", docx, env={"SOFFICE": "ninguno"})
    avisos = (dc or {}).get("avisos", [])
    entradas = entradas_docx(docx) if docx.exists() else []
    vacias = [t for t, n in entradas if n == ""]
    anotar("e) sin LibreOffice (SOFFICE=ninguno)",
           "código 1; aviso «SIN CALCULAR»; campo TOC con todas las entradas sin número; w:updateFields",
           f"código {cc}; avisos {avisos}; entradas {len(entradas)} (sin número {len(vacias)}); "
           f"updateFields: {'updateFields' in ajustes(docx) if docx.exists() else None}",
           cc == 1 and any("SIN CALCULAR" in a for a in avisos) and entradas
           and len(vacias) == len(entradas) and 'w:updateFields w:val="true"' in ajustes(docx)
           and not revisar_campo_toc(docx)[0])
    cv, dv, _ = verificar(docx, "tesis")
    p = hallazgos(dv, "p")
    anotar("e) verificador sobre el docx sin números (con LibreOffice)",
           "ERROR en p): entradas sin número de página",
           f"{[(x['nivel'], x['mensaje']) for x in p]}",
           any(x["nivel"] == "ERROR" and "sin número" in x["mensaje"] for x in p))
    cv, dv, _ = verificar(docx, "tesis", env={"SOFFICE": "ninguno"})
    p = hallazgos(dv, "p")
    anotar("e) verificador sin LibreOffice", "AVISO en p): números no comprobados",
           f"{[(x['nivel'], x['mensaje']) for x in p]}",
           any(x["nivel"] == "AVISO" and "no comprobados" in x["mensaje"] for x in p))


def main():
    comun.salida_utf8()
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("--salida", default=str(RAIZ / "pruebas" / "salida" / "caso_indice"))
    analizador.add_argument("--sin-regresion", action="store_true")
    args = analizador.parse_args()
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    docx = probar_largo(salida)
    probar_cuando(salida)
    alterado = probar_negativos(salida, docx)
    probar_libreoffice(salida, docx, alterado)
    probar_sin_libreoffice(salida)
    if not args.sin_regresion:
        probar_regresion(salida)

    if tabla_paginas:
        print("Caso largo: título | página en el índice | página real (pie de la página destino)")
        for titulo, numero, fisica, pie, presente in tabla_paginas:
            marca = "" if numero == pie and presente else "  <-- NO COINCIDE"
            print(f"  {titulo[:78]:78} | {numero:>3} | {pie:>3} (física {fisica}){marca}")
        print()
    malos = 0
    for caso, esperado, obtenido, bien in filas:
        malos += not bien
        print(f"[{'BIEN' if bien else 'FALLA'}] {caso}\n       esperado: {esperado}\n       obtenido: {obtenido}")
    print(f"\n{len(filas) - malos}/{len(filas)} casos bien")
    (salida / "resultado.json").write_text(json.dumps(
        [dict(zip(("caso", "esperado", "obtenido", "bien"), f)) for f in filas],
        ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(1 if malos else 0)


if __name__ == "__main__":
    main()
