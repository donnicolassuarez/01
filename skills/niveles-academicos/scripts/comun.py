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
            if error.code not in (429, 500, 502, 503, 504) or intento == intentos - 1:
                break
            pausa = error.headers.get("Retry-After", "")
            time.sleep(min(float(pausa), 30) if pausa.isdigit() else espera * (2 ** intento))
        except Exception as error:  # red caída, tiempo agotado, TLS
            ultimo = f"{type(error).__name__}: {error}"
            if intento < intentos - 1:
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
    """Ruta de LibreOffice o None. No depende del PATH de Windows.

    SOFFICE=ninguno (o "no", "0") desactiva la búsqueda: sirve para
    probar el comportamiento sin LibreOffice.
    """
    candidata = os.environ.get("SOFFICE", "").strip()
    if candidata.lower() in ("ninguno", "no", "0", "none"):
        return None
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


def escribir_atomico(ruta, contenido):
    """Escribe texto (str) o bytes en `ruta` vía temporal + reemplazo.

    Si el proceso se corta a mitad, el archivo anterior queda intacto.
    """
    import tempfile
    ruta = os.fspath(ruta)
    carpeta = os.path.dirname(os.path.abspath(ruta))
    os.makedirs(carpeta, exist_ok=True)
    binario = isinstance(contenido, (bytes, bytearray))
    descriptor, temporal = tempfile.mkstemp(dir=carpeta, prefix=".tmp_", suffix=".parcial")
    try:
        if binario:
            with os.fdopen(descriptor, "wb") as archivo:
                archivo.write(contenido)
        else:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as archivo:
                archivo.write(contenido)
        os.replace(temporal, ruta)
    except BaseException:
        try:
            os.remove(temporal)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Render a PDF y medición (compartido por construir_docx.py y
# verificar_formato.py). PyMuPDF es la única dependencia externa y se
# importa solo al medir.

PUNTOS_POR_CM = 72 / 2.54


class ErrorRender(Exception):
    """No se pudo convertir a PDF; el mensaje dice la causa."""


def importar_pymupdf():
    """Devuelve el módulo PyMuPDF (nombre nuevo `pymupdf` o el antiguo `fitz`)."""
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf
    return pymupdf


def renderizar_pdf(ruta_docx, carpeta_salida, limite=240):
    """Convierte un .docx a PDF con LibreOffice y devuelve la ruta del PDF.

    Trabaja sobre una copia con nombre simple en una carpeta temporal y
    con un perfil de usuario temporal, para no chocar con otra instancia
    de LibreOffice abierta. Lanza ErrorRender si no hay LibreOffice, si
    se agota el tiempo o si no sale el PDF.
    """
    import subprocess
    import tempfile
    from pathlib import Path

    soffice = ruta_soffice()
    if not soffice:
        raise ErrorRender("LibreOffice no encontrado (ni SOFFICE, ni PATH, "
                          "ni rutas habituales)")
    origen = Path(ruta_docx)
    destino = Path(carpeta_salida) / (origen.stem + ".pdf")
    with tempfile.TemporaryDirectory(prefix="agac_render_") as temporal:
        temporal = Path(temporal)
        entrada = temporal / "documento.docx"
        shutil.copyfile(origen, entrada)
        perfil = (temporal / "perfil").resolve().as_uri()
        orden = [soffice, f"-env:UserInstallation={perfil}", "--headless",
                 "--norestore", "--nolockcheck", "--convert-to", "pdf",
                 "--outdir", str(temporal / "pdf"), str(entrada)]
        try:
            resultado = subprocess.run(orden, capture_output=True,
                                       timeout=limite)
        except subprocess.TimeoutExpired:
            raise ErrorRender(f"LibreOffice no terminó en {limite} s")
        except OSError as error:
            raise ErrorRender(f"no se pudo ejecutar LibreOffice: {error}")
        pdf = temporal / "pdf" / "documento.pdf"
        if not pdf.exists():
            detalle = (resultado.stderr or resultado.stdout or b"")
            detalle = detalle.decode("utf-8", "replace").strip()[:300]
            raise ErrorRender(f"LibreOffice no produjo el PDF "
                              f"(código {resultado.returncode}) {detalle}")
        Path(carpeta_salida).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pdf, destino)
    return destino


def medir_pdf(ruta_pdf):
    """Páginas de un PDF: lista de dicts {ancho_cm, alto_cm, texto}."""
    pymupdf = importar_pymupdf()
    paginas = []
    with pymupdf.open(str(ruta_pdf)) as documento:
        for pagina in documento:
            paginas.append({
                "ancho_cm": round(pagina.rect.width / PUNTOS_POR_CM, 2),
                "alto_cm": round(pagina.rect.height / PUNTOS_POR_CM, 2),
                "texto": pagina.get_text("text"),
            })
    return paginas


def paginas_seccion_pdf(ruta_pdf, encabezados=ENCABEZADOS_REFERENCIAS,
                        margen_sup_cm=2.54, margen_inf_cm=2.54,
                        siguiente=None):
    """Páginas (fracción) que ocupa una sección en el PDF, o None.

    La sección empieza en la última línea cuyo texto normalizado está en
    `encabezados` y termina en la línea `siguiente` (texto del encabezado
    que la sigue, si lo hay) o en la última línea de texto del documento.
    Las líneas del pie de página (bajo el margen inferior) no cuentan.
    La fracción se calcula sobre el alto útil (página menos márgenes).
    """
    pymupdf = importar_pymupdf()
    objetivos = {normalizar(e) for e in encabezados}
    with pymupdf.open(str(ruta_pdf)) as documento:
        lineas = []  # (pagina, y0, y1, texto normalizado)
        for numero, pagina in enumerate(documento):
            limite = pagina.rect.height - margen_inf_cm * PUNTOS_POR_CM
            for bloque in pagina.get_text("dict")["blocks"]:
                for linea in bloque.get("lines", []):
                    texto = "".join(s["text"] for s in linea["spans"]).strip()
                    y0, y1 = linea["bbox"][1], linea["bbox"][3]
                    if texto and y0 < limite:
                        lineas.append((numero, y0, y1, normalizar(texto)))
        if not lineas:
            return None
        alto = documento[0].rect.height
    inicio = None
    for i, linea in enumerate(lineas):
        if linea[3] in objetivos:
            inicio = i
    if inicio is None:
        return None
    fin = None
    if siguiente:
        buscado = normalizar(siguiente)
        for k in range(inicio + 1, len(lineas)):
            if lineas[k][3] == buscado:
                # Termina en la última línea anterior al encabezado siguiente
                # (puede estar en otra página si hubo un salto).
                previa = lineas[k - 1]
                fin = (previa[0], previa[2])
                break
    if fin is None:
        ultima = lineas[-1]
        fin = (ultima[0], ultima[2])
    tope = margen_sup_cm * PUNTOS_POR_CM
    util = alto - (margen_sup_cm + margen_inf_cm) * PUNTOS_POR_CM
    pagina0, y0 = lineas[inicio][0], lineas[inicio][1]
    pagina1, y1 = fin
    if pagina0 == pagina1:
        return round((y1 - y0) / util, 2)
    fraccion = (alto - margen_inf_cm * PUNTOS_POR_CM - y0) / util
    fraccion += (pagina1 - pagina0 - 1) + (y1 - tope) / util
    return round(fraccion, 2)


def tras_referencias(parrafos):
    """Párrafos que siguen a la lista de referencias (anexos, apéndices).

    Complementa a separar_referencias: cuerpo + referencias + esto = todo.
    Lista vacía si no hay encabezado de referencias o nada lo sigue.
    """
    inicio = None
    for i, parrafo in enumerate(parrafos):
        if es_encabezado_referencias(parrafo):
            inicio = i
    if inicio is None:
        return []
    for j in range(inicio + 1, len(parrafos)):
        parrafo = parrafos[j]
        if parrafo.startswith("#") or normalizar(parrafo).startswith(("anexo", "apendice")):
            return list(parrafos[j:])
    return []


def leer_bloques(ruta):
    """Como leer_parrafos, pero en .md y .txt une las líneas de un mismo
    párrafo (separados por líneas en blanco). Encabezados "#", elementos
    de lista y líneas de tabla "|" van siempre como párrafo propio. En
    .docx es igual a leer_parrafos.
    """
    ruta = str(ruta)
    if ruta.lower().endswith(".docx"):
        return leer_parrafos(ruta)
    with open(ruta, encoding="utf-8-sig") as archivo:
        lineas = archivo.read().splitlines()
    bloques, actual = [], []
    for linea in lineas:
        limpia = linea.strip()
        propia = limpia.startswith(("#", "|", "- ", "* ", "+ ")) or re.match(r"\d+[.)] ", limpia)
        if not limpia or propia:
            if actual:
                bloques.append(" ".join(actual))
                actual = []
            if propia:
                bloques.append(limpia)
            continue
        actual.append(limpia)
    if actual:
        bloques.append(" ".join(actual))
    return bloques
