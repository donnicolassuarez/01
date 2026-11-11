# -*- coding: utf-8 -*-
"""Funciones compartidas por los scripts de la skill niveles-academicos.

Solo biblioteca estándar. Los demás scripts lo importan con
`import comun` (están en la misma carpeta).

Variables de entorno opcionales:
  AGENTE_ACADEMICO_CORREO  correo de contacto para Crossref y Unpaywall.
                           Sin él, Unpaywall no se consulta.
  OPENALEX_API_KEY         clave gratuita de OpenAlex.
  S2_API_KEY               clave de Semantic Scholar.
  SOFFICE                  ruta de LibreOffice si no está en el PATH.
"""
import html
import json
import os
import re
import shutil
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile

AGENTE = "agente-academico/1.0 (herramienta de investigacion academica)"
ENCABEZADOS_REFERENCIAS = (
    "referencias", "bibliografia", "referencias bibliograficas",
    "fuentes", "fuentes consultadas", "bibliografia consultada",
)
MARCA_PAGINA = "=== [p. {n}] ==="
PATRON_MARCA_PAGINA = re.compile(r"^=== \[p\. (\d+)\] ===$")
RUTAS_SOFFICE = (
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/usr/bin/soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
)


class ErrorRed(Exception):
    """Fallo de red ya reintentado; el mensaje dice la causa."""


def salida_utf8():
    """Evita errores de codificación al imprimir en la consola de Windows."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def normalizar(texto):
    """Minúsculas, sin tildes ni signos; espacios simples."""
    texto = unicodedata.normalize("NFKD", (texto or "").lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", texto)).strip()


def correo_contacto():
    return os.environ.get("AGENTE_ACADEMICO_CORREO", "").strip()


def pedir(url, cabeceras=None, intentos=3, espera=2.0, limite=60):
    """GET con reintentos ante 429 y 5xx. Devuelve (bytes, url_final, tipo).

    Lanza ErrorRed con el código y el motivo si no hubo respuesta útil.
    """
    cab = {"User-Agent": AGENTE, "Accept": "*/*"}
    cab.update(cabeceras or {})
    ultimo = "sin respuesta"
    for intento in range(intentos):
        try:
            solicitud = urllib.request.Request(url, headers=cab)
            with urllib.request.urlopen(solicitud, timeout=limite) as resp:
                tipo = resp.headers.get("Content-Type", "")
                return resp.read(), resp.geturl(), tipo
        except urllib.error.HTTPError as error:
            cuerpo = error.read(300).decode("utf-8", "replace")
            ultimo = f"HTTP {error.code}: {cuerpo.strip()[:200]}"
            if error.code not in (429, 500, 502, 503, 504):
                break
            pausa = error.headers.get("Retry-After", "")
            time.sleep(min(float(pausa), 30) if pausa.isdigit() else espera * (2 ** intento))
        except Exception as error:  # red caída, tiempo agotado, TLS
            ultimo = f"{type(error).__name__}: {error}"
            time.sleep(espera * (2 ** intento))
    raise ErrorRed(ultimo)


def pedir_json(url, cabeceras=None, **opciones):
    datos, _, _ = pedir(url, cabeceras, **opciones)
    return json.loads(datos.decode("utf-8"))


def limpiar_doi(texto):
    """Extrae un DOI de una cadena o URL; None si no hay."""
    hallado = re.search(r"10\.\d{4,9}/[^\s\"<>]+", texto or "")
    return hallado.group(0).rstrip(".,;)").lower() if hallado else None


def leer_parrafos(ruta):
    """Párrafos no vacíos de un .docx, .md o .txt, en orden."""
    ruta = str(ruta)
    if ruta.lower().endswith(".docx"):
        with zipfile.ZipFile(ruta) as paquete:
            xml = paquete.read("word/document.xml").decode("utf-8")
        parrafos = []
        for parrafo in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
            trozos = re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", parrafo, flags=re.S)
            parrafos.append(html.unescape("".join(trozos)))
    else:
        with open(ruta, encoding="utf-8-sig") as archivo:
            parrafos = archivo.read().splitlines()
    return [p.strip() for p in parrafos if p.strip()]


def es_encabezado_referencias(parrafo):
    return normalizar(parrafo.lstrip("# ").strip("*_ ")) in ENCABEZADOS_REFERENCIAS


def separar_referencias(parrafos):
    """Divide en (cuerpo, referencias) por el último encabezado de referencias.

    Si no hay encabezado, todo es cuerpo y la lista de referencias va vacía.
    Las referencias terminan donde empieza otro encabezado (anexos, etc.).
    """
    inicio = None
    for i, parrafo in enumerate(parrafos):
        if es_encabezado_referencias(parrafo):
            inicio = i
    if inicio is None:
        return list(parrafos), []
    referencias = []
    for parrafo in parrafos[inicio + 1:]:
        if parrafo.startswith("#") or normalizar(parrafo).startswith(("anexo", "apendice")):
            break
        referencias.append(parrafo.lstrip("-* ").strip())
    return list(parrafos[:inicio]), [r for r in referencias if r]


def leer_texto_paginado(ruta):
    """Lee un .txt de extraer_texto.py y devuelve [(pagina, texto), ...]."""
    paginas, numero, lineas = [], None, []
    with open(ruta, encoding="utf-8") as archivo:
        for linea in archivo.read().splitlines():
            marca = PATRON_MARCA_PAGINA.match(linea.strip())
            if marca:
                if numero is not None:
                    paginas.append((numero, "\n".join(lineas)))
                numero, lineas = int(marca.group(1)), []
            else:
                lineas.append(linea)
    if numero is not None:
        paginas.append((numero, "\n".join(lineas)))
    return paginas


def ruta_soffice():
    """Ruta de LibreOffice o None. No depende del PATH de Windows."""
    candidata = os.environ.get("SOFFICE", "").strip()
    if candidata and os.path.exists(candidata):
        return candidata
    for nombre in ("soffice", "libreoffice"):
        hallada = shutil.which(nombre)
        if hallada:
            return hallada
    for candidata in RUTAS_SOFFICE:
        if os.path.exists(candidata):
            return candidata
    return None
