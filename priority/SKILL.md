---
name: priority
description: Karchi's inbox and priority gate. Use at the start of every thread for Karchi before the first tool call, when he starts a different task in the same thread, before moving a thread to asus, and whenever he says inbox, priorita, zapíš si, zapíš do inboxu, nápad, úloha, čo ďalej, čo čaká or hotové.
---

# Inbox and priority gate

Karchi keeps one inbox for everything he wants to do: `~/inbox/inbox.md` on asus. From any machine
(quote the command, so `~` expands on asus):

    ssh -o ConnectTimeout=5 asus 'cat ~/inbox/inbox.md'

One line per item, `- [ ] YYYY-MM-DD · what · why or by when`, under `## P1 teraz` (important and
urgent: a deadline, blocks something, people or money waiting), `## P2 ďalej` (important, no
deadline), `## P3 niekedy` (ideas) and `## Hotové` (done, `- [x]`).

## At the start of a task

1. The inbox is already in your context: the SessionStart hook `inbox-context.sh` (this folder,
   wired in `~/.claude/settings.json` on every machine) prints the open items when a session starts.
   If it is missing, read it with the command above before the first tool call.
2. Compare the task with P1. If something there is more important or more urgent than what he just
   asked, say it in one line in Slovak, „V inboxe čaká: <item> (P1, od <date>).“, then do what he
   asked anyway. The decision is his; he does not want to be blocked or asked. When nothing beats the
   task, do not mention the inbox.
3. If the task is already in the inbox, do it and move it to Hotové when it is done.
4. If asus does not answer, say „inbox na asuse nedostupný“ once and go on.

## Moving the thread to asus

CLAUDE.md („Kde beží práca“) moves a thread that does not need its machine to asus. The moved
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

## Editing the inbox

- „zapíš do inboxu“, „zapíš si“, or an idea or task he does not want now: append one line with
  today's date under P1, P2 or P3 by the rules above (P1 only with a deadline or a real blocker; when
  unsure, P2). Confirm in one line with the priority you chose; he corrects it if he disagrees.
- „ukáž inbox“, „čo ďalej“, „čo čaká“: show the open items, P1 first, one line each, no commentary.
- „hotové“, or you finished an inbox item: change `[ ]` to `[x]`, keep the date, move the line to
  Hotové. Delete a line only when he says „vyhoď“.
- Change only the lines concerned, keep the format, and put nothing else into `~/inbox`. A safe way
  to edit from another machine is `ssh asus 'python3 - <<"PY" ... PY'` on the file.

## Night worker

A scheduled T3 task (00:30, new thread per run) works through the inbox while Karchi sleeps; its
rules are in `worker.md` here. Its report lands in `~/inbox/worker/<date>.md` on asus and the hook
shows it in the morning.
