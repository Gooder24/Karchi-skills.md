---
name: priority
description: Karchi's inbox and priority gate. Use at the start of every thread for Karchi before the first tool call, when he starts a different task in the same thread, and whenever he says inbox, priorita, zapíš si, zapíš do inboxu, nápad, úloha, čo ďalej, čo čaká or hotové.
---

# Inbox and priority gate

Karchi keeps one inbox for everything he wants to do: `~/inbox/inbox.md` on asus. From any machine
(quote the command, so `~` expands on asus):

    ssh -o ConnectTimeout=5 asus 'cat ~/inbox/inbox.md'

One line per item, `- [ ] YYYY-MM-DD · what · why or by when`, under `## P1 teraz` (important and
urgent: a deadline, blocks something, people or money waiting), `## P2 ďalej` (important, no
deadline), `## P3 niekedy` (ideas) and `## Hotové` (done, `- [x]`).

## At the start of a task

1. Read the inbox: one command, before the first tool call of the task.
2. Compare the task with P1. If something there is more important or more urgent than what he just
   asked, say it in one line in Slovak, „V inboxe čaká: <item> (P1, od <date>).“, then do what he
   asked anyway. The decision is his; he does not want to be blocked or asked. When nothing beats the
   task, do not mention the inbox.
3. If the task is already in the inbox, do it and move it to Hotové when it is done.
4. If asus does not answer, say „inbox na asuse nedostupný“ once and go on.

## Editing the inbox

- „zapíš do inboxu“, „zapíš si“, or an idea or task he does not want now: append one line with
  today's date under P1, P2 or P3 by the rules above (P1 only with a deadline or a real blocker; when
  unsure, P2). Confirm in one line with the priority you chose; he corrects it if he disagrees.
- „ukáž inbox“, „čo ďalej“, „čo čaká“: show the open items, P1 first, one line each, no commentary.
- „hotové“, or you finished an inbox item: change `[ ]` to `[x]`, keep the date, move the line to
  Hotové. Delete a line only when he says „vyhoď“.
- Change only the lines concerned, keep the format, and put nothing else into `~/inbox`. A safe way
  to edit from another machine is `ssh asus 'python3 - <<"PY" ... PY'` on the file.
