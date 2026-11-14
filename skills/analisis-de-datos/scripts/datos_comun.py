# -*- coding: utf-8 -*-
"""Funciones compartidas por los scripts de la skill analisis-de-datos.

Lectura de tablas (.csv, .txt, .tsv, .xlsx) sin perder lo que trae el
archivo: se decodifica a mano (utf-8, utf-8 con BOM, cp1252 o latin-1),
se detecta el separador y la marca decimal, y las filas se leen con el
módulo csv para poder informar líneas con más o menos campos que el
encabezado. Todo llega como texto (o, en xlsx, con el tipo de la celda);
la conversión a número o fecha la decide quien llama.

Reutiliza `comun.py` de la skill niveles-academicos si está a mano
(`../../niveles-academicos/scripts`); si no, usa copias mínimas.
"""
import csv
import datetime as dt
import hashlib
import io
import math
import re
import sys
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
_RUTA_COMUN = CARPETA.parent.parent / "niveles-academicos" / "scripts"
if _RUTA_COMUN.is_dir() and str(_RUTA_COMUN) not in sys.path:
    sys.path.append(str(_RUTA_COMUN))
try:
    import comun  # noqa: F401  (skill niveles-academicos)
except ImportError:  # respaldo: la skill se instaló sola
    comun = None

SEPARADORES = [",", ";", "\t", "|"]
NOMBRE_SEPARADOR = {",": "coma", ";": "punto y coma", "\t": "tabulador", "|": "barra vertical"}
# Formas habituales de "sin dato". El perfil las informa; el análisis solo
# trata como faltante la celda vacía o en blanco, salvo que el plan declare más.
TOKENS_FALTANTE = {"na", "n/a", "nan", "null", "none", "-", "--", ".", "s/d", "sd",
                   "sin dato", "sin datos", "ns/nr", "nr", "ns", "#n/a", "?"}
ERRORES_EXCEL = {"#DIV/0!", "#N/A", "#NAME?", "#NULL!", "#NUM!", "#REF!", "#VALUE!",
                 "#¿NOMBRE?", "#VALOR!", "#DIV/0", "#NUM", "Err:502", "Err:504", "#ERROR!"}

PATRON_NUM_PUNTO = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
PATRON_NUM_COMA = re.compile(r"^[+-]?(\d{1,3}(\.\d{3})+|\d+)(,\d+)?$")
PATRON_DECIMAL_COMA = re.compile(r"^[+-]?\d+,\d+$|^[+-]?\d{1,3}(\.\d{3})+,\d+$")
PATRON_DECIMAL_PUNTO = re.compile(r"^[+-]?\d+\.\d+$")
PATRON_FECHA_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2})(?:\.(\d+))?)?)?$")
PATRON_FECHA_DMA = re.compile(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2}|\d{4})(?: (\d{1,2}):(\d{2})(?::(\d{2}))?)?$")


class ErrorDatos(Exception):
    """Problema que impide leer o analizar; el mensaje dice la causa."""


# ---------------------------------------------------------------------------
# Utilidades generales

def salida_utf8():
    if comun is not None:
        comun.salida_utf8()
        return
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def escribir_atomico(ruta, contenido):
    if comun is not None:
        comun.escribir_atomico(ruta, contenido)
        return
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_name(".tmp_" + ruta.name)
    if isinstance(contenido, (bytes, bytearray)):
        temporal.write_bytes(contenido)
    else:
        temporal.write_text(contenido, encoding="utf-8", newline="\n")
    temporal.replace(ruta)


def ruta_soffice():
    if comun is not None:
        return comun.ruta_soffice()
    import shutil
    return shutil.which("soffice") or shutil.which("libreoffice")


def sha256_archivo(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(1 << 16), b""):
            h.update(bloque)
    return h.hexdigest()


def clave_categoria(texto):
    """Minúsculas, sin tildes, espacios simples: para hallar variantes."""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto.casefold()).strip()


def es_en_blanco(valor):
    if valor is None:
        return True
    if isinstance(valor, float) and math.isnan(valor):
        return True
    return isinstance(valor, str) and valor.strip() == ""


# ---------------------------------------------------------------------------
# Números y redondeo

def a_numero(valor, decimal="."):
    """Convierte un valor a float; None si no es un número.

    Con decimal "," acepta "12,5", "1.234,5" y "1234"; con "." acepta
    "12.5", "1e3" y "1234". No adivina: "1.234" con decimal "." es 1,234.
    """
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return None if (isinstance(valor, float) and math.isnan(valor)) else float(valor)
    if not isinstance(valor, str):
        return None
    texto = valor.strip().replace("−", "-")
    if not texto:
        return None
    if decimal == ",":
        if PATRON_NUM_COMA.match(texto):
            return float(texto.replace(".", "").replace(",", "."))
        return None
    if PATRON_NUM_PUNTO.match(texto):
        return float(texto)
    return None


def redondear(valor, decimales):
    """Redondeo "mitad hacia arriba" sobre la escritura decimal del número
    (34,25 → 34,3), no el redondeo bancario de Python. Devuelve Decimal."""
    cuanto = Decimal(1).scaleb(-decimales)
    return Decimal(repr(float(valor))).quantize(cuanto, rounding=ROUND_HALF_UP)


def formato_es(valor, decimales=0, miles="espacio"):
    """Número a texto en español: coma decimal; miles con espacio duro
    (norma RAE, solo desde cinco cifras), punto o nada."""
    if valor is None or (isinstance(valor, float) and (math.isnan(valor) or math.isinf(valor))):
        return "—"
    numero = redondear(valor, decimales)
    signo = "-" if numero < 0 else ""
    texto = f"{abs(numero):.{decimales}f}"
    entero, _, frac = texto.partition(".")
    if miles == "punto" and len(entero) > 3:
        entero = f"{int(entero):,}".replace(",", ".")
    elif miles == "espacio" and len(entero) > 4:
        entero = f"{int(entero):,}".replace(",", " ")
    return signo + entero + ("," + frac if frac else "")


# ---------------------------------------------------------------------------
# Fechas

def analizar_fecha(texto):
    """(datetime | None, formato) para un texto con aspecto de fecha.

    formato: "AAAA-MM-DD", "DD/MM/AAAA", "MM/DD/AAAA", "DD/MM o MM/DD"
    (ambigua; se lee como DD/MM) o None si no tiene aspecto de fecha.
    Si tiene aspecto pero no es válida (mes 13, 31 de febrero) devuelve
    (None, formato).
    """
    texto = texto.strip()
    m = PATRON_FECHA_ISO.match(texto)
    if m:
        a, me, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        h, mi, s = int(m.group(4) or 0), int(m.group(5) or 0), int(m.group(6) or 0)
        micro = int((m.group(7) or "0")[:6].ljust(6, "0"))
        try:
            return dt.datetime(a, me, d, h, mi, s, micro), "AAAA-MM-DD"
        except ValueError:
            return None, "AAAA-MM-DD"
    m = PATRON_FECHA_DMA.match(texto)
    if m:
        x, y, a = int(m.group(1)), int(m.group(2)), m.group(3)
        a = int(a) + (2000 if len(a) == 2 else 0)
        h, mi, s = int(m.group(4) or 0), int(m.group(5) or 0), int(m.group(6) or 0)
        if x > 12 >= y:
            formato, d, me = "DD/MM/AAAA", x, y
        elif y > 12 >= x:
            formato, d, me = "MM/DD/AAAA", y, x
        elif x <= 12 and y <= 12:
            formato, d, me = "DD/MM o MM/DD", x, y
        else:
            return None, "DD/MM/AAAA"
        try:
            return dt.datetime(a, me, d, h, mi, s), formato
        except ValueError:
            return None, formato
    return None, None


# ---------------------------------------------------------------------------
# Lectura

def _decodificar(crudo):
    """(texto, codificación, bom)."""
    if crudo.startswith(b"\xef\xbb\xbf"):
        return crudo[3:].decode("utf-8"), "utf-8", True
    if crudo.startswith((b"\xff\xfe", b"\xfe\xff")):
        return crudo.decode("utf-16"), "utf-16", True
    try:
        return crudo.decode("utf-8"), "utf-8", False
    except UnicodeDecodeError:
        pass
    # Bytes 0x80–0x9F solo tienen sentido en cp1252 (comillas, guiones de Windows).
    if any(0x80 <= b <= 0x9F for b in crudo):
        try:
            return crudo.decode("cp1252"), "cp1252", False
        except UnicodeDecodeError:
            pass
    return crudo.decode("latin-1"), "latin-1", False


def _finales_linea(crudo):
    crlf = crudo.count(b"\r\n")
    cr = crudo.count(b"\r") - crlf
    lf = crudo.count(b"\n") - crlf
    tipos = [n for n, c in (("CRLF (Windows)", crlf), ("LF (Unix)", lf), ("CR (Mac antiguo)", cr)) if c]
    return tipos or ["ninguno"]


def _detectar_separador(texto):
    muestra = texto[:200000]
    mejor, mejor_puntaje = ",", -1.0
    for sep in SEPARADORES:
        filas = []
        for i, fila in enumerate(csv.reader(io.StringIO(muestra, newline=""), delimiter=sep)):
            if fila:
                filas.append(len(fila))
            if i >= 200:
                break
        if len(filas) > 1:
            filas = filas[:-1]  # la última puede estar cortada por la muestra
        if not filas or filas[0] < 2:
            continue
        constantes = sum(1 for n in filas if n == filas[0]) / len(filas)
        puntaje = constantes * 1000 + filas[0]
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = sep, puntaje
    return mejor


def _detectar_decimal(filas, separador):
    coma = punto = 0
    for fila in filas[1:2000]:
        for celda in fila:
            celda = celda.strip()
            if PATRON_DECIMAL_COMA.match(celda):
                coma += 1
            elif PATRON_DECIMAL_PUNTO.match(celda):
                punto += 1
    return ("," if coma > punto else "."), {"con_coma": coma, "con_punto": punto}


def _nombres_columnas(encabezado):
    """Nombres únicos y avisos sobre el encabezado."""
    nombres, vistos, duplicadas, sin_nombre = [], {}, [], []
    for i, nombre in enumerate(encabezado):
        nombre = "" if nombre is None else str(nombre)
        limpio = nombre.strip()
        if not limpio:
            limpio = f"columna_{i + 1}"
            sin_nombre.append(i + 1)
        if limpio in vistos:
            vistos[limpio] += 1
            duplicadas.append(limpio)
            limpio = f"{limpio} ({vistos[limpio]})"
        else:
            vistos[limpio] = 1
        nombres.append(limpio)
    espacios = [n for n in encabezado if isinstance(n, str) and n != n.strip() and n.strip()]
    return nombres, {"duplicadas": duplicadas, "sin_nombre": sin_nombre,
                     "con_espacios_sobrantes": espacios}


def leer_tabla(ruta, hoja=None, separador=None, codificacion=None, decimal=None):
    """Lee la tabla y devuelve (DataFrame, info).

    En csv todas las celdas llegan como texto (sin recortar); en xlsx con
    el tipo de la celda (número, fecha, texto) y None si está vacía. La
    primera fila no vacía es el encabezado. `info` describe la lectura.
    """
    import pandas as pd

    ruta = Path(ruta)
    if not ruta.is_file():
        raise ErrorDatos(f"no existe el archivo de datos: {ruta}")
    extension = ruta.suffix.lower()
    info = {"archivo": str(ruta), "formato": extension.lstrip("."), "bytes": ruta.stat().st_size,
            "sha256": sha256_archivo(ruta)}
    if extension in (".xlsx", ".xlsm"):
        filas, info_x = _leer_xlsx(ruta, hoja)
        info.update(info_x)
        info.update({"codificacion": None, "separador": None, "decimal": decimal or "."})
    elif extension in (".xls", ".ods"):
        raise ErrorDatos(f"formato {extension} no admitido: guárdelo como .xlsx o .csv")
    else:
        crudo = ruta.read_bytes()
        if codificacion:
            texto = crudo.decode(codificacion)
            bom = crudo.startswith(b"\xef\xbb\xbf")
            if bom and texto.startswith("﻿"):
                texto = texto[1:]
        else:
            texto, codificacion, bom = _decodificar(crudo)
        sep = separador or _detectar_separador(texto)
        filas = [f for f in csv.reader(io.StringIO(texto, newline=""), delimiter=sep)]
        lineas_vacias = sum(1 for f in filas if not f or all(not c.strip() for c in f))
        filas = [f for f in filas if f and any(c.strip() for c in f)]
        dec, cuenta_dec = _detectar_decimal(filas, sep)
        info.update({"codificacion": codificacion, "bom": bom, "separador": sep,
                     "decimal": decimal or dec, "decimales_vistos": cuenta_dec,
                     "finales_de_linea": _finales_linea(crudo), "lineas_vacias": lineas_vacias,
                     "hojas": None, "hoja": None})
    if not filas:
        raise ErrorDatos("el archivo no tiene filas")
    encabezado, cuerpo = filas[0], filas[1:]
    nombres, info_enc = _nombres_columnas(encabezado)
    ancho = len(nombres)
    malformadas = []
    normalizadas = []
    for i, fila in enumerate(cuerpo):
        if len(fila) != ancho:
            sobrante = fila[ancho:]
            if len(fila) > ancho and all(es_en_blanco(c) for c in sobrante):
                fila = fila[:ancho]
            else:
                malformadas.append({"fila": i + 2, "campos": len(fila), "esperados": ancho})
                fila = list(fila[:ancho]) + [None if info["formato"].startswith("xls") else ""] * (ancho - len(fila))
        normalizadas.append(list(fila))
    info.update({"columnas_originales": [None if c is None else str(c) for c in encabezado],
                 "encabezado": info_enc, "filas_malformadas": malformadas,
                 "filas": len(normalizadas), "columnas": ancho})
    df = pd.DataFrame(normalizadas, columns=nombres, dtype=object)
    return df, info


def _leer_xlsx(ruta, hoja):
    from openpyxl import load_workbook

    try:
        libro = load_workbook(ruta, read_only=True, data_only=True)
    except Exception as error:
        raise ErrorDatos(f"no se pudo abrir el xlsx: {error}")
    hojas = libro.sheetnames
    if hoja is None:
        hoja = hojas[0]
    if hoja not in hojas:
        raise ErrorDatos(f"la hoja «{hoja}» no existe; hojas: {', '.join(hojas)}")
    filas = []
    errores = []
    for i, fila in enumerate(libro[hoja].iter_rows(values_only=True)):
        fila = list(fila)
        for j, valor in enumerate(fila):
            if isinstance(valor, str) and valor.strip() in ERRORES_EXCEL:
                errores.append({"fila": i + 1, "columna": j + 1, "valor": valor.strip()})
        filas.append(fila)
    libro.close()
    # Recorta filas y columnas vacías del final; salta filas vacías iniciales.
    filas_vacias_iniciales = 0
    while filas and all(es_en_blanco(v) for v in filas[0]):
        filas.pop(0)
        filas_vacias_iniciales += 1
    while filas and all(es_en_blanco(v) for v in filas[-1]):
        filas.pop()
    ancho = 0
    for fila in filas:
        for j in range(len(fila) - 1, -1, -1):
            if not es_en_blanco(fila[j]):
                ancho = max(ancho, j + 1)
                break
    filas = [list(f[:ancho]) + [None] * (ancho - len(f[:ancho])) for f in filas]
    lineas_vacias = sum(1 for f in filas if all(es_en_blanco(v) for v in f))
    filas = [f for f in filas if not all(es_en_blanco(v) for v in f)]
    return filas, {"hojas": hojas, "hoja": hoja, "celdas_con_error": errores,
                   "filas_vacias_iniciales": filas_vacias_iniciales, "lineas_vacias": lineas_vacias}
