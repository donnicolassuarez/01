# -*- coding: utf-8 -*-
"""Casos negativos para verificar_formato.py.

Parte del ensayo de prueba construido (correcto) y crea una variante por
defecto sembrado, cada una con un solo defecto. Con --comprobar ejecuta
verificar_formato.py sobre cada variante y comprueba que:
  1. el defecto se detecta como ERROR en la comprobación esperada;
  2. el lugar informado contiene el párrafo donde se sembró;
  3. no aparece ningún ERROR en otras comprobaciones.

Uso:
  python pruebas/crear_docx_defectuosos.py [base.docx] [--salida carpeta] [--comprobar]

Por defecto: base pruebas/salida/caso_docx/ensayo_prueba.docx (generarla
antes con construir_docx.py desde pruebas/casos/ensayo_prueba.md) y
salida pruebas/salida/caso_docx/defectuosos/.
Código de salida: 0 si todo se detecta bien, 1 si algo falla, 2 si no
se pudo ejecutar.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

RAIZ = Path(__file__).resolve().parent.parent
VERIFICADOR = RAIZ / "skills" / "niveles-academicos" / "scripts" / "verificar_formato.py"


def parrafo_que_empieza(documento, inicio):
    for parrafo in documento.paragraphs:
        if parrafo.text.startswith(inicio):
            return parrafo
    raise LookupError(f"no hay párrafo que empiece por «{inicio}»")


def fuente_arial(documento):
    parrafo = parrafo_que_empieza(documento, "Walter Ong (1982)")
    for run in parrafo.runs:
        run.font.name = "Arial"
        fuentes = run._r.rPr.find(qn("w:rFonts"))
        fuentes.set(qn("w:cs"), "Arial")
        fuentes.set(qn("w:eastAsia"), "Arial")
    return "Walter Ong (1982)"


def tamano_a4(documento):
    for seccion in documento.sections:
        seccion.page_width = Cm(21.0)
        seccion.page_height = Cm(29.7)
    return None


def titulo_falso(documento):
    parrafo = parrafo_que_empieza(documento, "La pantalla y la atención dividida")
    parrafo.style = documento.styles["Normal"]
    for run in parrafo.runs:
        run.bold = True
    return "La pantalla y la atención dividida"


def espaciado_titulo(documento):
    parrafo = parrafo_que_empieza(documento, "La imprenta y el lector silencioso")
    parrafo.paragraph_format.space_before = Pt(30)
    return "La imprenta y el lector silencioso"


def salto_escondido(documento):
    parrafo = parrafo_que_empieza(documento, "La parodia funciona")
    parrafo.runs[-1].add_break(WD_BREAK.PAGE)
    return "La parodia funciona"


def marcador_cita(documento):
    parrafo = parrafo_que_empieza(documento, "Maryanne Wolf (2007)")
    parrafo.runs[-1].text += " [cita]"
    return "Maryanne Wolf (2007)"


def por_verificar(documento):
    parrafo = parrafo_que_empieza(documento, "Nicholas Carr (2010)")
    parrafo.runs[-1].text += " (POR VERIFICAR)"
    return "Nicholas Carr (2010)"


def resto_markdown(documento):
    parrafo = parrafo_que_empieza(documento, "Ninguna de estas condiciones")
    run = parrafo.runs[0]
    run.text = run.text.replace("condiciones", "**condiciones**", 1)
    return "Ninguna de estas"


def referencias_mal(documento):
    referencias = [p for p in documento.paragraphs if p.style.name == "Referencia"]
    for parrafo in referencias:
        parrafo.paragraph_format.first_line_indent = Cm(0)
        parrafo.paragraph_format.left_indent = Cm(0)
    # Invertir el orden: Wolf, Ong, Eisenstein, Cervantes, Carr.
    ancla = referencias[0]._p.getprevious()
    for parrafo in referencias:
        ancla.addnext(parrafo._p)
    return "Carr, N. (2010)"


# nombre: (función, comprobaciones donde el ERROR es esperable)
CASOS = {
    "fuente_arial": (fuente_arial, {"c"}),
    "tamano_a4": (tamano_a4, {"b", "n"}),
    "titulo_falso": (titulo_falso, {"f"}),
    "espaciado_titulo": (espaciado_titulo, {"g"}),
    "salto_escondido": (salto_escondido, {"h"}),
    "marcador_cita": (marcador_cita, {"j"}),
    "por_verificar": (por_verificar, {"j"}),
    "resto_markdown": (resto_markdown, {"m"}),
    "referencias_mal": (referencias_mal, {"l"}),
}


def comprobar(ruta, esperadas, lugar):
    resultado = subprocess.run([sys.executable, str(VERIFICADOR), str(ruta), "--tipo", "ensayo",
                                "--json"], capture_output=True, text=True, encoding="utf-8")
    if resultado.returncode == 2:
        return False, f"el verificador no pudo ejecutar: {resultado.stdout}{resultado.stderr}"
    datos = json.loads(resultado.stdout)
    errores = [h for h in datos["hallazgos"] if h["nivel"] == "ERROR"]
    propios = [h for h in errores if h["comprobacion"] in esperadas]
    ajenos = [h for h in errores if h["comprobacion"] not in esperadas]
    problemas = []
    if resultado.returncode != 1:
        problemas.append(f"código {resultado.returncode}, se esperaba 1")
    if not propios:
        problemas.append(f"no detectado en {sorted(esperadas)}")
    if lugar and propios and not any(lugar in l for h in propios for l in h["lugares"]):
        problemas.append(f"lugar incorrecto: se esperaba «{lugar}»")
    for hallazgo in ajenos:
        problemas.append(f"ERROR ajeno: {hallazgo['comprobacion']}) {hallazgo['mensaje']} "
                         f"{hallazgo['lugares'][:2]}")
    detalle = "; ".join(f"{h['comprobacion']}) {h['mensaje']} {h['lugares'][:2]}" for h in propios)
    return not problemas, ("; ".join(problemas) if problemas else detalle)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    analizador = argparse.ArgumentParser(description="Casos negativos de formato")
    analizador.add_argument("base", nargs="?",
                            default=str(RAIZ / "pruebas" / "salida" / "caso_docx" / "ensayo_prueba.docx"))
    analizador.add_argument("--salida",
                            default=str(RAIZ / "pruebas" / "salida" / "caso_docx" / "defectuosos"))
    analizador.add_argument("--comprobar", action="store_true")
    args = analizador.parse_args()
    base = Path(args.base)
    if not base.is_file():
        print(f"No existe {base}: constrúyelo antes con construir_docx.py", file=sys.stderr)
        sys.exit(2)
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    fallos = 0
    for nombre, (funcion, esperadas) in CASOS.items():
        documento = Document(str(base))
        lugar = funcion(documento)
        ruta = salida / f"{nombre}.docx"
        documento.save(str(ruta))
        if not args.comprobar:
            print(f"creado {ruta}")
            continue
        bien, detalle = comprobar(ruta, esperadas, lugar)
        fallos += not bien
        print(f"[{'BIEN' if bien else 'FALLA'}] {nombre}: {detalle}")
    if args.comprobar:
        print(f"{len(CASOS) - fallos}/{len(CASOS)} defectos detectados sin errores ajenos")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
