#!/usr/bin/env bash
# Usage: verify.sh <brief.md> [verdict, default overenie/verdikt.md]    (run it in the project root)
# The independent verifiers of skill overenie (Karchi, 2026-11-24): two run side by side and each writes its own verdict,
# which this script joins into the one verdict file:
#   opus       Claude Opus 5.5 at high effort
#   the chain  the first of these that writes a verdict, so a used-up limit moves to the next:
#     opencode      DeepSeek V4.1 Flash, OpenCode's free tier without an account (one limit for the home public IP)
#     sol-moj       GPT Sol 6.2 on Karchi's own ChatGPT (T3's Codex login ~/.codex-t3code/moj)
#     sol-infowork  GPT Sol 6.2 on the Infowork ChatGPT (~/.codex-t3code/infowork)
#     neon          Gemini 4 Neon at high effort through Antigravity (agy-guard)
# OVERENIE_KTO="sol-moj neon" replaces the chain, in that order, when Karchi asks for other verifiers.
# Each verifier keeps its files in overenie/<name>/ (verdikt.md, output.txt, stderr.txt). Every run logs one line to
# ~/.claude/overenie-usage.jsonl. Exits 1 when neither wrote a verdict.
set -u
brief=$1 verdict=${2:-overenie/verdikt.md}
[ -s "$brief" ] || { echo "verify.sh: brief $brief neexistuje" >&2; exit 2; }
D=$(dirname "$(readlink -f "$0")"); V=$D/verifier-agents.md
export OVERENIE_VERIFIER=1   # tells the Stop hook this is the verifier, not a builder
export PATH=$PATH:$HOME/.local/bin:$HOME/.bun/bin:$HOME/.opencode/bin
mkdir -p overenie "$(dirname "$verdict")"; rm -f "$verdict"

prompt() {  # <dir>: the rules, the brief, and this verifier's own verdict path, which overrides the brief's
  cat "$V" "$brief"
  printf '\n\nWrite your verdict to %s (this overrides any verdict path above). Another verifier checks the same change at the same time: never touch its files under overenie/.\n' "$1/verdikt.md"
}

log() {  # <verifier> <dir> <start epoch>: one usage line for the CLIs that report no tokens
  jq -cn --arg v "$1" --arg p "$PWD" --arg t "$(date +%FT%T%z)" --argjson s "$3" \
    --argjson ok "$([ -s "$2/verdikt.md" ] && echo true || echo false)" '{time: $t, project: $p, verifier: $v, verdict: $ok,
      duration_s: ((now - $s) | round)}' >> ~/.claude/overenie-usage.jsonl
}

run_opus() {  # Claude gets six tools: the default set of about a hundred costs ~27 000 tokens a step (9. 11.)
  local d=overenie/opus t=$(date +%s)
  command -v claude >/dev/null || return 1
  timeout 3600 claude -p "$(prompt "$d")" --model claude-opus-5-5 --effort high --no-session-persistence \
    --tools Bash,Read,Write,Edit,Glob,Grep --permission-mode bypassPermissions --output-format json \
    < /dev/null > "$d/output.json" 2> "$d/stderr.txt"
  OVERENIE_ACCOUNT=opus python3 -I "$D/usage.py" "$d/output.json" "$t"
}

run_opencode() {
  local d=overenie/opencode t=$(date +%s)
  command -v opencode >/dev/null || return 1
  timeout 3600 opencode run --archived --auto -m "opencode/deepseek-v4.1-flash-free#high" "$(prompt "$d")" \
    < /dev/null > "$d/output.txt" 2> "$d/stderr.txt"
  log opencode-free "$d" "$t"
}

run_sol() {  # <account>: T3's Codex logins live in ~/.codex-t3code/<account>; ~/.codex is not logged in
  local d=overenie/sol-$1 h=$HOME/.codex-t3code/$1 c t
  c=$(command -v codex) && [ -f "$h/auth.json" ] && CODEX_HOME=$h "$c" login status >/dev/null 2>&1 || return 1
  t=$(date +%s)
  CODEX_HOME=$h timeout 3600 "$c" exec --skip-git-repo-check -s danger-full-access -C "$PWD" -m gpt-6.2-sol \
    -c model_reasoning_effort=high --json "$(prompt "$d")" < /dev/null > "$d/output.jsonl" 2> "$d/stderr.txt"
  OVERENIE_ACCOUNT=$1 python3 -I "$D/usage.py" "$d/output.jsonl" "$t"
}

run_neon() {
  local d=overenie/neon a=$HOME/.work/karchi-skills/antigravity/bin/agy t=$(date +%s)
  [ -x "$a" ] || return 1
  # In agy, -p takes the next word as the prompt: keep it last.
  timeout 3600 "$a" --dangerously-skip-permissions --model gemini-4-neon --effort high -p "$(prompt "$d")" \
    < /dev/null > "$d/output.txt" 2> "$d/stderr.txt"
  log neon "$d" "$t"
}

run_chain() {  # Every CLI exits 0 even when it hits a limit, so the verdict file is the judge.
  local kto
  for kto in ${OVERENIE_KTO:-opencode sol-moj sol-infowork neon}; do
    case $kto in
      opencode) run_opencode ;;
      sol-moj) run_sol moj ;;
      sol-infowork) run_sol infowork ;;
      neon) run_neon ;;
      *) echo "verify.sh: neznámy overovateľ $kto (opencode, sol-moj, sol-infowork, neon)" >&2; continue ;;
    esac
    [ -s "overenie/$kto/verdikt.md" ] && { echo "$kto" > overenie/chain-kto; return 0; }
    echo "verify.sh: $kto nenechal verdikt, skúšam ďalšieho" >&2
  done
}

for d in opus opencode sol-moj sol-infowork neon; do rm -rf "overenie/$d"; mkdir -p "overenie/$d"; done
rm -f overenie/chain-kto
run_opus & run_chain & wait

kto=$(cat overenie/chain-kto 2>/dev/null)
{
  for v in opus "${kto:-chain}"; do
    if [ -s "overenie/$v/verdikt.md" ]; then echo "## Overovateľ: $v"; echo; cat "overenie/$v/verdikt.md"
    else echo "## Overovateľ: $v – verdikt nevznikol (limit alebo chyba), pozri overenie/*/output.txt a stderr.txt"; fi
    echo
  done
} > "$verdict.tmp"
if [ -s overenie/opus/verdikt.md ] || [ -n "$kto" ]; then
  mv "$verdict.tmp" "$verdict"; echo "verify.sh: verdikt v $verdict" >&2; exit 0
fi
rm -f "$verdict.tmp"; echo "verify.sh: verdikt nevznikol, pozri overenie/*/output.txt a stderr.txt" >&2; exit 1
