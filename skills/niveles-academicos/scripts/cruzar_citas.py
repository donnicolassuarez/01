# -*- coding: utf-8 -*-
"""Cruce de citas del texto con la lista de referencias (APA 7, español).

Uso: python cruzar_citas.py <texto .md|.txt|.docx> [--referencias <archivo>] [--json]

Extrae del cuerpo (y de los anexos) las citas parentéticas
"(Autor, 2020)", "(Autor y Otro, 2020; Otro et al., 2019a)",
"(véase Autor, 2020, p. 5)", "(Instituto Nacional de Estadística
[INE], 2022)", y las narrativas "Autor (2020)", "Autor et al. (2020)",
"de la Cruz (2020)", y obras republicadas "(Autor, 1605/2004)" (se
coteja el año de la edición, el segundo). Analiza cada referencia (primer autor o
institución y su sigla, número de autores, año) y reporta:

  (a) citas sin referencia;
  (b) referencias no citadas;
  (c) autor que coincide con año distinto, o número de autores mal
      citado ("et al." con dos autores; "y" con tres o más; un solo
      apellido cuando la obra tiene dos);
  (d) referencias duplicadas o fuera de orden alfabético.

Observaciones (no cambian el código de salida): localizadores de página
o párrafo (regla del usuario: citas simples, sin página ni párrafo),
siglas usadas en la primera cita sin presentar el nombre completo, y
paréntesis descartados por ser lugar o periodo.

Heurísticas documentadas:
- Autor de una cita: la secuencia de palabras con mayúscula inicial
  (y partículas de, del, la, van, von, y, &...) justo antes de ", año"
  o de "(año)". Se prueban sus sufijos y gana el más largo que coincide
  con una referencia: así "Directrices del IPCC (2019)" es IPCC y
  "datos de Mongabay Latam (2024)" es Mongabay Latam.
- Si una cita narrativa no coincide, se mira el texto previo de la
  misma oración (hasta 80 caracteres): "datos del IPCC, Sexto Informe
  de Evaluación (2021)" se toma como cita de IPCC 2021.
- "(Bolivia, 2022)", "(Pando, 2024)", "(junio, 2024)": si el supuesto
  autor no coincide con ninguna referencia y es un lugar o periodo de
  la lista LUGARES_Y_PERIODOS, no es cita; se informa como descartado.
  En cualquier otro caso un autor sin referencia se reporta como
  posible cita sin referencia.
- "(Autor, 2010, como se citó en Otro, 2020)": la fuente original no
  necesita referencia; solo se exige la secundaria.
- Un año suelto entre paréntesis después de un sustantivo común,
  "(2023-2024)", "(2023 vs. 2024)" o "(PM2,5)" no son citas.

Códigos de salida: 0 sin problemas; 1 si (a), (b) o (c) tienen algo;
2 no se pudo ejecutar (archivo ilegible o sin lista de referencias).
"""
import argparse
import json
import re
import sys
from pathlib import Path

import comun

MAY = "A-ZÁÉÍÓÚÑÜÀÈÌÒÙÇ"
PALABRA_MAY = rf"[{MAY}](?:[^\W\d_]|['’\-/])*"  # sin cifras: "N2O" o "CO2" no son autores
PARTICULAS = ("de", "del", "la", "las", "los", "van", "von", "der", "den", "da", "das",
              "do", "dos", "di", "du", "le", "y", "e", "&")
PARTICULAS_INICIALES = ("de", "del", "la", "las", "los", "van", "von", "der", "den", "da",
                        "das", "do", "dos", "di", "du", "le")
CONECTORES = ("y", "e", "&")
ANIO = r"(?:1[5-9]\d\d|20\d\d)[a-z]?(?![\d])|s\.\s?f\.(?:-[a-z])?"
# "1605/2004": año de la obra original y año de la edición consultada (APA 7,
# obras republicadas); la referencia lleva el segundo.
ANIO_CITA = rf"(?:(?:1[5-9]\d\d|20\d\d)/(?=\d{{4}}))?(?:{ANIO})"
ANIOS = rf"(?:{ANIO_CITA})(?:\s*,\s*(?:{ANIO_CITA}))*"
LOCALIZADOR = r"(?:pp?\.|p[aá]rr\.|cap\.|sec\.|secc\.|min\.|fig\.|tabla)\s*[\w–\-]+"
CORRIDA = (rf"(?:{PALABRA_MAY}|(?:{'|'.join(PARTICULAS_INICIALES)})(?=\s+(?:{PALABRA_MAY}|"
           rf"(?:{'|'.join(PARTICULAS_INICIALES)})\s)))"
           rf"(?:[ \t]+(?:{PALABRA_MAY}|(?:{'|'.join(map(re.escape, PARTICULAS))})(?=[ \t])))*")
ET_AL = r"(?:\s+et\s+al\.?)"
SIGLA = r"(?:\s*\[(?P<sigla>[^\]]{1,20})\])"
PATRON_PARENTETICA = re.compile(
    rf"(?<![\w'’\-/])(?P<autor>{CORRIDA})(?P<etal>{ET_AL})?{SIGLA}?\s*,\s*(?P<anios>{ANIOS})"
    rf"(?P<loc>\s*,\s*{LOCALIZADOR})?")
PATRON_NARRATIVA = re.compile(
    rf"(?<![\w'’\-/])(?P<autor>{CORRIDA})(?P<etal>{ET_AL})?{SIGLA}?\s*"
    rf"\((?P<anios>{ANIOS})(?P<loc>\s*,\s*{LOCALIZADOR})?\)")
PATRON_LOCALIZADOR_SUELTO = re.compile(rf"\(\s*{LOCALIZADOR}[^()]*\)")
PATRON_SECUNDARIA = re.compile(r"^\s*,?\s*(?:como\s+se\s+cit[oó]\s+en|citad[oa]\s+en|en)\b",
                               re.I)
PALABRAS_VACIAS = {
    "segun", "como", "para", "por", "en", "con", "desde", "tal", "asi", "ademas", "tambien",
    "sin", "aunque", "mientras", "ya", "esto", "este", "esta", "estos", "estas", "ver",
    "vease", "cf", "el", "la", "los", "las", "lo", "un", "una", "al", "del", "de", "y", "e",
    "datos", "informe", "fuente", "elaboracion", "propia", "base", "figura", "tabla",
    "segun", "citado", "ejemplo", "veanse", "sobre", "que", "porque", "pero", "donde",
}
# Lugares y periodos evidentes: "(Bolivia, 2022)" no es una cita.
LUGARES_Y_PERIODOS = {
    "bolivia", "pando", "beni", "la paz", "cochabamba", "santa cruz", "oruro", "potosi",
    "chuquisaca", "tarija", "cobija", "riberalta", "trinidad", "sucre", "el alto", "guayaramerin",
    "brasil", "peru", "chile", "argentina", "paraguay", "uruguay", "colombia", "ecuador",
    "venezuela", "mexico", "espana", "estados unidos", "eeuu", "ee uu", "china", "india",
    "acre", "rondonia", "madre de dios", "amazonia", "amazonia boliviana", "amazonia sur",
    "america latina", "latinoamerica", "sudamerica", "suramerica", "america del sur",
    "mundo", "global", "nacional", "departamental", "municipal", "norte amazonico",
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
    "setiembre", "octubre", "noviembre", "diciembre", "verano", "invierno", "otono",
    "primavera", "gestion", "epoca seca", "epoca de lluvias", "temporada",
}


# ---------------------------------------------------------------- referencias

PATRON_ANIO_REF = re.compile(r"\((?P<anio>(?:1[5-9]\d\d|20\d\d)[a-z]?|s\.\s?f\.(?:-[a-z])?)"
                             r"(?:,[^)]*)?\)")
PATRON_INICIALES = re.compile(rf"(?:[{MAY}][a-z]?\.?)(?:[\s\-]*[{MAY}][a-z]?\.?)*")


def norm_anio(anio):
    anio = anio.replace(" ", "")
    return "s.f." + anio[4:] if anio.startswith("s.f.") else anio


def analizar_referencia(texto, indice):
    limpio = texto.replace("*", "").replace("_", " ").strip()
    hallado = PATRON_ANIO_REF.search(limpio)
    ref = {"indice": indice, "texto": texto, "anio": None, "autor": "", "sigla": None,
           "apellidos": [], "n_autores": 0, "institucional": False, "claves": set(),
           "titulo": "", "aviso": None}
    if not hallado:
        ref["aviso"] = "no se encontró el año entre paréntesis"
        return ref
    ref["anio"] = norm_anio(hallado.group("anio"))
    cabeza = limpio[:hallado.start()].strip().rstrip(".").strip()
    cabeza = re.sub(r"\s*\((?:Eds?|Coords?|Comps?|Dirs?)\.?\)\s*$", "", cabeza, flags=re.I)
    if not cabeza:  # obra sin autor: el título va primero
        ref["titulo"] = limpio[:hallado.start()]
        return ref
    sigla = re.search(r"\[([^\]]+)\]\s*$", cabeza)
    if sigla:
        ref["sigla"] = sigla.group(1).strip()
        cabeza = cabeza[:sigla.start()].strip()
    ref["autor"] = cabeza
    trozos = [t.strip() for t in re.split(r",\s*|\s+(?:y|&)\s+|\.\.\.|…", cabeza) if t.strip()]
    apellidos, iniciales = [], 0
    for i, trozo in enumerate(trozos):
        trozo = re.sub(r"^(?:y|&)\s+", "", trozo)
        # Iniciales: "J.", "J. C.", "J.-P.", "Á" (el punto final se quitó al cortar).
        # "M. de", "L. van der": partícula del apellido pospuesta a las iniciales.
        sin_particula = re.sub(r"(?:\s+(?:de|del|la|las|los|van|von|der|den|da|das|do|dos|di|du|le))+$",
                               "", trozo)
        if i > 0 and apellidos and len(sin_particula) <= 12 and \
                PATRON_INICIALES.fullmatch(sin_particula):
            iniciales += 1
        else:
            apellidos.append(trozo)
    if iniciales:
        ref["apellidos"] = apellidos
        ref["n_autores"] = 21 if ("..." in cabeza or "…" in cabeza) else len(apellidos)
    else:
        ref["institucional"] = True
        ref["apellidos"] = [cabeza]
        ref["n_autores"] = 1
    ref["claves"] = {comun.normalizar(ref["apellidos"][0])}
    if ref["sigla"]:
        ref["claves"].add(comun.normalizar(ref["sigla"]))
    return ref


def problemas_lista(refs):
    """(d): duplicadas y fuera de orden alfabético."""
    hallazgos, vistos = [], {}
    for ref in refs:
        clave = (comun.normalizar(ref["autor"] or ref["titulo"]), ref["anio"],
                 comun.normalizar(ref["texto"])[:60])
        if clave in vistos:
            hallazgos.append({"tipo": "duplicada", "referencia": ref["texto"],
                              "detalle": f"repite la referencia n.º {vistos[clave] + 1}"})
        vistos.setdefault(clave, ref["indice"])

    def orden(ref):
        anio = ref["anio"] or ""
        return (comun.normalizar(ref["autor"] or ref["titulo"]),
                "0" if anio.startswith("s.f.") else "1" + anio)
    for previa, actual in zip(refs, refs[1:]):
        if orden(actual) < orden(previa):
            hallazgos.append({"tipo": "fuera de orden", "referencia": actual["texto"],
                              "detalle": f"debería ir antes de «{previa['texto'][:70]}»"})
    return hallazgos


# ---------------------------------------------------------------- citas

def quitar_vacias(texto):
    palabras = texto.split()
    while palabras and (comun.normalizar(palabras[0]) in PALABRAS_VACIAS or palabras[0].islower()):
        palabras.pop(0)
    return " ".join(palabras)


def contexto(parrafo, inicio, fin, margen=50):
    pre = parrafo[max(0, inicio - margen):inicio]
    pos = parrafo[fin:fin + margen]
    return ("…" if inicio > margen else "") + pre + parrafo[inicio:fin] + pos + \
        ("…" if fin + margen < len(parrafo) else "")


def resolver(corrida, sigla, etal, refs):
    """Devuelve (ref_candidatas, autor_citado, n_autores_citados, segundo_apellido)."""
    tokens = corrida.split()
    if sigla:
        candidatas = [r for r in refs if comun.normalizar(sigla) in r["claves"]]
        if candidatas:
            return candidatas, sigla, 1, None
    # Nombre completo (instituciones con "y" dentro) por sufijos.
    for i in range(len(tokens)):
        sufijo = comun.normalizar(" ".join(tokens[i:]))
        candidatas = [r for r in refs if sufijo in r["claves"]]
        if candidatas and not etal:
            return candidatas, " ".join(tokens[i:]), 1, None
    # Varios autores: "A y B", "A, B y C".
    partes = re.split(r"\s+(?:y|e|&)\s+", corrida)
    primera = partes[0].split()
    n = 3 if etal else len(partes)
    segundo = partes[1] if len(partes) > 1 else None
    for i in range(len(primera)):
        sufijo = comun.normalizar(" ".join(primera[i:]))
        candidatas = [r for r in refs if sufijo in r["claves"]]
        if candidatas:
            return candidatas, " ".join(primera[i:]), n, segundo
    autor = quitar_vacias(partes[0]) or partes[0]
    return [], autor, n, segundo


def extraer_citas(parrafos, refs):
    citas, descartes, localizadores = [], [], []
    for numero, parrafo in enumerate(parrafos, 1):
        texto = parrafo.replace("*", "").replace("_", " ")
        for loc in PATRON_LOCALIZADOR_SUELTO.finditer(texto):
            localizadores.append({"parrafo": numero, "localizador": loc.group(0),
                                  "contexto": contexto(texto, loc.start(), loc.end())})
        # Parentéticas: contenido de cada paréntesis sin paréntesis internos.
        for grupo in re.finditer(r"\(([^()]*)\)", texto):
            interior = grupo.group(1)
            desplazamiento = grupo.start(1)
            for segmento in re.finditer(r"[^;]+", interior):
                trozo = segmento.group(0)
                for m in PATRON_PARENTETICA.finditer(trozo):
                    secundaria = bool(PATRON_SECUNDARIA.match(trozo[m.end():])) and \
                        bool(PATRON_PARENTETICA.search(trozo[m.end():]))
                    citas.extend(armar(m, "parentética", numero, texto,
                                       desplazamiento + segmento.start(), refs, secundaria))
        for m in PATRON_NARRATIVA.finditer(texto):
            citas.extend(armar(m, "narrativa", numero, texto, 0, refs, False))
    citas.sort(key=lambda c: (c["parrafo"], c["pos"]))
    validas = []
    for cita in citas:
        if cita["loc"]:
            localizadores.append({"parrafo": cita["parrafo"], "localizador": cita["loc"],
                                  "contexto": cita["contexto"]})
        if not cita["refs"] and not cita["autor_ok"]:
            if comun.normalizar(cita["autor"]) in LUGARES_Y_PERIODOS:
                descartes.append(cita)
                continue
        validas.append(cita)
    return validas, descartes, localizadores


def armar(m, forma, numero, texto, base, refs, secundaria):
    corrida = m.group("autor")
    candidatas, autor, n, segundo = resolver(corrida, m.group("sigla"), m.group("etal"), refs)
    inicio, fin = base + m.start(), base + m.end()
    if forma == "parentética":
        # Ampliar al paréntesis completo para el contexto.
        inicio = texto.rfind("(", 0, inicio + 1)
        fin = texto.find(")", fin - 1) + 1 or fin
    sin_original = re.sub(r"(?:1[5-9]\d\d|20\d\d)/(?=\d{4})", "", m.group("anios"))
    anios = [norm_anio(a.strip()) for a in re.findall(ANIO, sin_original)]
    salida = []
    for anio in anios:
        cand = candidatas
        if not cand and forma == "narrativa":
            # Mirar atrás en la misma oración: "datos del IPCC, Sexto Informe (2021)".
            previo = texto[max(0, base + m.start() - 80):base + m.end()]
            previo = re.split(r"[.!?]\s", previo)[-1]
            previo_n = f" {comun.normalizar(previo)} "
            cand = [r for r in refs if r["anio"] == anio and
                    any(f" {c} " in previo_n for c in r["claves"])]
            if cand:
                autor = cand[0]["sigla"] or cand[0]["apellidos"][0]
                n = 1 if cand[0]["institucional"] else n
        salida.append({
            "forma": forma, "parrafo": numero, "texto": m.group(0).strip(),
            "contexto": contexto(texto, max(inicio, 0), fin), "autor": autor,
            "sigla_presentada": m.group("sigla"), "anio": anio, "n_autores": n,
            "et_al": bool(m.group("etal")), "segundo": segundo,
            "loc": (m.group("loc") or "").strip(" ,"), "refs": cand, "pos": base + m.start(),
            "autor_ok": bool(cand), "secundaria": secundaria,
        })
    return salida


# ---------------------------------------------------------------- cruce

def cruzar(citas, refs):
    sin_ref, discordantes, citadas = [], [], set()
    for cita in citas:
        if cita["secundaria"]:
            continue  # fuente original citada a través de otra: no exige referencia
        if not cita["refs"]:
            sin_ref.append(cita)
            continue
        mismas = [r for r in cita["refs"] if r["anio"] == cita["anio"]]
        if not mismas:
            anios = ", ".join(sorted({r["anio"] or "?" for r in cita["refs"]}))
            discordantes.append((cita, f"el autor está en referencias pero con año {anios}"))
            for r in cita["refs"]:
                citadas.add(r["indice"])
            continue
        ref = mismas[0]
        for r in mismas:
            citadas.add(r["indice"])
        reales = ref["n_autores"]
        problema = None
        if cita["et_al"] and reales == 2:
            problema = "usa «et al.» pero la obra tiene dos autores: se citan ambos"
        elif cita["et_al"] and reales == 1:
            problema = "usa «et al.» pero la obra tiene un solo autor"
        elif not cita["et_al"] and cita["n_autores"] >= 2 and reales >= 3:
            problema = f"nombra {cita['n_autores']} autores pero la obra tiene {reales}: va «et al.»"
        elif not cita["et_al"] and cita["n_autores"] == 1 and reales == 2:
            problema = "nombra un solo autor pero la obra tiene dos: se citan ambos"
        elif not cita["et_al"] and cita["n_autores"] == 1 and reales >= 3:
            problema = f"nombra un solo autor pero la obra tiene {reales}: va «et al.»"
        elif cita["segundo"] and reales == 2 and len(ref["apellidos"]) > 1 and \
                comun.normalizar(cita["segundo"]) != comun.normalizar(ref["apellidos"][1]):
            problema = f"el segundo autor de la referencia es {ref['apellidos'][1]}"
        if problema:
            discordantes.append((cita, problema))
    no_citadas = [r for r in refs if r["indice"] not in citadas]
    return sin_ref, no_citadas, discordantes


def siglas_sin_presentar(citas, refs, parrafos):
    """Primera cita de una obra con sigla que usa la sigla sin el nombre completo."""
    obs, vistos = [], set()
    texto_previo = ""
    for numero, parrafo in enumerate(parrafos, 1):
        for cita in [c for c in citas if c["parrafo"] == numero and c["refs"]]:
            ref = cita["refs"][0]
            if not ref["sigla"] or ref["sigla"] in vistos:
                continue
            vistos.add(ref["sigla"])
            usada = comun.normalizar(cita["autor"]) == comun.normalizar(ref["sigla"])
            nombre = comun.normalizar(ref["apellidos"][0])
            presentado = nombre in comun.normalizar(texto_previo + " " + parrafo[:200])
            if usada and not cita["sigla_presentada"] and not presentado:
                obs.append({"parrafo": numero, "sigla": ref["sigla"],
                            "detalle": f"primera cita con «{ref['sigla']}» sin el nombre completo "
                                       f"«{ref['apellidos'][0]} [{ref['sigla']}]»",
                            "contexto": cita["contexto"]})
        texto_previo += " " + parrafo
    return obs


# ---------------------------------------------------------------- salida

def resumen_cita(c):
    return {"parrafo": c["parrafo"], "cita": c["texto"], "autor": c["autor"], "anio": c["anio"],
            "contexto": c["contexto"]}


def main(argv=None):
    comun.salida_utf8()
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("texto")
    analizador.add_argument("--referencias", help="archivo aparte con la lista de referencias")
    analizador.add_argument("--json", action="store_true")
    args = analizador.parse_args(argv)
    try:
        parrafos = comun.leer_bloques(args.texto)
        cuerpo, lista = comun.separar_referencias(parrafos)
        cuerpo = cuerpo + comun.tras_referencias(parrafos)
        if args.referencias:
            otros = comun.leer_bloques(args.referencias)
            _, lista = comun.separar_referencias(otros)
            lista = lista or otros
    except (OSError, KeyError, UnicodeDecodeError, Exception) as error:
        print(f"No se pudo leer el archivo: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    if not lista:
        print("No se encontró la lista de referencias (encabezado «Referencias» o "
              "«Bibliografía»). Use --referencias.", file=sys.stderr)
        return 2

    refs = [analizar_referencia(t, i) for i, t in enumerate(lista)]
    citas, descartes, localizadores = extraer_citas(cuerpo, refs)
    sin_ref, no_citadas, discordantes = cruzar(citas, refs)
    lista_d = problemas_lista(refs)
    siglas = siglas_sin_presentar(citas, refs, cuerpo)
    unicas = {(comun.normalizar(c["autor"]), c["anio"]) for c in citas}
    resultado = {
        "archivo": str(Path(args.texto)),
        "total_citas": len(citas), "citas_unicas": len(unicas), "referencias": len(refs),
        "a_citas_sin_referencia": [resumen_cita(c) for c in sin_ref],
        "b_referencias_no_citadas": [r["texto"] for r in no_citadas],
        "c_autor_o_anio_discordante": [dict(resumen_cita(c), problema=p) for c, p in discordantes],
        "d_lista_de_referencias": lista_d,
        "observaciones": {
            "localizadores": localizadores,
            "siglas_sin_presentar": siglas,
            "descartados_lugar_o_periodo": [resumen_cita(c) for c in descartes],
            "referencias_sin_anio": [r["texto"] for r in refs if r["aviso"]],
        },
        "citas": [dict(resumen_cita(c), forma=c["forma"],
                       referencia=c["refs"][0]["texto"][:80] if c["refs"] else None)
                  for c in citas],
        "analisis_referencias": [{"referencia": r["texto"], "primer_autor": r["apellidos"][0]
                                  if r["apellidos"] else None, "sigla": r["sigla"],
                                  "n_autores": r["n_autores"], "anio": r["anio"]} for r in refs],
    }
    codigo = 1 if (sin_ref or no_citadas or discordantes) else 0
    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return codigo

    print(f"Archivo: {resultado['archivo']}")
    print(f"Citas: {len(citas)} (únicas: {len(unicas)}). Referencias: {len(refs)}.")
    def bloque(titulo, filas):
        print(f"\n{titulo}: {len(filas) if filas else 'ninguna'}")
        for fila in filas:
            print("  - " + fila)
    bloque("(a) Citas sin referencia", [f"[párr. {c['parrafo']}] {c['autor']}, {c['anio']} — "
                                        f"{c['contexto']}" for c in sin_ref])
    bloque("(b) Referencias no citadas", [r["texto"] for r in no_citadas])
    bloque("(c) Autor o año que no coinciden", [f"[párr. {c['parrafo']}] {c['texto']}: {p}"
                                                 for c, p in discordantes])
    bloque("(d) Lista de referencias (duplicadas u orden)",
           [f"{h['tipo']}: {h['referencia'][:80]} — {h['detalle']}" for h in lista_d])
    bloque("Observación: localizadores de página o párrafo (la regla es citar sin ellos)",
           [f"[párr. {l['parrafo']}] {l['localizador']} — {l['contexto']}" for l in localizadores])
    bloque("Observación: siglas sin presentar en la primera cita",
           [f"[párr. {s['parrafo']}] {s['detalle']}" for s in siglas])
    bloque("Descartados por ser lugar o periodo (no son citas)",
           [f"[párr. {c['parrafo']}] {c['texto']}" for c in descartes])
    for r in refs:
        if r["aviso"]:
            print(f"Aviso: referencia sin año reconocible: {r['texto'][:80]}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
