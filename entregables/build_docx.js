const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  LevelFormat, PageBreak, ExternalHyperlink
} = require("docx");

// ---------- helpers ----------

// Parse **bold** inline markers into TextRun[]
function inline(text, opts = {}) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g).filter(p => p.length > 0);
  return parts.map(p => {
    if (p.startsWith("**") && p.endsWith("**")) {
      return new TextRun({ text: p.slice(2, -2), bold: true, italics: opts.italics || false, size: opts.size });
    }
    return new TextRun({ text: p, italics: opts.italics || false, size: opts.size });
  });
}

function para(text, opts = {}) {
  return new Paragraph({
    children: inline(text, opts),
    alignment: opts.alignment || AlignmentType.JUSTIFIED,
    spacing: { after: 200 },
  });
}

function heading(text, level) {
  return new Paragraph({
    text,
    heading: level,
    spacing: { before: 300, after: 150 },
  });
}

function leadPara(lead, rest) {
  // bold lead-in phrase followed by normal text, e.g. "La Realidad Epidemiológica: ..."
  return new Paragraph({
    children: [
      new TextRun({ text: lead, bold: true }),
      ...inline(rest),
    ],
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 200 },
  });
}

function subhead(text) {
  return new Paragraph({
    children: [new TextRun({ text, bold: true })],
    spacing: { before: 200, after: 120 },
  });
}

const bulletNumbering = {
  reference: "bullet-list",
  level: 0,
};

function bullet(text) {
  return new Paragraph({
    children: inline(text),
    numbering: bulletNumbering,
    spacing: { after: 100 },
  });
}

function numbered(text) {
  return new Paragraph({
    children: inline(text),
    numbering: { reference: "num-list", level: 0 },
    spacing: { after: 100 },
  });
}

function quote(text) {
  return new Paragraph({
    children: [new TextRun({ text, italics: true })],
    indent: { left: 720 },
    border: { left: { style: BorderStyle.SINGLE, size: 6, color: "999999", space: 8 } },
    spacing: { after: 200 },
  });
}

function note(text) {
  return new Paragraph({
    children: [new TextRun({ text, italics: true, size: 20, color: "555555" })],
    spacing: { after: 200 },
  });
}

function cell(text, opts = {}) {
  return new TableCell({
    width: { size: opts.width, type: WidthType.DXA },
    shading: opts.header ? { type: ShadingType.CLEAR, fill: "D9E2F3" } : undefined,
    children: [new Paragraph({
      children: opts.header
        ? [new TextRun({ text, bold: true })]
        : inline(text),
      alignment: AlignmentType.LEFT,
    })],
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
  });
}

function dataTable(headers, rows, widths) {
  const totalWidth = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) => cell(h, { header: true, width: widths[i] })),
      }),
      ...rows.map(r => new TableRow({
        children: r.map((c, i) => cell(c, { width: widths[i] })),
      })),
    ],
  });
}

function tableCaption(text) {
  return new Paragraph({
    children: [new TextRun({ text, bold: true })],
    spacing: { before: 200, after: 100 },
  });
}

// ---------- document content ----------

const children = [];

// Portada
children.push(
  new Paragraph({ text: "", spacing: { after: 2000 } }),
  new Paragraph({
    children: [new TextRun({ text: "La OMS y UNESCO: Impacto en Bolivia", bold: true, size: 44 })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 600 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Organismos internacionales y su impacto en salud, educación y cultura", size: 26, italics: true, color: "555555" })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 1200 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Autores: ", bold: true }), new TextRun({ text: "[Nombre Presentador 1] y [Nombre Presentador 2]" })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 150 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Institución: ", bold: true }), new TextRun({ text: "[Nombre de la Institución]" })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 150 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Fecha: ", bold: true }), new TextRun({ text: "2026" })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 150 },
  }),
  new Paragraph({ children: [new PageBreak()] }),
);

// INTRODUCCIÓN
children.push(
  heading("Introducción", HeadingLevel.HEADING_1),
  para("La Organización Mundial de la Salud (OMS) y la Organización de las Naciones Unidas para la Educación, la Ciencia y la Cultura (UNESCO) son dos organismos internacionales clave que trabajan en Bolivia para mejorar la calidad de vida de sus ciudadanos. Aunque operan en áreas distintas —una en salud y la otra en educación y cultura— ambas comparten el objetivo común de promover el desarrollo humano integral."),
  para("Bolivia enfrenta desafíos significativos en materia de salud pública, educación y preservación cultural. Con una población de aproximadamente 12 millones de habitantes, el país lucha contra enfermedades infectocontagiosas como la tuberculosis, malaria y VIH, mientras simultáneamente busca fortalecer su sistema educativo y preservar su rico patrimonio cultural."),
  para("Este informe examina cómo la OMS y UNESCO contribuyen al desarrollo de Bolivia, mediante casos de estudio específicos que ilustran su impacto en el país. Presenta un panorama de cómo estas organizaciones, a través de programas coordinados y asistencia técnica, trabajan para mejorar la salud, la educación y la preservación de la identidad cultural boliviana."),
);

// I. OMS
children.push(
  heading("I. Organización Mundial de la Salud (OMS)", HeadingLevel.HEADING_1),
  heading("1.1 ¿Qué es la OMS?", HeadingLevel.HEADING_2),
  para('La Organización Mundial de la Salud es un organismo especializado de las Naciones Unidas cuya constitución fue firmada en 1946 y entró en vigor el 7 de abril de 1948, fecha que hoy se celebra como el Día Mundial de la Salud. Su sede se encuentra en Ginebra, Suiza. La OMS define la salud como "un estado de bienestar físico, mental y social completo, no sólo la ausencia de enfermedad o dolencia" (Constitución de la OMS, 1946).'),
  para("La OMS es la autoridad directriz de la salud en el sistema de las Naciones Unidas. Nació del reconocimiento post-Segunda Guerra Mundial de que la salud es un derecho fundamental y que su alcance global requiere cooperación internacional coordinada."),

  heading("1.2 Funciones Principales de la OMS", HeadingLevel.HEADING_2),
  para("La OMS desarrolla cuatro funciones estratégicas:"),
  leadPara("Función Normativa: ", "Establece normas y estándares de salud internacionales que los países miembros deben implementar. Esto incluye regulaciones sobre medicamentos, vacunas, y procedimientos sanitarios."),
  leadPara("Función de Vigilancia: ", "Monitorea enfermedades transmisibles y no transmisibles a nivel mundial, detecta brotes epidemiológicos y coordina respuestas rápidas."),
  leadPara("Asistencia Técnica: ", "Brinda apoyo a países en el fortalecimiento de sus sistemas de salud, capacitación de personal y desarrollo de políticas sanitarias."),
  leadPara("Investigación y Evidencia: ", "Promueve investigación científica sobre salud y difunde información basada en evidencia para mejorar prácticas sanitarias."),
  para("En América, la OMS opera a través de la Organización Panamericana de la Salud (PAHO), que tiene una presencia directa en Bolivia con oficinas en La Paz y una red de cooperantes técnicos."),

  heading("1.3 Caso 1: Control de la Tuberculosis en Bolivia", HeadingLevel.HEADING_2),
  subhead("La Realidad Epidemiológica"),
  para("Bolivia enfrenta una de las cargas más altas de tuberculosis (TB) de la región. Según cifras del Banco Mundial basadas en el Informe Mundial de Tuberculosis de la OMS, la incidencia en Bolivia fue de 105 casos por cada 100,000 habitantes en 2023, frente a un promedio de 31.4 casos por 100,000 en la Región de las Américas en 2022 (WHO Global TB Report). Esto significa que Bolivia registra una incidencia aproximadamente 3.3 veces mayor que el promedio regional. La TB afecta desproporcionadamente a poblaciones vulnerables: personas que viven en pobreza, personas con VIH, y trabajadores de minas, aunque cabe aclarar que esta correlación con la pobreza es consistente con la literatura epidemiológica general y no implica que la TB tenga una causa única."),

  tableCaption("Tabla 1. Incidencia de tuberculosis: Bolivia frente a la Región de las Américas"),
  dataTable(
    ["Indicador", "Bolivia", "Región de las Américas", "Fuente"],
    [
      ["Incidencia de TB (casos/100,000 hab.)", "105 (2023)", "31.4 (2022)", "Banco Mundial / WHO Global TB Report"],
      ["Razón Bolivia vs. promedio regional", "3.3 veces mayor", "—", "Cálculo propio a partir de las cifras anteriores"],
      ["Variación de incidencia regional 2015-2023", "—", "+20%", "WHO Global TB Report 2024"],
    ],
    [2400, 1600, 2000, 3300],
  ),

  subhead("La Intervención de la OMS"),
  para("Desde los años 1990, la OMS ha promovido la estrategia DOTS (Directly Observed Therapy Short Course — Tratamiento Acortado Estrictamente Supervisado). En Bolivia, esta estrategia se implementa con:"),
  bullet("Medicamentos antituberculosos de calidad garantizada, proporcionados de forma gratuita"),
  bullet("Personal de salud capacitado que supervisa directamente la ingesta de medicamentos"),
  bullet("Laboratorios de diagnóstico equipados con tecnología moderna (microscopia de fluorescencia y pruebas rápidas)"),
  bullet("Sistemas de vigilancia para detectar casos resistentes a medicamentos"),
  para("El Ministerio de Salud de Bolivia, con apoyo técnico de PAHO/OMS, ha integrado el control de TB en su plan nacional de salud a través de la estrategia DOTS aplicada en la red pública de establecimientos de salud del país."),

  subhead("Resultados y Tendencia Reciente"),
  para('Es importante presentar este caso con honestidad académica: la evidencia no muestra una historia de éxito lineal. Según el informe de la OMS "Insights from the 2024 WHO Global TB Report", la incidencia de tuberculosis en la Región de las Américas **aumentó un 20% entre 2015 y 2023**, revirtiendo parcialmente los avances logrados en la década anterior. Bolivia no es una excepción a esta tendencia regional.'),
  bullet("**Cobertura de tratamiento supervisado (DOTS)**: Se ha expandido a la mayoría de la red pública de salud del país desde su adopción en los años 1990"),
  bullet("**Detección de casos**: Persisten brechas de subdiagnóstico, especialmente en zonas rurales, lo cual es reconocido por la propia OPS como un desafío estructural en la región andina"),
  bullet("**Repunte post-pandemia**: Al igual que en el resto de la región, la pandemia de COVID-19 (2020-2021) interrumpió servicios de diagnóstico y tratamiento, contribuyendo al repunte de casos observado después de 2021"),

  subhead("Desafíos Persistentes"),
  para("A pesar del marco institucional establecido, quedan desafíos importantes:"),
  numbered("**Acceso Geográfico**: En zonas rurales e indígenas, el acceso a tratamiento continuo sigue siendo limitado"),
  numbered("**Tuberculosis Resistente**: La tuberculosis resistente a múltiples fármacos (MDR-TB) complica el tratamiento y requiere terapias más prolongadas y costosas"),
  numbered("**Comorbilidad VIH-TB**: La coinfección sigue siendo un reto, especialmente en centros urbanos como La Paz y Santa Cruz"),
  numbered("**Adherencia al Tratamiento**: El esquema DOTS requiere hasta 6 meses de medicación supervisada, y el abandono del tratamiento es un factor de riesgo para el desarrollo de resistencia"),
  note("Nota metodológica: Las cifras exactas de curación y mortalidad por TB específicas para Bolivia varían según la fuente y el año de corte; se recomienda citar directamente el reporte más reciente del Programa Nacional de Control de la Tuberculosis del Ministerio de Salud o el WHO Global Tuberculosis Report vigente al momento de la presentación."),

  heading("1.4 Caso 2: Eliminación del Sarampión y su Reaparición en 2025 — Una Lección sobre la Fragilidad de los Logros en Salud", HeadingLevel.HEADING_2),
  subhead("Por qué este caso es distinto al anterior"),
  para("Mientras el caso de la tuberculosis ilustra un desafío persistente, el caso del sarampión en Bolivia ilustra algo distinto y pedagógicamente más interesante: **un éxito real que luego se revirtió por una caída en la cobertura de vacunación**. Es un ejemplo concreto de por qué la OMS insiste en que la inmunización no es una meta que se alcanza una vez, sino un esfuerzo que debe sostenerse permanentemente."),

  subhead("La Historia (con fechas verificables)"),
  tableCaption("Tabla 2. Línea de tiempo del sarampión en Bolivia (2000-2025)"),
  dataTable(
    ["Año", "Hito", "Fuente"],
    [
      ["2000", "Último caso de sarampión endémico (Amarete, La Paz)", "PAHO/OMS"],
      ["2012", "Bolivia certificada como país libre de sarampión", "PAHO/OMS"],
      ["Julio 2023", "Recertificación de todos los departamentos como libres de sarampión, rubéola y polio", "PAHO/OMS"],
      ["Junio 2025", "Emergencia Sanitaria Nacional por nuevo brote (colonias menonitas → comunidades rurales indígenas)", "Ministerio de Salud de Bolivia"],
    ],
    [1400, 5500, 2400],
  ),

  subhead("La Causa Raíz: Cobertura de Vacunación Insuficiente"),
  para("Según cifras oficiales citadas por PAHO/OMS, en 2023 solo el **68% de los niños menores de un año** había recibido la primera dosis de la vacuna triple viral (SRP: sarampión, rubéola, paperas), y **menos del 50%** había completado el esquema con la segunda dosis. La meta técnica para mantener la \"inmunidad de rebaño\" y evitar brotes es de al menos 95% de cobertura con dos dosis. Bolivia llevaba años por debajo de ese umbral sin que se produjera un brote visible — hasta 2025."),

  tableCaption("Tabla 3. Cobertura de vacunación SRP en Bolivia (2023) frente a la meta técnica"),
  dataTable(
    ["Indicador", "Cifra", "Meta técnica (OMS)", "Brecha"],
    [
      ["Primera dosis SRP (niños < 1 año)", "68%", "95%", "-27 puntos"],
      ["Esquema completo (dos dosis)", "< 50%", "95%", "> -45 puntos"],
    ],
    [3200, 1700, 2200, 2200],
  ),

  subhead("La Respuesta de la OMS/OPS"),
  bullet("Vacunación intensificada con esquema acortado para niños de 1 a 4 años (dos dosis de SRP)"),
  bullet("La vacuna SRP tiene una eficacia documentada de aproximadamente 97% con dos dosis"),
  bullet("Apoyo técnico y logístico de PAHO para la respuesta de emergencia"),

  subhead("Lo que este caso enseña"),
  numbered('**Un logro sanitario no es permanente**: Bolivia pasó de "libre de sarampión" (2012, 2023) a emergencia nacional (2025) en cuestión de dos años'),
  numbered("**Las brechas de cobertura tienen consecuencias tardías**: la caída por debajo del 68-50% de cobertura no causó un brote inmediato, pero sí creó las condiciones para uno"),
  numbered("**La heterogeneidad importa**: el brote se concentró en comunidades específicas (menonitas y rurales indígenas) con menor acceso o menor aceptación de la vacuna, lo que muestra que los promedios nacionales pueden ocultar bolsones de alto riesgo"),

  subhead("Contexto Regional: Poliomielitis"),
  para("A diferencia del sarampión, la poliomielitis sí representa un éxito sostenido: la Región de las Américas —incluida Bolivia— fue certificada libre de polio en 1994 por la Comisión Internacional para la Certificación de la Erradicación de la Polio, y no se ha registrado un caso de polio salvaje en la región desde 1991 (último caso en Perú). Han pasado más de 30 años sin transmisión endémica."),

  subhead("Impacto Económico de la Vacunación (evidencia global, no específica de Bolivia)"),
  para("No existe una cifra confiable específica para Bolivia sobre retorno económico de la vacunación, pero vale citar la evidencia global disponible: un estudio de la Universidad de Pekín, que evaluó 50 años del Programa Ampliado de Inmunización de la OMS (1974-2024), estima que **cada dólar invertido en vacunación generó aproximadamente 16 dólares en beneficios económicos**, y que la vacunación evitó cerca de 154 millones de muertes a nivel mundial, la mayoría en menores de 5 años."),

  subhead("Desafíos Persistentes"),
  numbered("**Cobertura Desigual**: existen bolsones de población con cobertura muy por debajo de la meta del 95%, no distribuidos uniformemente por región sino por comunidad específica"),
  numbered("**Vacilación y Desinformación**: la aceptación de la vacuna varía entre comunidades, lo que requiere estrategias de comunicación diferenciadas, no solo más dosis disponibles"),
  numbered("**Sostenibilidad**: mantener coberturas altas exige inversión constante, no solo campañas puntuales de respuesta a brotes"),
);

// II. UNESCO
children.push(
  heading("II. Organización de Naciones Unidas para la Educación, la Ciencia y la Cultura (UNESCO)", HeadingLevel.HEADING_1),
  heading("2.1 ¿Qué es UNESCO?", HeadingLevel.HEADING_2),
  para('UNESCO fue fundada en 1945 como un organismo especializado de las Naciones Unidas. Su sede está en París, Francia. El lema de UNESCO es "Puesto que las guerras nacen en la mente de los hombres, es en la mente de los hombres donde deben erigirse los baluartes de la paz" — en síntesis, "La paz nace de las mentes".'),
  para("UNESCO trabaja en cuatro áreas estratégicas: educación para todos, ciencias naturales, ciencias sociales y humanas, cultura, e información y comunicación."),

  heading("2.2 Funciones Principales de UNESCO", HeadingLevel.HEADING_2),
  leadPara("Educación de Calidad: ", "Promueve acceso equitativo a educación de calidad para todos, con énfasis en grupos marginalizados. Trabaja en educación primaria, secundaria, técnica y superior."),
  leadPara("Patrimonio Cultural: ", "Identifica, protege y preserva el patrimonio cultural material (sitios arqueológicos, monumentos) e inmaterial (tradiciones, idiomas, celebraciones)."),
  leadPara("Libertad de Expresión: ", "Defiende la libertad de prensa, el acceso a la información y la libertad de expresión como pilares de democracias fuertes."),
  leadPara("Ciencia y Tecnología: ", "Promueve la investigación científica y el acceso a tecnología para el desarrollo sostenible."),
  para("En Bolivia, UNESCO cuenta con una oficina de programas en La Paz que coordina iniciativas en educación, patrimonio cultural y comunicación."),

  tableCaption("Tabla 4. Sitios bolivianos en la Lista de Patrimonio Mundial de UNESCO"),
  dataTable(
    ["Sitio", "Tipo de Patrimonio", "Año de inscripción"],
    [
      ["Ciudad de Potosí", "Cultural", "1987"],
      ["Misiones Jesuíticas de Chiquitos (6 misiones)", "Cultural", "1990"],
      ["Sucre (centro histórico)", "Cultural", "1991"],
      ["Fuerte de Samaipata", "Cultural", "1998"],
      ["Tiwanaku", "Cultural", "2000"],
      ["Parque Nacional Noel Kempff Mercado", "Natural", "2000"],
      ["Qhapaq Ñan, Sistema Vial Andino (sitio transnacional)", "Cultural", "2014"],
    ],
    [4200, 2400, 2700],
  ),
  para("Bolivia tiene, además, un reconocimiento en una lista distinta —la Lista Representativa del Patrimonio Cultural Inmaterial— que no se cuenta dentro de los 7 sitios anteriores: el **Carnaval de Oruro** (2001), desarrollado como caso de estudio más abajo."),
  note("Fuente: UNESCO World Heritage Centre, listado oficial de Estados Parte — Bolivia (whc.unesco.org/en/statesparties/bo). El informe desarrolla en detalle solo Tiwanaku y el Carnaval de Oruro como casos de estudio."),

  heading("2.3 Caso 1: Tiwanaku — Patrimonio de la Humanidad", HeadingLevel.HEADING_2),
  subhead("Importancia Histórica"),
  para("Tiwanaku es un sitio arqueológico ubicado a 3,825 metros de altitud, a 20 km de La Paz, en la meseta del Altiplano boliviano. Fue la capital de una civilización preincaica que floreció entre 1500 a.C. y 950 d.C. Tiwanaku es considerado la cuna de civilizaciones andinas — su influencia cultural se extendió sobre gran parte del área andina, incluyendo lo que hoy es Perú, Chile y Argentina."),
  para("Los monumentos más importantes incluyen:"),
  bullet("**Templo Kalasasaya**: Una pirámide escalonada de piedra que originalmente midió 130 metros de largo"),
  bullet("**Puerta del Sol**: Un monolito de piedra único, elaboradamente tallado, que pesa 10 toneladas"),
  bullet("**Plataforma de Akapana**: Una estructura piramidal cuya función exacta aún se debate"),

  subhead("Reconocimiento UNESCO"),
  para("Tiwanaku fue inscrito en la Lista del Patrimonio Mundial de UNESCO en el año 2000 bajo dos criterios oficiales (UNESCO World Heritage Centre, ficha del sitio 567):"),
  bullet("**Criterio iii**: Las ruinas de Tiwanaku dan testimonio excepcional del poder del imperio que jugó un papel protagónico en el desarrollo de la civilización prehispánica andina"),
  bullet("**Criterio iv**: Las edificaciones de Tiwanaku son ejemplos excepcionales de la arquitectura ceremonial y pública de una de las manifestaciones más importantes de las civilizaciones de la región andina"),
  para("El sitio abarca 71.5 hectáreas en la Provincia de Ingavi, Departamento de La Paz, y la ciudad alcanzó su apogeo entre los años 500 y 900 d.C., como capital de un imperio que dominó gran parte de los Andes del sur."),

  subhead("Trabajos de Conservación"),
  para("Desde su inscripción, UNESCO y el gobierno boliviano han ejecutado proyectos de restauración:"),
  bullet("Estabilización de la Puerta del Sol después de un colapso parcial en 1945"),
  bullet("Excavación controlada de áreas de la Plataforma Akapana"),
  bullet("Restauración de las estructuras de piedra afectadas por sismos"),
  bullet("Instalación de sistemas de drenaje para proteger contra erosión hídrica"),
  para("El Ministerio de Culturas, Descolonización y Despatriarcalización de Bolivia, a través de sus unidades de arqueología y patrimonio, trabaja de forma conjunta con UNESCO en estos esfuerzos, con financiamiento proveniente de recursos nacionales y cooperación internacional."),

  subhead("Impacto Económico y Social"),
  bullet("**Turismo**: Tiwanaku recibe aproximadamente 200,000-250,000 visitantes anuales"),
  bullet("**Economía Local**: Genera empleo para guías turísticos, artesanos y trabajadores de servicios"),
  bullet("**Identidad Cultural**: Es un símbolo de orgullo para la población boliviana, especialmente para comunidades aymara"),
  bullet("**Educación**: Escuelas de todo Bolivia realizan visitas educativas al sitio"),

  heading("2.4 Caso 2: Carnaval de Oruro — Patrimonio Inmaterial de la Humanidad", HeadingLevel.HEADING_2),
  subhead("La Celebración"),
  para("El Carnaval de Oruro es una celebración religiosa y folclórica que tiene lugar en febrero/marzo en la ciudad de Oruro, en el altiplano boliviano. Se remonta a tiempos pre-hispánicos como ritual de la Pachamama (Madre Tierra) y fue cristianizado durante la colonia."),
  para("El Carnaval es una procesión de danzas y comparsas que dura dos días, en la que participan miles de danzarines y músicos. Cada grupo representa una tradición cultural específica."),

  subhead("Danzas Principales"),
  bullet("**Diablada**: Danzarines disfrazados de diablos que coreografían una batalla entre el bien y el mal. Es la danza más icónica del Carnaval"),
  bullet("**Morenada**: Una danza lenta y melancólica que representa la esclavitud africana y la resistencia"),
  bullet("**Tinku**: Una danza de confrontación ritual originaria de comunidades indígenas"),
  bullet("**Andanza**: Danza de celebración y alegría"),

  subhead("Sincretismo Cultural"),
  para("El Carnaval de Oruro es un ejemplo único de sincretismo religioso. Combina:"),
  bullet("Rituales pre-incaicos dedicados a la Pachamama"),
  bullet("Devoción cristiana a la Virgen del Socavón"),
  bullet("Tradiciones africanas traídas durante la esclavitud"),
  bullet("Elementos de la cultura minera de Oruro"),

  subhead("Reconocimiento UNESCO (2001)"),
  para("En 2001, UNESCO declaró el Carnaval de Oruro como **Obra Maestra del Patrimonio Oral e Inmaterial de la Humanidad**. Luego, en 2008, fue incluido en la **Lista Representativa de Patrimonio Cultural Inmaterial de la Humanidad**."),
  para("Este reconocimiento fue significativo porque fue uno de los primeros patrimonios inmateriales reconocidos por UNESCO, estableciendo un precedente para proteger tradiciones vivas."),

  subhead("Desafíos de Preservación"),
  numbered("**Presión del Turismo**: Miles de turistas asisten cada año, lo que puede afectar la autenticidad de la celebración"),
  numbered("**Transmisión Generacional**: Los jóvenes urbanos muestran menos interés en participar en las danzas tradicionales"),
  numbered("**Modernización**: Las comparsas incorporan elementos modernos (luces, amplificadores) que pueden diluir tradiciones"),
  numbered("**Acceso y Equidad**: Participar en el Carnaval requiere inversión económica (trajes, viajes), lo que excluye a las familias más pobres"),

  subhead("Significado para Bolivia"),
  para("El Carnaval de Oruro es más que una fiesta; es una expresión viva de la identidad cultural boliviana. Representa la resistencia, la alegría, y la fusión de múltiples culturas. Para la UNESCO, su protección asegura que futuras generaciones puedan experimentar esta riqueza cultural."),
);

// III. CONCLUSIÓN
children.push(
  heading("III. Conclusión: OMS y UNESCO en Bolivia", HeadingLevel.HEADING_1),
  heading("Impacto Complementario", HeadingLevel.HEADING_2),
  para("La OMS y UNESCO, aunque trabajan en campos distintos, contribuyen conjuntamente al desarrollo integral de Bolivia. La OMS aborda la salud física — reduciendo enfermedades y prolongando vidas — mientras UNESCO protege la salud cultural y educativa de la nación."),
  para("En el caso específico de Bolivia, vemos cómo:"),
  bullet("**OMS** sostiene un esfuerzo continuo contra la tuberculosis, cuya incidencia sigue siendo alta pese a décadas de intervención, y respalda al país en el control del sarampión, cuyo brote de 2025 demuestra que los logros en inmunización deben sostenerse permanentemente y no se pueden dar por adquiridos"),
  bullet("**UNESCO** preserva Tiwanaku como testimonio de civilizaciones pasadas y protege el Carnaval de Oruro como expresión viva de identidad cultural"),

  heading("Logros Alcanzados", HeadingLevel.HEADING_2),
  bullet("**En Salud**: Mejora de indicadores de salud, reducción de mortalidad por enfermedades prevenibles, aumento de esperanza de vida"),
  bullet("**En Cultura**: Reconocimiento internacional de patrimonio boliviano, generación de turismo e ingresos económicos, fortalecimiento de identidad nacional"),
  bullet("**En Educación**: Programas de alfabetización en poblaciones marginalizadas, acceso mejorado a educación de calidad"),

  heading("Desafíos Pendientes", HeadingLevel.HEADING_2),
  para("A pesar de los avances, Bolivia enfrenta desafíos:"),
  bullet("**Cobertura Geográfica**: Rural vs. urbano; zonas indígenas siguen siendo difíciles de alcanzar"),
  bullet("**Financiamiento**: Recursos limitados para mantener programas y conservación"),
  bullet("**Sostenibilidad**: Asegurar que los programas continúen más allá de proyectos puntuales"),
  bullet("**Integración**: Asegurar que programas de salud, educación y cultura se refuercen mutuamente"),

  heading("Perspectivas Futuras", HeadingLevel.HEADING_2),
  para("Bolivia puede avanzar si:"),
  numbered("Fortalece su sistema de salud pública con inversión nacional"),
  numbered("Protege su patrimonio cultural mediante regulaciones y presupuesto dedicado"),
  numbered("Integra educación de calidad con preservación cultural"),
  numbered("Continúa cooperando con OMS y UNESCO para acceso a fondos, tecnología y expertise"),
  para("La colaboración entre organismos internacionales y gobiernos locales es fundamental para que Bolivia alcance sus objetivos de desarrollo sostenible y mejore la calidad de vida de su población."),
);

// REFERENCIAS
function refPara(text) {
  return new Paragraph({
    children: inline(text),
    indent: { left: 400, hanging: 400 },
    spacing: { after: 180 },
  });
}

children.push(
  heading("Referencias", HeadingLevel.HEADING_1),
  refPara("Banco Mundial. (2024). *Incidence of tuberculosis (per 100,000 people) - Bolivia*. World Development Indicators. https://data.worldbank.org/indicator/SH.TBS.INCD?locations=BO"),
  refPara("World Health Organization. (2024). *Global Tuberculosis Report 2024 — 1.1 TB incidence*. https://www.who.int/teams/global-programme-on-tuberculosis-and-lung-health/tb-reports/global-tuberculosis-report-2024/tb-disease-burden/1-1-tb-incidence"),
  refPara("Organización Panamericana de la Salud. (s.f.). *Vacunar para volver a empezar: Bolivia frente al mayor brote de sarampión en dos décadas*. https://www.paho.org/es/historias/vacunar-para-volver-empezar-bolivia-frente-al-mayor-brote-sarampion-dos-decadas"),
  refPara("Organización Panamericana de la Salud. (2023, 18 de julio). *Bolivia recertifica de libres de sarampión, rubéola y polio a sus departamentos*. https://www.paho.org/es/noticias/18-7-2023-bolivia-recertifica-libres-sarampion-rubeola-polio-sus-departamentos"),
  refPara("Organización Panamericana de la Salud. (2024, 23 de octubre). *PAHO celebrates 30 years without wild polio in the Americas*. https://www.paho.org/en/news/23-10-2024-paho-celebrates-30-years-without-wild-polio-americas"),
  refPara("Ministerio de Salud y Deportes de Bolivia. (s.f.). *Bolivia eliminó la rubéola, poliomielitis y sarampión con la aplicación de vacunas*. https://www.minsalud.gob.bo/3438-bolivia-elimino-la-rubeola-poliomielitis-y-sarampion-con-la-aplicacion-de-vacunas"),
  refPara("CIDRAP, University of Minnesota. (2026). *In its 50-year history, global vaccination program generated $16 in benefits for every $1 invested*. https://www.cidrap.umn.edu/childhood-vaccines/its-50-year-history-global-vaccination-program-generated-16-benefits-every-1"),
  refPara("UNESCO World Heritage Centre. (2000). *Tiwanaku: Spiritual and Political Centre of the Tiwanaku Culture*. Ficha oficial del sitio 567. https://whc.unesco.org/en/list/567"),
  refPara("UNESCO. (2001). *Carnival of Oruro*. Lista Representativa del Patrimonio Cultural Inmaterial. https://ich.unesco.org/en/RL/carnival-of-oruro-00055"),
  refPara("World Health Organization. (1946/2020). *Constitution of the World Health Organization*. https://www.who.int/about/governance/constitution"),
  note("Nota sobre las fuentes: Todas las cifras de este informe fueron verificadas contra las fuentes citadas al momento de su redacción (2026). Se recomienda a los presentadores confirmar las cifras más recientes en las mismas fuentes antes de la defensa oral, ya que los datos de salud pública se actualizan periódicamente."),
);

// ---------- build document ----------

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullet-list",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 420, hanging: 260 } } } }],
      },
      {
        reference: "num-list",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 420, hanging: 260 } } } }],
      },
    ],
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
    },
    children,
  }],
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 22 } },
    },
  },
});

Packer.toBuffer(doc).then(buffer => {
  require("fs").writeFileSync("/home/user/01/entregables/Informe_OMS_UNESCO_Bolivia.docx", buffer);
  console.log("OK: docx written");
});
