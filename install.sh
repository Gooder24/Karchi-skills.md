#!/usr/bin/env bash
# Installs or updates these skills on this machine: pulls the repo and links every skill folder
# into ~/.claude/skills (and ~/.codex/skills where Codex is installed, ~/.gemini/config/skills where Antigravity
# is). Safe to run again; the karchi-skills-update.timer runs it every 3 minutes, and the SessionStart hook in
# ~/.claude/settings.json at
# the start of every session (that hook is async: the session has already read the old AGENTS.md).
set -e
R="$HOME/.work/karchi-skills"
if [ -d "$R/.git" ]; then git -C "$R" pull -q --ff-only
else mkdir -p "$HOME/.work" && git clone -q https://github.com/Gooder24/Karchi-skills.md.git "$R"; fi
# A pull that changed this script: run the new version, not the rest of the old one bash already reads.
[ -z "${KS_FRESH:-}" ] && KS_FRESH=1 exec bash "$R/install.sh"
# Antigravity reads its skills from ~/.gemini/config/skills, also before agy has made ~/.gemini/config.
if [ -d "$HOME/.gemini/antigravity-cli" ]; then mkdir -p "$HOME/.gemini/config"; fi
# A skill deleted or moved in the repo leaves a dead link; it goes too.
for t in "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.gemini/config/skills"; do
  for l in "$t"/*; do
    [ -L "$l" ] && [ ! -e "$l/SKILL.md" ] && case "$(readlink "$l")" in "$R"/*) rm "$l" && echo "rm $l";; esac
  done
done
for d in "$R"/*/; do
  [ -f "$d/SKILL.md" ] || continue
  n=$(basename "$d")
  for t in "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.gemini/config/skills"; do
    [ -d "$(dirname "$t")" ] || continue
    mkdir -p "$t"
    if [ -e "$t/$n" ] && [ ! -L "$t/$n" ]; then echo "SKIP $t/$n: real folder exists"; continue; fi
    ln -sfn "${d%/}" "$t/$n"
    echo "ok $t/$n"
  done
done
# weft: Karchi's Weft inbox for agents, on every machine (runs on asus, elsewhere over ssh; see weft/SKILL.md).
mkdir -p "$HOME/.local/bin" && ln -sfn "$R/weft/weft" "$HOME/.local/bin/weft"
# ucenie: Karchi's learning app Učenie for agents (runs on asus, elsewhere over ssh; see ucenie/SKILL.md).
ln -sfn "$R/ucenie/ucenie" "$HOME/.local/bin/ucenie"
# citacka: what the Orca screen reader says on a page or in a terminal (runs on e540 when Orca is not here).
ln -sfn "$R/citacka/citacka" "$HOME/.local/bin/citacka"
# stroj: is x270/asus/dell/e540 up, and if not, why (agents run it before saying a machine is asleep).
ln -sfn "$R/stroj/stroj.mts" "$HOME/.local/bin/stroj"
# ship and land: commit+push+CI and merge-on-green in one call (see github/SKILL.md).
ln -sfn "$R/github/ship.mts" "$HOME/.local/bin/ship"
ln -sfn "$R/github/land.mts" "$HOME/.local/bin/land"
ln -sfn "$R/github/pr-shots.mts" "$HOME/.local/bin/pr-shots"
# One AGENTS.md for every agent: Claude Code reads it as ~/.claude/CLAUDE.md, Codex as ~/.codex/AGENTS.md,
# Antigravity as ~/.gemini/AGENTS.md.
# A real file there is kept once as <name>.bak-<date>, then replaced by the link.
for f in "$HOME/.claude/CLAUDE.md" "$HOME/.claude/AGENTS.md" "$HOME/.codex/AGENTS.md" "$HOME/.gemini/AGENTS.md"; do
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
# Compaction at 350k on every machine (Karchi, 2026-11-11). /autocompact or --autocompact can override
# per model/session.
compact_changed = s.get("autoCompactWindow") != 350000
s["autoCompactWindow"] = 350000
for k, v in {"anthropic-skills:morning": "off", "anthropic-skills:google-workspace": "off",
             "anthropic-skills:deep-research": "off", "deep-research": "off",
             "anthropic-skills:computer-use": "user-invocable-only",
             "anthropic-skills:chrome-browser": "user-invocable-only",
             "anthropic-skills:built-in-browser": "user-invocable-only",
             # Only when he types /name: the agent never needs them on its own.
             "code-review": "user-invocable-only",
             "simplify": "user-invocable-only", "run": "user-invocable-only",
             "workflow-authoring": "user-invocable-only", "loop": "user-invocable-only",
             "schedule": "user-invocable-only", "anthropic-skills:skill-creator": "user-invocable-only",
             "anthropic-skills:xlsx": "user-invocable-only",
             # Not used: they overlap his own skills or tools he does not have.
             "anthropic-skills:brand-partner": "off", "anthropic-skills:import-memory": "off",
             "fewer-permission-prompts": "off", "plugin-authoring": "off"}.items():
    o.setdefault(k, v)
# delegate_task was denied for an hour on 2026-11-18; Karchi wants side threads back (AGENTS.md says when).
deny = s.get("permissions", {}).get("deny", [])
deny_changed = "mcp__t3-code__delegate_task" in deny
if deny_changed: deny.remove("mcp__t3-code__delegate_task")
# The Cowork plugin from claude.ai: its skills ignore skillOverrides, so the whole plugin goes off.
e = s.setdefault("enabledPlugins", {}); new_plugin = "cowork-plugin-management@synced" not in e
e.setdefault("cowork-plugin-management@synced", False)
if len(o) != n or new_plugin or compact_changed or deny_changed:
    json.dump(s, open(p + ".tmp", "w"), indent=2, ensure_ascii=False); os.replace(p + ".tmp", p)
    print("ok Claude settings: auto-compact 350k, skillOverrides, delegate_task allowed")
PY
# Codex compacts at 350k too (T3's Codex accounts link their config.toml to this one).
if [ -d "$HOME/.codex" ]; then
  python3 -I - "$HOME/.codex/config.toml" <<'PY' || true
import os, re, sys
p = os.path.realpath(sys.argv[1]); line = "model_auto_compact_token_limit = 350000\n"
old = open(p).read() if os.path.exists(p) else ""
rest = [l for l in old.splitlines(True) if not re.match(r"model_auto_compact_token_limit\s*=", l)]
new = line + "".join(rest)
if new != old:
    open(p, "w").write(new)  # in place, so links to it stay
    print("ok Codex config: auto-compact 350k")
PY
fi
# Antigravity CLI (agy) asks before reading files outside the workspace, so a skill it picks would wait for a
# yes (and headless `agy -p` drops it). Reading the skills is always allowed.
if [ -d "$HOME/.gemini/antigravity-cli" ]; then
  python3 -I - "$HOME/.gemini/antigravity-cli/settings.json" "$HOME" <<'PY' || true
import json, os, sys
p, h = sys.argv[1], sys.argv[2]
s = json.load(open(p)) if os.path.exists(p) and os.path.getsize(p) else {}
allow = s.setdefault("permissions", {}).setdefault("allow", [])
need = [f"read_file({h}/.gemini/config/skills/)", f"read_file({h}/.work/karchi-skills/)"]
if any(r not in allow for r in need):
    allow += [r for r in need if r not in allow]
    json.dump(s, open(p + ".tmp", "w"), indent=2); os.replace(p + ".tmp", p)
    print("ok Antigravity settings: skills readable")
PY
fi
# Verification files (skill overenie) stay out of every repo, so they never show in T3's changed files or in a commit.
ign=$(git config --global --get core.excludesFile || true); ign=${ign/#\~/$HOME}
ign=${ign:-${XDG_CONFIG_HOME:-$HOME/.config}/git/ignore}
if ! grep -qx 'overenie/' "$ign" 2>/dev/null; then
  mkdir -p "$(dirname "$ign")"
  [ -s "$ign" ] && [ -n "$(tail -c1 "$ign")" ] && echo >> "$ign"
  echo 'overenie/' >> "$ign" && echo "ok $ign: overenie/"
fi
# self-update: a push reaches every machine within 3 minutes, before the next session starts.
if command -v systemctl >/dev/null && systemctl --user show-environment >/dev/null 2>&1; then
  mkdir -p "$HOME/.config/systemd/user"
  if ! cmp -s "$R/self-update/karchi-skills-update.service" "$HOME/.config/systemd/user/karchi-skills-update.service" ||
     ! cmp -s "$R/self-update/karchi-skills-update.timer" "$HOME/.config/systemd/user/karchi-skills-update.timer"; then
    cp "$R"/self-update/karchi-skills-update.{service,timer} "$HOME/.config/systemd/user/"
    systemctl --user daemon-reload
  fi
  systemctl --user is-enabled --quiet karchi-skills-update.timer 2>/dev/null ||
    { systemctl --user enable --now karchi-skills-update.timer && echo "ok karchi-skills-update.timer"; }
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
# t3-links: len na asuse každý deň obnoví T3 prepojenia medzi strojmi, kým nevypršia (30-dňové tokeny T3 neobnovuje).
if [ "$(uname -n)" = asus-vivobook-x1504v ] && command -v systemctl >/dev/null; then
  mkdir -p "$HOME/.local/bin" "$HOME/.config/systemd/user"
  ln -sfn "$R/t3-links/t3-links" "$HOME/.local/bin/t3-links"
  if ! cmp -s "$R/t3-links/t3-links.service" "$HOME/.config/systemd/user/t3-links.service" ||
     ! cmp -s "$R/t3-links/t3-links.timer" "$HOME/.config/systemd/user/t3-links.timer" ||
     ! systemctl --user is-enabled -q t3-links.timer 2>/dev/null; then
    cp "$R"/t3-links/t3-links.{service,timer} "$HOME/.config/systemd/user/"
    systemctl --user daemon-reload && systemctl --user enable --now t3-links.timer && echo "ok t3-links.timer"
  fi
fi
# vykaz: výkaz práce pre eSYST z T3 vlákien a okien Outlook/Teams; súbory a okná sú na x270, inde len príkaz cez ssh.
ln -sfn "$R/vykaz/vykaz" "$HOME/.local/bin/vykaz"
if [ "$(uname -n)" = karchi ] && command -v systemctl >/dev/null; then
  [ -x "$HOME/.local/share/vykaz/venv/bin/python" ] || python3 -m venv "$HOME/.local/share/vykaz/venv"
  "$HOME/.local/share/vykaz/venv/bin/python" -c 'import openpyxl' 2>/dev/null ||
    "$HOME/.local/share/vykaz/venv/bin/pip" -q install openpyxl || true
  mkdir -p "$HOME/.config/systemd/user"
  if ! cmp -s "$R/vykaz/vykaz.timer" "$HOME/.config/systemd/user/vykaz.timer" ||
     ! cmp -s "$R/vykaz/vykaz.service" "$HOME/.config/systemd/user/vykaz.service" ||
     ! cmp -s "$R/vykaz/vykaz-okna.service" "$HOME/.config/systemd/user/vykaz-okna.service" ||
     ! cmp -s "$R/vykaz/vykaz-poslat.timer" "$HOME/.config/systemd/user/vykaz-poslat.timer" ||
     ! cmp -s "$R/vykaz/vykaz-poslat.service" "$HOME/.config/systemd/user/vykaz-poslat.service" ||
     ! cmp -s "$R/vykaz/okna.py" "$HOME/.local/share/vykaz/okna.py.bezi"; then
    cp "$R"/vykaz/vykaz{.service,.timer,-okna.service,-poslat.service,-poslat.timer} "$HOME/.config/systemd/user/"
    systemctl --user daemon-reload
    systemctl --user enable --now vykaz.timer vykaz-poslat.timer && echo "ok vykaz.timer vykaz-poslat.timer"
    systemctl --user enable vykaz-okna.service && systemctl --user restart vykaz-okna.service &&
      cp "$R/vykaz/okna.py" "$HOME/.local/share/vykaz/okna.py.bezi" && echo "ok vykaz-okna.service"
  fi
fi
# Codex: the overenie-gate Stop hook in every Codex home, trusted (hooks/codex-hooks.mts). A login shell, because bun
# and codex live in mise or vite-plus paths that the timer's PATH lacks.
bash -lc 'command -v bun >/dev/null && command -v codex >/dev/null || exit 0; bun "$0"' "$R/hooks/codex-hooks.mts" ||
  echo "<4>codex-hooks failed: run bun $R/hooks/codex-hooks.mts" >&2
# codex-unlock: po zlyhanom Codex ťahu (limit) pustí konverzáciu, aby išla prepnúť na iný Codex účet.
if [ -d "$HOME/.t3/userdata" ] && command -v systemctl >/dev/null; then
  mkdir -p "$HOME/.local/bin" "$HOME/.config/systemd/user"
  ln -sfn "$R/codex-unlock/t3-codex-unlock" "$HOME/.local/bin/t3-codex-unlock"
  if ! cmp -s "$R/codex-unlock/t3-codex-unlock.service" "$HOME/.config/systemd/user/t3-codex-unlock.service"; then
    cp "$R/codex-unlock/t3-codex-unlock.service" "$HOME/.config/systemd/user/"
    systemctl --user daemon-reload && systemctl --user enable --now t3-codex-unlock.service && echo "ok t3-codex-unlock.service"
  fi
fi

# Anna PDF automation: Hermes owns the daytime job; these are its maintained skill and monitor.
if [ "$(uname -n)" = asus-vivobook-x1504v ]; then
  mkdir -p "$HOME/.hermes/scripts" "$HOME/.hermes/skills/productivity"
  cp "$R/anna-pdf/watch.py" "$HOME/.hermes/scripts/anna-pdf.py"
  # anna-pdf: download, render, checks and sending without a model; the job's model only translates.
  mkdir -p "$HOME/.local/bin" && ln -sfn "$R/anna-pdf/anna-pdf.mts" "$HOME/.local/bin/anna-pdf"
  ln -sfn "$R/anna-pdf" "$HOME/.hermes/skills/productivity/anna-pdf"
  # anna-pdf-watch: bez modelu, nezávisle od Hermes cronu; po 30 minútach bez doručenia napíše do Hermes miestnosti.
  if command -v systemctl >/dev/null; then
    mkdir -p "$HOME/.config/systemd/user"
    if ! cmp -s "$R/anna-pdf/anna-pdf-watch.service" "$HOME/.config/systemd/user/anna-pdf-watch.service" ||
       ! cmp -s "$R/anna-pdf/anna-pdf-watch.timer" "$HOME/.config/systemd/user/anna-pdf-watch.timer"; then
      cp "$R"/anna-pdf/anna-pdf-watch.{service,timer} "$HOME/.config/systemd/user/"
      systemctl --user daemon-reload
    fi
    systemctl --user is-enabled --quiet anna-pdf-watch.timer 2>/dev/null ||
      { systemctl --user enable --now anna-pdf-watch.timer && echo "ok anna-pdf-watch.timer"; }
  fi
fi
