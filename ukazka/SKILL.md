---
name: ukazka
description: How to make a demo (ukážka) of a feature or UI for Karchi - one self-contained clickable HTML page in the product's real look with made-up data, shown inline in the thread with html_render, which later becomes the spec and the starting code for production. Use whenever he asks for an ukážka, demo, mockup, prototype, náhľad or "ako by to vyzeralo", and before building a new UI feature he has not seen yet. Not for presentations (skill prezentacie) or charts of real data (skill dataviz).
---

# Ukážka: a clickable page, not a picture

Karchi on 2026-11-25 about the Weft „Rozoslať“ demo (`priklad-rozoslat.html` here): „EPICKÁ UKÁŽKA … ak má byť
niečo ukážka tak toto“. Every demo is made this way, and the same page later serves production.

## What it is

- **One HTML file**, `<style>` and `<script>` inline, no build, no server, no network request.
- **The product's real look, copied, not imitated:** its CSS tokens (`:root` variables), its font, its icons
  (for Weft `app/icons.js`, pixelarticons), its component class names (Weft: `.cmd`, `.res`, `.chip`, `.rsec`),
  its rounding, its texts in Slovak as the app writes them. Read `taste` and the product's design rules first.
- **The whole flow, every step reachable:** tabs or steps he can click, the keyboard working as in the app
  (Space, Enter, Ctrl+Enter, Esc, arrows, letters), the main action focused. Show the hard cases too: an item that
  is left out and why, a guess he should check, a failure, a stop half-way.
- **Made-up data only** (names, numbers, chats), and one visible line: „ukážka · nič sa neposiela · mená sú
  vymyslené“. Actions are simulated: a timer that advances the state a few times and then stops (no running
  animation), never a real send, request or write.
- `index.html#3` opens step 3 directly, so each step can be screenshotted.

## Steps

1. Copy the product's tokens, font file and the icons you need next to the file in the scratchpad.
2. Write `index.html`: the app dimmed behind, the demo as the app's own overlay or pane, full window.
3. Screenshot every step and look at each one before he does:
   `chromium --headless=new --no-sandbox --hide-scrollbars --window-size=1366,768 --virtual-time-budget=9000 --screenshot=$PWD/shotN.png "file://$PWD/index.html#N"`.
   Fix overlaps, misaligned columns and wrong Slovak (cases, plurals) before showing it.
4. Run `node ~/.work/karchi-skills/avoid-ai-design/scripts/detect.mjs index.html` and fix every P0 and P1
   (a deliberate choice gets `avoid-ai-design-ignore: <ID>` with the reason).
5. Make the inline copy for the thread (`render.html`): no page background, no `vh` or `height: 100%` on
   html/body (give the box a fixed height in px), the font as a `data:font/woff2;base64,…` URL, local images as
   absolute paths, the app behind removed, ✕ starting the demo over. Check it with `html_preview`, then show it
   with `html_render` (height = `contentHeight`). Also give him the full-window `index.html` path.
6. When he approves the feature, the demo moves into the product repo next to its design note (Weft:
   `docs/navrhy/<yyyy-mm>-<name>/ukazka.html`; in a public repo nothing personal) and the thread that builds it
   gets it in its brief: copy its CSS, classes, texts and key map into the code instead of redesigning, and the
   verifier compares the real screens with the demo's screenshots.

## Why not a picture, a GIF or a video

Prices for Claude Opus 5.5 ($4 per million input tokens, $20 per million output tokens). An image costs about
width × height / 750 input tokens each time a model reads it (1366 × 768 ≈ 1 400, 1920 × 1080 ≈ 2 800, up to
about 4 800 at full resolution). Claude cannot draw pixels: every picture of a UI is a screenshot of HTML that
had to be written first anyway.

| | Cost to make | Cost to look at it | What Karchi gets | Reused in production |
|---|---|---|---|---|
| This page (Rozoslať: 28 KB, about 8 000 output tokens, estimated from its size) | about $0.16 once | inline in the thread: nothing; each check screenshot ≈ 600–1 400 input tokens | every step, clickable and with keys, hard cases included | CSS, classes, texts, key map, flow; the verifier's reference |
| One screenshot | the same HTML first, plus ≈ 1 400 tokens per look | ≈ 1 400 input tokens every time it is read | one still state | no |
| A GIF of the flow | the same HTML, a recorder and ffmpeg | the API takes a GIF as an image; to check the motion the model needs it split into frames, ≈ 1 400 tokens each | one fixed path, no keys, nothing to try | no |
| A video (30 s) | the same HTML and a recorder | the Messages API takes no video: 30 s at 2 frames a second = 60 frames ≈ 84 000 input tokens (≈ $0.34) per review | one fixed path | no |

So the page is the cheapest form, it is the only one he can try himself, and it is the only one that is not
thrown away.
