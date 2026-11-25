---
name: full-stop
description: Trigger this if the user says 'full stop', even as a closing "Full stop." that reads like emphasis.
---

# Full Stop

Do the same work as `full-send`, but stop with the PR ready for the user to merge.
Never merge it.

In a repo Karchi does not own (someone else's open-source project), `oss-prispevky` wins over this
skill: nothing is filed before his „podaj“ and nothing is merged by us. The work ends there with the
branch pushed to his fork, the PR body and the `obhajoba` ready for him to read.

Read [full-send](../full-send/SKILL.md) and follow its workflow, proof rules,
review, and babysitting steps. An explicit "full stop" request authorizes that
work without a separate "full send" request. That includes full-send's
testing permission. A "full stop" request is the permission for the test
methods Proof needs, even when a project file says to ask first, for
example before computer use. Use those methods directly. Its merge
permission does not apply. The overrides below take precedence.

## No merging

You may commit, push, rebase, fix conflicts, and use `--force-with-lease` on
this task's branch. Never merge, enable auto-merge, enter a merge queue, push
to the default branch, bypass branch protection, or delegate those actions.

Disable existing auto-merge and remove the PR from any merge queue before
work begins; check again before each push. Report these changes. If you
cannot prevent automatic merging, report the blocker before proceeding.

## Visual changes: frames he can step through

When the change is something Karchi sees (a UI, a page, a layout, a desktop look), the handoff shows him how it
looks before he merges (Karchi, 2026-11-23):

0. The PR body on GitHub shows every changed screen before and after (`github` skill, "UI changes",
   `pr-shots`); the frames below are the same screens for T3.
1. Take the proof's screenshots as a sequence, in the order he would see them (the start, each step or key, the
   end; a phone width last: the GIF fits it into the first frame's size), named `01-<what>.png`, `02-<what>.png`.
   The proof harness usually makes them already.
2. `~/.work/karchi-skills/full-stop/frames.sh <dir> <frames…>` makes `<dir>/flow.gif` (1.5 s a frame) and
   `<dir>/frames.html` (←/→, buttons, a slider, each frame's name as caption). It needs ffmpeg, so on dell run it on
   asus, copy `<dir>` back into the project's `overenie/<date>/` and run `frames.sh --html <dir>` there.
3. In T3: `html_render` with `path` to `frames.html` above the handoff (no `html_preview`: its picture costs tokens
   and `frames.sh` prints the height to give it). Put the GIF in the reply as
   `![…](/absolute/path/flow.gif)` and name the folder, so he can open each PNG in T3's file viewer.
4. Do not read the GIF or the frames back to yourself for this; look only at what the proof needs. Frames stay in
   gitignored `overenie/` on his machines and never go into a commit; into a PR only by full-send's rule and only
   when they show none of his private data (chats, names).

## Stop at the gate

Use full-send's merge gate as the readiness check. Replace its merge and
final report steps with a handoff. Proof and review must cover the final diff;
recheck behavior changes and meaningful conflict fixes before handoff.

Fetch the target branch and check the live PR's head, base, checks, reviews,
and mergeability. Confirm it is open, not a draft, and not set to merge
without the user. If someone else merged it, report that instead.

- **Ready to merge:** the merge gate passes. Leave the PR open and unmerged.
- **Waiting for required approval:** only human approval remains. Confirm
  that this is the actual blocker.
- **Blocked:** explain what prevents readiness, what you tried, and what is
  needed. Follow full-send's rules for asking the user.

In T3 Code, call `unwatch_pull_request` before the handoff or a question.
Report the PR link, final head, verdict, proof, reviewer outcome, and remaining
risks. State whether the PR is still open and unmerged.
