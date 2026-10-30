# Karchi skills

Personal skills for Claude. Each folder is one skill (`SKILL.md` + its files).

| Skill | What it does |
|-------|---------|
| [`taste`](taste/taste.md) | Karchi's taste: look, controls, performance, information, way of working |
| [`github`](github/SKILL.md) | How to write commits, pull requests and comments on GitHub |
| [`priority`](priority/SKILL.md) | Karchi's inbox on asus and the priority check at the start of every thread |
| [`priority/worker.md`](priority/worker.md) | The night worker: a scheduled T3 task takes one inbox item per night |
| [`frontend-design`](frontend-design/SKILL.md) | Anthropic's guide to distinctive UI: subject, type and colour decided before code |
| [`avoid-ai-design`](avoid-ai-design/SKILL.md) | Catalog of AI-design tells and `scripts/detect.mjs`, which finds them in code; `taste` runs it on every UI before Karchi sees it |

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
so a pushed change reaches every machine in its next session:

```json
"SessionStart": [{ "hooks": [{ "type": "command", "async": true, "timeout": 30,
  "command": "GIT_TERMINAL_PROMPT=0 timeout 20 bash ~/.work/karchi-skills/install.sh >/dev/null 2>&1 || true" }] }]
```

The `priority` skill needs a second `SessionStart` hook next to it, which prints the open inbox items
into the session's context:

```json
{ "hooks": [{ "type": "command", "timeout": 10,
  "command": "bash ~/.work/karchi-skills/priority/inbox-context.sh" }] }
```

## Claude on the web (claude.ai) and in the desktop app

```sh
cd ~/.work/karchi-skills && python3 -m zipfile -c taste.zip taste/
```

Upload `taste.zip` in Settings → Capabilities → Skills. After every change to `taste.md` it has to be
zipped and uploaded again; the web app does not fetch the repository on its own.

Without skills, it is enough to paste the content of `taste/taste.md` into the project instructions or into your personal preferences.
