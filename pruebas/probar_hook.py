#!/usr/bin/env python3
"""Prueba automática de hooks/bloqueo_entrega.py.

Crea encargos de juguete en un directorio temporal, lanza el hook como
subproceso con el JSON del evento Stop por stdin y compara la decisión
(pasa / bloquea) con la esperada. Imprime una tabla y sale con 1 si
algún caso falla. Solo biblioteca estándar.

Uso: python pruebas/probar_hook.py
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(RAIZ, "hooks", "bloqueo_entrega.py")
TIEMPO_MAX = 30  # segundos por caso

INFORME_OK = "# Informe de verificación\n\n## Dictamen\n\n**APROBADO**\n\nCitas revisadas: 10/10\n"
INFORME_NO = "# Informe de verificación\n\n## Dictamen\n\n**NO APROBADO**\n\nErrores materiales: cita sin fuente.\n"
INFORME_DOS = ("# Informe\n\nDictamen: NO APROBADO\n\n## Segunda vuelta\n\n"
               "Dictamen: APROBADO\n")
INFORME_DOS_AL_REVES = ("# Informe\n\nDictamen: APROBADO\n\n## Revisión posterior\n\n"
                        "Dictamen: No aprobado\n")


def escribir(ruta, contenido, modo="w"):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    if modo == "wb":
        with open(ruta, "wb") as f:
            f.write(contenido)
    else:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)


def tocar(ruta, segundos):
    os.utime(ruta, (segundos, segundos))


def crear_encargo(base, nombre, estado="en verificación", docx=True, informe=None,
                  controles="ok", huella_falsa=False, informe_viejo=False):
    """Crea una carpeta de encargo. Devuelve su ruta."""
    carpeta = os.path.join(base, nombre)
    escribir(os.path.join(carpeta, "encargo.md"),
             "# Encargo\n\ntema: prueba\nnivel: pregrado\n**Estado:** %s\n" % estado)
    os.makedirs(os.path.join(carpeta, "fuentes"), exist_ok=True)
    entrega = os.path.join(carpeta, "entrega")
    os.makedirs(entrega, exist_ok=True)
    ahora = time.time()
    if not docx:
        return carpeta
    doc = os.path.join(entrega, "monografia.docx")
    escribir(doc, b"PK\x03\x04 contenido de prueba", "wb")
    tocar(doc, ahora - 100)
    escribir(os.path.join(entrega, "~$nografia.docx"), b"temporal de Word", "wb")
    if controles is not None:
        huella = hashlib.sha256(b"PK\x03\x04 contenido de prueba").hexdigest()
        datos = {
            "archivo": "monografia.docx",
            "sha256": ("0" * 64) if huella_falsa else huella,
            "fecha": "2026-11-11T10:00:00-04:00",
            "aprobado_mecanico": controles == "ok",
            "controles": {
                "cruzar_citas": {"codigo": 0, "resumen": "sin hallazgos"},
                "verificar_formato": {"codigo": 0 if controles == "ok" else 1,
                                      "resumen": "ok" if controles == "ok" else "interlineado"},
            },
        }
        escribir(os.path.join(entrega, "controles.json"), json.dumps(datos, ensure_ascii=False))
    if informe is not None:
        inf = os.path.join(entrega, "informe_verificacion.md")
        escribir(inf, informe)
        tocar(inf, ahora - 500 if informe_viejo else ahora - 50)
    return carpeta


def transcripcion(base, nombre, textos):
    """Escribe un JSONL con mensajes que contienen `textos`, más una línea corrupta."""
    ruta = os.path.join(base, nombre)
    os.makedirs(base, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "user", "message": {"role": "user", "content": "hola"}}) + "\n")
        f.write('{"type": "assistant", "message": {"content": "línea cortada C:\\\\x\n')
        for t in textos:
            linea = {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Bash", "input": {"command": t}}]}}
            f.write(json.dumps(linea, ensure_ascii=False) + "\n")
    return ruta


def ruta_windows(ruta):
    """La misma ruta escrita con barras invertidas (en Windows es la ruta nativa)."""
    return ruta.replace("/", "\\")


def lanzar(entrada, args=None):
    """Ejecuta el hook. Devuelve (decisión, detalle)."""
    cmd = [sys.executable, HOOK] + (args or [])
    if isinstance(entrada, dict):
        entrada = json.dumps(entrada).encode("utf-8")
    try:
        p = subprocess.run(cmd, input=entrada, capture_output=True, timeout=TIEMPO_MAX)
    except subprocess.TimeoutExpired:
        return "colgado", "superó %d s" % TIEMPO_MAX
    out = p.stdout.decode("utf-8", errors="replace").strip()
    err = p.stderr.decode("utf-8", errors="replace").strip()
    if args:  # modo --comprobar
        return ("bloquea" if p.returncode == 1 else "pasa" if p.returncode == 0
                else "código %d" % p.returncode), out or err
    if p.returncode != 0:
        return "código %d" % p.returncode, err
    if not out:
        return "pasa", err
    try:
        datos = json.loads(out)
    except ValueError:
        return "salida inválida", out
    if datos.get("decision") == "block" and datos.get("reason"):
        return "bloquea", datos["reason"]
    return "salida inesperada", out


def evento(cwd, transcript, activo=False):
    return {"session_id": "prueba", "transcript_path": transcript, "cwd": cwd,
            "permission_mode": "default", "hook_event_name": "Stop",
            "stop_hook_active": activo, "last_assistant_message": "Listo."}


def main():
    base = tempfile.mkdtemp(prefix="probar_hook_")
    casos = []  # (nombre, esperado, obtenido, detalle, debe_contener)
    try:
        ajeno = os.path.join(base, "ajeno")
        os.makedirs(ajeno)
        vacia = transcripcion(base, "vacia.jsonl", [])

        def caso(nombre, esperado, entrada, contiene=None, args=None):
            obtenido, detalle = lanzar(entrada, args)
            ok = obtenido == esperado and (contiene is None or contiene in detalle)
            casos.append((nombre, esperado, obtenido, ok, detalle))

        caso("sin encargo", "pasa", evento(ajeno, vacia))

        c = crear_encargo(base, "e01_sin_entregables", docx=False)
        caso("encargo sin entregables", "pasa", evento(c, vacia))

        c = crear_encargo(base, "e02_sin_informe", controles=None)
        caso("entregable sin informe", "bloquea", evento(c, vacia), "falta entrega/informe_verificacion.md")

        c = crear_encargo(base, "e03_no_aprobado", informe=INFORME_NO)
        caso("informe NO APROBADO", "bloquea", evento(c, vacia), "NO APROBADO")

        c = crear_encargo(base, "e04_dos_dictamenes_ultimo_no", informe=INFORME_DOS_AL_REVES)
        caso("dos dictámenes, el último 'No aprobado'", "bloquea", evento(c, vacia), "NO APROBADO")

        c = crear_encargo(base, "e05_sin_controles", informe=INFORME_OK, controles=None)
        caso("APROBADO sin controles.json", "bloquea", evento(c, vacia), "falta entrega/controles.json")

        c = crear_encargo(base, "e06_mecanico_falso", informe=INFORME_OK, controles="mal")
        caso("aprobado_mecanico false", "bloquea", evento(c, vacia), "verificar_formato")

        c = crear_encargo(base, "e07_huella", informe=INFORME_OK)
        doc = os.path.join(c, "entrega", "monografia.docx")
        escribir(doc, b"PK\x03\x04 contenido MODIFICADO", "wb")
        tocar(doc, time.time() - 100)  # mismo orden de fechas: solo cambia la huella
        caso("docx modificado después (huella)", "bloquea", evento(c, vacia), "cambió después de los controles")

        c = crear_encargo(base, "e08_informe_viejo", informe=INFORME_OK, informe_viejo=True)
        caso("informe más viejo que el entregable", "bloquea", evento(c, vacia), "anterior al entregable")

        c_ok = crear_encargo(base, "e09_en_regla", informe=INFORME_OK)
        caso("todo en regla", "pasa", evento(c_ok, vacia))

        c = crear_encargo(base, "e10_dos_dictamenes_ultimo_si", informe=INFORME_DOS)
        caso("dos dictámenes, el último APROBADO", "pasa", evento(c, vacia))

        c = crear_encargo(base, "e11_estado_no_aprobado", estado="No aprobado", informe=INFORME_NO)
        caso("estado 'no aprobado' con entregable", "pasa", evento(c, vacia))

        c = crear_encargo(base, "e12_suspendido", estado="suspendido", controles=None)
        caso("estado 'suspendido' con entregable", "pasa", evento(c, vacia))

        c_mal = crear_encargo(base, "e13_activo", controles=None)
        caso("stop_hook_active true", "pasa", evento(c_mal, vacia, activo=True))

        # El cwd es una subcarpeta del encargo: se sube hasta encargo.md.
        caso("cwd dentro de fuentes/ del encargo", "bloquea",
             evento(os.path.join(c_mal, "fuentes"), vacia), "e13_activo")

        # Encargos hallados solo por la transcripción (cwd ajeno).
        c_win = crear_encargo(base, "e14 con espacios win", controles=None)
        t = transcripcion(base, "win.jsonl", [
            'type "%s"' % ruta_windows(os.path.join(c_win, "encargo.md"))])
        caso("transcripción: ruta Windows escapada", "bloquea", evento(ajeno, t), "e14 con espacios win")

        c_posix = crear_encargo(base, "e15_posix", controles=None)
        t = transcripcion(base, "posix.jsonl", [
            "python construir_docx.py --salida %s/entrega/monografia.docx" % c_posix])
        caso("transcripción: ruta POSIX con /entrega/", "bloquea", evento(ajeno, t), "e15_posix")

        t = transcripcion(base, "regla.jsonl", [
            "cat %s" % ruta_windows(os.path.join(c_ok, "encargo.md")),
            "ls %s/entrega/" % c_ok])
        caso("transcripción: encargo en regla", "pasa", evento(ajeno, t))

        c_sub = crear_encargo(base, "e16_subagente", controles=None)
        t = transcripcion(base, "sesion16.jsonl", [])
        transcripcion(os.path.join(base, "sesion16", "subagents"), "agent-1.jsonl",
                      ["ls %s/entrega/" % c_sub])
        caso("transcripción de subagente", "bloquea", evento(ajeno, t), "e16_subagente")

        caso("stdin basura", "pasa", b"\x00\xffesto no es JSON {{{")
        caso("stdin vacío", "pasa", b"")
        caso("transcripción inexistente", "pasa",
             evento(ajeno, os.path.join(base, "no_existe.jsonl")))

        caso("--comprobar encargo en regla", "pasa", None, "PASA", ["--comprobar", c_ok])
        caso("--comprobar encargo sin informe", "bloquea", None, "BLOQUEAR",
             ["--comprobar", os.path.join(base, "e02_sin_informe")])
    finally:
        shutil.rmtree(base, ignore_errors=True)

    ancho = max(len(c[0]) for c in casos)
    print("%-*s  %-8s  %-8s  %s" % (ancho, "caso", "esperado", "obtenido", "resultado"))
    print("-" * (ancho + 32))
    fallos = 0
    for nombre, esperado, obtenido, ok, detalle in casos:
        print("%-*s  %-8s  %-8s  %s" % (ancho, nombre, esperado, obtenido, "ok" if ok else "FALLA"))
        if not ok:
            fallos += 1
            print("    detalle: " + detalle.replace("\n", "\n    "))
    print("-" * (ancho + 32))
    print("%d casos, %d fallos" % (len(casos), fallos))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
