#!/usr/bin/env bash
# Installs or updates these skills on this machine: pulls the repo and links every skill folder
# into ~/.claude/skills (and ~/.codex/skills where Codex is installed). Safe to run again; the
# SessionStart hook in ~/.claude/settings.json runs it at the start of every session.
set -e
R="$HOME/.work/karchi-skills"
if [ -d "$R/.git" ]; then git -C "$R" pull -q --ff-only
else mkdir -p "$HOME/.work" && git clone -q https://github.com/Gooder24/Karchi-skills.md.git "$R"; fi
# A pull that changed this script: run the new version, not the rest of the old one bash already reads.
[ -z "${KS_FRESH:-}" ] && KS_FRESH=1 exec bash "$R/install.sh"
for d in "$R"/*/; do
  [ -f "$d/SKILL.md" ] || continue
  n=$(basename "$d")
  for t in "$HOME/.claude/skills" "$HOME/.codex/skills"; do
    [ -d "$(dirname "$t")" ] || continue
    mkdir -p "$t"
    if [ -e "$t/$n" ] && [ ! -L "$t/$n" ]; then echo "SKIP $t/$n: real folder exists"; continue; fi
    ln -sfn "${d%/}" "$t/$n"
    echo "ok $t/$n"
  done
done
# weft: Karchi's Weft inbox for agents, on every machine (runs on asus, elsewhere over ssh; see weft/SKILL.md).
mkdir -p "$HOME/.local/bin" && ln -sfn "$R/weft/weft" "$HOME/.local/bin/weft"
# One AGENTS.md for every agent: Claude Code reads it as ~/.claude/CLAUDE.md, Codex as ~/.codex/AGENTS.md.
# A real file there is kept once as <name>.bak-<date>, then replaced by the link.
for f in "$HOME/.claude/CLAUDE.md" "$HOME/.claude/AGENTS.md" "$HOME/.codex/AGENTS.md"; do
  [ -d "$(dirname "$f")" ] || continue
  [ "$(readlink "$f")" = "$R/AGENTS.md" ] && continue
  [ -e "$f" ] && [ ! -L "$f" ] && mv "$f" "$f.bak-$(date +%F)"
  ln -sfn "$R/AGENTS.md" "$f" && echo "ok $f -> AGENTS.md"
done
# Claude defaults and skills from claude.ai that Karchi does not want listed (2026-11-09).
# Skill overrides only fill missing keys, so a later change in /skills stays.
python3 -I - "$HOME/.claude/settings.json" <<'PY' || true
import json, os, sys
p = sys.argv[1]
if not os.path.exists(p): sys.exit()
s = json.load(open(p)); o = s.setdefault("skillOverrides", {}); n = len(o)
# Earlier compaction reduces growing history. /autocompact or --autocompact can override per model/session.
compact_changed = s.get("autoCompactWindow") != 200000
s["autoCompactWindow"] = 200000
for k, v in {"anthropic-skills:morning": "off", "anthropic-skills:google-workspace": "off",
             "anthropic-skills:deep-research": "off", "deep-research": "off",
             "anthropic-skills:computer-use": "user-invocable-only",
             "anthropic-skills:chrome-browser": "user-invocable-only",
             "anthropic-skills:built-in-browser": "user-invocable-only",
             # Only when he types /name: the agent never needs them on its own.
             "retro": "user-invocable-only", "code-review": "user-invocable-only",
             "simplify": "user-invocable-only", "run": "user-invocable-only",
             "workflow-authoring": "user-invocable-only", "loop": "user-invocable-only",
             "schedule": "user-invocable-only", "anthropic-skills:skill-creator": "user-invocable-only",
             "anthropic-skills:xlsx": "user-invocable-only",
             # Not used: they overlap his own skills or tools he does not have.
             "anthropic-skills:brand-partner": "off", "anthropic-skills:import-memory": "off",
             "fewer-permission-prompts": "off", "plugin-authoring": "off"}.items():
    o.setdefault(k, v)
# The Cowork plugin from claude.ai: its skills ignore skillOverrides, so the whole plugin goes off.
e = s.setdefault("enabledPlugins", {}); new_plugin = "cowork-plugin-management@synced" not in e
e.setdefault("cowork-plugin-management@synced", False)
if len(o) != n or new_plugin or compact_changed:
    json.dump(s, open(p + ".tmp", "w"), indent=2, ensure_ascii=False); os.replace(p + ".tmp", p)
    print("ok Claude settings: auto-compact 200k, skillOverrides")
PY
# Verification files (skill overenie) stay out of every repo, so they never show in T3's changed files or in a commit.
ign=$(git config --global --get core.excludesFile || true); ign=${ign/#\~/$HOME}
ign=${ign:-${XDG_CONFIG_HOME:-$HOME/.config}/git/ignore}
if ! grep -qx 'overenie/' "$ign" 2>/dev/null; then
  mkdir -p "$(dirname "$ign")"
  [ -s "$ign" ] && [ -n "$(tail -c1 "$ign")" ] && echo >> "$ign"
  echo 'overenie/' >> "$ign" && echo "ok $ign: overenie/"
fi
# limit-fallback: pri 3 % zvyšku týždenného Claude limitu prepne T3 default na Codex, po resete späť.
if [ -d "$HOME/.t3/userdata" ] && command -v systemctl >/dev/null; then
  mkdir -p "$HOME/.local/bin" "$HOME/.config/systemd/user"
  ln -sfn "$R/limit-fallback/t3-claude-fallback" "$HOME/.local/bin/t3-claude-fallback"
  if ! cmp -s "$R/limit-fallback/t3-claude-fallback.timer" "$HOME/.config/systemd/user/t3-claude-fallback.timer"; then
    cp "$R"/limit-fallback/t3-claude-fallback.{service,timer} "$HOME/.config/systemd/user/"
    systemctl --user daemon-reload && systemctl --user enable --now t3-claude-fallback.timer && echo "ok t3-claude-fallback.timer"
  fi
fi
# limit-ping: len na asuse drží 5-hodinové okná Claude a Codex účtov za sebou v plánovaných časoch.
if [ "$(uname -n)" = asus-vivobook-x1504v ] && command -v systemctl >/dev/null; then
  mkdir -p "$HOME/.local/bin" "$HOME/.config/systemd/user"
  ln -sfn "$R/limit-ping/limit-ping" "$HOME/.local/bin/limit-ping"
  if ! cmp -s "$R/limit-ping/limit-ping.service" "$HOME/.config/systemd/user/limit-ping.service" ||
     ! cmp -s "$R/limit-ping/limit-ping.timer" "$HOME/.config/systemd/user/limit-ping.timer"; then
    cp "$R"/limit-ping/limit-ping.{service,timer} "$HOME/.config/systemd/user/"
    systemctl --user daemon-reload && systemctl --user enable --now limit-ping.timer && echo "ok limit-ping.timer"
  fi
fi
# codex-unlock: po zlyhanom Codex ťahu (limit) pustí konverzáciu, aby išla prepnúť na iný Codex účet.
if [ -d "$HOME/.t3/userdata" ] && command -v systemctl >/dev/null; then
  mkdir -p "$HOME/.local/bin" "$HOME/.config/systemd/user"
  ln -sfn "$R/codex-unlock/t3-codex-unlock" "$HOME/.local/bin/t3-codex-unlock"
  if ! cmp -s "$R/codex-unlock/t3-codex-unlock.service" "$HOME/.config/systemd/user/t3-codex-unlock.service"; then
    cp "$R/codex-unlock/t3-codex-unlock.service" "$HOME/.config/systemd/user/"
    systemctl --user daemon-reload && systemctl --user enable --now t3-codex-unlock.service && echo "ok t3-codex-unlock.service"
  fi
fi
