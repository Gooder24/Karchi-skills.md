---
name: taste
description: Karchi's personal taste (Karchiho vkus) in visual design, UI behaviour, tool choice, performance and how he likes to work with Claude. Use before designing or changing any UI, widget, app, theme or desktop setting for him, before choosing or recommending a tool, before writing a report or summary for him, before looking for, copying or moving his files or data on any of his machines, and whenever a decision depends on what he would like.
---

Read `taste.md` in this folder before deciding anything, and apply it to the task.

For any UI he will see: design with `frontend-design` first (direction, type and colour before code), and
before showing the result run the `avoid-ai-design` detector over the files and fix every P0 and P1
(`node ~/.work/karchi-skills/avoid-ai-design/scripts/detect.mjs <files>`; a deliberate choice is kept
with `avoid-ai-design-ignore: <ID>`). Both skills are in this repo.

It holds his preferences with his own words as evidence. Treat it as a default, not a rule:
what he says in the current conversation wins. When he expresses a new lasting preference or
corrects one written there, offer to update `taste.md`.
