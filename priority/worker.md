# Night worker

A scheduled T3 task runs this every night (new thread per run) so Karchi is not the bottleneck:
the inbox is the queue, the worker takes one item. Karchi is asleep: never ask him anything, never
wait for him. The runs share his Claude subscription, so one item per night.

## Pick one item

1. The inbox is in your context (SessionStart hook); if not: `ssh -o ConnectTimeout=5 asus 'cat ~/inbox/inbox.md'`.
2. Take the highest open item you can finish without Karchi. Not allowed: his logins, passwords,
   tokens or secrets; decisions that are his (lines with „rozhodnúť“, client questions, money);
   anything on the VPS beyond reading; commits or pushes to work repos (spotrex, eSYSTAK, enex-*,
   porter, anything of eSYST); changes to the x270 desktop or installing software on x270.
   Allowed: karchi-os and karchi-skills on `main` per the github skill; asus, dell and e540;
   reading anywhere he can read.
3. Heavy work goes through `ssh asus` (CLAUDE.md rule).

## Do it

4. Finish the item completely and test it. Then in the inbox: `[ ]` to `[x]`, move the line under
   `## Hotové`, append ` · hotové <date>: <where the result is>`.
5. If it cannot be finished: leave it open and append ` · <date> worker: <what is missing, what was
   prepared>`. Never leave half-done changes behind: finish or revert.
6. One item per night. If it took under 30 minutes you may take a second one, never a third.

## Items that need Karchi

7. For the top P1 item that needs him, prepare everything so that one step remains (the exact
   command or click) and append that step to its line. At most one such preparation per night.

## When nothing is doable

8. Check his systems and write findings as new inbox items with a proposed priority (P3 unless
   something is broken): disk space on x270, asus, dell, e540; services `diktovanie` (asus) and
   `voxtype` (x270); failed systemd units; open karchi-os PRs; this worker's own schedule. A healthy
   system adds nothing. Do not invent work.

## Report

9. Write `~/inbox/worker/<YYYY-MM-DD>.md` on asus (the morning's date): 3 to 6 lines in Slovak,
   what was done (path or link), what waits for his one step, what was added to the inbox. The
   SessionStart hook shows it in his first session of the day. No questions.
10. On a usage limit or any hard stop: note where you stopped in the inbox line and in the report,
    then stop.
