#!/bin/sh
# Copies the night tasks' reports (~/inbox/worker/*.md from the last 20 h) into the notes of Rerun's
# Chief of Staff, so its 07:30 "Ranný prehľad" opens with them. Cron 07:20 Mon-Fri. Log: ~/.local/state/noc-pre-rerun.log
AGENT=/data/agents/x8j38cwag1625bjbuk6od/workspace/notes/noc
LOG="$HOME/.local/state/noc-pre-rerun.log"; mkdir -p "$(dirname "$LOG")"
docker exec -u rerun rerun-engine-1 mkdir -p "$AGENT" || { echo "$(date -Iseconds) FAIL engine" >> "$LOG"; exit 1; }
n=0
for f in $(find "$HOME/inbox/worker" -maxdepth 1 -name '*.md' -mmin -1200 | sort); do
  docker exec -i -u rerun rerun-engine-1 sh -c "cat > '$AGENT/$(basename "$f")'" < "$f" && n=$((n+1))
done
echo "$(date -Iseconds) ok $n" >> "$LOG"
