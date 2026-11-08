#!/usr/bin/env bash
# Installs or updates these skills on this machine: pulls the repo and links every skill folder
# into ~/.claude/skills (and ~/.codex/skills where Codex is installed). Safe to run again; the
# SessionStart hook in ~/.claude/settings.json runs it at the start of every session.
set -e
R="$HOME/.work/karchi-skills"
if [ -d "$R/.git" ]; then git -C "$R" pull -q --ff-only
else mkdir -p "$HOME/.work" && git clone -q https://github.com/Gooder24/Karchi-skills.md.git "$R"; fi
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
