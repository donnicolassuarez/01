const pptxgen = require("pptxgenjs");
const path = require("path");

const IMG_OMS = "/home/user/01/paquete_claude_design/imagenes_OMS";
const IMG_UN = "/home/user/01/paquete_claude_design/imagenes_UNESCO";

// ---------- palette (from ESPECIFICACION_DISENO.md) ----------
const BG = "F7F3EC";
const TEXT = "2B2620";
const MUTED = "6B5F52";
const LINEC = "D8CFC0";
const WHITE = "FFFFFF";

const OMS_DARK = "0A3D62";     // portada/conclusion background
const OMS_PRIMARY = "0072BC";
const OMS_SECOND = "2E8B7E";
const OMS_ALERT = "C1440E";

const UN_DARK = "6B3410";      // portada/conclusion background
const UN_PRIMARY = "B5651D";
const UN_SECOND = "CC9B36";
const UN_ACCENT = "1B3A4B";

const FONT_HEAD = "Calibri";
const FONT_BODY = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
const PW = 13.333, PH = 7.5;

// ---------- helpers ----------

function bgSlide(color) {
  const s = pres.addSlide();
  s.background = { color };
  return s;
}

function footer(slide, text, dark) {
  slide.addText(text, {
    x: 0.5, y: PH - 0.42, w: PW - 1, h: 0.3,
    fontFace: FONT_BODY, fontSize: 10, color: dark ? "C9BFB2" : MUTED,
    align: "left", isTextBox: true, margin: 0,
  });
}

function pageNum(slide, n, dark) {
  slide.addText(String(n), {
    x: PW - 0.9, y: PH - 0.42, w: 0.5, h: 0.3,
    fontFace: FONT_BODY, fontSize: 10, color: dark ? "C9BFB2" : MUTED,
    align: "right", isTextBox: true, margin: 0,
  });
}

// Title/closing slide on a solid color background
function titleSlide({ eyebrow, title, subtitle, footerText, bgColor, logoPath, logoW, logoH }) {
  const s = bgSlide(bgColor);
  if (logoPath) {
    s.addImage({ path: logoPath, x: (PW - logoW) / 2, y: 0.9, w: logoW, h: logoH });
  }
  const titleY = logoPath ? 0.9 + logoH + 0.5 : 2.6;
  if (eyebrow) {
    s.addText(eyebrow.toUpperCase(), {
      x: 0.8, y: titleY, w: PW - 1.6, h: 0.4,
      fontFace: FONT_BODY, fontSize: 14, color: "E8DFD3", charSpacing: 3,
      align: "center", isTextBox: true, margin: 0,
    });
  }
  s.addText(title, {
    x: 0.8, y: titleY + (eyebrow ? 0.45 : 0), w: PW - 1.6, h: 1.1,
    fontFace: FONT_HEAD, fontSize: 40, bold: true, color: WHITE,
    align: "center", isTextBox: true, margin: 0,
  });
  if (subtitle) {
    s.addText(subtitle, {
      x: 1.3, y: titleY + (eyebrow ? 0.45 : 0) + 1.15, w: PW - 2.6, h: 0.6,
      fontFace: FONT_BODY, fontSize: 18, italic: true, color: "E8DFD3",
      align: "center", isTextBox: true, margin: 0,
    });
  }
  if (footerText) {
    s.addText(footerText, {
      x: 0.8, y: PH - 1.0, w: PW - 1.6, h: 0.5,
      fontFace: FONT_BODY, fontSize: 13, color: "C9BFB2",
      align: "center", isTextBox: true, margin: 0,
    });
  }
  return s;
}

// Standard content slide: light background + title bar (no underline, no stripe - just typography)
function contentSlide({ kicker, title, accent, n, footText }) {
  const s = bgSlide(BG);
  if (kicker) {
    s.addText(kicker.toUpperCase(), {
      x: 0.6, y: 0.42, w: PW - 1.2, h: 0.32,
      fontFace: FONT_BODY, fontSize: 12, bold: true, color: accent, charSpacing: 2,
      align: "left", isTextBox: true, margin: 0,
    });
  }
  s.addText(title, {
    x: 0.6, y: kicker ? 0.72 : 0.5, w: PW - 1.2, h: 0.7,
    fontFace: FONT_HEAD, fontSize: 30, bold: true, color: TEXT,
    align: "left", isTextBox: true, margin: 0,
  });
  footer(s, footText, false);
  pageNum(s, n, false);
  return s;
}

function bulletBox(slide, items, opts) {
  const paras = items.map((it, i) => {
    const runs = Array.isArray(it.runs) ? it.runs : [{ text: it, bold: false }];
    return {
      text: runs.map(r => r.text).join(""),
      options: {
        bullet: opts.bullet === false ? false : { code: "2022", indent: 18 },
        color: TEXT, fontFace: FONT_BODY, fontSize: opts.fontSize || 14,
        breakLine: true, paraSpaceAfter: opts.spaceAfter || 10,
      },
    };
  });
  // Build proper rich runs (bold spans) per paragraph
  const richParas = items.map((it) => {
    const runs = Array.isArray(it) ? it : [{ text: it, bold: false }];
    return runs.map((r, idx) => ({
      text: r.text,
      options: {
        bold: !!r.bold, color: r.color || TEXT, fontFace: FONT_BODY,
        fontSize: opts.fontSize || 14,
        breakLine: idx === runs.length - 1,
        bullet: idx === 0 ? (opts.bullet === false ? false : { code: "2022", indent: 18 }) : false,
        paraSpaceAfter: opts.spaceAfter || 10,
      },
    }));
  }).flat();
  slide.addText(richParas, {
    x: opts.x, y: opts.y, w: opts.w, h: opts.h,
    align: "left", isTextBox: true, margin: 0, valign: "top",
  });
}

function numberedCircleRow(slide, x, y, w, num, color, title, desc) {
  const circleSize = 0.55;
  slide.addShape("ellipse", { x, y, w: circleSize, h: circleSize, fill: { color }, line: { type: "none" } });
  slide.addText(String(num), {
    x, y, w: circleSize, h: circleSize, fontFace: FONT_HEAD, fontSize: 20, bold: true,
    color: WHITE, align: "center", valign: "middle", isTextBox: true, margin: 0,
  });
  slide.addText(title, {
    x: x + circleSize + 0.25, y: y - 0.06, w: w - circleSize - 0.25, h: 0.35,
    fontFace: FONT_HEAD, fontSize: 15, bold: true, color: TEXT,
    align: "left", isTextBox: true, margin: 0,
  });
  slide.addText(desc, {
    x: x + circleSize + 0.25, y: y + 0.3, w: w - circleSize - 0.25, h: 0.55,
    fontFace: FONT_BODY, fontSize: 12, color: MUTED,
    align: "left", isTextBox: true, margin: 0, valign: "top",
  });
}

function statCallout(slide, x, y, w, value, label, color) {
  slide.addText(value, {
    x, y, w, h: 0.8, fontFace: FONT_HEAD, fontSize: 44, bold: true, color,
    align: "center", isTextBox: true, margin: 0,
  });
  slide.addText(label, {
    x, y: y + 0.78, w, h: 0.5, fontFace: FONT_BODY, fontSize: 11, color: MUTED,
    align: "center", isTextBox: true, margin: 0,
  });
}

function nativeTable(slide, x, y, w, headerRow, bodyRows, opts = {}) {
  const headerColor = opts.headerColor || OMS_PRIMARY;
  const rows = [
    headerRow.map(h => ({
      text: h,
      options: { bold: true, color: WHITE, fill: { color: headerColor }, fontFace: FONT_BODY, fontSize: 11, align: "left", valign: "middle" },
    })),
    ...bodyRows.map((r, ri) => r.map((c, ci) => ({
      text: c,
      options: {
        color: TEXT, fontFace: FONT_BODY, fontSize: 11, align: "left", valign: "middle",
        fill: { color: ri % 2 === 0 ? WHITE : "FBF8F3" },
        bold: opts.boldCols && opts.boldCols.includes(ci),
      },
    }))),
  ];
  const rowHeight = opts.rowH || 0.36;
  slide.addTable(rows, {
    x, y, w, colW: opts.colW,
    rowH: Array(rows.length).fill(rowHeight),
    border: { type: "solid", color: LINEC, pt: 0.75 },
    autoPage: false,
  });
}

function imageCover(slide, imgPath, x, y, w, h) {
  slide.addImage({ path: imgPath, x, y, w, h, sizing: { type: "cover", w, h } });
}

// ======================================================================
// DECK — OMS (slides 1-7)
// ======================================================================

// Slide 1 — Portada
titleSlide({
  eyebrow: "Organismos Internacionales en Bolivia",
  title: "Organización Mundial de la Salud",
  subtitle: "¿Cómo cuida la salud en Bolivia?",
  footerText: "[Nombre Presentador 1]  ·  [Institución]  ·  2026",
  bgColor: OMS_DARK,
  logoPath: path.join(IMG_OMS, "OMS_S1_portada_logo.png"),
  logoW: 1.7, logoH: 1.7 * (1594/1477),
});

// Slide 2 — ¿Qué es la OMS?
{
  const s = contentSlide({ kicker: "Organismo especializado de la ONU", title: "¿Qué es la OMS?", accent: OMS_PRIMARY, n: 2, footText: "OMS en Bolivia" });
  imageCover(s, path.join(IMG_OMS, "OMS_S2_que-es-la-oms_sede-ginebra.jpg"), 7.6, 1.55, 5.2, 3.75);
  s.addText("Sede en Ginebra, Suiza", { x: 7.6, y: 5.32, w: 5.2, h: 0.22, fontFace: FONT_BODY, fontSize: 9, italic: true, color: MUTED, isTextBox: true, margin: 0 });
  s.addImage({ path: path.join(IMG_OMS, "OMS_EXTRA_paho_logo.png"), x: 8.5, y: 5.65, w: 2.4, h: 2.4 * (618/1793) });
  s.addText("PAHO/OPS — oficina regional de la OMS para las Américas: un ejemplo de gobernanza multinivel", {
    x: 7.6, y: 6.55, w: 5.2, h: 0.4, fontFace: FONT_BODY, fontSize: 9.5, italic: true, color: MUTED,
    align: "center", isTextBox: true, margin: 0,
  });
  bulletBox(s, [
    [{ text: "Constitución firmada en 1946; entró en vigor el ", bold: false }, { text: "7 de abril de 1948", bold: true }],
    [{ text: "Organismo especializado de las Naciones Unidas", bold: false }],
    [{ text: "Sede en ", bold: false }, { text: "Ginebra, Suiza", bold: true }],
    [{ text: "194 países miembros (incluyendo Bolivia)", bold: false }],
  ], { x: 0.6, y: 1.65, w: 6.6, h: 2.3, fontSize: 15, spaceAfter: 14 });

  s.addShape("rect", { x: 0.6, y: 4.05, w: 6.6, h: 1.5, fill: { color: WHITE }, line: { color: LINEC, width: 1 } });
  s.addText([
    { text: '"Estado de bienestar físico, mental y social completo,\nno sólo la ausencia de enfermedad"', options: { italic: true, fontSize: 14, color: TEXT, breakLine: true } },
    { text: "— Definición de Salud, OMS", options: { fontSize: 11, color: MUTED } },
  ], { x: 0.85, y: 4.2, w: 6.1, h: 1.2, isTextBox: true, margin: 0, align: "left", valign: "top" });

  s.addText([
    { text: "¿Sabían que…?  ", options: { bold: true, color: OMS_ALERT } },
    { text: "cuando nació la OMS, la tuberculosis era la principal causa de muerte en el mundo.", options: { color: TEXT } },
  ], { x: 0.6, y: 5.75, w: 6.6, h: 0.8, fontFace: FONT_BODY, fontSize: 13, isTextBox: true, margin: 0, align: "left", valign: "top" });
}

// Slide 3 — ¿Qué hace la OMS?
{
  const s = contentSlide({ kicker: "Cuatro funciones estratégicas", title: "Funciones Principales de la OMS", accent: OMS_PRIMARY, n: 3, footText: "OMS en Bolivia" });
  const items = [
    ["Establecer Normas", "Crea estándares internacionales de salud que todos los países deben cumplir"],
    ["Vigilancia de Enfermedades", "Monitorea enfermedades en todo el mundo, detecta brotes y epidemias"],
    ["Asistencia Técnica", "Ayuda a países a fortalecer sistemas de salud y entrena personal médico"],
    ["Investigación", "Promueve investigación científica y comparte evidencia con todos"],
  ];
  let y = 1.75;
  items.forEach(([t, d], i) => {
    numberedCircleRow(s, 0.7, y, 11.9, i + 1, OMS_PRIMARY, t, d);
    y += 1.15;
  });
  s.addShape("rect", { x: 0.6, y: y + 0.05, w: 12.13, h: 0.7, fill: { color: "EAF2F8" }, line: { type: "none" } });
  s.addText([
    { text: "En América:  ", options: { bold: true, color: OMS_PRIMARY } },
    { text: "la OMS funciona a través de PAHO (Organización Panamericana de la Salud), con oficina en La Paz.", options: { color: TEXT } },
  ], { x: 0.85, y: y + 0.17, w: 11.6, h: 0.5, fontFace: FONT_BODY, fontSize: 13, isTextBox: true, margin: 0, align: "left", valign: "middle" });
}

// Slide 4 — OMS en Bolivia
{
  const s = contentSlide({ kicker: "Presencia y contexto", title: "La OMS en Bolivia", accent: OMS_PRIMARY, n: 4, footText: "OMS en Bolivia" });
  imageCover(s, path.join(IMG_OMS, "OMS_S4_oms-en-bolivia_skyline-lapaz.jpg"), 0.6, 1.55, 12.13, 2.55);
  s.addText("La Paz, sede de la oficina de PAHO en Bolivia", {
    x: 0.6, y: 4.14, w: 8.5, h: 0.3, fontFace: FONT_BODY, fontSize: 10, italic: true, color: MUTED,
    align: "left", isTextBox: true, margin: 0,
  });
  s.addImage({ path: path.join(IMG_OMS, "OMS_EXTRA_ministerio-salud-bolivia_logo.png"), x: 10.9, y: 4.08, w: 1.5, h: 1.5 * (217/547) });

  const colW = 5.9;
  s.addText("Principales desafíos de salud", { x: 0.6, y: 4.6, w: colW, h: 0.35, fontFace: FONT_HEAD, fontSize: 15, bold: true, color: OMS_ALERT, isTextBox: true, margin: 0 });
  bulletBox(s, [
    [{ text: "Tuberculosis (105 casos/100,000 hab., 2023)" }],
    [{ text: "Cobertura de vacunación insuficiente en algunas comunidades" }],
    [{ text: "VIH/SIDA (principalmente La Paz y Santa Cruz)" }],
    [{ text: "Desnutrición infantil en el altiplano" }],
  ], { x: 0.6, y: 5.0, w: colW, h: 2.0, fontSize: 12.5, spaceAfter: 8 });

  s.addText("Un logro sostenido", { x: 6.83, y: 4.6, w: colW, h: 0.35, fontFace: FONT_HEAD, fontSize: 15, bold: true, color: OMS_SECOND, isTextBox: true, margin: 0 });
  bulletBox(s, [
    [{ text: "Región de las Américas libre de poliomielitis desde 1994 (30+ años)" }],
    [{ text: "Red de cooperantes técnicos en las principales ciudades" }],
    [{ text: "Colaboración permanente con el Ministerio de Salud" }],
  ], { x: 6.83, y: 5.0, w: colW, h: 2.0, fontSize: 12.5, spaceAfter: 8 });
}

// Slide 5 — Caso 1: Tuberculosis
{
  const s = contentSlide({ kicker: "Caso de estudio 1", title: "Tuberculosis en Bolivia", accent: OMS_ALERT, n: 5, footText: "OMS en Bolivia" });
  imageCover(s, path.join(IMG_OMS, "OMS_S5_caso-tuberculosis_bacteria-microscopio.jpg"), 9.2, 1.55, 3.53, 3.53);
  s.addText("Mycobacterium tuberculosis (microscopía electrónica) — CDC", {
    x: 9.2, y: 5.1, w: 3.53, h: 0.4, fontFace: FONT_BODY, fontSize: 9, italic: true, color: MUTED, isTextBox: true, margin: 0,
  });

  nativeTable(s, 0.6, 1.6, 8.35,
    ["Indicador", "Cifra"],
    [
      ["Incidencia Bolivia (2023)", "105 / 100,000 hab."],
      ["Incidencia Región Américas (2022)", "31.4 / 100,000 hab."],
      ["Diferencia", "3.3 veces mayor"],
    ],
    { headerColor: OMS_ALERT, colW: [5.35, 3.0] }
  );

  s.addText([
    { text: "Estrategia OMS — DOTS: ", options: { bold: true, color: TEXT } },
    { text: "tratamiento supervisado directamente por personal de salud, medicamentos gratuitos en la red pública, 6 meses de duración.", options: { color: TEXT } },
  ], { x: 0.6, y: 3.35, w: 8.35, h: 0.9, fontFace: FONT_BODY, fontSize: 12.5, isTextBox: true, margin: 0, align: "left", valign: "top" });

  s.addShape("rect", { x: 0.6, y: 4.35, w: 8.35, h: 1.15, fill: { color: "FBEDE7" }, line: { type: "none" } });
  s.addText([
    { text: "Dato honesto:  ", options: { bold: true, color: OMS_ALERT } },
    { text: "según la OMS, la incidencia de TB en la Región de las Américas aumentó 20% entre 2015 y 2023 — no es una historia de progreso lineal.", options: { color: TEXT } },
  ], { x: 0.85, y: 4.47, w: 7.85, h: 0.95, fontFace: FONT_BODY, fontSize: 12.5, isTextBox: true, margin: 0, align: "left", valign: "top" });

  s.addText("Desafíos que persisten", { x: 0.6, y: 5.65, w: 8.35, h: 0.3, fontFace: FONT_HEAD, fontSize: 13, bold: true, color: TEXT, isTextBox: true, margin: 0 });
  bulletBox(s, [
    [{ text: "Subdiagnóstico en zonas rurales  ·  " }, { text: "TB resistente a fármacos (MDR-TB)  ·  " }, { text: "Abandono del tratamiento supervisado" }],
  ], { x: 0.6, y: 5.95, w: 8.35, h: 0.5, fontSize: 12, spaceAfter: 0, bullet: false });
}

// Slide 6 — Caso 2: Sarampión
{
  const s = contentSlide({ kicker: "Caso de estudio 2", title: "Sarampión — Cuando un Logro No Es Permanente", accent: OMS_ALERT, n: 6, footText: "OMS en Bolivia" });

  nativeTable(s, 0.6, 1.6, 6.3,
    ["Año", "Hito"],
    [
      ["2000", "Último caso endémico (Amarete, La Paz)"],
      ["2012", "Bolivia certificada libre de sarampión"],
      ["2023", "Recertificación de todos los departamentos"],
      ["Jun. 2025", "Emergencia Sanitaria Nacional por nuevo brote"],
    ],
    { headerColor: OMS_ALERT, colW: [1.3, 5.0] }
  );

  s.addText("La causa raíz", { x: 0.6, y: 4.0, w: 6.3, h: 0.3, fontFace: FONT_HEAD, fontSize: 13, bold: true, color: TEXT, isTextBox: true, margin: 0 });
  nativeTable(s, 0.6, 4.32, 6.3,
    ["Indicador 2023", "Cifra", "Meta"],
    [
      ["1ª dosis SRP (<1 año)", "68%", "95%"],
      ["Esquema completo", "< 50%", "95%"],
    ],
    { headerColor: OMS_PRIMARY, colW: [3.3, 1.5, 1.5] }
  );

  imageCover(s, path.join(IMG_OMS, "OMS_S6_caso-sarampion_vacuna-mmr.jpg"), 7.25, 1.6, 2.4, 3.2);
  s.addText("Vacuna MMR/SRP", { x: 7.25, y: 4.85, w: 2.4, h: 0.3, fontFace: FONT_BODY, fontSize: 9, italic: true, color: MUTED, isTextBox: true, margin: 0 });

  s.addShape("rect", { x: 9.95, y: 1.6, w: 2.78, h: 3.15, fill: { color: "EAF2F8" }, line: { type: "none" } });
  s.addText([
    { text: "Contraste — Poliomielitis\n", options: { bold: true, color: OMS_PRIMARY, breakLine: true, fontSize: 13 } },
    { text: "Región libre de polio desde 1994. Sin casos desde 1991 (último: Perú). Más de 30 años de éxito ininterrumpido.", options: { fontSize: 11.5, color: TEXT } },
  ], { x: 10.15, y: 1.75, w: 2.4, h: 2.9, isTextBox: true, margin: 0, align: "left", valign: "top" });

  s.addText([
    { text: "La lección:  ", options: { bold: true, color: OMS_ALERT } },
    { text: "un logro sanitario no es un punto de llegada. La cobertura cayó silenciosamente años antes del brote.", options: { color: TEXT } },
  ], { x: 0.6, y: 5.7, w: 12.13, h: 0.6, fontFace: FONT_BODY, fontSize: 12.5, isTextBox: true, margin: 0, align: "left", valign: "top" });
}

// Slide 7 — Conclusión OMS
{
  const s = titleSlide({
    eyebrow: "Conclusión — OMS",
    title: "Un Trabajo Nunca Terminado",
    subtitle: null,
    footerText: null,
    bgColor: OMS_DARK,
    logoPath: null, logoW: 0, logoH: 0,
  });
  s.addText([
    { text: "En salud pública, no hay logros permanentes,\n", options: { fontSize: 22, italic: true, color: WHITE, breakLine: true, align: "center" } },
    { text: "solo logros sostenidos.", options: { fontSize: 22, italic: true, bold: true, color: "9FD3F0", align: "center" } },
  ], { x: 1.3, y: 2.6, w: PW - 2.6, h: 1.3, isTextBox: true, margin: 0, align: "center", valign: "top" });

  statCallout(s, 2.0, 4.3, 4.0, "3.3x", "incidencia de TB vs. promedio regional", "9FD3F0");
  statCallout(s, 7.3, 4.3, 4.0, "68% → 95%", "brecha de cobertura SRP frente a la meta", "9FD3F0");

  s.addText("La tuberculosis nunca llegó a controlarse del todo; el sarampión sí se controló, y aun así volvió.", {
    x: 1.3, y: 6.0, w: PW - 2.6, h: 0.6, fontFace: FONT_BODY, fontSize: 13, italic: true, color: "E8DFD3",
    align: "center", isTextBox: true, margin: 0,
  });
}

// ======================================================================
// DECK — UNESCO (slides 8-14)
// ======================================================================

// Slide 8 — Portada UNESCO
titleSlide({
  eyebrow: "Organismos Internacionales en Bolivia",
  title: "UNESCO",
  subtitle: "Protegiendo la Cultura y Educación en Bolivia",
  footerText: "[Nombre Presentador 2]  ·  [Institución]  ·  2026",
  bgColor: UN_DARK,
  logoPath: path.join(IMG_UN, "UNESCO_S1_portada_logo.png"),
  logoW: 3.0, logoH: 3.0 * (410/1591),
});

// Slide 9 — ¿Qué es UNESCO?
{
  const s = contentSlide({ kicker: "Organismo especializado de la ONU", title: "¿Qué es UNESCO?", accent: UN_PRIMARY, n: 9, footText: "UNESCO en Bolivia" });
  bulletBox(s, [
    [{ text: "Fundada en " }, { text: "1945", bold: true }, { text: ", después de la Segunda Guerra Mundial" }],
    [{ text: "Organismo especializado de las Naciones Unidas" }],
    [{ text: "Sede en " }, { text: "París, Francia", bold: true }],
    [{ text: "195 países miembros (incluyendo Bolivia)" }],
  ], { x: 0.6, y: 1.65, w: 6.6, h: 2.1, fontSize: 15, spaceAfter: 14 });

  s.addShape("rect", { x: 0.6, y: 3.85, w: 6.6, h: 1.55, fill: { color: WHITE }, line: { color: LINEC, width: 1 } });
  s.addText([
    { text: '"Puesto que las guerras nacen en la mente de los\nhombres, es en la mente de los hombres donde\ndeben erigirse los baluartes de la paz"', options: { italic: true, fontSize: 13, color: TEXT, breakLine: true } },
    { text: "— Lema de UNESCO", options: { fontSize: 11, color: MUTED } },
  ], { x: 0.85, y: 3.98, w: 6.1, h: 1.3, isTextBox: true, margin: 0, align: "left", valign: "top" });

  s.addText([
    { text: "¿Sabían que…?  ", options: { bold: true, color: UN_PRIMARY } },
    { text: "Bolivia tiene 7 sitios en la Lista de Patrimonio Mundial de UNESCO.", options: { color: TEXT } },
  ], { x: 0.6, y: 5.6, w: 6.6, h: 0.8, fontFace: FONT_BODY, fontSize: 13, isTextBox: true, margin: 0, align: "left", valign: "top" });

  s.addImage({ path: path.join(IMG_UN, "UNESCO_S2_que-es-unesco_logo.png"), x: 8.1, y: 2.6, w: 4.6, h: 4.6 * (410/1591) });

  s.addText([
    { text: "Su instrumento característico: ", options: { bold: true, color: UN_PRIMARY, fontSize: 11.5 } },
    { text: "convenciones internacionales, como la de 1972 sobre Patrimonio Mundial, ratificada por Bolivia.", options: { color: TEXT, fontSize: 11.5 } },
  ], { x: 8.1, y: 3.85, w: 4.6, h: 0.55, isTextBox: true, margin: 0, align: "left", valign: "top" });

  imageCover(s, path.join(IMG_UN, "UNESCO_EXTRA_sede-paris.jpg"), 8.6, 4.55, 3.0, 1.99);
  s.addText("Sede de UNESCO, París", { x: 8.6, y: 6.57, w: 3.0, h: 0.22, fontFace: FONT_BODY, fontSize: 9, italic: true, color: MUTED, align: "center", isTextBox: true, margin: 0 });
}

// Slide 10 — ¿Qué hace UNESCO?
{
  const s = contentSlide({ kicker: "Cuatro pilares", title: "Funciones Principales de UNESCO", accent: UN_PRIMARY, n: 10, footText: "UNESCO en Bolivia" });
  const items = [
    ["Educación de Calidad", "Acceso equitativo para todos, con énfasis en niñas y minorías"],
    ["Patrimonio Cultural", "Protege sitios arqueológicos y preserva tradiciones vivas"],
    ["Libertad de Expresión", "Defiende la libertad de prensa y el acceso a información"],
    ["Ciencia y Tecnología", "Promueve investigación e innovación para el desarrollo"],
  ];
  let y = 1.75;
  items.forEach(([t, d], i) => {
    numberedCircleRow(s, 0.7, y, 7.3, i + 1, UN_PRIMARY, t, d);
    y += 1.15;
  });

  s.addImage({ path: path.join(IMG_UN, "UNESCO_S3_que-hace-unesco_emblema-patrimonio-mundial.png"), x: 9.15, y: 2.0, w: 3.3, h: 3.3 });
  s.addText("Oficina de Programas UNESCO en La Paz coordina educación, patrimonio y comunicación. UNESCO desde la gestión pública: el reconocimiento internacional no genera presupuesto por sí solo — la conservación depende de la administración pública nacional.", {
    x: 8.6, y: 5.55, w: 4.3, h: 1.45, fontFace: FONT_BODY, fontSize: 10.5, italic: true, color: MUTED,
    align: "center", isTextBox: true, margin: 0, valign: "top",
  });
}

// Slide 11 — UNESCO en Bolivia
{
  const s = contentSlide({ kicker: "Reconocimientos oficiales", title: "UNESCO en Bolivia", accent: UN_PRIMARY, n: 11, footText: "UNESCO en Bolivia" });

  nativeTable(s, 0.6, 1.6, 7.3,
    ["Sitio (Patrimonio Mundial)", "Año"],
    [
      ["Ciudad de Potosí", "1987"],
      ["Misiones Jesuíticas de Chiquitos", "1990"],
      ["Sucre (centro histórico)", "1991"],
      ["Fuerte de Samaipata", "1998"],
      ["Tiwanaku", "2000"],
      ["P.N. Noel Kempff Mercado", "2000"],
      ["Qhapaq Ñan (transnacional)", "2014"],
    ],
    { headerColor: UN_PRIMARY, colW: [5.8, 1.5] }
  );
  s.addText([
    { text: "+ 1 Patrimonio Cultural Inmaterial (lista aparte):  ", options: { bold: true, color: UN_SECOND } },
    { text: "Carnaval de Oruro (2001)", options: { color: TEXT } },
  ], { x: 0.6, y: 5.55, w: 7.3, h: 0.4, fontFace: FONT_BODY, fontSize: 12.5, isTextBox: true, margin: 0 });

  s.addImage({ path: path.join(IMG_UN, "UNESCO_S4_unesco-en-bolivia_mapa-departamentos.png"), x: 8.4, y: 1.7, w: 4.3, h: 4.3 * (339/300) < 4.9 ? 4.3 * (339/300) : 4.85 });
  s.addText("Programas activos: educación para el desarrollo sostenible, alfabetización rural, formación docente, preservación de lenguas indígenas", {
    x: 8.2, y: 6.35, w: 4.6, h: 0.75, fontFace: FONT_BODY, fontSize: 10.5, italic: true, color: MUTED,
    align: "left", isTextBox: true, margin: 0,
  });
}

// Slide 12 — Tiwanaku
{
  const s = contentSlide({ kicker: "Caso de estudio 1", title: "Tiwanaku: Civilización Ancestral", accent: UN_PRIMARY, n: 12, footText: "UNESCO en Bolivia" });

  imageCover(s, path.join(IMG_UN, "UNESCO_S5a_tiwanaku_puerta-del-sol.jpg"), 8.85, 1.55, 3.88, 2.45);
  imageCover(s, path.join(IMG_UN, "UNESCO_S5b_tiwanaku_templo-kalasasaya.jpg"), 8.85, 4.12, 3.88, 2.45);
  s.addText("Puerta del Sol", { x: 8.85, y: 4.0, w: 3.88, h: 0.25, fontFace: FONT_BODY, fontSize: 9, italic: true, color: MUTED, isTextBox: true, margin: 0 });
  s.addText("Templo de Kalasasaya", { x: 8.85, y: 6.6, w: 3.88, h: 0.25, fontFace: FONT_BODY, fontSize: 9, italic: true, color: MUTED, isTextBox: true, margin: 0 });

  bulletBox(s, [
    [{ text: "Sitio arqueológico a 20 km de La Paz (71.5 hectáreas), Provincia de Ingavi" }],
    [{ text: "Apogeo del imperio entre los años 500 y 900 d.C." }],
    [{ text: "Influencia extendida por los Andes del sur (hoy Perú, Chile, Argentina)" }],
  ], { x: 0.6, y: 1.65, w: 7.9, h: 1.6, fontSize: 13.5, spaceAfter: 10 });

  s.addText("Reconocimiento UNESCO (2000) — Ficha oficial 567", { x: 0.6, y: 3.35, w: 7.9, h: 0.3, fontFace: FONT_HEAD, fontSize: 13, bold: true, color: UN_PRIMARY, isTextBox: true, margin: 0 });
  bulletBox(s, [
    [{ text: "Criterio iii: ", bold: true }, { text: "testimonio excepcional del poder del imperio Tiwanaku" }],
    [{ text: "Criterio iv: ", bold: true }, { text: "arquitectura ceremonial y pública excepcional de los Andes" }],
  ], { x: 0.6, y: 3.7, w: 7.9, h: 1.1, fontSize: 12.5, spaceAfter: 8 });

  s.addShape("rect", { x: 0.6, y: 4.95, w: 7.9, h: 1.75, fill: { color: "FBF3E7" }, line: { type: "none" } });
  s.addText([
    { text: "Conservación e impacto\n", options: { bold: true, color: UN_PRIMARY, breakLine: true, fontSize: 13 } },
    { text: "Restauración de estructuras dañadas por sismos y sistemas de drenaje contra erosión, en trabajo conjunto con el Ministerio de Culturas de Bolivia. ~200,000–250,000 visitantes anuales; símbolo de orgullo para comunidades aymara.", options: { fontSize: 12, color: TEXT } },
  ], { x: 0.85, y: 5.08, w: 7.4, h: 1.55, isTextBox: true, margin: 0, align: "left", valign: "top" });
}

// Slide 13 — Carnaval de Oruro
{
  const s = contentSlide({ kicker: "Caso de estudio 2 — Patrimonio Inmaterial", title: "Carnaval de Oruro", accent: UN_ACCENT, n: 13, footText: "UNESCO en Bolivia" });

  imageCover(s, path.join(IMG_UN, "UNESCO_S6_carnaval-oruro_diablada.jpg"), 8.55, 1.55, 4.18, 5.1);
  s.addText("Danzarines de la Diablada", { x: 8.55, y: 6.68, w: 4.18, h: 0.25, fontFace: FONT_BODY, fontSize: 9, italic: true, color: MUTED, isTextBox: true, margin: 0 });

  bulletBox(s, [
    [{ text: "Celebración religiosa y folclórica, febrero/marzo, en Oruro" }],
    [{ text: "Miles de danzarines y músicos, procesión de 2 días" }],
  ], { x: 0.6, y: 1.65, w: 7.6, h: 0.95, fontSize: 13, spaceAfter: 8 });

  s.addText("Danzas principales", { x: 0.6, y: 2.65, w: 7.6, h: 0.3, fontFace: FONT_HEAD, fontSize: 13, bold: true, color: UN_ACCENT, isTextBox: true, margin: 0 });
  bulletBox(s, [
    [{ text: "Diablada: ", bold: true }, { text: "batalla entre el bien y el mal" }],
    [{ text: "Morenada: ", bold: true }, { text: "representa la esclavitud africana" }],
    [{ text: "Tinku: ", bold: true }, { text: "confrontación ritual indígena" }],
    [{ text: "Andanza: ", bold: true }, { text: "danza de celebración" }],
  ], { x: 0.6, y: 2.98, w: 7.6, h: 1.7, fontSize: 12.5, spaceAfter: 7 });

  s.addShape("rect", { x: 0.6, y: 4.85, w: 7.6, h: 1.0, fill: { color: "EAE6F0" }, line: { type: "none" } });
  s.addText([
    { text: "Reconocimiento UNESCO (2001): ", options: { bold: true, color: UN_ACCENT } },
    { text: "Patrimonio Inmaterial de la Humanidad — uno de los primeros reconocidos en esta categoría.", options: { color: TEXT } },
  ], { x: 0.85, y: 4.97, w: 7.1, h: 0.8, fontFace: FONT_BODY, fontSize: 12, isTextBox: true, margin: 0, align: "left", valign: "top" });

  bulletBox(s, [
    [{ text: "Desafíos: presión del turismo, menor interés juvenil, costo alto de participación, modernización vs. tradición" }],
  ], { x: 0.6, y: 6.0, w: 7.6, h: 0.7, fontSize: 11.5, spaceAfter: 0, bullet: false });
}

// Slide 14 — Conclusión UNESCO
{
  const s = titleSlide({
    eyebrow: "Conclusión — UNESCO",
    title: "Cultura y Educación",
    subtitle: null,
    footerText: null,
    bgColor: UN_DARK,
    logoPath: null, logoW: 0, logoH: 0,
  });
  s.addImage({ path: path.join(IMG_UN, "UNESCO_S7_conclusion_templo-kalasasaya.jpg"), x: 0, y: 0, w: PW, h: PH, sizing: { type: "cover", w: PW, h: PH }, transparency: 55 });
  s.addShape("rect", { x: 0, y: 0, w: PW, h: PH, fill: { color: UN_DARK, transparency: 35 }, line: { type: "none" } });

  s.addText("La cultura es un derecho humano", {
    x: 1.3, y: 2.2, w: PW - 2.6, h: 0.8, fontFace: FONT_HEAD, fontSize: 30, bold: true, color: WHITE,
    align: "center", isTextBox: true, margin: 0,
  });
  s.addText("La OMS cuida nuestra salud física. UNESCO cuida nuestra salud cultural.\nAmbas son necesarias para que Bolivia prospere.", {
    x: 1.6, y: 3.15, w: PW - 3.2, h: 1.0, fontFace: FONT_BODY, fontSize: 16, italic: true, color: "F0E6D8",
    align: "center", isTextBox: true, margin: 0,
  });

  statCallout(s, 2.0, 4.6, 4.0, "7 + 1", "sitios Patrimonio Mundial + Inmaterial", "F0C48A");
  statCallout(s, 7.3, 4.6, 4.0, "500+ años", "de historia, de Tiwanaku al Carnaval", "F0C48A");

  s.addText("Gracias.  Tanto la OMS como UNESCO trabajan por un Bolivia más desarrollado, más saludable y con mayor orgullo en su cultura.", {
    x: 1.3, y: 6.4, w: PW - 2.6, h: 0.6, fontFace: FONT_BODY, fontSize: 12, color: "E8DFD3",
    align: "center", isTextBox: true, margin: 0,
  });
}

pres.writeFile({ fileName: "/home/user/01/entregables/Presentacion_OMS_UNESCO_Bolivia.pptx" }).then(() => {
  console.log("OK: pptx written");
});
