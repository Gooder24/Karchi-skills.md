# Karchi skills

Personal skills for Claude. Each folder is one skill (`SKILL.md` + its files).

| Skill | What it does |
|-------|---------|
| [`taste`](taste/taste.md) | Karchi's taste: look, controls, performance, information, way of working |
| [`github`](github/SKILL.md) | How to write commits, pull requests and comments on GitHub |

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

## Claude on the web (claude.ai) and in the desktop app

```sh
cd ~/.work/karchi-skills && python3 -m zipfile -c taste.zip taste/
```

Upload `taste.zip` in Settings → Capabilities → Skills. After every change to `taste.md` it has to be
zipped and uploaded again; the web app does not fetch the repository on its own.

Without skills, it is enough to paste the content of `taste/taste.md` into the project instructions or into your personal preferences.
