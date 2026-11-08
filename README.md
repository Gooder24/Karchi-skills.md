# Karchi skills

Personal skills for Claude. Each folder is one skill (`SKILL.md` + its files).

| Skill | What it does |
|-------|---------|
| [`taste`](taste/taste.md) | Karchi's taste: look, controls, performance, information, way of working |
| [`prezentacie`](prezentacie/SKILL.md) | School PowerPoints with real images and a reusable GitHub Primer adaptation |
| [`github`](github/SKILL.md) | How to write commits, pull requests and comments on GitHub |
| [`priority`](priority/SKILL.md) | Karchi's inbox on asus: only Hermes reads it, every chat only writes to it; moving threads to asus |
| [`zadanie`](zadanie/SKILL.md) | Turns a short ask into a goal file with checks the agent runs itself, so a task runs for an hour or a night without his feedback |
| [`overenie`](overenie/SKILL.md) | Verification he can trust: checks fixed before the work, run by a fresh verifier, with evidence and a log of misses |
| [`retro`](retro/SKILL.md) | Morning retro on asus: the settled thread with the most rounds, and the one prompt that would have done it, saved to `~/inbox/retro/` |
| [`priority/review.md`](priority/review.md) | Nightly inbox review: closes done items and adds unfinished work from every machine's T3 threads (`thread-digest.py`) |
| [`priority/worker.md`](priority/worker.md) | The night worker: a scheduled T3 task on asus proposes one inbox item per night as a branch or patch |
| [`frontend-design`](frontend-design/SKILL.md) | Anthropic's guide to distinctive UI: subject, type and colour decided before code |
| [`avoid-ai-design`](avoid-ai-design/SKILL.md) | Catalog of AI-design tells and `scripts/detect.mjs`, which finds them in code; `taste` runs it on every UI before Karchi sees it |

## Hooks

Scripts in `hooks/` are not skills; `install.sh` does not wire them. Each is wired by hand into
`~/.claude/settings.json` on the machines named below.

| Hook | What it does |
|------|---------|
| [`background-wait.py`](hooks/background-wait.py) | asus only. `PostToolUse` on `Bash\|Monitor`: in a T3 thread, each background task reminds the agent to call `t3_background_wait`, so the thread stays in Working instead of showing Done ([pingdotgg/t3code#25585](https://github.com/pingdotgg/t3code/issues/25585)) |
| [`overenie-gate.py`](hooks/overenie-gate.py) | asus, x270, dell, e540. `Stop`: a turn that changed something must end with an `Overenie:` line (a fresh evidence file under `overenie/`, or neoverené, netreba, prebieha); otherwise it is sent back once. Decisions go to `~/.claude/overenie-gate.jsonl`; `overenie/audit.py` reports them with Karchi's complaints per week |

Wiring:

```json
"PostToolUse": [{ "matcher": "Bash|Monitor", "hooks": [{ "type": "command",
  "command": "python3 -I ~/.work/karchi-skills/hooks/background-wait.py", "timeout": 5 }] }],
"Stop": [{ "hooks": [{ "type": "command",
  "command": "python3 -I ~/.work/karchi-skills/hooks/overenie-gate.py", "timeout": 10 }] }]
```

## Third-party skills

`frontend-design` is `skills/frontend-design` from [anthropics/skills](https://github.com/anthropics/skills)
(commit ca45fc4, 2026-10-28, Apache-2.0, `LICENSE.txt` kept). `avoid-ai-design` is
[funboy322/avoid-ai-design](https://github.com/funboy322/avoid-ai-design) without its README, docs and
examples (commit 2b7c718, v0.4.0, MIT, `LICENSE` kept). To update one, copy the same files from upstream
again. The detector needs Node 18+ (asus, dell and x270 have it; e540 does not).

## One-off skills

Playbooks that were used once and worked. `install.sh` does not link them, so they do not load into every
session. When the situation comes back, link the one you need:

```sh
ln -s ~/.work/karchi-skills/one-off/ntfs-dirty-flag ~/.claude/skills/
```

| Skill | Used for |
|-------|---------|
| [`ntfs-dirty-flag`](one-off/ntfs-dirty-flag/SKILL.md) | External NTFS disk that Linux mounts only read-only: check the hardware, back up the metadata, rehearse `ntfsfix` on a copy, repair, verify (2026-10) |

## Claude Code

```sh
curl -fsSL https://raw.githubusercontent.com/Gooder24/Karchi-skills.md/main/install.sh | bash
```

It clones the repo to `~/.work/karchi-skills` and links every skill into `~/.claude/skills` (and
`~/.codex/skills` if Codex is installed). Installed on x270, asus, dell, e540 and the VPS, where a
`SessionStart` hook in `~/.claude/settings.json` runs `install.sh` again at the start of every session,
so a pushed change reaches every machine in its next session. It also puts `overenie/` in the global
gitignore, so verification files never show in T3's changed files or in a commit:

```json
"SessionStart": [{ "hooks": [{ "type": "command", "async": true, "timeout": 30,
  "command": "GIT_TERMINAL_PROMPT=0 timeout 20 bash ~/.work/karchi-skills/install.sh >/dev/null 2>&1 || true" }] }]
```

## Claude on the web (claude.ai) and in the desktop app

```sh
cd ~/.work/karchi-skills && python3 -m zipfile -c taste.zip taste/
```

Upload `taste.zip` in Settings → Capabilities → Skills. After every change to `taste.md` it has to be
zipped and uploaded again; the web app does not fetch the repository on its own.

Without skills, it is enough to paste the content of `taste/taste.md` into the project instructions or into your personal preferences.
