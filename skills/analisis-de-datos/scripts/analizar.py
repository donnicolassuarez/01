# -*- coding: utf-8 -*-
"""Análisis descriptivo reproducible a partir de analisis/plan_analisis.json.

Uso: python analizar.py <analisis/plan_analisis.json> [--salida carpeta]
     [--sin-figuras] [--json]

El plan declara qué archivo leer, cómo leerlo, qué valores son
faltantes, qué códigos se recodifican, qué filtros se aplican y qué
tablas se piden (frecuencias, cruzada, resumen, serie). Ver la
plantilla comentada en SKILL.md.

Salidas (por defecto en <carpeta del plan>/resultados/):
  resultados.json  todas las cifras con precisión completa, en tablas y
                   en una lista plana "cifras" (clave, valor, tipo) que
                   usa cifras_texto.py; metadatos: sha256 de datos y
                   plan, filas leídas y usadas, filtros, métodos,
                   versiones y fecha ("metadatos.generado", lo único que
                   cambia entre dos corridas con los mismos datos).
  resultados.md    tablas legibles para el redactor, redondeadas según
                   la regla declarada ("redondeo" del plan).
  figuras/*.png    si la tabla pide "figura": true (requiere matplotlib).

Métodos fijos (quedan escritos en metadatos.metodos):
- desviación estándar muestral (n − 1); cuartiles por interpolación
  lineal (tipo 7, igual que CUARTIL.INCLUYE de Excel);
- porcentajes sobre los casos válidos (y, en frecuencias, también sobre
  el total con faltantes);
- faltante = celda vacía o en blanco, más los valores que el plan
  declare en "faltantes". Nada se imputa ni se completa;
- pruebas (opcionales, solo con scipy): chi cuadrado de Pearson sin
  corrección de Yates, t de Welch, U de Mann-Whitney, ANOVA de un
  factor y Kruskal-Wallis. Sin scipy se omiten y se avisa.

Códigos de salida: 0 todo calculado; 1 calculado con avisos (algo no
se pudo calcular o se excluyó: se dice en resultados.md); 2 no se pudo
ejecutar (plan inválido, columna inexistente, valor no numérico en una
variable numérica, datos ilegibles).
"""
import argparse
import datetime as dt
import difflib
import json
import math
import os
import platform
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comun as dc  # noqa: E402

VERSION = "1.0"
TIPOS_TABLA = ("frecuencias", "cruzada", "resumen", "serie")
OPERADORES = ("==", "!=", "en", "no_en", ">", ">=", "<", "<=", "no_faltante")
PERIODOS = ("hora", "dia", "semana", "mes", "trimestre", "año")
PRUEBAS_GRUPOS = ("t", "mann-whitney", "anova", "kruskal")
REDONDEO_POR_DEFECTO = {"porcentaje": 1, "estadistico": 2, "prueba": 2, "p_valor": 3}
ESTADISTICOS = ("n", "faltantes", "media", "mediana", "de", "minimo", "q1", "q3", "maximo")
NOMBRE_ESTADISTICO = {"n": "n", "faltantes": "Faltantes", "media": "Media", "mediana": "Mediana",
                      "de": "DE", "minimo": "Mín.", "q1": "Q1", "q3": "Q3", "maximo": "Máx."}


# ---------------------------------------------------------------------------
# Plan

def cargar_plan(ruta):
    ruta = Path(ruta)
    if not ruta.is_file():
        raise dc.ErrorDatos(f"no existe el plan: {ruta}")
    try:
        plan = json.loads(ruta.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise dc.ErrorDatos(f"el plan no es JSON válido: {error}")
    if not isinstance(plan, dict):
        raise dc.ErrorDatos("el plan debe ser un objeto JSON")
    datos = plan.get("datos")
    if not isinstance(datos, dict) or not datos.get("archivo"):
        raise dc.ErrorDatos("falta \"datos\": {\"archivo\": ...} en el plan")
    tablas = plan.get("tablas")
    if not isinstance(tablas, list) or not tablas:
        raise dc.ErrorDatos("falta la lista \"tablas\" en el plan")
    ids = set()
    for i, t in enumerate(tablas):
        if not isinstance(t, dict):
            raise dc.ErrorDatos(f"la tabla {i + 1} no es un objeto")
        ident = t.get("id")
        if not ident or not re.fullmatch(r"[A-Za-z0-9_\-]+", str(ident)):
            raise dc.ErrorDatos(f"la tabla {i + 1} necesita un \"id\" con letras, números, - o _")
        if ident in ids:
            raise dc.ErrorDatos(f"id de tabla repetido: {ident}")
        ids.add(ident)
        if t.get("tipo") not in TIPOS_TABLA:
            raise dc.ErrorDatos(f"tabla {ident}: \"tipo\" debe ser uno de {', '.join(TIPOS_TABLA)}")
    for f in plan.get("filtros") or []:
        if f.get("op") not in OPERADORES:
            raise dc.ErrorDatos(f"filtro con operador inválido {f.get('op')!r}; use {', '.join(OPERADORES)}")
    return plan


def ruta_datos(plan, base):
    return (Path(base) / plan["datos"]["archivo"]).resolve()


def texto_valor(v):
    """Forma de texto canónica de un valor (para categorías y comparaciones)."""
    if dc.es_en_blanco(v):
        return None
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() and abs(v) < 1e15 else repr(v)
    if isinstance(v, (dt.datetime, dt.date)):
        return v.isoformat(sep=" ") if isinstance(v, dt.datetime) else v.isoformat()
    return str(v).strip()


def _comprobar_columna(df, columna, donde):
    if columna not in df.columns:
        parecidas = difflib.get_close_matches(str(columna), [str(c) for c in df.columns], n=3)
        extra = f"; ¿quiso decir {', '.join(repr(p) for p in parecidas)}?" if parecidas else ""
        raise dc.ErrorDatos(f"{donde}: la columna {columna!r} no existe{extra}")


def preparar_datos(plan, base):
    """Lee, marca faltantes, recodifica y filtra. Devuelve (df, info, avisos).

    El índice del DataFrame es la fila del archivo (encabezado = fila 1).
    Las celdas quedan como texto canónico (o None si faltan); la
    conversión a número se hace al calcular cada tabla.
    """
    datos = plan["datos"]
    ruta = ruta_datos(plan, base)
    sep = datos.get("separador")
    if sep in ("\\t", "tab", "tabulador"):
        sep = "\t"
    df, info = dc.leer_tabla(ruta, hoja=datos.get("hoja"), separador=sep,
                             codificacion=datos.get("codificacion"), decimal=datos.get("decimal"))
    avisos = []
    if info["filas_malformadas"]:
        m = info["filas_malformadas"]
        raise dc.ErrorDatos(f"{len(m)} filas con distinto número de campos que el encabezado (p. ej. fila "
                            f"{m[0]['fila']}: {m[0]['campos']} de {m[0]['esperados']}); revise el separador "
                            "o el archivo con perfilar_datos.py")
    df.index = range(2, len(df) + 2)
    filas_leidas = len(df)
    tokens = {texto_valor(x) for x in (datos.get("faltantes") or [])}
    tokens.discard(None)
    faltantes_declarados = Counter()

    def limpiar(v):
        t = texto_valor(v)
        if t is not None and t in tokens:
            faltantes_declarados[t] += 1
            return None
        return t

    df = df.apply(lambda col: col.map(limpiar)).astype(object)
    df = df.astype(object).where(df.notna(), None)

    recodificaciones = {}
    for columna, mapa in (plan.get("recodificar") or {}).items():
        _comprobar_columna(df, columna, "recodificar")
        mapa = {str(k): v for k, v in mapa.items()}
        sin_cambio = Counter(v for v in df[columna] if v is not None and v not in mapa)
        df[columna] = df[columna].map(lambda v: v if v is None or v not in mapa else
                                      (None if mapa[v] is None else str(mapa[v])))
        df[columna] = df[columna].astype(object).where(df[columna].notna(), None)
        recodificaciones[columna] = {"mapa": mapa, "valores_sin_cambio": dict(sorted(sin_cambio.items()))}

    filtros = []
    decimal = info.get("decimal") or "."
    for f in plan.get("filtros") or []:
        columna, op, valor = f.get("columna"), f["op"], f.get("valor")
        _comprobar_columna(df, columna, "filtros")
        antes = len(df)
        s = df[columna]
        if op == "no_faltante":
            mascara = s.notna()
        elif op in ("==", "!=", "en", "no_en"):
            lista = valor if isinstance(valor, list) else [valor]
            lista = {texto_valor(x) for x in lista}
            dentro = s.map(lambda v: v in lista)
            mascara = dentro if op in ("==", "en") else (~dentro & s.notna())
        else:
            numeros = serie_numerica(df, columna, decimal, f"filtro {columna} {op}")
            limite = float(valor)
            mascara = {">": numeros > limite, ">=": numeros >= limite,
                       "<": numeros < limite, "<=": numeros <= limite}[op]
        df = df[mascara.astype(bool)]
        filtros.append({"columna": columna, "op": op, "valor": valor,
                        "filas_antes": antes, "filas_despues": len(df)})
    if len(df) == 0:
        raise dc.ErrorDatos("los filtros no dejan ninguna fila")
    info_prep = {"lectura": info, "filas_leidas": filas_leidas, "filas_usadas": len(df),
                 "faltantes_declarados": dict(sorted(faltantes_declarados.items())),
                 "recodificaciones": recodificaciones, "filtros": filtros}
    return df, info_prep, avisos


def serie_numerica(df, columna, decimal, donde):
    """Columna como números (NaN si falta). Error si hay texto no numérico."""
    import pandas as pd
    _comprobar_columna(df, columna, donde)
    valores, malos = [], []
    for fila, v in df[columna].items():
        if v is None:
            valores.append(math.nan)
            continue
        numero = dc.a_numero(v, decimal)
        if numero is None:
            malos.append((fila, v))
            valores.append(math.nan)
        else:
            valores.append(numero)
    if malos:
        ejemplos = ", ".join(f"fila {f}: {v!r}" for f, v in malos[:5])
        raise dc.ErrorDatos(f"{donde}: la columna {columna!r} tiene {len(malos)} valores no numéricos "
                            f"({ejemplos}). Declárelos en \"faltantes\" si son sin dato, o corrija la "
                            "lectura (\"decimal\"); no se descartan en silencio")
    return pd.Series(valores, index=df.index, dtype="float64")


def serie_fechas(df, columna, formato, donde):
    """(lista de datetime|None por fila, excluidas, aviso). Error si el orden
    día/mes no se puede decidir."""
    _comprobar_columna(df, columna, donde)
    fechas, malas, formatos = [], [], Counter()
    for fila, v in df[columna].items():
        if v is None:
            fechas.append(None)
            continue
        if formato:
            try:
                fechas.append(dt.datetime.strptime(v, formato))
            except ValueError:
                fechas.append(None)
                malas.append((fila, v))
            continue
        fecha, forma = dc.analizar_fecha(v)
        if fecha is None:
            malas.append((fila, v))
        else:
            formatos[forma] += 1
        fechas.append(fecha)
    if not formato:
        if formatos.get("MM/DD/AAAA") and formatos.get("DD/MM/AAAA"):
            raise dc.ErrorDatos(f"{donde}: la columna {columna!r} mezcla día/mes y mes/día; "
                                "declare \"formato_fecha\"")
        if formatos.get("DD/MM o MM/DD") and not (formatos.get("DD/MM/AAAA") or formatos.get("MM/DD/AAAA")):
            raise dc.ErrorDatos(f"{donde}: no se puede saber si {columna!r} es día/mes o mes/día; "
                                "declare \"formato_fecha\" (p. ej. \"%d/%m/%Y\")")
        if formatos.get("DD/MM o MM/DD") and formatos.get("MM/DD/AAAA"):
            fechas = [None if f is None else f for f in fechas]
            raise dc.ErrorDatos(f"{donde}: fechas en formato mes/día con casos ambiguos; "
                                "declare \"formato_fecha\" (\"%m/%d/%Y\")")
    return fechas, malas


# ---------------------------------------------------------------------------
# Cálculos

def _f(x):
    """float de Python o None (nunca NaN)."""
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) or math.isinf(x) else x


def _pct(parte, todo):
    return None if not todo else 100.0 * parte / todo


def ordenar_categorias(valores, orden=None):
    conteo = Counter(valores)
    if orden:
        orden = [str(x) for x in orden]
        resto = sorted((c for c in conteo if c not in orden), key=lambda c: (-conteo[c], c))
        return orden + resto, [c for c in resto]
    return sorted(conteo, key=lambda c: (-conteo[c], c)), []


def estadisticos(serie):
    validos = serie.dropna()
    n = int(validos.count())
    r = {"n": n, "faltantes": int(serie.isna().sum())}
    if n == 0:
        r.update({k: None for k in ("media", "mediana", "de", "minimo", "q1", "q3", "maximo")})
        return r
    r.update({"media": _f(validos.mean()), "mediana": _f(validos.median()),
              "de": _f(validos.std(ddof=1)) if n > 1 else None,
              "minimo": _f(validos.min()), "q1": _f(validos.quantile(0.25)),
              "q3": _f(validos.quantile(0.75)), "maximo": _f(validos.max())})
    return r


def cargar_scipy():
    if os.environ.get("ANALISIS_SIN_SCIPY", "").strip() in ("1", "si", "sí", "true"):
        return None
    try:
        from scipy import stats
        return stats
    except ImportError:
        return None


class Calculo:
    def __init__(self, plan, df, decimal):
        self.plan, self.df, self.decimal = plan, df, decimal
        self.cifras, self.avisos = [], []
        self.stats = cargar_scipy()
        self.orden = {k: v for k, v in (plan.get("orden") or {}).items()}

    def cifra(self, clave, valor, tipo):
        valor = _f(valor) if not isinstance(valor, int) else valor
        if valor is not None:
            self.cifras.append({"clave": clave, "valor": valor, "tipo": tipo})

    def sin_prueba(self, t):
        msg = f"{t['id']}: prueba «{t['prueba']}» omitida porque scipy no está instalado"
        self.avisos.append(msg)
        return {"omitida": "scipy no está instalado"}

    # -- frecuencias
    def frecuencias(self, t):
        var = t.get("variable")
        _comprobar_columna(self.df, var, f"tabla {t['id']}")
        s = self.df[var]
        validos = [v for v in s if v is not None]
        conteo = Counter(validos)
        cats, extra = ordenar_categorias(validos, self.orden.get(var))
        if extra and self.orden.get(var):
            self.avisos.append(f"{t['id']}: categorías fuera de \"orden\" de {var!r}: {', '.join(extra)}")
        total, n_val = len(s), len(validos)
        filas = []
        for c in cats:
            n = conteo.get(c, 0)
            filas.append({"categoria": c, "n": n, "porcentaje_validos": _pct(n, n_val),
                          "porcentaje_total": _pct(n, total)})
            self.cifra(f"{t['id']}|{c}|n", n, "conteo")
            self.cifra(f"{t['id']}|{c}|porcentaje_validos", _pct(n, n_val), "porcentaje")
            if total != n_val:
                self.cifra(f"{t['id']}|{c}|porcentaje_total", _pct(n, total), "porcentaje")
        self.cifra(f"{t['id']}|n_validos", n_val, "conteo")
        self.cifra(f"{t['id']}|n_total", total, "conteo")
        if total != n_val:
            self.cifra(f"{t['id']}|faltantes|n", total - n_val, "conteo")
            self.cifra(f"{t['id']}|faltantes|porcentaje_total", _pct(total - n_val, total), "porcentaje")
        return {"variable": var, "n_total": total, "n_validos": n_val, "n_faltantes": total - n_val,
                "filas": filas}

    # -- cruzada
    def cruzada(self, t):
        fv, cv = t.get("filas"), t.get("columnas")
        for c in (fv, cv):
            _comprobar_columna(self.df, c, f"tabla {t['id']}")
        pares = [(a, b) for a, b in zip(self.df[fv], self.df[cv]) if a is not None and b is not None]
        excluidas = len(self.df) - len(pares)
        cf, _ = ordenar_categorias([a for a, _ in pares], self.orden.get(fv))
        cc, _ = ordenar_categorias([b for _, b in pares], self.orden.get(cv))
        conteo = Counter(pares)
        n = len(pares)
        tot_f = {f: sum(conteo.get((f, c), 0) for c in cc) for f in cf}
        tot_c = {c: sum(conteo.get((f, c), 0) for f in cf) for c in cc}
        conteos = {f: {**{c: conteo.get((f, c), 0) for c in cc}, "Total": tot_f[f]} for f in cf}
        conteos["Total"] = {**tot_c, "Total": n}
        for f, fila in conteos.items():
            for c, valor in fila.items():
                self.cifra(f"{t['id']}|n|{f}|{c}", valor, "conteo")
        pedidos = t.get("porcentajes", "fila")
        pedidos = pedidos if isinstance(pedidos, list) else [pedidos]
        porcentajes = {}
        for modo in pedidos:
            if modo not in ("fila", "columna", "total"):
                raise dc.ErrorDatos(f"tabla {t['id']}: \"porcentajes\" debe ser fila, columna o total")
            tabla = {}
            for f in cf + ["Total"]:
                tabla[f] = {}
                for c in cc + ["Total"]:
                    valor = conteos[f][c]
                    if modo == "fila":
                        base = tot_f[f] if f != "Total" else n
                    elif modo == "columna":
                        base = tot_c[c] if c != "Total" else n
                    else:
                        base = n
                    tabla[f][c] = _pct(valor, base)
                    self.cifra(f"{t['id']}|pct_{modo}|{f}|{c}", tabla[f][c], "porcentaje")
            porcentajes[modo] = tabla
        r = {"filas": fv, "columnas": cv, "categorias_filas": cf, "categorias_columnas": cc,
             "n": n, "excluidas_por_faltante": excluidas, "conteos": conteos, "porcentajes": porcentajes}
        if excluidas:
            self.cifra(f"{t['id']}|excluidas", excluidas, "conteo")
        if t.get("prueba"):
            if t["prueba"] != "chi2":
                raise dc.ErrorDatos(f"tabla {t['id']}: la única prueba de una tabla cruzada es \"chi2\"")
            r["prueba"] = self.sin_prueba(t) if self.stats is None else self.chi2(t, cf, cc, conteos, n)
        return r

    def chi2(self, t, cf, cc, conteos, n):
        matriz = [[conteos[f][c] for c in cc] for f in cf]
        if len(cf) < 2 or len(cc) < 2:
            self.avisos.append(f"{t['id']}: chi cuadrado no aplicable (hace falta al menos 2×2)")
            return {"omitida": "tabla menor que 2×2"}
        chi, p, gl, esperadas = self.stats.chi2_contingency(matriz, correction=False)
        bajas = sum(1 for fila in esperadas for e in fila if e < 5)
        celdas = len(cf) * len(cc)
        v = math.sqrt(chi / (n * (min(len(cf), len(cc)) - 1)))
        r = {"prueba": "chi cuadrado de Pearson (sin corrección de Yates)", "estadistico": _f(chi),
             "gl": int(gl), "p_valor": _f(p), "v_cramer": _f(v),
             "esperadas_menores_5": bajas, "pct_esperadas_menores_5": _pct(bajas, celdas),
             "esperada_minima": _f(min(e for fila in esperadas for e in fila))}
        self.cifra(f"{t['id']}|chi2|estadistico", chi, "prueba")
        self.cifra(f"{t['id']}|chi2|gl", int(gl), "gl")
        self.cifra(f"{t['id']}|chi2|p_valor", p, "p_valor")
        self.cifra(f"{t['id']}|chi2|v_cramer", v, "prueba")
        if bajas / celdas > 0.2:
            self.avisos.append(f"{t['id']}: {bajas} de {celdas} frecuencias esperadas son menores que 5; "
                               "el chi cuadrado no es fiable")
        return r

    # -- resumen
    def resumen(self, t):
        variables = t.get("variables") or ([t["variable"]] if t.get("variable") else [])
        if not variables:
            raise dc.ErrorDatos(f"tabla {t['id']}: falta \"variables\"")
        por = t.get("por")
        numeros = {v: serie_numerica(self.df, v, self.decimal, f"tabla {t['id']}") for v in variables}
        filas = []
        if por:
            _comprobar_columna(self.df, por, f"tabla {t['id']}")
            grupo = self.df[por]
            con_grupo = grupo.notna()
            grupos, extra = ordenar_categorias([g for g in grupo if g is not None], self.orden.get(por))
            excluidas = int((~con_grupo).sum())
        for v in variables:
            s = numeros[v]
            if por:
                for g in grupos:
                    e = estadisticos(s[grupo == g])
                    filas.append({"variable": v, "grupo": g, **e})
                e = estadisticos(s[con_grupo])
                filas.append({"variable": v, "grupo": "Total", **e})
            else:
                filas.append({"variable": v, "grupo": None, **estadisticos(s)})
        for fila in filas:
            for k in ESTADISTICOS:
                clave = f"{t['id']}|{fila['variable']}|{fila['grupo'] or 'Total'}|{k}"
                self.cifra(clave, fila[k], "conteo" if k in ("n", "faltantes") else "estadistico")
        r = {"variables": variables, "por": por, "filas": filas}
        if por:
            r["grupos"] = grupos
            r["excluidas_sin_grupo"] = excluidas
            if excluidas:
                self.cifra(f"{t['id']}|excluidas_sin_grupo", excluidas, "conteo")
        if t.get("prueba"):
            if not por:
                raise dc.ErrorDatos(f"tabla {t['id']}: una prueba de grupos necesita \"por\"")
            if t["prueba"] not in PRUEBAS_GRUPOS:
                raise dc.ErrorDatos(f"tabla {t['id']}: \"prueba\" debe ser {', '.join(PRUEBAS_GRUPOS)}")
            if self.stats is None:
                r["pruebas"] = self.sin_prueba(t)
            else:
                r["pruebas"] = {v: self.prueba_grupos(t, v, [numeros[v][grupo == g].dropna() for g in grupos], grupos)
                                for v in variables}
        return r

    def prueba_grupos(self, t, var, muestras, grupos):
        tipo = t["prueba"]
        st = self.stats
        if any(len(m) < 2 for m in muestras):
            self.avisos.append(f"{t['id']}: prueba omitida para {var!r} (algún grupo tiene menos de 2 casos)")
            return {"omitida": "algún grupo tiene menos de 2 casos"}
        if tipo in ("t", "mann-whitney") and len(muestras) != 2:
            raise dc.ErrorDatos(f"tabla {t['id']}: la prueba «{tipo}» compara exactamente 2 grupos "
                                f"(hay {len(muestras)}); use anova o kruskal, o un filtro")
        if tipo == "t":
            res = st.ttest_ind(muestras[0], muestras[1], equal_var=False)
            a, b = muestras
            va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
            gl = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
            r = {"prueba": "t de Welch (varianzas distintas), bilateral", "estadistico": _f(res.statistic),
                 "gl": _f(gl), "p_valor": _f(res.pvalue), "diferencia_medias": _f(a.mean() - b.mean()),
                 "grupos": grupos}
        elif tipo == "mann-whitney":
            res = st.mannwhitneyu(muestras[0], muestras[1], alternative="two-sided")
            r = {"prueba": "U de Mann-Whitney, bilateral", "estadistico": _f(res.statistic),
                 "p_valor": _f(res.pvalue), "grupos": grupos}
        elif tipo == "anova":
            res = st.f_oneway(*muestras)
            n = sum(len(m) for m in muestras)
            r = {"prueba": "ANOVA de un factor", "estadistico": _f(res.statistic),
                 "gl": [len(muestras) - 1, n - len(muestras)], "p_valor": _f(res.pvalue), "grupos": grupos}
        else:
            res = st.kruskal(*muestras)
            r = {"prueba": "H de Kruskal-Wallis", "estadistico": _f(res.statistic),
                 "gl": len(muestras) - 1, "p_valor": _f(res.pvalue), "grupos": grupos}
        base = f"{t['id']}|{var}|{tipo}"
        self.cifra(f"{base}|estadistico", r["estadistico"], "prueba")
        self.cifra(f"{base}|p_valor", r["p_valor"], "p_valor")
        gl = r.get("gl")
        for i, g in enumerate(gl if isinstance(gl, list) else [gl] if gl is not None else []):
            self.cifra(f"{base}|gl{i + 1 if isinstance(gl, list) else ''}", g, "gl")
        if "diferencia_medias" in r:
            self.cifra(f"{base}|diferencia_medias", r["diferencia_medias"], "estadistico")
        return r

    # -- serie
    def serie(self, t):
        columna = t.get("fecha")
        periodo = t.get("periodo", "mes")
        if periodo not in PERIODOS:
            raise dc.ErrorDatos(f"tabla {t['id']}: \"periodo\" debe ser {', '.join(PERIODOS)}")
        fechas, malas = serie_fechas(self.df, columna, t.get("formato_fecha"), f"tabla {t['id']}")
        variable, estad = t.get("variable"), t.get("estadistico", "conteo" if not t.get("variable") else "media")
        if estad not in ("conteo", "media", "suma"):
            raise dc.ErrorDatos(f"tabla {t['id']}: \"estadistico\" debe ser conteo, media o suma")
        if estad != "conteo" and not variable:
            raise dc.ErrorDatos(f"tabla {t['id']}: \"{estad}\" necesita \"variable\"")
        numeros = serie_numerica(self.df, variable, self.decimal, f"tabla {t['id']}") if variable else None
        sin_fecha = sum(1 for f in fechas if f is None)
        if malas:
            self.avisos.append(f"{t['id']}: {len(malas)} fechas no se pudieron leer y quedan fuera "
                               f"(p. ej. fila {malas[0][0]}: {malas[0][1]!r})")
        validas = [(i, f) for i, f in zip(self.df.index, fechas) if f is not None]
        if not validas:
            raise dc.ErrorDatos(f"tabla {t['id']}: ninguna fecha válida en {columna!r}")
        grupos = {}
        for i, f in validas:
            grupos.setdefault(inicio_periodo(f, periodo), []).append(i)
        actual, ultimo = min(grupos), max(grupos)
        filas = []
        while actual <= ultimo:
            siguiente = siguiente_periodo(actual, periodo)
            indices = grupos.get(actual, [])
            if numeros is not None:
                vals = numeros.loc[indices].dropna() if indices else numeros.iloc[0:0]
                n = int(vals.count())
                valor = None if n == 0 else _f(vals.mean() if estad == "media" else vals.sum())
                if estad == "conteo":
                    valor = None
            else:
                n, valor = len(indices), None
            etiqueta = etiqueta_periodo(actual, periodo)
            filas.append({"periodo": etiqueta, "inicio": actual.isoformat(sep=" "),
                          "fin": siguiente.isoformat(sep=" "), "n": n, "valor": valor})
            self.cifra(f"{t['id']}|{etiqueta}|n", n, "conteo")
            if valor is not None:
                self.cifra(f"{t['id']}|{etiqueta}|{estad}", valor, "estadistico")
            actual = siguiente
        if sin_fecha:
            self.cifra(f"{t['id']}|sin_fecha", sin_fecha, "conteo")
        return {"fecha": columna, "periodo": periodo, "variable": variable, "estadistico": estad,
                "formato_fecha": t.get("formato_fecha"), "sin_fecha": sin_fecha, "filas": filas,
                "nota": "periodos sin casos se muestran con n = 0; la media no se completa"}


def inicio_periodo(f, periodo):
    if periodo == "hora":
        return f.replace(minute=0, second=0, microsecond=0)
    d = f.replace(hour=0, minute=0, second=0, microsecond=0)
    if periodo == "dia":
        return d
    if periodo == "semana":
        return d - dt.timedelta(days=d.weekday())
    if periodo == "mes":
        return d.replace(day=1)
    if periodo == "trimestre":
        return d.replace(month=3 * ((d.month - 1) // 3) + 1, day=1)
    return d.replace(month=1, day=1)


def siguiente_periodo(f, periodo):
    if periodo == "hora":
        return f + dt.timedelta(hours=1)
    if periodo == "dia":
        return f + dt.timedelta(days=1)
    if periodo == "semana":
        return f + dt.timedelta(days=7)
    meses = {"mes": 1, "trimestre": 3, "año": 12}[periodo]
    total = f.year * 12 + f.month - 1 + meses
    return f.replace(year=total // 12, month=total % 12 + 1)


def etiqueta_periodo(f, periodo):
    if periodo == "hora":
        return f.strftime("%Y-%m-%d %H:00")
    if periodo in ("dia", "semana"):
        return f.strftime("%Y-%m-%d")
    if periodo == "mes":
        return f.strftime("%Y-%m")
    if periodo == "trimestre":
        return f"{f.year}-T{(f.month - 1) // 3 + 1}"
    return str(f.year)


# ---------------------------------------------------------------------------
# Salidas

def decimales_de(plan, t, tipo):
    redondeo = {**REDONDEO_POR_DEFECTO, **(plan.get("redondeo") or {}), **(t.get("redondeo") or {})}
    return int(redondeo[tipo])


def _md_tabla(cabecera, filas):
    lineas = ["| " + " | ".join(cabecera) + " |",
              "|" + "|".join([":---"] + ["---:"] * (len(cabecera) - 1)) + "|"]
    for fila in filas:
        lineas.append("| " + " | ".join(str(x).replace("|", "\\|") for x in fila) + " |")
    return lineas


def _p(valor, decimales):
    if valor is None:
        return "—"
    minimo = 10 ** -decimales
    if valor < minimo:
        return "< " + dc.formato_es(minimo, decimales)
    return dc.formato_es(valor, decimales)


def escribir_md(plan, resultado, ruta_plan):
    meta = resultado["metadatos"]
    miles = (plan.get("formato") or {}).get("miles", "espacio")
    num = lambda v, d=0: dc.formato_es(v, d, miles)  # noqa: E731
    L = [f"# Resultados: {meta['titulo']}", ""]
    L.append(f"- Datos: `{meta['datos']['archivo']}` (sha256 {meta['datos']['sha256'][:16]}…)")
    if meta.get("fuente"):
        L.append(f"- Fuente: {meta['fuente']}")
    L.append(f"- Filas leídas: {num(meta['filas_leidas'])}; filas usadas: {num(meta['filas_usadas'])}")
    for f in meta["filtros"]:
        L.append(f"- Filtro: {f['columna']} {f['op']} {f['valor']!r} "
                 f"({num(f['filas_antes'])} → {num(f['filas_despues'])} filas)")
    falt = "celda vacía o en blanco"
    if meta["faltantes_declarados"]:
        falt += "; además " + ", ".join(f"{k!r} ({v})" for k, v in meta["faltantes_declarados"].items())
    L.append(f"- Faltantes: {falt}. Nada se imputa.")
    for col, rec in meta["recodificaciones"].items():
        L.append(f"- Recodificado {col!r}: " + ", ".join(f"{k} → {v}" for k, v in rec["mapa"].items()))
    r = meta["redondeo"]
    L.append(f"- Redondeo (mitad hacia arriba): porcentajes {r['porcentaje']} decimal(es), "
             f"estadísticos {r['estadistico']}, pruebas {r['prueba']}, p {r['p_valor']}. Coma decimal.")
    L.append(f"- Rehacer: `python analizar.py {Path(ruta_plan).name}` desde la carpeta del plan. "
             f"Generado: {meta['generado']}.")
    L.append("- Copie las cifras tal como aparecen aquí: `cifras_texto.py` las coteja con resultados.json.")
    if resultado["avisos"]:
        L += ["", "**Avisos (lo que no se pudo calcular o quedó fuera):**", ""]
        L += [f"- {a}" for a in resultado["avisos"]]
    for t in resultado["tablas"]:
        L += ["", f"## {t['id']}. {t.get('titulo') or t['tipo']}", ""]
        dp = decimales_de(plan, t, "porcentaje")
        de = decimales_de(plan, t, "estadistico")
        if t["tipo"] == "frecuencias":
            hay_falt = t["n_faltantes"] > 0
            cab = [t["variable"], "n", "% válidos"] + (["% del total"] if hay_falt else [])
            filas = [[f["categoria"], num(f["n"]), num(f["porcentaje_validos"], dp)] +
                     ([num(f["porcentaje_total"], dp)] if hay_falt else []) for f in t["filas"]]
            if hay_falt:
                filas.append(["Sin dato", num(t["n_faltantes"]), "", num(100 * t["n_faltantes"] / t["n_total"], dp)])
            filas.append(["Total", num(t["n_total"] if hay_falt else t["n_validos"]),
                          num(100, dp), num(100, dp)][:len(cab)] if not hay_falt else
                         ["Total", num(t["n_total"]), num(100, dp) + " (de válidos)", num(100, dp)])
            L += _md_tabla(cab, filas)
            L += ["", f"n válidos = {num(t['n_validos'])}; sin dato = {num(t['n_faltantes'])}."]
        elif t["tipo"] == "cruzada":
            cc = t["categorias_columnas"] + ["Total"]
            L += [f"Frecuencias (filas: {t['filas']}; columnas: {t['columnas']})", ""]
            L += _md_tabla([t["filas"]] + cc, [[f] + [num(t["conteos"][f][c]) for c in cc]
                                                for f in t["categorias_filas"] + ["Total"]])
            for modo, tabla in t["porcentajes"].items():
                L += ["", f"Porcentajes por {modo}" if modo != "total" else "Porcentajes sobre el total", ""]
                L += _md_tabla([t["filas"]] + cc, [[f] + [num(tabla[f][c], dp) for c in cc]
                                                    for f in t["categorias_filas"] + ["Total"]])
            nota = f"n = {num(t['n'])}"
            if t["excluidas_por_faltante"]:
                nota += f"; excluidas por dato faltante en alguna de las dos variables: {num(t['excluidas_por_faltante'])}"
            L += ["", nota + "."]
            if "prueba" in t:
                L += ["", texto_prueba(plan, t, t["prueba"])]
        elif t["tipo"] == "resumen":
            cab = ["Variable"] + (["Grupo"] if t["por"] else []) + [NOMBRE_ESTADISTICO[k] for k in ESTADISTICOS]
            pedido = next((x for x in plan["tablas"] if x["id"] == t["id"]), {})
            factor = 100 if pedido.get("mostrar_por_100") else 1
            filas = []
            for f in t["filas"]:
                fila = [f["variable"]] + ([f["grupo"]] if t["por"] else [])
                fila += [num(f[k]) if k in ("n", "faltantes") else
                         num(None if f[k] is None else f[k] * factor, de) for k in ESTADISTICOS]
                filas.append(fila)
            L += _md_tabla(cab, filas)
            L += [""]
            if factor != 1:
                L += ["Valores multiplicados por 100 para leerlos como porcentajes (resultados.json "
                      "guarda la escala original)."]
            if t["por"]:
                L += [f"Grupos según {t['por']}." + (f" Excluidas por no tener grupo: {num(t['excluidas_sin_grupo'])}."
                                                         if t.get("excluidas_sin_grupo") else "")]
            L += ["DE: desviación estándar muestral (n − 1). Q1 y Q3: cuartiles por interpolación lineal."]
            if "pruebas" in t:
                if "omitida" in t["pruebas"]:
                    L += ["", f"Prueba omitida: {t['pruebas']['omitida']}."]
                else:
                    for var, pr in t["pruebas"].items():
                        L += ["", f"{var}: " + texto_prueba(plan, t, pr)]
        elif t["tipo"] == "serie":
            etiqueta = {"conteo": "n", "media": f"Media de {t['variable']}", "suma": f"Suma de {t['variable']}"}[t["estadistico"]]
            cab = ["Periodo", "n"] + ([etiqueta] if t["estadistico"] != "conteo" else [])
            filas = [[f["periodo"], num(f["n"])] + ([num(f["valor"], de)] if t["estadistico"] != "conteo" else [])
                     for f in t["filas"]]
            L += _md_tabla(cab, filas)
            L += ["", f"Periodo: {t['periodo']} (columna {t['fecha']}). " + t["nota"] + "."]
            if t["sin_fecha"]:
                L += [f"Filas sin fecha válida (excluidas): {num(t['sin_fecha'])}."]
        if t.get("figura_archivo"):
            L += ["", f"Figura: `{t['figura_archivo']}`"]
    return "\n".join(L) + "\n"


def texto_prueba(plan, t, pr):
    if "omitida" in pr:
        return f"Prueba omitida: {pr['omitida']}."
    dpr, dpv = decimales_de(plan, t, "prueba"), decimales_de(plan, t, "p_valor")
    partes = [pr["prueba"] + ":", f"estadístico = {dc.formato_es(pr['estadistico'], dpr)}"]
    gl = pr.get("gl")
    if gl is not None:
        partes.append("gl = " + (", ".join(dc.formato_es(g, 0) for g in gl) if isinstance(gl, list)
                                 else dc.formato_es(gl, 0 if float(gl).is_integer() else dpr)))
    pv = _p(pr["p_valor"], dpv)
    partes.append(f"p {pv}" if pv.startswith("<") else f"p = {pv}")
    if pr.get("v_cramer") is not None:
        partes.append(f"V de Cramér = {dc.formato_es(pr['v_cramer'], dpr)}")
        if pr.get("esperadas_menores_5"):
            partes.append(f"frecuencias esperadas < 5: {pr['esperadas_menores_5']}")
    if pr.get("diferencia_medias") is not None:
        pedido = next((x for x in plan["tablas"] if x["id"] == t["id"]), {})
        factor = 100 if pedido.get("mostrar_por_100") else 1
        partes.append(f"diferencia de medias ({pr['grupos'][0]} − {pr['grupos'][1]}) = "
                      f"{dc.formato_es(pr['diferencia_medias'] * factor, decimales_de(plan, t, 'estadistico'))}"
                      + (" (× 100)" if factor != 1 else ""))
    return " ".join(partes[:2]) + ("; " + "; ".join(partes[2:]) if len(partes) > 2 else "") + "."


# ---------------------------------------------------------------------------
# Figuras (matplotlib, sobrias: ancho 16 cm, apto para una página carta)

ANCHO_PULGADAS = 16 / 2.54
COLOR = "#4a4a4a"


def figuras(plan, resultado, carpeta):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import FuncFormatter
    except ImportError:
        resultado["avisos"].append("figuras omitidas: matplotlib no está instalado")
        return
    import textwrap
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "svg.hashsalt": "analisis", "axes.edgecolor": "#333333"})
    coma = FuncFormatter(lambda x, _: (f"{x:.10g}").replace(".", ","))
    carpeta.mkdir(parents=True, exist_ok=True)
    envolver = lambda s: "\n".join(textwrap.wrap(str(s), 28)) or str(s)  # noqa: E731
    for t in resultado["tablas"]:
        pedido = next((x for x in plan["tablas"] if x["id"] == t["id"]), {})
        if not pedido.get("figura"):
            continue
        fig = None
        if t["tipo"] == "frecuencias":
            cats = [f["categoria"] for f in t["filas"]][::-1]
            vals = [f["porcentaje_validos"] or 0 for f in t["filas"]][::-1]
            fig, ax = plt.subplots(figsize=(ANCHO_PULGADAS, max(2.2, 0.35 * len(cats) + 1)))
            ax.barh([envolver(c) for c in cats], vals, color=COLOR)
            ax.set_xlabel(pedido.get("etiqueta_x", "Porcentaje de casos válidos (%)"))
        elif t["tipo"] == "cruzada":
            modo = next(iter(t["porcentajes"]), None)
            cf, cc = t["categorias_filas"], t["categorias_columnas"]
            fig, ax = plt.subplots(figsize=(ANCHO_PULGADAS, 3.4))
            ancho = 0.8 / max(len(cc), 1)
            grises = [str(0.15 + 0.65 * i / max(len(cc) - 1, 1)) for i in range(len(cc))]
            for j, c in enumerate(cc):
                if modo:
                    vals = [t["porcentajes"][modo][f][c] or 0 for f in cf]
                else:
                    vals = [t["conteos"][f][c] for f in cf]
                ax.bar([i + j * ancho for i in range(len(cf))], vals, ancho, label=envolver(c), color=grises[j],
                       edgecolor="#222222", linewidth=0.4)
            ax.set_xticks([i + ancho * (len(cc) - 1) / 2 for i in range(len(cf))])
            ax.set_xticklabels([envolver(f) for f in cf])
            ax.set_ylabel(pedido.get("etiqueta_y", f"Porcentaje por {modo} (%)" if modo else "Frecuencia (n)"))
            ax.legend(title=t["columnas"], frameon=False, fontsize=8)
        elif t["tipo"] == "resumen" and t["por"]:
            var = t["variables"][0]
            datos = resultado["_series_figura"].get(t["id"], [])
            if datos:
                fig, ax = plt.subplots(figsize=(ANCHO_PULGADAS, 3.4))
                ax.boxplot([d for _, d in datos], tick_labels=[envolver(g) for g, _ in datos], widths=0.5,
                           medianprops={"color": "black"}, flierprops={"markersize": 3})
                ax.set_ylabel(pedido.get("etiqueta_y", var))
        elif t["tipo"] == "serie":
            etiquetas = [f["periodo"] for f in t["filas"]]
            vals = [f["n"] if t["estadistico"] == "conteo" else f["valor"] for f in t["filas"]]
            fig, ax = plt.subplots(figsize=(ANCHO_PULGADAS, 3.2))
            x = list(range(len(etiquetas)))
            ax.plot(x, [math.nan if v is None else v for v in vals], marker="o", markersize=3,
                    color=COLOR, linewidth=1)
            paso = max(1, len(etiquetas) // 10)
            ax.set_xticks(x[::paso])
            ax.set_xticklabels(etiquetas[::paso], rotation=45, ha="right")
            ax.set_ylabel(pedido.get("etiqueta_y", "Número de casos (n)" if t["estadistico"] == "conteo"
                                     else f"{t['estadistico'].capitalize()} de {t['variable']}"))
            ax.set_xlabel(pedido.get("etiqueta_x", f"Periodo ({t['periodo']})"))
        if fig is None:
            resultado["avisos"].append(f"{t['id']}: figura no disponible para este tipo de tabla")
            continue
        for eje in (ax.xaxis, ax.yaxis):
            if eje is ax.yaxis or t["tipo"] == "frecuencias":
                eje.set_major_formatter(coma)
        fig.tight_layout()
        destino = carpeta / f"{t['id']}.png"
        fig.savefig(destino, dpi=200, metadata={"Software": None})
        plt.close(fig)
        t["figura_archivo"] = f"figuras/{destino.name}"


# ---------------------------------------------------------------------------

def analizar(ruta_plan, salida=None, con_figuras=True):
    import numpy
    import pandas
    ruta_plan = Path(ruta_plan).resolve()
    plan = cargar_plan(ruta_plan)
    base = ruta_plan.parent
    salida = Path(salida).resolve() if salida else base / "resultados"
    df, prep, avisos = preparar_datos(plan, base)
    lectura = prep["lectura"]
    calculo = Calculo(plan, df, lectura.get("decimal") or ".")
    calculo.avisos.extend(avisos)
    calculo.cifra("datos|filas_leidas", prep["filas_leidas"], "conteo")
    calculo.cifra("datos|filas_usadas", prep["filas_usadas"], "conteo")
    tablas, series_figura = [], {}
    for t in plan["tablas"]:
        r = getattr(calculo, t["tipo"])(t)
        tablas.append({"id": t["id"], "tipo": t["tipo"], "titulo": t.get("titulo"), **r})
        if t["tipo"] == "resumen" and t.get("por") and t.get("figura"):
            s = serie_numerica(df, r["variables"][0], calculo.decimal, t["id"])
            series_figura[t["id"]] = [(g, s[df[t["por"]] == g].dropna().tolist()) for g in r["grupos"]]
    if calculo.stats is None and any(t.get("prueba") for t in plan["tablas"]):
        pass  # ya avisado por tabla
    datos = plan["datos"]
    scipy_version = None
    if calculo.stats is not None:
        import scipy
        scipy_version = scipy.__version__
    meta = {
        "titulo": plan.get("titulo") or ruta_plan.stem,
        "plan": ruta_plan.name, "plan_sha256": dc.sha256_archivo(ruta_plan),
        "datos": {"archivo": datos["archivo"], "sha256": lectura["sha256"], "bytes": lectura["bytes"],
                  "hoja": lectura.get("hoja"), "codificacion": lectura.get("codificacion"),
                  "separador": lectura.get("separador"), "decimal": lectura.get("decimal")},
        "fuente": datos.get("fuente"),
        "filas_leidas": prep["filas_leidas"], "filas_usadas": prep["filas_usadas"],
        "faltantes_declarados": prep["faltantes_declarados"],
        "recodificaciones": prep["recodificaciones"], "filtros": prep["filtros"],
        "redondeo": {**REDONDEO_POR_DEFECTO, **(plan.get("redondeo") or {}),
                     "regla": "mitad hacia arriba sobre el valor decimal (34,25 → 34,3)"},
        "metodos": {"desviacion_estandar": "muestral (n − 1)",
                    "cuartiles": "interpolación lineal (tipo 7; CUARTIL.INCLUYE)",
                    "porcentajes": "sobre casos válidos; en frecuencias también sobre el total",
                    "faltantes": "celda vacía o en blanco y valores declarados; sin imputación",
                    "categorias": "texto sin espacios al inicio ni al final; mayúsculas y tildes se respetan"},
        "versiones": {"script": VERSION, "python": platform.python_version(), "pandas": pandas.__version__,
                      "numpy": numpy.__version__, "scipy": scipy_version},
        "generado": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    resultado = {"metadatos": meta, "tablas": tablas, "avisos": calculo.avisos, "cifras": calculo.cifras,
                 "_series_figura": series_figura}
    if con_figuras and any(t.get("figura") for t in plan["tablas"]):
        figuras(plan, resultado, salida / "figuras")
    del resultado["_series_figura"]
    texto_json = json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False)
    dc.escribir_atomico(salida / "resultados.json", texto_json + "\n")
    dc.escribir_atomico(salida / "resultados.md", escribir_md(plan, resultado, ruta_plan))
    return resultado, salida


def main(argv=None):
    dc.salida_utf8()
    parser = argparse.ArgumentParser(description="Análisis descriptivo declarado en plan_analisis.json.")
    parser.add_argument("plan")
    parser.add_argument("--salida", help="carpeta de resultados (por defecto <plan>/resultados)")
    parser.add_argument("--sin-figuras", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        resultado, salida = analizar(args.plan, args.salida, not args.sin_figuras)
    except (dc.ErrorDatos, UnicodeDecodeError, LookupError, OSError, ValueError) as error:
        if args.json:
            print(json.dumps({"error": str(error)}, ensure_ascii=False))
        else:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    resumen = {"salida": str(salida), "tablas": [t["id"] for t in resultado["tablas"]],
               "cifras": len(resultado["cifras"]), "filas_usadas": resultado["metadatos"]["filas_usadas"],
               "avisos": resultado["avisos"]}
    if args.json:
        print(json.dumps(resumen, ensure_ascii=False, indent=2))
    else:
        print(f"Resultados en {salida}")
        print(f"  tablas: {', '.join(resumen['tablas'])}; cifras: {resumen['cifras']}; "
              f"filas usadas: {resumen['filas_usadas']}")
        for a in resumen["avisos"]:
            print(f"  AVISO: {a}")
    return 1 if resultado["avisos"] else 0


if __name__ == "__main__":
    sys.exit(main())
