---
name: github
description: How to write on GitHub for Karchi - commit messages, branches, pull requests, issues and comments. Use before any git commit or push, any gh pr or gh issue command, and before writing a PR description or a reply to a review.
---

# Writing on GitHub

## Where changes go

- Karchi's personal projects (karchi-os, karchi-skills) are committed straight to `main` and pushed.
  No branches or pull requests.
- Work projects (eSYST) do not have an agreed workflow yet. Ask before a commit, push, branch or PR.
- Never open a pull request unless Karchi explicitly asks. One request is one PR.
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
- One problem per PR, but everything that fix needs (contracts, server, clients, tests, docs).
  Cleanup and a second fix go elsewhere.

The change:

- The smallest complete fix. Before opening, check what reviewers and bots will ask: an older client
  or server, concurrent runs, stale state (a reused PID, a leftover file), interruption halfway.
- A test that fails on `main` and passes with the fix, in the module's existing test file.
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

## Babysitting a PR

When Karchi says babysit or babysitting, Hermes on asus takes the PR until it is merged or closed (job "PR
babysitting", every 20 minutes). He hears from it only about major events. The full rule is the
"Babysitting" section of `~/.claude/AGENTS.md`.

- Finish any push the PR needs.
- Add one line to `~/.hermes/pr-babysit.list` on asus (from another machine through `ssh asus`):
  `owner/repo#number`, then a checkout path only for his own PR checked out on asus on the PR's branch.
  A line without a path is only watched.
- Do not call `watch_pull_request` and do not make a scheduled task of your own. Confirm in one sentence.
