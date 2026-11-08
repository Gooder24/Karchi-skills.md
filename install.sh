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
