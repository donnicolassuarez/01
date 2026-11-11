# -*- coding: utf-8 -*-
"""Crea una biblioteca Zotero sintética para probar zotero_apa.py.

Uso: python pruebas/crear_zotero_prueba.py [carpeta_destino]
Por defecto: pruebas/salida/caso_zotero/

Reproduce las tablas del esquema real de Zotero 6/7 que usa
zotero_apa.py (con los mismos nombres de tablas y columnas) y carga
ítems reales cuyos metadatos se tomaron de Crossref el 2026-11-11:
artículo con 3 autores y DOI, artículo con 106 autores, libro con
edición, capítulo de libro editado, tesis de maestría, tesis de
doctorado, informe institucional, página web sin fecha, una ley, una
nota suelta (debe excluirse), un duplicado en la papelera (debe
excluirse) y un adjunto PDF con su archivo en storage/<clave>/.

Es una biblioteca sintética: no sustituye la prueba sobre la
biblioteca real del usuario.
"""
import sqlite3
import sys
from pathlib import Path

ESQUEMA = """
CREATE TABLE libraries (libraryID INTEGER PRIMARY KEY, type TEXT NOT NULL,
    editable INT NOT NULL, filesEditable INT NOT NULL, version INT NOT NULL DEFAULT 0,
    storageVersion INT NOT NULL DEFAULT 0, lastSync INT NOT NULL DEFAULT 0, archived INT NOT NULL DEFAULT 0);
CREATE TABLE itemTypes (itemTypeID INTEGER PRIMARY KEY, typeName TEXT,
    templateItemTypeID INT, display INT DEFAULT 1);
CREATE TABLE itemTypesCombined (itemTypeID INT NOT NULL, typeName TEXT NOT NULL,
    display INT DEFAULT 1 NOT NULL, custom INT NOT NULL, PRIMARY KEY (itemTypeID));
CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT, fieldFormatID INT);
CREATE TABLE fieldsCombined (fieldID INT NOT NULL, fieldName TEXT NOT NULL,
    label TEXT, fieldFormatID INT, custom INT NOT NULL, PRIMARY KEY (fieldID));
CREATE TABLE creatorTypes (creatorTypeID INTEGER PRIMARY KEY, creatorType TEXT);
CREATE TABLE items (itemID INTEGER PRIMARY KEY, itemTypeID INT NOT NULL,
    dateAdded TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dateModified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    clientDateModified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    libraryID INT NOT NULL, key TEXT NOT NULL, version INT NOT NULL DEFAULT 0,
    synced INT NOT NULL DEFAULT 0, UNIQUE (libraryID, key));
CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value UNIQUE);
CREATE TABLE itemData (itemID INT, fieldID INT, valueID, PRIMARY KEY (itemID, fieldID));
CREATE TABLE creators (creatorID INTEGER PRIMARY KEY, firstName TEXT, lastName TEXT,
    fieldMode INT, UNIQUE (lastName, firstName, fieldMode));
CREATE TABLE itemCreators (itemID INT NOT NULL, creatorID INT NOT NULL,
    creatorTypeID INT NOT NULL DEFAULT 1, orderIndex INT NOT NULL DEFAULT 0,
    PRIMARY KEY (itemID, orderIndex), UNIQUE (itemID, creatorID, creatorTypeID, orderIndex));
CREATE TABLE collections (collectionID INTEGER PRIMARY KEY, collectionName TEXT NOT NULL,
    parentCollectionID INT DEFAULT NULL, clientDateModified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    libraryID INT NOT NULL, key TEXT NOT NULL, version INT NOT NULL DEFAULT 0,
    synced INT NOT NULL DEFAULT 0, UNIQUE (libraryID, key));
CREATE TABLE collectionItems (collectionID INT NOT NULL, itemID INT NOT NULL,
    orderIndex INT NOT NULL DEFAULT 0, PRIMARY KEY (collectionID, itemID));
CREATE TABLE itemAttachments (itemID INTEGER PRIMARY KEY, parentItemID INT, linkMode INT,
    contentType TEXT, charsetID INT, path TEXT, syncState INT DEFAULT 0,
    storageModTime INT, storageHash TEXT, lastProcessedModificationTime INT);
CREATE TABLE itemNotes (itemID INTEGER PRIMARY KEY, parentItemID INT, note TEXT, title TEXT);
CREATE TABLE deletedItems (itemID INTEGER PRIMARY KEY,
    dateDeleted DEFAULT CURRENT_TIMESTAMP NOT NULL);
"""

TIPOS = ["note", "attachment", "book", "bookSection", "journalArticle", "report",
         "thesis", "webpage", "statute", "annotation"]
CAMPOS = ["title", "publicationTitle", "volume", "issue", "pages", "date", "DOI", "url",
          "accessDate", "publisher", "place", "edition", "bookTitle", "university",
          "thesisType", "institution", "reportNumber", "reportType", "websiteTitle",
          "archive", "nameOfAct", "publicLawNumber", "dateEnacted", "ISBN", "language"]
TIPOS_CREADOR = ["author", "contributor", "editor", "translator", "seriesEditor", "bookAuthor"]

# Autores de Friedlingstein et al. (2022), en el orden de Crossref.
GCB_2022 = """Friedlingstein, Pierre; O'Sullivan, Michael; Jones, Matthew W.; Andrew, Robbie M.;
Gregor, Luke; Hauck, Judith; Le Quéré, Corinne; Luijkx, Ingrid T.; Olsen, Are; Peters, Glen P.;
Peters, Wouter; Pongratz, Julia; Schwingshackl, Clemens; Sitch, Stephen; Canadell, Josep G.;
Ciais, Philippe; Jackson, Robert B.; Alin, Simone R.; Alkama, Ramdane; Arneth, Almut;
Arora, Vivek K.; Bates, Nicholas R.; Becker, Meike; Bellouin, Nicolas; Bittig, Henry C.;
Bopp, Laurent; Chevallier, Frédéric; Chini, Louise P.; Cronin, Margot; Evans, Wiley;
Falk, Stefanie; Feely, Richard A.; Gasser, Thomas; Gehlen, Marion; Gkritzalis, Thanos;
Gloege, Lucas; Grassi, Giacomo; Gruber, Nicolas; Gürses, Özgür; Harris, Ian; Hefner, Matthew;
Houghton, Richard A.; Hurtt, George C.; Iida, Yosuke; Ilyina, Tatiana; Jain, Atul K.;
Jersild, Annika; Kadono, Koji; Kato, Etsushi; Kennedy, Daniel; Klein Goldewijk, Kees;
Knauer, Jürgen; Korsbakken, Jan Ivar; Landschützer, Peter; Lefèvre, Nathalie; Lindsay, Keith;
Liu, Junjie; Liu, Zhu; Marland, Gregg; Mayot, Nicolas; McGrath, Matthew J.; Metzl, Nicolas;
Monacci, Natalie M.; Munro, David R.; Nakaoka, Shin-Ichiro; Niwa, Yosuke; O'Brien, Kevin;
Ono, Tsuneo; Palmer, Paul I.; Pan, Naiqing; Pierrot, Denis; Pocock, Katie; Poulter, Benjamin;
Resplandy, Laure; Robertson, Eddy; Rödenbeck, Christian; Rodriguez, Carmen; Rosan, Thais M.;
Schwinger, Jörg; Séférian, Roland; Shutler, Jamie D.; Skjelvan, Ingunn; Steinhoff, Tobias;
Sun, Qing; Sutton, Adrienne J.; Sweeney, Colm; Takao, Shintaro; Tanhua, Toste; Tans, Pieter P.;
Tian, Xiangjun; Tian, Hanqin; Tilbrook, Bronte; Tsujino, Hiroyuki; Tubiello, Francesco;
van der Werf, Guido R.; Walker, Anthony P.; Wanninkhof, Rik; Whitehead, Chris;
Willstrand Wranne, Anna; Wright, Rebecca; Yuan, Wenping; Yue, Chao; Yue, Xu; Zaehle, Sönke;
Zeng, Jiye; Zheng, Bo"""

NEPSTAD = {
    "title": "Globalization of the Amazon soy and beef industries: Opportunities for conservation",
    "publicationTitle": "Conservation Biology", "volume": "20", "issue": "6",
    "pages": "1595-1603", "date": "2006-07-27 2006-07-27",
    "DOI": "10.1111/j.1523-1739.2006.00510.x",
}

# (clave, tipo, campos, creadores [(apellido, nombre, fieldMode, tipo)], eliminado)
ITEMS = [
    ("NEPS2006", "journalArticle", NEPSTAD,
     [("Nepstad", "Daniel C.", 0, "author"), ("Stickler", "Claudia M.", 0, "author"),
      ("Almeida", "Oriana T.", 0, "author")], False),
    ("FRIE2022", "journalArticle",
     {"title": "Global carbon budget 2022", "publicationTitle": "Earth System Science Data",
      "volume": "14", "issue": "11", "pages": "4811-4900", "date": "2022-11-11 2022-11-11",
      "DOI": "10.5194/essd-14-4811-2022"},
     [(a.split(",")[0].strip(), a.split(",")[1].strip(), 0, "author")
      for a in GCB_2022.replace("\n", " ").split(";")], False),
    ("HERN2014", "book",
     {"title": "Metodología de la investigación", "edition": "6", "publisher": "McGraw-Hill Education",
      "place": "México", "date": "2014-00-00 2014", "ISBN": "978-1-4562-2396-0"},
     [("Hernández Sampieri", "Roberto", 0, "author"), ("Fernández Collado", "Carlos", 0, "author"),
      ("Baptista Lucio", "María del Pilar", 0, "author")], False),
    ("ALCO2021", "bookSection",
     {"title": "The Guaraní expansion in southeastern Bolivia",
      "bookTitle": "The archaeology of the Upper Amazon", "pages": "243-264",
      "publisher": "University Press of Florida", "date": "2021-09-21 2021-09-21",
      "DOI": "10.5744/florida/9780813066905.003.0013"},
     [("Alconini", "Sonia", 0, "author"), ("Clasby", "Ryan", 0, "editor"),
      ("Nesbitt", "Jason", 0, "editor")], False),
    ("MCDE2024", "thesis",
     {"title": "Impacts of US deforestation on rainfall from mesoscale convective systems",
      "thesisType": "Master's thesis", "university": "Iowa State University",
      "place": "Ames, Iowa", "date": "2024-00-00 2024", "DOI": "10.31274/td-20240617-17"},
     [("McDermott", "Dylan", 0, "author")], False),
    ("MONT2003", "thesis",
     {"title": "Construyendo identidades: Los nuevos sujetos obreros en Bolivia",
      "thesisType": "Tesis de doctorado", "university": "Universidad Autónoma Metropolitana",
      "date": "2003-06-01 2003-06-01", "DOI": "10.24275/uami.sj139257h"},
     [("Montero Justiniano", "Jenny Lourdes", 0, "author")], False),
    ("IPCC2023", "report",
     {"title": "Climate change 2023: Synthesis report. Contribution of Working Groups I, II and III "
               "to the Sixth Assessment Report of the Intergovernmental Panel on Climate Change",
      "institution": "IPCC", "place": "Ginebra", "date": "2023-07-25 2023-07-25",
      "DOI": "10.59327/IPCC/AR6-9789291691647"},
     [("Intergovernmental Panel on Climate Change", "", 1, "author")], False),
    ("GCPWEB00", "webpage",
     {"title": "Global carbon budget", "websiteTitle": "Global Carbon Project",
      "url": "https://www.globalcarbonproject.org/carbonbudget/", "accessDate": "2026-11-11 10:00:00"},
     [("Global Carbon Project", "", 1, "author")], False),
    ("LEY1333B", "statute",
     {"nameOfAct": "Ley del Medio Ambiente", "publicLawNumber": "1333",
      "dateEnacted": "1992-04-27 1992-04-27"},
     [], False),
    ("NOTA0001", "note", {}, [], False),
    ("NEPSDUPL", "journalArticle", dict(NEPSTAD), [("Nepstad", "Daniel C.", 0, "author")], True),
]

ADJUNTO_PDF = "Nepstad et al. - 2006 - Globalization of the Amazon soy and beef industries.pdf"


def crear(destino):
    destino.mkdir(parents=True, exist_ok=True)
    base = destino / "zotero.sqlite"
    if base.exists():
        base.unlink()
    con = sqlite3.connect(base)
    con.executescript(ESQUEMA)
    con.execute("INSERT INTO libraries VALUES (1, 'user', 1, 1, 0, 0, 0, 0)")
    for i, tipo in enumerate(TIPOS, 1):
        con.execute("INSERT INTO itemTypes VALUES (?, ?, NULL, 1)", (i, tipo))
        con.execute("INSERT INTO itemTypesCombined VALUES (?, ?, 1, 0)", (i, tipo))
    for i, campo in enumerate(CAMPOS, 1):
        con.execute("INSERT INTO fields VALUES (?, ?, NULL)", (i, campo))
        con.execute("INSERT INTO fieldsCombined VALUES (?, ?, NULL, NULL, 0)", (i, campo))
    for i, tipo in enumerate(TIPOS_CREADOR, 1):
        con.execute("INSERT INTO creatorTypes VALUES (?, ?)", (i, tipo))
    id_tipo = {t: i for i, t in enumerate(TIPOS, 1)}
    id_campo = {c: i for i, c in enumerate(CAMPOS, 1)}
    id_creador_tipo = {t: i for i, t in enumerate(TIPOS_CREADOR, 1)}

    def valor(texto):
        con.execute("INSERT OR IGNORE INTO itemDataValues (value) VALUES (?)", (texto,))
        return con.execute("SELECT valueID FROM itemDataValues WHERE value = ?", (texto,)).fetchone()[0]

    def creador(apellido, nombre, modo):
        con.execute("INSERT OR IGNORE INTO creators (firstName, lastName, fieldMode) VALUES (?, ?, ?)",
                    (nombre, apellido, modo))
        return con.execute("SELECT creatorID FROM creators WHERE lastName = ? AND firstName = ? "
                           "AND fieldMode = ?", (apellido, nombre, modo)).fetchone()[0]

    ids = {}
    for clave, tipo, campos, creadores, eliminado in ITEMS:
        cur = con.execute("INSERT INTO items (itemTypeID, libraryID, key) VALUES (?, 1, ?)",
                          (id_tipo[tipo], clave))
        ids[clave] = cur.lastrowid
        for campo, texto in campos.items():
            con.execute("INSERT INTO itemData VALUES (?, ?, ?)",
                        (ids[clave], id_campo[campo], valor(texto)))
        for orden, (apellido, nombre, modo, rol) in enumerate(creadores):
            con.execute("INSERT INTO itemCreators VALUES (?, ?, ?, ?)",
                        (ids[clave], creador(apellido, nombre, modo), id_creador_tipo[rol], orden))
        if tipo == "note":
            con.execute("INSERT INTO itemNotes VALUES (?, NULL, ?, ?)",
                        (ids[clave], "<p>Nota de lectura</p>", "Nota de lectura"))
        if eliminado:
            con.execute("INSERT INTO deletedItems (itemID) VALUES (?)", (ids[clave],))

    # Adjunto PDF importado (linkMode 1) hijo del artículo de Nepstad.
    cur = con.execute("INSERT INTO items (itemTypeID, libraryID, key) VALUES (?, 1, 'PDFNEPS1')",
                      (id_tipo["attachment"],))
    con.execute("INSERT INTO itemAttachments (itemID, parentItemID, linkMode, contentType, path) "
                "VALUES (?, ?, 1, 'application/pdf', ?)",
                (cur.lastrowid, ids["NEPS2006"], "storage:" + ADJUNTO_PDF))
    carpeta = destino / "storage" / "PDFNEPS1"
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / ADJUNTO_PDF).write_bytes(b"%PDF-1.4\n% archivo de prueba\n%%EOF\n")

    # Colecciones: "Tesis GEI Pando" con una subcolección "Metodología".
    con.execute("INSERT INTO collections (collectionID, collectionName, libraryID, key) "
                "VALUES (1, 'Tesis GEI Pando', 1, 'COLGEI01')")
    con.execute("INSERT INTO collections (collectionID, collectionName, parentCollectionID, "
                "libraryID, key) VALUES (2, 'Metodología', 1, 1, 'COLMET01')")
    for orden, clave in enumerate(["NEPS2006", "FRIE2022", "IPCC2023", "GCPWEB00", "NEPSDUPL"]):
        con.execute("INSERT INTO collectionItems VALUES (1, ?, ?)", (ids[clave], orden))
    con.execute("INSERT INTO collectionItems VALUES (2, ?, 0)", (ids["HERN2014"],))
    con.commit()
    con.close()
    return base


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else raiz / "salida" / "caso_zotero"
    print("Biblioteca de prueba creada en", crear(destino))
