---
name: weft
description: Karchi's messages and calendar through Weft (Messenger, Instagram, WhatsApp, Discord, EduPage, Gmail in one inbox on asus), with the `weft` command on every machine. Use when he asks what someone wrote, what is unread, to find a message, to reply or write to someone (draft or send), or to see, add or change a calendar event.
---

# Weft for agents

`weft` (in `~/.local/bin` on asus, dell, e540 and x270; it runs on asus, elsewhere over `ssh asus`) reads
and writes Karchi's Weft as him. Same data he sees in Weft. `weft --help` lists everything; add `--json`
for machine-readable output.

```
weft chats [TEXT] [--unread] [--net messenger|instagram|whatsapp|discord|edupage|gmail] [-n 30] [--all]
weft read CHAT [-n 30]               the chat, oldest first (older pages come from the archive, never from Meta)
weft search WORDS [--chat CHAT]      homeserver and archive, newest first
weft draft CHAT TEXT|-               a draft in that chat's message box in Weft; he sends it himself
weft drafts [--clear CHAT]           drafts he has not sent yet
weft send CHAT TEXT|- --yes          sends as Karchi (without --yes it only shows where it would go)
weft cals | weft cal [--from YYYY-MM-DD] [--days 7] [--cal NAME]
weft cal-add TITLE --start "YYYY-MM-DD HH:MM" [--end ...|--minutes 60] [--cal NAME] [--location ..] [--notes ..]
weft cal-edit UID [--title|--start|--end|--location|--notes|--cal ...]   weft cal-del UID
```

CHAT is part of the chat's name (diacritics and case do not matter) or its room id; a name that fits more
chats is refused with the list, then use the room id. `TEXT` `-` reads stdin (for longer or multi-line text).
Times are Europe/Bratislava; `--start 2026-11-12` alone is an all-day event.

## Rules

- **Draft by default.** When he asks you to answer or write to someone, use `weft draft`: it appears in
  that chat's message box in Weft (and as „Koncept:“ in the list) and he sends it. Use `weft send --yes`
  only when he said to send it in this conversation (pošli, odošli) and the text and the chat are settled.
  Run it once without `--yes` first and check the chat it names.
- A message goes to real people and cannot be taken back. Never send in a loop, never to a chat you
  guessed, never a test message. Tests run against a fake (weft repo, `overenie/agent-drafts/ui.cjs`).
- Reading changes nothing in Weft: no read receipts, nothing marked seen. Keep reads small (`-n`), no
  bulk export of his chats, and do not paste his messages into anything outside his machines.
- Calendar: events of the EduPage timetable (calendar `lifeos-edupage`, uid ending `@lifeos`) belong to a
  sync program and are refused. `cal-del` on a repeating event deletes the whole series.
- If `weft` says asus does not answer, say so; do not work around it.
