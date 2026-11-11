# -*- coding: utf-8 -*-
"""Descarga la versión de acceso abierto (PDF) de una o varias fuentes.

Uso:
  python descargar_abierto.py <DOI | archivo .txt con DOIs | JSON de buscar_academico.py>
         --carpeta <trabajo>/fuentes [--json]

Orígenes, en este orden (se pasa al siguiente si uno falla o no da un PDF):
  1. enlace_abierto ya conocido (si la entrada es el JSON del buscador);
  2. Unpaywall, solo si existe AGENTE_ACADEMICO_CORREO (si no, se omite y
     se dice);
  3. OpenAlex (best_oa_location, open_access.oa_url y demás locations);
     usa OPENALEX_API_KEY como en buscar_academico.py;
  4. Crossref (campo link con content-type application/pdf);
  5. arXiv, si el DOI es 10.48550/arXiv.*;
  6. la página de destino de https://doi.org/<doi>, buscando la etiqueta
     meta citation_pdf_url (SciELO, Redalyc, OJS...).
Si un origen devuelve una página HTML, también se busca en ella
citation_pdf_url antes de pasar al siguiente.

Un archivo solo se acepta si empieza por %PDF y pesa al menos 5 KB.
Se guarda como apellido_anio_slug-del-titulo.pdf (ASCII, minúsculas,
máx. 80 caracteres) y se registra en <carpeta>/indice.json (escritura
atómica). No se descarga de nuevo si el DOI ya está en el índice y su
archivo existe. Lo que no se pudo obtener se anota en
<carpeta>/descartadas.md, una línea por DOI con el motivo concreto; si
más tarde se obtiene, su línea se retira.

Códigos de salida: 0 todo obtenido o ya existente; 1 alguna descartada;
2 no se pudo ejecutar (entrada ilegible, carpeta imposible).
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import comun

TAMANO_MINIMO = 5 * 1024
ACEPTAR = {"Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8"}
PATRON_META_PDF = re.compile(
    r"<meta\s+[^>]*?(?:name|property)\s*=\s*[\"']citation_pdf_url[\"'][^>]*>", re.I)
PATRON_CONTENT = re.compile(r"content\s*=\s*[\"']([^\"']+)[\"']", re.I)
# Páginas de verificación antibots: se informan y no se intenta saltarlas.
SENALES_ANTIBOTS = (b"bunny-shield", b"just a moment...", b"challenge-platform",
                    b"cf-chl", b"<title>access denied</title>", b"captcha", b"bm-verify")


# ------------------------------------------------------------ entrada

def leer_entrada(argumento):
    """Devuelve lista de dicts {doi, titulo, autores, anio, enlace_abierto}."""
    ruta = Path(argumento)
    if ruta.is_file():
        texto = ruta.read_text(encoding="utf-8-sig")
        if ruta.suffix.lower() == ".json" or texto.lstrip().startswith(("{", "[")):
            datos = json.loads(texto)
            lista = datos.get("resultados", []) if isinstance(datos, dict) else datos
            salida = []
            for item in lista:
                if isinstance(item, str):
                    item = {"doi": item}
                salida.append({"doi": comun.limpiar_doi(item.get("doi") or ""),
                               "titulo": item.get("titulo"), "autores": item.get("autores") or [],
                               "anio": item.get("anio"), "enlace_abierto": item.get("enlace_abierto")})
            return salida
        salida = []
        for linea in texto.splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            salida.append({"doi": comun.limpiar_doi(linea), "texto_original": linea})
        return salida
    doi = comun.limpiar_doi(argumento)
    if not doi:
        raise ValueError(f"no es un DOI ni un archivo existente: {argumento}")
    return [{"doi": doi}]


# ----------------------------------------------------------- utilidades

def ascii_slug(texto, maximo=60):
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = texto.encode("ascii", "ignore").decode("ascii").lower()
    texto = re.sub(r"[^a-z0-9]+", "-", texto).strip("-")
    if len(texto) > maximo:
        texto = texto[:maximo].rsplit("-", 1)[0] or texto[:maximo]
    return texto


def nombre_archivo(fuente, carpeta):
    apellido = ""
    if fuente.get("autores"):
        apellido = ascii_slug(str(fuente["autores"][0]).split(",")[0], 20)
    titulo = ascii_slug(fuente.get("titulo") or "", 80)
    if fuente.get("titulo"):
        partes = [p for p in (apellido, str(fuente.get("anio") or "sf"), titulo) if p]
        base = "_".join(partes)[:80].rstrip("-_")
    else:
        base = ascii_slug(fuente.get("doi") or "sin-doi", 80)
    candidato, n = base, 2
    while (carpeta / f"{candidato}.pdf").exists():  # otro DOI ya usa ese nombre
        candidato, n = f"{base[:76]}-{n}", n + 1
    return f"{candidato}.pdf"


def es_pdf(datos):
    return len(datos) >= TAMANO_MINIMO and b"%PDF" in datos[:1024]


def pdf_en_html(datos, url_base):
    """URL de citation_pdf_url en una página HTML, o None."""
    texto = datos[:400000].decode("utf-8", "replace")
    etiqueta = PATRON_META_PDF.search(texto)
    if not etiqueta:
        return None
    contenido = PATRON_CONTENT.search(etiqueta.group(0))
    if not contenido:
        return None
    return urllib.parse.urljoin(url_base, html.unescape(contenido.group(1).strip()))


def cabeceras_openalex():
    clave = os.environ.get("OPENALEX_API_KEY", "").strip()
    return {"Authorization": f"Bearer {clave}"} if clave else {}


# --------------------------------------------------------------- metadatos

def completar_metadatos(fuente, notas):
    """Rellena título, autores y año desde Crossref (o arXiv) si faltan."""
    if fuente.get("titulo") and fuente.get("autores") and fuente.get("anio"):
        return
    doi = fuente["doi"]
    try:
        if doi.startswith("10.48550/arxiv."):
            identificador = doi.split("arxiv.", 1)[1]
            datos, _, _ = comun.pedir("https://export.arxiv.org/api/query?id_list="
                                      + urllib.parse.quote(identificador), espera=3.0)
            ns = {"a": "http://www.w3.org/2005/Atom"}
            entrada = ET.fromstring(datos).find("a:entry", ns)
            if entrada is None:
                return
            fuente.setdefault("titulo", None)
            fuente["titulo"] = fuente["titulo"] or re.sub(r"\s+", " ", entrada.findtext("a:title", "", ns)).strip()
            if not fuente.get("autores"):
                nombres = [a.findtext("a:name", "", ns).split() for a in entrada.findall("a:author", ns)]
                fuente["autores"] = [f"{n[-1]}, " + " ".join(p[0] + "." for p in n[:-1]) for n in nombres if n]
            publicado = entrada.findtext("a:published", "", ns)
            fuente["anio"] = fuente.get("anio") or (int(publicado[:4]) if publicado[:4].isdigit() else None)
            return
        obra = comun.pedir_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]
        fuente["_crossref"] = obra
        fuente["titulo"] = fuente.get("titulo") or (obra.get("title") or [None])[0]
        if not fuente.get("autores"):
            fuente["autores"] = [f"{a.get('family')}, " + " ".join(p[0] + "." for p in (a.get("given") or "").split() if p)
                                 for a in obra.get("author") or [] if a.get("family")]
        partes = ((obra.get("issued") or {}).get("date-parts") or [[None]])[0]
        fuente["anio"] = fuente.get("anio") or (partes[0] if partes else None)
    except comun.ErrorRed as error:
        notas.append(f"metadatos no disponibles ({breve(error)})")
    except Exception as error:
        notas.append(f"metadatos no disponibles ({type(error).__name__}: {error})")


# ------------------------------------------------------------- orígenes

def origen_conocido(fuente):
    return [fuente["enlace_abierto"]] if fuente.get("enlace_abierto") else []


def origen_unpaywall(fuente):
    correo = comun.correo_contacto()
    if not correo:
        raise LookupError("omitido: falta AGENTE_ACADEMICO_CORREO")
    datos = comun.pedir_json(f"https://api.unpaywall.org/v2/{urllib.parse.quote(fuente['doi'])}?"
                             + urllib.parse.urlencode({"email": correo}))
    urls = []
    for ubicacion in [datos.get("best_oa_location")] + list(datos.get("oa_locations") or []):
        if ubicacion:
            urls += [ubicacion.get("url_for_pdf"), ubicacion.get("url")]
    return urls


def origen_openalex(fuente):
    obra = comun.pedir_json("https://api.openalex.org/works/doi:" + urllib.parse.quote(fuente["doi"]),
                            cabeceras_openalex())
    mejor = obra.get("best_oa_location") or {}
    urls = [mejor.get("pdf_url"), (obra.get("open_access") or {}).get("oa_url"), mejor.get("landing_page_url")]
    for ubicacion in obra.get("locations") or []:
        if ubicacion.get("is_oa"):
            urls.append(ubicacion.get("pdf_url"))
    return urls


def origen_crossref(fuente):
    obra = fuente.get("_crossref")
    if obra is None:
        obra = comun.pedir_json("https://api.crossref.org/works/" + urllib.parse.quote(fuente["doi"]))["message"]
    enlaces = obra.get("link") or []
    return ([l.get("URL") for l in enlaces if l.get("content-type") == "application/pdf"]
            + [l.get("URL") for l in enlaces if l.get("content-type") == "unspecified"])


def origen_arxiv(fuente):
    if not fuente["doi"].startswith("10.48550/arxiv."):
        return []
    return ["https://arxiv.org/pdf/" + fuente["doi"].split("arxiv.", 1)[1]]


def origen_doi(fuente):
    return ["https://doi.org/" + fuente["doi"]]


ORIGENES = (("enlace conocido", origen_conocido), ("Unpaywall", origen_unpaywall),
            ("OpenAlex", origen_openalex), ("Crossref", origen_crossref),
            ("arXiv", origen_arxiv), ("doi.org", origen_doi))


def es_antibots(datos):
    inicio = datos[:6000].lower()
    return any(senal in inicio for senal in SENALES_ANTIBOTS)


def con_https(url):
    """Un enlace http:// se prueba primero como https:// y luego tal cual."""
    return ["https://" + url[7:], url] if url.startswith("http://") else [url]


def breve(texto, maximo=160):
    return re.sub(r"\s+", " ", str(texto)).strip()[:maximo]


def intentar_url(url, intentos_hechos):
    """Devuelve (bytes_pdf, url_final) o (None, motivo). Sigue un citation_pdf_url."""
    pendientes, vistos, motivos = con_https(url), set(), []
    while pendientes:
        actual = pendientes.pop(0)
        if actual in vistos or actual in intentos_hechos:
            continue
        vistos.add(actual)
        intentos_hechos.add(actual)
        try:
            datos, final, tipo = comun.pedir(actual, ACEPTAR, intentos=2, espera=2.0, limite=90)
        except comun.ErrorRed as error:
            if es_antibots(str(error).encode()):
                motivos.append(f"{actual}: verificación antibots del sitio (no se fuerza)")
            else:
                motivos.append(f"{actual}: {breve(error)}")
            continue
        if es_pdf(datos):
            return datos, final
        if b"%PDF" in datos[:1024]:
            motivos.append(f"{actual}: PDF demasiado pequeño ({len(datos)} bytes)")
        elif es_antibots(datos):
            motivos.append(f"{actual}: verificación antibots del sitio (no se fuerza)")
        else:
            es_html = "html" in tipo.lower() or b"<html" in datos[:2000].lower()
            siguiente = pdf_en_html(datos, final) if es_html else None
            if siguiente and len(vistos) < 5:
                pendientes += con_https(siguiente)
            else:
                motivos.append(f"{actual}: no es PDF ({tipo.split(';')[0] or 'tipo desconocido'}, "
                               f"{len(datos)} bytes, sin citation_pdf_url)")
    if not motivos:
        motivos.append(f"{url}: ya probado")
    return None, " / ".join(motivos)


def obtener(fuente):
    """Prueba los orígenes en orden. Devuelve (bytes, url, origen, notas)."""
    notas, hechos = [], set()
    for nombre, funcion in ORIGENES:
        try:
            urls = [u for u in funcion(fuente) if u]
        except LookupError as aviso:
            notas.append(f"{nombre}: {aviso}")
            continue
        except comun.ErrorRed as error:
            notas.append(f"{nombre}: {breve(error)}")
            continue
        except Exception as error:
            notas.append(f"{nombre}: {type(error).__name__}: {error}")
            continue
        if not urls:
            if funcion not in (origen_arxiv, origen_conocido):
                notas.append(f"{nombre}: sin enlace abierto")
            continue
        for url in dict.fromkeys(urls):
            datos, resultado = intentar_url(url, hechos)
            if datos:
                return datos, resultado, nombre, notas
            if not resultado.endswith("ya probado"):
                notas.append(f"{nombre}: {resultado}")
    return None, None, None, notas


# ------------------------------------------------------- índice y descartes

def cargar_indice(ruta):
    if not ruta.exists():
        return []
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return datos if isinstance(datos, list) else []
    except json.JSONDecodeError as error:
        raise RuntimeError(f"indice.json ilegible ({error}); no se sobrescribe") from error


def actualizar_descartadas(ruta, nuevas, obtenidos):
    """nuevas: {doi: linea}. Quita las líneas de DOI ya obtenidos; no duplica."""
    lineas = ruta.read_text(encoding="utf-8").splitlines() if ruta.exists() else []
    if not lineas:
        lineas = ["# Fuentes descartadas", "",
                  "Una línea por fuente: DOI | título | motivo.", ""]
    salida = []
    for linea in lineas:
        doi = comun.limpiar_doi(linea) if linea.startswith("- ") else None
        if doi and (doi in nuevas or doi in obtenidos):
            continue  # se reemplaza por la línea nueva o ya se obtuvo
        salida.append(linea)
    salida += list(nuevas.values())
    comun.escribir_atomico(ruta, "\n".join(salida).rstrip("\n") + "\n")


def motivo_resumido(notas):
    utiles = [n for n in notas if "omitido" not in n]
    texto = "; ".join(utiles or notas) or "sin enlace abierto en ningún origen"
    return re.sub(r"\s+", " ", texto)[:900]


# --------------------------------------------------------------------- main

def main():
    comun.salida_utf8()
    analizador = argparse.ArgumentParser(description="Descarga PDF de acceso abierto por DOI.")
    analizador.add_argument("entrada", help="DOI, archivo con DOIs o JSON de buscar_academico.py")
    analizador.add_argument("--carpeta", required=True, help="carpeta fuentes/ del trabajo")
    analizador.add_argument("--json", action="store_true")
    opciones = analizador.parse_args()

    try:
        fuentes = leer_entrada(opciones.entrada)
        carpeta = Path(opciones.carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta_indice = carpeta / "indice.json"
        indice = cargar_indice(ruta_indice)
    except (ValueError, OSError, RuntimeError, json.JSONDecodeError) as error:
        print(f"No se pudo ejecutar: {error}", file=sys.stderr)
        sys.exit(2)

    por_doi = {e.get("doi"): e for e in indice if e.get("doi")}
    informe = {"descargadas": [], "ya_existentes": [], "descartadas": []}
    descartes, obtenidos = {}, set()
    vistos = set()
    for fuente in fuentes:
        doi = fuente.get("doi")
        if not doi:
            linea = fuente.get("texto_original") or fuente.get("titulo") or "(entrada vacía)"
            informe["descartadas"].append({"doi": None, "titulo": fuente.get("titulo"),
                                           "motivo": f"sin DOI reconocible: {linea}"})
            continue
        if doi in vistos:
            continue
        vistos.add(doi)
        previa = por_doi.get(doi)
        if previa and (carpeta / previa.get("archivo", "")).is_file():
            informe["ya_existentes"].append({"doi": doi, "archivo": previa["archivo"]})
            obtenidos.add(doi)
            continue

        notas = []
        completar_metadatos(fuente, notas)
        datos, url, origen, notas_origen = obtener(fuente)
        notas += notas_origen
        if not datos:
            motivo = motivo_resumido(notas)
            titulo = fuente.get("titulo") or "título desconocido"
            descartes[doi] = f"- {doi} | {titulo} | {motivo}"
            informe["descartadas"].append({"doi": doi, "titulo": fuente.get("titulo"), "motivo": motivo})
            continue

        archivo = previa.get("archivo") if previa else None
        if not archivo:
            archivo = nombre_archivo(fuente, carpeta)
        comun.escribir_atomico(carpeta / archivo, datos)
        entrada = {"doi": doi, "titulo": fuente.get("titulo"), "autores": fuente.get("autores") or [],
                   "anio": fuente.get("anio"), "archivo": archivo, "url_origen": url, "origen": origen,
                   "sha256": hashlib.sha256(datos).hexdigest(),
                   "fecha": datetime.now().astimezone().isoformat(timespec="seconds")}
        if previa:
            indice[indice.index(previa)] = entrada
        else:
            indice.append(entrada)
        por_doi[doi] = entrada
        obtenidos.add(doi)
        # se guarda el índice tras cada descarga: un corte no pierde lo hecho
        comun.escribir_atomico(ruta_indice, json.dumps(indice, ensure_ascii=False, indent=2) + "\n")
        informe["descargadas"].append({"doi": doi, "archivo": archivo, "origen": origen,
                                       "url": url, "bytes": len(datos)})

    if descartes or obtenidos:
        actualizar_descartadas(carpeta / "descartadas.md", descartes, obtenidos)
    if not comun.correo_contacto():
        informe["aviso"] = "Unpaywall omitido: no hay AGENTE_ACADEMICO_CORREO."

    if opciones.json:
        print(json.dumps(informe, ensure_ascii=False, indent=2))
    else:
        for d in informe["descargadas"]:
            print(f"DESCARGADA  {d['doi']} -> {d['archivo']} ({d['origen']}, {d['bytes'] // 1024} KB)")
        for d in informe["ya_existentes"]:
            print(f"YA EXISTE   {d['doi']} -> {d['archivo']}")
        for d in informe["descartadas"]:
            print(f"DESCARTADA  {d['doi'] or '-'} | {d['titulo'] or '-'}\n            motivo: {d['motivo']}")
        if informe.get("aviso"):
            print(informe["aviso"])
        print(f"\nRESUMEN: descargadas {len(informe['descargadas'])}, ya existentes "
              f"{len(informe['ya_existentes'])}, descartadas {len(informe['descartadas'])}.")
    sys.exit(1 if informe["descartadas"] else 0)


if __name__ == "__main__":
    main()
