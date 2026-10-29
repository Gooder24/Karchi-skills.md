#!/usr/bin/env bash
# SessionStart hook (~/.claude/settings.json on every machine): prints Karchi's open inbox items and
# the night worker's report from the last 20 hours, so both are in the context of each session and
# the priority check needs no tool call. The inbox lives on asus (~/inbox); on asus it is read from disk.
snippet='
f="$HOME/inbox/inbox.md"; [ -f "$f" ] || exit 1
sed -n "/^## P1/,/^## Hotové/p" "$f" | grep -v -E "^## Hotové|^- \[x\]|^$"
r=$(ls -t "$HOME"/inbox/worker/*.md 2>/dev/null | head -1)
if [ -n "$r" ] && [ $(( $(date +%s) - $(stat -c %Y "$r") )) -lt 72000 ]; then
  echo "--- Nočný worker $(basename "$r" .md):"; cat "$r"
fi
'
if [ -f "$HOME/inbox/inbox.md" ]; then out=$(bash -s <<< "$snippet")
else out=$(ssh -o ConnectTimeout=3 -o BatchMode=yes asus 'bash -s' <<< "$snippet" 2>/dev/null); fi
if [ -z "$out" ]; then echo "Inbox na asuse nedostupný (skill priority): asus neodpovedá."; exit 0; fi
echo "Karchiho inbox (asus:~/inbox/inbox.md, skill priority), otvorené položky:"
printf '%s\n' "$out"
