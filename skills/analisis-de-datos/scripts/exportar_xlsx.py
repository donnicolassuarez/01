# -*- coding: utf-8 -*-
"""Libro xlsx con formato cuidado a partir de resultados.json y los datos.

Uso: python exportar_xlsx.py <analisis/resultados/resultados.json>
     [--salida archivo.xlsx] [--formulas] [--sin-datos] [--comprobar] [--json]

Hojas:
  Leeme   origen de los datos (archivo, sha256, fuente), filas, filtros,
          faltantes, recodificaciones, fecha y cómo rehacer todo.
  Datos   las filas usadas en el análisis (tras filtros y
          recodificaciones), con números como números y fechas como
          fechas. Con --sin-datos no se incluye y Leeme remite al
          archivo de origen (incompatible con --formulas).
  una hoja por tabla del plan: encabezados claros, primera fila fija,
          anchos ajustados y formato numérico según el redondeo del plan
          (el valor de la celda conserva la precisión completa; los
          porcentajes se guardan como fracción con formato 0,0 %).

Por defecto las celdas llevan valores fijos. Con --formulas llevan
fórmulas vivas sobre la hoja Datos (SUMPRODUCT+EXACT para contar
categorías distinguiendo mayúsculas, COUNTBLANK, AVERAGE, MEDIAN,
STDEV, QUARTILE, COUNTIFS por fechas; por grupos, fórmulas matriciales
con IF), para cuando el usuario vaya a editar los datos. Openpyxl exige
los nombres de función en inglés; Excel y LibreOffice los muestran en
el idioma del usuario. Las pruebas estadísticas van siempre como
valores fijos (no tienen fórmula de hoja de cálculo equivalente).
Toda división está protegida: no quedan celdas de error.

Antes de escribir comprueba que el sha256 del plan y de los datos sean
los de resultados.json: si cambiaron, hay que volver a correr
analizar.py.

--comprobar: recalcula el libro con LibreOffice (si está) y verifica
que ninguna celda tenga error y que cada cifra coincida con
resultados.json. En modo valores fijos basta abrirlo con openpyxl.

Códigos de salida: 0 libro escrito (y comprobado si se pidió); 1 libro
escrito pero la comprobación falló o no pudo hacerse; 2 no se pudo
escribir (resultados o datos cambiados, faltan archivos).
"""
import argparse
import datetime as dt
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comun as dc  # noqa: E402
import analizar as an  # noqa: E402

LIMITE_FILAS_EXCEL = 1_048_575
RELLENO = "D9D9D9"


class Libro:
    def __init__(self, resultados, plan, df, decimal, formulas):
        from openpyxl import Workbook
        self.r, self.plan, self.df, self.decimal, self.formulas = resultados, plan, df, decimal, formulas
        self.wb = Workbook()
        self.mapa = []  # (hoja, celda, clave, factor)
        self.cifras = {c["clave"]: c["valor"] for c in resultados["cifras"]}
        self.columnas = {}  # nombre de columna de datos -> letra en Datos
        self.n_datos = len(df)
        self.anchos = {}

    # -- utilidades de estilo
    def encabezado(self, ws, fila, valores, col0=1):
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        for j, v in enumerate(valores):
            c = ws.cell(row=fila, column=col0 + j, value=v)
            c.font = Font(bold=True)
            c.fill = PatternFill("solid", fgColor=RELLENO)
            c.border = Border(bottom=Side(style="thin"))
            c.alignment = Alignment(wrap_text=True, vertical="center",
                                    horizontal="left" if j == 0 else "center")
            self.ancho(ws, col0 + j, v, encabezado=True)

    def ancho(self, ws, columna, valor, encabezado=False):
        texto = "" if valor is None else str(valor)
        largo = len(texto) if not texto.startswith("=") else 12
        if encabezado:
            largo = min(largo, 30)
        clave = (ws.title, columna)
        self.anchos[clave] = max(self.anchos.get(clave, 8), min(largo + 2, 60))

    def aplicar_anchos(self):
        from openpyxl.utils import get_column_letter
        for (hoja, col), ancho in self.anchos.items():
            self.wb[hoja].column_dimensions[get_column_letter(col)].width = ancho

    def poner(self, ws, fila, col, valor, formato=None, clave=None, factor=1.0, matricial=False):
        from openpyxl.worksheet.formula import ArrayFormula
        from openpyxl.utils import get_column_letter
        if isinstance(valor, float) and (math.isnan(valor) or math.isinf(valor)):
            valor = None
        ref = f"{get_column_letter(col)}{fila}"
        if matricial and isinstance(valor, str) and valor.startswith("="):
            ws[ref] = ArrayFormula(ref, valor)
        else:
            ws[ref] = valor
        if formato:
            ws[ref].number_format = formato
        if clave:
            self.mapa.append((ws.title, ref, clave, factor))
        self.ancho(ws, col, valor if not isinstance(valor, float) else round(valor, 4))
        return ref

    def formato_decimales(self, t, tipo, porcentaje=False):
        d = an.decimales_de(self.plan, t, tipo)
        base = "0" + ("." + "0" * d if d else "")
        return base + "%" if porcentaje else base

    def nombre_hoja(self, t):
        nombre = f"{t['id']} {t.get('titulo') or t['tipo']}"
        nombre = re.sub(r"[\[\]:*?/\\]", "", nombre).strip()[:31]
        base, i = nombre, 2
        while nombre in self.wb.sheetnames:
            nombre = f"{base[:28]} {i}"
            i += 1
        return nombre

    def rango(self, columna):
        letra = self.columnas[columna]
        return f"Datos!${letra}$2:${letra}${self.n_datos + 1}"

    # -- hojas
    def hoja_datos(self):
        from openpyxl.utils import get_column_letter
        ws = self.wb.create_sheet("Datos")
        df = self.df
        categoricas, numericas, fechas = set(), set(), {}
        for t in self.plan["tablas"]:
            if t["tipo"] == "frecuencias":
                categoricas.add(t["variable"])
            elif t["tipo"] == "cruzada":
                categoricas.update([t["filas"], t["columnas"]])
            elif t["tipo"] == "resumen":
                numericas.update(t.get("variables") or [t.get("variable")])
                if t.get("por"):
                    categoricas.add(t["por"])
            elif t["tipo"] == "serie":
                fechas[t["fecha"]] = t.get("formato_fecha")
                if t.get("variable"):
                    numericas.add(t["variable"])
        self.encabezado(ws, 1, list(df.columns))
        for j, columna in enumerate(df.columns, start=1):
            self.columnas[columna] = get_column_letter(j)
            if columna in fechas:
                valores, _ = an.serie_fechas(df, columna, fechas[columna], "Datos")
                valores = [v if v is not None else (None if df[columna].iloc[i] is None else df[columna].iloc[i])
                           for i, v in enumerate(valores)]
                formato = "yyyy-mm-dd hh:mm:ss"
            elif columna in numericas:
                valores = an.serie_numerica(df, columna, self.decimal, "Datos").tolist()
                valores = [None if (isinstance(v, float) and math.isnan(v)) else v for v in valores]
                formato = None
            elif columna in categoricas:
                valores, formato = df[columna].tolist(), "@"
            else:
                crudos = df[columna].tolist()
                nums = [dc.a_numero(v, self.decimal) if v is not None else None for v in crudos]
                todos = all(n is not None for v, n in zip(crudos, nums) if v is not None)
                valores, formato = (nums, None) if todos and any(v is not None for v in crudos) else (crudos, None)
            for i, v in enumerate(valores, start=2):
                c = ws.cell(row=i, column=j, value=v)
                if formato and v is not None:
                    c.number_format = formato
            muestra = [str(v) for v in valores[:200] if v is not None]
            ancho = max([len(s) for s in muestra] + [8])
            self.anchos[("Datos", j)] = min(max(self.anchos.get(("Datos", j), 8), ancho + 2), 40)
        ws.freeze_panes = "A2"

    def hoja_frecuencias(self, t, ws):
        var = t["variable"]
        hay_falt = t["n_faltantes"] > 0
        cab = [var, "n", "% válidos"] + (["% del total"] if hay_falt else [])
        self.encabezado(ws, 1, cab)
        k = len(t["filas"])
        f_val = k + 2
        f_falt, f_tot = (k + 3, k + 4) if hay_falt else (None, f_val)
        fp = self.formato_decimales(t, "porcentaje", True)
        R = self.rango(var) if self.formulas else None
        for i, fila in enumerate(t["filas"], start=2):
            self.poner(ws, i, 1, fila["categoria"])
            n = f"=SUMPRODUCT(EXACT({R},$A{i})*1)" if R else fila["n"]
            self.poner(ws, i, 2, n, "0", f"{t['id']}|{fila['categoria']}|n")
            pv = f'=IF($B${f_val}=0,"",B{i}/$B${f_val})' if R else _frac(fila["porcentaje_validos"])
            self.poner(ws, i, 3, pv, fp, f"{t['id']}|{fila['categoria']}|porcentaje_validos", 0.01)
            if hay_falt:
                pt = f'=IF($B${f_tot}=0,"",B{i}/$B${f_tot})' if R else _frac(fila["porcentaje_total"])
                self.poner(ws, i, 4, pt, fp, f"{t['id']}|{fila['categoria']}|porcentaje_total", 0.01)
        self.poner(ws, f_val, 1, "Total válidos")
        self.poner(ws, f_val, 2, f"=SUM(B2:B{k + 1})" if R else t["n_validos"], "0", f"{t['id']}|n_validos")
        self.poner(ws, f_val, 3, f'=IF($B${f_val}=0,"",SUM(C2:C{k + 1}))' if R else 1.0, fp)
        if hay_falt:
            self.poner(ws, f_falt, 1, "Sin dato")
            self.poner(ws, f_falt, 2, f"=COUNTBLANK({R})" if R else t["n_faltantes"], "0", f"{t['id']}|faltantes|n")
            self.poner(ws, f_falt, 4, f'=IF($B${f_tot}=0,"",B{f_falt}/$B${f_tot})' if R else
                       _frac(100 * t["n_faltantes"] / t["n_total"]), fp, f"{t['id']}|faltantes|porcentaje_total", 0.01)
            self.poner(ws, f_tot, 1, "Total")
            self.poner(ws, f_tot, 2, f"=B{f_val}+B{f_falt}" if R else t["n_total"], "0", f"{t['id']}|n_total")
            self.poner(ws, f_tot, 4, f'=IF($B${f_tot}=0,"",SUM(D2:D{k + 1})+D{f_falt})' if R else 1.0, fp)
        _negrita_fila(ws, f_tot, len(cab))

    def hoja_cruzada(self, t, ws):
        from openpyxl.utils import get_column_letter as L
        cf, cc = t["categorias_filas"], t["categorias_columnas"]
        RF = self.rango(t["filas"]) if self.formulas else None
        RC = self.rango(t["columnas"]) if self.formulas else None
        nc = len(cc)
        col_tot = nc + 2
        fila_tot = len(cf) + 2
        self.encabezado(ws, 1, [f"{t['filas']} (filas) / {t['columnas']} (columnas)"] + cc + ["Total"])
        for i, f in enumerate(cf, start=2):
            self.poner(ws, i, 1, f)
            for j, c in enumerate(cc, start=2):
                v = f"=SUMPRODUCT(EXACT({RF},$A{i})*EXACT({RC},{L(j)}$1))" if RF else t["conteos"][f][c]
                self.poner(ws, i, j, v, "0", f"{t['id']}|n|{f}|{c}")
            self.poner(ws, i, col_tot, f"=SUM(B{i}:{L(col_tot - 1)}{i})" if RF else t["conteos"][f]["Total"],
                       "0", f"{t['id']}|n|{f}|Total")
        self.poner(ws, fila_tot, 1, "Total")
        for j, c in enumerate(cc + ["Total"], start=2):
            v = f"=SUM({L(j)}2:{L(j)}{fila_tot - 1})" if RF else t["conteos"]["Total"][c]
            self.poner(ws, fila_tot, j, v, "0", f"{t['id']}|n|Total|{c}")
        _negrita_fila(ws, fila_tot, col_tot)
        fp = self.formato_decimales(t, "porcentaje", True)
        fila = fila_tot + 2
        nombres = {"fila": "% por fila", "columna": "% por columna", "total": "% sobre el total"}
        for modo, tabla in t["porcentajes"].items():
            self.encabezado(ws, fila, [nombres[modo]] + cc + ["Total"])
            inicio = fila + 1
            for k, f in enumerate(cf + ["Total"]):
                r = inicio + k
                rn = 2 + k  # fila de la misma categoría en el bloque de conteos
                self.poner(ws, r, 1, f)
                for j, c in enumerate(cc + ["Total"], start=2):
                    if RF:
                        base = {"fila": f"${L(col_tot)}{rn}", "columna": f"{L(j)}${fila_tot}",
                                "total": f"${L(col_tot)}${fila_tot}"}[modo]
                        v = f'=IF({base}=0,"",{L(j)}{rn}/{base})'
                    else:
                        v = _frac(tabla[f][c])
                    self.poner(ws, r, j, v, fp, f"{t['id']}|pct_{modo}|{f}|{c}", 0.01)
            _negrita_fila(ws, inicio + len(cf), col_tot)
            fila = inicio + len(cf) + 2
        if "prueba" in t:
            self.bloque_prueba(ws, fila, t, t["prueba"], f"{t['id']}|chi2")

    def bloque_prueba(self, ws, fila, t, pr, base_clave):
        self.encabezado(ws, fila, ["Prueba (valor fijo, calculado en Python)", "Valor"])
        if "omitida" in pr:
            self.poner(ws, fila + 1, 1, f"Omitida: {pr['omitida']}")
            return fila + 3
        filas = [(pr["prueba"], None, None, None)]
        filas.append(("Estadístico", pr["estadistico"], self.formato_decimales(t, "prueba"), "estadistico"))
        gl = pr.get("gl")
        if isinstance(gl, list):
            for i, g in enumerate(gl, start=1):
                filas.append((f"gl {i}", g, "0", f"gl{i}"))
        elif gl is not None:
            filas.append(("gl", gl, "0" if float(gl).is_integer() else self.formato_decimales(t, "prueba"), "gl"))
        filas.append(("p", pr["p_valor"], self.formato_decimales(t, "p_valor"), "p_valor"))
        if pr.get("v_cramer") is not None:
            filas.append(("V de Cramér", pr["v_cramer"], self.formato_decimales(t, "prueba"), "v_cramer"))
            filas.append(("Frecuencias esperadas < 5", pr["esperadas_menores_5"], "0", None))
        if pr.get("diferencia_medias") is not None:
            filas.append((f"Diferencia de medias ({pr['grupos'][0]} − {pr['grupos'][1]})",
                          pr["diferencia_medias"], self.formato_decimales(t, "estadistico"), "diferencia_medias"))
        for i, (etiqueta, valor, formato, sufijo) in enumerate(filas, start=fila + 1):
            self.poner(ws, i, 1, etiqueta)
            if valor is not None:
                self.poner(ws, i, 2, valor, formato, f"{base_clave}|{sufijo}" if sufijo else None)
        return fila + len(filas) + 2

    def hoja_resumen(self, t, ws):
        por = t["por"]
        pedido = next((x for x in self.plan["tablas"] if x["id"] == t["id"]), {})
        pct = bool(pedido.get("mostrar_por_100"))
        fe = self.formato_decimales(t, "estadistico", pct)
        cab = ["Variable"] + (["Grupo"] if por else []) + [an.NOMBRE_ESTADISTICO[k] for k in an.ESTADISTICOS]
        self.encabezado(ws, 1, cab)
        c0 = 3 if por else 2
        for i, f in enumerate(t["filas"], start=2):
            self.poner(ws, i, 1, f["variable"])
            if por:
                self.poner(ws, i, 2, f["grupo"])
            grupo = f["grupo"] or "Total"
            formulas = self.formulas_resumen(f["variable"], por, i, f["grupo"]) if self.formulas else {}
            for j, k in enumerate(an.ESTADISTICOS):
                v = formulas.get(k, f[k])
                self.poner(ws, i, c0 + j, v, "0" if k in ("n", "faltantes") else fe,
                           f"{t['id']}|{f['variable']}|{grupo}|{k}",
                           matricial=bool(formulas) and k not in ("n", "faltantes") and por and f["grupo"] != "Total")
            if f["grupo"] == "Total" and por:
                _negrita_fila(ws, i, len(cab))
        fila = len(t["filas"]) + 3
        if pct:
            self.poner(ws, fila, 1, "Los estadísticos se muestran con formato de porcentaje (valor × 100).")
            fila += 2
        for var, pr in (t.get("pruebas") or {}).items():
            if var == "omitida":
                self.poner(ws, fila, 1, f"Prueba omitida: {pr}")
                break
            self.poner(ws, fila, 1, var)
            fila = self.bloque_prueba(ws, fila + 1, t, pr, f"{t['id']}|{var}|{pedido.get('prueba')}")

    def formulas_resumen(self, variable, por, fila, grupo):
        R = self.rango(variable)
        if not por or grupo is None:
            return {"n": f"=COUNT({R})", "faltantes": f"=COUNTBLANK({R})",
                    "media": f'=IF(COUNT({R})=0,"",AVERAGE({R}))',
                    "mediana": f'=IF(COUNT({R})=0,"",MEDIAN({R}))',
                    "de": f'=IF(COUNT({R})<2,"",STDEV({R}))',
                    "minimo": f'=IF(COUNT({R})=0,"",MIN({R}))',
                    "q1": f'=IF(COUNT({R})=0,"",QUARTILE({R},1))',
                    "q3": f'=IF(COUNT({R})=0,"",QUARTILE({R},3))',
                    "maximo": f'=IF(COUNT({R})=0,"",MAX({R}))'}
        G = self.rango(por)
        cond = f"(LEN({G})>0)" if grupo == "Total" else f"EXACT({G},$B{fila})"
        sel = f'IF({cond}*ISNUMBER({R}),{R},"")'
        n = f"$C{fila}"
        return {"n": f"=SUMPRODUCT({cond}*ISNUMBER({R}))",
                "faltantes": f'=SUMPRODUCT({cond}*({R}=""))',
                "media": f'=IF({n}=0,"",AVERAGE({sel}))', "mediana": f'=IF({n}=0,"",MEDIAN({sel}))',
                "de": f'=IF({n}<2,"",STDEV({sel}))', "minimo": f'=IF({n}=0,"",MIN({sel}))',
                "q1": f'=IF({n}=0,"",QUARTILE({sel},1))', "q3": f'=IF({n}=0,"",QUARTILE({sel},3))',
                "maximo": f'=IF({n}=0,"",MAX({sel}))'}

    def hoja_serie(self, t, ws):
        con_valor = t["estadistico"] != "conteo"
        etiqueta = {"conteo": None, "media": f"Media de {t['variable']}", "suma": f"Suma de {t['variable']}"}[t["estadistico"]]
        self.encabezado(ws, 1, ["Periodo", "Inicio", "Fin (excluido)", "n"] + ([etiqueta] if con_valor else []))
        D = self.rango(t["fecha"]) if self.formulas else None
        V = self.rango(t["variable"]) if (self.formulas and con_valor) else None
        fe = self.formato_decimales(t, "estadistico")
        for i, f in enumerate(t["filas"], start=2):
            self.poner(ws, i, 1, f["periodo"])
            self.poner(ws, i, 2, dt.datetime.fromisoformat(f["inicio"]), "yyyy-mm-dd hh:mm")
            self.poner(ws, i, 3, dt.datetime.fromisoformat(f["fin"]), "yyyy-mm-dd hh:mm")
            crit = f'{D},">="&B{i},{D},"<"&C{i}' if D else None
            if D:
                n = f'=COUNTIFS({crit},{V},"<>")' if con_valor else f"=COUNTIFS({crit})"
            else:
                n = f["n"]
            self.poner(ws, i, 4, n, "0", f"{t['id']}|{f['periodo']}|n")
            if con_valor:
                funcion = "AVERAGEIFS" if t["estadistico"] == "media" else "SUMIFS"
                v = f'=IF(D{i}=0,"",{funcion}({V},{crit}))' if D else f["valor"]
                self.poner(ws, i, 5, v, fe, f"{t['id']}|{f['periodo']}|{t['estadistico']}")

    def hoja_leeme(self, ruta_resultados, sin_datos):
        from openpyxl.styles import Alignment, Font
        ws = self.wb.active
        ws.title = "Leeme"
        m = self.r["metadatos"]
        filas = [
            ("Título", m["titulo"]),
            ("Fuente de los datos", m.get("fuente") or "(no declarada en el plan)"),
            ("Archivo de datos", m["datos"]["archivo"]),
            ("sha256 del archivo", m["datos"]["sha256"]),
            ("Filas leídas / usadas", f"{m['filas_leidas']} / {m['filas_usadas']}"),
            ("Filtros", "; ".join(f"{f['columna']} {f['op']} {f['valor']}" for f in m["filtros"]) or "ninguno"),
            ("Faltantes", "celda vacía o en blanco" + (
                "; además " + ", ".join(map(repr, m["faltantes_declarados"])) if m["faltantes_declarados"] else "")
             + ". Nada se imputa ni se completa."),
            ("Recodificaciones", "; ".join(f"{c}: " + ", ".join(f"{k} → {v}" for k, v in r["mapa"].items())
                                           for c, r in m["recodificaciones"].items()) or "ninguna"),
            ("Análisis generado", m["generado"]),
            ("Libro exportado", dt.datetime.now().astimezone().isoformat(timespec="seconds")),
            ("Contenido", "fórmulas vivas sobre la hoja Datos: si cambia un dato, las tablas se recalculan; "
                          "las pruebas estadísticas son valores fijos" if self.formulas else
             "valores fijos copiados de resultados.json (no cambian si se editan los datos)"),
            ("Hoja Datos", "no incluida: los datos están en el archivo de origen" if sin_datos else
             "filas usadas en el análisis, ya filtradas y recodificadas"),
            ("Redondeo", "las celdas guardan la precisión completa; el formato muestra "
                         f"{m['redondeo']['porcentaje']} decimal(es) en porcentajes y "
                         f"{m['redondeo']['estadistico']} en estadísticos"),
            ("Cómo rehacer", "1) python perfilar_datos.py <datos>  2) python analizar.py plan_analisis.json  "
                             "3) python exportar_xlsx.py resultados/resultados.json"
                             + (" --formulas" if self.formulas else "")),
            ("Versiones", ", ".join(f"{k} {v}" for k, v in m["versiones"].items() if v)),
        ]
        ws.append(["Leeme", ""])
        ws["A1"].font = Font(bold=True, size=13)
        for etiqueta, valor in filas:
            ws.append([etiqueta, valor])
        ws.append([])
        ws.append(["Hojas", ""])
        ws.cell(row=ws.max_row, column=1).font = Font(bold=True)
        self.indice_fila = ws.max_row + 1
        for fila in ws.iter_rows(min_row=2):
            fila[0].font = Font(bold=True)
            fila[1].alignment = Alignment(wrap_text=True, vertical="top")
        ws.column_dimensions["A"].width = 24
        ws.column_dimensions["B"].width = 95
        ws.freeze_panes = "A2"

    def construir(self, ruta_resultados, sin_datos):
        self.hoja_leeme(ruta_resultados, sin_datos)
        if not sin_datos:
            self.hoja_datos()
        hojas = []
        for t in self.r["tablas"]:
            ws = self.wb.create_sheet(self.nombre_hoja(t))
            getattr(self, f"hoja_{t['tipo']}")(t, ws)
            ws.freeze_panes = "A2"
            hojas.append((ws.title, t.get("titulo") or t["tipo"]))
        leeme = self.wb["Leeme"]
        for nombre, titulo in [("Datos", "datos usados")] * (not sin_datos) + hojas:
            leeme.append([nombre, titulo])
        self.aplicar_anchos()
        if self.formulas:
            from openpyxl.workbook.properties import CalcProperties
            self.wb.calculation = CalcProperties(fullCalcOnLoad=True)


def _frac(pct):
    return None if pct is None else pct / 100.0


def _negrita_fila(ws, fila, columnas):
    from openpyxl.styles import Border, Font, Side
    for j in range(1, columnas + 1):
        c = ws.cell(row=fila, column=j)
        c.font = Font(bold=True)
        c.border = Border(top=Side(style="thin"))


# ---------------------------------------------------------------------------
# Comprobación

def recalcular(ruta_xlsx, carpeta):
    soffice = dc.ruta_soffice()
    if not soffice:
        return None, "LibreOffice no encontrado"
    with tempfile.TemporaryDirectory(prefix="agac_xlsx_") as temporal:
        temporal = Path(temporal)
        entrada = temporal / "libro.xlsx"
        shutil.copyfile(ruta_xlsx, entrada)
        perfil = (temporal / "perfil").resolve().as_uri()
        orden = [soffice, f"-env:UserInstallation={perfil}", "--headless", "--norestore",
                 "--convert-to", "xlsx", "--outdir", str(temporal / "out"), str(entrada)]
        try:
            subprocess.run(orden, capture_output=True, timeout=240)
        except (subprocess.TimeoutExpired, OSError) as error:
            return None, f"LibreOffice falló: {error}"
        salida = temporal / "out" / "libro.xlsx"
        if not salida.exists():
            return None, "LibreOffice no produjo el libro recalculado"
        destino = Path(carpeta) / (Path(ruta_xlsx).stem + "_recalculado.xlsx")
        shutil.copyfile(salida, destino)
        return destino, None


def comprobar(ruta_xlsx, mapa, cifras, formulas):
    """Errores de celda y diferencias con resultados.json."""
    from openpyxl import load_workbook
    informe = {"recalculado_con": None, "celdas_con_error": [], "diferencias": [], "comprobadas": 0}
    ruta = Path(ruta_xlsx)
    if formulas:
        with tempfile.TemporaryDirectory(prefix="agac_comp_") as tmp:
            recalculado, error = recalcular(ruta, tmp)
            if error:
                informe["error"] = error
                return informe
            informe["recalculado_con"] = "LibreOffice"
            return _comparar(load_workbook(recalculado, data_only=True), mapa, cifras, informe)
    return _comparar(load_workbook(ruta, data_only=True), mapa, cifras, informe)


def _comparar(libro, mapa, cifras, informe):
    for ws in libro.worksheets:
        for fila in ws.iter_rows():
            for c in fila:
                if isinstance(c.value, str) and (c.value.startswith("#") and c.value.rstrip("!?").upper().lstrip("#")
                                                 in {"DIV/0", "N/A", "NAME", "NULL", "NUM", "REF", "VALUE", "VALOR", "¿NOMBRE"}
                                                 or c.value.startswith("Err:")):
                    informe["celdas_con_error"].append(f"{ws.title}!{c.coordinate}: {c.value}")
    for hoja, ref, clave, factor in mapa:
        if clave not in cifras:
            continue
        esperado = cifras[clave] * factor
        valor = libro[hoja][ref].value
        informe["comprobadas"] += 1
        if not isinstance(valor, (int, float)) or abs(valor - esperado) > 1e-9 * max(1.0, abs(esperado)):
            informe["diferencias"].append({"celda": f"{hoja}!{ref}", "clave": clave, "esperado": esperado,
                                           "obtenido": valor})
    informe["ok"] = not informe["celdas_con_error"] and not informe["diferencias"] and informe["comprobadas"] > 0
    return informe


# ---------------------------------------------------------------------------

def exportar(ruta_resultados, salida=None, formulas=False, sin_datos=False, plan_ruta=None):
    ruta_resultados = Path(ruta_resultados).resolve()
    if not ruta_resultados.is_file():
        raise dc.ErrorDatos(f"no existe {ruta_resultados}")
    try:
        resultados = json.loads(ruta_resultados.read_text(encoding="utf-8"))
        meta = resultados["metadatos"]
    except (json.JSONDecodeError, KeyError) as error:
        raise dc.ErrorDatos(f"resultados.json ilegible: {error}")
    if formulas and sin_datos:
        raise dc.ErrorDatos("--formulas necesita la hoja Datos: no se puede usar con --sin-datos")
    plan_ruta = Path(plan_ruta).resolve() if plan_ruta else ruta_resultados.parent.parent / meta["plan"]
    if not plan_ruta.is_file():
        raise dc.ErrorDatos(f"no encuentro el plan {plan_ruta}; indíquelo con --plan")
    if dc.sha256_archivo(plan_ruta) != meta["plan_sha256"]:
        raise dc.ErrorDatos("el plan cambió después del análisis: vuelva a correr analizar.py")
    plan = an.cargar_plan(plan_ruta)
    if dc.sha256_archivo(an.ruta_datos(plan, plan_ruta.parent)) != meta["datos"]["sha256"]:
        raise dc.ErrorDatos("los datos cambiaron después del análisis: vuelva a correr analizar.py")
    df, prep, _ = an.preparar_datos(plan, plan_ruta.parent)
    if len(df) > LIMITE_FILAS_EXCEL and not sin_datos:
        raise dc.ErrorDatos(f"{len(df)} filas no caben en una hoja de Excel: use --sin-datos")
    libro = Libro(resultados, plan, df, prep["lectura"].get("decimal") or ".", formulas)
    libro.construir(ruta_resultados, sin_datos)
    salida = Path(salida).resolve() if salida else ruta_resultados.parent / "tablas.xlsx"
    salida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=salida.parent, prefix=".tmp_", suffix=".xlsx", delete=False) as tmp:
        temporal = Path(tmp.name)
    libro.wb.save(temporal)
    temporal.replace(salida)
    return salida, libro, resultados


def main(argv=None):
    dc.salida_utf8()
    parser = argparse.ArgumentParser(description="Exporta resultados.json a un xlsx con formato.")
    parser.add_argument("resultados")
    parser.add_argument("--salida")
    parser.add_argument("--plan", help="ruta del plan si no está junto a la carpeta resultados")
    parser.add_argument("--formulas", action="store_true", help="fórmulas vivas sobre la hoja Datos")
    parser.add_argument("--sin-datos", action="store_true")
    parser.add_argument("--comprobar", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        salida, libro, resultados = exportar(args.resultados, args.salida, args.formulas, args.sin_datos, args.plan)
    except (dc.ErrorDatos, OSError, ValueError) as error:
        if args.json:
            print(json.dumps({"error": str(error)}, ensure_ascii=False))
        else:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    informe = {"salida": str(salida), "modo": "fórmulas" if args.formulas else "valores",
               "hojas": libro.wb.sheetnames, "celdas_mapeadas": len(libro.mapa)}
    codigo = 0
    if args.comprobar:
        comp = comprobar(salida, libro.mapa, {c["clave"]: c["valor"] for c in resultados["cifras"]}, args.formulas)
        informe["comprobacion"] = comp
        codigo = 0 if comp.get("ok") else 1
    if args.json:
        print(json.dumps(informe, ensure_ascii=False, indent=2, default=str))
    else:
        print(f"Libro escrito: {salida} ({informe['modo']})")
        print(f"  hojas: {', '.join(informe['hojas'])}")
        if args.comprobar:
            comp = informe["comprobacion"]
            if comp.get("error"):
                print(f"  COMPROBACIÓN NO HECHA: {comp['error']}")
            else:
                print(f"  comprobación ({comp['recalculado_con'] or 'openpyxl'}): {comp['comprobadas']} cifras, "
                      f"{len(comp['diferencias'])} diferencias, {len(comp['celdas_con_error'])} celdas con error")
                for d in comp["diferencias"][:10]:
                    print(f"    DIFERENCIA {d['celda']} ({d['clave']}): esperado {d['esperado']}, obtenido {d['obtenido']}")
                for e in comp["celdas_con_error"][:10]:
                    print(f"    ERROR {e}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
