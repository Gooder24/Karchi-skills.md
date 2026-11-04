#!/usr/bin/env bash
# SessionStart hook (~/.claude/settings.json on every machine): prints Karchi's open inbox items and
# every night-task report from the last 20 hours (worker and long tasks), so both are in the context of each session and
# the priority check needs no tool call. The inbox lives on asus (~/inbox); on asus it is read from disk.
snippet='
f="$HOME/inbox/inbox.md"; [ -f "$f" ] || exit 1
sed -n "/^## P1/,/^## Hotové/p" "$f" | grep -v -E "^## Hotové|^- \[x\]|^$"
for r in $(ls -tr "$HOME"/inbox/worker/*.md 2>/dev/null); do
  [ $(( $(date +%s) - $(stat -c %Y "$r") )) -lt 72000 ] || continue
  echo "--- Nočný worker $(basename "$r" .md):"; cat "$r"
done
'
if [ -f "$HOME/inbox/inbox.md" ]; then out=$(bash -s <<< "$snippet")
else out=$(ssh -o ConnectTimeout=3 -o BatchMode=yes asus 'bash -s' <<< "$snippet" 2>/dev/null); fi
if [ -z "$out" ]; then echo "Inbox na asuse nedostupný (skill priority): asus neodpovedá."; exit 0; fi
echo "Karchiho inbox (asus:~/inbox/inbox.md, skill priority), otvorené položky:"
printf '%s\n' "$out"
