#!/usr/bin/env bash
# Before/after evidence for a T3 Code web PR, against an isolated dev server.
# Run from the PR checkout: before-after.sh <home-dir> <command...>
# <command> runs twice with LABEL=after (this branch) and LABEL=before (origin/main's copies of the
# changed apps/web and packages files), with PAIRING_URL and ORIGIN set. Use capture.mjs as the command.
# Seed <home-dir> first: start once, `node apps/server/src/bin.ts project add`, then
# `node apps/server/scripts/t3-sqlite-state.ts exec --base-dir <home-dir> --file seed.sql` with the server stopped.
set -uo pipefail
export PATH=$HOME/.local/share/vite-plus/bin:$HOME/.local/bin:$PATH
HOME_DIR=$1; shift
LOG=$(mktemp)
FILES=$(git diff --name-only origin/main...HEAD -- apps/web packages | grep -v '\.test\.')
T3CODE_DEV_SEED=0 setsid vp run dev --home-dir "$HOME_DIR" >"$LOG" 2>&1 &
DEV=$!
cleanup() { git checkout -q HEAD -- $FILES; kill -- -$DEV 2>/dev/null; wait $DEV 2>/dev/null; rm -f "$LOG"; }
trap cleanup EXIT
for _ in $(seq 1 90); do grep -q pairingUrl "$LOG" && break; sleep 2; done
export PAIRING_URL=$(grep -o 'pairingUrl: \S*' "$LOG" | tail -1 | cut -d' ' -f2)
export ORIGIN=${PAIRING_URL%%/pair*}
[ -n "$PAIRING_URL" ] || { echo "dev server did not print a pairing URL"; tail -20 "$LOG"; exit 1; }
LABEL=after "$@"
git checkout -q origin/main -- $FILES && sleep 5   # Vite reloads the changed modules
LABEL=before "$@"
