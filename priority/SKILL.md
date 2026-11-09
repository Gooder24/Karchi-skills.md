---
name: priority
description: Karchi's inbox on asus, which only Hermes reads, and moving a thread to asus. Use before moving a thread to asus, when a turn leaves Karchi a step or a decision, and whenever he says inbox, zapíš si, zapíš do inboxu, nápad, úloha or hotové about an inbox item.
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
  stop with the work unfinished: append one line, `- [ ] <date> · <what is left> · <machine> vlákno
  „<thread title>“`, at most 300 characters. If this thread already has a line (grep for its title,
  nothing else), update that line in place instead.
- „hotové“ about an item: change that line's `[ ]` to `[x]`, move it to Hotové, append
  ` · hotové <date>: <where>`. Delete a line only when he says „vyhoď“.
- Change only the lines concerned, keep the format, put nothing else into `~/inbox`. From another
  machine: `ssh asus 'python3 - <<"PY" ... PY'` on the file. If asus does not answer, say
  „inbox na asuse nedostupný“ once and go on.

## Moving the thread to asus

AGENTS.md („Kde beží práca“) moves a thread that does not need its machine to asus. The moved
thread has to start working on its own; Karchi must never find it stopped.

1. A thread whose first message starts with „Presunuté z vlákna“ has been moved already: never move
   it again, do the task where you are (heavy parts through `ssh asus` when this is not asus).
2. Before `t3_thread_launch`, call `t3_environment_read` with asus's `environmentId`
   (`5182d572-beb3-4cf2-9f9e-d459777f2d15`). Move only when it answers with that id. On an error, or
   when it answers for this machine (an older T3 drops `environmentId` silently, which on 2026-10-29
   put a „moved“ thread on dell instead of asus), launch nothing: say „Presun na asus nejde (Linked
   environments vypnuté).“ first and do the task in this thread, heavy parts through `ssh asus`.
3. Launch with `environmentId`, `delegatedFrom` and the whole task and context in `message`; without
   `message` the thread stays idle. Then `t3_thread_read` it with asus's `environmentId`: it must be
   `preparing`, `queued`, `starting` or `running`. If it is `idle`, send the message with
   `t3_thread_send`; if it failed, say so and do the task here.
4. Send Karchi its link and end your turn. Never `t3_thread_interrupt` the moved thread and never do
   its work here in parallel.
