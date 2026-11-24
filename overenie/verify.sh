#!/usr/bin/env bash
# Usage: verify.sh <brief.md> [verdict, default overenie/verdikt.md]    (run it in the project root)
# The independent verifier of skill overenie: one verifier, the first in the chain that writes the verdict
# (Karchi, 2026-11-24). None of them spends Karchi's Claude limit:
#   opencode   DeepSeek V4.1 Flash, OpenCode's free tier without an account (one limit for the home public IP)
#   sol-moj    GPT Sol 6.2 on Karchi's own ChatGPT (T3's Codex login ~/.codex-t3code/moj)
#   sol-infowork  GPT Sol 6.2 on the Infowork ChatGPT (~/.codex-t3code/infowork)
#   neon       Gemini 4 Neon at high effort through Antigravity (agy-guard)
# OVERENIE_KTO="sol-moj neon" runs only those, in that order: for a second verifier when Karchi asks for one
# (run verify.sh again with another verdict path), or for a different model than the one that built the change.
# Every run logs one line to ~/.claude/overenie-usage.jsonl. Exits 1 when no verdict was written.
set -u
brief=$1 verdict=${2:-overenie/verdikt.md}
[ -s "$brief" ] || { echo "verify.sh: brief $brief neexistuje" >&2; exit 2; }
D=$(dirname "$(readlink -f "$0")"); V=$D/verifier-agents.md
export OVERENIE_VERIFIER=1   # tells the Stop hook this is the verifier, not a builder
export PATH=$PATH:$HOME/.local/bin:$HOME/.bun/bin:$HOME/.opencode/bin
mkdir -p overenie "$(dirname "$verdict")"; rm -f "$verdict"
prompt="$(cat "$V" "$brief")"
out=overenie/verifier-output.txt err=overenie/verifier-stderr.txt

log() {  # <verifier> <start epoch>: one usage line; tokens only where the CLI reports them (Codex, via usage.py)
  jq -cn --arg v "$1" --arg p "$PWD" --arg t "$(date +%FT%T%z)" --argjson s "$2" \
    --argjson ok "$([ -s "$verdict" ] && echo true || echo false)" '{time: $t, project: $p, verifier: $v, verdict: $ok,
      duration_s: ((now - $s) | round)}' >> ~/.claude/overenie-usage.jsonl
}

run_opencode() {
  command -v opencode >/dev/null || return 1
  local t=$(date +%s)
  timeout 3600 opencode run --archived --auto -m "opencode/deepseek-v4.1-flash-free#high" "$prompt" \
    < /dev/null > "$out" 2> "$err"
  log opencode-free "$t"
}

run_sol() {  # <account>: T3's Codex logins live in ~/.codex-t3code/<account>; ~/.codex is not logged in
  local c h=$HOME/.codex-t3code/$1 t
  c=$(command -v codex) && [ -f "$h/auth.json" ] && CODEX_HOME=$h "$c" login status >/dev/null 2>&1 || return 1
  t=$(date +%s)
  CODEX_HOME=$h timeout 3600 "$c" exec --skip-git-repo-check -s danger-full-access -C "$PWD" -m gpt-6.2-sol \
    -c model_reasoning_effort=high --json "$prompt" < /dev/null > overenie/verifier-codex.jsonl 2> "$err"
  OVERENIE_ACCOUNT=$1 python3 -I "$D/usage.py" overenie/verifier-codex.jsonl "$t"
}

run_neon() {
  local a=$HOME/.work/karchi-skills/antigravity/bin/agy t=$(date +%s)
  [ -x "$a" ] || return 1
  # In agy, -p takes the next word as the prompt: keep it last.
  timeout 3600 "$a" --dangerously-skip-permissions --model gemini-4-neon --effort high -p "$prompt" \
    < /dev/null > "$out" 2> "$err"
  log neon "$t"
}

# Every CLI exits 0 even when it hits a limit, so the verdict file is the judge.
for kto in ${OVERENIE_KTO:-opencode sol-moj sol-infowork neon}; do
  case $kto in
    opencode) run_opencode ;;
    sol-moj) run_sol moj ;;
    sol-infowork) run_sol infowork ;;
    neon) run_neon ;;
    *) echo "verify.sh: neznámy overovateľ $kto (opencode, sol-moj, sol-infowork, neon)" >&2; continue ;;
  esac
  [ -s "$verdict" ] && { echo "verify.sh: verdikt od $kto v $verdict" >&2; exit 0; }
  echo "verify.sh: $kto nenechal verdikt, skúšam ďalšieho" >&2
done
echo "verify.sh: verdikt nevznikol, pozri $out a $err" >&2; exit 1
