# -*- coding: utf-8 -*-
"""Perfil de un archivo de datos antes de analizarlo. No corrige nada.

Uso: python perfilar_datos.py <archivo .csv|.tsv|.txt|.xlsx> [--hoja nombre] [--json]
     [--separador X] [--codificacion X] [--decimal , | .]

Describe:
- cómo se leyó: codificación (utf-8, utf-8 con BOM, cp1252, latin-1),
  separador, marca decimal, finales de línea, hojas del xlsx;
- filas, columnas, filas duplicadas, filas con más o menos campos que
  el encabezado, encabezados vacíos, repetidos o con espacios;
- por columna: tipo inferido (numérica, binaria 0/1, fecha, categórica,
  texto libre, identificador, mixta, vacía, constante), faltantes
  (celdas vacías, en blanco o con formas como "NA", "-", "s/d"),
  rango, valores atípicos groseros (fuera de Q1 − 3·RIC y Q3 + 3·RIC)
  y posibles códigos de faltante (99, 999, -9…);
- problemas de calidad: columnas mixtas (números y texto), decimales
  con coma y con punto mezclados, fechas mal formadas o con formatos
  mezclados, categorías que difieren solo por mayúsculas, tildes o
  espacios, valores con espacios sobrantes, celdas con error de Excel.

Es el primer paso obligado: con su salida se escribe la sección
"datos" de plan_analisis.json (separador, faltantes, recodificaciones).

Códigos de salida: 0 sin problemas de calidad; 1 hay problemas
descritos (no impide analizar, pero cada uno debe decidirse y anotarse
en el plan); 2 no se pudo leer el archivo.
"""
import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comun as dc  # noqa: E402

MAX_EJEMPLOS = 5
CODIGOS_FALTANTE = {99, 999, 9999, 98, 998, -9, -99, -999, -1}


def _cuartiles(valores):
    import pandas as pd
    s = pd.Series(valores, dtype="float64")
    return float(s.quantile(0.25)), float(s.quantile(0.5)), float(s.quantile(0.75))


def _formato(v):
    """Número en español sin ceros sobrantes (hasta 6 decimales)."""
    if isinstance(v, str):
        return repr(v)
    if isinstance(v, (int, float)):
        texto = dc.formato_es(v, 6, miles="ninguno")
        return texto.rstrip("0").rstrip(",") if "," in texto else texto
    return str(v)


def perfilar_columna(nombre, serie, decimal):
    total = len(serie)
    faltantes = Counter()
    numeros, fechas, formatos_fecha, fechas_malas, textos = [], [], Counter(), [], []
    filas_texto_en_numerica = []
    dec_coma = dec_punto = 0
    espacios_sobrantes = 0
    for i, valor in enumerate(serie.tolist()):
        fila = i + 2
        if valor is None or (isinstance(valor, float) and math.isnan(valor)):
            faltantes["(celda vacía)"] += 1
            continue
        if isinstance(valor, bool):
            textos.append((fila, str(valor)))
            continue
        if isinstance(valor, (int, float)):
            numeros.append((fila, float(valor)))
            continue
        if hasattr(valor, "year") and hasattr(valor, "month"):
            fechas.append((fila, valor))
            formatos_fecha["fecha de Excel"] += 1
            continue
        texto = str(valor)
        limpio = texto.strip()
        if not limpio:
            faltantes["(vacía)" if texto == "" else "(solo espacios)"] += 1
            continue
        if limpio.casefold() in dc.TOKENS_FALTANTE:
            faltantes[limpio] += 1
            continue
        if texto != limpio:
            espacios_sobrantes += 1
        numero = dc.a_numero(limpio, decimal)
        if numero is None:
            otra = dc.a_numero(limpio, "." if decimal == "," else ",")
            if otra is not None and ("," in limpio or "." in limpio):
                # Número escrito con la otra marca decimal.
                numero = otra
        if numero is not None:
            if dc.PATRON_DECIMAL_COMA.match(limpio):
                dec_coma += 1
            elif dc.PATRON_DECIMAL_PUNTO.match(limpio):
                dec_punto += 1
            numeros.append((fila, numero))
            continue
        fecha, formato = dc.analizar_fecha(limpio)
        if formato:
            if fecha is None:
                fechas_malas.append((fila, limpio))
            else:
                fechas.append((fila, fecha))
            formatos_fecha[formato] += 1
            continue
        textos.append((fila, limpio))

    n_faltantes = sum(faltantes.values())
    validos = total - n_faltantes
    col = {"nombre": nombre, "filas": total, "faltantes": n_faltantes,
           "faltantes_por_forma": dict(faltantes.most_common()),
           "pct_faltantes": round(100 * n_faltantes / total, 1) if total else 0.0,
           "validos": validos, "problemas": [], "observaciones": []}
    problemas, obs = col["problemas"], col["observaciones"]
    if faltantes.get("(solo espacios)"):
        obs.append(f"{faltantes['(solo espacios)']} celdas con solo espacios: el análisis las "
                   "trata como faltantes (celda en blanco)")
    formas_raras = [k for k in faltantes if k not in ("(celda vacía)", "(vacía)", "(solo espacios)")]
    if formas_raras:
        obs.append("faltantes escritos como " + ", ".join(
            f"{k!r}: {faltantes[k]}" if not k.startswith("(") else f"{k}: {faltantes[k]}"
            for k in formas_raras) + "; declárelos en \"faltantes\" del plan si son sin dato")
    if espacios_sobrantes:
        problemas.append(f"{espacios_sobrantes} valores con espacios al inicio o al final")

    n_num, n_fec, n_mal, n_tex = len(numeros), len(fechas), len(fechas_malas), len(textos)
    if validos == 0:
        col["tipo"] = "vacía"
        problemas.append("columna sin ningún dato")
        return col

    distintos_texto = Counter(t for _, t in textos)
    if n_fec + n_mal and (n_fec + n_mal) >= 0.8 * validos:
        col["tipo"] = "fecha"
        if fechas:
            orden = sorted(f for _, f in fechas)
            col["rango"] = [orden[0].isoformat(sep=" "), orden[-1].isoformat(sep=" ")]
        col["formatos_fecha"] = dict(formatos_fecha)
        if n_mal:
            problemas.append(f"{n_mal} fechas mal formadas (no existen): " +
                             ", ".join(f"fila {f}: {t!r}" for f, t in fechas_malas[:MAX_EJEMPLOS]))
        familias = {("ISO" if k == "AAAA-MM-DD" else "otra" if k == "fecha de Excel" else "DMA" if k != "MM/DD/AAAA" else "MDA")
                    for k in formatos_fecha}
        if "MM/DD/AAAA" in formatos_fecha and ("DD/MM/AAAA" in formatos_fecha):
            problemas.append("fechas con día/mes y mes/día mezclados")
        elif len(familias) > 1:
            problemas.append("formatos de fecha mezclados: " + ", ".join(sorted(formatos_fecha)))
        if formatos_fecha.get("DD/MM o MM/DD"):
            obs.append(f"{formatos_fecha['DD/MM o MM/DD']} fechas ambiguas (día y mes ≤ 12); "
                       "declare \"formato_fecha\" en el plan")
        if n_num or n_tex:
            problemas.append(f"columna de fechas con {n_num + n_tex} valores que no son fechas: " +
                             ", ".join(f"fila {f}: {_formato(v)}" for f, v in (textos + numeros)[:MAX_EJEMPLOS]))
        return col

    if n_num and (n_tex or n_mal or n_fec):
        col["tipo"] = "mixta"
        otros = textos + [(f, t) for f, t in fechas_malas] + [(f, str(t)) for f, t in fechas]
        problemas.append(f"columna mixta: {n_num} valores numéricos y {len(otros)} no numéricos; "
                         "ejemplos no numéricos: " +
                         ", ".join(f"fila {f}: {v!r}" for f, v in otros[:MAX_EJEMPLOS]) +
                         "; ejemplos numéricos: " +
                         ", ".join(f"fila {f}: {_formato(v)}" for f, v in numeros[:3]))
    elif n_num:
        valores = [v for _, v in numeros]
        enteros = all(v.is_integer() for v in valores)
        distintos = set(valores)
        if distintos <= {0.0, 1.0}:
            col["tipo"] = "binaria 0/1"
            obs.append("códigos 0/1 sin etiqueta: averigüe qué significa cada código "
                       "(libro de códigos o artículo) y declárelo en \"recodificar\"")
        elif len(distintos) == 1:
            col["tipo"] = "constante"
        else:
            col["tipo"] = "numérica entera" if enteros else "numérica decimal"
        col["rango"] = [min(valores), max(valores)]
        col["distintos"] = len(distintos)
        if dec_coma and dec_punto:
            problemas.append(f"decimales escritos con coma ({dec_coma}) y con punto ({dec_punto}) en la misma columna")
        elif dec_coma and decimal == ".":
            problemas.append(f"{dec_coma} números con coma decimal en un archivo leído con punto decimal")
        elif dec_punto and decimal == ",":
            problemas.append(f"{dec_punto} números con punto decimal en un archivo leído con coma decimal")
        if len(distintos) <= 12 and len(valores) >= 50:
            obs.append(f"solo {len(distintos)} valores distintos: ¿código, escala o categoría "
                       "numerada? (no se buscan atípicos)")
        elif len(valores) >= 10 and len(distintos) > 2:
            q1, mediana, q3 = _cuartiles(valores)
            ric = q3 - q1
            col["cuartiles"] = [q1, mediana, q3]
            if ric > 0:
                bajo, alto = q1 - 3 * ric, q3 + 3 * ric
                atipicos = [(f, v) for f, v in numeros if v < bajo or v > alto]
                if atipicos:
                    col["atipicos"] = {"n": len(atipicos), "limites": [bajo, alto],
                                       "ejemplos": [{"fila": f, "valor": v} for f, v in atipicos[:MAX_EJEMPLOS]]}
                    problemas.append(f"{len(atipicos)} valores atípicos groseros (fuera de "
                                     f"[{_formato(round(bajo, 4))}; {_formato(round(alto, 4))}]): " +
                                     ", ".join(f"fila {f}: {_formato(v)}" for f, v in atipicos[:MAX_EJEMPLOS]))
                    codigos = sorted({v for _, v in atipicos if v in CODIGOS_FALTANTE})
                    if codigos:
                        problemas.append("posibles códigos de faltante entre los atípicos: " +
                                         ", ".join(_formato(c) for c in codigos))
        if col["tipo"] == "constante":
            obs.append(f"todas las filas válidas valen {_formato(valores[0])}")
        return col
    else:
        col["tipo"] = "texto"

    # Columnas de texto (o mixtas): categorías y variantes.
    distintos = len(distintos_texto)
    col["distintos"] = distintos
    if col["tipo"] == "texto":
        largo_medio = sum(len(t) for t in distintos_texto.elements()) / max(n_tex, 1)
        if distintos == 1:
            col["tipo"] = "constante"
            obs.append(f"todas las filas válidas valen {next(iter(distintos_texto))!r}")
        elif distintos == n_tex and n_tex > 20:
            col["tipo"] = "identificador o texto libre"
        elif distintos > max(30, 0.5 * n_tex) or (largo_medio > 60 and distintos > 15):
            col["tipo"] = "texto libre"
        else:
            col["tipo"] = "categórica"
    if col["tipo"] in ("categórica", "mixta", "constante") or distintos <= 50:
        col["categorias"] = dict(sorted(distintos_texto.items(), key=lambda kv: (-kv[1], kv[0]))[:30])
        if distintos > 30:
            col["categorias_omitidas"] = distintos - 30
    grupos = defaultdict(list)
    for valor in distintos_texto:
        grupos[dc.clave_categoria(valor)].append(valor)
    variantes = [sorted(v) for v in grupos.values() if len(v) > 1]
    if variantes:
        col["variantes"] = [{v: distintos_texto[v] for v in grupo} for grupo in sorted(variantes)]
        problemas.append("categorías que difieren solo por mayúsculas, tildes o espacios: " +
                         "; ".join(" / ".join(f"{v!r} ({distintos_texto[v]})" for v in g)
                                   for g in sorted(variantes)[:MAX_EJEMPLOS]))
    if col["tipo"] == "categórica" and distintos >= 4:
        raras = [v for v, c in distintos_texto.items() if c == 1]
        if raras and len(raras) <= 10 and n_tex >= 50:
            obs.append(f"{len(raras)} categorías con un solo caso (¿respuestas abiertas tipo «otro»?): " +
                       ", ".join(repr(v[:60]) for v in sorted(raras)[:MAX_EJEMPLOS]))
    return col


def perfilar(ruta, hoja=None, separador=None, codificacion=None, decimal=None):
    df, info = dc.leer_tabla(ruta, hoja=hoja, separador=separador,
                             codificacion=codificacion, decimal=decimal)
    perfil = {"archivo": str(Path(ruta)), "lectura": {k: info.get(k) for k in (
        "formato", "bytes", "sha256", "codificacion", "bom", "separador", "decimal",
        "finales_de_linea", "hojas", "hoja", "lineas_vacias")},
        "filas": info["filas"], "columnas": info["columnas"], "problemas": [], "observaciones": []}
    problemas, obs = perfil["problemas"], perfil["observaciones"]
    lectura = perfil["lectura"]
    if info.get("separador"):
        lectura["separador_nombre"] = dc.NOMBRE_SEPARADOR.get(info["separador"], info["separador"])
    if info.get("codificacion") in ("latin-1", "cp1252"):
        obs.append(f"codificación {info['codificacion']} (no UTF-8): típico de Excel en Windows; "
                   f"declare \"codificacion\": \"{info['codificacion']}\" en el plan")
    if info.get("bom"):
        obs.append("el archivo empieza con BOM (marca de orden de bytes); se ignora al leer")
    if info.get("finales_de_linea") and len(info["finales_de_linea"]) > 1:
        problemas.append("finales de línea mezclados: " + ", ".join(info["finales_de_linea"]))
    elif info.get("finales_de_linea") == ["CR (Mac antiguo)"]:
        obs.append("finales de línea CR (Mac antiguo): algunos programas ven una sola línea")
    if info.get("separador") and info["separador"] != ",":
        obs.append(f"separador: {lectura['separador_nombre']}")
    if info.get("decimal") == ",":
        obs.append("marca decimal: coma; declare \"decimal\": \",\" en el plan")
    if info.get("lineas_vacias"):
        obs.append(f"{info['lineas_vacias']} líneas vacías (se ignoran)")
    if info.get("filas_vacias_iniciales"):
        obs.append(f"el encabezado está en la fila {info['filas_vacias_iniciales'] + 1}")
    for error in info.get("celdas_con_error") or []:
        problemas.append(f"celda con error de Excel en fila {error['fila']}, columna {error['columna']}: {error['valor']}")
    if info["filas_malformadas"]:
        m = info["filas_malformadas"]
        problemas.append(f"{len(m)} filas con distinto número de campos que el encabezado: " +
                         ", ".join(f"fila {x['fila']} ({x['campos']} de {x['esperados']})" for x in m[:MAX_EJEMPLOS]))
    enc = info["encabezado"]
    if enc["duplicadas"]:
        problemas.append("nombres de columna repetidos: " + ", ".join(sorted(set(enc["duplicadas"]))) +
                         " (se leen como «nombre (2)»)")
    if enc["sin_nombre"]:
        problemas.append("columnas sin nombre en las posiciones " + ", ".join(map(str, enc["sin_nombre"])))
    if enc["con_espacios_sobrantes"]:
        problemas.append("nombres de columna con espacios al inicio o al final: " +
                         ", ".join(repr(n) for n in enc["con_espacios_sobrantes"]))
    if info["filas"] == 0:
        problemas.append("el archivo solo tiene encabezado")
    claves = df.apply(lambda fila: tuple("" if dc.es_en_blanco(v) else str(v).strip() for v in fila), axis=1) \
        if info["filas"] else []
    vistas, duplicadas = {}, []
    for i, clave in enumerate(claves):
        if clave in vistas:
            duplicadas.append((i + 2, vistas[clave]))
        else:
            vistas[clave] = i + 2
    perfil["filas_duplicadas"] = len(duplicadas)
    if duplicadas:
        problemas.append(f"{len(duplicadas)} filas idénticas a otra anterior: " +
                         ", ".join(f"fila {a} = fila {b}" for a, b in duplicadas[:MAX_EJEMPLOS]))
    perfil["columnas_detalle"] = [perfilar_columna(c, df[c], info["decimal"] or ".") for c in df.columns]
    perfil["n_problemas"] = len(problemas) + sum(len(c["problemas"]) for c in perfil["columnas_detalle"])
    return perfil


def _num(v):
    return _formato(v) if isinstance(v, (int, float)) else str(v)


def informe_texto(p):
    lineas = [f"Perfil de datos: {p['archivo']}"]
    lec = p["lectura"]
    if lec["formato"].startswith("xls"):
        lineas.append(f"Lectura: xlsx, hoja «{lec['hoja']}» (hojas: {', '.join(lec['hojas'])})")
    else:
        lineas.append(f"Lectura: codificación {lec['codificacion']}{' con BOM' if lec['bom'] else ''}, "
                      f"separador {lec.get('separador_nombre')}, decimal «{lec['decimal']}», "
                      f"finales de línea {', '.join(lec['finales_de_linea'])}")
    lineas.append(f"sha256: {lec['sha256']}")
    lineas.append(f"Filas: {p['filas']}   Columnas: {p['columnas']}   Filas duplicadas: {p['filas_duplicadas']}")
    if p["problemas"]:
        lineas.append("\nProblemas del archivo:")
        lineas += [f"  - {x}" for x in p["problemas"]]
    if p["observaciones"]:
        lineas.append("\nObservaciones del archivo:")
        lineas += [f"  - {x}" for x in p["observaciones"]]
    lineas.append("\nColumnas:")
    for c in p["columnas_detalle"]:
        cab = f"  [{c['tipo']}] {c['nombre']}: válidos {c['validos']}, faltantes {c['faltantes']} ({dc.formato_es(c['pct_faltantes'], 1)} %)"
        if "rango" in c:
            cab += f", rango {_num(c['rango'][0])} a {_num(c['rango'][1])}"
        if "distintos" in c:
            cab += f", {c['distintos']} valores distintos"
        lineas.append(cab)
        if "categorias" in c and c["tipo"] in ("categórica", "mixta", "constante", "binaria 0/1"):
            cats = ", ".join(f"{k[:40]!r}: {v}" for k, v in list(c["categorias"].items())[:8])
            lineas.append(f"      categorías: {cats}{' …' if len(c['categorias']) > 8 else ''}")
        for x in c["problemas"]:
            lineas.append(f"      PROBLEMA: {x}")
        for x in c["observaciones"]:
            lineas.append(f"      nota: {x}")
    lineas.append(f"\nTotal de problemas de calidad: {p['n_problemas']}"
                  " (este script describe; no corrige ni completa nada)")
    return "\n".join(lineas)


def main(argv=None):
    dc.salida_utf8()
    parser = argparse.ArgumentParser(description="Perfil de un archivo de datos (no corrige nada).")
    parser.add_argument("archivo")
    parser.add_argument("--hoja")
    parser.add_argument("--separador", help="forzar separador (use \\t para tabulador)")
    parser.add_argument("--codificacion")
    parser.add_argument("--decimal", choices=[",", "."])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    sep = "\t" if args.separador in ("\\t", "tab", "tabulador") else args.separador
    try:
        perfil = perfilar(args.archivo, hoja=args.hoja, separador=sep,
                          codificacion=args.codificacion, decimal=args.decimal)
    except (dc.ErrorDatos, UnicodeDecodeError, LookupError, OSError) as error:
        if args.json:
            print(json.dumps({"error": str(error)}, ensure_ascii=False))
        else:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(perfil, ensure_ascii=False, indent=2, default=str))
    else:
        print(informe_texto(perfil))
    return 1 if perfil["n_problemas"] else 0


if __name__ == "__main__":
    sys.exit(main())
