#!/usr/bin/env bash
# Usage: verify.sh <brief.md> [verdict, default overenie/verdikt.md]    (run it in the project root)
# The independent verifier of skill overenie. Codex goes first: it spends the ChatGPT limit, not Karchi's Claude
# limit, and in the 9. 11. pilot it found as much as Opus in half the time. When Codex leaves no verdict (its limit,
# a crash, not installed), Claude Opus runs. OVERENIE_CLAUDE_FIRST=1 swaps the order: use it only for
# `Hĺbka: dôkladná` on a change Codex built, so a different model checks it. How deep it goes is in the brief (verifier-agents.md).
# Every run logs its usage to ~/.claude/overenie-usage.jsonl. Exits 1 when no verdict was written.
set -u
brief=$1 verdict=${2:-overenie/verdikt.md}
[ -s "$brief" ] || { echo "verify.sh: brief $brief neexistuje" >&2; exit 2; }
D=$(dirname "$(readlink -f "$0")"); V=$D/verifier-agents.md
export OVERENIE_VERIFIER=1   # tells the Stop hook this is the verifier, not a builder
mkdir -p overenie "$(dirname "$verdict")"; rm -f "$verdict"

codex_run() {
  local c; c=$(command -v codex || echo ~/.local/bin/codex); [ -x "$c" ] || return 0
  local t=$(date +%s)
  timeout 3600 "$c" exec --skip-git-repo-check -s danger-full-access -C "$PWD" -c model_reasoning_effort=high \
    --json "$(cat "$V" "$brief")" < /dev/null > overenie/verifier-codex.jsonl 2> overenie/verifier-stderr.txt
  python3 -I "$D/usage.py" overenie/verifier-codex.jsonl "$t"
}
claude_run() {
  local t=$(date +%s)
  timeout 3600 claude -p "$(cat "$brief")" --model claude-opus-5-5 --effort high --no-session-persistence \
    --append-system-prompt "$(cat "$V")" --tools Bash,Read,Write,Edit,Glob,Grep \
    --permission-mode bypassPermissions --output-format json < /dev/null > overenie/verifier-output.json 2>&1
  python3 -I "$D/usage.py" overenie/verifier-output.json "$t"
}

# Both CLIs exit 0 even when they hit a limit, so the verdict file is the judge.
if [ -n "${OVERENIE_CLAUDE_FIRST:-}" ]; then claude_run; [ -s "$verdict" ] || codex_run
else codex_run; [ -s "$verdict" ] || claude_run; fi
[ -s "$verdict" ] && echo "verify.sh: verdikt v $verdict" >&2 && exit 0
echo "verify.sh: verdikt nevznikol, pozri overenie/verifier-output.txt" >&2; exit 1
