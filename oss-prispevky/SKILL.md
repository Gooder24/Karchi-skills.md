---
name: oss-prispevky
description: How Karchi contributes to other people's open-source projects so maintainers see a careful developer and not AI slop - picking the project, its contribution and AI rules, reproducing the bug in a desktop VM, the fix, tests and measurements, a PR with evidence and a merge chance, following the replies, and a Slovak explanation he can defend. Use when he wants to contribute to an open-source project he does not own, choose one or an issue, prepare or file a PR or issue there, or when a maintainer replies to one. His own repos follow `github` alone.
---

# Open-source contributions

Karchi contributes upstream to build a name: remote work or contracts, GitHub Sponsors, people who follow his
work. One sloppy PR costs more than ten good ones earn, because maintainers remember names and some keep public
lists (Ghostty denounces "bad AI drivers"). Everything here serves one test: **a maintainer reading the PR thinks
"this person checked it and understands it"**.

The `github` skill still applies to every commit, PR body and reply. This skill adds what comes before and around
it. Built from the Atlas port (`neondeex/atlas-filemanager`, 2026-11-15 to 18; thread „Dokončiť funkčný Arch fork
správcu súborov“ on asus, its folder `~/.t3/scratch/2026-11-15-https-github-com-martasskv5-atlas-a9115650/`).

## Rules that never bend

1. **Karchi decides every outward step.** Choosing the project and the issue, each issue, comment and PR: only after
   he says so in the thread. Research and local work need no permission. Until he decides, the choice goes to his
   inbox (skill `priority`) as a decision.
2. **One problem per PR, with proof.** A repro, a test that fails on `main` and passes on the branch, a real run
   (screenshots or video for UI, numbers for performance). "Tests pass" is not proof.
3. **Issue or discussion first**, unless the project's CONTRIBUTING invites PRs for obvious bugs and the bug is one,
   or the PR fixes red CI on the default branch. Features always start as an issue or discussion (Zed: "If there isn't
   a GitHub issue with staff confirmation that we want it, start a discussion"). Our own tooling (a VM test harness,
   performance numbers, packaging for another distro) stays in the fork unless a maintainer asks for it: merged, it is
   code he has to keep working (Atlas #24 Nix flake, #31 harness of 1 644 lines).
4. **No batches.** At most three open PRs in a new project until the first one merges, and only in a project that
   regularly merges outside PRs; otherwise one. Each is a small, independent bug fix with its own issue (or a failure
   anyone can see, such as red CI on the default branch) and its own evidence, so any one can be merged or closed
   alone; never a stack of features or cleanups. Never above the project's limit (Zed: three). Atlas lesson: five PRs
   in two days to a project that had never merged an outside PR, zero replies after two days, and the owner's habit is
   to reimplement outside fixes himself (#4, #11). Two of Karchi's open PRs never change the same file; when one fix
   needs another, it waits until that one is merged (Atlas #35 clashed with #23 and #27 in `ops.rs` and was held back).
   Count before every new one: `gh pr list -R owner/repo --author Gooder24 --state open`.
5. **Disclose AI the way the project asks, and at the top.** Name the tools (Claude Code, Codex) and the extent. A
   project that bans AI-generated content is skipped entirely, not worked around (list below).
6. **Karchi understands every line and speaks for himself.** Before a PR goes out he has read its `obhajoba` (below)
   and can answer the likely questions without an agent. Replies to maintainers are his own words. When he writes in
   Slovak and translates with AI, the projects that ask for it (Zed) get the translation in a quote block with his
   original below. The agent drafts explanations for him, never the reply he posts as his own.
7. **No autonomous agent opens anything.** Zed closes PRs that look agent-driven; Flathub forbids AI-opened
   submissions; Warp forbids agents talking to the team. The agent prepares, Karchi approves, then the PR is filed.

## The steps

Keep everything for one project in the thread's working folder: `progress.md` (state, decisions, what runs),
`results/`, `pr-drafts/`, `overenie/`. A later thread finds it there.

### 1. Pick the project and the issue

Measure; do not trust a project's reputation.

```sh
T=~/.work/karchi-skills/oss-prispevky/tools
python3 $T/prstats.py owner/repo 2026-08-01 2026-11-04 --new   # outside PRs: merged, closed, open, hours to first reply
$T/issues.sh owner/repo 'label:"platform:linux" wayland' 10      # open issues by reactions
gh pr list -R owner/repo --state all --limit 30                  # does the owner merge outsiders or redo their work?
```

Score each candidate 0-5 on fit with what Karchi has already shown (GPUI, Wayland clipboard, file managers, FUSE,
packaging, desktop VM testing and measurement), the newcomers' merge rate and reply time, career value (a company
that hires remotely, Sponsors, a visible community), and an open gap nobody has claimed. Before proposing an issue,
check its cross-referenced PRs (Zed #65132 and #65270 already had outside PRs when checked on 18. 11.). A good
first contribution is often not a PR: reproduce an open bug in a VM and report what you saw, or test an open PR on a
desktop its author could not try, with numbers.

### 2. Read the rules and the AI policy

```sh
$T/fetchpolicy.sh owner/repo ./policy/owner_repo && rg --hidden -in 'LLM|\bAI\b|generat|copilot|agent' ./policy/owner_repo
```

Read CONTRIBUTING, AI_POLICY, AGENTS.md, the PR template, the CLA and the code of conduct whole, then write the
project's rules in `progress.md`. Follow every guide they link, also one in another repo of the org (COSMIC's PR
template links the ban in `pop-os/pop`). Known as of 2026-11-18 (recheck before each project, policies change):

| Project | AI rule |
|---|---|
| Alacritty, Servo, niri | **Banned** (LLM content in code, docs, issues, comments). Skip. |
| Pop!_OS and COSMIC (all `pop-os` repos, also its smithay-clipboard and libcosmic forks) | **Banned** in issues and PRs, "including code, comments, and descriptions" (pop-os/pop CONTRIBUTING, since 2026-09-30); the PR template makes you tick "I have not included any LLM generated content". Skip. |
| Flathub | Manifests must not contain AI-generated or AI-assisted content; AI in the app must be disclosed; no AI-opened PRs or replies. Flathub packaging is not for this workflow. |
| Ghostty (Zig) | Disclose every use and its extent; a maintainer must vouch for a first-time contributor before PRs; bad AI contributions go on a public denounce list. |
| Smithay (and Smithay/smithay-clipboard) | `AI.md`: allowed but "strongly advise against"; AI code marked in the commit messages; no AI-written issues, comments or PR descriptions (a translation tool is fine). |
| Tauri | `.github/CONTRIBUTING.md` "AI Tool Policy": review and test all LLM content yourself; no AI replies to review comments except translations; else closed as `ai-slop`. |
| Zed | LLM coding welcome with a human who understands it; no autonomous agents; replies and PR text in your own words; three open PRs at most; CLA. |
| Linebender (Xilem, Vello) | Disclose ahead of time in the PR description, also plans an LLM proposed; never write "no AI was used". |
| Rerun, egui | You own the quality; Rerun asks you to state your confidence; egui closes "LLM slop" and massive PRs. |
| Warp | Any coding agent may write code; talk to the team as a human; every PR starts from an issue with a `ready-to-implement` label. |
| This Week in Rust | Articles must be written by humans; no LLM-written articles. |

### 3. Reproduce the bug in a desktop VM

Never on Karchi's live screen. The harness in `desktop-vm/` (from Atlas) boots QEMU/KVM VMs with a real Wayland
desktop that nobody watches, driven by ssh and QMP input:

```sh
D=~/.work/karchi-skills/oss-prispevky/desktop-vm
export DVM_NAME=<project>                  # VMs go to ~/vm/<project>-<distro>
$D/dvm.sh fedora up && $D/dvm.sh fedora provision gnome ./app.rpm
$D/dvm.sh debian up && $D/dvm.sh debian provision sway ./app.deb   # 2 GB, no XWayland
$D/dvm.sh fedora qmp key ctrl-c; $D/dvm.sh fedora qmp click 400 300 right; $D/dvm.sh fedora qmp shot before.png
$D/dvm.sh fedora down
```

Only Debian `up`/`ssh`/`qmp shot`/`down` was rerun after the move into this skill (18. 11.); the GNOME and sway
provisioning ran on Atlas with user `atlas`; Arch GNOME provisioning is new and untested. NixOS needs an image built
first (Atlas: `nixos-image.sh` in the Atlas folder). Before `up`: `free -h` and `uptime`, at most two VMs on asus and
none while it compiles. Write the steps that trigger the bug as a script (`gui-test.sh` in the Atlas folder is the
model: input through QMP, results checked on the guest's disk over ssh), so the same script proves the fix later.
Save the before screenshot or log.

Software rendering in VMs (llvmpipe, lavapipe) caps frame rates and hides GPU bugs: say so next to every number,
and measure GPU-dependent bugs on real hardware.

### 4. Fix

The smallest complete fix, in the project's style, on a branch in Karchi's fork. Read `github` ("Pull requests that
merge on the first review"). Check what reviewers will ask: other desktops (GNOME has no data-control protocol;
sway and KDE do), X11 and XWayland, older compositor versions, Windows and macOS when the code is shared.

### 5. Tests and measurements

- A test in the module's existing test file that fails on `main` and passes on the branch; the project's own
  formatter, linter and test commands on the changed crates.
- Rerun the VM repro script: after screenshot or log next to the before.
- Performance: the numbers that matter to a user, p50 and p95 over repeated runs, before and after on the same
  machine. Atlas tools: `wdlog.py` reads timings from a client's `WAYLAND_DEBUG=1` log (first frame, key-to-frame,
  frames during scroll), `perf.sh` and `frames.sh` in the Atlas folder drive them. Name the machine, the renderer
  and what you could not measure.

### 6. Review before anyone else sees it

Once for every change: `overenie/verify.sh` (skill `overenie`, one round for another project's repo). For anything
beyond a small fix (shared code, data, concurrency): one council round (skill `council`) before filing. Fix what
they find; scores go in the PR body only if the project would want them (usually not).

### 7. The PR draft, the merge chance and the obhajoba

Write `pr-drafts/<branch>.md` in the project's template (`github` headings otherwise), English, short, the AI
disclosure in the place the project asks for, else as the first line:
`I used Claude Code to write this change and its tests; I reviewed every line and tested it as described below.`
Write it with Karchi's wording in mind: he must be able to say all of it himself.

Give Karchi a **merge chance in percent** with one sentence of reasons: the project's measured newcomer merge rate,
whether a maintainer confirmed the issue, the size of the diff, competing PRs.

Write `pr-drafts/<branch>-obhajoba.md` in Slovak, at most a page:

- **Problém**: what the user sees, before and after, on which desktop.
- **Príčina**: the function and the line, in two sentences.
- **Oprava**: each changed hunk in one or two sentences: what it does and why it is needed.
- **Prečo nie inak**: the obvious alternative and why it was rejected.
- **Otázky, ktoré prídu**: three to five likely reviewer questions, each with the answer and where in the code it is.
- **Čo nie je otestované** and what he would answer if asked.

He reads it before saying „podaj“. The PR is filed (`gh pr create` with the approved body, from his fork) only then and never merged by us (full stop: the maintainers merge),
and its link goes into the thread.

### 8. Follow the replies

Add the PR to Hermes' watch list (`owner/repo#N` in `~/.hermes/pr-babysit.list` on asus) without a checkout path.
When Karchi says babysit, add the asus checkout on the PR's branch as the path, but only after the PR as filed passed
its check (its GitHub head SHA is the one the gates and `verify.sh` ran on). With a path, Hermes pushes fixes for CI,
conflicts and real bot findings to his fork, and in repos not owned by Gooder24 never writes to people there (rule in
its job prompt since 2026-11-18): questions and reviews reach him as inbox notes. For every human review or question: a Slovak note for
Karchi with what they ask, whether they are right, the fix if one is needed (pushed only after he agrees), and the
points his reply should make. He writes and posts the reply. Bot findings (CI, CodeRabbit) are fixed the way
`github` says. When a PR is closed unmerged, write down why in `progress.md` and in this skill's lessons if it
teaches something.

When a release ships his code, watch the project's new issues for two weeks (`gh issue list -R owner/repo --search
"created:>=<release date>"`) and give Karchi any that touch his changes first, with the fix ready: a regression fixed
the same week is what makes a maintainer trust a large contribution he merged without reading every line.

## Lessons (append one line each with date and evidence)

- 2026-11-18 arboard INCR (X11 clipboard): three council rounds found three real races the builder's tests missed (two
  transfers to one window, a reused property, a late Delete). An unforced race test passes or fails by chance: one run
  on the fixed commit failed in the other, unfixable order and looked like the fix had failed. Force the order (here
  GrabServer) and run it 20 times on the old and the new commit (20/20 vs 0/20).
- 2026-11-18 Atlas: the owner had never merged an outside PR and reimplemented them (#4, #11). Measure that in
  step 1 before investing days; five PRs (#23 to #27) waited with no reply.
- 2026-11-17 Atlas #23: three council rounds before filing caught real problems; worth it for code that every
  desktop runs.
- 2026-11-17 Atlas: Fedora GNOME showed that the Wayland clipboard fix (#23, data-control) does not work on GNOME;
  without the GNOME VM it would have shipped as "fixes the clipboard". Test every desktop family you claim.
- 2026-11-17 Debian #1144467 (see `github`): disclose AI at the top and keep it short; a 150-line reply got told off.
- 2026-11-18 COSMIC Files #2136: the research called COSMIC "no written AI rules" although its PR template, already
  fetched into `data/policy/`, bans LLM content; caught only after the root-cause work. Read the template whole
  in step 2 before scoring a project. Same day: Smithay's `AI.md` and Tauri's policy were missed too, because `rg`
  skips the hidden `.github_*` files `fetchpolicy.sh` saves (now `rg --hidden`, and it fetches `AI.md` and the org's
  `.github` defaults).
- 2026-11-22 Atlas outcome: the owner did take outside work after all. 13 of the 14 PRs (#23 to #36, about 6 700 lines,
  nine of them filed on 18. 11. after this skill's limit of three existed) went into 0.1.6-beta.4 "as-is" (8e05818a,
  changelog thanks Gooder24), nine merged within 47 minutes, so most of it was trusted, not read; #35 held back for
  clashing with #23 and #27. Only #23 had an issue. A written limit did not stop the batch: count open PRs before
  each one (rule 4), and treat the merged features (#24, #29, #30, #31, #36) as code to answer for in step 8.
