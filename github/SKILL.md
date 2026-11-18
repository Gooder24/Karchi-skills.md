---
name: github
description: How to write on GitHub for Karchi - commit messages, branches, pull requests, issues and comments. Use before any git commit or push, any gh pr or gh issue command, before writing a PR description or a reply to a review, and before writing to another project's bug tracker by mail (Debian BTS).
---

# Writing on GitHub

## Where changes go

- Karchi's personal repos are full send: every repo of Gooder24's own except forks and the eSYST work repos
  (spotrex, eSYSTAK, partsheet, enex-crz-email-mvp). Commit straight to `main` and push without asking. No
  branches or pull requests; an open PR there is cleaned up at once (AGENTS.md, GitHub).
- Repos that his machines use by themselves (Karchi, 2026-11-18): karchi-os, karchi-os-headless-debian with
  its parts laptop-server and reboot-when-idle, weft, kalendarix and Karchi-skills.md. A change reaches them
  in exactly one of two ways:
  1. Commit straight to `main` and push, once the repo's own checks pass locally. This is the default.
     When CI on `main` then turns red, fix it in the next commit.
  2. Open a pull request, wait until the repo's tests (CI) pass on its current head, merge it yourself and
     only then deploy, all in the same turn. Never deploy before the tests pass.

  No third way may happen there: no PR left open for Karchi or a review, and no merge on red tests. When
  the tests stay red and you cannot fix them, close the PR with one sentence why and put the step in his
  inbox (skill `priority`).
- Work projects (eSYST) do not have an agreed workflow yet. Ask before a commit, push, branch or PR.
- Never open a pull request unless Karchi explicitly asks, apart from way 2 above. One request is one PR.
- A repo with `scripts/land.sh` (Partsheet) lands PRs only through it, never with `gh pr merge` or the
  merge button: it merges only when CI passed on the PR's current head. On a private repo without
  GitHub Pro nothing else stops a merge on red CI.

## Commits

- Conventional commit titles in plain language: `fix(web): new threads no longer spike CPU`.
- Never commit secrets or tokens.

## Pull requests that merge on the first review

These apply to every PR, open source and work (eSYST) alike. The goal is a PR a reviewer can approve
without asking anything. Evidence (Karchi, 2026-11-15): on T3 Code, outside bug-fix PRs in this shape
merge within hours; his first SSH fix was too naive and closed, and a feature PR waits unmerged.

Before writing code:

- Read the repo's CONTRIBUTING and PR template and follow them literally. If the repo does not accept
  something (T3 Code takes only bug fixes from outside the team: features go to Ideas discussions,
  not PRs), do not open the PR and tell Karchi why. Never argue in the PR that a feature is a fix.
- Search open PRs and issues first. If one covers the problem, do not open another: test it and tell
  Karchi, and comment what you saw only when he agrees.
- When an open PR on the same defect lists your problem as left out ("Not in this change") and the
  missing piece is small, the cheapest fix is a comment on that PR or its issue with the diagnosis and a
  short diff, which the maintainers' pipeline finishes. Offer Karchi that comment first; open your own PR
  only when he picks it (#37314, 15. 11.: a 15-line fix #34957 had listed as left out took a whole PR).
- A PR you do open names every related open PR in its body: what each fixes, what yours takes off its
  list, and that they merge cleanly (`git merge-tree --write-tree <your branch> <their head>`).
- One problem per PR, but everything that fix needs (contracts, server, clients, tests, docs).
  Cleanup and a second fix go elsewhere.

The change:

- The smallest complete fix. Before opening, check what reviewers and bots will ask: an older client
  or server, concurrent runs, stale state (a reused PID, a leftover file), interruption halfway.
- A test that fails on `main` and passes with the fix, in the module's existing test file.
- A test of formatted dates, times or numbers takes its expected text from `Intl` in the host locale
  (`new Intl.DateTimeFormat(undefined, { …, hour12 })`), not English literals, and passes under
  `LC_ALL` sk_SK, de_DE, ja_JP and ar_EG (#37314: three review rounds went to an en-US-only assertion).
- The repo's own checks green on the changed files (T3 Code: `vp run check:changed`).

The body (use the repo's template; without one, these headings):

- **Problem**: one or two sentences, with a repro. A table of input / today / expected works well.
- **Change**: what changed and why that fixes it. No narration of every file.
- **Scope**: one sentence, `Fixes #N` or "small fix of an obvious bug". No lobbying paragraph.
- **Verification**: the test output on `main` vs the branch, plus a real run (a transcript; for a UI
  change before/after screenshots, and a short video for motion or timing). "Tests pass" is not evidence.
  End with **Not checked:** and what you could not run.
- End with the model and harness that did the work.
- Upload images to GitHub (PR body or comment); never commit assets that only the PR needs.

T3 Code UI evidence: `github/t3code-evidence/before-after.sh <home-dir> node <skill>/capture.mjs …`
from the PR checkout starts an isolated dev server, captures this branch, swaps in `origin/main`'s copies
of the changed files, captures again, and restores them. The header of each file says how to seed data
and which options exist (`--setup`, `--hover`, `--text`, `--clip`). Run `vp run check:changed` where you
work; only when it cannot run there at all (lint or knip crash for lack of memory), run it over `ssh asus`.

After opening (in work projects, ask before each push, as above):

- Read every bot finding (CodeRabbit, Macroscope), including the security and risk sections. Fix real
  ones with a push and a short reply, dismiss false ones with a reason. Never close your own PR to
  dodge feedback.
- Keep it mergeable (rebase on conflicts) and under the repo's open-PR limit.

## Issues

- One problem per issue: what happened, a diagnosis naming files and functions, deterministic steps
  to reproduce, version and environment, logs, related issues, the workaround.
- Attach evidence when filing; do not promise a screenshot "to follow".
- When you have a fix, tell Karchi in the same reply and, once he asks for the PR, open it with
  `Fixes #N`; an issue that only offers a fix gets fixed by someone else.

## Bug trackers by mail (Debian BTS and similar)

- The first line of the body (after a `Control:` line, if any) says that an AI assistant did the reproduction
  and the analysis. Never at the end.
- At most about 15 lines: what is wrong and where, the fix, one or two numbers that show it was tested, the
  ask. The root-cause walk-through, tables per release, scripts and logs go into attachments or wait until
  someone asks. Side findings are separate reports, not paragraphs.
- Evidence (2026-11-17): Debian #1144467 got a 150-line reply with the disclosure as its last paragraph. The
  maintainer's answer: "Next time please disclose this *before* the wall of mega-verbose text."
- Send it with `weft mail` only when Karchi says so. Hermes watches a Debian bug that has a line in
  `~/.hermes/debian-bugs.list` on asus (job "Debian bugs").

## Babysitting a PR

When Karchi says babysit or babysitting, Hermes on asus takes the PR until it is merged or closed (job "PR
babysitting", every 20 minutes). He hears from it only about major events. The full rule is the
"Babysitting" section of `~/.claude/AGENTS.md`.

- Finish any push the PR needs.
- Add one line to `~/.hermes/pr-babysit.list` on asus (from another machine through `ssh asus`):
  `owner/repo#number`, then a checkout path only for his own PR checked out on asus on the PR's branch.
  A line without a path is only watched.
- Do not call `watch_pull_request` and do not make a scheduled task of your own. Confirm in one sentence.
