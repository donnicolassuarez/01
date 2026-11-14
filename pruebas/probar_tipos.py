# -*- coding: utf-8 -*-
"""Pruebas de la skill tipos-de-trabajo con el constructor y el verificador.

Uso:
  python pruebas/probar_tipos.py [--salida carpeta]

Por defecto escribe en pruebas/salida/caso_tipos/ (no versionada).

Casos:
  1. Positivos: cada pruebas/casos/tipo_<tipo>.md se construye sin avisos y
     verificar_formato.py da CONFORME sin ERROR en o).
  2. Negativos, por tipo y variante: falta una sección obligatoria; dos
     secciones en orden incorrecto. Deben dar ERROR solo en o), con el
     nombre de la sección. Más: monografía por capítulos sin capítulos,
     artículo sin resumen, informe sin portada.
  3. Regresión: ensayo_prueba.md (4 páginas, CONFORME), el ensayo de la
     prueba de aceptación (5 páginas, CONFORME), la monografía real (mismo
     resultado de o) que antes de tipos.json) y crear_docx_defectuosos.py.
  4. tipos.json ausente (regla anterior + aviso), corrupto o con esquema
     inválido (salida 2) y respaldo por la variable TIPOS_TRABAJO.
  5. Coherencia de SKILL.md con tipos.json (secciones y portada por tipo).

Imprime una tabla caso -> esperado / obtenido. Sale con 1 si algo falla.
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPTS = RAIZ / "skills" / "niveles-academicos" / "scripts"
SKILL_TIPOS = RAIZ / "skills" / "tipos-de-trabajo"
CASOS = RAIZ / "pruebas" / "casos"
ACEPTACION = RAIZ / "pruebas" / "aceptacion" / "ensayo_incendios" / "entrega"
MONOGRAFIA = RAIZ / "pruebas" / "salida" / "monografia" / "monografia.docx"

# (archivo de caso, --tipo para el verificador, --variante)
CASOS_TIPO = [
    ("ensayo", "ensayo", None),
    ("monografia", "monografia", None),
    ("monografia_capitulos", "monografia", "capitulos"),
    ("informe", "informe", None),
    ("informe_simple", "informe", "simple"),
    ("articulo", "articulo", None),
    ("articulo_revision", "articulo", "revision"),
    ("perfil", "perfil", None),
    ("tesis", "tesis", None),
]

# Resultado de o) en la monografía real antes de tipos.json (regla anterior).
MONOGRAFIA_O_ANTES = [
    ("ERROR", "la primera página no está en blanco"),
    ("ERROR", "«Introducción» no aparece como encabezado solo con estilo de título"),
    ("ERROR", "falta el encabezado «Desarrollo»"),
]

tt_spec = importlib.util.spec_from_file_location("tipos_trabajo", SKILL_TIPOS / "tipos_trabajo.py")
tt = importlib.util.module_from_spec(tt_spec)
tt_spec.loader.exec_module(tt)
DEFS = tt.cargar(SKILL_TIPOS / "tipos.json")

filas = []


def anotar(caso, esperado, obtenido, bien):
    filas.append((caso, esperado, obtenido, bien))


def entorno(extra=None):
    env = {k: v for k, v in os.environ.items() if k != "TIPOS_TRABAJO"}
    env.update(extra or {})
    return env


def correr(script, *argumentos, scripts=SCRIPTS, env=None):
    r = subprocess.run([sys.executable, str(scripts / script), *map(str, argumentos)],
                       capture_output=True, text=True, encoding="utf-8", env=entorno(env))
    try:
        datos = json.loads(r.stdout)
    except json.JSONDecodeError:
        datos = None
    return r.returncode, datos, r.stdout + r.stderr


def construir(md, docx, *extra, **kw):
    return correr("construir_docx.py", md, "--salida", docx, "--json", *extra, **kw)


def verificar(docx, tipo=None, variante=None, *extra, **kw):
    args = [docx, "--json"]
    if tipo:
        args += ["--tipo", tipo]
    if variante:
        args += ["--variante", variante]
    return correr("verificar_formato.py", *args, *extra, **kw)


def errores(datos, fuera_de=None):
    return [h for h in (datos or {}).get("hallazgos", []) if h["nivel"] == "ERROR"
            and (fuera_de is None or h["comprobacion"] != fuera_de)]


def mensajes_o(datos):
    return [(h["nivel"], h["mensaje"]) for h in (datos or {}).get("hallazgos", [])
            if h["comprobacion"] == "o"]


# ---------------------------------------------------------------- Markdown

def bloques_md(texto):
    """(cabecera, [(título, líneas)], referencias): partes por títulos de nivel 1."""
    lineas = texto.splitlines(keepends=True)
    cortes = [i for i, l in enumerate(lineas) if re.match(r"^# \S", l)]
    cabecera = "".join(lineas[:cortes[0]])
    partes = []
    for n, i in enumerate(cortes):
        fin = cortes[n + 1] if n + 1 < len(cortes) else len(lineas)
        partes.append((lineas[i][2:].strip(), "".join(lineas[i:fin])))
    return cabecera, partes


def ubicar(est, partes):
    """Índice del bloque de cada sección obligatoria ordenable (no capítulos)."""
    resultado = []
    for seccion in est["secciones"]:
        if seccion.get("capitulos") or seccion.get("orden", True) is False:
            continue
        for i, (titulo, _) in enumerate(partes):
            if tt.coincide(tt.normalizar(titulo), seccion):
                resultado.append((seccion, i))
                break
    return resultado


def negativos(nombre, tipo, variante, carpeta):
    """Genera los .md negativos: [(etiqueta, ruta, nombres esperados, patrón)]."""
    texto = (CASOS / f"tipo_{nombre}.md").read_text(encoding="utf-8")
    cabecera, partes = bloques_md(texto)
    est = tt.estructura(DEFS, tipo, variante)
    ubicadas = ubicar(est, partes)
    casos = []
    # falta una sección: la segunda ordenable (o la única)
    seccion, i = ubicadas[1] if len(ubicadas) > 1 else ubicadas[0]
    ruta = carpeta / f"{nombre}_falta.md"
    ruta.write_text(cabecera + "".join(b for j, (_, b) in enumerate(partes) if j != i), encoding="utf-8")
    casos.append((f"falta «{seccion['nombre']}»", ruta, [seccion["nombre"]],
                  r"falta el encabezado|no aparece como encabezado"))
    # orden: se intercambian las dos primeras ordenables
    (s1, i1), (s2, i2) = ubicadas[0], ubicadas[1]
    nuevas = [b for _, b in partes]
    nuevas[i1], nuevas[i2] = nuevas[i2], nuevas[i1]
    ruta = carpeta / f"{nombre}_orden.md"
    ruta.write_text(cabecera + "".join(nuevas), encoding="utf-8")
    casos.append((f"«{s2['nombre']}» antes de «{s1['nombre']}»", ruta, [s1["nombre"], s2["nombre"]],
                  r"fuera de orden"))
    return casos


# ---------------------------------------------------------------- pruebas

def probar_tipos(salida):
    carpeta = salida / "tipos"
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre, tipo, variante in CASOS_TIPO:
        md = CASOS / f"tipo_{nombre}.md"
        docx = carpeta / f"{nombre}.docx"
        codigo_c, datos_c, _ = construir(md, docx)
        codigo_v, datos_v, salida_v = verificar(docx, tipo, variante)
        avisos_c = (datos_c or {}).get("avisos", [])
        o = mensajes_o(datos_v)
        bien = codigo_c == 0 and codigo_v == 0 and not any(n == "ERROR" for n, _ in o)
        obtenido = (f"construir {codigo_c}{' ' + '; '.join(avisos_c) if avisos_c else ''}; "
                    f"{(datos_v or {}).get('veredicto', salida_v[-120:])}; "
                    f"{(datos_v or {}).get('paginas')} pág.; o) " + " | ".join(m for _, m in o))
        anotar(f"{nombre}: esqueleto", "CONFORME, o) sin ERROR", obtenido, bien)

        for etiqueta, ruta_md, nombres, patron in negativos(nombre, tipo, variante, carpeta):
            docx = ruta_md.with_suffix(".docx")
            codigo_c, datos_c, _ = construir(ruta_md, docx)
            codigo_v, datos_v, salida_v = verificar(docx, tipo, variante)
            errores_o = [h["mensaje"] for h in errores(datos_v) if h["comprobacion"] == "o"]
            ajenos = errores(datos_v, fuera_de="o")
            acierto = any(re.search(patron, m) and any(f"«{n}»" in m for n in nombres) for m in errores_o)
            avisa = any(any(f"«{n}»" in a for n in nombres) for a in (datos_c or {}).get("avisos", []))
            bien = codigo_v == 1 and acierto and not ajenos and avisa
            obtenido = (" | ".join(errores_o) or salida_v[-150:]) + \
                (f" | AJENOS: {[h['comprobacion'] + ') ' + h['mensaje'] for h in ajenos]}" if ajenos else "") + \
                ("" if avisa else " | el constructor no avisó")
            anotar(f"{nombre}: {etiqueta}", "ERROR en o) con la sección, sin ajenos", obtenido, bien)


def probar_extras(salida):
    carpeta = salida / "tipos"
    # monografía por capítulos sin capítulos
    texto = (CASOS / "tipo_monografia_capitulos.md").read_text(encoding="utf-8")
    ruta = carpeta / "monografia_capitulos_sin_capitulos.md"
    ruta.write_text(re.sub(r"^# Capítulo [IVX]+\. ", "# ", texto, flags=re.M), encoding="utf-8")
    construir(ruta, ruta.with_suffix(".docx"))
    codigo, datos, _ = verificar(ruta.with_suffix(".docx"), "monografia", "capitulos")
    errores_o = [h["mensaje"] for h in errores(datos) if h["comprobacion"] == "o"]
    bien = codigo == 1 and any("Capítulos numerados" in m for m in errores_o) and not errores(datos, "o")
    anotar("monografia_capitulos: sin capítulos", "ERROR «Capítulos numerados»", " | ".join(errores_o), bien)
    # artículo sin resumen
    texto = (CASOS / "tipo_articulo.md").read_text(encoding="utf-8")
    texto = re.sub(r"# Resumen\n\n.*?\n\n", "", texto, flags=re.S)
    ruta = carpeta / "articulo_sin_resumen.md"
    ruta.write_text(texto, encoding="utf-8")
    construir(ruta, ruta.with_suffix(".docx"))
    codigo, datos, _ = verificar(ruta.with_suffix(".docx"), "articulo")
    errores_o = [h["mensaje"] for h in errores(datos) if h["comprobacion"] == "o"]
    bien = codigo == 1 and any("«Resumen»" in m for m in errores_o) and not errores(datos, "o")
    anotar("articulo: sin resumen", "ERROR falta «Resumen»", " | ".join(errores_o), bien)
    # informe sin portada
    docx = carpeta / "informe_sin_portada.docx"
    construir(CASOS / "tipo_informe.md", docx, "--portada", "ninguna")
    codigo, datos, _ = verificar(docx, "informe")
    errores_o = [h["mensaje"] for h in errores(datos) if h["comprobacion"] == "o"]
    bien = codigo == 1 and errores_o == ["falta la portada con datos"] and not errores(datos, "o")
    anotar("informe: sin portada", "ERROR falta la portada con datos", " | ".join(errores_o), bien)
    # sinónimo y tipo desconocido
    codigo, datos, _ = verificar(carpeta / "perfil.docx", "Perfil de tesis")
    anotar("sinónimo «Perfil de tesis»", "se resuelve a perfil, CONFORME",
           f"tipo {(datos or {}).get('tipo')}; {(datos or {}).get('veredicto')}",
           codigo == 0 and (datos or {}).get("tipo") == "perfil")
    codigo, datos, texto = verificar(carpeta / "perfil.docx", "novela")
    anotar("tipo desconocido", "salida 2 con la lista de tipos", f"salida {codigo}: {(datos or {}).get('error')}",
           codigo == 2 and "tipos:" in ((datos or {}).get("error") or ""))
    codigo, datos, texto = verificar(carpeta / "ensayo.docx", "ensayo", "capitulos")
    anotar("variante inexistente", "salida 2", f"salida {codigo}: {(datos or {}).get('error')}", codigo == 2)


def probar_regresion(salida):
    carpeta = salida / "regresion"
    carpeta.mkdir(parents=True, exist_ok=True)
    docx = carpeta / "ensayo_prueba.docx"
    codigo_c, datos_c, _ = construir(CASOS / "ensayo_prueba.md", docx, "--tipo", "ensayo")
    codigo_v, datos_v, _ = verificar(docx, "ensayo")
    bien = codigo_c == 0 and (datos_c or {}).get("paginas") == 4 and codigo_v == 0 and \
        (datos_v or {}).get("avisos") == 0
    anotar("regresión: ensayo_prueba.md", "construye sin avisos, 4 pág., CONFORME sin avisos",
           f"construir {codigo_c}, {(datos_c or {}).get('paginas')} pág.; {(datos_v or {}).get('veredicto')}", bien)

    entregables = sorted(ACEPTACION.glob("*.docx"))
    if entregables:
        codigo, datos, _ = verificar(entregables[0], "ensayo", None, "--min-paginas", 5, "--max-paginas", 5)
        anotar("regresión: ensayo de aceptación", "CONFORME, 5 pág.",
               f"{(datos or {}).get('veredicto')}; {(datos or {}).get('paginas')} pág.",
               codigo == 0 and (datos or {}).get("paginas") == 5)
    else:
        anotar("regresión: ensayo de aceptación", "CONFORME, 5 pág.", "no está el docx", False)

    if MONOGRAFIA.is_file():
        codigo, datos, _ = verificar(MONOGRAFIA, "monografia")
        o = mensajes_o(datos)
        anotar("regresión: monografía real, por defecto", "o) igual que antes (3 ERROR)",
               f"{(datos or {}).get('veredicto')}; o) " + " | ".join(m for _, m in o),
               o == MONOGRAFIA_O_ANTES and (datos or {}).get("errores") == 10)
        codigo, datos, _ = verificar(MONOGRAFIA, "monografia", "capitulos")
        o = mensajes_o(datos)
        anotar("monografía real, variante capitulos", "informativo: qué cambia en o)",
               f"{(datos or {}).get('veredicto')}; o) " + " | ".join(f"{n} {m}" for n, m in o), True)
    else:
        anotar("regresión: monografía real", "o) igual que antes", "no está el docx", False)

    r = subprocess.run([sys.executable, str(RAIZ / "pruebas" / "crear_docx_defectuosos.py"), "--comprobar"],
                       capture_output=True, text=True, encoding="utf-8", env=entorno())
    ultima = (r.stdout.strip().splitlines() or [""])[-1]
    anotar("regresión: crear_docx_defectuosos.py", "9/9", ultima, r.returncode == 0 and ultima.startswith("9/9"))


def copia_scripts(destino, tipos_json=None):
    """Copia los scripts en <destino>/skills/niveles-academicos/scripts y, si se
    pide, una skill tipos-de-trabajo hermana con el tipos.json dado (texto)."""
    if destino.exists():
        shutil.rmtree(destino)
    scripts = destino / "skills" / "niveles-academicos" / "scripts"
    scripts.mkdir(parents=True)
    for archivo in SCRIPTS.glob("*.py"):
        shutil.copy2(archivo, scripts)
    if tipos_json is not None:
        hermana = destino / "skills" / "tipos-de-trabajo"
        hermana.mkdir(parents=True)
        shutil.copy2(SKILL_TIPOS / "tipos_trabajo.py", hermana)
        (hermana / "tipos.json").write_text(tipos_json, encoding="utf-8")
    return scripts


def probar_sin_tipos(salida):
    carpeta = salida / "configuracion"
    carpeta.mkdir(parents=True, exist_ok=True)
    # ausente: regla anterior + aviso
    scripts = copia_scripts(carpeta / "sin_json")
    docx = carpeta / "ensayo_sin_json.docx"
    codigo_c, datos_c, _ = construir(CASOS / "ensayo_prueba.md", docx, "--tipo", "ensayo", scripts=scripts)
    codigo_v, datos_v, _ = verificar(docx, "ensayo", scripts=scripts)
    o = mensajes_o(datos_v)
    bien = codigo_c == 0 and (datos_c or {}).get("paginas") == 4 and codigo_v == 0 and \
        ("OK", "portada blanca e Introducción, Desarrollo y Conclusiones presentes") in o and \
        any(n == "AVISO" and "tipos.json" in m for n, m in o) and \
        any("tipos.json" in n for n in (datos_c or {}).get("notas", []))
    anotar("tipos.json ausente: ensayo", "regla anterior, CONFORME + aviso",
           f"construir {codigo_c}, {(datos_c or {}).get('paginas')} pág.; {(datos_v or {}).get('veredicto')}; "
           f"o) " + " | ".join(f"{n} {m}" for n, m in o), bien)
    if MONOGRAFIA.is_file():
        codigo, datos, _ = verificar(MONOGRAFIA, "monografia", scripts=scripts)
        o = [x for x in mensajes_o(datos) if x[0] == "ERROR"]
        anotar("tipos.json ausente: monografía real", "mismos 3 ERROR en o)", f"{len(o)} ERROR en o)",
               o == MONOGRAFIA_O_ANTES)
    codigo, datos, _ = verificar(carpeta / ".." / "tipos" / "tesis.docx", "tesis", scripts=scripts)
    o = mensajes_o(datos)
    anotar("tipos.json ausente: --tipo tesis", "no aplica + aviso (sin salida 2)",
           f"salida {codigo}; o) " + " | ".join(f"{n} {m}" for n, m in o),
           codigo in (0, 1) and ("OK", "no aplica a este tipo") in o)
    # respaldo por variable de entorno
    env = {"TIPOS_TRABAJO": str(SKILL_TIPOS / "tipos.json")}
    codigo, datos, _ = verificar(carpeta / ".." / "tipos" / "tesis.docx", "tesis", scripts=scripts, env=env)
    anotar("TIPOS_TRABAJO como respaldo", "usa la definición (tesis CONFORME, sin aviso de ausencia)",
           f"salida {codigo}; {(datos or {}).get('veredicto')}",
           codigo == 0 and not any("tipos.json" in m for _, m in mensajes_o(datos)))
    # corrupto y esquema inválido: salida 2 en ambos scripts
    original = (SKILL_TIPOS / "tipos.json").read_text(encoding="utf-8")
    for etiqueta, contenido, pista in (
            ("corrupto", original[:200], "no es JSON válido"),
            ("esquema inválido", original.replace('"portada": "blanca"', '"portada": "azul"', 1), "portada")):
        scripts = copia_scripts(carpeta / etiqueta.replace(" ", "_"), contenido)
        codigo_c, datos_c, _ = construir(CASOS / "ensayo_prueba.md", carpeta / "x.docx", "--tipo", "ensayo",
                                         "--sin-pdf", scripts=scripts)
        codigo_v, datos_v, _ = verificar(carpeta / "regresion_inexistente.docx", "ensayo", scripts=scripts)
        mensaje_c, mensaje_v = (datos_c or {}).get("error", ""), (datos_v or {}).get("error", "")
        anotar(f"tipos.json {etiqueta}", "salida 2 en los dos scripts, mensaje claro",
               f"construir {codigo_c}: {mensaje_c[:110]} | verificar {codigo_v}: {mensaje_v[:60]}",
               codigo_c == 2 and codigo_v == 2 and pista in mensaje_c and pista in mensaje_v)


def probar_skill():
    texto = (SKILL_TIPOS / "SKILL.md").read_text(encoding="utf-8")
    for clave, t in DEFS["tipos"].items():
        if clave == "otro":
            continue
        hallado = re.search(rf"^### .*\(`{clave}`\)\n(.*?)(?=^### |^## |\Z)", texto, re.S | re.M)
        if not hallado:
            anotar(f"SKILL.md: {clave}", "sección del tipo", "no está", False)
            continue
        bloque = hallado.group(1)
        faltan = []
        estructuras = [tt.estructura(DEFS, clave)] + [tt.estructura(DEFS, clave, v) for v in t["variantes"]]
        for est in estructuras:
            for s in est["secciones"]:
                if s["nombre"] not in bloque:
                    faltan.append(s["nombre"])
            if f"portada {est['portada']}" not in bloque:
                faltan.append(f"portada {est['portada']}")
            if est["variante"] and f"`{est['variante']}`" not in bloque:
                faltan.append(f"variante {est['variante']}")
        anotar(f"SKILL.md: {clave}", "secciones, portada y variantes de tipos.json",
               "coherente" if not faltan else f"no menciona: {sorted(set(faltan))}", not faltan)


def main():
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("--salida", default=str(RAIZ / "pruebas" / "salida" / "caso_tipos"))
    args = analizador.parse_args()
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    probar_tipos(salida)
    probar_extras(salida)
    probar_regresion(salida)
    probar_sin_tipos(salida)
    probar_skill()
    fallos = 0
    for caso, esperado, obtenido, bien in filas:
        fallos += not bien
        print(f"[{'BIEN' if bien else 'FALLA'}] {caso}\n       esperado: {esperado}\n       obtenido: {obtenido}")
    print(f"{len(filas) - fallos}/{len(filas)} casos bien")
    (salida / "resultado.json").write_text(json.dumps(
        [dict(zip(("caso", "esperado", "obtenido", "bien"), f)) for f in filas],
        ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
