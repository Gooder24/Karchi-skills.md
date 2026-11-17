# Karchi skills

Personal skills for Claude. Each folder is one skill (`SKILL.md` + its files).

[`AGENTS.md`](AGENTS.md) holds Karchi's rules for every agent on every machine; `install.sh` links it as
`~/.claude/CLAUDE.md`, `~/.claude/AGENTS.md` and `~/.codex/AGENTS.md`.

## Requirements

- `bash`, `git` and `curl` for the install.
- Python 3 for the hooks, the tests and `check-docs.py`.
- Node.js 18 or later for the `avoid-ai-design` detector and its test.

## Quick start

On a machine with Claude Code or Codex:

```sh
curl -fsSL https://raw.githubusercontent.com/Gooder24/Karchi-skills.md/main/install.sh | bash
```

This links the skills into `~/.claude` and `~/.codex` and edits their settings files on the machine it runs on.
The [Claude Code](#claude-code) section says what it does.

## Skills

| Skill | What it does |
|-------|---------|
| [`taste`](taste/taste.md) | Karchi's taste: look, controls, performance, information, way of working |
| [`prezentacie`](prezentacie/SKILL.md) | Entry point for every presentation: outline, three style previews he picks from, checks before showing |
| [`frontend-slides`](frontend-slides/SKILL.md) | The look of his presentations: style presets, 34 bold templates, single-file HTML decks, PDF export |
| [`academic-pptx`](academic-pptx/SKILL.md) | The content of his presentations: narrative spine, action titles, one job per slide, sources |
| [`github`](github/SKILL.md) | How to write commits, pull requests and comments on GitHub |
| [`priority`](priority/SKILL.md) | Karchi's inbox on asus: only Hermes reads it, every chat only writes to it; moving threads to asus |
| [`zadanie`](zadanie/SKILL.md) | Turns a short ask into a goal file with checks the agent runs itself, so a task runs for an hour or a night without his feedback |
| [`overenie`](overenie/SKILL.md) | Verification he can trust: checks fixed before the work, run by a fresh verifier, with evidence and a log of misses |
| [`retro`](retro/SKILL.md) | Morning retro on asus: the settled thread with the most rounds, and the one prompt that would have done it, saved to `~/inbox/retro/` |
| [`ucenie`](ucenie/SKILL.md) | Karchi's learning app Učenie and the `ucenie` command: cards and packs, homework drafts, the learn harness, Anki import and export; points to the e540 thread that built it |
| [`weft`](weft/SKILL.md) | `weft` on every machine: Karchi's chats, search, drafts, sending and calendar in Weft on asus |
| [`frontend-design`](frontend-design/SKILL.md) | Anthropic's guide to distinctive UI: subject, type and colour decided before code |
| [`avoid-ai-design`](avoid-ai-design/SKILL.md) | Catalog of AI-design tells and `scripts/detect.mjs`, which finds them in code; `taste` runs it on every user interface (UI) before Karchi sees it |
| [`council`](council/SKILL.md) | Review by Opus 5.5, Sol 6.2 (high) and Kimi K3.1 Pro (OpenCode Go), on another machine when this one cannot run a member |
| `full-send`, `full-stop`, `sol-loop`, `file-pr`, `takeover`, `babysit-pr`, `modernize`, `leaving-pr-comments` | From [tstack](https://github.com/t3dotgg/tstack) (MIT, `LICENSE-tstack`), as published |

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

## Services

`install.sh` installs these as systemd user units on every machine that runs T3.

| Service | What it does |
|---------|---------|
| [`limit-fallback`](limit-fallback/t3-claude-fallback) | Every 10 min: at 3 % of the weekly Claude limit left, switches T3's default model to Codex Infowork, and back after the reset |
| [`codex-unlock`](codex-unlock/t3-codex-unlock) | Every 3 s: when a Codex turn fails (usually the usage limit), stops that account's idle app-server so the thread can switch to another Codex account without "open in another Codex client". `journalctl --user -u t3-codex-unlock` shows each stop; `t3-codex-unlock --dry-run` shows what it would stop |

## Third-party skills

`frontend-design` is `skills/frontend-design` from [anthropics/skills](https://github.com/anthropics/skills)
(commit ca45fc4, 2026-10-28, Apache-2.0, `LICENSE.txt` kept). `avoid-ai-design` is
[funboy322/avoid-ai-design](https://github.com/funboy322/avoid-ai-design) without its README, docs and
examples (commit 2b7c718, v0.4.0, MIT, `LICENSE` kept). `frontend-slides` is
[zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides) without its README, `.gitignore`,
`.claude-plugin`, `plugins` copy, `bold-template-pack/README.md` and `scripts/deploy.sh` (commit 9906a34,
2026-06-23, MIT, `LICENSE` kept); `scripts/export-pdf.sh` is changed: its server listens only on
127.0.0.1 and serves only the deck's folder, it uses `/usr/bin/chromium` when there is one instead of
downloading a browser, and it no longer opens the PDF. `academic-pptx` is [Gabberflast/academic-pptx-skill](https://github.com/Gabberflast/academic-pptx-skill)
without its README and PDF (commit 9f2b703, 2026-07-14, MIT, `LICENSE` kept; the `license` line of its
frontmatter said Proprietary and is corrected). In both, the `description` starts with a pointer to
`prezentacie` and a note under the title says what `prezentacie` overrides. To update one, copy the same files from upstream
again. The detector needs Node 18+ (asus, dell and x270 have it; e540 does not).

## One-off skills

Playbooks that were used once and worked. `install.sh` does not link them, so they do not load into every
session. When the situation comes back, link the one you need:

```sh
ln -s ~/.work/karchi-skills/one-off/ntfs-dirty-flag ~/.claude/skills/
```

| Skill | Used for |
|-------|---------|
| [`ntfs-dirty-flag`](one-off/ntfs-dirty-flag/SKILL.md) | External NTFS (Windows file system) disk that Linux mounts only read-only: check the hardware, back up the metadata, rehearse `ntfsfix` on a copy, repair, verify (2026-10) |

## Claude Code

The [quick start](#quick-start) command clones the repo to `~/.work/karchi-skills` and links every skill into
`~/.claude/skills` (and `~/.codex/skills` if Codex is installed). Installed on x270, asus, dell, e540 and the
VPS (virtual private server), where a `SessionStart` hook in `~/.claude/settings.json` runs `install.sh` again
at the start of every session,
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

## Testing

Run these from the repository root:

```sh
node --test avoid-ai-design/scripts/detect.test.mjs
python3 anna-pdf/test_watch.py
python3 .github/scripts/check-docs.py
```

`anna-pdf/test_watch.py` runs its checks when the file is executed and ends with one `PASS:` line; `pytest` finds no tests in it.

## Accessibility

[ACCESSIBILITY.md](ACCESSIBILITY.md) says what the repository checks, how to report a barrier, and what has not been tested yet. The Markdown check runs on every pull request, see [the workflow](.github/workflows/accessibility.yml).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

No license has been chosen yet. Without one, the default copyright rules apply, so reuse needs the owner's permission. The third-party skills keep their own licenses, see [Third-party skills](#third-party-skills).
