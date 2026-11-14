# -*- coding: utf-8 -*-
"""Inicio, diagnóstico y bitácora de un encargo académico.

Uso:
  python encargo.py nuevo --tema "..." [--tipo ensayo] [--nivel pregrado]
         [--paginas 5 | 8-10] [--categoria nombre] [--carpeta nombre]
         [--para don_nico|jota] [--materia ...] [--docente ...]
         [--fecha-entrega AAAA-MM-DD] [--formato docx] [--con-revisor]
         [--nota "..."]
  python encargo.py estado <carpeta>        (también: retomar <carpeta>)
  python encargo.py anotar <carpeta> "texto" [--estado valor] [--vuelta]
  python encargo.py listar [--para ...] [--estado ...]
Todos aceptan --raiz <carpeta> y --json.

Raíz de los trabajos: --raiz, o la variable ENCARGOS_RAIZ, o
~/Desktop/JP/ACADEMIA_CLAUDE/08_PRODUCCION_ACADEMICA. Cada encargo vive
en <raíz>/<destinatario>/trabajos/<categoría>/<carpeta>/, con
encargo.md, fuentes/, borrador/ y entrega/. Destinatario: don_nico
(por defecto) o jota. Categoría por defecto: el tipo en plural.

<carpeta> en estado, retomar y anotar: una ruta, o una parte del nombre
de la carpeta que se busca bajo la raíz (si hay varias, sale con 2 y
las lista).

encargo.md: un bloque de líneas "clave: valor" (tema, tipo, nivel,
paginas, formato, estado y, si se dan, revisor, para, categoria,
materia, docente, fecha_entrega, creado), que leen control_final.py y
el hook bloqueo_entrega.py, y una sección "## Bitácora" con una línea
fechada por evento. Una línea de bitácora que empieza por "vuelta N:"
(la escribe `anotar --vuelta`) cuenta como vuelta de corrección; el
máximo son tres.

estado: deduce la etapa de los archivos reales (no de lo que dice
encargo.md), señala incoherencias y termina con "SIGUIENTE PASO:".
La lectura del dictamen del verificador y de controles.json repite la
lógica de hooks/bloqueo_entrega.py: el hook se instala en otra carpeta
y no se importa.

anotar --estado: en curso | en verificación | aprobado | no aprobado |
suspendido. "aprobado" se rechaza (código 1, sin escribir) si el
diagnóstico no lo sostiene.

Códigos de salida: 0 bien; 1 hay hallazgos o advertencias (estado con
incoherencias, aprobado rechazado, encargo creado sin extensión);
2 no se pudo ejecutar (carpeta inexistente o ya existente, valor
inválido). Solo biblioteca estándar; Windows y Linux.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

import comun

TIPOS = ("ensayo", "monografia", "informe", "articulo", "perfil", "tesis", "otro")
PLURAL = {"ensayo": "ensayos", "monografia": "monografias", "informe": "informes",
          "articulo": "articulos", "perfil": "perfiles", "tesis": "tesis", "otro": "otros"}
NIVELES = ("pregrado", "maestria", "doctorado", "postdoctorado")
DESTINATARIOS = ("don_nico", "jota")
ESTADOS = {"en curso": "en curso", "en verificacion": "en verificación",
           "aprobado": "aprobado", "no aprobado": "no aprobado", "suspendido": "suspendido"}
ABIERTOS = ("en curso", "en verificacion")
CON_TILDE = {"monografia": "monografía", "articulo": "artículo", "maestria": "maestría"}
MAX_VUELTAS = 3
TOLERANCIA_MTIME = 2.0  # segundos, como el hook
RAIZ_POR_DEFECTO = Path("Desktop") / "JP" / "ACADEMIA_CLAUDE" / "08_PRODUCCION_ACADEMICA"
VACIAS = {"de", "del", "la", "las", "el", "los", "y", "e", "o", "u", "en", "a", "al",
          "con", "por", "para", "su", "sus", "un", "una", "unos", "unas", "que", "se",
          "lo", "como", "sobre", "entre", "desde", "hacia", "sin"}
PROHIBIDOS_EN_NOMBRE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
CAMPOS_ORDEN = ("tema", "tipo", "estructura", "nivel", "paginas", "formato", "estado", "revisor", "para",
                "categoria", "materia", "docente", "fecha_entrega", "creado")


class Fallo(Exception):
    """No se pudo ejecutar: código 2."""


# ----------------------------------------------------------------- utilidades

def sin_tildes(texto):
    d = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in d if not unicodedata.combining(c))


def plano(texto):
    """Minúsculas, sin tildes, espacios simples (conserva signos)."""
    return re.sub(r"\s+", " ", sin_tildes(texto).lower()).strip()


def una_linea(texto):
    return re.sub(r"\s+", " ", texto or "").strip()


def ahora():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def sha256_de(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer(ruta):
    with open(ruta, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def escribir(ruta, texto):
    """Escritura atómica que conserva los permisos del archivo anterior."""
    modo = os.stat(ruta).st_mode & 0o777 if os.path.exists(ruta) else 0o644
    comun.escribir_atomico(ruta, texto)
    try:
        os.chmod(ruta, modo)
    except OSError:
        pass


def slug(texto, max_palabras=6, max_largo=50):
    palabras = [p for p in comun.normalizar(texto).split() if p not in VACIAS]
    salida = ""
    for p in palabras[:max_palabras]:
        candidato = (salida + "_" + p) if salida else p
        if len(candidato) > max_largo:
            break
        salida = candidato
    return salida or (palabras[0][:max_largo] if palabras else "")


def nombre_seguro(texto):
    """Nombre de carpeta dado por el usuario: válido en Windows y Linux."""
    nombre = PROHIBIDOS_EN_NOMBRE.sub("_", una_linea(texto)).strip(" .")
    if not nombre or nombre in (".", ".."):
        raise Fallo("nombre de carpeta no válido: «%s»" % texto)
    return nombre


def raiz_de(args):
    if getattr(args, "raiz", None):
        return Path(args.raiz).expanduser()
    if os.environ.get("ENCARGOS_RAIZ", "").strip():
        return Path(os.environ["ENCARGOS_RAIZ"].strip()).expanduser()
    return Path.home() / RAIZ_POR_DEFECTO


def canon_estado(valor):
    v = plano(valor).strip(" .`'\"")
    if v not in ESTADOS:
        raise Fallo("estado no válido: «%s». Valores: %s" % (valor, ", ".join(ESTADOS.values())))
    return ESTADOS[v]


# ----------------------------------------------------------------- encargo.md

def limpiar_linea(linea):
    """Mismo criterio que el hook y control_final.py."""
    return sin_tildes(linea).replace("*", "").replace("_", "").strip(" \t-#>").lower()


def leer_encargo(carpeta):
    """Campos (clave normalizada -> valor original), bitácora y vueltas."""
    texto = leer(carpeta / "encargo.md")
    campos, bitacora = {}, []
    en_bitacora = False
    for linea in texto.splitlines():
        s = linea.strip()
        if s.startswith("#"):
            en_bitacora = plano(s.lstrip("#").strip()) == "bitacora"
            continue
        if en_bitacora:
            if s.startswith(("- ", "* ")):
                bitacora.append(s[2:].strip())
            continue
        m = re.match(r"([a-z ]+?)\s*:\s*(.*)$", limpiar_linea(linea))
        if m and ":" in linea:
            k = m.group(1).replace(" ", "")
            k = {"fechaentrega": "fecha_entrega", "extension": "paginas"}.get(k, k)
            valor = re.sub(r"\s+", " ", linea.split(":", 1)[1]).strip(" *_`.'\"")
            campos.setdefault(k, valor)
    vueltas = [b for b in bitacora if re.match(r"(\d{4}-\d\d-\d\d[ T]\d\d:\d\d\s+)?vuelta\s+\d+\s*:", plano(b))]
    return {"campos": campos, "bitacora": bitacora, "vueltas": len(vueltas), "texto": texto}


def nivel_de(campos):
    v = plano(campos.get("nivel", ""))
    for n in ("postdoctorado", "doctorado", "maestria", "pregrado"):
        if n in v:
            return n
    return "pregrado"


def tipo_de(campos):
    v = plano(campos.get("tipo", ""))
    return next((t for t in TIPOS if re.search(r"\b%s\b" % t, v)), None)


def estado_de(campos):
    return re.sub(r"\s+", " ", plano(campos.get("estado", ""))).strip(" .`'\"")


def generar_encargo_md(campos, nota):
    lineas = ["# Encargo", ""]
    lineas += ["%s: %s" % (k, campos[k]) for k in CAMPOS_ORDEN if campos.get(k)]
    if nota:
        lineas += ["", "## Notas", "- " + una_linea(nota)]
    lineas += ["", "## Bitácora"]
    return "\n".join(lineas) + "\n"


def anadir_bitacora(texto, linea):
    """Añade «- fecha linea» al final de la sección Bitácora (la crea si falta)."""
    lineas = texto.rstrip("\n").split("\n")
    inicio = None
    for i, l in enumerate(lineas):
        if l.strip().startswith("#") and plano(l.strip().lstrip("#").strip()) == "bitacora":
            inicio = i
    nueva = "- %s %s" % (ahora(), una_linea(linea))
    if inicio is None:
        lineas += ["", "## Bitácora", nueva]
    else:
        fin = len(lineas)
        for j in range(inicio + 1, len(lineas)):
            if lineas[j].strip().startswith("#"):
                fin = j
                break
        while fin > inicio + 1 and not lineas[fin - 1].strip():
            fin -= 1
        lineas.insert(fin, nueva)
    return "\n".join(lineas) + "\n"


def poner_estado(texto, valor):
    """Cambia el valor de la primera línea estado: (la que lee el hook)."""
    lineas = texto.split("\n")
    for i, l in enumerate(lineas):
        if re.match(r"estado\s*:", limpiar_linea(l)) and ":" in l:
            izquierda, derecha = l.split(":", 1)
            m = re.match(r"(\s*[*_`]*\s*)(.*?)(\s*[*_`]*\s*)$", derecha)
            lineas[i] = izquierda + ":" + (m.group(1) or " ") + valor + m.group(3)
            return "\n".join(lineas)
    # sin línea estado: va después del último campo del bloque inicial
    pos = 1
    for i, l in enumerate(lineas):
        if l.strip().startswith("## "):
            break
        if re.match(r"[a-z ]+:", limpiar_linea(l)):
            pos = i + 1
    lineas.insert(pos, "estado: " + valor)
    return "\n".join(lineas)


# --------------------------------------- lectura de dictámenes (copia del hook)

RE_NO_APROBADO = re.compile(r"\bno[\s\-_]+aprobado\b", re.IGNORECASE)
RE_APROBADO = re.compile(r"\baprobado\b", re.IGNORECASE)


def veredicto_de(linea):
    no = RE_NO_APROBADO.search(linea)
    si = RE_APROBADO.search(linea)
    if no and (not si or no.start() <= si.start()):
        return "NO APROBADO"
    if si:
        return "APROBADO"
    return None


def leer_dictamen(informe):
    """Último dictamen del informe del verificador (misma lógica que el hook)."""
    lineas = [sin_tildes(l) for l in leer(informe).splitlines()]
    candidatos = []
    for i, l in enumerate(lineas):
        if "dictamen" not in l.lower():
            continue
        v = veredicto_de(l)
        if v is None:
            vistas = 0
            for siguiente in lineas[i + 1:]:
                if not siguiente.strip():
                    continue
                v = veredicto_de(siguiente)
                vistas += 1
                if v or vistas >= 2:
                    break
        if v:
            candidatos.append((i, v))
    if not candidatos:
        for i, l in enumerate(lineas):
            pelada = re.sub(r"[\s*#_\-:>.`]+", " ", l).strip().upper()
            if pelada in ("APROBADO", "NO APROBADO"):
                candidatos.append((i, pelada))
    return candidatos[-1][1] if candidatos else None


def veredicto_revision(linea):
    v = plano(linea)
    if "rehacer" in v:
        return "rehacer"
    if "cambios mayores" in v:
        return "cambios mayores"
    if "cambios menores" in v:
        return "aceptar con cambios menores"
    if re.search(r"\baceptar\b|\baceptado\b", v):
        return "aceptar"
    return None


def leer_dictamen_revision(informe):
    """Dictamen del revisor: aceptar, ... con cambios menores, cambios mayores, rehacer."""
    lineas = leer(informe).splitlines()
    hallado = None
    for i, l in enumerate(lineas):
        if "dictamen" not in plano(l):
            continue
        v = veredicto_revision(l)
        if v is None:
            for siguiente in [x for x in lineas[i + 1:] if x.strip()][:2]:
                v = veredicto_revision(siguiente)
                if v:
                    break
        if v:
            hallado = v
    return hallado


# ----------------------------------------------------------------- diagnóstico

def tiene_contenido(ruta):
    """Existe y tiene algo más que encabezados y líneas en blanco."""
    if not ruta.is_file():
        return False
    return any(l.strip() and not l.strip().startswith("#") for l in leer(ruta).splitlines())


def cuerpo_md(texto):
    m = re.match(r"^\ufeff?---\s*\n.*?\n---\s*\n", texto, re.S)
    return texto[m.end():] if m else texto


def palabras_md(ruta):
    return comun.normalizar(cuerpo_md(leer(ruta))).split()


def palabras_docx(ruta):
    return comun.normalizar(" ".join(comun.leer_parrafos(ruta))).split()


def docx_de(entrega, controles):
    """Lista de .docx de entrega/ (un nivel de subcarpetas) y el principal."""
    docs = []
    if entrega.is_dir():
        for p in sorted(entrega.rglob("*.docx")):
            rel = p.relative_to(entrega)
            if len(rel.parts) <= 2 and not p.name.startswith("~$"):
                docs.append(p)
    principal = None
    if isinstance(controles, dict) and isinstance(controles.get("archivo"), str):
        candidato = entrega / controles["archivo"]
        if candidato in docs:
            principal = candidato
    if principal is None and docs:
        principal = max(docs, key=lambda p: p.stat().st_mtime)
    return docs, principal


def diagnosticar(carpeta):
    carpeta = Path(carpeta)
    enc = leer_encargo(carpeta)
    campos = enc["campos"]
    nivel = nivel_de(campos)
    estado = estado_de(campos)
    revisor_pedido = plano(campos.get("revisor", "")) in ("si", "sí", "yes", "true")
    d = {"carpeta": str(carpeta), "tema": campos.get("tema", ""), "tipo": tipo_de(campos),
         "nivel": nivel, "paginas": campos.get("paginas"), "estado": campos.get("estado", ""),
         "vueltas": enc["vueltas"], "max_vueltas": MAX_VUELTAS,
         "ultima_bitacora": enc["bitacora"][-1] if enc["bitacora"] else None,
         "etapas": {}, "incoherencias": [], "avisos": []}
    if not campos.get("estado"):
        d["avisos"].append("encargo.md no tiene línea «estado:»")
    if not enc["bitacora"]:
        d["avisos"].append("encargo.md no tiene bitácora (formato antiguo): se diagnostica por los archivos")
    fuentes, borrador, entrega = carpeta / "fuentes", carpeta / "borrador", carpeta / "entrega"

    # investigación
    pdfs = [p for p in fuentes.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"] if fuentes.is_dir() else []
    fichas_md, matriz_md = fuentes / "fichas.md", fuentes / "matriz_evidencia.md"
    n_fichas = sum(1 for l in leer(fichas_md).splitlines() if l.startswith("## ")) if fichas_md.is_file() else 0
    filas = []
    if matriz_md.is_file():
        filas = [l for l in leer(matriz_md).splitlines()
                 if l.strip().startswith("|") and not re.match(r"^\s*\|[\s:|-]+\|\s*$", l)][1:]
    sin_respaldo = sum(1 for f in filas if "sin respaldo" in plano(f) or "no respaldada" in plano(f))
    inv_ok = tiene_contenido(fichas_md) and tiene_contenido(matriz_md)
    d["etapas"]["investigacion"] = {"hecha": inv_ok, "pdf": len(pdfs), "fichas": n_fichas,
                                    "filas_matriz": len(filas), "sin_respaldo": sin_respaldo,
                                    "fichas_md": fichas_md.is_file(), "matriz_md": matriz_md.is_file()}

    # redacción
    texto_md = borrador / "texto.md"
    red_ok = tiene_contenido(texto_md)
    d["etapas"]["redaccion"] = {"hecha": red_ok,
                                "palabras": len(re.findall(r"\w+", cuerpo_md(leer(texto_md)))) if red_ok else 0}

    # revisión
    rev_md = borrador / "informe_revision.md"
    obligatoria = nivel != "pregrado" or revisor_pedido
    rev = {"obligatoria": obligatoria, "existe": rev_md.is_file(), "dictamen": None,
           "anterior_al_texto": False}
    if rev_md.is_file():
        rev["dictamen"] = leer_dictamen_revision(rev_md)
        if red_ok:
            rev["anterior_al_texto"] = texto_md.stat().st_mtime > rev_md.stat().st_mtime + TOLERANCIA_MTIME
    d["etapas"]["revision"] = rev

    # controles.json
    controles, ctrl = None, {"existe": (entrega / "controles.json").is_file(), "valido": False,
                             "aprobado_mecanico": False, "archivo": None, "huella_vigente": False,
                             "bloquean": []}
    if ctrl["existe"]:
        try:
            controles = json.loads(leer(entrega / "controles.json"))
            if not isinstance(controles, dict):
                raise ValueError("no es un objeto")
            ctrl["valido"] = True
            ctrl["aprobado_mecanico"] = controles.get("aprobado_mecanico") is True
            ctrl["archivo"] = controles.get("archivo")
            detalle = controles.get("controles")
            if isinstance(detalle, dict):
                for nombre, r in detalle.items():
                    if isinstance(r, dict) and (r.get("estado") == "bloquea" if "estado" in r
                                                else r.get("codigo") not in (0, None)):
                        ctrl["bloquean"].append(nombre)
        except ValueError as e:
            d["incoherencias"].append("entrega/controles.json no es JSON válido (%s)" % e)
            controles = None

    # producción
    docs, docx = docx_de(entrega, controles)
    prod = {"hecha": docx is not None, "docx": [str(p.relative_to(entrega)) for p in docs],
            "principal": str(docx.relative_to(entrega)) if docx else None,
            "texto_mas_nuevo": False}
    if len(docs) > 1:
        d["avisos"].append("hay %d docx en entrega/; se toma %s" % (len(docs), prod["principal"]))
    if docx and red_ok and texto_md.stat().st_mtime > docx.stat().st_mtime + TOLERANCIA_MTIME:
        try:
            distinto = palabras_md(texto_md) != palabras_docx(docx)
        except Exception:  # docx ilegible: manda la fecha
            distinto = True
        prod["texto_mas_nuevo"] = distinto
        if distinto:
            d["incoherencias"].append("borrador/texto.md es más nuevo que el docx y su contenido "
                                      "es distinto: hay que reconstruir el docx")
    d["etapas"]["produccion"] = prod

    # control mecánico
    if docx and ctrl["valido"]:
        huella = controles.get("sha256")
        if not isinstance(ctrl["archivo"], str) or (entrega / ctrl["archivo"]) != docx:
            d["incoherencias"].append("controles.json se refiere a «%s», no al docx actual (%s)"
                                      % (ctrl["archivo"], prod["principal"]))
        elif not isinstance(huella, str) or sha256_de(docx).lower() != huella.strip().lower():
            d["incoherencias"].append("el docx cambió después de los controles (la huella sha256 "
                                      "no coincide con controles.json)")
        else:
            ctrl["huella_vigente"] = True
    d["etapas"]["control"] = ctrl

    # verificación
    inf_md = entrega / "informe_verificacion.md"
    ver = {"existe": inf_md.is_file(), "dictamen": None, "posterior_al_docx": False}
    if inf_md.is_file():
        ver["dictamen"] = leer_dictamen(inf_md)
        if docx:
            ver["posterior_al_docx"] = docx.stat().st_mtime <= inf_md.stat().st_mtime + TOLERANCIA_MTIME
            if not ver["posterior_al_docx"]:
                d["incoherencias"].append("el informe de verificación es anterior al docx: no vale "
                                          "para el archivo actual")
    d["etapas"]["verificacion"] = ver

    # ¿sostiene el cierre como aprobado?
    faltas = []
    if not docx:
        faltas.append("no hay docx en entrega/")
    if not ctrl["valido"] or not ctrl["aprobado_mecanico"]:
        faltas.append("controles mecánicos sin aprobar (control_final.py)")
    elif not ctrl["huella_vigente"]:
        faltas.append("la huella de controles.json no corresponde al docx actual")
    if ver["dictamen"] != "APROBADO":
        faltas.append("no hay informe de verificación con dictamen APROBADO")
    elif docx and not ver["posterior_al_docx"]:
        faltas.append("el informe APROBADO es anterior al docx actual")
    if prod["texto_mas_nuevo"]:
        faltas.append("texto.md cambió después de construir el docx")
    if obligatoria and not rev["existe"]:
        faltas.append("falta la revisión de fondo (borrador/informe_revision.md)")
    d["faltas_para_aprobar"] = faltas
    d["sostiene_aprobado"] = not faltas
    if estado == "aprobado" and faltas:
        d["incoherencias"].append("encargo.md dice «aprobado» pero: " + "; ".join(faltas))

    d["etapa"], d["siguiente"] = siguiente_paso(d, estado)
    if d["vueltas"] >= MAX_VUELTAS and d["etapa"] != "cerrado":
        d["avisos"].append("se alcanzó el máximo de %d vueltas de corrección" % MAX_VUELTAS)
    return d


def devolver(d, quien, que):
    """Devolución por una no aprobación: respeta el máximo de vueltas."""
    if d["vueltas"] >= MAX_VUELTAS:
        return ("director", "ya van %d vueltas de corrección (máximo %d): pon `estado: no aprobado` "
                "con encargo.py anotar e informa al usuario qué falla y por qué" % (d["vueltas"], MAX_VUELTAS))
    return (quien, "%s (vuelta %d de %d; anótala con `anotar --vuelta`)" % (que, d["vueltas"] + 1, MAX_VUELTAS))


def siguiente_paso(d, estado):
    e = d["etapas"]
    inv, red, rev, prod, ctrl, ver = (e["investigacion"], e["redaccion"], e["revision"],
                                      e["produccion"], e["control"], e["verificacion"])
    if estado.startswith("suspendido"):
        return "suspendido", ("director", "encargo suspendido: no continuar salvo que el usuario lo "
                              "pida (entonces `anotar --estado \"en curso\"`)")
    if estado.startswith("no aprobado"):
        return "cerrado sin aprobar", ("director", "cerrado como no aprobado: solo se reabre si el "
                                       "usuario lo pide")
    if not inv["hecha"]:
        ya = ""
        if inv["pdf"] or inv["fichas"]:
            ya = " Ya hay %d PDF y %d fichas: completar, sin volver a descargar lo que está." % (inv["pdf"], inv["fichas"])
        return "investigación", ("investigador", "reunir y fichar fuentes; dejar fuentes/fichas.md y "
                                 "fuentes/matriz_evidencia.md." + ya)
    if not red["hecha"]:
        return "redacción", ("redactor", "redactar borrador/texto.md con las %d fichas y la matriz de "
                             "evidencia" % inv["fichas"])
    if rev["obligatoria"] or rev["existe"]:
        if not rev["existe"]:
            return "revisión", ("revisor", "revisión de fondo de borrador/texto.md; dejar "
                                "borrador/informe_revision.md")
        if rev["dictamen"] is None:
            return "revisión", ("revisor", "informe_revision.md no tiene un dictamen legible: escribir "
                                "la línea «Dictamen: ...»")
        if rev["dictamen"] in ("cambios mayores", "rehacer"):
            if rev["anterior_al_texto"]:
                return "revisión", ("revisor", "texto.md se corrigió después del dictamen «%s»: revisar "
                                    "de nuevo" % rev["dictamen"])
            return ("revisión",) + (devolver(d, "redactor", "corregir lo que señala "
                                             "borrador/informe_revision.md (dictamen «%s»)" % rev["dictamen"]),)
        if rev["dictamen"] == "aceptar con cambios menores" and not rev["anterior_al_texto"]:
            return "revisión", ("redactor", "aplicar los cambios menores de borrador/informe_revision.md, "
                                "sin tocar el resto")
    if not prod["hecha"]:
        return "producción", ("productor", "construir el docx en entrega/ desde borrador/texto.md y "
                              "correr control_final.py")
    if prod["texto_mas_nuevo"]:
        return "producción", ("productor", "texto.md cambió: reconstruir el docx y volver a correr "
                              "control_final.py")
    if not ctrl["valido"] or not ctrl["huella_vigente"]:
        motivo = "no hay controles.json" if not ctrl["existe"] else "controles.json no vale para el docx actual"
        return "control mecánico", ("productor", "%s: correr control_final.py sobre la carpeta" % motivo)
    if not ctrl["aprobado_mecanico"]:
        bloquean = ", ".join(ctrl["bloquean"]) or "ver entrega/controles.md"
        quien = "productor" if ctrl["bloquean"] and set(ctrl["bloquean"]) <= {"formato"} else "redactor"
        return ("control mecánico",) + (devolver(d, quien, "corregir lo que bloquea el control "
                                                 "mecánico (%s) según entrega/controles.md" % bloquean),)
    if not ver["existe"]:
        return "verificación", ("verificador", "verificar entrega/%s y escribir "
                                "entrega/informe_verificacion.md" % prod["principal"])
    if not ver["posterior_al_docx"]:
        return "verificación", ("verificador", "el docx es posterior al informe: verificar de nuevo el "
                                "archivo actual")
    if ver["dictamen"] is None:
        return "verificación", ("verificador", "el informe no tiene línea de dictamen legible: escribir "
                                "«**Dictamen: APROBADO**» o «**Dictamen: NO APROBADO**»")
    if ver["dictamen"] == "NO APROBADO":
        return ("verificación",) + (devolver(d, "redactor o productor", "corregir solo los errores "
                                             "materiales de entrega/informe_verificacion.md (redactor "
                                             "si son de contenido o citas; productor si son de formato)"),)
    if estado != "aprobado":
        return "cierre", ("director", "cierre: control mecánico aprobado y dictamen APROBADO sobre el "
                      "mismo archivo; `anotar --estado aprobado` e informar al usuario")
    return "cerrado", ("cerrado", "aprobado y en regla; no hay nada que hacer")


# ----------------------------------------------------------------- localizar

def encargos_bajo(raiz):
    if not raiz.is_dir():
        return []
    return sorted(p.parent for p in raiz.glob("*/trabajos/*/*/encargo.md"))


def resolver_carpeta(texto, raiz):
    p = Path(texto).expanduser()
    if (p / "encargo.md").is_file():
        return p.resolve()
    if p.is_dir():
        raise Fallo("la carpeta %s no tiene encargo.md" % p)
    buscado = comun.normalizar(texto)
    if not buscado:
        raise Fallo("no se indicó la carpeta del encargo")
    hallados = [c for c in encargos_bajo(raiz) if buscado in comun.normalizar(c.name)]
    exactos = [c for c in hallados if comun.normalizar(c.name) == buscado]
    if len(exactos) == 1:
        return exactos[0]
    if len(hallados) == 1:
        return hallados[0]
    if not hallados:
        raise Fallo("no hay ninguna carpeta de encargo «%s» (ni como ruta ni bajo %s)" % (texto, raiz))
    raise Fallo("«%s» coincide con varias carpetas; indica la ruta:\n  %s"
                % (texto, "\n  ".join(str(c) for c in hallados)))


# ----------------------------------------------------------------- subcomandos

def cmd_nuevo(args):
    tema = una_linea(args.tema)
    if not tema:
        raise Fallo("falta --tema")
    supuestos, avisos = [], []
    tipo = plano(args.tipo) if args.tipo else None
    if tipo is None:
        tipo = "ensayo"
        supuestos.append("tipo no indicado: ensayo")
    elif tipo not in TIPOS:
        raise Fallo("tipo no válido: «%s». Valores: %s" % (args.tipo, ", ".join(TIPOS)))
    nivel = plano(args.nivel) if args.nivel else None
    if nivel is None:
        nivel = "pregrado"
        supuestos.append("nivel no indicado: pregrado")
    elif nivel not in NIVELES:
        raise Fallo("nivel no válido: «%s». Valores: %s" % (args.nivel, ", ".join(NIVELES)))
    paginas = None
    if args.paginas:
        m = re.fullmatch(r"\s*(\d+)\s*(?:(?:-|–|a)\s*(\d+))?\s*", args.paginas)
        if not m or int(m.group(1)) == 0:
            raise Fallo("páginas no válidas: «%s» (usa 5 o 8-10)" % args.paginas)
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        paginas = str(a) if a == b else "%d-%d" % (min(a, b), max(a, b))
    else:
        avisos.append("sin extensión (--paginas): control_final.py no controlará las páginas")
    formato = una_linea(args.formato) if args.formato else None
    if not formato:
        formato = "docx"
        supuestos.append("formato no indicado: docx")
    para = args.para or "don_nico"
    if para not in DESTINATARIOS:
        raise Fallo("destinatario no válido: «%s» (don_nico o jota)" % para)
    if args.fecha_entrega:
        try:
            date.fromisoformat(args.fecha_entrega)
        except ValueError:
            raise Fallo("fecha de entrega no válida: «%s» (AAAA-MM-DD)" % args.fecha_entrega)
    categoria = nombre_seguro(args.categoria) if args.categoria else PLURAL[tipo]
    if not args.categoria:
        supuestos.append("categoría no indicada: %s" % categoria)
    nombre = nombre_seguro(args.carpeta) if args.carpeta else slug(tema)
    if not nombre:
        raise Fallo("el tema no da un nombre de carpeta: indica --carpeta")

    raiz = raiz_de(args)
    carpeta = raiz / para / "trabajos" / categoria / nombre
    if carpeta.exists():
        raise Fallo("ya existe %s: no se pisa. Para seguir con ese encargo usa "
                    "`encargo.py retomar \"%s\"`; para uno nuevo, otro --carpeta" % (carpeta, nombre))
    tipo, nivel = CON_TILDE.get(tipo, tipo), CON_TILDE.get(nivel, nivel)
    campos = {"tema": tema, "tipo": tipo, "nivel": nivel, "paginas": paginas, "formato": formato,
              "estado": "en curso", "revisor": "sí" if args.con_revisor else None,
              "estructura": una_linea(args.estructura) if args.estructura else None,
              "para": para, "categoria": categoria,
              "materia": una_linea(args.materia) if args.materia else None,
              "docente": una_linea(args.docente) if args.docente else None,
              "fecha_entrega": args.fecha_entrega, "creado": date.today().isoformat()}
    for sub in ("fuentes", "borrador", "entrega"):
        (carpeta / sub).mkdir(parents=True, exist_ok=False if sub == "fuentes" else True)
    resumen = "%s, %s%s" % (tipo, nivel, ", %s páginas" % paginas if paginas else "")
    texto = anadir_bitacora(generar_encargo_md(campos, args.nota), "encargo creado (%s)" % resumen)
    escribir(carpeta / "encargo.md", texto)
    r = {"codigo": 1 if avisos else 0, "carpeta": str(carpeta), "encargo_md": str(carpeta / "encargo.md"),
         "campos": {k: v for k, v in campos.items() if v}, "supuestos": supuestos, "avisos": avisos}
    if args.json:
        return r
    print("Encargo creado: %s" % carpeta)
    print("  " + resumen + "; estado: en curso")
    for s in supuestos:
        print("  supuesto: " + s)
    for a in avisos:
        print("  aviso: " + a)
    print("SIGUIENTE PASO: investigador — reunir y fichar fuentes en %s" % (carpeta / "fuentes"))
    return r


def texto_estado(d):
    e = d["etapas"]
    inv, red, rev, prod, ctrl, ver = (e["investigacion"], e["redaccion"], e["revision"],
                                      e["produccion"], e["control"], e["verificacion"])
    si = lambda x: "sí" if x else "no"
    out = ["Encargo: %s" % d["carpeta"],
           "  tema: %s" % (d["tema"] or "(sin tema)"),
           "  %s, %s, páginas %s; estado declarado: %s" % (d["tipo"] or "tipo sin indicar", d["nivel"],
                                                           d["paginas"] or "sin indicar",
                                                           d["estado"] or "(sin línea estado)"),
           "  vueltas de corrección: %d de %d" % (d["vueltas"], d["max_vueltas"])]
    if d["ultima_bitacora"]:
        out.append("  última anotación: %s" % d["ultima_bitacora"])
    out.append("Etapas:")
    out.append("  investigación: %s (%d PDF, %d fichas, matriz %d filas%s)" % (
        "hecha" if inv["hecha"] else "pendiente", inv["pdf"], inv["fichas"], inv["filas_matriz"],
        ", %d sin respaldo" % inv["sin_respaldo"] if inv["sin_respaldo"] else ""))
    out.append("  redacción: %s" % ("texto.md, %d palabras" % red["palabras"] if red["hecha"] else "pendiente"))
    if rev["obligatoria"] or rev["existe"]:
        out.append("  revisión: %s%s" % ("dictamen «%s»" % rev["dictamen"] if rev["dictamen"]
                                         else ("informe sin dictamen legible" if rev["existe"] else "pendiente"),
                                         " (texto corregido después)" if rev["anterior_al_texto"] else ""))
    else:
        out.append("  revisión: no obligatoria en pregrado")
    out.append("  producción: %s" % (prod["principal"] if prod["hecha"] else "pendiente"))
    if ctrl["existe"]:
        out.append("  control mecánico: %s; huella vigente: %s%s" % (
            "aprobado" if ctrl["aprobado_mecanico"] else "NO aprobado", si(ctrl["huella_vigente"]),
            "; bloquean: " + ", ".join(ctrl["bloquean"]) if ctrl["bloquean"] else ""))
    else:
        out.append("  control mecánico: pendiente")
    if ver["existe"]:
        out.append("  verificación: dictamen %s; posterior al docx: %s" % (
            ver["dictamen"] or "ilegible", si(ver["posterior_al_docx"])))
    else:
        out.append("  verificación: pendiente")
    if d["incoherencias"]:
        out.append("INCOHERENCIAS:")
        out.extend("  - " + i for i in d["incoherencias"])
    for a in d["avisos"]:
        out.append("aviso: " + a)
    quien, que = d["siguiente"]
    out.append("Etapa: %s" % d["etapa"])
    out.append("SIGUIENTE PASO: cerrado — %s" % que if quien == "cerrado"
               else "SIGUIENTE PASO: %s — %s" % (quien, que))
    return "\n".join(out)


def json_estado(d):
    r = dict(d)
    r["siguiente"] = {"agente": d["siguiente"][0], "accion": d["siguiente"][1]}
    return r


def cmd_estado(args):
    carpeta = resolver_carpeta(args.carpeta, raiz_de(args))
    d = diagnosticar(carpeta)
    d["codigo"] = 1 if d["incoherencias"] else 0
    if args.json:
        return json_estado(d)
    print(texto_estado(d))
    return d


def cmd_anotar(args):
    carpeta = resolver_carpeta(args.carpeta, raiz_de(args))
    texto_linea = una_linea(args.texto)
    if not texto_linea:
        raise Fallo("el texto de la anotación está vacío")
    nuevo_estado = canon_estado(args.estado) if args.estado else None
    enc = leer_encargo(carpeta)
    r = {"carpeta": str(carpeta), "codigo": 0}
    if nuevo_estado == "aprobado":
        d = diagnosticar(carpeta)
        if not d["sostiene_aprobado"]:
            r.update(codigo=1, rechazado=True, faltas=d["faltas_para_aprobar"])
            if not args.json:
                print("RECHAZADO: no se cambia a «aprobado» ni se escribe nada.")
                for f in d["faltas_para_aprobar"]:
                    print("  - " + f)
            return r
    linea = texto_linea
    if args.vuelta:
        if enc["vueltas"] >= MAX_VUELTAS:
            r.update(codigo=1, rechazado=True,
                     faltas=["ya hay %d vueltas registradas (máximo %d): corresponde `--estado "
                             "\"no aprobado\"`" % (enc["vueltas"], MAX_VUELTAS)])
            if not args.json:
                print("RECHAZADO: " + r["faltas"][0])
            return r
        linea = "vuelta %d: %s" % (enc["vueltas"] + 1, linea)
    anterior = enc["campos"].get("estado", "")
    texto = enc["texto"]
    if nuevo_estado:
        texto = poner_estado(texto, nuevo_estado)
        linea += " (estado: %s → %s)" % (anterior or "sin estado", nuevo_estado)
    texto = anadir_bitacora(texto, linea)
    escribir(carpeta / "encargo.md", texto)
    r.update(rechazado=False, anotado=linea, estado=nuevo_estado or anterior,
             vueltas=enc["vueltas"] + (1 if args.vuelta else 0))
    if not args.json:
        print("Anotado en %s:" % (carpeta / "encargo.md"))
        print("  " + linea)
    return r


ORDEN_ESTADOS = {"en curso": 0, "en verificacion": 0, "": 1, "no aprobado": 2, "suspendido": 3, "aprobado": 4}


def cmd_listar(args):
    raiz = raiz_de(args)
    if not raiz.is_dir():
        raise Fallo("no existe la raíz de los trabajos: %s" % raiz)
    filtro_estado = canon_estado(args.estado) if args.estado else None
    filas = []
    for carpeta in encargos_bajo(raiz):
        para = carpeta.parents[2].name
        if args.para and para != args.para:
            continue
        try:
            enc = leer_encargo(carpeta)
        except OSError:
            continue
        c = enc["campos"]
        est = estado_de(c)
        if filtro_estado and est != plano(filtro_estado):
            continue
        filas.append({"carpeta": str(carpeta), "nombre": carpeta.name, "para": para,
                      "categoria": carpeta.parent.name, "tema": c.get("tema", ""),
                      "nivel": nivel_de(c), "tipo": tipo_de(c) or "", "estado": c.get("estado", ""),
                      "abierto": est in ABIERTOS or est not in ORDEN_ESTADOS,
                      "ultima": enc["bitacora"][-1] if enc["bitacora"] else "",
                      "_orden": (ORDEN_ESTADOS.get(est, 1), -(carpeta / "encargo.md").stat().st_mtime)})
    filas.sort(key=lambda f: f["_orden"])
    for f in filas:
        del f["_orden"]
    r = {"codigo": 0, "raiz": str(raiz), "encargos": filas}
    if args.json:
        return r
    if not filas:
        print("Sin encargos bajo %s" % raiz)
        return r
    print("Encargos bajo %s (%d), abiertos primero:" % (raiz, len(filas)))
    for f in filas:
        print("- [%s] %s/%s/%s — %s (%s, %s)" % (f["estado"] or "sin estado", f["para"], f["categoria"],
                                               f["nombre"], f["tema"][:70], f["tipo"] or "tipo ?", f["nivel"]))
        if f["ultima"]:
            print("    última: %s" % f["ultima"])
    return r


# ----------------------------------------------------------------- main

def analizador():
    comunes = argparse.ArgumentParser(add_help=False)
    comunes.add_argument("--raiz", help="raíz de los trabajos (o variable ENCARGOS_RAIZ)")
    comunes.add_argument("--json", action="store_true", help="salida JSON")
    a = argparse.ArgumentParser(description="Inicio, diagnóstico y bitácora de un encargo académico.")
    sub = a.add_subparsers(dest="orden", required=True)
    n = sub.add_parser("nuevo", parents=[comunes], help="crea la carpeta y encargo.md")
    n.add_argument("--tema", required=True)
    n.add_argument("--tipo", help="|".join(TIPOS) + " (por defecto ensayo)")
    n.add_argument("--nivel", help="|".join(NIVELES) + " (por defecto pregrado)")
    n.add_argument("--paginas", help="total de páginas: 5 o 8-10")
    n.add_argument("--categoria", help="subcarpeta de trabajos/ (por defecto el tipo en plural)")
    n.add_argument("--carpeta", help="nombre de la carpeta (por defecto, derivado del tema)")
    n.add_argument("--para", choices=DESTINATARIOS, default="don_nico")
    n.add_argument("--materia")
    n.add_argument("--docente")
    n.add_argument("--fecha-entrega", dest="fecha_entrega", help="AAAA-MM-DD")
    n.add_argument("--formato", help="por defecto docx")
    n.add_argument("--con-revisor", dest="con_revisor", action="store_true",
                   help="sumar el revisor aunque sea pregrado")
    n.add_argument("--nota", help="nota libre para la sección Notas")
    n.add_argument("--estructura", help="variante del tipo según la skill tipos-de-trabajo "
                   "(p. ej. capitulos para una monografía por capítulos)")
    for nombre in ("estado", "retomar"):
        e = sub.add_parser(nombre, parents=[comunes], help="diagnóstico para retomar")
        e.add_argument("carpeta", help="ruta o parte del nombre de la carpeta")
    an = sub.add_parser("anotar", parents=[comunes], help="línea en la bitácora y, si se pide, estado")
    an.add_argument("carpeta")
    an.add_argument("texto")
    an.add_argument("--estado", help=", ".join(ESTADOS.values()))
    an.add_argument("--vuelta", action="store_true", help="registra una vuelta de corrección")
    li = sub.add_parser("listar", parents=[comunes], help="encargos bajo la raíz")
    li.add_argument("--para", choices=DESTINATARIOS)
    li.add_argument("--estado")
    return a


def main(argv=None):
    comun.salida_utf8()
    args = analizador().parse_args(argv)
    funciones = {"nuevo": cmd_nuevo, "estado": cmd_estado, "retomar": cmd_estado,
                 "anotar": cmd_anotar, "listar": cmd_listar}
    try:
        r = funciones[args.orden](args)
    except Fallo as e:
        if args.json:
            print(json.dumps({"codigo": 2, "error": str(e)}, ensure_ascii=False, indent=2))
        else:
            print("ERROR: %s" % e, file=sys.stderr)
        return 2
    except OSError as e:
        if args.json:
            print(json.dumps({"codigo": 2, "error": str(e)}, ensure_ascii=False, indent=2))
        else:
            print("ERROR: %s" % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    return r.get("codigo", 0)


if __name__ == "__main__":
    sys.exit(main())
