---
name: overenie
description: Verification Karchi can trust, done before saying any change is finished. Use whenever you are about to say hotové, funguje, fixnuté or done about something he will see or use (a UI, a shortcut, a service, a desktop setting, a script), at the end of every `zadanie` goal, and when he says over, prever, otestuj, neverím or si si istý.
---

# Overenie: proof, not a promise

Karchi does not trust "funguje" from the agent that wrote the change, and he is right: he asked
"takže už to funguje?" 28 times in October and often found it broken. Trust comes from four things:
the checks are fixed before the work, someone other than the builder runs them, every result leaves
evidence he can see in ten seconds, and every miss becomes a new check.

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
- Services: an HTTP request or a command against the real endpoint, plus a check that it survives a
  restart when it is meant to.
- Looks that no machine can judge ("not AI generic", "nice icons"): mark them `👁 tvoje oko`, put the
  screenshot beside the reference, and never count them as passed.

## 3. Verify with fresh eyes

After building, start a verifier that has not seen your work: a separate headless Claude on Opus, not a
subagent, because subagents run on Haiku and inherit your assumptions.

```sh
claude -p "$(cat overenie/verifier.md)" --model claude-opus-5-5 --effort high --no-session-persistence
```

`overenie/verifier.md` gives it only the checks, where the thing runs, and these rules: run
`overenie/run.sh`; then try to break each item by hand (another order, a reload or restart, keyboard
only, empty and long data, a second monitor); look at every screenshot yourself and compare it with the
reference; do not edit any code; write the verdict for each check (prešlo, neprešlo, nedá sa overiť)
with the evidence path to `overenie/verdikt.md`. Fix what it found and run it again, three rounds at
most. Then report what is still failing.

## 4. Show the evidence

Generate `overenie/<YYYY-MM-DD>/index.html` from the results, not from your own summary: one row per
check with its status, the screenshot or video, and the command that reruns it. Link it in the final
reply, or show it with `html_render` in T3. The reply lists every check that failed or could not be
verified, then the `zadanie` footer (Commit, Beží, Tvoj krok).

## 5. Every miss becomes a check

When Karchi finds something broken that the verification passed, first add a check that fails on it,
then fix it. Append one line to `~/inbox/overenie-chyby.md` on asus (`ssh asus`):
`- YYYY-MM-DD · <project> · <what the check missed> · <the new check>`. The morning retro reads this file,
so he can see how often a passed check was wrong.
