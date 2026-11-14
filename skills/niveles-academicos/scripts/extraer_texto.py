# -*- coding: utf-8 -*-
"""Texto con número de página a partir de PDF, y búsqueda de pasajes.

Uso A (extraer):
  python extraer_texto.py <archivo.pdf | carpeta fuentes> [--salida carpeta] [--forzar] [--json]
  Escribe un .txt por PDF en <carpeta del PDF>/texto/<mismo nombre>.txt (o
  en --salida), con la línea "=== [p. N] ===" antes de cada página; lo lee
  comun.leer_texto_paginado. Une palabras cortadas con guion a fin de línea.
  No reextrae si el .txt es más nuevo que el PDF, salvo --forzar.
  Un PDF con menos de 200 caracteres por página de media se lista como
  "sin texto: requiere OCR" (probablemente escaneado).

Uso B (buscar un pasaje):
  python extraer_texto.py --buscar "frase" <carpeta fuentes | carpeta texto | .txt>
         [--umbral 0.8] [--json]
  Busca en los .txt ya extraídos. Primero coincidencia exacta tras
  comun.normalizar (sin tildes, signos ni mayúsculas, y sin importar los
  saltos de línea o de página); si no la hay, aproximada por ventana de
  palabras (similitud de caracteres de difflib entre 0 y 1). Devuelve
  fuente, página, puntaje y el fragmento con contexto.
  Límite: con frases de menos de 5 palabras la búsqueda aproximada no es
  fiable y no se hace; solo vale la exacta.

Requiere PyMuPDF (pip install pymupdf).

Códigos de salida: A) 0 todo extraído; 1 algún PDF sin texto o con error;
2 no se pudo ejecutar. B) 0 encontrada; 1 no encontrada; 2 no hay textos.
"""
import argparse
import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

import comun

MINIMO_CARACTERES_POR_PAGINA = 200
CONTEXTO_PALABRAS = 25
PATRON_GUION = re.compile(r"(\w)[-­‐]\n[ \t]*(\w)")


def cargar_pymupdf():
    try:
        import pymupdf
        return pymupdf
    except ImportError:
        try:
            import fitz
            return fitz
        except ImportError:
            return None


# --------------------------------------------------------------- extracción

def unir_guiones(texto):
    """'investiga-\\nción' -> 'investigación'. Solo si la línea siguiente empieza
    en minúscula: 'Bolivia-\\nChile' o '2019-\\n2020' no se tocan."""
    def unir(m):
        return m.group(1) + m.group(2) if m.group(2).islower() else m.group(0)
    return PATRON_GUION.sub(unir, texto)


def texto_de_pagina(pagina):
    texto = pagina.get_text("text")
    texto = unir_guiones(texto.replace("\r\n", "\n"))
    # una marca de página dentro del texto rompería la lectura posterior
    return "\n".join(l for l in texto.splitlines() if not comun.PATRON_MARCA_PAGINA.match(l.strip()))


def extraer_pdf(pymupdf, ruta_pdf, ruta_txt):
    with pymupdf.open(ruta_pdf) as documento:
        partes, caracteres = [], 0
        for numero, pagina in enumerate(documento, 1):
            texto = texto_de_pagina(pagina).strip()
            caracteres += len(re.sub(r"\s", "", texto))
            partes.append(comun.MARCA_PAGINA.format(n=numero))
            partes.append(texto)
        paginas = documento.page_count
    comun.escribir_atomico(ruta_txt, "\n".join(partes) + "\n")
    return paginas, caracteres


def densidad_txt(ruta_txt):
    paginas = comun.leer_texto_paginado(ruta_txt)
    caracteres = sum(len(re.sub(r"\s", "", t)) for _, t in paginas)
    return len(paginas), caracteres


def modo_extraer(opciones):
    pymupdf = cargar_pymupdf()
    if pymupdf is None:
        print("No se pudo ejecutar: falta PyMuPDF (pip install pymupdf).", file=sys.stderr)
        return 2
    origen = Path(opciones.objetivo)
    if origen.is_dir():
        pdfs = sorted(p for p in origen.iterdir() if p.suffix.lower() == ".pdf" and p.is_file())
        carpeta_base = origen
    elif origen.is_file() and origen.suffix.lower() == ".pdf":
        pdfs, carpeta_base = [origen], origen.parent
    else:
        print(f"No se pudo ejecutar: no es un PDF ni una carpeta: {origen}", file=sys.stderr)
        return 2
    if not pdfs:
        print(f"No se pudo ejecutar: no hay PDF en {origen}", file=sys.stderr)
        return 2
    destino = Path(opciones.salida) if opciones.salida else carpeta_base / "texto"

    informe = {"extraidos": [], "omitidos": [], "sin_texto": [], "errores": []}
    for pdf in pdfs:
        txt = destino / (pdf.stem + ".txt")
        try:
            if txt.exists() and txt.stat().st_mtime >= pdf.stat().st_mtime and not opciones.forzar:
                paginas, caracteres = densidad_txt(txt)
                lista = informe["omitidos"]
            else:
                paginas, caracteres = extraer_pdf(pymupdf, pdf, txt)
                lista = informe["extraidos"]
        except Exception as error:  # PDF dañado, cifrado, sin permisos
            informe["errores"].append({"pdf": pdf.name, "motivo": f"{type(error).__name__}: {error}"})
            continue
        dato = {"pdf": pdf.name, "txt": str(txt), "paginas": paginas, "caracteres": caracteres,
                "caracteres_por_pagina": round(caracteres / paginas) if paginas else 0}
        lista.append(dato)
        if not paginas or caracteres / paginas < MINIMO_CARACTERES_POR_PAGINA:
            informe["sin_texto"].append(dato)

    if opciones.json:
        print(json.dumps(informe, ensure_ascii=False, indent=2))
    else:
        for d in informe["extraidos"]:
            print(f"EXTRAÍDO  {d['pdf']}: {d['paginas']} p., {d['caracteres']} caracteres")
        for d in informe["omitidos"]:
            print(f"AL DÍA    {d['pdf']}: el .txt es más nuevo (use --forzar para rehacerlo)")
        for d in informe["sin_texto"]:
            print(f"SIN TEXTO {d['pdf']}: {d['caracteres_por_pagina']} caracteres por página; requiere OCR")
        for d in informe["errores"]:
            print(f"ERROR     {d['pdf']}: {d['motivo']}")
        print(f"\nRESUMEN: extraídos {len(informe['extraidos'])}, al día {len(informe['omitidos'])}, "
              f"sin texto {len(informe['sin_texto'])}, errores {len(informe['errores'])}. "
              f"Textos en {destino}")
    return 1 if informe["sin_texto"] or informe["errores"] else 0


# ------------------------------------------------------------------ búsqueda

def textos_disponibles(objetivo):
    ruta = Path(objetivo)
    if ruta.is_file() and ruta.suffix.lower() == ".txt":
        return [ruta]
    if ruta.is_dir():
        carpeta = ruta / "texto" if (ruta / "texto").is_dir() else ruta
        return sorted(carpeta.glob("*.txt"))
    return []


class Fichas(list):
    """Lista de fichas con el texto original de cada página (para el fragmento)."""
    textos = ()


def fichas_de(ruta_txt):
    """Lista de (token_normalizado, palabra_original, página, (k, inicio, fin)) del
    documento entero; (k, inicio, fin) sitúa la palabra en el texto original
    de la página k. Las palabras que no dan token ("±", "—") no entran en la
    lista pero sí en el fragmento, que se corta del texto original."""
    fichas = Fichas()
    textos = []
    for k, (pagina, texto) in enumerate(comun.leer_texto_paginado(ruta_txt)):
        textos.append(texto)
        for m in re.finditer(r"\S+", texto):
            palabra = m.group(0)
            for token in comun.normalizar(palabra).split():
                fichas.append((token, palabra, pagina, (k, m.start(), m.end())))
    fichas.textos = textos
    return fichas


def fragmento(fichas, inicio, fin):
    """Fragmento con contexto, tal como está en el texto original (con «±»,
    ligaduras y signos); solo se reducen los saltos de línea a espacios."""
    desde = max(0, inicio - CONTEXTO_PALABRAS)
    hasta = min(len(fichas), fin + CONTEXTO_PALABRAS)
    textos = getattr(fichas, "textos", ())
    if not textos or len(fichas[desde]) < 4:  # fichas sin posiciones: palabras sueltas
        palabras, previa = [], None
        for i in range(desde, hasta):
            if fichas[i][1] is not previa:  # una palabra puede dar varios tokens
                palabras.append(("»" if i == inicio else "") + fichas[i][1])
                previa = fichas[i][1]
        texto = " ".join(palabras)
    else:
        def corte(a, b):
            """Texto original desde la ficha a hasta el final de la ficha b."""
            (ka, ia, _), (kb, _, fb) = fichas[a][3], fichas[b][3]
            if ka == kb:
                return textos[ka][ia:fb]
            trozos = [textos[ka][ia:]] + list(textos[ka + 1:kb]) + [textos[kb][:fb]]
            return "\n".join(trozos)
        primera = inicio  # la palabra entera donde empieza el pasaje
        while primera > desde and fichas[primera - 1][3] == fichas[inicio][3]:
            primera -= 1
        texto = (corte(desde, primera - 1) + " " if primera > desde else "") + "»" + \
            corte(primera, hasta - 1)
        # "»" va pegado a la palabra donde empieza el pasaje, aunque el token no
        # sea el primero de esa palabra.
        texto = " ".join(texto.split())
    return ("… " if desde else "") + texto + (" …" if hasta < len(fichas) else "")


def paginas_de(fichas, inicio, fin):
    primera, ultima = fichas[inicio][2], fichas[fin - 1][2]
    return str(primera) if primera == ultima else f"{primera}-{ultima}"


def buscar_exacta(fichas, buscada):
    n, hallazgos = len(buscada), []
    tokens = [f[0] for f in fichas]
    primero = buscada[0]
    for i, token in enumerate(tokens):
        if token == primero and tokens[i:i + n] == buscada:
            hallazgos.append((i, i + n, 1.0))
    return hallazgos


def buscar_aproximada(fichas, buscada, umbral):
    n = len(buscada)
    frase = " ".join(buscada)
    objetivo = Counter(buscada)
    tokens = [f[0] for f in fichas]
    if len(tokens) < n:
        return []
    # 1) criba barata: palabras en común en una ventana de n tokens
    ventana = Counter(tokens[:n])
    candidatos = []
    minimo = max(1, int(n * umbral * 0.6))
    for i in range(0, len(tokens) - n + 1):
        if i:
            ventana[tokens[i - 1]] -= 1
            ventana[tokens[i + n - 1]] += 1
        comunes = sum(min(c, ventana[t]) for t, c in objetivo.items())
        if comunes >= minimo:
            candidatos.append((comunes, i))
    candidatos.sort(reverse=True)
    # 2) similitud de caracteres con ventanas algo más cortas o largas
    holgura = max(1, n // 8)
    hallazgos = []
    for _, i in candidatos[:300]:
        mejor = (0.0, i, i + n)
        for largo in range(max(1, n - holgura), n + holgura + 1):
            for desplazamiento in range(-holgura, holgura + 1):
                ini = i + desplazamiento
                if ini < 0 or ini + largo > len(tokens):
                    continue
                puntaje = SequenceMatcher(None, frase, " ".join(tokens[ini:ini + largo]),
                                          autojunk=False).ratio()
                if puntaje > mejor[0]:
                    mejor = (puntaje, ini, ini + largo)
        if mejor[0] >= umbral:
            hallazgos.append((mejor[1], mejor[2], mejor[0]))
    # quitar solapados, quedarse con el mejor de cada zona
    hallazgos.sort(key=lambda h: -h[2])
    elegidos = []
    for h in hallazgos:
        if all(h[1] <= e[0] or h[0] >= e[1] for e in elegidos):
            elegidos.append(h)
    return elegidos[:5]


def modo_buscar(opciones):
    textos = textos_disponibles(opciones.objetivo)
    if not textos:
        print(f"No se pudo ejecutar: no hay .txt extraídos en {opciones.objetivo}", file=sys.stderr)
        return 2
    buscada = comun.normalizar(opciones.buscar).split()
    if not buscada:
        print("No se pudo ejecutar: la frase buscada está vacía.", file=sys.stderr)
        return 2
    exactas, aproximadas = [], []
    documentos = {txt: fichas_de(txt) for txt in textos}
    # la extracción une "satellite-\ndetected" en "satellitedetected": se prueba
    # también la frase con los guiones internos unidos
    variantes = [buscada]
    unida = comun.normalizar(re.sub(r"(\w)-(\w)", r"\1\2", opciones.buscar)).split()
    if unida != buscada:
        variantes.append(unida)
    for txt, fichas in documentos.items():
        for variante in variantes:
            hallados = buscar_exacta(fichas, variante)
            for ini, fin, puntaje in hallados:
                exactas.append((txt, fichas, ini, fin, puntaje))
            if hallados:
                break
    tipo = "exacta"
    resultados = exactas
    if not exactas and len(buscada) >= 5:
        tipo = "aproximada"
        for txt, fichas in documentos.items():
            for ini, fin, puntaje in buscar_aproximada(fichas, buscada, opciones.umbral):
                aproximadas.append((txt, fichas, ini, fin, puntaje))
        aproximadas.sort(key=lambda r: -r[4])
        resultados = aproximadas[:10]
    salida = [{"fuente": txt.stem + ".pdf", "texto": str(txt), "pagina": paginas_de(fichas, ini, fin),
               "puntaje": round(puntaje, 3), "tipo": tipo, "fragmento": fragmento(fichas, ini, fin)}
              for txt, fichas, ini, fin, puntaje in resultados]
    informe = {"frase": opciones.buscar, "umbral": opciones.umbral, "textos_revisados": len(textos),
               "encontrada": bool(salida), "resultados": salida}
    if len(buscada) < 5 and not exactas:
        informe["aviso"] = "frase de menos de 5 palabras: solo se busca coincidencia exacta"
    if opciones.json:
        print(json.dumps(informe, ensure_ascii=False, indent=2))
    else:
        if not salida:
            print(f"NO ENCONTRADA en {len(textos)} textos (umbral {opciones.umbral}).")
            if informe.get("aviso"):
                print(informe["aviso"])
        for r in salida:
            print(f"{r['tipo'].upper()} {r['puntaje']:.3f} | {r['fuente']} | p. {r['pagina']}\n    {r['fragmento']}\n")
    return 0 if salida else 1


def main():
    comun.salida_utf8()
    analizador = argparse.ArgumentParser(description="Extrae texto paginado de PDF o busca un pasaje.")
    analizador.add_argument("objetivo", help="PDF, carpeta fuentes, carpeta texto o .txt")
    analizador.add_argument("--salida", help="carpeta para los .txt (por defecto <fuentes>/texto)")
    analizador.add_argument("--forzar", action="store_true", help="reextraer aunque el .txt esté al día")
    analizador.add_argument("--buscar", help="frase o pasaje a localizar en los .txt")
    analizador.add_argument("--umbral", type=float, default=0.8)
    analizador.add_argument("--json", action="store_true")
    opciones = analizador.parse_args()
    if not 0 < opciones.umbral <= 1:
        print("No se pudo ejecutar: --umbral debe estar entre 0 y 1.", file=sys.stderr)
        sys.exit(2)
    sys.exit(modo_buscar(opciones) if opciones.buscar else modo_extraer(opciones))


if __name__ == "__main__":
    main()
