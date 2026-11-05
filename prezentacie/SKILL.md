---
name: prezentacie
description: Create or revise Karchi's school presentations in editable PowerPoint with real images and a reusable, simple Primer-based style. Use whenever he asks for a presentation, slides, or presentation materials; preserve an explicitly requested different theme.
---

# Karchi's presentations

On 2026-11-05 Karchi asked for pictures and a simple but comprehensive design language from GitHub,
remembered for future presentations. The working default is **GitHub Primer adapted for PowerPoint**,
not a claim that his older decks used Primer. Older files have several styles; the shared anchors are
plain readable type, short text, real pictures and the school identity. A new reference from him wins.

## Style

Use the reusable [primer.js](primer.js) rather than inventing new colours and components for each deck.
Its colours follow [primer/primitives](https://github.com/primer/primitives); the PowerPoint layout and
components are our adaptation, not an official GitHub presentation template.

- 16:9, 10 × 5.625 inches, 0.5-inch outside margins; align titles and body content left.
- White content slides (`FFFFFF`), dark text (`1F2328`), secondary text (`59636E`), subtle panels
  (`F6F8FA`), borders (`D1D9E0`), blue accent (`0969DA`). Green is a semantic success/status colour.
- Dark title and closing slide (`0D1117`, text `F0F6FC`). No gradients, decorative grids or shadows.
- Arial for title and body, Courier New only for identifiers such as patent numbers. Scale in points:
  display 48, title 26, subtitle 18, lead 14, body 12, small 11, label 10, footer 9. These are for the
  10-inch canvas; scale with slide size. Prefer larger body text when there is room. Shorten content
  instead of shrinking it to fit, especially when it will be projected in class.
- Thin borders, mildly rounded panels, consistent spacing. The theme supports labels, state badges,
  lists, facts and a timeline; use only the components that serve this presentation. A patent panel
  belongs to Inventors, not to every future topic. Do not turn every slide into the same three cards.
- Use genuine topic images with preserved proportions. A portrait can sit beside a short text block;
  use a drawing or photograph of the object when no reliable portrait exists. Do not fabricate a
  historical portrait. Give a caption and an original source link; check the licence.
- Use OATA's logo for school work only when it is present in his supplied material. Read current
  name/class from that material; do not hard-code III.A into future years.
- Normal structure: title, contents if useful, topic slides, conclusion, thanks, public bibliography.
  The topic decides the number of slides, not this example's 15.

## His files and school constraint

Read `~/school/CLAUDE.md` on x270 before preparing a school submission. The rule known on 2026-11-05:
no private presenter script, timings, internal suggestions, TODOs, comments or speaker notes in the
submitted file. Those belong in chat. A public bibliography/image attribution is audience content,
not private research notes. Source-by-source fact checking stays outside the submission.

His school files are on x270 under `~/school/`; OKA's reference was
`OKA/13 SCIENCE AND TECHNOLOGY.pptx` (English). This does not make every future deck English: inspect
the actual assignment. Earlier examples included Teplička nad Váhom, Hypertext, Schoolinfo and Riskuj.
Build work can run on asus; `~/work/inventors/` contains the first deck using this style, its photos
and rendered PDF. Do not depend on its node_modules symlink for a new project.

## Build and delivery

Copy `primer.js`, [scripts/apply_theme.js](scripts/apply_theme.js), and
[assets/starter.js](assets/starter.js) into the new build directory. Install `pptxgenjs@4.0.1` there
if no suitable project dependency exists. The starter shows the actual API:

```sh
node starter.js Example.pptx
```

`P.setup()` adds LIGHT/DARK masters, footer and slide numbering. `P.photo()` contains an image in its
box without stretching; pass `{url: originalSource}` for attribution. After `writeFile`, call
`applyTheme(output, P.THEME)` so the editable PowerPoint palette also says Primer.

Render through LibreOffice to PDF, then inspect every slide image. Check wrapping, captions, photo
proportions and alignment; a PPTX XML validator alone cannot prove the layout. Inspect the actual
final exported file, not a previous build. Preserve editable text; don't flatten slides into pictures.

Deliver linked PPTX and PDF in the working thread. If the current request includes x270 delivery,
copy to its `~/Downloads` (keep an existing differing version as a backup) and compare checksums.
Do not claim that a file reached x270 if it is offline. Do not embed private verification notes in the
presentation. Avoid making the user run a build or copy command you can run yourself.
