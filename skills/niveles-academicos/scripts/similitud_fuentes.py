# -*- coding: utf-8 -*-
"""Frases del texto copiadas o casi idénticas a las de las fuentes.

Uso: python similitud_fuentes.py <texto .md|.txt|.docx> <carpeta fuentes>
                                 [--min-palabras 8] [--umbral 0.85] [--json]

Compara el cuerpo del texto (sin la lista de referencias) con los .txt
de <fuentes>/texto/ que deja extraer_texto.py (marcas "=== [p. N] ===").

Método:
1. El texto se divide en oraciones y se normaliza (minúsculas, sin
   tildes ni signos).
2. Las fuentes se indexan por n-gramas de 4 palabras en un diccionario
   (índice por hash: no se compara todo contra todo). Las semillas de
   4 palabras permiten encontrar también las oraciones copiadas con
   algunas palabras cambiadas, que no comparten ningún tramo de
   --min-palabras seguidas.
3. Para cada oración con semillas en común se toma la alineación
   (fuente, desplazamiento) con más semillas y se calculan el tramo
   idéntico más largo y la razón de similitud de difflib contra la
   ventana de la fuente que cubre la oración.

Categorías:
  COPIA            tramo idéntico de al menos --min-palabras palabras.
  CASI IDÉNTICA    razón >= --umbral (oraciones de --min-palabras o más).
  ENTRE COMILLAS   lo anterior, pero dentro de « », " " o “ ”: cita
                   textual; se informa aparte y no cuenta para el código.

Exclusiones (heurística para evitar falsos positivos): antes de
comparar se quitan de cada oración
  - los tramos de 4 o más palabras que aparecen tal cual en una
    referencia de la lista (títulos de obras citadas, nombres de revistas);
  - los nombres propios largos: 3 o más palabras seguidas con mayúscula
    inicial (admitiendo partículas como de, la, sobre), como "Convención
    Marco de las Naciones Unidas sobre el Cambio Climático".
  El resto de la oración se compara igual, así que una oración copiada
  que además menciona un título sigue apareciendo. Las oraciones que
  solo coincidían por esos tramos se listan como excluidas en el JSON.
Las oraciones se cortan en . ! ? salvo tras abreviaturas (et al., p.,
pp., ej., iniciales) y dentro de comillas.

Códigos de salida: 0 sin hallazgos; 1 hay COPIA o CASI IDÉNTICA fuera
de comillas; 2 no se pudo ejecutar (falta <fuentes>/texto/ o está vacía).
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import comun

SEMILLA = 4
PARTICULAS = {"de", "del", "la", "las", "los", "el", "y", "e", "en", "sobre", "para", "por",
              "a", "al", "of", "the", "and", "for", "on", "in", "da", "do", "dos", "das"}
PATRON_COMILLAS = re.compile(r"«[^»]*»|“[^”]*”|\"[^\"]*\"|„[^“”]*[“”]")
PATRON_ORACION = re.compile(r"(?<=[.!?…])[\"”»)]*\s+(?=[«\"“¿¡(]?[A-ZÁÉÍÓÚÑ0-9])")


def palabras_con_posicion(texto):
    """[(palabra_normalizada, inicio, fin, original)] de un texto."""
    salida = []
    for m in re.finditer(r"\w+", texto):
        for parte in comun.normalizar(m.group(0)).split():
            salida.append((parte, m.start(), m.end(), m.group(0)))
    return salida


# ---------------------------------------------------------------- fuentes

class Indice:
    def __init__(self):
        self.fuentes = []          # [(nombre, [palabras], [paginas], [originales])]
        self.semillas = defaultdict(list)

    def agregar(self, ruta):
        palabras, paginas, originales = [], [], []
        for pagina, texto in comun.leer_texto_paginado(ruta):
            texto = re.sub(r"(\w)[-­]\s*\n\s*(\w)", r"\1\2", texto)  # guion de fin de línea
            for palabra, _, _, original in palabras_con_posicion(texto):
                palabras.append(palabra)
                paginas.append(pagina)
                originales.append(original)
        numero = len(self.fuentes)
        self.fuentes.append((Path(ruta).name, palabras, paginas, originales))
        for i in range(len(palabras) - SEMILLA + 1):
            self.semillas[hash(tuple(palabras[i:i + SEMILLA]))].append((numero, i))

    def candidatos(self, tokens):
        """Alineaciones (fuente, desplazamiento) ordenadas por número de semillas."""
        cuenta = Counter()
        for i in range(len(tokens) - SEMILLA + 1):
            for fuente, pos in self.semillas.get(hash(tuple(tokens[i:i + SEMILLA])), ()):
                cuenta[(fuente, pos - i)] += 1
        return cuenta.most_common()


def tramo_mas_largo(tokens, fuente_palabras, desplazamiento):
    """Tramo idéntico más largo en la diagonal dada: (inicio_oracion, largo)."""
    mejor, actual, inicio = (0, 0), 0, 0
    for i, palabra in enumerate(tokens):
        j = desplazamiento + i
        if 0 <= j < len(fuente_palabras) and fuente_palabras[j] == palabra:
            if actual == 0:
                inicio = i
            actual += 1
            if actual > mejor[1]:
                mejor = (inicio, actual)
        else:
            actual = 0
    return mejor


def comparar(tokens, indice, fuente, desplazamiento):
    nombre, palabras, paginas, originales = indice.fuentes[fuente]
    margen = max(5, len(tokens) // 3)
    a = max(0, desplazamiento - margen)
    b = min(len(palabras), desplazamiento + len(tokens) + margen)
    ventana = palabras[a:b]
    comparador = SequenceMatcher(None, tokens, ventana, autojunk=False)
    bloques = [bl for bl in comparador.get_matching_blocks() if bl.size]
    if not bloques:
        return None
    ini, fin = a + bloques[0].b, a + bloques[-1].b + bloques[-1].size
    razon = SequenceMatcher(None, tokens, palabras[ini:fin], autojunk=False).ratio()
    tramo_ini, tramo_largo = tramo_mas_largo(tokens, palabras, desplazamiento)
    # El tramo más largo puede estar en otra diagonal cercana (palabras insertadas).
    for bl in bloques:
        if bl.size > tramo_largo:
            tramo_ini, tramo_largo = bl.a, bl.size
    pag_ini, pag_fin = paginas[ini], paginas[max(ini, fin - 1)]
    return {
        "archivo": nombre, "pagina": pag_ini if pag_ini == pag_fin else f"{pag_ini}-{pag_fin}",
        "fragmento_fuente": " ".join(originales[ini:fin]), "razon": round(razon, 3),
        "palabras_seguidas": tramo_largo, "tramo": (tramo_ini, tramo_largo),
    }


# ---------------------------------------------------------------- texto

ABREVIATURAS = {"al", "p", "pp", "ej", "etc", "fig", "figs", "dr", "dra", "sr", "sra", "vol",
                "núm", "num", "n", "ed", "eds", "cap", "párr", "parr", "cf", "vs", "aprox",
                "e.g", "i.e", "ca", "no", "art", "inc", "op", "cit"}


def oraciones(parrafos):
    """(número de párrafo, oración, tramos entre comillas relativos a la oración)."""
    for numero, parrafo in enumerate(parrafos, 1):
        texto = parrafo.lstrip("#>-* ").replace("*", "").replace("_", " ")
        comillas = [(m.start(), m.end()) for m in PATRON_COMILLAS.finditer(texto)]
        cortes = []
        for corte in PATRON_ORACION.finditer(texto):
            previa = re.search(r"([\w.]+)[.!?…][\"”»)]*$", texto[:corte.start()])
            palabra = previa.group(1).lower() if previa else ""
            if palabra in ABREVIATURAS or (len(palabra) == 1 and palabra.isalpha()):
                continue  # "et al. (2016)", "p. 5", iniciales
            if any(a < corte.start() < b for a, b in comillas):
                continue  # no cortar dentro de una cita entre comillas
            cortes.append(corte)
        inicio = 0
        for corte in cortes + [None]:
            fin = corte.start() if corte else len(texto)
            oracion = texto[inicio:fin].strip()
            if oracion:
                desfase = texto.index(oracion, inicio)
                yield numero, oracion, [(a - desfase, b - desfase) for a, b in comillas]
            if corte:
                inicio = corte.end()


def es_nombre_propio(originales):
    contenido = [o for o in originales if o.lower() not in PARTICULAS]
    return len(contenido) >= 2 and all(o[:1].isupper() for o in contenido)


def enmascarar(datos, semillas_refs):
    """Quita de la oración los tramos que son títulos de obras de la lista de
    referencias (4 palabras seguidas presentes en una referencia) y los
    nombres propios largos (3 o más palabras con mayúscula seguidas)."""
    quitar = set()
    tokens = [d[0] for d in datos]
    for i in range(len(tokens) - SEMILLA + 1):
        if tuple(tokens[i:i + SEMILLA]) in semillas_refs:
            quitar.update(range(i, i + SEMILLA))
    corrida = []
    for i, d in enumerate(datos + [("", 0, 0, "")]):
        if d[3][:1].isupper() or (corrida and d[3].lower() in PARTICULAS):
            corrida.append(i)
            continue
        while corrida and datos[corrida[-1]][3].lower() in PARTICULAS:
            corrida.pop()
        if sum(1 for j in corrida if datos[j][3].lower() not in PARTICULAS) >= 3:
            quitar.update(corrida)
        corrida = []
    return [d for i, d in enumerate(datos) if i not in quitar], bool(quitar)


def mejor_coincidencia(datos, indice, min_palabras, umbral):
    tokens = [d[0] for d in datos]
    if len(tokens) < SEMILLA:
        return None
    mejor = None
    for (fuente, despl), _ in indice.candidatos(tokens)[:5]:
        r = comparar(tokens, indice, fuente, despl)
        if r and (mejor is None or (r["palabras_seguidas"], r["razon"]) >
                  (mejor["palabras_seguidas"], mejor["razon"])):
            mejor = r
    if not mejor:
        return None
    mejor["copia"] = mejor["palabras_seguidas"] >= min_palabras
    mejor["casi"] = len(tokens) >= min_palabras and mejor["razon"] >= umbral
    return mejor if (mejor["copia"] or mejor["casi"]) else None


def analizar(parrafos, referencias, indice, min_palabras, umbral):
    semillas_refs = set()
    for ref in referencias:
        t = comun.normalizar(ref).split()
        semillas_refs.update(tuple(t[i:i + SEMILLA]) for i in range(len(t) - SEMILLA + 1))
    hallazgos, excluidos = [], []
    for numero, oracion, comillas in oraciones(parrafos):
        completos = palabras_con_posicion(oracion)
        datos, enmascarado = enmascarar(completos, semillas_refs)
        mejor = mejor_coincidencia(datos, indice, min_palabras, umbral)
        if not mejor:
            if enmascarado:
                sin_mascara = mejor_coincidencia(completos, indice, min_palabras, umbral)
                if sin_mascara:
                    sin_mascara.pop("tramo")
                    excluidos.append(dict(sin_mascara, parrafo=numero, oracion=oracion,
                                          motivo="el tramo común es un título de la lista de "
                                                 "referencias o un nombre propio largo"))
            continue
        t_ini, t_largo = mejor.pop("tramo")
        tramo = datos[t_ini:t_ini + t_largo]
        mejor.update({"parrafo": numero, "oracion": oracion,
                      "tramo_comun": oracion[tramo[0][1]:tramo[-1][2]] if tramo else ""})
        # ¿Las palabras coincidentes están entre comillas?
        dentro = sum(1 for d in tramo if any(a <= d[1] < b for a, b in comillas))
        if tramo and dentro >= len(tramo) / 2:
            categoria = "ENTRE COMILLAS"
        else:
            categoria = "COPIA" if mejor["copia"] else "CASI IDÉNTICA"
        mejor["categoria"] = categoria
        del mejor["copia"], mejor["casi"]
        hallazgos.append(mejor)
    return hallazgos, excluidos


def main(argv=None):
    comun.salida_utf8()
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("texto")
    analizador.add_argument("fuentes")
    analizador.add_argument("--min-palabras", type=int, default=8)
    analizador.add_argument("--umbral", type=float, default=0.85)
    analizador.add_argument("--json", action="store_true")
    args = analizador.parse_args(argv)
    carpeta = Path(args.fuentes) / "texto"
    archivos = sorted(carpeta.glob("*.txt")) if carpeta.is_dir() else []
    if not archivos:
        print(f"No hay textos en {carpeta}. Corra antes extraer_texto.py sobre la carpeta de "
              "fuentes para generar fuentes/texto/*.txt.", file=sys.stderr)
        return 2
    if args.min_palabras < SEMILLA:
        print(f"--min-palabras debe ser al menos {SEMILLA}.", file=sys.stderr)
        return 2
    try:
        parrafos = comun.leer_bloques(args.texto)
        indice = Indice()
        for archivo in archivos:
            indice.agregar(archivo)
    except (OSError, UnicodeDecodeError, KeyError, ValueError) as error:
        print(f"No se pudo leer: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    cuerpo, referencias = comun.separar_referencias(parrafos)
    cuerpo += comun.tras_referencias(parrafos)
    hallazgos, excluidos = analizar(cuerpo, referencias, indice, args.min_palabras, args.umbral)
    graves = [h for h in hallazgos if h["categoria"] != "ENTRE COMILLAS"]
    if args.json:
        print(json.dumps({"archivo": str(args.texto), "fuentes": [a.name for a in archivos],
                          "min_palabras": args.min_palabras, "umbral": args.umbral,
                          "hallazgos": hallazgos, "excluidos": excluidos},
                         ensure_ascii=False, indent=2))
    else:
        print(f"Texto: {args.texto}")
        print(f"Fuentes comparadas: {len(archivos)} ({sum(len(f[1]) for f in indice.fuentes)} "
              f"palabras). Mínimo {args.min_palabras} palabras seguidas; umbral {args.umbral}.")
        orden = {"COPIA": 0, "CASI IDÉNTICA": 1, "ENTRE COMILLAS": 2}
        for h in sorted(hallazgos, key=lambda h: (orden[h["categoria"]], h["parrafo"])):
            print(f"\n[{h['categoria']}] párr. {h['parrafo']} — {h['archivo']}, p. {h['pagina']} "
                  f"({h['palabras_seguidas']} palabras seguidas, razón {h['razon']})")
            print(f"  Texto:  {h['oracion']}")
            print(f"  Fuente: {h['fragmento_fuente']}")
        if not hallazgos:
            print("\nSin coincidencias.")
        if excluidos:
            print(f"\nExcluidos por título o nombre propio: {len(excluidos)} (ver --json).")
    return 1 if graves else 0


if __name__ == "__main__":
    sys.exit(main())
