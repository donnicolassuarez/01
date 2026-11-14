#!/usr/bin/env python3
"""Prueba automática de la skill analisis-de-datos con datos reales.

Usa los conjuntos versionados en pruebas/casos/datos/ (si faltan, los
descarga de Zenodo y verifica su md5; si no se puede, informa
"omitido"). Deriva variantes "sucias" para el perfil, corre el análisis
con dos planes reales, comprueba a mano (pandas por su cuenta) cifras
de resultados.json, exporta el xlsx en los dos modos y lo recalcula con
LibreOffice, y coteja un texto con discrepancias sembradas.

Salidas en pruebas/salida/caso_datos/. Imprime una tabla caso →
esperado / obtenido y sale con 1 si algún caso falla.

Uso: python pruebas/probar_datos.py
"""
import csv
import hashlib
import io
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPTS = RAIZ / "skills" / "analisis-de-datos" / "scripts"
CASOS = RAIZ / "pruebas" / "casos"
DATOS = CASOS / "datos"
SALIDA = RAIZ / "pruebas" / "salida" / "caso_datos"
PY = sys.executable

FUENTES = {
    "PLoSOneData_ExamsDisWomen.csv": ("https://zenodo.org/api/records/4947590/files/"
                                      "PLoSOneData_ExamsDisWomen.csv/content",
                                      "236c38983d349f4f23bcde48e55e08bd"),
    "Respuestas_Encuesta.csv": ("https://zenodo.org/api/records/12702201/files/Respuestas_Encuesta.csv/content",
                                "6444dea8d87c4529be8e04bc41466101"),
}

resultados = []  # (caso, esperado, obtenido, estado)


def registrar(caso, esperado, obtenido, ok):
    ok = bool(ok) if ok is not None else None
    resultados.append((caso, str(esperado), str(obtenido), "ok" if ok is True else ("OMITIDO" if ok is None else "FALLA")))


def correr(script, *args, entorno=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.update(entorno or {})
    p = subprocess.run([PY, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True,
                       encoding="utf-8", env=env, timeout=600)
    return p.returncode, p.stdout, p.stderr


def correr_json(script, *args, entorno=None):
    codigo, out, err = correr(script, *args, "--json", entorno=entorno)
    try:
        return codigo, json.loads(out)
    except json.JSONDecodeError:
        return codigo, {"_salida": out, "_error": err}


def cerca(a, b, rel=1e-9):
    return bool(a is not None and b is not None and abs(a - b) <= rel * max(1.0, abs(b)))


# ---------------------------------------------------------------------------
def conseguir_datos():
    disponibles = {}
    for nombre, (url, md5) in FUENTES.items():
        ruta = DATOS / nombre
        if not ruta.exists():
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    contenido = r.read()
                if hashlib.md5(contenido).hexdigest() != md5:
                    raise ValueError("md5 distinto")
                destino = SALIDA / "descargas" / nombre
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_bytes(contenido)
                ruta = destino
            except Exception as error:  # sin red o sin acceso
                registrar(f"datos {nombre}", "disponible", f"omitido: {error}", None)
                continue
        disponibles[nombre] = ruta
        md5_ok = hashlib.md5(ruta.read_bytes()).hexdigest() == md5
        registrar(f"datos {nombre} íntegros (md5)", md5, "igual" if md5_ok else "distinto", md5_ok)
    return disponibles


def preparar_trabajo(nombre, plan, datos):
    base = SALIDA / nombre / "analisis"
    (base / "datos").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(CASOS / "datos" / plan, base / "plan_analisis.json")
    shutil.copyfile(datos, base / "datos" / datos.name)
    return base


def leer_filas(ruta, sep, codificacion):
    texto = ruta.read_bytes().decode(codificacion)
    return list(csv.reader(io.StringIO(texto.lstrip("﻿"), newline=""), delimiter=sep))


def escribir_filas(ruta, filas, sep=",", codificacion="utf-8"):
    buf = io.StringIO(newline="")
    csv.writer(buf, delimiter=sep, lineterminator="\r\n").writerows(filas)
    ruta.write_bytes(buf.getvalue().encode(codificacion))


# ---------------------------------------------------------------------------
def pruebas_perfil(ex, no):
    var = SALIDA / "variantes"
    var.mkdir(parents=True, exist_ok=True)
    if ex:
        c, p = correr_json("perfilar_datos.py", ex)
        cols = {x["nombre"]: x for x in p.get("columnas_detalle", [])}
        lec = p.get("lectura", {})
        ok = (c == 1 and lec.get("separador") == "\t" and lec.get("bom") is True
              and lec.get("finales_de_linea") == ["CR (Mac antiguo)"]
              and cols.get("COMP_ACT_SCORE", {}).get("faltantes") == 269
              and cols.get("Gender", {}).get("tipo") == "binaria 0/1"
              and cols.get("SUBJECT", {}).get("tipo") == "constante")
        registrar("perfil exámenes (real)", "código 1; tab, BOM, CR; ACT 269 faltantes; Gender 0/1; SUBJECT constante",
                  f"código {c}; sep {lec.get('separador')!r}, BOM {lec.get('bom')}, {lec.get('finales_de_linea')}; "
                  f"ACT {cols.get('COMP_ACT_SCORE', {}).get('faltantes')}; Gender {cols.get('Gender', {}).get('tipo')}",
                  ok)
        filas = leer_filas(ex, "\t", "utf-8")
        # Variante punto y coma + coma decimal.
        sucia = [filas[0]] + [[x.replace(".", ",") if x.replace(".", "", 1).replace("-", "", 1).isdigit() else x
                               for x in f] for f in filas[1:]]
        ruta = var / "examenes_pyc_coma.csv"
        escribir_filas(ruta, sucia, ";")
        c, p = correr_json("perfilar_datos.py", ruta)
        cols = {x["nombre"]: x for x in p.get("columnas_detalle", [])}
        tipo = cols.get("Exams_percent", {}).get("tipo")
        ok = p.get("lectura", {}).get("separador") == ";" and p.get("lectura", {}).get("decimal") == "," \
            and tipo == "numérica decimal"
        registrar("perfil punto y coma + decimal coma", "sep ';', decimal ',', Exams_percent numérica decimal",
                  f"sep {p.get('lectura', {}).get('separador')!r}, decimal {p.get('lectura', {}).get('decimal')!r}, {tipo}", ok)
        # Variante columna mixta.
        i_age = filas[0].index("AGE")
        mixta = [list(f) for f in filas]
        for k, v in ((5, "veinte"), (9, "n/d"), (20, "20 años")):
            mixta[k][i_age] = v
        ruta = var / "examenes_mixta.csv"
        escribir_filas(ruta, mixta, "\t")
        c, p = correr_json("perfilar_datos.py", ruta)
        cols = {x["nombre"]: x for x in p.get("columnas_detalle", [])}
        age = cols.get("AGE", {})
        texto = " ".join(age.get("problemas", []))
        ok = age.get("tipo") == "mixta" and "veinte" in texto and "fila 6" in texto
        registrar("perfil columna mixta (AGE)", "tipo mixta, cita 'veinte' en fila 6",
                  f"tipo {age.get('tipo')}; {texto[:90]}", ok)
    if no:
        c, p = correr_json("perfilar_datos.py", no)
        cols = {x["nombre"]: x for x in p.get("columnas_detalle", [])}
        marca = cols.get("Marca temporal", {})
        q5 = [x for n, x in cols.items() if n.startswith("5.")]
        ok = (c == 1 and marca.get("tipo") == "fecha" and p.get("filas") == 640
              and q5 and any("espacios" in x for x in q5[0]["problemas"]))
        registrar("perfil noticias (real)", "código 1; 640 filas; Marca temporal fecha; espacios sobrantes en p. 5",
                  f"código {c}; {p.get('filas')} filas; {marca.get('tipo')}; "
                  f"{q5[0]['problemas'] if q5 else '—'}", ok)
        filas = leer_filas(no, ",", "utf-8")
        # latin-1
        ruta = var / "noticias_latin1.csv"
        texto = io.StringIO(newline="")
        csv.writer(texto, lineterminator="\n").writerows(filas)
        ruta.write_bytes(texto.getvalue().encode("cp1252", errors="strict"))
        c, p = correr_json("perfilar_datos.py", ruta)
        nombres = [x["nombre"] for x in p.get("columnas_detalle", [])]
        cod = p.get("lectura", {}).get("codificacion")
        ok = cod in ("latin-1", "cp1252") and "Género" in nombres and any(
            "codificación" in o for o in p.get("observaciones", []))
        registrar("perfil codificación latin-1/cp1252", "detecta cp1252 o latin-1 y lee 'Género'",
                  f"{cod}; 'Género' {'leído' if 'Género' in nombres else 'NO leído'}", ok)
        # Categorías con variantes de mayúsculas, tildes y espacios.
        i_gen, i_fac = filas[0].index("Género"), filas[0].index("Facultad")
        cat = [list(f) for f in filas]
        cat[2][i_gen], cat[3][i_gen], cat[4][i_gen] = "femenino", "Femenino ", "MASCULINO"
        for k in (5, 6):
            if cat[k][i_fac] == "Ciencias Económicas y Empresariales":
                cat[k][i_fac] = "Ciencias Economicas y Empresariales"
        cat[7][i_fac] = "Ciencias Economicas y Empresariales"
        ruta = var / "noticias_categorias.csv"
        escribir_filas(ruta, cat)
        c, p = correr_json("perfilar_datos.py", ruta)
        cols = {x["nombre"]: x for x in p.get("columnas_detalle", [])}
        vg = cols.get("Género", {}).get("variantes", [])
        vf = cols.get("Facultad", {}).get("variantes", [])
        ok = (any("femenino" in g and "Femenino" in g for g in vg) and any("MASCULINO" in g for g in vg)
              and any("Ciencias Economicas y Empresariales" in g for g in vf)
              and any("espacios" in x for x in cols.get("Género", {}).get("problemas", [])))
        registrar("perfil categorías variantes", "Género femenino/Femenino, MASCULINO; Facultad sin tilde; espacios",
                  f"Género {vg}; Facultad {[list(g) for g in vf]}"[:160], ok)
        # Fechas mal formadas y formatos mezclados.
        i_m = filas[0].index("Marca temporal")
        fec = [list(f) for f in filas]
        fec[3][i_m], fec[8][i_m], fec[12][i_m] = "2024-13-45 10:00:00", "31/02/2024", "15/01/2024 09:30"
        ruta = var / "noticias_fechas.csv"
        escribir_filas(ruta, fec)
        c, p = correr_json("perfilar_datos.py", ruta)
        marca = {x["nombre"]: x for x in p.get("columnas_detalle", [])}.get("Marca temporal", {})
        texto = " ".join(marca.get("problemas", []))
        ok = "2 fechas mal formadas" in texto and "2024-13-45" in texto and "31/02/2024" in texto and "mezclados" in texto
        registrar("perfil fechas mal formadas", "2 mal formadas (2024-13-45, 31/02/2024) y formatos mezclados",
                  texto[:160], ok)
        # xlsx con dos hojas.
        from openpyxl import Workbook
        wb = Workbook()
        wb.active.title = "Portada"
        wb.active["A1"] = "Encuesta"
        ws = wb.create_sheet("Respuestas")
        for f in filas:
            ws.append(f)
        ruta = var / "noticias.xlsx"
        wb.save(ruta)
        c, p = correr_json("perfilar_datos.py", ruta, "--hoja", "Respuestas")
        c2, _ = correr_json("perfilar_datos.py", ruta, "--hoja", "NoExiste")
        ok = p.get("filas") == 640 and p.get("lectura", {}).get("hojas") == ["Portada", "Respuestas"] and c2 == 2
        registrar("perfil xlsx --hoja", "640 filas en 'Respuestas'; hoja inexistente → código 2",
                  f"{p.get('filas')} filas; hojas {p.get('lectura', {}).get('hojas')}; inexistente → {c2}", ok)
    c, _ = correr_json("perfilar_datos.py", SALIDA / "no_existe.csv")
    registrar("perfil archivo inexistente", "código 2", f"código {c}", c == 2)


# ---------------------------------------------------------------------------
def pruebas_analisis(ex, no):
    import pandas as pd
    trabajos = {}
    if ex:
        base = preparar_trabajo("examenes", "plan_examenes.json", ex)
        trabajos["examenes"] = base
        c, j = correr_json("analizar.py", base / "plan_analisis.json")
        res_path = base / "resultados" / "resultados.json"
        registrar("analizar exámenes", "código 0 (1 si falta scipy)", f"código {c}; avisos {j.get('avisos')}",
                  c in (0, 1) and res_path.exists())
        r = json.loads(res_path.read_text(encoding="utf-8"))
        cif = {x["clave"]: x["valor"] for x in r["cifras"]}
        # Cálculo independiente con pandas directamente.
        d = pd.read_csv(ex, sep="\t", encoding="utf-8-sig", na_values=[" "], keep_default_na=False)
        exam = pd.to_numeric(d["Exams_percent"])
        act = pd.to_numeric(d["COMP_ACT_SCORE"])
        nonex = pd.to_numeric(d["NonExam_percent"])
        chequeos = [
            ("mujeres (Gender = 0); artículo Tabla 2: 868", "t3|n|Mujer|Total", int((d["Gender"] == 0).sum())),
            ("% Sophomore", "t1|Sophomore|porcentaje_validos", 100 * (d["YearSchool"] == "Sophomore").mean()),
            ("mujeres con WTH", "t3|n|Mujer|WTH", int(((d["Gender"] == 0) & (d["GRADING_BASIS_ENRL"] == "WTH")).sum())),
            ("% por fila hombres A-F", "t3|pct_fila|Hombre|A-F",
             100 * ((d["Gender"] == 1) & (d["GRADING_BASIS_ENRL"] == "A-F")).sum() / (d["Gender"] == 1).sum()),
            ("% URM sobre válidos", "t2|URM|porcentaje_validos", 100 * (pd.to_numeric(d["URM"]) == 1).sum() /
             pd.to_numeric(d["URM"]).notna().sum()),
            ("media Exams_percent", "t4|Exams_percent|Total|media", exam.mean()),
            ("DE ACT (n − 1)", "t4|COMP_ACT_SCORE|Total|de", act.std(ddof=1)),
            ("n ACT", "t4|COMP_ACT_SCORE|Total|n", int(act.notna().sum())),
            ("Q1 AGE", "t4|AGE|Total|q1", d["AGE"].quantile(0.25)),
            ("mediana Exams_percent hombres", "t5|Exams_percent|Hombre|mediana", exam[d["Gender"] == 1].median()),
            ("máx. NonExam_percent mujeres", "t5|NonExam_percent|Mujer|maximo", nonex[d["Gender"] == 0].max()),
        ]
        a, b = exam[d["Gender"] == 0].dropna(), exam[d["Gender"] == 1].dropna()
        t_welch = (a.mean() - b.mean()) / math.sqrt(a.var() / len(a) + b.var() / len(b))
        chequeos.append(("t de Welch (fórmula a mano)", "t5|Exams_percent|t|estadistico", t_welch))
        tabla = pd.crosstab(d["Gender"], d["GRADING_BASIS_ENRL"])
        esperadas = tabla.sum(axis=1).values[:, None] * tabla.sum(axis=0).values[None, :] / tabla.values.sum()
        chi = float(((tabla.values - esperadas) ** 2 / esperadas).sum())
        chequeos.append(("chi cuadrado (fórmula a mano)", "t3|chi2|estadistico", chi))
        for nombre, clave, valor in chequeos:
            obtenido = cif.get(clave)
            if obtenido is None and clave.startswith(("t5|Exams_percent|t", "t3|chi2")):
                registrar(f"a mano: {nombre}", repr(valor), "omitido (sin scipy)", None)
                continue
            registrar(f"a mano: {nombre}", repr(float(valor)), repr(obtenido), cerca(obtenido, float(valor)))
        # Determinismo.
        c2, _ = correr_json("analizar.py", base / "plan_analisis.json", "--salida", base / "resultados_2")
        r2 = json.loads((base / "resultados_2" / "resultados.json").read_text(encoding="utf-8"))
        for x in (r, r2):
            x["metadatos"].pop("generado")
        registrar("dos corridas → mismo resultados.json (salvo fecha)", "idéntico",
                  "idéntico" if r == r2 else "distinto", r == r2)
        sha = hashlib.sha256(ex.read_bytes()).hexdigest()
        registrar("sha256 de datos en metadatos", sha[:16], r["metadatos"]["datos"]["sha256"][:16],
                  r["metadatos"]["datos"]["sha256"] == sha)
        anchos = {}
        for png in sorted((base / "resultados" / "figuras").glob("*.png")):
            with open(png, "rb") as f:
                cab = f.read(24)
            anchos[png.name] = struct.unpack(">I", cab[16:20])[0]
        ok = set(anchos) == {"t1.png", "t3.png", "t5.png"} and all(1250 <= w <= 1270 for w in anchos.values())
        registrar("figuras PNG (16 cm a 200 ppp ≈ 1260 px)", "t1, t3, t5 de ~1260 px", anchos, ok)
        # Sin scipy.
        c, j = correr_json("analizar.py", base / "plan_analisis.json", "--salida", base / "resultados_sin_scipy",
                           entorno={"ANALISIS_SIN_SCIPY": "1"})
        avisos = " ".join(j.get("avisos", []))
        r3 = json.loads((base / "resultados_sin_scipy" / "resultados.json").read_text(encoding="utf-8"))
        sin_p = not any("chi2" in x["clave"] or "|t|" in x["clave"] for x in r3["cifras"])
        registrar("sin scipy: pruebas omitidas y avisadas", "código 1; aviso 'omitida'; sin cifras de prueba",
                  f"código {c}; {avisos[:80]}", c == 1 and "omitida" in avisos and sin_p)
        # Plan con columna inexistente.
        malo = json.loads((base / "plan_analisis.json").read_text(encoding="utf-8"))
        malo["tablas"][0]["variable"] = "YearSchol"
        (base / "plan_malo.json").write_text(json.dumps(malo, ensure_ascii=False), encoding="utf-8")
        c, j = correr_json("analizar.py", base / "plan_malo.json", "--salida", base / "resultados_malo")
        registrar("plan con columna inexistente", "código 2 y sugiere YearSchool", f"código {c}; {j.get('error', '')[:80]}",
                  c == 2 and "YearSchool" in j.get("error", ""))
        # Valor no numérico sin declarar.
        mixta = SALIDA / "variantes" / "examenes_mixta.csv"
        if mixta.exists():
            shutil.copyfile(mixta, base / "datos" / "mixta.csv")
            p = json.loads((base / "plan_analisis.json").read_text(encoding="utf-8"))
            p["datos"]["archivo"] = "datos/mixta.csv"
            (base / "plan_mixta.json").write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")
            c, j = correr_json("analizar.py", base / "plan_mixta.json", "--salida", base / "resultados_mixta")
            registrar("valor no numérico sin declarar (AGE 'veinte')", "código 2, no se descarta en silencio",
                      f"código {c}; {j.get('error', '')[:80]}", c == 2 and "no numéricos" in j.get("error", ""))
            p["datos"]["faltantes"] = ["veinte", "n/d", "20 años"]
            (base / "plan_mixta.json").write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")
            c, j = correr_json("analizar.py", base / "plan_mixta.json", "--salida", base / "resultados_mixta")
            rm = json.loads((base / "resultados_mixta" / "resultados.json").read_text(encoding="utf-8"))
            n_age = {x["clave"]: x["valor"] for x in rm["cifras"]}.get("t4|AGE|Total|n")
            registrar("mismos valores declarados como faltantes", "corre; n de AGE = 1558",
                      f"código {c}; n AGE {n_age}", c in (0, 1) and n_age == 1558)
    if no:
        base = preparar_trabajo("noticias", "plan_noticias.json", no)
        trabajos["noticias"] = base
        c, j = correr_json("analizar.py", base / "plan_analisis.json")
        r = json.loads((base / "resultados" / "resultados.json").read_text(encoding="utf-8"))
        cif = {x["clave"]: x["valor"] for x in r["cifras"]}
        d = pd.read_csv(no)
        d = d[d["Género"].isin(["Femenino", "Masculino"])]
        semana = pd.to_datetime(d["Marca temporal"]).dt.to_period("W-SUN").dt.start_time
        n_sem = int((semana == pd.Timestamp("2024-01-29")).sum())
        p7 = d.columns[11]
        pct = 100 * ((d["Género"] == "Masculino") & (d[p7] == "Casi siempre")).sum() / (d["Género"] == "Masculino").sum()
        registrar("analizar noticias", "código 0; 635 filas tras filtro", f"código {c}; {j.get('filas_usadas')} filas",
                  c in (0, 1) and j.get("filas_usadas") == 635)
        registrar("a mano: respuestas semana 2024-01-29", n_sem, cif.get("n3|2024-01-29|n"), cif.get("n3|2024-01-29|n") == n_sem)
        registrar("a mano: % hombres 'Casi siempre' (p. 7)", repr(pct), repr(cif.get("n2|pct_fila|Masculino|Casi siempre")),
                  cerca(cif.get("n2|pct_fila|Masculino|Casi siempre"), pct))
        registrar("a mano: Facultad Derecho n", int((d["Facultad"] == "Derecho y Gobernabilidad").sum()),
                  cif.get("n1|Derecho y Gobernabilidad|n"),
                  cif.get("n1|Derecho y Gobernabilidad|n") == int((d["Facultad"] == "Derecho y Gobernabilidad").sum()))
    return trabajos


# ---------------------------------------------------------------------------
def pruebas_xlsx(trabajos):
    from openpyxl import load_workbook
    sys.path.insert(0, str(SCRIPTS))
    import datos_comun as dc
    for nombre, base in trabajos.items():
        res = base / "resultados" / "resultados.json"
        r = json.loads(res.read_text(encoding="utf-8"))
        n_tablas = len(r["tablas"])
        valores = base / "resultados" / "tablas_valores.xlsx"
        c, j = correr_json("exportar_xlsx.py", res, "--salida", valores, "--comprobar")
        comp = j.get("comprobacion", {})
        wb = load_workbook(valores)
        hojas = wb.sheetnames
        primera = wb[hojas[2]]
        fijas = all(wb[h].freeze_panes == "A2" for h in hojas[1:])
        fmt = primera["C2"].number_format if r["tablas"][0]["tipo"] == "frecuencias" else "0.0%"
        negrita = primera["A1"].font.bold
        ok = (c == 0 and hojas[:2] == ["Leeme", "Datos"] and len(hojas) == 2 + n_tablas and fijas
              and fmt == "0.0%" and negrita and comp.get("ok"))
        registrar(f"xlsx valores {nombre}", f"Leeme, Datos + {n_tablas} tablas; fila 1 fija; 0,0 %; 0 errores; cifras iguales",
                  f"código {c}; {len(hojas)} hojas; fija {fijas}; formato {fmt}; comprobadas {comp.get('comprobadas')}, "
                  f"dif {len(comp.get('diferencias', []))}, errores {len(comp.get('celdas_con_error', []))}", ok)
        formulas = base / "resultados" / "tablas_formulas.xlsx"
        c, j = correr_json("exportar_xlsx.py", res, "--salida", formulas, "--formulas", "--comprobar")
        comp = j.get("comprobacion", {})
        if comp.get("error"):
            registrar(f"xlsx fórmulas {nombre} (LibreOffice)", "recalculado", f"omitido: {comp['error']}", None)
            continue
        wb = load_workbook(formulas)
        n_formulas = sum(1 for ws in wb.worksheets for fila in ws.iter_rows() for x in fila
                         if (isinstance(x.value, str) and x.value.startswith("=")) or type(x.value).__name__ == "ArrayFormula")
        registrar(f"xlsx fórmulas {nombre}: recálculo LibreOffice = resultados.json",
                  "0 diferencias, 0 celdas de error",
                  f"código {c}; {n_formulas} fórmulas; comprobadas {comp.get('comprobadas')}, "
                  f"dif {len(comp.get('diferencias', []))}, errores {len(comp.get('celdas_con_error', []))}",
                  c == 0 and comp.get("ok") and n_formulas > 20)
        # Comprobación independiente: recalcular a mano y leer por estructura.
        soffice = dc.ruta_soffice()
        if soffice:
            with tempfile.TemporaryDirectory() as tmp:
                perfil = (Path(tmp) / "perfil").as_uri()
                subprocess.run([soffice, f"-env:UserInstallation={perfil}", "--headless", "--convert-to", "xlsx",
                                "--outdir", tmp, str(formulas)], capture_output=True, timeout=240)
                recalc = load_workbook(Path(tmp) / formulas.name, data_only=True)
            fallos, revisadas = [], 0
            for t, hoja in zip(r["tablas"], recalc.sheetnames[2:]):
                ws = recalc[hoja]
                if t["tipo"] == "frecuencias":
                    for i, f in enumerate(t["filas"], start=2):
                        revisadas += 2
                        if ws.cell(i, 1).value != f["categoria"] or ws.cell(i, 2).value != f["n"]:
                            fallos.append(f"{hoja} fila {i}")
                        if not cerca(ws.cell(i, 3).value, f["porcentaje_validos"] / 100):
                            fallos.append(f"{hoja} % fila {i}")
                elif t["tipo"] == "resumen":
                    c0 = 3 if t["por"] else 2
                    for i, f in enumerate(t["filas"], start=2):
                        for k, est in enumerate(["n", "faltantes", "media", "mediana", "de", "minimo", "q1", "q3", "maximo"]):
                            revisadas += 1
                            v = ws.cell(i, c0 + k).value
                            if not cerca(v, f[est]):
                                fallos.append(f"{hoja} {f['variable']} {f['grupo']} {est}: {v} ≠ {f[est]}")
                elif t["tipo"] == "serie":
                    for i, f in enumerate(t["filas"], start=2):
                        revisadas += 1
                        if ws.cell(i, 4).value != f["n"]:
                            fallos.append(f"{hoja} {f['periodo']}")
            registrar(f"xlsx fórmulas {nombre}: lectura independiente por estructura", "0 fallos",
                      f"{revisadas} celdas; fallos {fallos[:3]}", not fallos and revisadas > 0)
    if "examenes" in trabajos:
        base = trabajos["examenes"]
        c, _ = correr_json("exportar_xlsx.py", base / "resultados" / "resultados.json", "--formulas", "--sin-datos",
                           "--salida", base / "resultados" / "x.xlsx")
        registrar("xlsx --formulas con --sin-datos", "código 2", f"código {c}", c == 2)
        datos = base / "datos" / "PLoSOneData_ExamsDisWomen.csv"
        original = datos.read_bytes()
        try:
            datos.write_bytes(original + b"\r")
            c, j = correr_json("exportar_xlsx.py", base / "resultados" / "resultados.json",
                               "--salida", base / "resultados" / "x.xlsx")
        finally:
            datos.write_bytes(original)
        registrar("xlsx con datos cambiados tras el análisis", "código 2 (rehacer análisis)",
                  f"código {c}; {j.get('error', '')[:60]}", c == 2 and "cambiaron" in j.get("error", ""))


# ---------------------------------------------------------------------------
def pruebas_cifras(trabajos):
    if "examenes" not in trabajos:
        registrar("cifras_texto", "—", "omitido (sin datos de exámenes)", None)
        return
    res = trabajos["examenes"] / "resultados" / "resultados.json"
    texto = CASOS / "cifras_prueba.md"
    c, j = correr_json("cifras_texto.py", texto, res)
    if j.get("resumen", {}).get("DISCREPA") is None:
        registrar("cifras_texto md", "funciona", f"código {c}; {j}", False)
        return
    discrepa = sorted(x["texto"] for x in j["cifras"] if x["estado"] == "DISCREPA")
    registrar("cifras_texto: exactamente las 2 sembradas", "['1302', '14,9 %'] y código 1",
              f"{discrepa}; código {c}", discrepa == ["1302", "14,9 %"] and c == 1)
    cita = [x for x in j["cifras"] if x["texto"] == "1205"]
    registrar("cifras_texto: cifra con cita fuera del análisis", "1205 NO HALLADA con cita",
              f"{cita[0]['estado']} con_cita={cita[0]['con_cita']}" if cita else "no extraída",
              bool(cita) and cita[0]["estado"] == "NO HALLADA" and cita[0]["con_cita"])
    textos = [x["texto"] for x in j["cifras"]]
    prohibidas = {"2016", "2018", "2026", "14", "19", "3.2", "3,2", "2.1", "2.2", "1", "1.", "10"}
    vistas = sorted(prohibidas.intersection(textos))
    registrar("cifras_texto: ignora años, fechas, numeraciones, COVID-19", "ninguna de 2016, 2026, 14 (fecha), 3.2, 19…",
              f"ignoradas: {'todas' if not vistas else vistas}; extraídas {len(textos)}", not vistas)
    no_sin_cita = [x["texto"] for x in j["cifras"] if x["estado"] == "NO HALLADA" and not x["con_cita"]]
    registrar("cifras_texto: sin NO HALLADA sin cita", "ninguna", no_sin_cita or "ninguna", not no_sin_cita)
    corregido = SALIDA / "cifras_corregido.md"
    corregido.write_text(texto.read_text(encoding="utf-8").replace("14,9 %", "14,5 %").replace("n = 1302", "n = 1292"),
                         encoding="utf-8")
    c, j2 = correr_json("cifras_texto.py", corregido, res)
    registrar("cifras_texto: texto corregido", "0 DISCREPA, código 0",
              f"{j2.get('resumen', {}).get('DISCREPA')} DISCREPA, código {c}", c == 0)
    try:
        import docx
        doc = docx.Document()
        for bloque in texto.read_text(encoding="utf-8").split("\n\n"):
            bloque = " ".join(bloque.split("\n"))
            if bloque.startswith("#"):
                doc.add_heading(bloque.lstrip("# "), level=bloque.count("#", 0, 4))
            elif bloque[:2] in ("1.",):
                for item in bloque.split(" 2. "):
                    doc.add_paragraph(item if item.startswith("1.") else "2. " + item)
            else:
                doc.add_paragraph(bloque)
        ruta = SALIDA / "cifras_prueba.docx"
        doc.save(ruta)
        c, j3 = correr_json("cifras_texto.py", ruta, res)
        d3 = sorted(x["texto"] for x in j3["cifras"] if x["estado"] == "DISCREPA")
        registrar("cifras_texto docx", "['1302', '14,9 %'] y código 1", f"{d3}; código {c}",
                  d3 == ["1302", "14,9 %"] and c == 1)
    except ImportError:
        registrar("cifras_texto docx", "—", "omitido (sin python-docx)", None)
    c, _ = correr_json("cifras_texto.py", SALIDA / "no_existe.md", res)
    registrar("cifras_texto archivo inexistente", "código 2", f"código {c}", c == 2)


def main():
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    SALIDA.mkdir(parents=True)
    disponibles = conseguir_datos()
    ex = disponibles.get("PLoSOneData_ExamsDisWomen.csv")
    no = disponibles.get("Respuestas_Encuesta.csv")
    pruebas_perfil(ex, no)
    trabajos = pruebas_analisis(ex, no)
    pruebas_xlsx(trabajos)
    pruebas_cifras(trabajos)
    ancho = max(len(r[0]) for r in resultados)
    print(f"{'caso':<{ancho}} | estado | esperado | obtenido")
    for caso, esperado, obtenido, estado in resultados:
        print(f"{caso:<{ancho}} | {estado:<6} | {esperado} | {obtenido}")
    fallas = sum(1 for r in resultados if r[3] == "FALLA")
    omitidos = sum(1 for r in resultados if r[3] == "OMITIDO")
    print(f"\n{len(resultados)} casos: {len(resultados) - fallas - omitidos} ok, {fallas} fallas, {omitidos} omitidos")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
