---
name: github
description: How to write on GitHub for Karchi - commit messages, branches, pull requests, issues and comments. Use before any git commit or push, any gh pr or gh issue command, and before writing a PR description or a reply to a review.
---

# Writing on GitHub

## Where changes go

- Karchi's personal projects (karchi-os, karchi-skills) are committed straight to `main` and pushed.
  No branches or pull requests.
- Work projects do not have an agreed workflow yet. Ask before creating a branch or a PR.
- Never open a pull request unless Karchi explicitly asks. One request is one PR.
- A repo with `scripts/land.sh` (Partsheet) lands PRs only through it, never with `gh pr merge` or the
  merge button: it merges only when CI passed on the PR's current head. On a private repo without
  GitHub Pro nothing else stops a merge on red CI.

## Commits and pull requests

- Conventional commit titles in plain language: `fix(web): new threads no longer spike CPU`.
- PR body: the problem in a sentence or two, then how you fixed it. End with the model and harness
  that did the work.
- UI changes need before/after images; motion or timing needs a short video. Upload them to GitHub
  (PR body or comment); never commit screenshots or assets that only the PR needs.
- Never commit secrets or tokens.

## Babysitting a PR

When Karchi says babysit or babysitting, Hermes on asus takes the PR until it is merged or closed (job "PR
babysitting", every 20 minutes). He hears from it only about major events. The full rule is the
"Babysitting" section of `~/.claude/AGENTS.md`.

- Finish any push the PR needs.
- Add one line to `~/.hermes/pr-babysit.list` on asus (from another machine through `ssh asus`):
  `owner/repo#number`, then a checkout path only for his own PR checked out on asus on the PR's branch.
  A line without a path is only watched.
- Do not call `watch_pull_request` and do not make a scheduled task of your own. Confirm in one sentence.
