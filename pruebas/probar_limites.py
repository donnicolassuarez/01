#!/usr/bin/env python3
"""Pruebas de los límites conocidos de las capas 1 y 2 (corregidos).

Uso: python pruebas/probar_limites.py [--sin-red]

Casos:
  1 cruzar_citas.py: localizadores tras el año ("I, cap. 1", "sec. 2.1",
    "t. 2"...) -> cita reconocida y localizador en la observación.
  2 cruzar_citas.py: apellidos compuestos ("García" frente a "García
    Linera") -> (c) una vez; dos referencias posibles -> ambigua.
  3 cruzar_citas.py: ventana hacia atrás ("IPCC ... Pérez (2021)").
  4 verificar_referencias.py: DOI de arXiv y de Zenodo fuera de Crossref.
    Lógica sin red (respuestas simuladas y página de arXiv guardada) y,
    con red, la prueba real (Ke et al. 2024, Zenodo 19723104 y un arXiv
    inexistente). Con --sin-red los casos de red salen "omitido".
  5 buscar_academico.py: apellidos con partícula y preferencia por los
    autores de Crossref al unir, con respuestas reales guardadas en
    pruebas/casos/limites/registros_autores/.
  6 control_final.py con .xlsx (openpyxl genera los casos) y el hook
    hooks/bloqueo_entrega.py --comprobar sobre ellos.
  7 extraer_texto.py --buscar: el fragmento conserva «±» y ligaduras.
  R regresión: cruzar_citas.py y control_final.py --sin-red sobre los
    casos de referencia (salidas guardadas antes de los cambios en
    pruebas/casos/limites/referencia/).

Requiere openpyxl (caso 6). Imprime una tabla caso -> esperado/obtenido y
sale con 1 si algún caso falla (los omitidos no cuentan como aprobados ni
como fallos).
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPTS = RAIZ / "skills" / "niveles-academicos" / "scripts"
CASOS = RAIZ / "pruebas" / "casos"
SALIDA = RAIZ / "pruebas" / "salida" / "caso_limites"
REGISTROS = CASOS / "limites" / "registros_autores"
REFERENCIA = CASOS / "limites" / "referencia"
HOOK = RAIZ / "hooks" / "bloqueo_entrega.py"
sys.path.insert(0, str(SCRIPTS))

RESULTADOS = []  # (caso, esperado, obtenido, estado: ok | FALLA | omitido)


def anotar(caso, esperado, obtenido, ok, omitido=False):
    estado = "omitido" if omitido else ("ok" if ok else "FALLA")
    RESULTADOS.append((caso, str(esperado), str(obtenido), estado))


def correr(script, *args, tiempo=900):
    proceso = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True,
                             text=True, encoding="utf-8", timeout=tiempo, cwd=str(RAIZ))
    return proceso.returncode, proceso.stdout, proceso.stderr


def citas(archivo):
    codigo, salida, error = correr(SCRIPTS / "cruzar_citas.py", archivo, "--json")
    if codigo not in (0, 1):
        raise RuntimeError(error)
    return codigo, json.loads(salida)


# ------------------------------------------------------------------ 1-3

def caso_localizadores():
    codigo, d = citas(CASOS / "citas_localizadores.md")
    locs = sorted(l["localizador"] for l in d["observaciones"]["localizadores"])
    esperado = sorted(["I, cap. 1", "cap. 3", "sec. 2.1", "fig. 2", "pp. 3-4", "t. 2", "cap. 3",
                       "II, cap. 4", "párr. 4"])
    anotar("1 localizadores tras el año", esperado, locs, locs == esperado)
    limpio = not (d["a_citas_sin_referencia"] or d["b_referencias_no_citadas"]
                  or d["c_autor_o_anio_discordante"])
    anotar("1 citas con localizador = (Autor, año)", "9 citas, (a)(b)(c) vacías, código 0",
           f"{d['total_citas']} citas, vacías={limpio}, código {codigo}",
           d["total_citas"] == 9 and limpio and codigo == 0)
    cervantes = [c for c in d["citas"] if c["autor"] == "Cervantes"]
    anotar("1 Cervantes 1605/2004, I, cap. 1", "2 citas de Cervantes 2004 con referencia",
           [(c["anio"], bool(c["referencia"])) for c in cervantes],
           len(cervantes) == 2 and all(c["anio"] == "2004" and c["referencia"] for c in cervantes))


def caso_compuestos():
    _, d = citas(CASOS / "citas_compuestos.md")
    c = [(x["cita"], x["problema"]) for x in d["c_autor_o_anio_discordante"]]
    garcia = [p for t, p in c if "García" in t]
    anotar("2 García vs García Linera", "una vez en (c), ni en (a) ni en (b)",
           f"(c)={len(garcia)}; a={len(d['a_citas_sin_referencia'])}; "
           f"b={len(d['b_referencias_no_citadas'])}",
           len(garcia) == 1 and "«García» y la referencia «García Linera»" in garcia[0]
           and not d["a_citas_sin_referencia"] and not d["b_referencias_no_citadas"])
    rivera = [p for t, p in c if "Rivera" in t]
    anotar("2 Rivera Cusicanqui vs Rivera (inversa)", "una vez en (c)", rivera,
           len(rivera) == 1 and "«Rivera Cusicanqui» y la referencia «Rivera»" in rivera[0])
    perez = [p for t, p in c if "Pérez" in t]
    anotar("2 Pérez con dos Pérez … 2018", "ambigua (no se resuelve), 2 citas",
           [p[:40] for p in perez], len(perez) == 2 and all(p.startswith("ambigua") for p in perez))
    exactas = [t for t, _ in c if "Mendoza" in t or "Cruz" in t]
    anotar("2 apellidos exactos no se tocan", "Mendoza y de la Cruz fuera de (c)", exactas,
           not exactas)


def caso_ventana():
    _, d = citas(CASOS / "citas_ventana.md")
    a = [x["cita"] for x in d["a_citas_sin_referencia"]]
    anotar("3 IPCC … Pérez (2021) sin referencia de Pérez", "Pérez en (a)", a,
           any("Pérez" in x for x in a))
    c = [x["cita"] for x in d["c_autor_o_anio_discordante"]]
    anotar("3 El IPCC y Pérez (2021)", "en (c): dos autores, la obra tiene uno", c,
           any("IPCC y Pérez" in x for x in c))
    sexto = [x for x in d["citas"] if x["cita"].startswith("Sexto Informe")]
    anotar("3 IPCC, Sexto Informe de Evaluación (2021)", "sigue siendo IPCC 2021",
           [(x["autor"], bool(x["referencia"])) for x in sexto],
           len(sexto) == 1 and sexto[0]["autor"] == "IPCC" and sexto[0]["referencia"])


# ------------------------------------------------------------------ 4

def caso_registros_sin_red():
    import verificar_referencias as vr
    html = (REGISTROS / "arxiv_abs_2407.12447.html").read_bytes()
    originales = (vr.en_arxiv_api, vr.pedir_bytes, vr.en_crossref, vr.en_openalex, vr.en_registro)
    try:
        # arXiv limita (429): se usa la página arxiv.org/abs guardada.
        def api_limitada(_):
            raise vr.SinRespuesta("HTTP 429 (simulado)")
        vr.en_arxiv_api = api_limitada
        vr.pedir_bytes = lambda url, *a, **k: (html, url)
        r = vr.en_arxiv("2407.12447")
        anotar("4 arXiv con 429 -> página abs (guardada)", "título y 2024",
               (r[0][0][:40], r[0][1]),
               r[0][1] == 2024 and r[0][0].startswith("Low latency carbon budget"))
        # evaluar(): Crossref 404 + registro sin respuesta -> SIN COMPROBAR.
        def crossref_404(_):
            raise urllib.error.HTTPError("u", 404, "Not Found", None, None)
        def openalex_401(_):
            raise urllib.error.HTTPError("u", 401, "Unauthorized", None, None)
        vr.en_crossref, vr.en_openalex = crossref_404, openalex_401
        ref = (CASOS / "referencias_registros.md").read_text(encoding="utf-8").split("\n## Referencias")[1]
        ke = [l for l in ref.splitlines() if l.startswith("Ke, P.")][0]
        def registro_mudo(_):
            raise vr.SinRespuesta("HTTP 429 (simulado)")
        vr.en_registro = registro_mudo
        estado = vr.evaluar(ke)[0]
        anotar("4 Crossref 404 + arXiv mudo", "SIN COMPROBAR", estado, estado == "SIN COMPROBAR")
        def registro_inexistente(_):
            raise vr.DoiInexistente("arXiv no tiene el identificador (simulado)")
        vr.en_registro = registro_inexistente
        estado = vr.evaluar(ke)[0]
        anotar("4 Crossref 404 + arXiv sin el id", "NO ENCONTRADA", estado, estado == "NO ENCONTRADA")
    finally:
        (vr.en_arxiv_api, vr.pedir_bytes, vr.en_crossref, vr.en_openalex, vr.en_registro) = originales


def caso_registros_red(sin_red):
    nombres = ["4 red: Ke et al. 2024 (arXiv 2407.12447)", "4 red: Zenodo 19723104",
               "4 red: arXiv inexistente 2407.99999"]
    esperados = ["ENCONTRADA (o SIN COMPROBAR)", "ENCONTRADA", "NO ENCONTRADA"]
    if sin_red:
        for n, e in zip(nombres, esperados):
            anotar(n, e, "--sin-red", False, omitido=True)
        return
    codigo, salida, error = correr(SCRIPTS / "verificar_referencias.py",
                                   CASOS / "referencias_registros.md", "--json", tiempo=1200)
    try:
        estados = [r["estado"] for r in json.loads(salida)["referencias"]]
    except ValueError:
        for n, e in zip(nombres, esperados):
            anotar(n, e, f"código {codigo}: {error.strip()[-80:]}", False, omitido=codigo == 2)
        return
    anotar(nombres[0], esperados[0], estados[0], estados[0] in ("ENCONTRADA", "SIN COMPROBAR"))
    for n, e, obtenido in zip(nombres[1:], esperados[1:], estados[1:]):
        # SIN COMPROBAR = el servicio no respondió: no se puede afirmar nada.
        anotar(n, e, obtenido, obtenido == e, omitido=obtenido == "SIN COMPROBAR")


# ------------------------------------------------------------------ 5

def caso_apellidos():
    import buscar_academico as ba
    import comun

    class Opciones:
        max, desde, hasta, idioma, solo_abierto, scielo = 20, None, None, None, False, False

    pruebas_nombre = [("Jeffeson Goncalves de Souza", "de Souza, J. G."),       # arXiv
                      ("Auke M. van der Woude", "van der Woude, A. M."),        # arXiv
                      ("Guido R. van der Werf", "van der Werf, G. R."),         # arXiv
                      ("A. D. de Almeida", "de Almeida, A. D."),                # Semantic Scholar
                      ("T. C. da Silva", "da Silva, T. C."),                    # Semantic Scholar
                      ("A. C. Do Rêgo", "Do Rêgo, A. C."),                      # Semantic Scholar
                      ("Juan Pablo Narváez-Herrera", "Narváez-Herrera, J. P."),
                      ("Philippe Ciais", "Ciais, P."),
                      # Límite documentado: compuesto hispano sin partícula.
                      ("Adrian Rolando Riascos Vallejos", "Vallejos, A. R. R.")]
    obtenidos = [ba.autor_desde_nombre_completo(n) for n, _ in pruebas_nombre]
    malos = [(n, e, o) for (n, e), o in zip(pruebas_nombre, obtenidos) if e != o]
    anotar("5 partículas (nombres reales de arXiv y S2)", "9/9 como se espera",
           malos or "9/9", not malos)

    # Respuestas reales guardadas, pasadas por los analizadores reales.
    originales = (comun.pedir_json, comun.pedir)
    try:
        def leer(nombre):
            return json.loads((REGISTROS / nombre).read_text(encoding="utf-8"))
        s2 = leer("s2_10_17268_sci_agropecu_2025_051.json")
        cr = leer("crossref_10_17268_sci_agropecu_2025_051.json")["message"]
        comun.pedir_json = lambda url, *a, **k: {"data": [s2]}
        reg_s2 = ba.buscar_s2("x", Opciones)
        comun.pedir_json = lambda url, *a, **k: {"message": {"items": [cr]}}
        reg_cr = ba.buscar_crossref("x", Opciones)
        comun.pedir = lambda url, *a, **k: ((REGISTROS / "arxiv_2504.09189.xml").read_bytes(), url, "")
        reg_ax = ba.buscar_arxiv("x", Opciones)
    finally:
        comun.pedir_json, comun.pedir = originales
    for lista, base in ((reg_s2, "s2"), (reg_cr, "crossref"), (reg_ax, "arxiv")):
        for reg in lista:
            reg["bases"] = [base]  # como hace main() con cada base
    anotar("5 S2 real: «Jorge Cardoso de Azevedo»", "de Azevedo, J. C.", reg_s2[0]["autores"][1],
           reg_s2[0]["autores"][1] == "de Azevedo, J. C.")
    ax = [a for a in reg_ax[0]["autores"] if "Woude" in a or "Werf" in a]
    anotar("5 arXiv real 2504.09189", "van der Woude / van der Werf", ax,
           ax == ["van der Woude, A. M.", "van der Werf, G. R."])
    for orden, lista in (("S2 primero", reg_s2 + reg_cr), ("Crossref primero", reg_cr + reg_s2)):
        copia = json.loads(json.dumps(lista))
        unidos = ba.unir(copia)
        autores = unidos[0]["autores"] if len(unidos) == 1 else None
        anotar(f"5 unir ({orden}): autores de Crossref", "1 registro con «Cardoso de Azevedo, J.»",
               (len(unidos), autores[1] if autores else None),
               len(unidos) == 1 and autores == reg_cr[0]["autores"]
               and "_autores_crossref" not in unidos[0])


# ------------------------------------------------------------------ 6

def crear_xlsx(ruta, malo):
    import openpyxl
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = "Focos"
    hoja.append(["Departamento", "Focos de calor 2024", "Nota"])
    if malo:
        hoja.append(["Pando", "#REF!", "pendiente: confirmar con la fuente"])
    else:
        hoja.append(["Pando", 1520, "Fuente: elaboración propia"])
    hoja.append(["Beni", 3010, ""])
    hoja["D1"], hoja["D2"] = "Total", "=SUM(B2:B3)"
    if malo:
        libro.create_sheet("Vacía")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    libro.save(ruta)


def encargo_xlsx(nombre, malo):
    carpeta = SALIDA / nombre
    shutil.rmtree(carpeta, ignore_errors=True)
    (carpeta / "entrega").mkdir(parents=True)
    (carpeta / "encargo.md").write_text("# Encargo\n\n- nivel: pregrado\n- tipo: informe\n"
                                       "- estado: en verificación\n", encoding="utf-8")
    crear_xlsx(carpeta / "entrega" / "focos_pando.xlsx", malo)
    time.sleep(0.05)
    (carpeta / "entrega" / "informe_verificacion.md").write_text(
        "# Informe de verificación\n\n## Dictamen\n\n**APROBADO**\n", encoding="utf-8")
    return carpeta


def caso_xlsx():
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        anotar("6 xlsx", "openpyxl instalado", "falta openpyxl", False, omitido=True)
        return
    control = SCRIPTS / "control_final.py"
    bueno = encargo_xlsx("xlsx_bueno", False)
    codigo, salida, error = correr(control, bueno, "--sin-red", "--json")
    datos = json.loads(salida) if salida.strip() else {}
    estados = {k: v["estado"] for k, v in datos.get("controles", {}).items()}
    anotar("6 xlsx bueno: control_final", "código 0; hoja ok; resto no aplica",
           f"código {codigo}; {estados}",
           codigo == 0 and estados.get("hoja") == "ok"
           and all(v == "no aplica" for k, v in estados.items() if k != "hoja"))
    codigo, salida, _ = correr(HOOK, "--comprobar", bueno)
    anotar("6 xlsx bueno: hook --comprobar", "PASA (0)", f"{codigo} {salida.strip().splitlines()[-1]}",
           codigo == 0)

    malo = encargo_xlsx("xlsx_malo", True)
    codigo, salida, _ = correr(control, malo, "--sin-red", "--json")
    datos = json.loads(salida) if salida.strip() else {}
    hoja = datos.get("controles", {}).get("hoja", {})
    resumen = hoja.get("resumen", "")
    anotar("6 xlsx malo: control_final", "código 1; #REF! y «pendiente:»; aviso hoja vacía",
           f"código {codigo}; {hoja.get('estado')}; {resumen[:90]}",
           codigo == 1 and hoja.get("estado") == "bloquea" and "#REF!" in resumen
           and "pendiente:" in resumen and any("Vacía" in a for a in datos.get("avisos", [])))
    codigo, salida, _ = correr(HOOK, "--comprobar", malo)
    anotar("6 xlsx malo: hook --comprobar", "BLOQUEARÍA (1) por hoja",
           f"{codigo} {'hoja' if 'hoja (código 1)' in salida else salida[-80:]}",
           codigo == 1 and "hoja (código 1)" in salida)
    # El xlsx cambia después del control: el hook lo ve por la huella.
    crear_xlsx(bueno / "entrega" / "focos_pando.xlsx", True)
    codigo, salida, _ = correr(HOOK, "--comprobar", bueno)
    anotar("6 xlsx cambiado tras el control: hook", "BLOQUEARÍA (huella)", codigo,
           codigo == 1 and "huella" in salida)

    # .docx y .xlsx juntos: el principal sigue siendo el .docx.
    mixto = SALIDA / "xlsx_mixto"
    shutil.rmtree(mixto, ignore_errors=True)
    shutil.copytree(RAIZ / "pruebas" / "salida" / "caso_control" / "bueno", mixto)
    crear_xlsx(mixto / "entrega" / "datos.xlsx", True)
    codigo, salida, _ = correr(control, mixto, "--sin-red", "--json")
    datos = json.loads(salida) if salida.strip() else {}
    avisos = " ".join(datos.get("avisos", []))
    anotar("6 docx + xlsx: principal", ".docx; el .xlsx en avisos; sin control hoja",
           f"{datos.get('archivo')}; aviso xlsx={'datos.xlsx' in avisos}",
           str(datos.get("archivo", "")).endswith(".docx") and "datos.xlsx" in avisos
           and "hoja" not in datos.get("controles", {}))
    codigo, salida, _ = correr(control, mixto, "--sin-red", "--json", "--archivo", "datos.xlsx")
    datos = json.loads(salida) if salida.strip() else {}
    anotar("6 docx + xlsx con --archivo datos.xlsx", "xlsx controlado, código 1",
           f"{datos.get('archivo')}; código {codigo}",
           datos.get("archivo") == "datos.xlsx" and codigo == 1
           and any(".docx" in a for a in datos.get("avisos", [])))


# ------------------------------------------------------------------ 7

def caso_fragmento():
    textos = RAIZ / "pruebas" / "salida" / "aceptacion" / "ensayo_incendios" / "fuentes" / "texto"
    for frase, debe in (("global net land CO2 sink of 0.44", "0.44 ± 0.21 GtC"),
                        ("37 0.11 ppm at Mauna Loa", "»3.37 ± 0.11 ppm"),
                        ("account for most of the fire events in Amazonia", "of the ﬁre events")):
        codigo, salida, _ = correr(SCRIPTS / "extraer_texto.py", "--buscar", frase, textos, "--json")
        try:
            fragmento = json.loads(salida)["resultados"][0]["fragmento"]
        except (ValueError, IndexError, KeyError):
            fragmento = f"código {codigo}"
        i = fragmento.find(debe)
        anotar(f"7 --buscar «{frase[:28]}»", debe,
               fragmento[max(0, i - 5):i + len(debe) + 5] if i >= 0 else fragmento[:60], i >= 0)


# ------------------------------------------------------------------ R

def resumen_citas(d):
    return {"a": [(x["cita"], x["anio"]) for x in d["a_citas_sin_referencia"]],
            "b": d["b_referencias_no_citadas"],
            "c": [(x["cita"], x["problema"]) for x in d["c_autor_o_anio_discordante"]],
            "d": [(x["tipo"], x["referencia"]) for x in d["d_lista_de_referencias"]],
            "loc": [x["localizador"] for x in d["observaciones"]["localizadores"]],
            "siglas": [x["sigla"] for x in d["observaciones"]["siglas_sin_presentar"]],
            "desc": [x["cita"] for x in d["observaciones"]["descartados_lugar_o_periodo"]],
            "citas": [(x["cita"], x["autor"], x["referencia"]) for x in d["citas"]]}


def caso_regresion():
    ensayo = sorted((RAIZ / "pruebas" / "aceptacion" / "ensayo_incendios" / "entrega").glob("*.docx"))
    for nombre, archivo in (("cruzar_citas_prueba", CASOS / "citas_prueba.md"),
                            ("cruzar_monografia", RAIZ / "pruebas" / "salida" / "monografia" /
                             "monografia.docx"),
                            ("cruzar_ensayo_aceptacion", ensayo[0] if ensayo else None)):
        if archivo is None or not archivo.exists():
            anotar(f"R {nombre}", "igual a la referencia", "falta el archivo", False)
            continue
        _, actual = citas(archivo)
        antes = json.loads((REFERENCIA / f"{nombre}.json").read_text(encoding="utf-8"))
        a, b = resumen_citas(antes), resumen_citas(actual)
        distintos = [k for k in a if a[k] != b[k]]
        anotar(f"R {nombre}", "igual a la referencia", distintos or "igual", not distintos)
    for caso in ("bueno", "malo", "ensayo_incendios"):
        origen = (RAIZ / "pruebas" / "salida" / ("aceptacion" if caso == "ensayo_incendios"
                                                  else "caso_control") / caso)
        copia = SALIDA / caso  # control_final reescribe entrega/controles.json: copia
        if not copia.exists():
            shutil.copytree(origen, copia)
        codigo, salida, _ = correr(SCRIPTS / "control_final.py", copia, "--sin-red", "--json")
        actual = json.loads(salida)
        antes = json.loads((REFERENCIA / f"control_final_{caso}.json").read_text(encoding="utf-8"))

        def resumen(d):
            return (d["aprobado_mecanico"], {k: v["estado"] for k, v in d["controles"].items()},
                    len(d["avisos"]), len(d["pendientes_verificador"]))
        anotar(f"R control_final {caso}", resumen(antes), resumen(actual),
               resumen(antes) == resumen(actual))


# ------------------------------------------------------------------ principal

def main():
    sin_red = "--sin-red" in sys.argv[1:]
    SALIDA.mkdir(parents=True, exist_ok=True)
    for prueba in (caso_localizadores, caso_compuestos, caso_ventana, caso_registros_sin_red,
                   lambda: caso_registros_red(sin_red), caso_apellidos, caso_xlsx,
                   caso_fragmento, caso_regresion):
        try:
            prueba()
        except Exception as error:  # una prueba rota no tapa a las demás
            anotar(getattr(prueba, "__name__", "prueba"), "sin excepción",
                   f"{type(error).__name__}: {error}", False)
    ancho = max(len(c) for c, *_ in RESULTADOS)
    for caso, esperado, obtenido, estado in RESULTADOS:
        print(f"{caso:<{ancho}}  {estado:<7}  esperado: {esperado}")
        print(f"{'':<{ancho}}  {'':<7}  obtenido: {obtenido}")
    fallos = sum(e == "FALLA" for *_, e in RESULTADOS)
    omitidos = sum(e == "omitido" for *_, e in RESULTADOS)
    print(f"\n{len(RESULTADOS)} casos: {len(RESULTADOS) - fallos - omitidos} ok, "
          f"{fallos} fallos, {omitidos} omitidos")
    return 1 if fallos else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sys.exit(main())
