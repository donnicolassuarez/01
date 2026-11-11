# -*- coding: utf-8 -*-
"""Búsqueda académica en OpenAlex, Crossref, Semantic Scholar y arXiv.

Uso:
  python buscar_academico.py "consulta" [--max N] [--desde AAAA] [--hasta AAAA]
         [--idioma es|en|pt] [--solo-abierto] [--scielo]
         [--bases openalex,crossref,s2,arxiv] [--json] [--salida archivo.json]

--max es el número de resultados pedidos a CADA base (por defecto 20).
Los resultados se unen por DOI o, sin DOI, por título normalizado + año.
Orden: primero los que aparecen en más bases, luego por número de citas.

Claves (variables de entorno, opcionales):
  OPENALEX_API_KEY  OpenAlex exige clave gratuita desde 2026; se envía como
                    cabecera "Authorization: Bearer". Sin ella se intenta
                    igual y, si OpenAlex la rechaza, se informa como base con
                    error y se sigue con las demás.
  S2_API_KEY        Semantic Scholar (cabecera x-api-key). Sin clave suele
                    responder 429; se reintenta con espera y, si sigue, se
                    informa.
  AGENTE_ACADEMICO_CORREO  si existe, se añade como mailto a Crossref.

SciELO: no se consulta search.scielo.org (tiene control antibots y no se
fuerza). Cada resultado lleva `scielo: true` si su enlace o su página de
destino está en un dominio scielo (scielo.br, scielo.org.bo, scielo.cl...).
Con --scielo:
  * a Crossref se le pide `filter=member:530,member:2516,member:2868`
    (los tres miembros de Crossref que son SciELO: Brasil/FapUNIFESP con
    prefijo 10.1590, Chile/ANID con 10.4067 y España). Comprobado: con la
    consulta de prueba devuelve casi solo páginas scielo.br y scielo.cl;
  * los resultados de todas las bases se restringen a los marcados scielo.
Límite conocido: las revistas de SciELO Bolivia (y otras nacionales)
registran sus DOI por su cuenta y el DOI apunta al sitio de la revista, no a
scielo.org.bo; esos artículos aparecen en la búsqueda normal pero no quedan
marcados como scielo. OpenAlex sí puede marcarlos si lista una ubicación
scielo entre sus `locations`.

Idioma: OpenAlex lo informa; arXiv y Crossref casi nunca. Con --idioma, a
OpenAlex se le pasa como filtro y en las demás bases se descarta un
resultado solo si su idioma (declarado o deducido de palabras vacías del
título) es claramente otro.

Códigos de salida: 0 sin problemas; 1 alguna base falló o no hubo
resultados; 2 fallaron todas las bases o los argumentos son inválidos.
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET

import comun

BASES = ("openalex", "crossref", "s2", "arxiv")
NOMBRE_BASE = {"openalex": "OpenAlex", "crossref": "Crossref",
               "s2": "Semantic Scholar", "arxiv": "arXiv"}
MIEMBROS_SCIELO_CROSSREF = ("530", "2516", "2868")
PATRON_SCIELO = re.compile(r"https?://[^/\s]*scielo[^/\s]*", re.I)
PALABRAS_VACIAS = {
    "es": {"el", "la", "los", "las", "de", "del", "y", "en", "para", "por",
           "con", "una", "un", "sobre", "entre", "como", "su", "sus", "al"},
    "en": {"the", "of", "and", "in", "for", "on", "with", "a", "an", "to",
           "from", "by", "its", "using", "between", "at"},
    "pt": {"o", "a", "os", "as", "de", "do", "da", "dos", "das", "e", "em",
           "para", "por", "com", "uma", "um", "no", "na", "nos", "nas", "ao"},
}


# ---------------------------------------------------------------- utilidades

def autor_formateado(apellido, nombre):
    """('Pérez Gómez', 'Juan Carlos') -> 'Pérez Gómez, J. C.'"""
    apellido = (apellido or "").strip()
    iniciales = " ".join(p[0].upper() + "." for p in re.split(r"[\s.\-]+", nombre or "") if p)
    if not apellido:
        return iniciales or None
    return f"{apellido}, {iniciales}" if iniciales else apellido


def autor_desde_nombre_completo(nombre):
    """'Juan Carlos Pérez' -> 'Pérez, J. C.' (última palabra como apellido)."""
    partes = (nombre or "").strip().split()
    if not partes:
        return None
    if len(partes) == 1:
        return partes[0]
    return autor_formateado(partes[-1], " ".join(partes[:-1]))


def es_scielo(*urls):
    return any(u and PATRON_SCIELO.match(u) for u in urls)


def idioma_probable(titulo):
    """Deducción grosera es/en/pt por palabras vacías del título; None si duda."""
    palabras = comun.normalizar(titulo).split()
    if len(palabras) < 4:
        return None
    cuentas = {idi: sum(p in vacias for p in palabras) for idi, vacias in PALABRAS_VACIAS.items()}
    mejor = max(cuentas, key=cuentas.get)
    orden = sorted(cuentas.values(), reverse=True)
    return mejor if orden[0] >= 2 and orden[0] > orden[1] else None


def registro(**campos):
    base = {"titulo": None, "autores": [], "anio": None, "doi": None, "tipo": None,
            "revista_o_fuente": None, "idioma": None, "citas": None,
            "enlace_abierto": None, "url": None, "bases": [], "scielo": False}
    base.update(campos)
    if base["doi"]:
        base["doi"] = comun.limpiar_doi(base["doi"])
    base["titulo"] = re.sub(r"\s+", " ", base["titulo"] or "").strip() or None
    return base


# ------------------------------------------------------------------- bases

def buscar_openalex(consulta, opciones):
    filtros = []
    if opciones.desde or opciones.hasta:
        filtros.append(f"publication_year:{opciones.desde or ''}-{opciones.hasta or ''}")
    if opciones.idioma:
        filtros.append(f"language:{opciones.idioma}")
    if opciones.solo_abierto:
        filtros.append("is_oa:true")
    parametros = {"search": consulta, "per-page": str(min(opciones.max, 200))}
    if filtros:
        parametros["filter"] = ",".join(filtros)
    cabeceras = {}
    clave = os.environ.get("OPENALEX_API_KEY", "").strip()
    if clave:
        cabeceras["Authorization"] = f"Bearer {clave}"
    datos = comun.pedir_json("https://api.openalex.org/works?" + urllib.parse.urlencode(parametros),
                             cabeceras)
    salida = []
    for obra in datos.get("results", []):
        primaria = obra.get("primary_location") or {}
        fuente = (primaria.get("source") or {}).get("display_name")
        mejor_oa = obra.get("best_oa_location") or {}
        enlace = mejor_oa.get("pdf_url") or (obra.get("open_access") or {}).get("oa_url")
        urls = [primaria.get("landing_page_url"), enlace]
        for ubicacion in obra.get("locations") or []:
            urls += [ubicacion.get("landing_page_url"), ubicacion.get("pdf_url")]
        autores = []
        for autoria in obra.get("authorships") or []:
            nombre = (autoria.get("author") or {}).get("display_name")
            if nombre:
                autores.append(autor_desde_nombre_completo(nombre))
        salida.append(registro(
            titulo=obra.get("title") or obra.get("display_name"), autores=autores,
            anio=obra.get("publication_year"), doi=obra.get("doi"), tipo=obra.get("type"),
            revista_o_fuente=fuente, idioma=obra.get("language"),
            citas=obra.get("cited_by_count"), enlace_abierto=enlace,
            url=primaria.get("landing_page_url") or obra.get("doi") or obra.get("id"),
            scielo=es_scielo(*urls)))
    return salida


def buscar_crossref(consulta, opciones):
    parametros = {"query.bibliographic": consulta, "rows": str(min(opciones.max, 1000))}
    filtros = []
    if opciones.desde:
        filtros.append(f"from-pub-date:{opciones.desde}")
    if opciones.hasta:
        filtros.append(f"until-pub-date:{opciones.hasta}-12-31")
    if opciones.scielo:
        filtros += [f"member:{m}" for m in MIEMBROS_SCIELO_CROSSREF]
    if filtros:
        parametros["filter"] = ",".join(filtros)
    if comun.correo_contacto():
        parametros["mailto"] = comun.correo_contacto()
    datos = comun.pedir_json("https://api.crossref.org/works?" + urllib.parse.urlencode(parametros))
    salida = []
    for obra in datos.get("message", {}).get("items", []):
        if obra.get("type") == "component":  # material suplementario (.s001...)
            continue
        partes = ((obra.get("issued") or {}).get("date-parts") or [[None]])[0]
        destino = ((obra.get("resource") or {}).get("primary") or {}).get("URL")
        licencias = " ".join(l.get("URL", "") for l in obra.get("license") or [])
        pdfs = [l.get("URL") for l in obra.get("link") or []
                if l.get("content-type") == "application/pdf"]
        enlace = None
        if "creativecommons.org" in licencias:  # licencia abierta declarada
            enlace = pdfs[0] if pdfs else destino
        if es_scielo(destino):  # SciELO es acceso abierto por definición
            enlace = enlace or destino
        autores = [autor_formateado(a.get("family"), a.get("given")) or a.get("name")
                   for a in obra.get("author") or []]
        salida.append(registro(
            titulo=(obra.get("title") or [None])[0], autores=[a for a in autores if a],
            anio=partes[0] if partes else None, doi=obra.get("DOI"), tipo=obra.get("type"),
            revista_o_fuente=(obra.get("container-title") or [None])[0] or obra.get("publisher"),
            idioma=obra.get("language"), citas=obra.get("is-referenced-by-count"),
            enlace_abierto=enlace, url=destino or obra.get("URL"),
            scielo=es_scielo(destino, *pdfs)))
    return salida


def buscar_s2(consulta, opciones):
    parametros = {"query": consulta, "limit": str(min(opciones.max, 100)),
                  "fields": "title,authors,year,externalIds,publicationTypes,venue,"
                            "citationCount,openAccessPdf,url,isOpenAccess,journal"}
    if opciones.desde or opciones.hasta:
        parametros["year"] = f"{opciones.desde or ''}-{opciones.hasta or ''}"
    if opciones.solo_abierto:
        parametros["openAccessPdf"] = ""
    cabeceras = {}
    clave = os.environ.get("S2_API_KEY", "").strip()
    if clave:
        cabeceras["x-api-key"] = clave
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(parametros)
    datos = comun.pedir_json(url, cabeceras, intentos=4, espera=3.0)
    salida = []
    for obra in datos.get("data") or []:
        ids = obra.get("externalIds") or {}
        doi = ids.get("DOI") or (f"10.48550/arXiv.{ids['ArXiv']}" if ids.get("ArXiv") else None)
        pdf = (obra.get("openAccessPdf") or {}).get("url") or None
        salida.append(registro(
            titulo=obra.get("title"),
            autores=[a for a in (autor_desde_nombre_completo(x.get("name")) for x in obra.get("authors") or []) if a],
            anio=obra.get("year"), doi=doi,
            tipo=", ".join(obra.get("publicationTypes") or []) or None,
            revista_o_fuente=(obra.get("journal") or {}).get("name") or obra.get("venue") or None,
            citas=obra.get("citationCount"), enlace_abierto=pdf, url=obra.get("url"),
            scielo=es_scielo(pdf)))
    return salida


def buscar_arxiv(consulta, opciones):
    palabras = [p for p in re.findall(r"\w+", consulta) if len(p) > 2]
    expresion = " AND ".join(f"all:{p}" for p in palabras) or f"all:{consulta}"
    if opciones.desde or opciones.hasta:
        expresion += (f" AND submittedDate:[{opciones.desde or 1990}01010000"
                      f" TO {opciones.hasta or 2100}12312359]")
    parametros = {"search_query": expresion, "start": "0",
                  "max_results": str(min(opciones.max, 200)), "sortBy": "relevance"}
    datos, _, _ = comun.pedir("https://export.arxiv.org/api/query?" + urllib.parse.urlencode(parametros),
                              espera=3.0)
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    raiz = ET.fromstring(datos)
    salida = []
    for entrada in raiz.findall("a:entry", ns):
        identificador = (entrada.findtext("a:id", "", ns) or "").rsplit("/abs/", 1)[-1]
        base_id = re.sub(r"v\d+$", "", identificador)
        doi_revista = entrada.findtext("arxiv:doi", None, ns)
        pdf = None
        for enlace in entrada.findall("a:link", ns):
            if enlace.get("title") == "pdf" or enlace.get("type") == "application/pdf":
                pdf = enlace.get("href")
        publicado = entrada.findtext("a:published", "", ns)
        revista = entrada.findtext("arxiv:journal_ref", None, ns)
        salida.append(registro(
            titulo=entrada.findtext("a:title", "", ns),
            autores=[a for a in (autor_desde_nombre_completo(x.findtext("a:name", "", ns))
                                 for x in entrada.findall("a:author", ns)) if a],
            anio=int(publicado[:4]) if publicado[:4].isdigit() else None,
            doi=doi_revista or f"10.48550/arXiv.{base_id}",
            tipo="preprint", revista_o_fuente=revista or "arXiv",
            enlace_abierto=pdf or f"https://arxiv.org/pdf/{base_id}",
            url=f"https://arxiv.org/abs/{base_id}"))
    return salida


BUSCADORES = {"openalex": buscar_openalex, "crossref": buscar_crossref,
              "s2": buscar_s2, "arxiv": buscar_arxiv}


# -------------------------------------------------------------- unión

def clave_titulo(reg):
    titulo = comun.normalizar(reg["titulo"])
    return f"t:{titulo}|{reg['anio']}" if titulo else None


def fusionar(destino, nuevo):
    for campo in ("titulo", "doi", "tipo", "revista_o_fuente", "idioma", "url", "anio"):
        if not destino[campo] and nuevo[campo]:
            destino[campo] = nuevo[campo]
    if len(nuevo["autores"]) > len(destino["autores"]):
        destino["autores"] = nuevo["autores"]
    if nuevo["citas"] is not None:
        destino["citas"] = max(destino["citas"] or 0, nuevo["citas"])
    actual = destino["enlace_abierto"]
    if nuevo["enlace_abierto"] and (not actual or (not actual.lower().endswith(".pdf")
                                                   and nuevo["enlace_abierto"].lower().endswith(".pdf"))):
        destino["enlace_abierto"] = nuevo["enlace_abierto"]
    destino["scielo"] = destino["scielo"] or nuevo["scielo"]
    for base in nuevo["bases"]:
        if base not in destino["bases"]:
            destino["bases"].append(base)


def unir(registros):
    """Une por DOI; por título + año solo si a uno de los dos le falta DOI.

    Dos registros con DOI distintos nunca se unen (preprint y artículo
    publicado el mismo año son obras distintas para citar).
    """
    unidos, indice = [], {}
    for reg in registros:
        claves = [k for k in (f"d:{reg['doi']}" if reg["doi"] else None, clave_titulo(reg)) if k]
        existente = None
        for k in claves:
            candidato = indice.get(k)
            if candidato is not None and (k.startswith("d:") or not (candidato["doi"] and reg["doi"])):
                existente = candidato
                break
        if existente is None:
            unidos.append(reg)
            existente = reg
        else:
            fusionar(existente, reg)
        for k in claves + [k for k in (f"d:{existente['doi']}" if existente["doi"] else None,
                                       clave_titulo(existente)) if k]:
            indice.setdefault(k, existente)
    return unidos


def filtrar(registros, opciones):
    salida = []
    for reg in registros:
        if reg["anio"] and ((opciones.desde and reg["anio"] < opciones.desde)
                            or (opciones.hasta and reg["anio"] > opciones.hasta)):
            continue
        if opciones.idioma:
            idioma = (reg["idioma"] or "")[:2].lower() or idioma_probable(reg["titulo"])
            if idioma and idioma != opciones.idioma:
                continue
        if opciones.solo_abierto and not reg["enlace_abierto"]:
            continue
        if opciones.scielo and not reg["scielo"]:
            continue
        salida.append(reg)
    salida.sort(key=lambda r: (-len(r["bases"]), -(r["citas"] or 0), r["titulo"] or ""))
    return salida


# ------------------------------------------------------------- presentación

def tabla(resultado):
    lineas = []
    for n, reg in enumerate(resultado["resultados"], 1):
        autores = reg["autores"][0] + (" et al." if len(reg["autores"]) > 1 else "") if reg["autores"] else "s/a"
        marcas = []
        if reg["enlace_abierto"]:
            marcas.append("OA")
        if reg["scielo"]:
            marcas.append("SciELO")
        lineas.append(f"{n:>3}. [{reg['anio'] or 's.f.'}] {reg['titulo'] or '(sin título)'}")
        lineas.append(f"     {autores} | {reg['revista_o_fuente'] or '-'} | {reg['tipo'] or '-'}"
                      f"{' | idioma ' + reg['idioma'] if reg['idioma'] else ''}")
        lineas.append(f"     DOI: {reg['doi'] or '-'} | citas: {reg['citas'] if reg['citas'] is not None else '-'}"
                      f" | bases: {', '.join(reg['bases'])}{' | ' + ' '.join(marcas) if marcas else ''}")
        if reg["enlace_abierto"]:
            lineas.append(f"     abierto: {reg['enlace_abierto']}")
    lineas.append("")
    lineas.append(f"Total: {resultado['total']} resultados únicos "
                  f"({resultado['recibidos']} recibidos antes de unir y filtrar).")
    for base, cantidad in resultado["por_base"].items():
        lineas.append(f"  {NOMBRE_BASE[base]}: {cantidad}")
    if resultado["bases_con_error"]:
        lineas.append("Bases con error: " + "; ".join(
            f"{NOMBRE_BASE[b]} ({m})" for b, m in resultado["bases_con_error"].items()))
    return "\n".join(lineas)


def main():
    comun.salida_utf8()
    analizador = argparse.ArgumentParser(description="Búsqueda en bases académicas abiertas.")
    analizador.add_argument("consulta")
    analizador.add_argument("--max", type=int, default=20, help="resultados por base")
    analizador.add_argument("--desde", type=int)
    analizador.add_argument("--hasta", type=int)
    analizador.add_argument("--idioma", choices=("es", "en", "pt"))
    analizador.add_argument("--solo-abierto", action="store_true")
    analizador.add_argument("--scielo", action="store_true",
                            help="solo resultados alojados en SciELO (ver límites en la ayuda del módulo)")
    analizador.add_argument("--bases", default=",".join(BASES))
    analizador.add_argument("--json", action="store_true")
    analizador.add_argument("--salida", help="guarda el JSON en este archivo")
    opciones = analizador.parse_args()

    bases = [b.strip().lower() for b in opciones.bases.split(",") if b.strip()]
    desconocidas = [b for b in bases if b not in BUSCADORES]
    if desconocidas or not bases or opciones.max < 1 or not opciones.consulta.strip():
        print(f"Argumentos inválidos. Bases válidas: {', '.join(BASES)}.", file=sys.stderr)
        sys.exit(2)

    recibidos, errores, por_base = [], {}, {}
    for base in bases:
        try:
            hallados = BUSCADORES[base](opciones.consulta, opciones)
        except comun.ErrorRed as error:
            errores[base] = str(error)
            continue
        except Exception as error:  # respuesta inesperada, XML roto, etc.
            errores[base] = f"{type(error).__name__}: {error}"
            continue
        for reg in hallados:
            reg["bases"] = [base]
        por_base[base] = len(hallados)
        recibidos.extend(hallados)

    resultados = filtrar(unir(recibidos), opciones)
    resultado = {
        "consulta": opciones.consulta,
        "filtros": {"desde": opciones.desde, "hasta": opciones.hasta, "idioma": opciones.idioma,
                    "solo_abierto": opciones.solo_abierto, "scielo": opciones.scielo,
                    "max_por_base": opciones.max},
        "bases_consultadas": bases, "por_base": por_base, "bases_con_error": errores,
        "recibidos": len(recibidos), "total": len(resultados), "resultados": resultados,
    }
    texto_json = json.dumps(resultado, ensure_ascii=False, indent=2)
    if opciones.salida:
        comun.escribir_atomico(opciones.salida, texto_json + "\n")
    print(texto_json if opciones.json else tabla(resultado))

    if len(errores) == len(bases):
        sys.exit(2)
    sys.exit(1 if errores or not resultados else 0)


if __name__ == "__main__":
    main()
