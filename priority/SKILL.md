---
name: priority
description: Karchi's inbox on asus, which only Hermes reads. Use when a turn leaves Karchi a step or a decision, when a step this thread wrote there is done, and whenever he says inbox, zapíš si, zapíš do inboxu, nápad, úloha, hotové or done about an inbox item.
---

# Inbox

Karchi keeps one inbox for everything he wants to do: `~/inbox/inbox.md` on asus. One line per
item, `- [ ] YYYY-MM-DD · what · why or by when`, under `## P1 teraz` (important and urgent: a
deadline, blocks something, people or money waiting), `## P2 ďalej` (important, no deadline),
`## P3 niekedy` (ideas) and `## Hotové` (done, `- [x]`).

**Only Hermes reads it** (Hermes Agent on asus, Weft room „Hermes“, `~/.hermes/SOUL.md`; Karchi,
2026-11-07). It keeps the inbox current and builds his day plan from it. Every other chat writes to it
and never reads it: no inbox in the session context, no priority check against the task he gave
you, no „V inboxe čaká“. When he asks you what is in the inbox („ukáž inbox“, „čo čaká“), show it
only because he asked in this thread, and mention that Hermes keeps it.

## Writing to it

- „zapíš do inboxu“, „zapíš si“, or an idea or task he does not want now: append one line with
  today's date under P1, P2 or P3 (P1 only with a deadline or a real blocker; when unsure, P2).
  Confirm in one line with the priority you chose.
- Your reply leaves Karchi a step (a „tvoj krok“, a decision, a login, a test only he can do), or you
  stop unfinished and only he can restart the work: one line for this thread, `- [ ] <date> · <his
  step> · <machine> vlákno „<thread title>“ #<id>`, at most 300 characters. `<id>` is the last 8
  characters of `$T3CODE_THREAD_ID` (the same as the end of a T3 scratch folder's name).
- Never a line for what is not his to do: your own work still running or scheduled, what you did,
  what cannot be done, a mistake you made, a setting he may change if he likes. Say it in the reply.
- One thread, one line. Find it by `#<id>` (by the title only in old lines without an id) and
  replace that one line; never write the same text over every match and never add a second line. If
  this thread has several, merge them into one.
- When the step is done (he says „done“, „hotové“ or „spravil som“ in this thread, or his answer shows
  he did it) or it no longer applies, mark this thread's line done (next point) in the
  same turn. A new step replaces the line only when it is his again under the rules above.
- „hotové“ or „done“ about an item: change that line's `[ ]` to `[x]`, move it to Hotové, append
  ` · hotové <date>: <where>`. Delete a line only when he says „vyhoď“, „daj preč“,
  „nepotrebujem“, „netreba“ or „nerieš“ about it (Karchi, 2026-11-19: „nerieš“ means drop the line, not
  keep it and leave it alone).
- Before you call an item done or stale, check its real state (PR, file, service, thread), not just
  its text.
- Change only the lines concerned, keep the format, put nothing else into `~/inbox`. From another
  machine: `ssh asus 'python3 - <<"PY" ... PY'` on the file. If asus does not answer, say
  „inbox na asuse nedostupný“ once and go on.
