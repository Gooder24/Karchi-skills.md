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

- `Overenie: <full path to …/overenie/verdikt.md or …/overenie/<date>/index.html>`, written in this
  turn after the checks below and the independent verifier;
- `Overenie: neoverené – <what he should try and what he should then see>`; then the reply calls
  nothing hotové or funguje;
- `Overenie: netreba – <why>`, only for a change he will not see or use;
- `Overenie: prebieha – <what still runs>`.

The Stop hook `hooks/overenie-gate.py` (asus, x270, dell, e540) sends a turn back once when the line is
missing, names no such fresh, non-empty file, or says neoverené while the opening says hotové. Write the line truthfully from the start; never touch
an evidence file or pick `netreba` only to get past the hook.

## 1. Fix the checks before you build

Write the checks into the goal file (`zadanie`, section „Hotové keď“), or into
`overenie/checks.md` in the project for a smaller change. Each check states what he would do
("otvorím DM", "stlačím Super+N") and what he should then see. Once work has started, do not weaken a
check. If a check turns out to be wrong, change it with a line `zmenené: <prečo>`, so he sees it in the
report.

## 2. Make every check runnable

Put the checks in `overenie/` in the project, as a script or a Playwright spec, with one runner
`overenie/run.sh` that exits non-zero when anything fails. This becomes the project's regression suite:
run it after every later change too, so an old fix cannot break without anyone noticing (his "zase" and
"stále").

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

After building, start a verifier that has not seen your work: a separate headless Claude on Opus, not a
subagent, because subagents run on Haiku and inherit your assumptions. When Claude cannot run it (the
5-hour limit, an expired login), use Codex, a different model with its own limits. On 5. 11. two
verdicts were written by the builder because the verifier hit the limit; that must not happen again.

```sh
cd "$PROJECT" && rm -f overenie/verdikt.md
export OVERENIE_VERIFIER=1   # tells the Stop hook this is the verifier, not a builder
claude -p "$(cat overenie/verifier.md)" --model claude-opus-5-5 --effort high --no-session-persistence \
  --permission-mode bypassPermissions < /dev/null > overenie/verifier-output.txt 2>&1
# claude exits 0 even when it hit the limit or could not write, so judge by the verdict file
[ -s overenie/verdikt.md ] || "$(command -v codex || echo ~/.local/bin/codex)" exec --skip-git-repo-check \
  -s danger-full-access -C "$PWD" "$(cat overenie/verifier.md)" < /dev/null >> overenie/verifier-output.txt 2>&1
```

Run it in the foreground or as `systemd-run --user` with a wait on `overenie/verdikt.md`: in a T3 thread a
plain background command can end before the verifier does. The verifier needs network and SSH to reach
the real target, hence the full-access sandbox; `verifier.md` forbids it to edit anything but the verdict.
If no verdict appears, every check that only the verifier could judge is `nedá sa overiť` and the reply
ends with `Overenie: neoverené – …`. A verdict written by the builder never says `prešlo` for those checks.

On dell and e540 (3.7 GB) do not run the verifier locally: an Opus verifier with its browser took an hour
there and froze dell for every other thread (7. 11.). Run it on asus (15 GB). Weft has a runner,
`tools/verify-on-asus <brief> [verdict]`: it copies the working tree, uncommitted changes included, runs the
command above on asus and brings back only the verdict and `verifier-output.txt`. Any project without one: copy
the tree to asus and run the same command there over `ssh asus`. The verifier stays just as strict; only where it
runs changes.

`overenie/verifier.md` gives it only the checks, where the thing runs, and these rules: run
`overenie/run.sh`; read what each check really measures and flag a check that tests a proxy instead of
what he sees (the 5. 11. partsheet check measured only the line width and missed chords torn from their
words; a run.sh that finds a number anywhere on the page instead of in its row); then try to break each item by hand (another order, a reload or restart, keyboard
only, empty and long data, a second monitor); look at every screenshot yourself and compare it with the
reference; do not edit any code; write the verdict for each check (prešlo, neprešlo, nedá sa overiť)
with the evidence path to `overenie/verdikt.md`. Fix what it found and run it again, three rounds at
most. Then report what is still failing.

## 4. Show the evidence

Generate `overenie/<YYYY-MM-DD>/index.html` from the results, not from your own summary: one row per
check with its status, the screenshot or video, and the command that reruns it. Put its full path (or that of
`verdikt.md`) on the reply's `Overenie:` line, which is what the Stop hook checks, and show it with
`html_render` in T3 when it has screenshots.
The reply lists every check that failed or could not be verified, then the `zadanie` footer (Commit,
Beží, Tvoj krok).

## 5. Every miss becomes a check

When Karchi finds something broken that the verification passed, first add a check that fails on it,
then fix it. Append one line to `~/inbox/overenie-chyby.md` on asus (`ssh asus`):
`- YYYY-MM-DD · <project> · <what the check missed> · <the new check>`. The morning retro reads this file,
so he can see how often a passed check was wrong.
