// Primer, GitHub's design system, for pptxgenjs decks: colour tokens, two slide masters and the
// handful of components a school deck needs. Colours are resolved from primer/primitives
// (src/tokens/functional/color + base/color, read 2026-11-05). Slide size is 10 x 5.625 in.
//
// Usage:
//   const P = require(process.env.HOME + "/.work/karchi-skills/prezentacie/primer.js");
//   const pres = new pptxgen(); P.setup(pres, { footer: "Inventors · Karol Ľupták" });
//   const slide = pres.addSlide({ masterName: "LIGHT" }); P.box(pres, slide, {...});

const LIGHT = {
  fg: "1F2328", fgMuted: "59636E", onEmphasis: "FFFFFF",
  bg: "FFFFFF", bgMuted: "F6F8FA", bgEmphasis: "25292E", neutralMuted: "EFF2F5",
  border: "D1D9E0", borderEmphasis: "818B98",
  accent: "0969DA", accentMuted: "DDF4FF",
  success: "1A7F37", successEmphasis: "1F883D", successMuted: "DAFBE1",
  attention: "9A6700", attentionMuted: "FFF8C5",
  danger: "D1242F", dangerEmphasis: "CF222E", dangerMuted: "FFEBE9",
  done: "8250DF", doneMuted: "FBEFFF",
  neutralEmphasis: "59636E",
};
const DARK = {
  fg: "F0F6FC", fgMuted: "9198A1", onEmphasis: "FFFFFF",
  bg: "0D1117", bgMuted: "151B23", bgEmphasis: "3D444D", neutralMuted: "212830",
  border: "3D444D", borderEmphasis: "656C76",
  accent: "4493F8", accentMuted: "111D2E",
  success: "3FB950", successEmphasis: "238636", successMuted: "12261E",
  attention: "D29922", attentionMuted: "272115",
  danger: "F85149", dangerEmphasis: "DA3633", dangerMuted: "2B1416",
  done: "AB7DF8", doneMuted: "221B36",
  neutralEmphasis: "656C76",
};
const FONT = "Arial";
const MONO = "Courier New";
const TYPE = { display: 48, title: 26, subtitle: 18, lead: 14, body: 12, small: 11, label: 10, footer: 9 };
const RADIUS = 0.08; // Primer's 6 px "medium" radius, scaled to the slide
const HAIR = 0.75;   // 1 px border
const W = 10, H = 5.625, M = 0.5; // slide size and margin, inches

// Theme colours for apply_theme.js, so PowerPoint's palette matches the deck.
const THEME = {
  name: "Primer",
  headFontFace: FONT,
  bodyFontFace: FONT,
  colors: {
    dk1: LIGHT.fg, lt1: LIGHT.bg, dk2: LIGHT.fgMuted, lt2: LIGHT.bgMuted,
    accent1: LIGHT.accent, accent2: LIGHT.successEmphasis, accent3: LIGHT.dangerEmphasis,
    accent4: LIGHT.attention, accent5: LIGHT.done, accent6: LIGHT.border,
    hlink: LIGHT.accent, folHlink: LIGHT.done,
  },
};

function tokens(mode) { return mode === "dark" ? DARK : LIGHT; }

// Two masters: DARK for the title and the end, LIGHT for everything between. The light master
// carries the title placeholder, the footer and the slide number.
function setup(pres, { footer = "", title = "", author = "" } = {}) {
  pres.layout = "LAYOUT_16x9";
  if (title) pres.title = title;
  if (author) pres.author = author;
  pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
  pres.defineSlideMaster({ title: "DARK", background: { color: DARK.bg }, objects: [] });
  pres.defineSlideMaster({
    title: "LIGHT",
    background: { color: LIGHT.bg },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: M, y: 0.38, w: 7.6, h: 0.5,
        fontSize: TYPE.title, bold: true, color: LIGHT.fg, margin: 0, valign: "top", align: "left" }, text: "" } },
      { text: { text: footer, options: { x: M, y: 5.2, w: 5, h: 0.25, fontSize: TYPE.footer, color: LIGHT.fgMuted, margin: 0 } } },
    ],
    slideNumber: { x: 8.5, y: 5.2, w: 1.0, h: 0.25, fontSize: TYPE.footer, color: LIGHT.fgMuted, align: "right", margin: 0 },
  });
}

// 1 px rule, like the border between two rows of a list.
function rule(pres, slide, x, y, w, { mode = "light", name = "rule" } = {}) {
  slide.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: tokens(mode).border, width: HAIR }, objectName: name });
}

// Breadcrumb header "Karol Ľupták / III.A / OATA" with the last crumb emphasised, a border under
// it and an optional logo at the right. Returns the y below the border.
function header(pres, slide, crumbs, { mode = "dark", logo = null, y = 0.45 } = {}) {
  const T = tokens(mode);
  const runs = [];
  crumbs.forEach((c, i) => {
    if (i) runs.push({ text: "  /  ", options: { color: T.fgMuted } });
    runs.push({ text: c, options: { color: i === crumbs.length - 1 ? T.fg : T.fgMuted, bold: i === crumbs.length - 1 } });
  });
  slide.addText(runs, { x: M, y, w: 7, h: 0.3, fontSize: TYPE.small, margin: 0, valign: "middle", isTextBox: true });
  if (logo) slide.addImage({ path: logo, x: W - M - 0.5, y: y - 0.1, w: 0.5, h: 0.5 });
  rule(pres, slide, M, y + 0.5, W - 2 * M, { mode, name: "header border" });
  return y + 0.5;
}

// Outlined pill, like a GitHub label. Width is given, the text is centred.
function label(pres, slide, text, x, y, w, { mode = "light", color = null, fill = null, h = 0.27, bold = true, name = "label" } = {}) {
  const T = tokens(mode);
  slide.addText(text, { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: h / 2, x, y, w, h, fontSize: TYPE.label, bold,
    color: color || T.fgMuted, fill: fill ? { color: fill } : { type: "none" },
    line: fill ? { type: "none" } : { color: color || T.borderEmphasis, width: HAIR },
    align: "center", valign: "middle", margin: 0, objectName: name });
}

// Filled pill with white text, like the state badge of an issue: kind success | neutral | accent | danger | done.
function badge(pres, slide, text, x, y, w, kind = "success", { mode = "light", h = 0.27, name = "badge" } = {}) {
  const T = tokens(mode);
  const fill = { success: T.successEmphasis, neutral: T.neutralEmphasis, accent: T.accent, danger: T.dangerEmphasis, done: T.done }[kind];
  slide.addText(text, { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: h / 2, x, y, w, h, fontSize: TYPE.label, bold: true,
    color: T.onEmphasis, fill: { color: fill }, line: { type: "none" }, align: "center", valign: "middle", margin: 0, objectName: name });
}

// Bordered box with an optional header strip (title left, a badge or label drawn by the caller
// at the right). Returns the content area inside the padding.
function box(pres, slide, { x, y, w, h, title = null, mode = "light", pad = 0.22, name = "box" }) {
  const T = tokens(mode);
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: RADIUS, fill: { color: T.bg },
    line: { color: T.border, width: HAIR }, objectName: name });
  let top = y;
  if (title !== null) {
    const hh = 0.46;
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.01, y: y + 0.01, w: w - 0.02, h: hh, rectRadius: RADIUS,
      fill: { color: T.bgMuted }, line: { type: "none" }, objectName: name + " header" });
    slide.addShape(pres.shapes.RECTANGLE, { x: x + 0.01, y: y + hh - 0.1, w: w - 0.02, h: 0.1, fill: { color: T.bgMuted },
      line: { type: "none" }, objectName: name + " header fill" });
    rule(pres, slide, x, y + hh, w, { mode, name: name + " header border" });
    slide.addText(title, { x: x + pad, y: y + 0.08, w: w - 2 * pad, h: 0.3, fontSize: TYPE.body, bold: true, color: T.fg,
      margin: 0, valign: "middle", isTextBox: true });
    top = y + hh;
  }
  return { x: x + pad, y: top + pad * 0.7, w: w - 2 * pad, bottom: y + h - pad, headerY: y + 0.1, headerRight: x + w - pad };
}

// Photo with a 1 px border and a muted caption under it.
function photo(pres, slide, path, x, y, w, h, caption = "", { mode = "light", name = "photo", url = null } = {}) {
  const T = tokens(mode);
  slide.addImage({ path, x, y, w, h, sizing: { type: "contain", w, h }, objectName: name, ...(url ? { hyperlink: { url } } : {}) });
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { type: "none" }, line: { color: T.border, width: HAIR }, objectName: name + " border" });
  if (caption) slide.addText(caption, { x, y: y + h + 0.04, w, h: 0.36, fontSize: TYPE.footer, color: T.fgMuted, margin: 0,
    valign: "top", isTextBox: true, ...(url ? { hyperlink: { url } } : {}) });
}

// Progress bar, like a milestone's: a track and the done part in green.
function progress(pres, slide, x, y, w, frac, { mode = "light", h = 0.07 } = {}) {
  const T = tokens(mode);
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: h / 2, fill: { color: T.neutralMuted }, line: { type: "none" }, objectName: "progress track" });
  if (frac > 0) slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: Math.max(h, w * frac), h, rectRadius: h / 2,
    fill: { color: T.successEmphasis }, line: { type: "none" }, objectName: "progress done" });
}

// Rows of "Lead  text" separated by 1 px rules, like a list in a box. pitch is the row height.
function rows(pres, slide, x, y, w, items, { mode = "light", pitch = 0.72, size = TYPE.body, lineBefore = true } = {}) {
  const T = tokens(mode);
  items.forEach(([lead, text], i) => {
    const ry = y + i * pitch;
    if (lineBefore || i) rule(pres, slide, x, ry, w, { mode, name: `row ${lead}` });
    slide.addText([
      { text: lead + "  ", options: { bold: true, color: T.fg } },
      { text, options: { color: T.fgMuted } },
    ], { x, y: ry + 0.07, w, h: pitch - 0.09, fontSize: size, margin: 0, valign: "top", isTextBox: true });
  });
  return y + items.length * pitch;
}

// "Label" in small muted type with the value under it, as on a details panel.
function field(pres, slide, x, y, w, name, value, { mode = "light", mono = false, h = 0.6 } = {}) {
  const T = tokens(mode);
  slide.addText(name, { x, y, w, h: 0.2, fontSize: TYPE.label, color: T.fgMuted, margin: 0, valign: "top", isTextBox: true });
  slide.addText(value, { x, y: y + 0.2, w, h: h - 0.2, fontSize: TYPE.body, color: T.fg, fontFace: mono ? MONO : FONT, margin: 0,
    valign: "top", isTextBox: true });
  return y + h;
}

module.exports = { LIGHT, DARK, FONT, MONO, TYPE, RADIUS, HAIR, W, H, M, THEME, tokens, setup, rule, header, label, badge, box, photo, progress, rows, field };
