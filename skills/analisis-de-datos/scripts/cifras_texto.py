# -*- coding: utf-8 -*-
"""Control mecánico de cifras: ¿las del texto salen del análisis?

Uso: python cifras_texto.py <texto .md|.txt|.docx> <analisis/resultados/resultados.json> [--json]

Extrae las cifras del cuerpo del texto (no de la lista de referencias)
y busca cada una en la lista "cifras" de resultados.json. Clasifica:

  COINCIDE    la cifra es el redondeo correcto de un valor del análisis:
              |valor − cifra| ≤ media unidad del último decimal escrito
              (34,6 vale para 34,55 … 34,65; 868 para 867,5 … 868,5).
  NO HALLADA  no corresponde a ningún valor del análisis. Puede venir
              de una fuente: se lista para que el verificador la
              compruebe; si la oración lleva cita APA se marca
              "con cita".
  DISCREPA    no coincide, pero hay un valor del mismo tipo muy cercano
              (el texto parece haber copiado mal o redondeado mal):
              porcentajes a ≤ 1 punto; conteos y otros números a ≤ 3 %
              del valor. Ej.: texto 34,6 % y análisis 34,2 %.

Cómo se lee una cifra:
- coma decimal ("34,6"); miles con punto ("1.561") o espacio
  ("1 561", también duro o fino); un punto seguido de otra cantidad de
  cifras se toma como decimal ("0.75");
- "%" o "por ciento" la hace porcentaje; se compara con los
  porcentajes del análisis y con proporciones (valores entre −1 y 1)
  multiplicadas por 100;
- "n = 120", "N = 120", "n=120" la hace conteo; solo se compara con
  conteos;
- "p < 0,001" o "p < ,05" es una cota: COINCIDE si algún p del
  análisis la cumple; si no, NO HALLADA (nunca DISCREPA);
- los rangos ("18–21", "entre 18 y 21") dan dos cifras;
- signo menos (− o -) solo si va pegado al número y no sigue a otra cifra.

Se ignoran: años (1900–2100 sin decimales, sin % y sin "n ="),
fechas (14/11/2026, 2024-01-08, "14 de noviembre"), horas (17:10),
numeración de tablas, figuras, gráficos, cuadros, anexos, secciones,
capítulos, páginas, preguntas, ítems, notas, leyes, decretos y
artículos ("Tabla 3", "p. 12", "pregunta 7", "Ley 1333"), numeración
al inicio de títulos y listas ("## 3.2 Resultados", "1. "), ordinales
(1.º, 2.ª, 3er), cifras dentro de palabras (COVID-19, msl01, H2O),
las citas entre paréntesis con año y la sección de referencias.

Límites conocidos: no entiende números escritos con letras ("ochocientos
sesenta y ocho"); no sabe a qué variable se refiere la cifra, solo si
el número existe en el análisis (una cifra puede COINCIDIR por azar con
otro valor; cuanto más decimales, menor ese riesgo; los enteros chicos
coinciden casi siempre); un conteo de 1900 a 2100 sin "n =" se toma
por año; "1.561" se lee como mil quinientos sesenta y uno (convención
española), no como 1,561. Con cita y valor cercano se informa NO
HALLADA "con cita" y se anota el valor cercano, porque la cifra se
atribuye a una fuente; el verificador decide.

Códigos de salida: 1 si hay alguna DISCREPA; 0 si no; 2 si no pudo
ejecutarse (archivos ausentes o ilegibles).
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comun as dc  # noqa: E402

MESES = ("enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|"
         "noviembre|diciembre")
PALABRAS_NUMERACION = (r"tablas?|figuras?|gr[aá]ficos?|cuadros?|anexos?|ap[eé]ndices?|secci[oó]n|secciones|"
                       r"cap[ií]tulos?|apartados?|p[aá]ginas?|p\.|pp\.|preguntas?|[ií]tems?|notas?|"
                       r"leyes|ley|decretos?|art[ií]culos?|art\.|incisos?|n\.?\s?º|nº|n°|n\.?\s?°|vol\.|"
                       r"vol[uú]menes|volumen|ediciones|edici[oó]n|ed\.|versi[oó]n|fila|columna|hoja|paso|fase|"
                       r"hip[oó]tesis|objetivo|modelo|ronda|ola|semestre|curso|grado|nivel|piso")
IGNORAR = [
    re.compile(r"\b\d{1,2}\s+de\s+(?:" + MESES + r")(?:\s+de(?:l)?\s+\d{4})?", re.I),
    re.compile(r"\b(?:" + MESES + r")\s+de(?:l)?\s+\d{4}", re.I),
    re.compile(r"\b\d{4}-\d{1,2}-\d{1,2}(?:[ T]\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?\b"),
    re.compile(r"\b\d{1,2}[/.]\d{1,2}[/.]\d{2,4}\b"),
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:h|hrs?|horas)?\b"),
    re.compile(r"(?<![\w])(?:" + PALABRAS_NUMERACION + r")\s*\d+(?:[.\-–]\d+)*(?:\s*(?:y|a|–|-)\s*\d+(?:\.\d+)*)?", re.I),
    re.compile(r"\b\d+\s?\.?[ºª°]"),
    re.compile(r"\b\d+(?:er|ro|do|to|vo|no|mo)\b", re.I),
    re.compile(r"\b[A-Za-zÁÉÍÓÚÑáéíóúñ]+[-_]?\d+[A-Za-z0-9]*\b|\b\d+[A-Za-zÁÉÍÓÚÑáéíóúñ]+\d*\b"),
    re.compile(r"\([^()]*\b(?:1[5-9]\d\d|20\d\d)[a-z]?\b[^()]*\)"),  # (Autor, 2017; Otro, 2019)
    re.compile(r"\b(?:https?://|doi\.org/|10\.\d{4,9}/)\S+", re.I),
]
CITA = re.compile(r"\([^()]*[A-ZÁÉÍÓÚÑ][^()]*,\s*(?:1[5-9]\d\d|20\d\d)[a-z]?(?:,[^()]*)?\)|"
                  r"\([^()]*,\s*s\.\s?f\.\)|"
                  r"[A-ZÁÉÍÓÚÑ][\w\-]+(?:\s+(?:et\s+al\.|y\s+[A-ZÁÉÍÓÚÑ][\w\-]+))?\s+\((?:1[5-9]\d\d|20\d\d)[a-z]?\)")
NUMERO = re.compile(
    r"(?P<signo>[−-])?(?P<num>(?:\d{1,3}(?:\.\d{3})+|\d{1,3}(?:[    ]\d{3})+|\d+)(?:,\d+)?|\d+\.\d+|,\d+)"
    r"(?P<pct>\s?%|\s+por\s+ciento)?")
CONTEO = re.compile(r"\b[nN]\s?=\s?$")
COTA = re.compile(r"\bp\s?(?P<op>[<>≤≥]|<=|>=)\s?$")
TITULO_NUMERADO = re.compile(r"^(?:#+\s*)?\d+(?:\.\d+)*\.?\s+(?=\S)")
LISTA_NUMERADA = re.compile(r"^\d+[.)]\s+")
FIN_ORACION = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])")


def oraciones(bloque):
    return FIN_ORACION.split(bloque)


def enmascarar(texto):
    for patron in IGNORAR:
        texto = patron.sub(lambda m: " " * len(m.group(0)), texto)
    return texto


def leer_numero(crudo):
    """(valor, decimales) de un número escrito en español."""
    if re.fullmatch(r"\d+\.\d+", crudo) and not re.fullmatch(r"\d{1,3}(?:\.\d{3})+", crudo):
        entero, frac = crudo.split(".")
        return float(crudo), len(frac)
    entero, _, frac = crudo.partition(",")
    entero = re.sub(r"[.\s   ]", "", entero) or "0"
    valor = float(f"{entero}.{frac}" if frac else entero)
    return valor, len(frac)


def extraer(parrafos):
    """Lista de cifras con contexto."""
    cifras = []
    for nb, bloque in enumerate(parrafos):
        limpio = bloque
        prefijo = TITULO_NUMERADO.match(limpio) if len(limpio) < 150 or limpio.startswith("#") else None
        prefijo = prefijo or LISTA_NUMERADA.match(limpio)
        if prefijo:
            limpio = " " * prefijo.end() + limpio[prefijo.end():]
        if limpio.lstrip().startswith("|") and re.fullmatch(r"[\s|:\-]+", limpio):
            continue
        for oracion in oraciones(limpio):
            con_cita = bool(CITA.search(oracion))
            visible = enmascarar(oracion)
            for m in NUMERO.finditer(visible):
                inicio = m.start()
                previo = visible[max(0, inicio - 1):inicio]
                if previo and (previo.isalnum() or previo in "_"):
                    continue
                siguiente = visible[m.end():m.end() + 1]
                if siguiente and (siguiente.isalpha() and not m.group("pct")):
                    continue
                crudo = m.group("num")
                if crudo.startswith(","):
                    valor, dec = float("0." + crudo[1:]), len(crudo) - 1
                else:
                    valor, dec = leer_numero(crudo.strip())
                signo = m.group("signo")
                if signo and not (inicio == 0 or not visible[inicio - 1].isdigit()):
                    signo = None
                if signo and inicio > 0 and visible[inicio - 1] not in " (\t[;:=":
                    signo = None
                if signo:
                    valor = -valor
                antes = visible[max(0, inicio - 12):inicio]
                tipo = "porcentaje" if m.group("pct") else "numero"
                if CONTEO.search(antes):
                    tipo = "conteo"
                cota = COTA.search(antes)
                if (tipo == "numero" and dec == 0 and 1900 <= abs(valor) <= 2100 and "." not in crudo
                        and " " not in crudo):
                    continue  # año
                texto = (signo or "") + crudo + (m.group("pct") or "")
                cifras.append({"texto": texto.strip(), "valor": valor, "decimales": dec, "tipo": tipo,
                               "cota": (cota.group("op") if cota else None), "bloque": nb + 1,
                               "contexto": _contexto(oracion, m.start(), m.end()), "con_cita": con_cita})
    return cifras


def _contexto(oracion, a, b):
    ini, fin = max(0, a - 50), min(len(oracion), b + 30)
    return ("…" if ini else "") + oracion[ini:fin].strip() + ("…" if fin < len(oracion) else "")


def candidatos(cifra, lista):
    """(clave, valor) del análisis comparables con la cifra del texto."""
    if cifra["tipo"] == "conteo":
        return [(c["clave"], c["valor"]) for c in lista if c["tipo"] == "conteo"]
    if cifra["tipo"] == "porcentaje":
        r = [(c["clave"], c["valor"]) for c in lista if c["tipo"] == "porcentaje"]
        r += [(c["clave"] + " (×100)", 100 * c["valor"]) for c in lista
              if c["tipo"] in ("estadistico", "prueba") and -1 <= c["valor"] <= 1]
        return r
    return [(c["clave"], c["valor"]) for c in lista]


def clasificar(cifra, lista):
    t, d = cifra["valor"], cifra["decimales"]
    if cifra["cota"]:
        ps = [(c["clave"], c["valor"]) for c in lista if c["tipo"] == "p_valor"]
        op = cifra["cota"]
        cumple = [(k, v) for k, v in ps if {"<": v < t, "≤": v <= t, "<=": v <= t,
                                             ">": v > t, "≥": v >= t, ">=": v >= t}[op]]
        if cumple:
            return "COINCIDE", cumple[:3], None
        return "NO HALLADA", [], None
    tolerancia = 0.5 * 10 ** -d + 1e-9 * max(1.0, abs(t))
    lista_c = candidatos(cifra, lista)
    iguales = sorted(((k, v) for k, v in lista_c if abs(v - t) <= tolerancia), key=lambda kv: abs(kv[1] - t))
    if iguales:
        return "COINCIDE", iguales[:3], None
    # Cercanos del mismo tipo.
    if cifra["tipo"] == "porcentaje":
        cerca = [(k, v) for k, v in lista_c if abs(v - t) <= 1.0]
    else:
        tipos = {"conteo"} if (cifra["tipo"] == "conteo" or d == 0) else {"estadistico", "prueba", "porcentaje"}
        cerca = [(c["clave"], c["valor"]) for c in lista if c["tipo"] in tipos
                 and abs(c["valor"] - t) <= 0.03 * max(abs(c["valor"]), abs(t))]
    cerca.sort(key=lambda kv: abs(kv[1] - t))
    if cerca:
        return "DISCREPA", [], cerca[0]
    return "NO HALLADA", [], None


def revisar(ruta_texto, ruta_resultados):
    ruta_texto, ruta_resultados = Path(ruta_texto), Path(ruta_resultados)
    for r in (ruta_texto, ruta_resultados):
        if not r.is_file():
            raise dc.ErrorDatos(f"no existe {r}")
    try:
        resultados = json.loads(ruta_resultados.read_text(encoding="utf-8"))
        lista = resultados["cifras"]
    except (json.JSONDecodeError, KeyError) as error:
        raise dc.ErrorDatos(f"resultados.json ilegible o sin \"cifras\": {error}")
    if dc.comun is not None:
        parrafos = dc.comun.leer_bloques(str(ruta_texto))
        cuerpo, _ = dc.comun.separar_referencias(parrafos)
        cuerpo += dc.comun.tras_referencias(parrafos)
    else:
        cuerpo = [p.strip() for p in ruta_texto.read_text(encoding="utf-8-sig").split("\n\n") if p.strip()]
    cifras = extraer(cuerpo)
    for c in cifras:
        estado, iguales, cercano = clasificar(c, lista)
        c["estado"] = estado
        if iguales:
            c["coincide_con"] = [{"clave": k, "valor": v} for k, v in iguales]
        if cercano:
            c["valor_cercano"] = {"clave": cercano[0], "valor": cercano[1]}
        if estado == "DISCREPA" and c["con_cita"]:
            c["estado"] = "NO HALLADA"
            c["nota"] = "con cita y valor cercano en el análisis: comprobar contra la fuente"
            c["valor_cercano"] = {"clave": cercano[0], "valor": cercano[1]}
    resumen = {e: sum(1 for c in cifras if c["estado"] == e) for e in ("COINCIDE", "NO HALLADA", "DISCREPA")}
    resumen["NO HALLADA con cita"] = sum(1 for c in cifras if c["estado"] == "NO HALLADA" and c["con_cita"])
    return {"texto": str(ruta_texto), "resultados": str(ruta_resultados),
            "datos_sha256": resultados.get("metadatos", {}).get("datos", {}).get("sha256"),
            "resumen": resumen, "cifras": cifras}


def informe_texto(r):
    L = [f"Cifras del texto: {r['texto']}", f"Análisis: {r['resultados']}",
         "Resumen: " + ", ".join(f"{k}: {v}" for k, v in r["resumen"].items())]
    for estado in ("DISCREPA", "NO HALLADA", "COINCIDE"):
        grupo = [c for c in r["cifras"] if c["estado"] == estado]
        if not grupo:
            continue
        L += ["", f"{estado} ({len(grupo)})"]
        for c in grupo:
            linea = f"  [{c['bloque']}] {c['texto']}"
            if estado == "DISCREPA":
                v = c["valor_cercano"]
                linea += f" — en el análisis: {v['valor']!r} ({v['clave']})"
            elif estado == "NO HALLADA":
                linea += " (con cita)" if c["con_cita"] else " (sin cita: ¿de dónde sale?)"
                if c.get("valor_cercano"):
                    linea += f"; valor cercano {c['valor_cercano']['valor']!r} ({c['valor_cercano']['clave']})"
            else:
                linea += f" = {c['coincide_con'][0]['clave']}"
            L.append(linea)
            if estado != "COINCIDE":
                L.append(f"      «{c['contexto']}»")
    return "\n".join(L)


def main(argv=None):
    dc.salida_utf8()
    parser = argparse.ArgumentParser(description="Coteja las cifras del texto con resultados.json.")
    parser.add_argument("texto")
    parser.add_argument("resultados")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        r = revisar(args.texto, args.resultados)
    except (dc.ErrorDatos, OSError, ValueError, KeyError) as error:
        if args.json:
            print(json.dumps({"error": str(error)}, ensure_ascii=False))
        else:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps(r, ensure_ascii=False, indent=2) if args.json else informe_texto(r))
    return 1 if r["resumen"]["DISCREPA"] else 0


if __name__ == "__main__":
    sys.exit(main())
