# Karchi skills

Personal skills for Claude. Each folder is one skill (`SKILL.md` + its files).

| Skill | What it does |
|-------|---------|
| [`taste`](taste/taste.md) | Karchi's taste: look, controls, performance, information, way of working |

## Claude Code

```sh
git clone https://github.com/Gooder24/Karchi-skills.md ~/.work/karchi-skills
ln -s ~/.work/karchi-skills/taste ~/.claude/skills/taste
```

## Claude on the web (claude.ai) and in the desktop app

```sh
cd ~/.work/karchi-skills && python3 -m zipfile -c taste.zip taste/
```

Upload `taste.zip` in Settings → Capabilities → Skills. After every change to `taste.md` it has to be
zipped and uploaded again; the web app does not fetch the repository on its own.

Without skills, it is enough to paste the content of `taste/taste.md` into the project instructions or into your personal preferences.
