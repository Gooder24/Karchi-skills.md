#!/usr/bin/env bash
# SessionStart hook (~/.claude/settings.json on every machine): prints Karchi's open inbox items so
# they are in the context of each session and the priority check needs no tool call. The inbox lives
# on asus (~/inbox/inbox.md); on asus itself it is read from disk.
f="$HOME/inbox/inbox.md"
if [ -f "$f" ]; then out=$(cat "$f")
else out=$(ssh -o ConnectTimeout=3 -o BatchMode=yes asus 'cat ~/inbox/inbox.md' 2>/dev/null); fi
if [ -z "$out" ]; then echo "Inbox na asuse nedostupný (skill priority): asus neodpovedá."; exit 0; fi
echo "Karchiho inbox (asus:~/inbox/inbox.md, skill priority), otvorené položky:"
printf '%s\n' "$out" | sed -n '/^## P1/,/^## Hotové/p' | grep -v -E '^## Hotové|^- \[x\]|^$'
