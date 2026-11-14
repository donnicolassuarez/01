#!/usr/bin/env python3
"""Prueba automática de skills/niveles-academicos/scripts/encargo.py.

Crea una raíz de trabajos en un directorio temporal (o en la carpeta
que se pase como argumento), ejercita nuevo, estado/retomar, anotar y
listar, y comprueba que el encargo.md generado lo lean bien
control_final.py y hooks/bloqueo_entrega.py. Las etapas con archivos
reales usan copias de pruebas/aceptacion/ensayo_incendios/ a las que se
quitan o alteran archivos. Imprime una tabla caso -> esperado/obtenido
y sale con 1 si algún caso falla. Solo biblioteca estándar.

Uso: python pruebas/probar_encargo.py [carpeta de trabajo]
"""

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO, "skills", "niveles-academicos", "scripts")
ENCARGO = os.path.join(SCRIPTS, "encargo.py")
CONTROL = os.path.join(SCRIPTS, "control_final.py")
HOOK = os.path.join(REPO, "hooks", "bloqueo_entrega.py")
ACEPTACION = os.path.join(REPO, "pruebas", "aceptacion", "ensayo_incendios")
DOCX = "Los_incendios_en_Pando_y_su_costo_climatico.docx"

resultados = []  # (caso, esperado, obtenido, ok)


def caso(nombre, esperado, obtenido, ok):
    resultados.append((nombre, str(esperado), str(obtenido), bool(ok)))


def correr(script, *args, json_salida=False):
    orden = [sys.executable, script] + [str(a) for a in args] + (["--json"] if json_salida else [])
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8")
    entorno.pop("ENCARGOS_RAIZ", None)
    p = subprocess.run(orden, capture_output=True, timeout=600, env=entorno)
    salida = p.stdout.decode("utf-8", "replace")
    error = p.stderr.decode("utf-8", "replace")
    datos = None
    if json_salida:
        try:
            datos = json.loads(salida)
        except ValueError:
            datos = None
    return p.returncode, salida + error, datos


def enc(raiz, *args, j=True):
    return correr(ENCARGO, *args, "--raiz", raiz, json_salida=j)


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def escribir(ruta, texto):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)


def huella(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def tocar(ruta, t):
    os.utime(ruta, (t, t))


def importar(nombre, ruta):
    if SCRIPTS not in sys.path:
        sys.path.insert(0, SCRIPTS)
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def copia(raiz, nombre, quitar=(), nivel=None):
    """Copia del encargo de aceptación con fechas en orden de etapas."""
    destino = os.path.join(raiz, "don_nico", "trabajos", "ensayos", nombre)
    shutil.copytree(ACEPTACION, destino)
    t0 = time.time() - 10000
    orden = [("fuentes", 0), ("borrador", 100), ("entrega/" + DOCX, 200),
             ("entrega/controles.json", 300), ("entrega/controles.md", 300),
             ("entrega/informe_verificacion.md", 400), ("encargo.md", 0)]
    for rel, dt in orden:
        r = os.path.join(destino, rel)
        if os.path.isdir(r):
            for n in os.listdir(r):
                tocar(os.path.join(r, n), t0 + dt)
        elif os.path.exists(r):
            tocar(r, t0 + dt)
    for rel in quitar:
        r = os.path.join(destino, rel)
        if os.path.isdir(r):
            shutil.rmtree(r)
            os.makedirs(r)
        elif os.path.exists(r):
            os.remove(r)
    if nivel:
        e = os.path.join(destino, "encargo.md")
        escribir(e, leer(e).replace("nivel: pregrado", "nivel: " + nivel))
    return destino, t0


def siguiente(datos):
    return (datos or {}).get("siguiente", {}).get("agente"), (datos or {}).get("siguiente", {}).get("accion", "")


def main():
    if len(sys.argv) > 1:
        base = os.path.abspath(sys.argv[1])
        if os.path.isdir(base):
            shutil.rmtree(base)
        os.makedirs(base)
        temporal = None
    else:
        temporal = tempfile.mkdtemp(prefix="probar_encargo_")
        base = temporal
    raiz = os.path.join(base, "raiz")
    try:
        probar(raiz)
    finally:
        if temporal:
            shutil.rmtree(temporal, ignore_errors=True)
    ancho = max(len(r[0]) for r in resultados)
    print("%-*s  %-4s  %s" % (ancho, "caso", "ok", "esperado | obtenido"))
    for nombre, esp, obt, ok in resultados:
        print("%-*s  %-4s  %s | %s" % (ancho, nombre, "sí" if ok else "NO", esp, obt))
    fallos = [r for r in resultados if not r[3]]
    print("\n%d casos, %d fallos" % (len(resultados), len(fallos)))
    return 1 if fallos else 0


def probar(raiz):
    ens = os.path.join(raiz, "don_nico", "trabajos", "ensayos")

    # ---------------------------------------------------------------- a) nuevo
    rc, txt, d = enc(raiz, "nuevo", "--tema", "Los incendios en Pando y su costo climático", "--paginas", "5")
    a1 = os.path.join(ens, "incendios_pando_costo_climatico")
    md = leer(os.path.join(a1, "encargo.md")) if os.path.isfile(os.path.join(a1, "encargo.md")) else ""
    subs = all(os.path.isdir(os.path.join(a1, s)) for s in ("fuentes", "borrador", "entrega"))
    campos_ok = all(l in md.splitlines() for l in ("tipo: ensayo", "nivel: pregrado", "formato: docx",
                                                   "estado: en curso", "paginas: 5", "para: don_nico"))
    sup = " ".join((d or {}).get("supuestos", []))
    caso("a1 nuevo por defecto", "0, carpeta+3 subcarpetas, campos por defecto",
         "%s, %s, subcarpetas %s, campos %s" % (rc, os.path.relpath((d or {}).get("carpeta", "?"), raiz), subs, campos_ok),
         rc == 0 and d and os.path.samefile(d["carpeta"], a1) and subs and campos_ok)
    caso("a1 supuestos dichos", "ensayo y pregrado en la salida", sup,
         "ensayo" in sup and "pregrado" in sup and "docx" in sup)
    caso("a1 bitácora inicial", "## Bitácora + 1 línea fechada",
         [l for l in md.splitlines() if l.startswith("- 20")],
         "## Bitácora" in md and len([l for l in md.splitlines() if re.match(r"- \d{4}-\d\d-\d\d \d\d:\d\d ", l)]) == 1)

    antes = huella(os.path.join(a1, "encargo.md"))
    rc, txt, d = enc(raiz, "nuevo", "--tema", "Los incendios en Pando y su costo climático", "--paginas", "5")
    caso("a2 carpeta existente", "2, sugiere retomar, sin tocar",
         "%s, retomar=%s, intacto=%s" % (rc, "retomar" in (d or {}).get("error", ""), huella(os.path.join(a1, "encargo.md")) == antes),
         rc == 2 and "retomar" in (d or {}).get("error", "") and huella(os.path.join(a1, "encargo.md")) == antes)

    rc, txt, d = enc(raiz, "nuevo", "--tema", "La reforma agraria de 1953 en el oriente", "--tipo", "monografia",
                     "--nivel", "maestría", "--paginas", "10-8", "--categoria", "historia de Bolivia",
                     "--carpeta", "monografia reforma", "--materia", "Historia Económica",
                     "--docente", "Lic. Pérez", "--fecha-entrega", "2026-12-01", "--formato", "docx",
                     "--con-revisor", "--nota", "Usar la Gaceta Oficial.")
    a3 = os.path.join(raiz, "don_nico", "trabajos", "historia de Bolivia", "monografia reforma")
    md3 = leer(os.path.join(a3, "encargo.md")) if os.path.isfile(os.path.join(a3, "encargo.md")) else ""
    esperadas = ("tipo: monografía", "nivel: maestría", "paginas: 8-10", "revisor: sí",
                 "categoria: historia de Bolivia", "materia: Historia Económica", "docente: Lic. Pérez",
                 "fecha_entrega: 2026-12-01", "- Usar la Gaceta Oficial.")
    faltan = [e for e in esperadas if e not in md3.splitlines()]
    caso("a3 nuevo con todas las opciones", "0, todos los campos", "%s, faltan %s" % (rc, faltan),
         rc == 0 and not faltan)

    rc, txt, d = enc(raiz, "nuevo", "--tema", "¿Qué pasó con la «Reforma» agraria? Ñandutí, señoríos & café (1953–2026)!")
    nombre = os.path.basename((d or {}).get("carpeta", ""))
    caso("a4 slug con tildes, eñes y signos", "ASCII [a-z0-9_], sin vacías", nombre,
         rc == 1 and re.fullmatch(r"[a-z0-9_]+", nombre) and "nanduti" in nombre and "senorios" in nombre
         and not nombre.startswith("que_") and len(nombre) <= 50)
    caso("a4b sin extensión avisa", "código 1 y aviso", "%s %s" % (rc, (d or {}).get("avisos")),
         rc == 1 and any("extensi" in a for a in (d or {}).get("avisos", [])))

    rc, txt, d = enc(raiz, "nuevo", "--tema", "Perfil de proyecto de turismo", "--tipo", "perfil", "--para", "jota",
                     "--paginas", "12")
    caso("a5 --para jota", "raiz/jota/trabajos/perfiles/...", os.path.relpath((d or {}).get("carpeta", "?"), raiz),
         rc == 0 and os.path.relpath(d["carpeta"], raiz).split(os.sep)[:3] == ["jota", "trabajos", "perfiles"]
         and "para: jota" in leer(os.path.join(d["carpeta"], "encargo.md")))

    malos = [("--tipo", "novela"), ("--nivel", "secundaria"), ("--paginas", "cinco"), ("--fecha-entrega", "1/12/2026")]
    rcs = [enc(raiz, "nuevo", "--tema", "Tema de prueba inválido", k, v)[0] for k, v in malos]
    caso("a6 valores inválidos", "2 en los cuatro", rcs, rcs == [2, 2, 2, 2]
         and not os.path.exists(os.path.join(ens, "tema_prueba_invalido")))

    # ------------------------------------------------- b) lo leen control_final y el hook
    cf = importar("control_final", CONTROL)
    from pathlib import Path
    datos1, avisos1 = cf.leer_encargo(Path(a1))
    datos3, avisos3 = cf.leer_encargo(Path(a3))
    caso("b1 control_final.leer_encargo (defecto)", "pregrado/ensayo/5-5/en curso, sin avisos",
         "%s/%s/%s-%s/%s %s" % (datos1["nivel"], datos1["tipo"], datos1["min"], datos1["max"], datos1["estado"], avisos1),
         (datos1["nivel"], datos1["tipo"], datos1["min"], datos1["max"], datos1["estado"]) == ("pregrado", "ensayo", 5, 5, "en curso") and not avisos1)
    caso("b2 control_final.leer_encargo (opciones)", "maestria/monografia/8-10, sin avisos",
         "%s/%s/%s-%s %s" % (datos3["nivel"], datos3["tipo"], datos3["min"], datos3["max"], avisos3),
         (datos3["nivel"], datos3["tipo"], datos3["min"], datos3["max"]) == ("maestria", "monografia", 8, 10) and not avisos3)

    # control_final.py ejecutado de verdad sobre un encargo creado por nuevo + el docx de aceptación
    rc, txt, d = enc(raiz, "nuevo", "--tema", "Control final sobre encargo nuevo", "--paginas", "5")
    b3 = d["carpeta"]
    shutil.copy2(os.path.join(ACEPTACION, "entrega", DOCX), os.path.join(b3, "entrega", DOCX))
    rc, txt, dcf = correr(CONTROL, b3, "--sin-red", json_salida=True)
    resumen_md = leer(os.path.join(b3, "entrega", "controles.md")) if os.path.isfile(os.path.join(b3, "entrega", "controles.md")) else ""
    linea = next((l for l in resumen_md.splitlines() if l.startswith("- Encargo:")), "")
    av = [a for a in (dcf or {}).get("avisos", []) if "encargo.md" in a]
    caso("b3 control_final.py ejecutado", "Encargo: pregrado; ensayo; 5; «en curso», sin avisos de encargo.md",
         "%s | avisos %s" % (linea, av),
         "nivel pregrado" in linea and "tipo ensayo" in linea and "páginas 5" in linea and "en curso" in linea and not av)
    shutil.rmtree(b3)

    rc, txt, _ = correr(HOOK, "--comprobar", a1)
    caso("b4 hook --comprobar sin entregables", "0, PASA, lee estado en curso", "%s %s" % (rc, "PASA" in txt),
         rc == 0 and "PASA" in txt and "estado: en curso" in txt)

    hook = importar("bloqueo_entrega", HOOK)
    encm = importar("encargo", ENCARGO)
    muestras = ["# I\n\n## Dictamen\n\n**APROBADO**\n", "**Dictamen: NO APROBADO**\n",
                "Dictamen: NO APROBADO\n\n## Segunda vuelta\n\nDictamen: APROBADO\n",
                "Dictamen: APROBADO\n\nDictamen: No aprobado\n", "Sin veredicto\n", "## Resultado\n\nNO APROBADO\n",
                leer(os.path.join(ACEPTACION, "entrega", "informe_verificacion.md"))]
    tmp = os.path.join(raiz, "muestra_informe.md")
    iguales = []
    for m in muestras:
        escribir(tmp, m)
        iguales.append(hook.leer_dictamen(tmp) == encm.leer_dictamen(tmp))
    os.remove(tmp)
    caso("b5 dictamen igual que el hook", "7/7 iguales", "%d/7" % sum(iguales), all(iguales))

    # ----------------------------------------------------------- c) estado por etapa
    rc, txt, d = enc(raiz, "estado", a1)
    caso("c1 recién creado", "investigador", siguiente(d)[0], rc == 0 and siguiente(d)[0] == "investigador")

    rc, txt, d = enc(raiz, "retomar", "incendios_pando")  # parte del nombre
    caso("c1b retomar por parte del nombre", "0, investigador", "%s %s" % (rc, siguiente(d)[0]),
         rc == 0 and siguiente(d)[0] == "investigador")

    c2, _ = copia(raiz, "etapa_redaccion", quitar=("borrador", "entrega"))
    rc, txt, d = enc(raiz, "estado", c2)
    inv = (d or {}).get("etapas", {}).get("investigacion", {})
    caso("c2 con fichas y matriz", "redactor; 7 fichas", "%s; %s fichas" % (siguiente(d)[0], inv.get("fichas")),
         siguiente(d)[0] == "redactor" and inv.get("fichas") == 7 and inv.get("hecha"))
    caso("c2b tolera encargo.md antiguo", "aviso de formato antiguo",
         [a for a in (d or {}).get("avisos", []) if "antiguo" in a],
         any("antiguo" in a for a in (d or {}).get("avisos", [])))

    c2c, _ = copia(raiz, "fichas_vacias", quitar=("borrador", "entrega"))
    escribir(os.path.join(c2c, "fuentes", "fichas.md"), "# Fichas de lectura\n\n")
    rc, txt, d = enc(raiz, "estado", c2c)
    caso("c2c fichas.md solo con título", "investigador", siguiente(d)[0], siguiente(d)[0] == "investigador")

    c3, _ = copia(raiz, "etapa_produccion", quitar=("entrega",))
    rc, txt, d = enc(raiz, "estado", c3)
    caso("c3 texto.md, pregrado", "productor", "%s (%s palabras)" % (siguiente(d)[0], d["etapas"]["redaccion"]["palabras"]),
         siguiente(d)[0] == "productor" and d["etapas"]["redaccion"]["palabras"] > 1000)

    c4, t0 = copia(raiz, "etapa_revision", quitar=("entrega",), nivel="maestría")
    rc, txt, d = enc(raiz, "estado", c4)
    caso("c4 texto.md, maestría", "revisor", siguiente(d)[0], siguiente(d)[0] == "revisor")
    rev = os.path.join(c4, "borrador", "informe_revision.md")
    escribir(rev, "# Informe de revisión\n\n**Dictamen:** cambios mayores\n\nObservaciones...\n")
    tocar(rev, t0 + 150)
    rc, txt, d = enc(raiz, "estado", c4)
    caso("c4b revisión con cambios mayores", "redactor, vuelta 1", "%s / %s" % siguiente(d),
         siguiente(d)[0] == "redactor" and "vuelta 1 de 3" in siguiente(d)[1])
    tocar(os.path.join(c4, "borrador", "texto.md"), t0 + 180)
    rc, txt, d = enc(raiz, "estado", c4)
    caso("c4c texto corregido tras la revisión", "revisor", siguiente(d)[0], siguiente(d)[0] == "revisor")
    escribir(rev, "# Informe de revisión\n\n## Dictamen\n\nAceptar\n")
    tocar(rev, t0 + 190)
    rc, txt, d = enc(raiz, "estado", c4)
    caso("c4d revisión aceptada", "productor", siguiente(d)[0], siguiente(d)[0] == "productor")

    c5, _ = copia(raiz, "docx_sin_controles", quitar=("entrega/controles.json", "entrega/controles.md",
                                                      "entrega/informe_verificacion.md"))
    rc, txt, d = enc(raiz, "estado", c5)
    caso("c5 docx sin controles", "productor: control_final", "%s / %s" % siguiente(d),
         siguiente(d)[0] == "productor" and "control_final" in siguiente(d)[1])

    c6, _ = copia(raiz, "sin_informe", quitar=("entrega/informe_verificacion.md",))
    e6 = os.path.join(c6, "encargo.md")
    escribir(e6, leer(e6).replace("estado: aprobado", "estado: en verificación"))
    rc, txt, d = enc(raiz, "estado", c6)
    caso("c6 controles aprobados, sin informe", "verificador", siguiente(d)[0],
         rc == 0 and siguiente(d)[0] == "verificador")

    c7, t0 = copia(raiz, "no_aprobado", quitar=())
    e7 = os.path.join(c7, "encargo.md")
    escribir(e7, leer(e7).replace("estado: aprobado", "estado: en verificación"))
    inf = os.path.join(c7, "entrega", "informe_verificacion.md")
    escribir(inf, "**Dictamen: NO APROBADO**\n\n## Errores materiales\n\n1. Cita sin respaldo.\n")
    tocar(inf, t0 + 400)
    rc, txt, d = enc(raiz, "estado", c7)
    caso("c7 informe NO APROBADO", "redactor o productor, vuelta 1 de 3", "%s / vueltas %s" % (siguiente(d)[0], d.get("vueltas")),
         siguiente(d)[0] == "redactor o productor" and "vuelta 1 de 3" in siguiente(d)[1])
    for i in range(3):
        enc(raiz, "anotar", c7, "verificador NO APROBADO; vuelve al redactor", "--vuelta")
    rc, txt, d = enc(raiz, "estado", c7)
    caso("c7b NO APROBADO tras 3 vueltas", "director: no aprobado; aviso de máximo",
         "%s / vueltas %s / %s" % (siguiente(d)[0], d.get("vueltas"), [a for a in d.get("avisos", []) if "máximo" in a]),
         d.get("vueltas") == 3 and siguiente(d)[0] == "director" and "no aprobado" in siguiente(d)[1]
         and any("máximo" in a for a in d.get("avisos", [])))
    rc, txt, d = enc(raiz, "anotar", c7, "otra vuelta", "--vuelta")
    caso("c7c cuarta vuelta", "rechazada (1)", rc, rc == 1)

    c8, _ = copia(raiz, "completo")
    rc, txt, d = enc(raiz, "estado", c8)
    caso("c8 todo en regla, aprobado", "0, cerrado, sin incoherencias", "%s %s %s" % (rc, siguiente(d)[0], d.get("incoherencias")),
         rc == 0 and siguiente(d)[0] == "cerrado" and not d.get("incoherencias"))
    rc_txt, txt, _ = enc(raiz, "estado", c8, j=False)
    caso("c8b salida en texto", "termina en SIGUIENTE PASO: cerrado", txt.strip().splitlines()[-1][:40],
         txt.strip().splitlines()[-1].startswith("SIGUIENTE PASO: cerrado"))

    c9, t0 = copia(raiz, "docx_modificado")
    docx9 = os.path.join(c9, "entrega", DOCX)
    with zipfile.ZipFile(docx9, "a") as z:
        z.writestr("customXml/extra.xml", "<x/>")
    tocar(docx9, t0 + 500)
    rc, txt, d = enc(raiz, "estado", c9)
    inc = " ".join(d.get("incoherencias", []))
    caso("c9 docx modificado tras los controles", "1, huella + informe anterior + aprobado sin respaldo; productor",
         "%s %s | %s" % (rc, siguiente(d)[0], inc[:90]),
         rc == 1 and "huella" in inc and "anterior al docx" in inc and "dice «aprobado»" in inc
         and siguiente(d)[0] == "productor")

    c10, t0 = copia(raiz, "texto_nuevo")
    tx = os.path.join(c10, "borrador", "texto.md")
    escribir(tx, leer(tx).replace("# Conclusiones", "Un párrafo nuevo que no está en el docx.\n\n# Conclusiones"))
    tocar(tx, t0 + 600)
    rc, txt, d = enc(raiz, "estado", c10)
    caso("c10 texto.md más nuevo y distinto", "1, reconstruir; productor",
         "%s %s %s" % (rc, siguiente(d)[0], d.get("incoherencias", [""])[0][:60]),
         rc == 1 and siguiente(d)[0] == "productor" and "reconstruir" in " ".join(d.get("incoherencias", [])))
    c10b, t0 = copia(raiz, "texto_tocado")
    tocar(os.path.join(c10b, "borrador", "texto.md"), t0 + 600)
    rc, txt, d = enc(raiz, "estado", c10b)
    caso("c10b texto.md más nuevo, mismo contenido", "0, cerrado", "%s %s" % (rc, siguiente(d)[0]),
         rc == 0 and siguiente(d)[0] == "cerrado")

    c11, _ = copia(raiz, "aprobado_sin_informe", quitar=("entrega/informe_verificacion.md",))
    rc, txt, d = enc(raiz, "estado", c11)
    caso("c11 «aprobado» sin informe", "1, incoherencia, verificador",
         "%s %s" % (rc, siguiente(d)[0]),
         rc == 1 and any("dice «aprobado»" in i for i in d.get("incoherencias", [])) and siguiente(d)[0] == "verificador")

    # ------------------------------------------------------------------ d) anotar
    rc, txt, d = enc(raiz, "anotar", a1, "investigador: 7 fuentes leídas y fichadas")
    lineas = [l for l in leer(os.path.join(a1, "encargo.md")).splitlines() if l.startswith("- 20")]
    caso("d1 anotar añade línea", "0, 2 líneas, la última con el texto", "%s, %d líneas" % (rc, len(lineas)),
         rc == 0 and len(lineas) == 2 and lineas[-1].endswith("investigador: 7 fuentes leídas y fichadas"))

    antes = huella(os.path.join(a1, "encargo.md"))
    rc, txt, d = enc(raiz, "anotar", a1, "algo", "--estado", "terminado")
    caso("d2 estado inválido", "2, sin escribir", "%s %s" % (rc, huella(os.path.join(a1, "encargo.md")) == antes),
         rc == 2 and huella(os.path.join(a1, "encargo.md")) == antes)

    antes = huella(e6)
    rc, txt, d = enc(raiz, "anotar", c6, "cierre", "--estado", "aprobado")
    caso("d3 aprobado sin informe", "1, rechazado, sin escribir", "%s %s" % (rc, (d or {}).get("faltas")),
         rc == 1 and d.get("rechazado") and huella(e6) == antes)
    rc, txt, d = enc(raiz, "anotar", a1, "cierre", "--estado", "aprobado")
    caso("d3b aprobado recién creado", "1, rechazado", rc, rc == 1)
    rc, txt, d = enc(raiz, "anotar", c9, "cierre", "--estado", "aprobado")
    caso("d3c aprobado con huella vencida", "1, rechazado", "%s %s" % (rc, (d or {}).get("faltas")),
         rc == 1 and any("huella" in f for f in d.get("faltas", [])))

    d4, _ = copia(raiz, "cierre_valido")
    e4 = os.path.join(d4, "encargo.md")
    escribir(e4, leer(e4).replace("estado: aprobado", "estado: en verificación"))
    rc, txt, d = enc(raiz, "estado", d4)
    caso("c12 en regla pero sin cerrar", "director: cierre", "%s / %s" % (siguiente(d)[0], d.get("etapa")),
         rc == 0 and siguiente(d)[0] == "director" and d.get("etapa") == "cierre")
    rc, txt, d = enc(raiz, "anotar", d4, "verificador APROBADO; 18/18 citas", "--estado", "aprobado")
    rc_h, txt_h, _ = correr(HOOK, "--comprobar", d4)
    md4 = leer(e4)
    caso("d4 aprobado con respaldo (aceptación)", "0, hook lee aprobado y PASA, bitácora creada",
         "%s, hook %s, bitácora %s" % (rc, rc_h, "## Bitácora" in md4),
         rc == 0 and rc_h == 0 and "estado: aprobado" in txt_h and "## Bitácora" in md4
         and "estado: aprobado" in md4.splitlines())
    rc, txt, d = enc(raiz, "estado", d4)
    caso("d4b estado tras cerrar", "cerrado", siguiente(d)[0], siguiente(d)[0] == "cerrado")

    rc, txt, d = enc(raiz, "nuevo", "--tema", "Estado con negritas", "--paginas", "3")
    d5 = d["carpeta"]
    e5 = os.path.join(d5, "encargo.md")
    escribir(e5, leer(e5).replace("estado: en curso", "- **Estado:** en curso"))
    rc, txt, d = enc(raiz, "anotar", d5, "producido", "--estado", "en verificacion")
    rc_h, txt_h, _ = correr(HOOK, "--comprobar", d5)
    caso("d5 cambia estado con formato **Estado:**", "0; hook lee «en verificacion»",
         "%s; %s" % (rc, next((l.strip() for l in txt_h.splitlines() if "estado:" in l), "")),
         rc == 0 and "estado: en verificacion" in txt_h and "- **Estado:** en verificación" in leer(e5))
    parciales = [n for n in os.listdir(d5) if n.endswith(".parcial")]
    caso("d6 escritura atómica sin restos", "sin .parcial", parciales, not parciales)

    # ------------------------------------------------------------------ e) listar
    rc, txt, d = enc(raiz, "anotar", c11, "suspendido por el usuario", "--estado", "suspendido")
    rc, txt, d = enc(raiz, "anotar", c7, "tres vueltas sin aprobar", "--estado", "no aprobado")
    rc, txt, d = enc(raiz, "listar")
    filas = (d or {}).get("encargos", [])
    estados = [plano(f["estado"]) for f in filas]
    primer_cerrado = next((i for i, f in enumerate(filas) if not f["abierto"]), len(filas))
    abiertos_primero = all(not f["abierto"] for f in filas[primer_cerrado:])
    caso("e1 listar todos", "0, varios estados, abiertos primero",
         "%s, %d encargos, estados %s" % (rc, len(filas), sorted(set(estados))),
         rc == 0 and len(filas) >= 10 and abiertos_primero
         and {"en curso", "en verificacion", "aprobado", "no aprobado", "suspendido"} <= set(estados))
    caso("e1b última línea de bitácora", "presente en los nuevos",
         next((f["ultima"] for f in filas if f["nombre"] == "incendios_pando_costo_climatico"), None),
         next((f["ultima"] for f in filas if f["nombre"] == "incendios_pando_costo_climatico"), "").endswith("fichadas"))
    rc, txt, d = enc(raiz, "listar", "--para", "jota")
    caso("e2 listar --para jota", "solo jota (1)", [f["para"] for f in d["encargos"]],
         rc == 0 and [f["para"] for f in d["encargos"]] == ["jota"])
    rc, txt, d = enc(raiz, "listar", "--estado", "aprobado")
    caso("e3 listar --estado aprobado", "solo aprobados", [f["nombre"] for f in d["encargos"]],
         rc == 0 and d["encargos"] and all(plano(f["estado"]) == "aprobado" for f in d["encargos"]))
    rc, txt, _ = enc(raiz, "listar", j=False)
    caso("e4 listar en texto", "0, una línea por encargo", "%s, %d líneas «- [»" % (rc, txt.count("\n- [")),
         rc == 0 and txt.count("\n- [") == len(filas))
    rc, txt, d = enc(raiz, "listar", "--estado", "cualquiera")
    caso("e5 listar con estado inválido", "2", rc, rc == 2)


def plano(texto):
    import unicodedata
    d = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in d if not unicodedata.combining(c)).lower().strip()


if __name__ == "__main__":
    sys.exit(main())
