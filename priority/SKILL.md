---
name: priority
description: Karchi's inbox on asus, which only Hermes reads. Use whenever he says inbox, zapíš si, zapíš do inboxu, nápad, úloha, hotové or done about an inbox item, when a Hermes job or a scheduled task without a thread leaves him a step, and before writing anything to the inbox from a T3 thread (steps of an unsettled thread stay in the thread).
---

# Inbox

Karchi keeps one inbox for everything he wants to do: `~/inbox/inbox.md` on asus. One line per
item, `- [ ] YYYY-MM-DD · what · why or by when`, under `## P1 teraz` (important and urgent: a
deadline, blocks something, people or money waiting), `## P2 ďalej` (important, no deadline),
`## P3 niekedy` (ideas) and `## Hotové` (done, `- [x]`).

**Only Hermes reads it** (Hermes Agent on asus, Weft room „Hermes“, `~/.hermes/SOUL.md`; Karchi,
2026-11-07). It keeps the inbox current and builds his day plan from it. Every other chat writes to it
only as „Writing to it“ below allows, and never reads it: no inbox in the session context, no priority check against the task he gave
you, no „V inboxe čaká“. When he asks you what is in the inbox („ukáž inbox“, „čo čaká“), show it
only because he asked in this thread, and mention that Hermes keeps it.

## Writing to it

Karchi's rule (2026-11-19): a T3 thread that is not settled is one he still means to finish, so its
steps and decisions stay in the thread and never go to the inbox. A thread he settled that left him a
step he did not do is a problem, and that step gets one inbox line. The Hermes job „Settled kroky“
(`settled-steps.py` here, every 30 min, all four machines) writes those lines after he settles a
thread, and removes a line when its thread is unsettled again. You do not.

- „zapíš do inboxu“, „zapíš si“, or an idea or task he does not want now: append one line with
  today's date under P1, P2 or P3 (P1 only with a deadline or a real blocker; when unsure, P2).
  Confirm in one line with the priority you chose.
- A step or decision of his from this thread (a choice, a login, a command, a test, a reply to
  someone): say it plainly at the end of the reply, one line per step, and leave it in the thread.
  No inbox line, also when it waits on a date or on someone else, and also in a `zadanie` or night run.
- Outside T3 (a Hermes job, a scheduled task without a thread) the run's step goes to the inbox: one
  line `- [ ] <date> · <his step> · Hermes úloha „<name>“`, at most 300 characters, found again by its
  job name and never written twice.
- Never a line for what is not his to do: your own work still running or scheduled, what you did,
  what cannot be done, a mistake you made, a setting he may change if he likes.
- A line with `#<id>` (the last 8 characters of `$T3CODE_THREAD_ID`) belongs to that thread. When he
  says in this thread that its step is done („done“, „hotové“, „spravil som“), or his answer shows he
  did it, mark that line done (next point) in the same turn. A line without an id is yours only when
  this thread's history shows you wrote it; if not, change none and say so in the reply.
- „hotové“ or „done“ about an item: change that line's `[ ]` to `[x]`, move it to Hotové, append
  ` · hotové <date>: <where>`. Delete a line only when he says „vyhoď“, „daj preč“,
  „nepotrebujem“, „netreba“ or „nerieš“ about it (Karchi, 2026-11-19: „nerieš“ means drop the line, not
  keep it and leave it alone).
- Before you call an item done or stale, check its real state (PR, file, service, thread), not just
  its text.
- Change only the lines concerned, keep the format, put nothing else into `~/inbox`. From another
  machine: `ssh asus 'python3 - <<"PY" ... PY'` on the file. If asus does not answer, say
  „inbox na asuse nedostupný“ once and go on.
