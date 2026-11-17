---
name: prezentacie
description: The entry point for EVERY presentation Karchi asks for, in any form (prezentácia, slajdy, deck, slides, Claude Slides artifact, PowerPoint, HTML, PDF), for school, SOČ, eSYST or himself, new or revised. Read it before any other slide skill or artifact type, and before writing the first slide. It says which GitHub skills design and structure the deck and how he chooses the look.
---

# Karchi's presentations

Karchi asked several times for presentation skills from GitHub that are used for every deck. On
2026-11-05 an agent misread "cez github" as GitHub's Primer design system and built a Primer theme; on
2026-11-17 he rejected the eSYST workflow deck made with it as "extrémne AI, nezaujímavý a strašne
stručný" and repeated the request. The answer is the two third-party skills below, vendored in this
repo. Use them for every presentation, whatever the output format, also when an artifact type
(Claude Slides) or another skill (`pptx`, `soc`) builds the file.

| Half | Skill | What it decides |
| --- | --- | --- |
| Look | [`frontend-slides`](../frontend-slides/SKILL.md) (zarazhangrui, MIT) | Style, type, colour, layout system, motion; three previews he chooses from |
| Content | [`academic-pptx`](../academic-pptx/SKILL.md) (Gabberflast, MIT) | The argument: narrative spine, action titles, one job per slide, sources |

## Order of work

1. **Read both skills** (their `SKILL.md`; from `academic-pptx` also `content_guidelines.md`).
2. **Outline first.** One line per slide: an action title (a full sentence with the takeaway) and what
   the slide shows. The titles read in order must tell the whole argument (ghost deck test). Put the
   outline in the thread with the previews; do not ask about it separately.
3. **Three style previews**, as `frontend-slides` Phase 2 says: one safe preset, one bold template, one
   wildcard. Each preview is the real title slide plus one real content slide of this deck, so he sees
   the density too. Render them to PNG and show them in the thread. Skip the previews only when he
   named the style, or when the deck continues one whose style he already picked (list below).
4. **He picks, then build the whole deck** in that style: read that template's `design.md`, follow
   `frontend-slides` Phase 3.
5. **Check before showing** (below), then deliver.

Do not ask the Phase 1 questions of `frontend-slides`; take purpose, length and content from the
thread. Density: a deck he or someone else reads alone is reading-first (high density); a deck he
presents out loud is speaker-led.

## What his feedback rules out

- **Thin slides.** A title over three small cards with one line each, on a slide that is half empty.
  The content of a slide fills at least about 70 % of the area under the title. A reading deck carries
  the real substance: numbers, names of steps, the example, the reason, what happens when it fails.
- **The same layout again and again.** No more than two slides in a row with the same structure, and
  not every slide a row of cards.
- **Default looks**: a dark cover with white content slides and one blue accent, system fonts,
  everything in rounded grey panels. `frontend-slides` lists more under "DO NOT USE".
- **Topic-label titles** ("Náklady", "Riziká"). The title says what the slide shows.
- Where the two skills disagree, `frontend-slides` wins on the look and `academic-pptx` on the content:
  its Step 3 (white background, navy, Arial, no palette) and its limit of 40 words per slide apply only
  to a deck that is presented out loud to a committee, and even there the style is one he picked.

## Pictures and facts

Use genuine pictures of the subject (a photo, a screenshot of the real system, a real diagram of the
real thing) with preserved proportions, a caption and the original source link; check the licence. Do
not fabricate a historical portrait. A deck about software shows the software. Numbers and claims need
a source on the slide or in a closing sources slide; never invent one.

## Output format

- **HTML** (default for work and for sharing a link): the single file `frontend-slides` produces. Give
  him a link he can open: publish it as a private artifact, or the file path. Never deploy to Vercel or
  any other outside host (its `deploy.sh` is not vendored); PDF with `frontend-slides/scripts/export-pdf.sh`.
- **Claude Slides artifact**: the artifact type is only the container. The style and content still come
  from the two skills; all look lives in the deck's own CSS.
- **PowerPoint** (school asks for an editable `.pptx`; it must open in OnlyOffice on x270): build the
  chosen style with the `pptx` skill and pptxgenjs. [primer.js](primer.js),
  [scripts/apply_theme.js](scripts/apply_theme.js) and [assets/starter.js](assets/starter.js) remain as
  helpers for masters, footer, slide numbers, `P.photo()` (fits an image without stretching) and the
  editable theme palette; replace their Primer colours and Arial with the chosen style's. Render through
  LibreOffice to PDF and inspect every slide image; keep text editable.

## Check before showing

- Render every slide to PNG at 1920×1080 and look at each: no overflow, no overlap, no slide left half
  empty, text readable.
- Run `node ~/.work/karchi-skills/avoid-ai-design/scripts/detect.mjs <files>` and fix every P0 and P1; a
  deliberate part of the chosen template is kept with `avoid-ai-design-ignore: <ID>`.
- Ghost deck test on the final titles. Slovak text with full diacritics; check that the chosen fonts
  have ľ, š, č, ť, ž, ý, á, í, é, ú, ä, ô, ň, ď, ŕ, ĺ.
- Show him the rendered slides in the thread, not only a link.

## Styles he has picked

None yet. When he picks a style for a kind of deck (eSYST, school, SOČ), write it here with the date,
so the next deck of that kind starts in it without new previews.

## School

Read `~/school/CLAUDE.md` on x270 before preparing a school submission. The rule known on 2026-11-05:
no private presenter script, timings, internal suggestions, TODOs, comments or speaker notes in the
submitted file; those belong in chat. A public bibliography and image attribution is audience content.
Use OATA's logo only when it is in his supplied material; read the current name and class from that
material. His school files are on x270 under `~/school/`; inspect the actual assignment for language
and length. `~/work/inventors/` on asus holds the first deck made with the old Primer theme, its photos
and PDF.

Deliver linked files in the working thread. If the request includes x270 delivery, copy to its
`~/Downloads` (keep an existing differing version as a backup) and compare checksums; do not claim a
file reached x270 if it is offline. Do not make him run a build or copy command you can run yourself.
