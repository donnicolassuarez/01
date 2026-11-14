# -*- coding: utf-8 -*-
"""Control mecánico final de un encargo antes de pasarlo al verificador.

Uso:
  python control_final.py <carpeta del encargo> [--archivo entrega/x.docx]
         [--sin-red] [--json]

Corre, como subprocesos y con --json, los scripts hermanos sobre el
entregable REAL de entrega/ y escribe dos archivos en entrega/:
  controles.json  lo lee el hook bloqueo_entrega.py (contrato abajo);
  controles.md    resumen legible para el verificador.
No modifica el entregable. Solo biblioteca estándar.

Formato esperado de encargo.md (todas las líneas son opcionales; se
admiten viñetas, negritas y mayúsculas, p. ej. "- **Nivel:** Maestría"):
  nivel: pregrado | maestría | doctorado | postdoctorado   (por defecto pregrado)
  tipo: ensayo | monografía | informe | artículo | otro
  paginas: 8 | 8-10 | 8 a 10 | mínimo 8 | máximo 10      (también "páginas:"
           o "extensión:"; "8" es el total exacto: mínimo y máximo 8)
  estado: en curso | en verificación | aprobado | no aprobado | suspendido
El nivel fija el límite de la lista de referencias: página y media en
pregrado; sin límite de páginas desde maestría.

Entregable: --archivo (relativo a la carpeta del encargo o absoluto,
siempre dentro de entrega/; .docx o .xlsx) o, si no se indica, el único
.docx de entrega/ o de una subcarpeta suya (se ignoran "~$*" y "*.bak").
Si hay varios, sale con 2 y pide --archivo. Si no hay ningún .docx y hay
un único .xlsx, ese es el entregable. Con un .docx y un .xlsx, el
principal es el .docx (salvo --archivo) y el otro va a avisos.

Entregable .xlsx (hoja de cálculo): corre un solo control, "hoja", sin
dependencias nuevas (zipfile + ElementTree):
  - zip íntegro, con [Content_Types].xml y xl/workbook.xml;
  - todas las partes XML legibles;
  - ninguna celda con error almacenado (#REF!, #DIV/0!, #N/A, #NAME?,
    #VALUE!, #NULL!, #NUM!: tipo "e" o valor guardado) ni fórmula con
    #REF!; solo se ven los valores guardados en el archivo: una fórmula
    que nunca se calculó (escrita por openpyxl sin abrir en Excel o
    LibreOffice) no tiene valor que revisar;
  - ningún marcador prohibido («por verificar», «pendiente:», «TODO»,
    «XXX», «[cita]») en las cadenas compartidas o en línea;
  - hojas sin ninguna celda con valor: aviso, no bloquea.
Bloquean los cuatro primeros. Los controles citas, similitud,
formato, referencias y fuentes quedan "no aplica" (no bloquean).

Controles y política (aprobado_mecanico = ningún control bloquea):
  citas       cruzar_citas.py: bloquea si hay citas sin referencia,
              referencias no citadas o autor/año discordante. Orden
              alfabético, duplicadas, localizadores y siglas: avisos.
  similitud   similitud_fuentes.py contra fuentes/ (antes corre
              extraer_texto.py sobre fuentes/ si hay PDF; solo extrae los
              que no estén al día). Bloquea con COPIA o CASI IDÉNTICA.
              Sin ningún PDF ni texto en fuentes/: "no ejecutado" y
              BLOQUEA (solo se cita lo descargado y leído).
  formato     verificar_formato.py con --tipo y páginas del encargo:
              bloquea si hay algún ERROR.
  referencias verificar_referencias.py (red): no bloquea. Las DUDOSA y
              NO ENCONTRADA pasan a pendientes_verificador (libros, leyes
              y documentos oficiales salen NO ENCONTRADA legítimamente).
              Con --sin-red o sin red: "no ejecutado", no bloquea.
  fuentes     cada referencia se empareja con fuentes/indice.json (por
              DOI o título normalizado), con un archivo de fuentes/ cuyo
              nombre lleve primer autor y año, y con una ficha de
              fuentes/fichas.md (bloque con primer autor y año). Sin
              archivo localizado: pendiente para el verificador (no
              bloquea). Archivo sin ficha: aviso.
Un control que no se pudo ejecutar (código 2 del script) bloquea, salvo
referencias y fuentes.

Contrato de entrega/controles.json (escritura atómica):
  {"archivo": "<ruta relativa a entrega/>", "sha256": "...",
   "fecha": "<ISO 8601>", "aprobado_mecanico": bool,
   "controles": {"<nombre>": {"codigo": int,
                 "estado": "ok|bloquea|aviso|no ejecutado|no aplica",
                 "resumen": "..."}},
   "pendientes_verificador": [{"referencia": "...", "motivos": [...]}],
   "avisos": ["..."]}
"codigo" es el código de salida del script (-1 si no llegó a correr).

Códigos de salida: 0 control mecánico aprobado; 1 no aprobado; 2 no se
pudo ejecutar (carpeta o entregable inexistente, varios .docx sin
--archivo, el archivo cambió durante el control).
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TIPOS = {"ensayo": "ensayo", "monografia": "monografia", "informe": "informe",
         "articulo": "articulo", "otro": "otro"}
NIVELES = ("postdoctorado", "doctorado", "maestria", "pregrado")
ORDEN = ("citas", "similitud", "formato", "referencias", "fuentes")
NO_BLOQUEAN_SI_NO_CORREN = ("referencias", "fuentes")
TIEMPO = {"cruzar_citas.py": 300, "extraer_texto.py": 900, "similitud_fuentes.py": 900,
          "verificar_formato.py": 900, "verificar_referencias.py": 1800}
MAX_LISTA = 15


# ----------------------------------------------------------------- utilidades

def sin_tildes(texto):
    descompuesto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def normalizar(texto):
    texto = sin_tildes(texto).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", texto)).strip()


def sha256_de(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def escribir_atomico(ruta, texto):
    carpeta = os.path.dirname(os.path.abspath(ruta))
    descriptor, temporal = tempfile.mkstemp(dir=carpeta, prefix=".tmp_", suffix=".parcial")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        try:
            os.chmod(temporal, 0o644)  # mkstemp crea 0600
        except OSError:
            pass
        os.replace(temporal, ruta)
    except BaseException:
        try:
            os.remove(temporal)
        except OSError:
            pass
        raise


def salida_utf8():
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def correr(script, *argumentos):
    """Ejecuta un script hermano. Devuelve (código, json o None, stderr)."""
    ruta = AQUI / script
    if not ruta.is_file():
        return -1, None, f"no se encuentra {ruta}"
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    try:
        proceso = subprocess.run([sys.executable, str(ruta), *map(str, argumentos)],
                                 capture_output=True, env=entorno, timeout=TIEMPO.get(script, 600))
    except subprocess.TimeoutExpired:
        return -1, None, f"{script} superó {TIEMPO.get(script, 600)} s y se detuvo"
    except OSError as error:
        return -1, None, f"no se pudo lanzar {script}: {error}"
    salida = proceso.stdout.decode("utf-8", errors="replace")
    error = proceso.stderr.decode("utf-8", errors="replace").strip()
    try:
        datos = json.loads(salida) if salida.strip() else None
    except ValueError:
        datos = None
        error = (error + "\n" if error else "") + "salida no es JSON: " + salida[:300]
    return proceso.returncode, datos, error


def ultima_linea(texto):
    lineas = [l for l in (texto or "").splitlines() if l.strip()]
    return lineas[-1].strip() if lineas else ""


def recortar(texto, n=160):
    texto = re.sub(r"\s+", " ", texto or "").strip()
    return texto if len(texto) <= n else texto[:n - 1] + "…"


# ----------------------------------------------------------------- encargo.md

def leer_encargo(carpeta):
    """Campos de encargo.md: nivel, tipo, paginas (min, max), estado, y avisos."""
    datos = {"nivel": None, "tipo": None, "min": None, "max": None, "estado": "", "estado_texto": "",
             "paginas_texto": None, "existe": False}
    avisos = []
    ruta = carpeta / "encargo.md"
    if not ruta.is_file():
        avisos.append("la carpeta no tiene encargo.md: el hook no la reconocerá como encargo")
        return datos, avisos
    datos["existe"] = True
    with open(ruta, encoding="utf-8-sig", errors="replace") as f:
        lineas = f.read().splitlines()
    for linea in lineas:
        # mismo criterio que el hook: sin tildes, sin * ni _, sin viñetas, minúsculas
        limpia = sin_tildes(linea).replace("*", "").replace("_", "").strip(" \t-#>").lower()
        m = re.match(r"(nivel|tipo|paginas|extension|estado)\s*:\s*(.*)$", limpia)
        if not m:
            continue
        clave, valor = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip(" .`'\"")
        original = re.sub(r"\s+", " ", linea.split(":", 1)[1]).strip(" *_`.'\"")
        if clave == "estado" and not datos["estado"]:
            datos["estado"] = valor  # normalizado como en el hook (sin tildes, minúsculas)
            datos["estado_texto"] = original
        elif clave == "nivel" and datos["nivel"] is None:
            datos["nivel"] = next((n for n in NIVELES if n in valor), None)
            if datos["nivel"] is None:
                avisos.append(f"nivel no reconocido en encargo.md: «{valor}»; se asume pregrado")
        elif clave == "tipo" and datos["tipo"] is None:
            datos["tipo"] = next((TIPOS[t] for t in TIPOS if re.search(rf"\b{t}\b", valor)), None)
            if datos["tipo"] is None:
                avisos.append(f"tipo no reconocido en encargo.md: «{valor}»; formato sin --tipo")
        elif clave in ("paginas", "extension") and datos["paginas_texto"] is None:
            datos["paginas_texto"] = original
            datos["min"], datos["max"] = leer_paginas(valor)
            if datos["min"] is None and datos["max"] is None:
                avisos.append(f"extensión no reconocida en encargo.md: «{valor}»; páginas sin límites")
    if not datos["estado"]:
        avisos.append("encargo.md no tiene línea «estado:»")
    if datos["tipo"] is None and not any("tipo" in a for a in avisos):
        avisos.append("encargo.md no indica el tipo: el formato se revisa sin --tipo")
    if datos["paginas_texto"] is None:
        avisos.append("encargo.md no indica páginas: no se controla la extensión")
    return datos, avisos


def leer_paginas(valor):
    """'8' -> (8, 8); '8-10' / '8 a 10' -> (8, 10); 'mínimo 8' -> (8, None); 'máximo 10' -> (None, 10)."""
    v = valor.lower()
    m = re.search(r"(\d+)\s*(?:-|–|a|al|hasta)\s*(\d+)", v)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return min(a, b), max(a, b)
    m = re.search(r"(\d+)", v)
    if not m:
        return None, None
    n = int(m.group(1))
    if re.search(r"\bmin|\bal menos|\bdesde", v):
        return n, None
    if re.search(r"\bmax|\bhasta|\bno mas de", v):
        return None, n
    return n, n


# ----------------------------------------------------------------- entregable

def es_docx(nombre):
    bajo = nombre.lower()
    return bajo.endswith(".docx") and not nombre.startswith("~$")


def es_xlsx(nombre):
    return nombre.lower().endswith(".xlsx") and not nombre.startswith("~$")


def buscar_entregable(carpeta, archivo):
    """Devuelve (ruta, None) o (None, mensaje de error)."""
    entrega = carpeta / "entrega"
    if archivo:
        ruta = Path(archivo)
        if not ruta.is_absolute():  # "entrega/x.docx" (relativo al encargo) o "x.docx"
            ruta = carpeta / ruta if (carpeta / ruta).is_file() else entrega / ruta
        ruta = ruta.resolve()
        if not ruta.is_file():
            return None, f"no existe el archivo {ruta}"
        try:
            ruta.relative_to(entrega.resolve())
        except ValueError:
            return None, f"el entregable debe estar dentro de {entrega}"
        if ruta.suffix.lower() not in (".docx", ".xlsx"):
            return None, "control_final.py solo controla entregables .docx y .xlsx"
        return ruta, None
    if not entrega.is_dir():
        return None, f"no existe la carpeta {entrega}"
    def listar(prueba):
        hallados = []
        for hijo in sorted(entrega.iterdir()):
            if hijo.is_file() and prueba(hijo.name):
                hallados.append(hijo)
            elif hijo.is_dir():
                hallados.extend(n for n in sorted(hijo.iterdir()) if n.is_file() and prueba(n.name))
        return hallados
    candidatos, tipo = listar(es_docx), ".docx"
    if not candidatos:  # sin .docx: un único .xlsx es el entregable principal
        candidatos, tipo = listar(es_xlsx), ".xlsx"
    if not candidatos:
        return None, f"no hay ningún .docx ni .xlsx en {entrega}"
    if len(candidatos) > 1:
        nombres = ", ".join(str(c.relative_to(entrega)) for c in candidatos)
        return None, f"hay varios {tipo} en entrega/ ({nombres}): indique cuál con --archivo"
    return candidatos[0].resolve(), None


def otros_entregables(entrega, principal):
    """Archivos que el hook también considera entregables y este control no revisa."""
    ext = (".docx", ".xlsx", ".pptx", ".pdf")
    otros = []
    for raiz in [entrega] + [d for d in entrega.iterdir() if d.is_dir()]:
        for n in raiz.iterdir():
            bajo = n.name.lower()
            if n.is_file() and bajo.endswith(ext) and not n.name.startswith("~$") \
                    and n.resolve() != principal:
                otros.append(str(n.relative_to(entrega)))
    return sorted(otros)


# ----------------------------------------------------------------- hoja de cálculo

ERRORES_EXCEL = ("#REF!", "#DIV/0!", "#N/A", "#NAME?", "#VALUE!", "#NULL!", "#NUM!")
PATRON_MARCADOR = re.compile(r"por\s+verificar|pendiente\s*:|\[\s*cita\s*\]|\bTODO\b|\bXXX\b",
                             re.I)
NS_HOJA = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def marcador_en(texto):
    """Marcador prohibido en un texto; TODO y XXX solo en mayúsculas."""
    for m in PATRON_MARCADOR.finditer(texto or ""):
        if m.group(0).upper() in ("TODO", "XXX") and m.group(0) not in ("TODO", "XXX"):
            continue
        return m.group(0)
    return None


def texto_si(elemento):
    """Texto de un <si> o <is> (con o sin formato enriquecido)."""
    return "".join(t.text or "" for t in elemento.iter(NS_HOJA + "t"))


def control_hoja(ruta, detalle, avisos):
    """Control "hoja" de un .xlsx. Devuelve el dict del control."""
    import xml.etree.ElementTree as ET
    import zipfile
    try:
        paquete = zipfile.ZipFile(ruta)
    except (zipfile.BadZipFile, OSError) as error:
        detalle["bloqueos"].append(("hoja", f"el .xlsx no es un zip válido: {error}"))
        return control(1, "bloquea", "BLOQUEA: el archivo no es un .xlsx legible (zip roto)")
    problemas, avisos_hoja = [], []
    with paquete:
        dañado = paquete.testzip()
        nombres = set(paquete.namelist())
        if dañado:
            problemas.append(f"zip dañado: la parte {dañado} no supera la suma de control")
        for obligatoria in ("[Content_Types].xml", "xl/workbook.xml"):
            if obligatoria not in nombres:
                problemas.append(f"falta la parte {obligatoria}")
        arboles = {}
        for nombre in sorted(nombres):
            if not nombre.lower().endswith((".xml", ".rels")) or nombre == dañado:
                continue
            try:
                arboles[nombre] = ET.fromstring(paquete.read(nombre))
            except (ET.ParseError, zipfile.BadZipFile, OSError) as error:
                problemas.append(f"XML ilegible en {nombre}: {error}")
        # Cadenas compartidas: marcadores prohibidos.
        compartidas = []
        if "xl/sharedStrings.xml" in arboles:
            compartidas = [texto_si(si) for si in arboles["xl/sharedStrings.xml"].iter(NS_HOJA + "si")]
        for texto in compartidas:
            marca = marcador_en(texto)
            if marca:
                problemas.append(f"marcador prohibido «{marca}» en el texto «{recortar(texto, 80)}»")
        # Nombres de hojas: workbook.xml + relaciones.
        hojas = {}
        libro, rels = arboles.get("xl/workbook.xml"), arboles.get("xl/_rels/workbook.xml.rels")
        if libro is not None and rels is not None:
            destinos = {r.get("Id"): r.get("Target", "") for r in rels}
            for hoja in libro.iter(NS_HOJA + "sheet"):
                destino = destinos.get(hoja.get(NS_REL + "id"), "")
                destino = destino.lstrip("/")
                destino = destino if destino.startswith("xl/") else "xl/" + destino
                hojas[destino] = hoja.get("name")
        for parte in sorted(n for n in arboles if re.match(r"xl/worksheets/[^/]+\.xml$", n)):
            nombre_hoja = hojas.get(parte, parte)
            con_valor = 0
            for celda in arboles[parte].iter(NS_HOJA + "c"):
                ref, tipo = celda.get("r", "?"), celda.get("t")
                valor = celda.findtext(NS_HOJA + "v")
                formula = celda.findtext(NS_HOJA + "f")
                en_linea = celda.find(NS_HOJA + "is")
                texto = texto_si(en_linea) if en_linea is not None else None
                if valor not in (None, "") or texto:
                    con_valor += 1
                if tipo == "s" and valor and valor.isdigit() and int(valor) < len(compartidas):
                    texto = compartidas[int(valor)]
                elif tipo == "str":
                    texto = valor
                if tipo == "e" or (valor or "").strip() in ERRORES_EXCEL or \
                        (texto or "").strip() in ERRORES_EXCEL:
                    problemas.append(f"hoja «{nombre_hoja}», celda {ref}: error "
                                     f"{(valor or texto or '').strip() or '(tipo error)'}")
                elif formula and "#REF!" in formula:
                    problemas.append(f"hoja «{nombre_hoja}», celda {ref}: fórmula con #REF! "
                                     f"(={recortar(formula, 60)})")
                if en_linea is not None and tipo == "inlineStr":
                    marca = marcador_en(texto)
                    if marca:
                        problemas.append(f"hoja «{nombre_hoja}», celda {ref}: marcador prohibido "
                                         f"«{marca}»")
            if not con_valor:
                avisos_hoja.append(f"la hoja «{nombre_hoja}» está vacía")
    avisos.extend(avisos_hoja)
    if problemas:
        detalle["bloqueos"].extend(("hoja", p) for p in problemas[:MAX_LISTA * 4])
        return control(1, "bloquea", f"BLOQUEA: {len(problemas)} problema(s) en la hoja de cálculo: "
                                     + "; ".join(recortar(p, 90) for p in problemas[:3]))
    if avisos_hoja:
        return control(0, "aviso", f"sin errores ni marcadores; {len(avisos_hoja)} hoja(s) vacía(s)")
    return control(0, "ok", f"{len(hojas) or 'las'} hoja(s) sin errores almacenados ni marcadores")


def no_aplica(motivo):
    return control(-1, "no aplica", motivo)


# ----------------------------------------------------------------- controles

def control(codigo, estado, resumen):
    return {"codigo": codigo, "estado": estado, "resumen": resumen}


def no_ejecutado(codigo, motivo, bloquea):
    return control(codigo, "no ejecutado", ("BLOQUEA: " if bloquea else "") + motivo)


def control_citas(docx, detalle, avisos):
    codigo, datos, error = correr("cruzar_citas.py", docx, "--json")
    if codigo not in (0, 1) or not isinstance(datos, dict):
        return no_ejecutado(codigo, "cruzar_citas.py no se pudo ejecutar: "
                            + (ultima_linea(error) or "sin salida"), True), None
    a = datos.get("a_citas_sin_referencia", [])
    b = datos.get("b_referencias_no_citadas", [])
    c = datos.get("c_autor_o_anio_discordante", [])
    d = datos.get("d_lista_de_referencias", [])
    obs = datos.get("observaciones", {})
    for x in a:
        detalle["bloqueos"].append(("citas", f"cita sin referencia: «{x.get('cita')}» "
                                    f"(párr. {x.get('parrafo')}): {recortar(x.get('contexto'), 140)}"))
    for x in b:
        detalle["bloqueos"].append(("citas", f"referencia no citada: {recortar(x, 140)}"))
    for x in c:
        detalle["bloqueos"].append(("citas", f"autor o año discordante: «{x.get('cita')}» "
                                    f"(párr. {x.get('parrafo')}): {x.get('problema')}"))
    for x in d:
        avisos.append(f"citas: referencia {x.get('tipo')}: {recortar(x.get('referencia'), 90)} "
                      f"— {x.get('detalle')}")
    for x in obs.get("localizadores", []):
        avisos.append(f"citas: localizador de página o párrafo «{x.get('localizador')}» "
                      f"(párr. {x.get('parrafo')}); la regla es citar sin localizador")
    for x in obs.get("siglas_sin_presentar", []):
        avisos.append(f"citas: {x.get('detalle')} (párr. {x.get('parrafo')})")
    for x in obs.get("referencias_sin_anio", []):
        avisos.append(f"citas: referencia sin año reconocible: {recortar(x, 90)}")
    resumen = (f"{datos.get('total_citas', 0)} citas, {datos.get('referencias', 0)} referencias; "
               f"sin referencia {len(a)}, no citadas {len(b)}, discordantes {len(c)}; "
               f"lista (orden/duplicadas) {len(d)}")
    estado = "bloquea" if (a or b or c) else ("aviso" if d or any(obs.get(k) for k in
                                              ("localizadores", "siglas_sin_presentar",
                                               "referencias_sin_anio")) else "ok")
    return control(codigo, estado, resumen), datos


def control_similitud(docx, fuentes, detalle, avisos):
    pdfs = sorted(p for p in fuentes.glob("*.pdf")) if fuentes.is_dir() else []
    texto = fuentes / "texto"
    if pdfs:
        codigo_e, datos_e, error_e = correr("extraer_texto.py", fuentes, "--json")
        if isinstance(datos_e, dict):
            for x in datos_e.get("sin_texto", []):
                avisos.append(f"similitud: {x.get('pdf')} no tiene texto extraíble (¿escaneado?): "
                              "no se pudo comparar; el verificador debe revisarlo a mano")
            for x in datos_e.get("errores", []):
                avisos.append(f"similitud: no se pudo extraer {x.get('pdf')}: {x.get('motivo')}")
        elif codigo_e != 0:
            avisos.append("similitud: extraer_texto.py falló: " + (ultima_linea(error_e) or "sin salida"))
    txts = sorted(texto.glob("*.txt")) if texto.is_dir() else []
    if not txts:
        if not pdfs:
            motivo = ("fuentes/ no tiene ningún PDF ni texto extraído: no hay contra qué comparar, "
                      "y solo se cita lo descargado y leído")
        else:
            motivo = "no se pudo obtener texto de los PDF de fuentes/ (fuentes/texto/ vacía)"
        return no_ejecutado(-1, motivo, True)
    codigo, datos, error = correr("similitud_fuentes.py", docx, fuentes, "--json")
    if codigo not in (0, 1) or not isinstance(datos, dict):
        return no_ejecutado(codigo, "similitud_fuentes.py no se pudo ejecutar: "
                            + (ultima_linea(error) or "sin salida"), True)
    hallazgos = datos.get("hallazgos", [])
    graves = [h for h in hallazgos if h.get("categoria") in ("COPIA", "CASI IDÉNTICA")]
    comillas = [h for h in hallazgos if h.get("categoria") == "ENTRE COMILLAS"]
    for h in graves:
        detalle["bloqueos"].append(("similitud", f"{h.get('categoria')} (párr. {h.get('parrafo')}, "
                                    f"{h.get('palabras_seguidas')} palabras seguidas) con "
                                    f"{h.get('archivo')}, p. {h.get('pagina')}: "
                                    f"«{recortar(h.get('oracion'), 150)}»"))
    for h in comillas:
        avisos.append(f"similitud: cita textual entre comillas (párr. {h.get('parrafo')}) de "
                      f"{h.get('archivo')}, p. {h.get('pagina')}: comprobar que lleve su cita")
    resumen = (f"{len(txts)} fuentes comparadas; copia {sum(h['categoria'] == 'COPIA' for h in graves)}, "
               f"casi idéntica {sum(h['categoria'] == 'CASI IDÉNTICA' for h in graves)}, "
               f"entre comillas {len(comillas)}")
    estado = "bloquea" if graves else ("aviso" if comillas else "ok")
    return control(codigo, estado, resumen)


def control_formato(docx, encargo, detalle, avisos):
    argumentos = [docx, "--json"]
    if encargo["tipo"]:
        argumentos += ["--tipo", encargo["tipo"]]
    if encargo["min"]:
        argumentos += ["--min-paginas", encargo["min"]]
    if encargo["max"]:
        argumentos += ["--max-paginas", encargo["max"]]
    if (encargo["nivel"] or "pregrado") != "pregrado":
        argumentos += ["--max-paginas-referencias", "1000"]  # el límite de 1,5 es solo de pregrado
    codigo, datos, error = correr("verificar_formato.py", *argumentos)
    if codigo not in (0, 1) or not isinstance(datos, dict) or "hallazgos" not in datos:
        motivo = (datos or {}).get("error") if isinstance(datos, dict) else None
        return no_ejecutado(codigo, "verificar_formato.py no se pudo ejecutar: "
                            + (motivo or ultima_linea(error) or "sin salida"), True)
    errores = [h for h in datos["hallazgos"] if h.get("nivel") == "ERROR"]
    for h in errores:
        lugares = "; ".join(recortar(l, 70) for l in h.get("lugares", [])[:4])
        detalle["bloqueos"].append(("formato", f"{h.get('comprobacion')}) {h.get('nombre')}: "
                                    f"{h.get('mensaje')}" + (f" — en: {lugares}" if lugares else "")))
    for h in datos["hallazgos"]:
        if h.get("nivel") == "AVISO":
            avisos.append(f"formato: {h.get('comprobacion')}) {h.get('nombre')}: {h.get('mensaje')}")
    paginas = datos.get("paginas")
    resumen = (f"{datos.get('errores', len(errores))} errores, {datos.get('avisos', 0)} avisos; "
               f"páginas: {paginas if paginas is not None else 'no medidas'}")
    if encargo["min"] or encargo["max"]:
        resumen += f" (pedido: {encargo['paginas_texto']})"
    estado = "bloquea" if (codigo == 1 or errores) else ("aviso" if datos.get("avisos") else "ok")
    return control(codigo, estado, resumen)


def control_referencias(docx, sin_red, pendientes):
    if sin_red:
        return no_ejecutado(-1, "se pidió --sin-red: la existencia de las referencias no se "
                            "comprobó en Crossref ni OpenAlex", False)
    codigo, datos, error = correr("verificar_referencias.py", docx, "--json")
    if not isinstance(datos, dict) or "referencias" not in datos:
        return no_ejecutado(codigo, "verificar_referencias.py no se pudo ejecutar: "
                            + (ultima_linea(error) or "sin salida"), False)
    if datos.get("red_caida"):
        return no_ejecutado(codigo, "sin red: no se pudo consultar Crossref ni OpenAlex", False)
    dudosas = 0
    for r in datos["referencias"]:
        if r.get("estado") != "ENCONTRADA":
            dudosas += 1
            anotar(pendientes, r.get("referencia"),
                   f"verificar_referencias: {r.get('estado')} ({recortar(r.get('detalle'), 120)}); "
                   "comprobar contra el archivo de fuentes/")
    conteo = datos.get("conteo", {})
    resumen = ", ".join(f"{k.lower()} {v}" for k, v in conteo.items())
    return control(codigo, "aviso" if dudosas else "ok", resumen)


def anotar(pendientes, referencia, motivo):
    clave = normalizar(referencia)[:120]
    for p in pendientes:
        if normalizar(p["referencia"])[:120] == clave:
            p["motivos"].append(motivo)
            return
    pendientes.append({"referencia": referencia, "motivos": [motivo]})


# --------------------------------------------------------- fuente en carpeta

def leer_indice(fuentes):
    ruta = fuentes / "indice.json"
    if not ruta.is_file():
        return [], None
    try:
        with open(ruta, encoding="utf-8-sig") as f:
            datos = json.load(f)
    except (OSError, ValueError) as error:
        return [], f"fuentes/indice.json ilegible: {error}"
    if isinstance(datos, dict):
        datos = datos.get("fuentes") or list(datos.values())
    return [e for e in datos if isinstance(e, dict)], None


def bloques_fichas(fuentes):
    """Bloques de fichas.md: por encabezados si los hay; si no, por párrafos."""
    ruta = fuentes / "fichas.md"
    if not ruta.is_file():
        return None
    with open(ruta, encoding="utf-8-sig", errors="replace") as f:
        lineas = f.read().splitlines()
    con_encabezado = any(l.lstrip().startswith("#") for l in lineas)
    bloques, actual = [], []
    for linea in lineas:
        corte = linea.lstrip().startswith("#") if con_encabezado else not linea.strip()
        if corte and actual:
            bloques.append(" ".join(actual))
            actual = []
        if linea.strip():
            actual.append(linea)
    if actual:
        bloques.append(" ".join(actual))
    return [f" {normalizar(b)} " for b in bloques]


def anio_base(anio):
    anio = (anio or "").strip()
    if anio.startswith("s.f"):
        return "s f"
    return re.sub(r"[a-z]$", "", anio)


def tiene_autor_y_anio(texto_n, autor, sigla, anio):
    if not anio:
        return False
    nombres = [normalizar(autor)] + ([normalizar(sigla)] if sigla else [])
    return any(n and f" {n} " in texto_n for n in nombres) and f" {anio} " in texto_n


def control_fuentes(datos_citas, fuentes, pendientes, avisos):
    if not datos_citas or not datos_citas.get("analisis_referencias"):
        return no_ejecutado(-1, "sin lista de referencias analizada (ver control de citas)", False)
    indice, error_indice = leer_indice(fuentes)
    if error_indice:
        avisos.append("fuentes: " + error_indice)
    fichas = bloques_fichas(fuentes)
    if fichas is None:
        avisos.append("fuentes: no existe fuentes/fichas.md")
        fichas = []
    archivos = [p for p in fuentes.iterdir() if p.is_file() and p.suffix.lower() in
                (".pdf", ".html", ".htm", ".txt", ".docx", ".epub", ".xlsx", ".csv")] \
        if fuentes.is_dir() else []
    con_archivo = con_ficha = 0
    for r in datos_citas["analisis_referencias"]:
        ref = r.get("referencia") or ""
        ref_n = f" {normalizar(ref)} "
        autor, sigla, anio = r.get("primer_autor") or "", r.get("sigla"), anio_base(r.get("anio"))
        doi = re.search(r"10\.\d{4,9}/[^\s\"<>]+", ref)
        doi = doi.group(0).rstrip(".,;)").lower() if doi else None
        archivo = None
        for e in indice:
            nombre = e.get("archivo")
            if not nombre or not (fuentes / nombre).is_file():
                continue
            titulo = normalizar(e.get("titulo") or "")
            if (doi and (e.get("doi") or "").lower() == doi) or \
                    (len(titulo) >= 15 and f" {titulo} " in ref_n):
                archivo = nombre
                break
        if archivo is None and autor and anio:
            for p in archivos:  # nombre del archivo con primer autor y año
                if tiene_autor_y_anio(f" {normalizar(p.stem)} ", autor, sigla, anio):
                    archivo = p.name
                    break
        ficha = any(tiene_autor_y_anio(b, autor, sigla, anio) for b in fichas) if autor else False
        con_archivo += archivo is not None
        con_ficha += ficha
        if archivo is None and not ficha:
            anotar(pendientes, ref, "fuente en carpeta: sin archivo en fuentes/ ni ficha en fichas.md")
        elif archivo is None:
            anotar(pendientes, ref, "fuente en carpeta: tiene ficha pero no se localizó su archivo "
                                    "en fuentes/ (ni en indice.json ni por nombre)")
        elif not ficha:
            avisos.append(f"fuentes: {recortar(ref, 80)} tiene archivo ({archivo}) pero no ficha")
    total = len(datos_citas["analisis_referencias"])
    resumen = f"{total} referencias: con archivo {con_archivo}, con ficha {con_ficha}"
    return control(0, "ok" if con_archivo == total and con_ficha == total else "aviso", resumen)


# ----------------------------------------------------------------- informe

def informe_md(r, encargo, detalle):
    si = r["aprobado_mecanico"]
    l = ["# Control mecánico final", "",
         f"- Archivo controlado: `entrega/{r['archivo']}`",
         f"- Huella sha256: `{r['sha256']}`",
         f"- Fecha: {r['fecha']}",
         f"- Encargo: nivel {encargo['nivel'] or 'pregrado (por defecto)'}; tipo "
         f"{encargo['tipo'] or 'sin indicar'}; páginas {encargo['paginas_texto'] or 'sin indicar'}; "
         f"estado «{encargo['estado_texto'] or 'sin línea estado'}»", "",
         f"**Resultado del control mecánico: {'superado' if si else 'NO superado'}.**", "",
         "Esto no es el dictamen del verificador: solo dice si los controles automáticos "
         "están en regla para este archivo exacto. Si el archivo cambia, hay que volver a "
         "correr control_final.py.", "",
         "| Control | Estado | Resumen |", "|---|---|---|"]
    for nombre in r["controles"]:
        c = r["controles"][nombre]
        l.append(f"| {nombre} | {c['estado']} | {c['resumen'].replace('|', '/')} |")
    l += ["", "## Qué bloquea", ""]
    bloqueos = detalle["bloqueos"] + [(n, r["controles"][n]["resumen"]) for n in r["controles"]
                                      if r["controles"][n]["resumen"].startswith("BLOQUEA")]
    l += [f"- **{n}**: {t}" for n, t in bloqueos] or ["- Nada."]
    l += ["", "## Pendientes para el verificador (comprobar a mano)", ""]
    if r["pendientes_verificador"]:
        l.append("No bloquean por sí solos; el verificador decide. Abrir el archivo de "
                 "`fuentes/` (o buscarlo) y confirmar que la obra existe y dice lo citado.")
        l.append("")
        for p in r["pendientes_verificador"]:
            l.append(f"- {recortar(p['referencia'], 200)}")
            l += [f"  - {m}" for m in p["motivos"]]
    else:
        l.append("- Ninguno de los controles automáticos dejó referencias pendientes.")
    l += ["", "## Avisos (no bloquean)", ""]
    l += [f"- {a}" for a in r["avisos"]] or ["- Ninguno."]
    l += ["", "## Lo que este control no cubre", "",
          "- Cita contra pasaje: que cada fuente diga lo que el texto le atribuye "
          "(`extraer_texto.py --buscar \"frase\" fuentes`).",
          "- Cifras frente al script de análisis o la fuente.",
          "- Ortografía, concordancia, voz y nivel del texto.",
          "- Número y tipo de fuentes según el perfil del nivel.", ""]
    return "\n".join(l)


def imprimir_tabla(r):
    print(f"Archivo: entrega/{r['archivo']}")
    print(f"{'Control':<12} {'Estado':<13} Resumen")
    for nombre in r["controles"]:
        c = r["controles"][nombre]
        print(f"{nombre:<12} {c['estado']:<13} {c['resumen']}")
    if r["pendientes_verificador"]:
        print(f"\nPendientes para el verificador: {len(r['pendientes_verificador'])}")
        for p in r["pendientes_verificador"][:MAX_LISTA]:
            print(f"  - {recortar(p['referencia'], 100)}")
    if r["avisos"]:
        print(f"Avisos: {len(r['avisos'])} (ver entrega/controles.md)")


# ----------------------------------------------------------------- principal

def main(argv=None):
    salida_utf8()
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("carpeta", help="carpeta del encargo (la que tiene encargo.md)")
    analizador.add_argument("--archivo", help="entregable dentro de entrega/ (si hay varios .docx)")
    analizador.add_argument("--sin-red", action="store_true",
                            help="no consulta Crossref ni OpenAlex (referencias: no ejecutado)")
    analizador.add_argument("--json", action="store_true")
    args = analizador.parse_args(argv)

    carpeta = Path(args.carpeta).resolve()
    if not carpeta.is_dir():
        print(f"No se pudo ejecutar: no existe la carpeta {carpeta}", file=sys.stderr)
        return 2
    docx, error = buscar_entregable(carpeta, args.archivo)
    if error:
        print(f"No se pudo ejecutar: {error}", file=sys.stderr)
        return 2
    entrega = (carpeta / "entrega").resolve()
    fuentes = carpeta / "fuentes"
    huella = sha256_de(docx)
    encargo, avisos = leer_encargo(carpeta)
    if encargo["estado"].startswith(("no aprobado", "suspendido")):
        avisos.append(f"encargo.md dice estado «{encargo['estado_texto']}»")
    otros = otros_entregables(entrega, docx)
    if otros:
        avisos.append("en entrega/ hay otros archivos que el hook trata como entregables y este "
                      "control no revisa: " + ", ".join(otros))

    detalle = {"bloqueos": []}
    pendientes = []
    controles = {}
    if docx.suffix.lower() == ".xlsx":
        controles["hoja"] = control_hoja(docx, detalle, avisos)
        for nombre in ORDEN:
            controles[nombre] = no_aplica("no aplica a una hoja de cálculo (.xlsx)")
    else:
        controles["citas"], datos_citas = control_citas(docx, detalle, avisos)
        controles["similitud"] = control_similitud(docx, fuentes, detalle, avisos)
        controles["formato"] = control_formato(docx, encargo, detalle, avisos)
        controles["referencias"] = control_referencias(docx, args.sin_red, pendientes)
        controles["fuentes"] = control_fuentes(datos_citas, fuentes, pendientes, avisos) \
            if fuentes.is_dir() else no_ejecutado(-1, "no existe la carpeta fuentes/", False)

    if sha256_de(docx) != huella:
        print("No se pudo ejecutar: el entregable cambió mientras corrían los controles; "
              "vuelva a ejecutar.", file=sys.stderr)
        return 2

    def bloquea(nombre, c):
        if c["estado"] == "bloquea":
            return True
        return c["estado"] == "no ejecutado" and nombre not in NO_BLOQUEAN_SI_NO_CORREN

    resultado = {
        "archivo": docx.relative_to(entrega).as_posix(),
        "sha256": huella,
        "fecha": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "aprobado_mecanico": not any(bloquea(n, c) for n, c in controles.items()),
        "controles": controles,
        "pendientes_verificador": pendientes,
        "avisos": avisos,
    }
    escribir_atomico(entrega / "controles.json",
                     json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    escribir_atomico(entrega / "controles.md", informe_md(resultado, encargo, detalle))
    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        imprimir_tabla(resultado)
        if detalle["bloqueos"]:
            print("\nQué bloquea:")
        for nombre, texto in detalle["bloqueos"][:MAX_LISTA]:
            print(f"  [{nombre}] {texto}")
        if len(detalle["bloqueos"]) > MAX_LISTA:
            print(f"  ... y {len(detalle['bloqueos']) - MAX_LISTA} más en entrega/controles.md")
        print("\nCONTROL MECÁNICO: " + ("APROBADO" if resultado["aprobado_mecanico"]
                                       else "NO APROBADO"))
    return 0 if resultado["aprobado_mecanico"] else 1


if __name__ == "__main__":
    sys.exit(main())
