# -*- coding: utf-8 -*-
"""Referencias APA 7 en español desde la biblioteca Zotero local.

Uso:
  python zotero_apa.py [--biblioteca <carpeta o .sqlite>]
                       [--buscar "texto"] [--doi 10.x/y] [--coleccion "nombre"]
                       [--todo] [--json]

No toca la biblioteca: copia zotero.sqlite (y sus -wal/-journal si
existen) a una carpeta temporal y abre la copia en solo lectura.
Funciona con Zotero abierto.

Biblioteca por defecto: variable ZOTERO_DIR o la carpeta ~/Zotero.

Filtros (se combinan; hace falta al menos uno, o --todo):
  --buscar     palabras que deben aparecer todas en el título o en los
               apellidos de los creadores (sin tildes ni mayúsculas).
  --doi        DOI exacto (acepta la URL https://doi.org/...).
  --coleccion  nombre de una colección; incluye sus subcolecciones.

Salida: referencias APA 7 en orden alfabético, cursivas con asteriscos
de Markdown, sin localizadores de cita. Con --json, además, por ítem:
clave, tipo, doi, url, anio, autores, adjuntos (ruta local del archivo
en storage/<clave>/ y si existe) y avisos de datos incompletos.

Límites: los títulos se escriben tal como están en Zotero (APA pide
mayúsculas de oración en artículos y capítulos; si un título parece
estar en mayúsculas de título se avisa, pero no se cambia, porque no
se pueden distinguir los nombres propios). Los adjuntos enlazados
("attachments:") se dan con su ruta relativa tal cual.

Códigos de salida: 0 hay ítems; 1 ningún ítem coincide con el filtro
(la fuente no está en la biblioteca); 2 no se pudo ejecutar.
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

import comun

TIPOS_EXCLUIDOS = ("attachment", "note", "annotation")
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre")
PARTICULAS_NOMBRE = {"de", "del", "la", "las", "los", "y", "da", "do", "dos", "das", "van", "von"}
ARTICULOS_INICIALES = ("el ", "la ", "los ", "las ", "lo ", "un ", "una ", "the ", "a ", "an ")
# Campos equivalentes en Zotero: cada tipo guarda el dato con su propio nombre.
CAMPOS_TITULO = ("title", "nameOfAct", "caseName", "subject")
CAMPOS_EDITORIAL = ("publisher", "university", "institution", "label", "company",
                    "distributor", "studio", "network")
CAMPOS_FECHA = ("date", "dateEnacted", "dateDecided", "issueDate", "filingDate")
CAMPOS_CONTENEDOR = ("publicationTitle", "websiteTitle", "blogTitle", "forumTitle",
                     "proceedingsTitle", "encyclopediaTitle", "dictionaryTitle",
                     "programTitle", "bookTitle", "code", "reporter")


# ---------------------------------------------------------------- lectura

def ubicar_base(opcion):
    """Ruta del zotero.sqlite a partir de la opción, ZOTERO_DIR o ~/Zotero."""
    candidata = Path(opcion or os.environ.get("ZOTERO_DIR", "") or Path.home() / "Zotero")
    candidata = candidata.expanduser()
    if candidata.is_dir():
        candidata = candidata / "zotero.sqlite"
    return candidata


def copiar_base(base, destino):
    """Copia la base y sus archivos auxiliares; devuelve la ruta de la copia."""
    copia = Path(destino) / "zotero.sqlite"
    shutil.copy2(base, copia)
    for sufijo in ("-wal", "-journal"):
        auxiliar = Path(str(base) + sufijo)
        if auxiliar.exists():
            shutil.copy2(auxiliar, Path(str(copia) + sufijo))
    return copia


def abrir_solo_lectura(copia):
    con = sqlite3.connect(Path(copia).as_uri() + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def tabla_existe(con, nombre):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') "
                       "AND name = ?", (nombre,)).fetchone() is not None


def leer_items(con, carpeta_biblioteca):
    """Ítems bibliográficos (sin adjuntos, notas, anotaciones ni papelera)."""
    tipos = "itemTypesCombined" if tabla_existe(con, "itemTypesCombined") else "itemTypes"
    campos = "fieldsCombined" if tabla_existe(con, "fieldsCombined") else "fields"
    excluir = ["SELECT itemID FROM deletedItems"]
    if tabla_existe(con, "feedItems"):
        excluir.append("SELECT itemID FROM feedItems")
    filas = con.execute(
        f"SELECT i.itemID, i.key, t.typeName FROM items i "
        f"JOIN {tipos} t ON t.itemTypeID = i.itemTypeID "
        f"WHERE t.typeName NOT IN ({','.join('?' * len(TIPOS_EXCLUIDOS))}) "
        f"AND i.itemID NOT IN ({' UNION '.join(excluir)})", TIPOS_EXCLUIDOS).fetchall()
    items = {f["itemID"]: {"id": f["itemID"], "clave": f["key"], "tipo": f["typeName"],
                           "campos": {}, "creadores": [], "adjuntos": []} for f in filas}
    for f in con.execute(f"SELECT d.itemID, c.fieldName, v.value FROM itemData d "
                         f"JOIN {campos} c ON c.fieldID = d.fieldID "
                         f"JOIN itemDataValues v ON v.valueID = d.valueID"):
        if f["itemID"] in items:
            items[f["itemID"]]["campos"][f["fieldName"]] = str(f["value"])
    for f in con.execute("SELECT ic.itemID, c.firstName, c.lastName, c.fieldMode, ct.creatorType "
                         "FROM itemCreators ic JOIN creators c ON c.creatorID = ic.creatorID "
                         "JOIN creatorTypes ct ON ct.creatorTypeID = ic.creatorTypeID "
                         "ORDER BY ic.itemID, ic.orderIndex"):
        if f["itemID"] in items:
            items[f["itemID"]]["creadores"].append({
                "apellido": (f["lastName"] or "").strip(), "nombre": (f["firstName"] or "").strip(),
                "institucional": f["fieldMode"] == 1, "rol": f["creatorType"]})
    for f in con.execute("SELECT a.parentItemID, a.path, a.contentType, i.key FROM itemAttachments a "
                         "JOIN items i ON i.itemID = a.itemID WHERE a.parentItemID IS NOT NULL "
                         "AND a.path IS NOT NULL AND a.itemID NOT IN (SELECT itemID FROM deletedItems)"):
        if f["parentItemID"] not in items:
            continue
        ruta = f["path"]
        if ruta.startswith("storage:"):
            ruta = str(Path(carpeta_biblioteca) / "storage" / f["key"] / ruta[len("storage:"):])
            existe = os.path.exists(ruta)
        else:  # enlazado: absoluto o relativo a la carpeta base ("attachments:")
            existe = os.path.exists(ruta) if os.path.isabs(ruta) else None
        items[f["parentItemID"]]["adjuntos"].append(
            {"ruta": ruta, "tipo": f["contentType"] or "", "existe": existe})
    colecciones = {}
    if tabla_existe(con, "collections"):
        nombres = {f["collectionID"]: (f["collectionName"], f["parentCollectionID"])
                   for f in con.execute("SELECT collectionID, collectionName, parentCollectionID "
                                        "FROM collections")}
        for f in con.execute("SELECT collectionID, itemID FROM collectionItems"):
            if f["itemID"] not in items:
                continue
            actual = f["collectionID"]
            while actual in nombres:  # la colección y todas sus madres
                colecciones.setdefault(f["itemID"], set()).add(comun.normalizar(nombres[actual][0]))
                actual = nombres[actual][1]
    for item_id, item in items.items():
        item["colecciones"] = colecciones.get(item_id, set())
    return list(items.values())


# ---------------------------------------------------------------- formato APA

def campo(item, *nombres):
    for nombre in nombres:
        valor = item["campos"].get(nombre, "").strip()
        if valor:
            return valor
    return ""


def iniciales(nombre):
    """'Juan Carlos' -> 'J. C.'; 'Jean-Paul' -> 'J.-P.'; omite 'de', 'del'."""
    partes = []
    for palabra in nombre.replace(".", ". ").split():
        if palabra.lower() in PARTICULAS_NOMBRE:
            continue
        guiones = [p for p in palabra.split("-") if p]
        if guiones:
            partes.append("-".join(p[0].upper() + "." for p in guiones))
    return " ".join(partes)


def nombre_invertido(creador):
    """Apellido, N. N. (o el nombre institucional tal cual)."""
    if creador["institucional"] or not creador["nombre"]:
        return creador["apellido"]
    return f"{creador['apellido']}, {iniciales(creador['nombre'])}"


def nombre_directo(creador):
    """N. N. Apellido, para editores dentro de 'En ...'."""
    if creador["institucional"] or not creador["nombre"]:
        return creador["apellido"]
    return f"{iniciales(creador['nombre'])} {creador['apellido']}"


def lista_autores(creadores):
    """Hasta 20 con 'y' antes del último; 21 o más: 19, '...', último."""
    nombres = [nombre_invertido(c) for c in creadores]
    if len(nombres) == 1:
        return nombres[0]
    if len(nombres) <= 20:
        return ", ".join(nombres[:-1]) + ", y " + nombres[-1]
    return ", ".join(nombres[:19]) + ", ... " + nombres[-1]


def lista_editores(creadores):
    nombres = [nombre_directo(c) for c in creadores]
    if len(nombres) > 20:
        nombres = nombres[:19] + ["... " + nombres[-1]]
        texto = ", ".join(nombres)
    elif len(nombres) == 1:
        texto = nombres[0]
    else:
        texto = ", ".join(nombres[:-1]) + " y " + nombres[-1]
    return f"{texto} ({'Ed.' if len(creadores) == 1 else 'Eds.'})"


def partes_fecha(item):
    """(año o None, mes, día) desde el formato de Zotero 'AAAA-MM-DD original'."""
    hallado = re.match(r"\s*(\d{4})-(\d{2})-(\d{2})", campo(item, *CAMPOS_FECHA))
    if hallado:
        return hallado.group(1), int(hallado.group(2)), int(hallado.group(3))
    anio = re.search(r"\b(1[5-9]\d\d|20\d\d)\b", campo(item, *CAMPOS_FECHA))
    return (anio.group(1) if anio else None), 0, 0


def con_punto(texto):
    texto = texto.rstrip()
    nucleo = texto.rstrip("*")
    return texto if not nucleo or nucleo[-1] in ".?!" else texto + "."


def cursiva(texto):
    return f"*{texto}*" if texto else ""


def paginas(texto):
    return re.sub(r"\s*[-‐‑–—]\s*", "–", texto.strip())


def edicion(texto):
    numero = re.match(r"\s*(\d+)", texto or "")
    if numero:
        return "1.ª ed." if numero.group(1) == "1" else f"{numero.group(1)}.ª ed."
    return texto.strip()


def doi_tal_cual(item):
    """DOI con sus mayúsculas originales (APA lo copia como está registrado)."""
    for nombre in ("DOI", "extra"):
        hallado = re.search(r"10\.\d{4,9}/[^\s\"<>]+", campo(item, nombre))
        if hallado:
            return hallado.group(0).rstrip(".,;)")
    return None


def enlace(item):
    doi = doi_tal_cual(item)
    return f"https://doi.org/{doi}" if doi else campo(item, "url")


def sigla(nombre):
    return "".join(p[0] for p in nombre.split() if p[:1].isupper())


def misma_entidad(editorial, autores):
    """La editorial repite al autor (o su sigla): APA la omite."""
    e = comun.normalizar(editorial)
    for c in autores:
        n = comun.normalizar(c["apellido"])
        if e and (e == n or (c["institucional"] and e == comun.normalizar(sigla(c["apellido"])))):
            return True
    return False


def tipo_tesis(texto, publicada):
    t = comun.normalizar(texto)
    if any(p in t for p in ("master", "maestr", "magist", "msc", "mestrado")):
        base = "Tesis de maestría"
    elif any(p in t for p in ("doct", "phd", "ph d", "dissertation")):
        base = "Tesis de doctorado"
    elif any(p in t for p in ("licenci", "bachelor", "grado", "pregrado")):
        base = "Tesis de licenciatura"
    else:
        base = texto.strip() or "Tesis"
    return base if publicada else base + " no publicada"


def avisos_de(item, autores, anio):
    avisos = []
    if not anio:
        avisos.append("sin fecha: se usa (s. f.)")
    if not campo(item, *CAMPOS_TITULO):
        avisos.append("sin título")
    if item["tipo"] == "journalArticle" and not campo(item, "publicationTitle"):
        avisos.append("artículo sin nombre de revista")
    if item["tipo"] in ("book", "bookSection") and not campo(item, *CAMPOS_EDITORIAL):
        avisos.append("sin editorial")
    if item["tipo"] in ("journalArticle", "bookSection", "conferencePaper"):
        palabras = re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{4,}", campo(item, "title"))[1:]
        mayusculas = [p for p in palabras if p[0].isupper()]
        if len(palabras) >= 3 and len(mayusculas) / len(palabras) > 0.6:
            avisos.append("título en mayúsculas de título: APA pide mayúsculas de oración")
    if not autores and item["tipo"] not in ("statute", "case", "webpage"):
        avisos.append("sin autor: la referencia empieza por el título")
    return avisos


def componer(item):
    """Devuelve el diccionario del ítem con 'autor', 'fecha', 'cuerpo' y datos."""
    creadores = item["creadores"]
    autores = [c for c in creadores if c["rol"] in ("author", "contributor", "inventor",
                                                    "artist", "director", "presenter", "sponsor")]
    editores = [c for c in creadores if c["rol"] == "editor"]
    tipo = item["tipo"]
    rol_autor = ""
    if not autores and editores and tipo != "bookSection":
        autores, rol_autor = editores, (" (Ed.)." if len(editores) == 1 else " (Eds.).")
    anio, mes, dia = partes_fecha(item)
    titulo = campo(item, *CAMPOS_TITULO)
    editorial = campo(item, *CAMPOS_EDITORIAL)
    if misma_entidad(editorial, autores):
        editorial = ""
    url = enlace(item)
    resto = []

    if tipo == "journalArticle":
        titulo_txt = titulo
        revista = campo(item, "publicationTitle")
        volumen, numero = campo(item, "volume"), campo(item, "issue")
        fuente = cursiva(f"{revista}, {volumen}" if volumen else revista)
        if numero:
            fuente += f"({numero})"
        if campo(item, "pages"):
            fuente += ", " + paginas(campo(item, "pages"))
        resto.append(fuente)
    elif tipo == "book":
        titulo_txt = cursiva(titulo)
        if campo(item, "edition"):
            titulo_txt += f" ({edicion(campo(item, 'edition'))})"
        resto.append(editorial)
    elif tipo == "bookSection":
        titulo_txt = titulo
        datos = [edicion(campo(item, "edition"))] if campo(item, "edition") else []
        if campo(item, "pages"):
            datos.append("pp. " + paginas(campo(item, "pages")))
        libro = cursiva(campo(item, "bookTitle")) + (f" ({', '.join(datos)})" if datos else "")
        resto.append(f"En {lista_editores(editores)}, {libro}" if editores else f"En {libro}")
        resto.append(editorial)
    elif tipo == "thesis":
        publicada = bool(url or campo(item, "archive"))
        descripcion = tipo_tesis(campo(item, "thesisType"), publicada)
        universidad = campo(item, "university", "publisher")
        titulo_txt = cursiva(titulo) + f" [{descripcion}{', ' + universidad if universidad else ''}]"
        resto.append(campo(item, "archive"))
    elif tipo == "report":
        titulo_txt = cursiva(titulo)
        numero = campo(item, "reportNumber")
        if numero:
            titulo_txt += f" ({campo(item, 'reportType') or 'Informe'} N.º {numero})"
        resto.append(editorial)
    elif tipo in ("webpage", "blogPost", "forumPost"):
        titulo_txt = cursiva(titulo)
        sitio = campo(item, "websiteTitle", "blogTitle", "forumTitle")
        if not misma_entidad(sitio, autores):
            resto.append(sitio)
    elif tipo == "statute":
        titulo_txt = cursiva(titulo)
        numero = campo(item, "publicLawNumber")
        if numero:
            titulo_txt += f" [Ley N.º {numero}]"
        resto.append(campo(item, "code"))
    else:  # forma genérica: título en cursiva, contenedor y editorial
        titulo_txt = cursiva(titulo)
        contenedor = campo(item, *CAMPOS_CONTENEDOR)
        resto.append(cursiva(contenedor) if contenedor else "")
        resto.append(editorial)

    if anio and mes and tipo in ("webpage", "blogPost", "forumPost", "statute", "newspaperArticle",
                                 "magazineArticle", "presentation"):
        fecha = f"{anio}, {dia} de {MESES[mes - 1]}" if dia else f"{anio}, {MESES[mes - 1]}"
    else:
        fecha = anio or "s. f."
    return {
        "item": item, "anio": anio, "fecha": fecha, "sufijo": "",
        "autor": (lista_autores(autores) + rol_autor) if autores else "",
        "titulo": titulo_txt, "resto": [r for r in resto if r], "url": url,
        "avisos": avisos_de(item, autores, anio),
    }


def texto_referencia(ref):
    fecha = ref["fecha"]
    if ref["sufijo"]:
        fecha = fecha.replace(ref["anio"], ref["anio"] + ref["sufijo"], 1) if ref["anio"] \
            else f"s. f.-{ref['sufijo']}"
    partes = []
    if ref["autor"]:
        partes += [con_punto(ref["autor"]), f"({fecha}).", con_punto(ref["titulo"])]
    else:
        partes += [con_punto(ref["titulo"]), f"({fecha})."]
    partes += [con_punto(r) for r in ref["resto"]]
    if ref["url"]:
        partes.append(ref["url"])
    return " ".join(partes)


def clave_orden(ref):
    cabeza = ref["autor"] or ref["titulo"].strip("*")
    cabeza = comun.normalizar(cabeza)
    for articulo in ARTICULOS_INICIALES:
        if not ref["autor"] and cabeza.startswith(articulo):
            cabeza = cabeza[len(articulo):]
            break
    return (cabeza, ref["anio"] or "0000", comun.normalizar(ref["titulo"]))


def asignar_sufijos(refs):
    """Mismo autor y mismo año: 2020a, 2020b (orden por título)."""
    grupos = {}
    for ref in refs:
        if ref["autor"]:
            grupos.setdefault((ref["autor"], ref["anio"]), []).append(ref)
    for grupo in grupos.values():
        if len(grupo) > 1:
            for letra, ref in zip("abcdefghijklmnopqrstuvwxyz",
                                  sorted(grupo, key=lambda r: comun.normalizar(r["titulo"]))):
                ref["sufijo"] = letra


# ---------------------------------------------------------------- filtros y salida

def filtrar(items, buscar=None, doi=None, coleccion=None):
    elegidos = items
    if buscar:
        palabras = comun.normalizar(buscar).split()
        def coincide(item):
            pajar = comun.normalizar(" ".join([campo(item, *CAMPOS_TITULO)] +
                                              [c["apellido"] for c in item["creadores"]]))
            return all(p in pajar for p in palabras)
        elegidos = [i for i in elegidos if coincide(i)]
    if doi:
        buscado = comun.limpiar_doi(doi) or doi.strip().lower()
        elegidos = [i for i in elegidos if comun.limpiar_doi(campo(i, "DOI", "extra")) == buscado]
    if coleccion:
        nombre = comun.normalizar(coleccion)
        elegidos = [i for i in elegidos if nombre in i["colecciones"]]
    return elegidos


def a_json(ref):
    item = ref["item"]
    return {
        "clave": item["clave"], "tipo": item["tipo"], "referencia": texto_referencia(ref),
        "doi": comun.limpiar_doi(campo(item, "DOI", "extra")), "url": campo(item, "url") or None,
        "anio": ref["anio"],
        "autores": [c["apellido"] + (", " + c["nombre"] if c["nombre"] else "")
                    for c in item["creadores"] if c["rol"] != "editor"],
        "adjuntos": item["adjuntos"], "avisos": ref["avisos"],
    }


def main(argv=None):
    comun.salida_utf8()
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("--biblioteca", help="carpeta de Zotero o archivo zotero.sqlite")
    analizador.add_argument("--buscar", help="palabras del título o apellidos")
    analizador.add_argument("--doi", help="DOI a buscar")
    analizador.add_argument("--coleccion", help="nombre de colección (incluye subcolecciones)")
    analizador.add_argument("--todo", action="store_true", help="toda la biblioteca")
    analizador.add_argument("--json", action="store_true", help="salida JSON")
    args = analizador.parse_args(argv)
    if not (args.todo or args.buscar or args.doi or args.coleccion):
        print("Indique --buscar, --doi, --coleccion o --todo.", file=sys.stderr)
        return 2
    base = ubicar_base(args.biblioteca)
    if not base.is_file():
        print(f"No se encontró la biblioteca Zotero en {base}. Use --biblioteca o la variable "
              "ZOTERO_DIR.", file=sys.stderr)
        return 2
    try:
        with tempfile.TemporaryDirectory(prefix="zotero_apa_") as temporal:
            con = abrir_solo_lectura(copiar_base(base, temporal))
            try:
                items = leer_items(con, base.parent)
            finally:
                con.close()
    except (OSError, sqlite3.Error) as error:
        print(f"No se pudo leer la biblioteca ({type(error).__name__}: {error}). Si Zotero está "
              "sincronizando, espere y vuelva a intentar.", file=sys.stderr)
        return 2

    refs = [componer(i) for i in filtrar(items, args.buscar, args.doi, args.coleccion)]
    asignar_sufijos(refs)
    refs.sort(key=clave_orden)
    if args.json:
        print(json.dumps({"biblioteca": str(base), "total": len(refs),
                          "items": [a_json(r) for r in refs]}, ensure_ascii=False, indent=2))
    else:
        for ref in refs:
            print(texto_referencia(ref))
            print()
        print(f"{len(refs)} referencia(s).", file=sys.stderr)
        for ref in refs:
            for aviso in ref["avisos"]:
                print(f"Aviso [{ref['item']['clave']}]: {aviso}", file=sys.stderr)
    if not refs:
        print("Ningún ítem coincide: la fuente no está en la biblioteca.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
