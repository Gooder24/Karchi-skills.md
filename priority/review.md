# Inbox review

The inbox goes stale in two ways: items get done in some thread and stay open, and work Karchi
starts in a thread and leaves unfinished never reaches the inbox. Agents are told to update the
inbox as they go (SKILL.md), but they forget, so once a day this review reconciles the inbox with
what the threads on every machine actually did. It runs first in the nightly scheduled task, before
`worker.md`, and you can run it by hand when Karchi says „uprac inbox“.

## Read

1. The inbox `~/inbox/inbox.md` and the state file `~/worker/review-state.json` (hostname as the digest's first line
   prints it → UTC time of its last review, e.g. `"karchi": "2026-11-04T23:30:00"` for x270; missing:
   48 hours ago).
2. The digest of each machine since its time in the state file. On asus:
   `python3 ~/.claude/skills/priority/thread-digest.py --since <time>`; the others:
   `ssh -o ConnectTimeout=5 <dell|e540|x270> python3 - --since <time> < ~/.claude/skills/priority/thread-digest.py`.
   A machine that does not answer (x270 often sleeps) keeps its old time and is read next night.
3. Need more than the digest shows? Read that thread in full with the same script and
   `--thread <id> --messages 20` on its machine, or check the result itself (the file, the commit,
   the URL). Read only; never send to a thread, never write to a T3 database.

## Reconcile

4. Done: an open line whose result the threads show done and checked → `[x]`, move it under
   `## Hotové`, append ` · hotové <date>: <where the result is>`. If only Karchi's part is left,
   rewrite the line to that part.
5. Unfinished: a thread that ended waiting for Karchi (a „tvoj krok“, a question, a decision, a
   test only he can do) or stopped midway (interrupted, failed, a limit, his last message got no
   finished answer) and has no line yet → add one, P2 unless it blocks something:
   `- [ ] <date> · <what is left, one sentence> · <machine> vlákno „<title>“`.
   A thread that is still running, or that ended with everything done, adds nothing.
6. Stale wording: a line whose facts the threads changed (a version, a path, a step already done)
   → rewrite it to the current state. A line over 300 characters → cut it to what Karchi needs to
   act; the history belongs in the thread, not the inbox.
7. Not sure whether something is done: leave the line and append ` · revízia <date>: neviem
   overiť, <why>`. Never close a line on a guess, never delete one (only Karchi says „vyhoď“).
8. Old lines: open lines older than 7 days that no longer seem to hold but that you cannot close on
   evidence (deadline gone, superseded by another line, he said he does not use the thing) go into
   the morning report, one per line with the reason; he answers „vyhoď“ or keeps it.

## Finish

9. Write the inbox in one go (python: read, change only the lines concerned, write), then update
   `~/worker/review-state.json` with the time you started for each machine you read.
10. Add to the morning report `~/inbox/worker/<YYYY-MM-DD>.md` one line: „Revízia: N uzavretých,
   M pridaných, K upravených“ with the titles of what you closed or added, then the old lines of 8.
