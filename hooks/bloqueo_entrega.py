#!/usr/bin/env python3
"""Hook de bloqueo de entrega (evento Stop de Claude Code).

Impide que Claude dé por terminado el turno si en algún encargo de la
sesión hay un entregable en `entrega/` sin verificación válida:
informe del verificador con dictamen APROBADO, `controles.json` con
`aprobado_mecanico: true`, huella sha256 vigente e informe no anterior
al entregable.

Uso como hook: Claude Code envía un JSON por stdin. Para bloquear se
imprime `{"decision": "block", "reason": "..."}` y se sale con 0; para
dejar pasar se sale con 0 sin salida. Ante cualquier error interno se
deja pasar y se escribe la causa en stderr: un fallo del hook nunca
debe dejar atrapada la sesión.

Uso manual (depuración):
    python bloqueo_entrega.py --comprobar <carpeta del encargo>
Imprime el diagnóstico y sale con 0 (pasa) o 1 (bloquearía).

Solo biblioteca estándar. Windows y Linux.
"""

import hashlib
import json
import os
import re
import sys
import time
import unicodedata

EXT_ENTREGABLES = (".docx", ".xlsx", ".pptx", ".pdf")
NO_SON_ENTREGABLES = {"informe_verificacion.md", "controles.json"}
ESTADOS_QUE_LIBERAN = ("no aprobado", "suspendido")
TOLERANCIA_MTIME = 2.0          # segundos
PRESUPUESTO_TRANSCRIPCION = 20.0  # segundos como máximo leyendo transcripciones
MAX_RETROCESO = 400             # caracteres hacia atrás para buscar el inicio de una ruta
DELIMITADORES = set(" \t\r\n\"'`()[]{}<>=,;|")

QUE_HACER = (
    "Qué hacer: ejecuta control_final.py sobre la carpeta, pasa el trabajo "
    "al verificador y, si tras tres vueltas no aprueba, pon `estado: no "
    "aprobado` en encargo.md e informa al usuario qué falla."
)


# ---------------------------------------------------------------- utilidades

def sin_tildes(texto):
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def leer_texto(ruta):
    with open(ruta, "r", encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def sha256_de(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def clave(ruta):
    """Clave de deduplicación (mayúsculas en Windows, enlaces resueltos)."""
    return os.path.normcase(os.path.realpath(ruta))


# ------------------------------------------------- localizar los encargos

def encargos_desde_cwd(cwd):
    encontrados = []
    if not cwd:
        return encontrados
    actual = os.path.abspath(cwd)
    while True:
        if os.path.isfile(os.path.join(actual, "encargo.md")):
            encontrados.append(actual)
        padre = os.path.dirname(actual)
        if padre == actual:
            break
        actual = padre
    return encontrados


def cadenas_de(obj):
    """Todas las cadenas contenidas en un objeto JSON."""
    pila = [obj]
    while pila:
        x = pila.pop()
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            pila.extend(x.values())
            pila.extend(k for k in x.keys() if isinstance(k, str))
        elif isinstance(x, list):
            pila.extend(x)


def inicios_posibles(texto, fin):
    """Posiciones donde podría empezar una ruta que termina en `fin`.

    Se prueban de la más larga a la más corta: así una ruta con espacios
    también se encuentra (luego se filtra por existencia en disco).
    """
    desde = max(0, fin - MAX_RETROCESO)
    inicios = []
    for i in range(desde, fin):
        c = texto[i]
        if i + 2 < len(texto) and c.isalpha() and texto[i + 1] == ":" and texto[i + 2] in "\\/":
            if i == 0 or not texto[i - 1].isalnum():
                inicios.append(i)
        elif c in "/\\~" or c.isalnum() or c == ".":
            if i == 0 or texto[i - 1] in DELIMITADORES:
                inicios.append(i)
    return inicios


def normalizar_candidata(ruta, cwd):
    ruta = ruta.strip()
    if os.sep == "/":
        ruta = ruta.replace("\\", "/")
    ruta = os.path.expanduser(ruta)
    if not os.path.isabs(ruta) and cwd:
        ruta = os.path.join(cwd, ruta)
    return os.path.normpath(ruta)


class Buscador:
    """Extrae carpetas de encargo de cadenas de texto."""

    PATRON = re.compile(r"encargo\.md|[\\/]entrega(?=[\\/\"'`\s)\]]|$)", re.IGNORECASE)

    def __init__(self, cwd):
        self.cwd = cwd
        self.probadas = set()
        self.carpetas = []

    def _probar(self, carpeta):
        if not carpeta:
            return False
        k = carpeta.lower() if os.name == "nt" else carpeta
        if k in self.probadas:
            return self._ya_tiene(carpeta)
        self.probadas.add(k)
        if os.path.isfile(os.path.join(carpeta, "encargo.md")):
            self.carpetas.append(carpeta)
            return True
        return False

    def _ya_tiene(self, carpeta):
        return any(c == carpeta for c in self.carpetas)

    def analizar(self, texto):
        bajo = texto.lower()
        if "encargo.md" not in bajo and "entrega" not in bajo:
            return
        for m in self.PATRON.finditer(texto):
            if m.group(0).lower() == "encargo.md":
                fin = m.end()
                for i in inicios_posibles(texto, m.start() + 1):
                    ruta = normalizar_candidata(texto[i:fin], self.cwd)
                    if os.path.basename(ruta).lower() != "encargo.md":
                        continue
                    if self._probar(os.path.dirname(ruta)):
                        break
            else:
                fin = m.start()  # carpeta del encargo = lo que precede a /entrega
                for i in inicios_posibles(texto, fin):
                    carpeta = normalizar_candidata(texto[i:fin], self.cwd)
                    if self._probar(carpeta):
                        break


def transcripciones(ruta):
    """La transcripción principal y, si existen, las de sus subagentes."""
    rutas = []
    if ruta and os.path.isfile(ruta):
        rutas.append(ruta)
        base, _ = os.path.splitext(ruta)
        sub = os.path.join(base, "subagents")
        if os.path.isdir(sub):
            for nombre in sorted(os.listdir(sub)):
                if nombre.endswith(".jsonl"):
                    rutas.append(os.path.join(sub, nombre))
    return rutas


def encargos_desde_transcripcion(ruta, cwd, avisos):
    buscador = Buscador(cwd)
    limite = time.monotonic() + PRESUPUESTO_TRANSCRIPCION
    for archivo in transcripciones(ruta):
        try:
            with open(archivo, "r", encoding="utf-8", errors="replace") as f:
                for linea in f:
                    if time.monotonic() > limite:
                        avisos.append("transcripción demasiado larga: lectura cortada por tiempo")
                        return buscador.carpetas
                    bajo = linea.lower()
                    if "encargo.md" not in bajo and "entrega" not in bajo:
                        continue
                    try:
                        textos = list(cadenas_de(json.loads(linea)))
                    except ValueError:
                        # línea corrupta: se analiza en bruto, deshaciendo el escape de "\"
                        textos = [linea.replace("\\\\", "\\")]
                    for t in textos:
                        buscador.analizar(t)
        except OSError as e:
            avisos.append("no se pudo leer %s: %s" % (archivo, e))
    return buscador.carpetas


def localizar_encargos(cwd, transcript_path, avisos):
    carpetas = []
    vistas = set()
    for c in encargos_desde_cwd(cwd) + encargos_desde_transcripcion(transcript_path, cwd, avisos):
        try:
            if not os.path.isfile(os.path.join(c, "encargo.md")):
                continue
            k = clave(c)
        except OSError:
            continue
        if k not in vistas:
            vistas.add(k)
            carpetas.append(c)
    return carpetas


# ------------------------------------------------- evaluar un encargo

def leer_estado(encargo_md):
    for linea in leer_texto(encargo_md).splitlines():
        limpia = sin_tildes(linea).replace("*", "").replace("_", "").strip(" \t-#>").lower()
        m = re.match(r"estado\s*:\s*(.*)$", limpia)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip(" .`'\"")
    return ""


def listar_entregables(entrega):
    salida = []

    def es_entregable(nombre):
        bajo = nombre.lower()
        return (bajo.endswith(EXT_ENTREGABLES) and not nombre.startswith("~$")
                and not bajo.endswith(".bak") and bajo not in NO_SON_ENTREGABLES)

    for nombre in sorted(os.listdir(entrega)):
        ruta = os.path.join(entrega, nombre)
        if os.path.isfile(ruta) and es_entregable(nombre):
            salida.append(ruta)
        elif os.path.isdir(ruta):  # un nivel de subcarpetas, no más
            for sub in sorted(os.listdir(ruta)):
                rs = os.path.join(ruta, sub)
                if os.path.isfile(rs) and es_entregable(sub):
                    salida.append(rs)
    return salida


RE_NO_APROBADO = re.compile(r"\bno[\s\-_]+aprobado\b", re.IGNORECASE)
RE_APROBADO = re.compile(r"\baprobado\b", re.IGNORECASE)


def veredicto_de(linea):
    """'NO APROBADO', 'APROBADO' o None para una línea."""
    no = RE_NO_APROBADO.search(linea)
    si = RE_APROBADO.search(linea)
    if no and (not si or no.start() <= si.start()):
        return "NO APROBADO"
    if si:
        return "APROBADO"
    return None


def leer_dictamen(informe):
    """Último dictamen del informe, o None si no hay ninguno reconocible."""
    lineas = [sin_tildes(l) for l in leer_texto(informe).splitlines()]
    candidatos = []
    for i, l in enumerate(lineas):
        if "dictamen" not in l.lower():
            continue
        v = veredicto_de(l)
        if v is None:  # "## Dictamen" y el veredicto en las líneas siguientes
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
    if not candidatos:  # sin la palabra "dictamen": líneas que solo dicen el veredicto
        for i, l in enumerate(lineas):
            pelada = re.sub(r"[\s*#_\-:>.`]+", " ", l).strip().upper()
            if pelada in ("APROBADO", "NO APROBADO"):
                candidatos.append((i, pelada))
    return candidatos[-1][1] if candidatos else None


def evaluar(carpeta):
    """Devuelve (faltas, notas). Si `faltas` está vacía, el encargo no bloquea."""
    faltas, notas = [], []
    encargo_md = os.path.join(carpeta, "encargo.md")
    estado = leer_estado(encargo_md) if os.path.isfile(encargo_md) else ""
    notas.append("estado: %s" % (estado or "(sin línea estado:)"))
    if any(estado.startswith(e) for e in ESTADOS_QUE_LIBERAN):
        notas.append("estado '%s': se permite cerrar informando qué falla" % estado)
        return faltas, notas

    entrega = os.path.join(carpeta, "entrega")
    entregables = listar_entregables(entrega) if os.path.isdir(entrega) else []
    if not entregables:
        notas.append("sin entregables en entrega/: no hay nada que verificar")
        return faltas, notas
    notas.append("entregables: " + ", ".join(os.path.relpath(e, entrega) for e in entregables))

    informe = os.path.join(entrega, "informe_verificacion.md")
    if not os.path.isfile(informe):
        faltas.append("falta entrega/informe_verificacion.md (el verificador no dictaminó)")
    else:
        dictamen = leer_dictamen(informe)
        if dictamen is None:
            faltas.append("informe_verificacion.md no tiene una línea de dictamen APROBADO / NO APROBADO")
        elif dictamen != "APROBADO":
            faltas.append("el dictamen del verificador es NO APROBADO")
        else:
            notas.append("dictamen: APROBADO")
        m_inf = os.path.getmtime(informe)
        viejos = [os.path.relpath(e, entrega) for e in entregables
                  if os.path.getmtime(e) > m_inf + TOLERANCIA_MTIME]
        if viejos:
            faltas.append("el informe de verificación es anterior al entregable (%s): "
                          "un informe viejo no vale para un archivo nuevo" % ", ".join(viejos))

    controles_json = os.path.join(entrega, "controles.json")
    if not os.path.isfile(controles_json):
        faltas.append("falta entrega/controles.json (no se ejecutó control_final.py)")
        return faltas, notas
    try:
        controles = json.loads(leer_texto(controles_json))
        if not isinstance(controles, dict):
            raise ValueError("no es un objeto JSON")
    except ValueError as e:
        faltas.append("entrega/controles.json no es JSON válido (%s)" % e)
        return faltas, notas

    if controles.get("aprobado_mecanico") is not True:
        malos = []
        detalle = controles.get("controles")
        if isinstance(detalle, dict):
            for nombre, r in detalle.items():
                if not isinstance(r, dict):
                    continue
                # Con "estado" manda el estado: un aviso con código 1 no bloquea.
                if "estado" in r:
                    es_malo = r.get("estado") == "bloquea"
                else:
                    es_malo = r.get("codigo") not in (0, None)
                if es_malo:
                    malos.append("%s (código %s)" % (nombre, r.get("codigo")))
        faltas.append("los controles mecánicos no pasaron (aprobado_mecanico no es true)"
                      + (": " + ", ".join(malos) if malos else ""))

    archivo = controles.get("archivo")
    huella = controles.get("sha256")
    if not isinstance(archivo, str) or not archivo.strip():
        faltas.append("controles.json no indica el archivo controlado")
    elif not isinstance(huella, str) or not huella.strip():
        faltas.append("controles.json no tiene la huella sha256")
    else:
        principal = os.path.join(entrega, archivo)
        if not os.path.isfile(principal):
            faltas.append("el archivo de controles.json (%s) no está en entrega/" % archivo)
        elif sha256_de(principal).lower() != huella.strip().lower():
            faltas.append("el entregable cambió después de los controles (%s: la huella "
                          "sha256 no coincide con controles.json)" % archivo)
        else:
            notas.append("huella vigente: %s" % archivo)
    return faltas, notas


# ------------------------------------------------------------- salida

def motivo(bloqueados):
    partes = ["No se puede cerrar: hay entregables sin verificación válida."]
    for carpeta, faltas in bloqueados:
        partes.append("Encargo: %s" % carpeta)
        partes.extend("- " + f for f in faltas)
    partes.append(QUE_HACER)
    return "\n".join(partes)


def escribir(flujo, texto):
    flujo.buffer.write(texto.encode("utf-8"))
    flujo.flush()


def aviso(texto):
    try:
        escribir(sys.stderr, "bloqueo_entrega: %s\n" % texto)
    except Exception:
        pass


def modo_hook():
    if sys.stdin is None or sys.stdin.isatty():
        aviso("sin entrada por stdin; se deja pasar")
        return 0
    crudo = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")
    datos = json.loads(crudo)
    if not isinstance(datos, dict):
        raise ValueError("la entrada no es un objeto JSON")
    if datos.get("stop_hook_active"):
        return 0
    avisos = []
    carpetas = localizar_encargos(datos.get("cwd") or "", datos.get("transcript_path") or "", avisos)
    for a in avisos:
        aviso(a)
    bloqueados = []
    for carpeta in carpetas:
        try:
            faltas, _ = evaluar(carpeta)
        except Exception as e:  # un encargo ilegible no debe atrapar la sesión
            aviso("no se pudo evaluar %s: %s" % (carpeta, e))
            continue
        if faltas:
            bloqueados.append((carpeta, faltas))
    if bloqueados:
        salida = json.dumps({"decision": "block", "reason": motivo(bloqueados)}, ensure_ascii=True)
        escribir(sys.stdout, salida + "\n")
    return 0


def modo_comprobar(carpeta):
    carpeta = os.path.abspath(carpeta)
    lineas = ["Encargo: %s" % carpeta]
    if not os.path.isfile(os.path.join(carpeta, "encargo.md")):
        lineas.append("aviso: la carpeta no tiene encargo.md; el hook no la consideraría un encargo")
    faltas, notas = evaluar(carpeta)
    lineas.extend("  " + n for n in notas)
    if faltas:
        lineas.append("BLOQUEARÍA:")
        lineas.extend("  - " + f for f in faltas)
        lineas.append(QUE_HACER)
    else:
        lineas.append("PASA")
    escribir(sys.stdout, "\n".join(lineas) + "\n")
    return 1 if faltas else 0


def main(argv):
    if len(argv) >= 2 and argv[0] == "--comprobar":
        return modo_comprobar(argv[1])
    if argv and argv[0] in ("-h", "--help"):
        escribir(sys.stdout, __doc__)
        return 0
    try:
        return modo_hook()
    except Exception as e:  # nunca dejar atrapada la sesión
        aviso("error interno, se deja pasar: %r" % (e,))
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
