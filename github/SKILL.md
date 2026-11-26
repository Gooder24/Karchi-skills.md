---
name: github
description: How to write on GitHub for Karchi - commit messages, branches, pull requests, issues and comments. Use before any git commit or push, any gh pr or gh issue command, before writing a PR description or a reply to a review.
---

# Writing on GitHub

## Where changes go

- Karchi's personal repos are full send: every repo of Gooder24's own except forks and the eSYST work repos
  (enex-crz-email-mvp, and every repo of the organization `e-SYST`: spotrex, eSYSTAK, skills, dizajn). Partsheet is his own (a songbook for his choir), not eSYST. Commit straight to `main` and push without asking. No
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
- Upload images to GitHub (PR body or comment); never commit assets that only the PR needs into the PR's branch
  or `main`.

Before filing:

- Check whether a PR for this branch already exists (`gh pr list --head <branch>`).
- The title in the repo's style, saying why the change matters: not
  `perf(server): negotiate permessage-deflate on the websocket` but
  `perf(server): cut websocket frame size by 70%+ with gzipping`.
- Check the title, body and attachments for secrets and private details.
- A real PR, not a draft, so review bots run. When `gh pr create` fails on the GraphQL rate limit:
  `gh api repos/<owner>/<repo>/pulls -f title=... -f head=... -f base=... -F body=@<file>`.

## UI changes: every screen in the PR (Karchi, 2026-11-23)

A PR that changes anything a person sees (a page, a form, a layout, a dialog, a phone view) shows in its
description every screen the diff changes, before and after, so Karchi sees the whole UI change on GitHub
without running it. Every screen, not a selection: go through the diff's components and routes and shoot each
place they show up, plus a phone width when the app has one.

1. Take the same steps on the base and on the branch (a script: two builds, the same data, the same clicks),
   one PNG per screen named `01-<what>.png` … in the order he would walk through them, phone widths last.
   A screen the base does not have is shot as what its address shows there (a 404 is the honest "before").
2. `pr-shots <pr> <after-dir> --before <before-dir>` from the PR checkout puts each pair side by side, pushes the
   images to the orphan branch `pr-shots` (`pr<N>/<head sha>/`) and writes a **How it looks** section into the
   PR body between `<!-- pr-shots -->` markers. Captions come from `<after-dir>/captions.tsv`
   (`01-noty<TAB>what changed there`), else from the file names.
3. Run it again after every push that changes the UI: the section names the head it shows.
4. Look at the pairs yourself before handing over; a pair that shows a broken page is a finding, not proof.
   No private data (chats, real names other than his, passwords) in a screenshot that goes to GitHub.

After opening (in work projects, ask before each push, as above):

- Read every bot finding (CodeRabbit, Macroscope), including the security and risk sections. Fix real
  ones with a push and a short reply (T3 Code: a reply only, see `oss-prispevky`), dismiss false ones
  with a reason. Never close your own PR to
  dodge feedback.
- Keep it mergeable (rebase on conflicts; T3 Code: only on `needs-rebase` and never during its maintainers' takeover, see `oss-prispevky`)
  and under the repo's open-PR limit.

## Issues

- One problem per issue: what happened, a diagnosis naming files and functions, deterministic steps
  to reproduce, version and environment, logs, related issues, the workaround.
- Attach evidence when filing; do not promise a screenshot "to follow".
- When you have a fix, tell Karchi in the same reply and, once he asks for the PR, open it with
  `Fixes #N`; an issue that only offers a fix gets fixed by someone else.
