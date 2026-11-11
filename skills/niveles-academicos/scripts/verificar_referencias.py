# -*- coding: utf-8 -*-
"""Verificación mecánica de referencias contra Crossref y OpenAlex.

Uso: python verificar_referencias.py <archivo .txt, .md o .docx>
Solo biblioteca estándar. Devuelve código 1 si alguna referencia
queda DUDOSA o NO ENCONTRADA.
"""
import json
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
    solicitud = urllib.request.Request(url, headers={"User-Agent": AGENTE})
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
    candidatas = [l.lstrip("-* ").strip() for l in lineas[inicio:]]
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
            errores.append(f"{buscar.__name__}: {error}")
            continue
        for titulo, publicado, doi, base in candidatos:
            if not coincide(titulo, ref):
                continue
            detalle = f"{base} | {publicado} | {doi or 'sin DOI'} | {titulo}"
            if anio is None or publicado is None or abs(publicado - anio) <= 1:
                return "ENCONTRADA", detalle
            dudosa = dudosa or f"año distinto ({anio} en la referencia) | {detalle}"
    if dudosa:
        return "DUDOSA", dudosa
    return "NO ENCONTRADA", "; ".join(errores) or "sin coincidencia de título en Crossref ni OpenAlex"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.stdout.reconfigure(encoding="utf-8")
    referencias = leer_referencias(sys.argv[1])
    if not referencias:
        sys.exit("No se hallaron referencias en el archivo.")
    conteo = {"ENCONTRADA": 0, "DUDOSA": 0, "NO ENCONTRADA": 0}
    for numero, ref in enumerate(referencias, 1):
        estado, detalle = evaluar(ref)
        conteo[estado] += 1
        print(f"[{numero}] {estado}\n    {ref[:160]}\n    -> {detalle}\n")
    print("RESUMEN:", ", ".join(f"{k}: {v}" for k, v in conteo.items()))
    sys.exit(0 if conteo["ENCONTRADA"] == len(referencias) else 1)


if __name__ == "__main__":
    main()
