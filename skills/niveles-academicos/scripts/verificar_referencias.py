# -*- coding: utf-8 -*-
"""Verificación mecánica de referencias contra Crossref y OpenAlex.

Uso: python verificar_referencias.py <archivo .txt, .md o .docx> [--json]

Toma las líneas posteriores al último encabezado «Referencias» o
«Bibliografía» que tengan un año entre paréntesis y marca cada una como
ENCONTRADA, DUDOSA (título hallado con año distinto), NO ENCONTRADA o
SIN COMPROBAR (Crossref no respondió: límite de uso o red caída).
Libros, leyes y documentos oficiales suelen salir NO ENCONTRADA y se
comprueban contra el archivo guardado en fuentes/.

DOI que no están en Crossref (Crossref responde 404):
  - arXiv (10.48550/arXiv.<id>): se consulta la API de arXiv
    (export.arxiv.org, Atom) y se compara título y año. arXiv limita
    con 429: se reintenta con pausa; si no responde, SIN COMPROBAR. Un
    identificador que arXiv no conoce: NO ENCONTRADA.
  - Otros (DataCite: Zenodo, repositorios): se resuelve
    https://doi.org/<doi> con negociación de contenido CSL-JSON; si esa
    vía no responde (doi.org deriva a api.datacite.org, que puede estar
    bloqueado), se sigue la redirección normal de doi.org a la página
    del registro: Zenodo se lee por su API (zenodo.org/api/records/<id>)
    y las demás páginas por sus metadatos (citation_title, DC.title,
    og:title). doi.org con 404: el DOI no existe, NO ENCONTRADA. Sin
    respuesta: SIN COMPROBAR.

Variable de entorno opcional: OPENALEX_API_KEY (OpenAlex exige clave
gratuita desde 2026; sin ella solo responde Crossref).

Solo biblioteca estándar. Códigos de salida: 0 todas ENCONTRADA;
1 alguna DUDOSA o NO ENCONTRADA; 2 no se pudo ejecutar (archivo
ilegible, sin referencias, o ninguna consulta llegó a Crossref ni a
OpenAlex: red caída).
"""
import argparse
import json
import os
import re
import sys
import unicodedata
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from difflib import SequenceMatcher

AGENTE = "verificador-referencias/1.0 (uso academico)"
ENCABEZADOS = ("referencias", "bibliografia", "referencias bibliograficas")


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", texto).strip()


def pedir(url):
    cabeceras = {"User-Agent": AGENTE}
    clave = os.environ.get("OPENALEX_API_KEY", "").strip()
    if clave and "api.openalex.org" in url:  # OpenAlex exige clave gratuita desde 2026
        cabeceras["Authorization"] = f"Bearer {clave}"
    solicitud = urllib.request.Request(url, headers=cabeceras)
    for intento in range(3):  # 429 y 5xx son pasajeros: se reintenta con pausa
        try:
            respuesta = urllib.request.urlopen(solicitud, timeout=25)
            break
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or intento == 2:
                raise
            time.sleep(3 * (intento + 1))
    with respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


class DoiInexistente(Exception):
    """El registro del DOI (o de arXiv) respondió que no existe."""


class SinRespuesta(Exception):
    """El servicio no respondió (límite de uso, red, host bloqueado)."""


def pedir_bytes(url, cabeceras=None, intentos=3, pausa=3.0, limite=25):
    """GET con reintentos ante 429 y 5xx. Devuelve (bytes, url_final).
    404 o 410 -> DoiInexistente; sin respuesta útil -> SinRespuesta."""
    cab = {"User-Agent": AGENTE}
    cab.update(cabeceras or {})
    ultimo = "sin respuesta"
    for intento in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=cab),
                                        timeout=limite) as respuesta:
                return respuesta.read(), respuesta.geturl()
        except urllib.error.HTTPError as error:
            if error.code in (404, 410):
                raise DoiInexistente(f"HTTP {error.code} en {url}")
            ultimo = f"HTTP {error.code} en {url}"
            if error.code not in (429, 500, 502, 503, 504):
                break
            espera = error.headers.get("Retry-After", "") if error.headers else ""
            if intento < intentos - 1:
                time.sleep(min(float(espera), 30) if espera.isdigit() else pausa * (2 ** intento))
        except Exception as error:  # red caída, tiempo agotado, túnel rechazado
            ultimo = f"{type(error).__name__}: {error}"
            if intento < intentos - 1:
                time.sleep(pausa)
    raise SinRespuesta(ultimo)


ATOM = "{http://www.w3.org/2005/Atom}"


def en_arxiv(identificador):
    """[(título, año, doi, "arXiv")] para un identificador de arXiv: primero la
    API Atom de export.arxiv.org; si limita (429) o no responde, la página
    arxiv.org/abs/<id> y sus metadatos citation_title y citation_date."""
    try:
        return en_arxiv_api(identificador)
    except SinRespuesta as error_api:
        try:
            datos, _ = pedir_bytes("https://arxiv.org/abs/" + urllib.parse.quote(identificador),
                                   intentos=2, limite=30)
        except SinRespuesta as error_abs:
            raise SinRespuesta(f"{error_api}; {error_abs}")
        texto = datos.decode("utf-8", "replace")
        titulo = meta_html(texto, "citation_title")
        if not titulo:
            raise SinRespuesta(f"{error_api}; arxiv.org/abs sin citation_title")
        return [(titulo, anio_texto(meta_html(texto, "citation_date", "citation_online_date")),
                 "10.48550/arXiv." + identificador, "arXiv (página)")]


def en_arxiv_api(identificador):
    import xml.etree.ElementTree as ET
    url = "https://export.arxiv.org/api/query?id_list=" + urllib.parse.quote(identificador)
    datos, _ = pedir_bytes(url, intentos=3, pausa=4.0, limite=20)
    try:
        raiz = ET.fromstring(datos)
    except ET.ParseError:
        raise SinRespuesta("arXiv devolvió una respuesta que no es Atom ("
                           + datos[:60].decode("utf-8", "replace") + ")")
    salida = []
    for entrada in raiz.findall(ATOM + "entry"):
        titulo = " ".join((entrada.findtext(ATOM + "title") or "").split())
        enlace = entrada.findtext(ATOM + "id") or ""
        if not titulo or titulo.lower() == "error" or "/api/errors" in enlace:
            continue
        publicado = (entrada.findtext(ATOM + "published") or "")[:4]
        salida.append((titulo, int(publicado) if publicado.isdigit() else None,
                       "10.48550/arXiv." + identificador, "arXiv"))
    if not salida:
        raise DoiInexistente(f"arXiv no tiene el identificador {identificador}")
    return salida


def meta_html(html_texto, *nombres):
    import html
    for nombre in nombres:
        for patron in (rf'<meta[^>]+(?:name|property)=["\']{re.escape(nombre)}["\'][^>]*'
                       rf'content=["\']([^"\']+)["\']',
                       rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]*'
                       rf'(?:name|property)=["\']{re.escape(nombre)}["\']'):
            hallado = re.search(patron, html_texto, flags=re.I)
            if hallado:
                return html.unescape(hallado.group(1)).strip()
    return None


def anio_texto(texto):
    hallado = re.search(r"(1[5-9]\d\d|20\d\d)", texto or "")
    return int(hallado.group(1)) if hallado else None


def en_doi_org(doi):
    """[(título, año, doi, base)] resolviendo el DOI en doi.org."""
    quoted = urllib.parse.quote(doi, safe="/")
    try:  # 1) negociación de contenido CSL-JSON (DataCite, mEDRA, etc.)
        datos, _ = pedir_bytes("https://doi.org/" + quoted,
                               {"Accept": "application/vnd.citationstyles.csl+json"}, intentos=2)
        d = json.loads(datos.decode("utf-8"))
        partes = ((d.get("issued") or {}).get("date-parts") or [[None]])[0]
        titulo = d.get("title")
        titulo = titulo[0] if isinstance(titulo, list) and titulo else titulo
        if titulo:
            return [(titulo, partes[0] if partes else None, doi, "doi.org (CSL)")]
    except (SinRespuesta, ValueError, AttributeError):
        pass  # la negociación deriva a api.datacite.org, que puede no estar al alcance
    # 2) redirección normal a la página del registro.
    datos, final = pedir_bytes("https://doi.org/" + quoted, intentos=2)
    zenodo = re.match(r"https://zenodo\.org/(?:records|record|doi/10\.5281/zenodo\.)/?(\d+)", final)
    if zenodo:
        d, _ = pedir_bytes(f"https://zenodo.org/api/records/{zenodo.group(1)}", intentos=2)
        meta = json.loads(d.decode("utf-8")).get("metadata", {})
        return [(meta.get("title"), anio_texto(meta.get("publication_date")), doi, "Zenodo")]
    texto = datos.decode("utf-8", "replace")
    titulo = meta_html(texto, "citation_title", "DC.title", "dc.title", "og:title")
    if not titulo:
        hallado = re.search(r"<title[^>]*>(.*?)</title>", texto, flags=re.S | re.I)
        titulo = " ".join(hallado.group(1).split()) if hallado else None
    anio = anio_texto(meta_html(texto, "citation_publication_date", "citation_date",
                                "DC.date", "dc.date", "citation_online_date"))
    return [(titulo, anio, doi, "doi.org (página)")]


def leer_lineas(ruta):
    if ruta.lower().endswith(".docx"):
        import html
        xml = zipfile.ZipFile(ruta).read("word/document.xml").decode("utf-8")
        lineas = []
        for parrafo in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
            trozos = re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", parrafo, flags=re.S)
            lineas.append(html.unescape("".join(trozos)))
    else:
        with open(ruta, encoding="utf-8-sig") as archivo:
            lineas = archivo.read().splitlines()
    return [linea.strip() for linea in lineas if linea.strip()]


def leer_referencias(ruta):
    lineas = leer_lineas(ruta)
    inicio = 0
    for i, linea in enumerate(lineas):
        if normalizar(linea.lstrip("# ")) in ENCABEZADOS:
            inicio = i + 1
    candidatas = []
    for linea in lineas[inicio:]:
        # La lista termina donde empieza otro apartado (anexos, apéndices).
        if inicio and (linea.startswith("#") or normalizar(linea).startswith(("anexo", "apendice"))):
            break
        candidatas.append(linea.lstrip("-* ").strip())
    patron = re.compile(r"\((\d{4}[a-z]?|s\.\s?f\.)[^)]*\)")
    return [l for l in candidatas if len(l) > 30 and patron.search(l)]


def anio_de(ref):
    hallado = re.search(r"\((\d{4})[a-z]?[^)]*\)", ref)
    return int(hallado.group(1)) if hallado else None


def coincide(titulo, ref):
    t, r = normalizar(titulo or ""), normalizar(ref)
    if len(t) < 8:
        return False
    if t in r:
        return True
    bloque = SequenceMatcher(None, t, r, autojunk=False).find_longest_match(0, len(t), 0, len(r))
    return bloque.size / len(t) >= 0.8


def doi_de(ref):
    doi = re.search(r"10\.\d{4,9}/[^\s\"<>]+", ref)
    return doi.group(0).rstrip(".,;)") if doi else None


def en_registro(ref):
    """DOI que Crossref no tiene: arXiv o doi.org. Solo se llama tras un 404."""
    doi = doi_de(ref)
    arxiv = re.match(r"10\.48550/arxiv\.(.+)$", doi or "", flags=re.I)
    if arxiv:
        return en_arxiv(arxiv.group(1))
    return en_doi_org(doi)


def en_crossref(ref):
    limpio = doi_de(ref)
    if limpio:
        datos = [pedir("https://api.crossref.org/works/" + urllib.parse.quote(limpio))["message"]]
    else:
        consulta = urllib.parse.quote(ref[:300])
        datos = pedir("https://api.crossref.org/works?rows=3&query.bibliographic=" + consulta)["message"]["items"]
    salida = []
    for d in datos:
        partes = (d.get("issued") or {}).get("date-parts") or [[None]]
        salida.append(((d.get("title") or [""])[0], partes[0][0], d.get("DOI"), "Crossref"))
    return salida


def en_openalex(ref):
    titulo = re.search(r"\(\d{4}[a-z]?[^)]*\)\.\s*(.+?)[.?!](\s|$)", ref)
    consulta = urllib.parse.quote((titulo.group(1) if titulo else ref)[:200])
    datos = pedir("https://api.openalex.org/works?per-page=3&search=" + consulta)["results"]
    return [(d.get("title"), d.get("publication_year"), d.get("doi"), "OpenAlex") for d in datos]


def evaluar(ref):
    anio = anio_de(ref)
    dudosa, errores = None, []
    registro = None  # resultado de arXiv / doi.org: "inexistente" o "sin respuesta"
    crossref_404 = False
    for buscar in (en_crossref, en_registro, en_openalex):
        if buscar is en_registro and not (doi_de(ref) and crossref_404):
            continue  # solo para DOI que Crossref no tiene
        try:
            candidatos = buscar(ref)
        except DoiInexistente as error:
            registro = "inexistente"
            errores.append(f"{buscar.__name__}: {error}")
            continue
        except SinRespuesta as error:
            registro = "sin respuesta"
            errores.append(f"{buscar.__name__}: {error}")
            continue
        except Exception as error:  # red caída, DOI inexistente, etc.
            if buscar is en_crossref and getattr(error, "code", None) == 404:
                crossref_404 = True
            nota = ""
            if buscar is en_openalex and "401" in str(error) and not os.environ.get("OPENALEX_API_KEY"):
                nota = " (falta la variable OPENALEX_API_KEY)"
            errores.append(f"{buscar.__name__}: {error}{nota}")
            continue
        for titulo, publicado, doi, base in candidatos:
            if not coincide(titulo, ref):
                continue
            detalle = f"{base} | {publicado} | {doi or 'sin DOI'} | {titulo}"
            if anio is None or publicado is None or abs(publicado - anio) <= 1:
                return "ENCONTRADA", detalle, len(errores)
            dudosa = dudosa or f"año distinto ({anio} en la referencia) | {detalle}"
    if dudosa:
        return "DUDOSA", dudosa, len(errores)
    # Si Crossref no llegó a responder (límite de uso, caída, sin red), la
    # referencia no quedó comprobada: decir "no encontrada" sería falso.
    pasajero = any(e.startswith("en_crossref") and " 404" not in e for e in errores)
    # DOI fuera de Crossref (arXiv, DataCite) cuyo registro no respondió: no
    # quedó comprobada; tampoco es "no encontrada" por un 429 de arXiv.
    pasajero = pasajero or registro == "sin respuesta"
    if pasajero:
        return "SIN COMPROBAR", "; ".join(errores), len(errores)
    return ("NO ENCONTRADA", "; ".join(errores) or "sin coincidencia de título en Crossref ni OpenAlex",
            len(errores))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("archivo", help="archivo .txt, .md o .docx con la lista de referencias")
    analizador.add_argument("--json", action="store_true")
    args = analizador.parse_args()
    try:
        referencias = leer_referencias(args.archivo)
    except (OSError, KeyError, UnicodeDecodeError, zipfile.BadZipFile) as error:
        print(f"No se pudo leer el archivo: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(2)
    if not referencias:
        print("No se hallaron referencias en el archivo.", file=sys.stderr)
        sys.exit(2)
    conteo = {"ENCONTRADA": 0, "DUDOSA": 0, "NO ENCONTRADA": 0, "SIN COMPROBAR": 0}
    resultados, sin_red = [], 0
    for numero, ref in enumerate(referencias, 1):
        estado, detalle, fallos = evaluar(ref)
        conteo[estado] += 1
        sin_red += fallos == 2
        resultados.append({"numero": numero, "estado": estado, "referencia": ref,
                           "detalle": detalle})
        if not args.json:
            print(f"[{numero}] {estado}\n    {ref[:160]}\n    -> {detalle}\n")
    red_caida = sin_red == len(referencias)
    if args.json:
        print(json.dumps({"archivo": args.archivo, "conteo": conteo, "red_caida": red_caida,
                          "referencias": resultados}, ensure_ascii=False, indent=2))
    else:
        print("RESUMEN:", ", ".join(f"{k}: {v}" for k, v in conteo.items()))
        if red_caida:
            print("No se pudo consultar Crossref ni OpenAlex (red caída): nada quedó verificado.",
                  file=sys.stderr)
    if red_caida:
        sys.exit(2)
    sys.exit(0 if conteo["ENCONTRADA"] == len(referencias) else 1)


if __name__ == "__main__":
    main()
