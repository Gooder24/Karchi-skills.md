---
name: retro
description: Prompt retro for Karchi - reviews a finished thread and tells him how he could have reached the same result with one prompt. Use when he says retro, ako som to mohol povedať, ako som to mohol napísať na jeden prompt, or asks how to prompt a finished task better. The morning run on asus does this by itself.
---

# Retro: how one prompt would have done it

## Morning run (automatic)

Cron on asus, 07:05 Mon-Fri: `python3 -I ~/.work/karchi-skills/retro/retro.py`. It takes the T3 thread
settled in the last 24 h (72 h on Monday) on any machine where Karchi wrote the most messages, five at
least, and has Opus (`claude -p`, high effort) review it with `prompt.md`. The retro is saved to
`~/inbox/retro/<date>.md` and copied to Rerun Chief of Staff `notes/retro/`, so the 07:30
„Ranný prehľad“ opens with a three-line tip. On a day without such a thread nothing is written.

- Test without calling Claude: `retro.py --dry`.
- One particular thread: `retro.py --thread <id>`. Other window: `--hours 48`, `--min-rounds 3`.

## In a thread (on request)

When he asks for a retro of the current or a named thread, run
`ssh asus 'python3 -I ~/.work/karchi-skills/retro/retro.py --thread <id>'` and show him the saved file.
If asus does not answer, write the retro yourself following `prompt.md`, reading his messages with
`priority/thread-digest.py --thread <id> --messages 200`.
