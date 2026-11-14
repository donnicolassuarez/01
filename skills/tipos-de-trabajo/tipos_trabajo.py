# -*- coding: utf-8 -*-
"""Lectura de tipos.json: la definición única de cada tipo de trabajo.

Lo usan construir_docx.py y verificar_formato.py. Solo biblioteca estándar.

  cargar(ruta)                      -> definiciones validadas (ErrorTipos si no)
  resolver(defs, texto)             -> clave del tipo por nombre o sinónimo, o None
  estructura(defs, clave, variante) -> estructura efectiva (tipo + variante)
  buscar_secciones(est, titulos)    -> presencia, nivel y orden de las secciones
  buscar_previos(est, parrafos)     -> índice, resumen y palabras clave

Comparación de encabezados (sin tildes, mayúsculas ni signos):
  solo = true   el encabezado es exactamente una de las variantes.
  solo = false  además se acepta con numeración delante ("Capítulo II.",
                "2.", "II.") y con texto detrás ("Conclusiones y
                recomendaciones" vale por "Conclusiones").
  nivel = 1|2|3 el encabezado debe tener ese nivel; null = cualquiera.
  orden = false la sección se exige pero no entra en la comprobación de orden.
Una sección con "capitulos": true se cumple con al menos "minimo" títulos
numerados como capítulo ("Capítulo I", "Capítulo 1", "I.", "1.").
"""
import json
import re
import unicodedata

PORTADAS = ("blanca", "datos", "ninguna")
ESTADOS = ("obligatorio", "opcional", "no")
NIVELES_ACADEMICOS = ("pregrado", "maestria", "doctorado", "postdoctorado")
PREVIOS = ("indice", "resumen", "palabras_clave")
FINALES = ("referencias", "anexos")
CLAVES_TIPO = ("nombre", "sinonimos", "fuente", "portada", "capitulos", "secciones",
               "opcionales", "previos", "finales", "extension", "por_nivel", "variantes")
CLAVES_VARIANTE = ("descripcion", "fuente", "portada", "capitulos", "secciones",
                   "opcionales", "previos", "finales")

PATRON_CAPITULO = re.compile(r"^capitulo\s+([ivxlc]+|\d+)\b")
PATRON_NUMERO = re.compile(r"^(?:[ivx]+|\d+(?:\s\d+)*)\s+(?=\S)")
PATRON_CAPITULO_NUMERO = re.compile(r"^(?:[ivx]+|\d+)\s+[a-z]")  # "II Marco", "2 Marco"; no "2 1 ..."


class ErrorTipos(Exception):
    """tipos.json ilegible o con un esquema que no se puede usar."""


def normalizar(texto):
    """Minúsculas, sin tildes ni signos; espacios simples (igual que comun.py)."""
    texto = unicodedata.normalize("NFKD", (texto or "").lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", texto)).strip()


def sin_numeracion(texto_normalizado):
    """Quita "capitulo ii", "2 1" o "iii" del comienzo de un encabezado normalizado."""
    texto = re.sub(r"^(?:capitulo|cap|parte)\s+(?:[ivxlc]+|\d+)\s*", "", texto_normalizado)
    if texto != texto_normalizado:
        return texto
    return PATRON_NUMERO.sub("", texto_normalizado)


def es_capitulo(texto_normalizado):
    return bool(PATRON_CAPITULO.match(texto_normalizado) or
                PATRON_CAPITULO_NUMERO.match(texto_normalizado))


# ---------------------------------------------------------------------------
# Carga y validación

def _validar_seccion(s, donde, obligatoria):
    if not isinstance(s, dict):
        raise ErrorTipos(f"{donde}: cada sección debe ser un objeto")
    for campo in ("clave", "nombre"):
        if not isinstance(s.get(campo), str) or not s[campo].strip():
            raise ErrorTipos(f"{donde}: falta «{campo}» (texto)")
    donde = f"{donde} «{s['nombre']}»"
    if s.get("capitulos"):
        if not obligatoria:
            raise ErrorTipos(f"{donde}: «capitulos» solo vale en secciones obligatorias")
        if not isinstance(s.get("minimo", 1), int) or s.get("minimo", 1) < 1:
            raise ErrorTipos(f"{donde}: «minimo» debe ser un entero mayor que 0")
    else:
        variantes = s.get("variantes")
        if not isinstance(variantes, list) or not variantes or \
                not all(isinstance(v, str) and normalizar(v) for v in variantes):
            raise ErrorTipos(f"{donde}: «variantes» debe ser una lista de textos no vacía")
    if obligatoria:
        if "solo" in s and not isinstance(s["solo"], bool):
            raise ErrorTipos(f"{donde}: «solo» debe ser true o false")
        if s.get("nivel") not in (None, 1, 2, 3):
            raise ErrorTipos(f"{donde}: «nivel» debe ser 1, 2, 3 o null")
        if "orden" in s and not isinstance(s["orden"], bool):
            raise ErrorTipos(f"{donde}: «orden» debe ser true o false")


def _validar_estructura(t, donde, completa):
    claves = CLAVES_TIPO if completa else CLAVES_VARIANTE
    desconocidas = [k for k in t if k not in claves]
    if desconocidas:
        raise ErrorTipos(f"{donde}: campos desconocidos {desconocidas}")
    if completa:
        faltan = [k for k in ("nombre", "portada", "secciones", "previos", "finales") if k not in t]
        if faltan:
            raise ErrorTipos(f"{donde}: faltan los campos {faltan}")
    if "portada" in t and t["portada"] not in PORTADAS:
        raise ErrorTipos(f"{donde}: «portada» debe ser una de {list(PORTADAS)}")
    if "capitulos" in t and not isinstance(t["capitulos"], bool):
        raise ErrorTipos(f"{donde}: «capitulos» debe ser true o false")
    for campo, obligatoria in (("secciones", True), ("opcionales", False)):
        if campo in t:
            if not isinstance(t[campo], list):
                raise ErrorTipos(f"{donde}: «{campo}» debe ser una lista")
            vistas = set()
            for s in t[campo]:
                _validar_seccion(s, f"{donde}, {campo}", obligatoria)
                if s["clave"] in vistas:
                    raise ErrorTipos(f"{donde}: clave de sección repetida «{s['clave']}»")
                vistas.add(s["clave"])
    for campo, permitidas in (("previos", PREVIOS), ("finales", FINALES)):
        if campo in t:
            valor = t[campo]
            if not isinstance(valor, dict) or any(k not in permitidas for k in valor) or \
                    any(v not in ESTADOS for v in valor.values()):
                raise ErrorTipos(f"{donde}: «{campo}» admite {list(permitidas)} con valores "
                                 f"{list(ESTADOS)}")


def cargar(ruta):
    try:
        with open(ruta, encoding="utf-8-sig") as f:
            datos = json.load(f)
    except OSError as error:
        raise ErrorTipos(f"no se pudo leer {ruta}: {error}") from None
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ErrorTipos(f"{ruta} no es JSON válido: {error}") from None
    if not isinstance(datos, dict) or not isinstance(datos.get("tipos"), dict) or not datos["tipos"]:
        raise ErrorTipos(f"{ruta}: falta el objeto «tipos»")
    previos = datos.get("elementos_previos")
    if not isinstance(previos, dict) or any(k not in previos for k in PREVIOS):
        raise ErrorTipos(f"{ruta}: «elementos_previos» debe definir {list(PREVIOS)}")
    for clave, previo in previos.items():
        _validar_seccion(dict(previo, clave=clave), f"elementos_previos.{clave}", False)
    indice = {}
    for clave, t in datos["tipos"].items():
        donde = f"tipo «{clave}»"
        if clave != normalizar(clave).replace(" ", "_") or not isinstance(t, dict):
            raise ErrorTipos(f"{donde}: la clave debe ir en minúsculas sin tildes y su valor ser un objeto")
        _validar_estructura(t, donde, True)
        if not isinstance(t.get("variantes", {}), dict):
            raise ErrorTipos(f"{donde}: «variantes» debe ser un objeto")
        for nombre_v, v in t.get("variantes", {}).items():
            if not isinstance(v, dict):
                raise ErrorTipos(f"{donde}, variante «{nombre_v}»: debe ser un objeto")
            _validar_estructura(v, f"{donde}, variante «{nombre_v}»", False)
        extension = t.get("extension", {})
        if not isinstance(extension, dict) or any(k not in NIVELES_ACADEMICOS for k in extension):
            raise ErrorTipos(f"{donde}: «extension» admite {list(NIVELES_ACADEMICOS)}")
        for nivel, rango in extension.items():
            if rango is not None and not (isinstance(rango, list) and len(rango) == 2 and
                                          all(isinstance(n, int) for n in rango) and rango[0] <= rango[1]):
                raise ErrorTipos(f"{donde}: «extension.{nivel}» debe ser [mínimo, máximo] o null")
        for nombre in [clave, t["nombre"]] + list(t.get("sinonimos", [])):
            n = normalizar(nombre)
            if indice.get(n, clave) != clave:
                raise ErrorTipos(f"{donde}: el nombre o sinónimo «{nombre}» ya es de «{indice[n]}»")
            indice[n] = clave
    datos["_indice"] = indice
    return datos


def tipos_disponibles(defs):
    return list(defs["tipos"])


def resolver(defs, texto):
    """Clave del tipo por clave, nombre o sinónimo (sin tildes ni mayúsculas)."""
    n = normalizar(texto)
    return defs["_indice"].get(n) or defs["_indice"].get(n.replace("_", " "))


def estructura(defs, clave, variante=None):
    """Tipo con la variante aplicada encima. ErrorTipos si la variante no existe."""
    t = defs["tipos"][clave]
    resultado = {k: t.get(k) for k in CLAVES_TIPO if k != "variantes"}
    resultado.update(clave=clave, variante=None)
    resultado.setdefault("opcionales", [])
    if variante:
        nombre_v = normalizar(variante).replace(" ", "_")
        if nombre_v not in t.get("variantes", {}):
            disponibles = ", ".join(t.get("variantes", {})) or "ninguna"
            raise ErrorTipos(f"el tipo «{clave}» no tiene la variante «{variante}» "
                             f"(variantes: {disponibles})")
        for campo, valor in t["variantes"][nombre_v].items():
            if campo in ("previos", "finales"):
                resultado[campo] = dict(resultado[campo], **valor)
            else:
                resultado[campo] = valor
        resultado["variante"] = nombre_v
    resultado["elementos_previos"] = defs["elementos_previos"]
    return resultado


# ---------------------------------------------------------------------------
# Comparación

def coincide(texto_normalizado, seccion):
    """¿El encabezado (ya normalizado) corresponde a la sección?"""
    if seccion.get("capitulos"):
        return es_capitulo(texto_normalizado)
    variantes = [normalizar(v) for v in seccion["variantes"]]
    if texto_normalizado in variantes:
        return True
    if seccion.get("solo", True):
        return False
    resto = sin_numeracion(texto_normalizado)
    return any(resto == v or resto.startswith(v + " ") for v in variantes)


def parecido(texto, seccion):
    """Párrafo que parece la sección sin serlo (p. ej. «INTRODUCCIÓN» sin
    estilo de título, o «Introducción al tema»): comienza como alguna variante."""
    if seccion.get("capitulos"):
        return False
    n = normalizar(texto)
    if not seccion.get("solo", True):
        n = sin_numeracion(n)
    return any(n.startswith(normalizar(v)[:10]) for v in seccion["variantes"])


def lista_nombres(nombres):
    nombres = list(nombres)
    if len(nombres) <= 1:
        return "".join(nombres)
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


def buscar_secciones(est, titulos):
    """titulos: lista de dicts {"pos", "nivel", "texto"} en orden del documento.

    Devuelve {"secciones": [{"seccion", "estado", "pos", "nivel", "titulo",
    "cantidad"}], "fuera_de_orden": [(seccion, pos, seccion_previa, pos_previa)]}.
    estado: "ok", "falta" o "nivel" (solo está con otro nivel).
    """
    resultado = []
    for seccion in est["secciones"]:
        candidatos = [t for t in titulos if coincide(normalizar(t["texto"]), seccion)]
        nivel = seccion.get("nivel")
        validos = [t for t in candidatos if nivel is None or t["nivel"] == nivel]
        fila = {"seccion": seccion, "estado": "ok", "pos": None, "nivel": None,
                "titulo": None, "cantidad": len(validos)}
        if seccion.get("capitulos") and len(validos) < seccion.get("minimo", 1):
            fila["estado"] = "falta" if not candidatos else "nivel"
            if candidatos:
                fila.update(pos=candidatos[0]["pos"], nivel=candidatos[0]["nivel"], titulo=candidatos[0])
        elif validos:
            fila.update(pos=validos[0]["pos"], nivel=validos[0]["nivel"], titulo=validos[0])
        elif candidatos:
            fila.update(estado="nivel", pos=candidatos[0]["pos"], nivel=candidatos[0]["nivel"],
                        titulo=candidatos[0])
        else:
            fila["estado"] = "falta"
        resultado.append(fila)
    fuera = []
    mayor = None
    for fila in resultado:
        if fila["estado"] != "ok" or fila["seccion"].get("orden", True) is False:
            continue
        if mayor is not None and fila["pos"] < mayor["pos"]:
            fuera.append((fila["seccion"], fila["titulo"], mayor["seccion"], mayor["titulo"]))
        elif mayor is None or fila["pos"] >= mayor["pos"]:
            mayor = fila
    return {"secciones": resultado, "fuera_de_orden": fuera}


def orden_esperado(est):
    return lista_nombres(s["nombre"] for s in est["secciones"] if s.get("orden", True) is not False)


def buscar_previos(est, parrafos):
    """parrafos: dicts {"pos", "texto", "titulo" (bool), "indice" (bool)}.

    Devuelve {previo: {"estado": obligatorio|opcional|no, "pos": int|None,
    "nombre": str}} para índice, resumen y palabras clave.
    """
    resultado = {}
    for clave in PREVIOS:
        definicion = est["elementos_previos"][clave]
        variantes = [normalizar(v) for v in definicion["variantes"]]
        pos = None
        for p in parrafos:
            n = normalizar(p["texto"])
            if not n:
                continue
            if clave == "indice" and p.get("indice"):
                pos = p["pos"]
            elif n in variantes and (p.get("titulo") or len(n) < 40):
                pos = p["pos"]
            elif clave != "indice" and re.match(
                    r"^\W*(" + "|".join(re.escape(v) for v in definicion["variantes"]) + r")\s*[:.]",
                    p["texto"], re.I):
                pos = p["pos"]
            if pos is not None:
                break
        resultado[clave] = {"estado": est["previos"].get(clave, "no"), "pos": pos,
                            "nombre": definicion["nombre"]}
    return resultado


def extension(est, nivel):
    """Rango orientativo [min, max] para el nivel, o None."""
    return (est.get("extension") or {}).get(normalizar(nivel or "pregrado"))
