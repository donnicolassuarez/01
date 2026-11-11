# -*- coding: utf-8 -*-
"""Verificación mecánica de referencias contra Crossref y OpenAlex.

Uso: python verificar_referencias.py <archivo .txt, .md o .docx> [--json]

Toma las líneas posteriores al último encabezado «Referencias» o
«Bibliografía» que tengan un año entre paréntesis y marca cada una como
ENCONTRADA, DUDOSA (título hallado con año distinto) o NO ENCONTRADA.
Libros, leyes y documentos oficiales suelen salir NO ENCONTRADA y se
comprueban contra el archivo guardado en fuentes/.

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
    with urllib.request.urlopen(solicitud, timeout=25) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


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


def en_crossref(ref):
    doi = re.search(r"10\.\d{4,9}/[^\s\"<>]+", ref)
    if doi:
        limpio = doi.group(0).rstrip(".,;)")
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
    for buscar in (en_crossref, en_openalex):
        try:
            candidatos = buscar(ref)
        except Exception as error:  # red caída, DOI inexistente, etc.
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
    conteo = {"ENCONTRADA": 0, "DUDOSA": 0, "NO ENCONTRADA": 0}
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
