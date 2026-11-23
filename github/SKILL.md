---
name: github
description: How to write on GitHub for Karchi - commit messages, branches, pull requests, issues and comments. Use before any git commit or push, any gh pr or gh issue command, before writing a PR description or a reply to a review, and before writing to another project's bug tracker by mail (Debian BTS).
---

# Writing on GitHub

## Where changes go

- Karchi's personal repos are full send: every repo of Gooder24's own except forks and the eSYST work repos
  (spotrex, eSYSTAK, enex-crz-email-mvp). Partsheet is his own (a songbook for his choir), not eSYST. Commit straight to `main` and push without asking. No
  branches or pull requests; an open PR there is cleaned up at once (AGENTS.md, GitHub).
- Repos that his machines use by themselves (Karchi, 2026-11-18): karchi-os, karchi-os-headless-debian with
  its parts laptop-server and reboot-when-idle, weft, kalendarix and Karchi-skills.md. A change reaches them
  in exactly one of two ways:
  1. Commit straight to `main` and push, once the repo's own checks pass locally. This is the default.
     When CI on `main` then turns red, fix it in the next commit.
  2. Open a pull request, wait until the repo's tests (CI) pass on its current head, merge it yourself and
     only then deploy, all in the same turn. Never deploy before the tests pass.

  No third way may happen there: no PR left open for Karchi or a review, and no merge on red tests. When
  the tests stay red and you cannot fix them, close the PR with one sentence why and name his step at the end
  of the reply (it waits in the thread; skill `priority`).
- Work projects (eSYST) do not have an agreed workflow yet. Ask before a commit, push, branch or PR.
- Never open a pull request unless Karchi explicitly asks, apart from way 2 above. One request is one PR.
- A repo with `scripts/land.sh` (Partsheet) lands PRs only through it, never with `gh pr merge` or the
  merge button: it merges only when CI passed on the PR's current head. On a private repo without
  GitHub Pro nothing else stops a merge on red CI.

## ship and land (Karchi, 2026-11-21)

The routine steps are commands, not hand-typed git and gh calls (each hand step costs a model round trip):

- `ship -m "<title>" [-m "<body>"] FILE...` is the default way: on `main` of a full-send repo it stages
  exactly those files (it refuses when anything else is staged), commits, `git pull --rebase --autostash`,
  pushes and waits for CI on that commit. Exit 0 pushed and green (or no CI), 1 pushed but CI failed (the
  failed log tail is printed: fix it in the next `ship`), 2 nothing pushed.
- `land <pr|url>` is way 2: it updates a branch that is behind, waits for CI on the current head, merges with
  `--match-head-commit`, deletes the branch and pulls the local base. It uses `scripts/land.sh` where one
  exists. Exit 0 merged, 1 not merged (CI red, conflict, timeout), 2 refused.
- Both refuse the eSYST work repos until Karchi says yes in the thread; then add `--yes-work`.

## CI runs on asus (Karchi, 2026-11-20)

- Every job of Karchi's personal repos runs on asus, not on GitHub's minutes: `runs-on` is
  `${{ github.event.pull_request && github.event.pull_request.head.repo.full_name != github.repository && 'ubuntu-24.04' || 'asus' }}`,
  so only a pull request from a fork (someone else's code) goes to GitHub's machines. A new workflow
  gets this line; a step that needs `sudo` gets `if: runner.environment == 'github-hosted'` and its
  packages are installed on asus once by hand.
- A repo with CI gets its runner with `github/asus-runner.sh <repo>` (from any machine; `--remove`
  takes it away). It runs as the user `github-ci`, which has no Docker and so no way to root: a job on
  asus cannot use `services:` or `container:` (a database comes from an embedded one, e.g. embedded-postgres). The
  runner's hook `reject-forks.sh` fails a fork's job even when its workflow asks for asus.
- Jobs that need another OS (kalendarix `release.yml`: Windows, macOS) stay on GitHub. The eSYST repos
  spotrex and eSYSTAK have their own runners on asus from before, as `github-runner`, which is in the
  docker group because their tests run in Docker.

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
- A PR you do open names each related open PR in one line: what it fixes and that yours merges cleanly
  with it (`git merge-tree --write-tree <your branch> <their head>`). No table and no paragraph per PR:
  in a sample of 40 unvouched PRs T3 Code merged 10. to 18. 11. the median body had 2,900 characters,
  #37314 had 7,900.
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

T3 Code merges most outside bug fixes through the maintainers' pipeline, not a person's review. Measured
18. 11. 2026 on 197 outside PRs merged 15. to 18. 11. (about half of that window's): 165 ended with a
maintainer's commit, a median 0.9 h from opening to merge. A maintainer labels the PR `takeover:in-progress`; an agent merges
`main`, reworks the fix, captures its own proof in a real dev app and merges. It stops with
`takeover:blocked` and a `factory:stopped-<reason>` comment. In a sample of 68 stopped PRs (of about 410
with that label), 27 needed something its workers cannot run (macOS, Windows, a provider login), 20 showed
no bug on `main`, and 13 got a push from outside the pipeline during the takeover, in 10 of them from the
author (#37314: three force-pushes in the 13 minutes after the label). So:

- Pick bugs their worker can show in an isolated dev web app (`vp run dev`, the Replay provider, seeded
  data). A bug that needs other hardware or accounts gets an issue with the diagnosis, or a PR whose body
  carries a capture of the bug on `main` and the exact steps.
- Write repro steps that a stranger can run unchanged on `main`, and say what to look at.
- Once the PR is open, do not push while it is `takeover:in-progress` or before a maintainer has looked:
  the pipeline merges `main` and reworks the fix itself. Answer a bot finding in a reply; push only when a
  person asks for a change, or to resolve a `needs-rebase` label when no takeover is running.
- Features from authors who are not in `.github/VOUCHED.td` are closed (7 of the 197 merged were `feat`,
  all from vouched authors). The maintainers add people to that list by hand, lately Theo in commits like
  `chore: vouch <login>`.
- The cheapest help is what CONTRIBUTING asks for first: link a duplicate, confirm that an issue no longer
  happens on the latest release, or test an open PR and comment what you saw.

After opening (in work projects, ask before each push, as above):

- Read every bot finding (CodeRabbit, Macroscope), including the security and risk sections. Fix real
  ones with a push and a short reply (T3 Code: a reply only, see above), dismiss false ones
  with a reason. Never close your own PR to
  dodge feedback.
- Keep it mergeable (rebase on conflicts; T3 Code: only on `needs-rebase` and never during a takeover)
  and under the repo's open-PR limit.

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
