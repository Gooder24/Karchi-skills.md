---
name: overenie
description: Verification Karchi can trust, done before saying any change is finished. Use whenever you are about to say hotové, funguje, fixnuté or done about something he will see or use (a UI, a shortcut, a service, a desktop setting, a script), at the end of every `zadanie` goal, and when he says over, prever, otestuj, neverím or si si istý.
---

# Overenie: proof, not a promise

Karchi does not trust "funguje" from the agent that wrote the change, and he is right: he asked
"takže už to funguje?" 28 times in October and often found it broken. An audit on 7. 11. 2026 of 343
threads on five machines found him discovering the breakage himself after a done-claim at least 20
times, also after this skill existed, on 5 and 6 November (partsheet 404, Rerun, Weft), because the
skill was used on 4-5 November and then skipped. When the independent verifier did run, it caught real
errors that the builder's own green `run.sh` let through. Trust comes from four things: the checks are
fixed before the work, someone other than the builder runs them, every result leaves evidence he can
see in ten seconds, and every miss becomes a new check.

Every reply after a turn that changed something ends with one line he can trust at a glance:

- `Overenie: <full path to …/overenie/verdikt.md>`, written in this turn by the independent verifier;
- `Overenie: neoverené – <what he should try and what he should then see>`; then the reply calls
  nothing hotové or funguje;
- `Overenie: netreba – <why>`, only for a change he will not see or use;
- `Overenie: prebieha – <what still runs>`, only for work that outlives this thread's wait (another thread, a
  build of hours) and never for the verifier: a turn that ends puts the thread in Done, and on 10. 11. he saw
  unfinished work there while its verifier still ran.

The Stop hook `hooks/overenie-gate.py` (asus, x270, dell, e540) sends a turn back once when the line is
missing, names no such fresh, non-empty file, or says neoverené while the opening says hotové. Write the line truthfully from the start; never touch
an evidence file or pick `netreba` only to get past the hook.

## 1. Fix the checks before you build

Write the checks into the goal file (`zadanie`, section „Hotové keď“), or into
`overenie/checks.md` in the project for a smaller change. Each check states what he would do
("otvorím DM", "stlačím Super+N") and what he should then see. Once work has started, do not weaken a
check. If a check turns out to be wrong, change it with a line `zmenené: <prečo>` and name the change in the
reply.

## 2. Make every check runnable

Put the checks in `overenie/` in the project, as a script or a Playwright spec, with one runner
`overenie/run.sh` that exits non-zero when anything fails. This becomes the project's regression suite:
run it after every later change too, so an old fix cannot break without anyone noticing (his "zase" and
"stále").

`overenie/` is in the global gitignore on every machine (`install.sh` puts it there), so none of it shows in
T3's changed files or goes into a commit. On 8. 11. the card under a Weft reply listed 17 files, 829 of 928
lines from `overenie/`, and he lost what the change was. The suite stays on disk, but git no longer carries
it between machines. Never `git add -f` it and never move checks to another folder to get them into git.

- UI: Playwright with the system Chromium (`/usr/bin/chromium` on dell and asus). Drive it the way he
  does: keyboard first, his window size, then a phone width when the app has one. Save a screenshot per
  check, next to the reference image when there is one, and a short video for anything that moves or
  needs several key presses.
- Desktop (x270, Hyprland): `hyprctl` and `grim` screenshots; say when a check needs a restart.
  Never put anything on his live screen to test it (a lock screen demo, a fullscreen overlay, a modal, a test
  window outside workspace 5): he is working, it interrupts him, he clicks it away, and the check then measures
  his desktop instead (7. 11.: `dms ipc call lock demo` from run.sh and the verifier, several times). Test such UI
  in the KarchiOS test VM (`python3 -B tools/vm.py test-up` → `push` → screenshot → `test-down`). If only his
  screen will do, ask once for a moment and show it once, never from a verifier.
- Services: an HTTP request or a command against the real endpoint, plus a check that it survives a
  restart when it is meant to.
- Where he will see it, test it there, not on a stand-in: his x270 session over `ssh x270` (`hyprctl`,
  `grim` of the live screen), his phone through Playwright WebKit with an iPhone profile on dell, the
  public URL rather than localhost. What you truly cannot reach (his real chats, a physical cable, his
  eyes) is a `tvoj krok` check: put it on the `Overenie: neoverené – …` line and add it to his inbox.
- Looks that no machine can judge ("not AI generic", "nice icons"): mark them `👁 tvoje oko`, put the
  screenshot beside the reference, and never count them as passed.

## 3. Verify with fresh eyes

First run `overenie/run.sh` yourself. A verifier is the expensive step: never start one on a red run. Fix the
failure, or, when it is not your change (changed data, a flaky machine), name each failing check and your guess in the
brief as unverified, so the verifier judges it instead of rediscovering it. Start the verifier once the whole change
he asked for is finished, not after each partial step: several commits for one ask go to one round.

After building, start a verifier that has not seen your work, always through `verify.sh` (Weft: `tools/verify-on-asus`),
never as a subagent, a T3 `delegate_task` or a new thread: those inherit your assumptions or load a whole agent with
every tool, and on 10. 11. a Codex builder's `delegate_task` to Claude Opus spent his Claude limit on a routine check.
`verify.sh` starts Codex first (it spends the ChatGPT limit, not Karchi's Claude limit, and in the 9. 11. pilot it found
as much as Opus in half the time) and Claude Opus when Codex leaves no verdict. This holds when Codex built the change
too: a fresh Codex has not seen your work. Only for `Hĺbka: dôkladná` on a change Codex built, set
`OVERENIE_CLAUDE_FIRST=1`, so a different model checks it. On 5. 11. two verdicts were written by the builder because
the verifier hit the limit; that must not happen again.

```sh
cd "$PROJECT" && ~/.work/karchi-skills/overenie/verify.sh overenie/verifier.md   # [verdict, default overenie/verdikt.md]
```

The turn waits for the verdict, so the thread stays in Working until the work is really done. Codex: run it in the
foreground with a timeout of an hour. Claude: run it in the background and call `t3_background_wait` with its task
ID, then read the verdict in the same thread before you reply. Never end the turn with `Overenie: prebieha` while the
verifier runs. The verifier needs network and SSH to reach
the real target, hence the full-access sandbox; `verifier-agents.md` forbids it to edit anything but the verdict
and fixes the verdict's shape and how deep it goes. Claude gets six tools: the default set of about a hundred costs
about 27 000 tokens on every one of its steps (measured 9. 11.). Every run logs its usage to
`~/.claude/overenie-usage.jsonl`.
If no verdict appears, every check that only the verifier could judge is `nedá sa overiť` and the reply
ends with `Overenie: neoverené – …`. A verdict written by the builder never says `passed` for those checks.

On dell and e540 (3.7 GB) do not run the verifier locally: an Opus verifier with its browser took an hour
there and froze dell for every other thread (7. 11.). Run it on asus (15 GB). Weft has a runner,
`tools/verify-on-asus <brief> [verdict]`: it copies the working tree, uncommitted changes included, runs the
command above on asus and brings back only the verdict and `verifier-output.txt`. Any project without one: copy
the tree to asus and run the same command there over `ssh asus`. The verifier stays just as strict; only where it
runs changes.

Depth follows the risk, because a detailed round on KarchiOS or Weft ate too much of his limits (9. 11.). By default
the verifier checks only this change: the brief's checks, the two or three likeliest ways to break it, your run.sh
output instead of a rerun, about ten minutes. Write `Hĺbka: dôkladná` in the brief only for data that can be lost,
messages to real people, live company services, code every case shares, or when he asks for it.

`overenie/verifier.md` is short and points instead of pasting: the checks (or the path to `checks.md`), where the
thing runs, what changed (`git show <commits>` or a diff path), the path of your run.sh output, and these rules. Earlier
verdicts and long context go in as paths it reads when it needs them, and `Hĺbka: dôkladná` when it applies. The
rules: read what each check really measures and flag a check that tests a proxy instead of
what he sees (the 5. 11. partsheet check measured only the line width and missed chords torn from their
words; a run.sh that finds a number anywhere on the page instead of in its row); then try to break the change by hand the ways that apply (another order, a reload or
restart, keyboard only, empty and long data, a second monitor); look at every screenshot yourself and compare it with the
reference; do not edit any code; write the verdict for each check (passed, failed, unverifiable)
with its evidence to `overenie/verdikt.md`, in the terse shape `verifier-agents.md` fixes: only the builder reads it.

Fix what it found, run `overenie/run.sh` yourself, then start a targeted round: two rounds at most, three for
`Hĺbka: dôkladná`. Its brief names
the findings you fixed and the fix's diff, and gives your run.sh output in place of a rerun. The verifier checks the fixed
findings in the real UI or target, follows every path the changed code runs on (not only the one the finding named) and
tries to break each, and reruns run.sh only when it doubts your output or the brief says `Hĺbka: dôkladná`. When the fix touches code that every case
shares, the brief says `Hĺbka: dôkladná` and it re-checks every check the fix can reach. It never trusts the builder's
word on a check it judges. Then report what is still failing.

## 4. Report

No report page: he does not read one (10. 11.). The reply names in a sentence or two only what failed or could not be
verified, then the `zadanie` footer when there is one (Commit, Beží, Tvoj krok), and the `Overenie:` line with the
path of `verdikt.md`.

## 5. Every miss becomes a check

When Karchi finds something broken that the verification passed, first add a check that fails on it,
then fix it. Append one line to `~/inbox/overenie-chyby.md` on asus (`ssh asus`):
`- YYYY-MM-DD · <project> · <what the check missed> · <the new check>`. The morning retro reads this file,
so he can see how often a passed check was wrong.
