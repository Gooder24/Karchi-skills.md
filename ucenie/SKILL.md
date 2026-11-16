---
name: ucenie
description: Karchi's planned learning app for KarchiOS (maturita reading quiz, Anki flashcards and a "learn harness" in one app) and the snoozed e540 thread that holds its plan. Use whenever he talks about a learning or study system, Anki, flashcards, kartičky, opakovanie, spaced repetition, a daily quiz, maturita practice, the maturita Telegram bot or a learn harness, before you propose or build anything for it.
---

# Learning app: the plan already exists

On 16. 11. 2026 Karchi asked for one KarchiOS app that joins his maturita practice, his Anki flashcards
and a "learn harness". He snoozed the planning thread until 30. 11. and asked that it speak up whenever
he talks about a learning system again. That thread holds the plan and all the work so far:

[zober z x270 všetky stiahnuté maturity (ak tu nie ...](t3-thread://v2/93bab4d1-e3e8-41f6-a853-20b3b844f477/d48da998-18e1-4ae9-bf76-5d96673c0255)
on e540, T3 environment `93bab4d1-e3e8-41f6-a853-20b3b844f477`, thread `d48da998-18e1-4ae9-bf76-5d96673c0255`.

## When it comes up

1. Start your reply with one sentence saying the plan exists, with the thread link above.
2. Wake that thread: `t3_thread_organize` with `action: "unsnooze"`, its `threadId` and the
   `environmentId` above, then the same call with `action: "mark_unread"`. Outside T3, or when the call
   fails, say once that the thread is on e540 and go on.
3. Build on the plan below. When his new ask changes it, say what changes; never start a second plan
   beside it.

## The plan (proposed 16. 11., nothing built yet)

- One new KarchiOS package in Quickshell/QML with `karchi-pixelkit`, like Files and Music. The other
  options were Electron (like Kalendarix) and plain Anki. RAM in `asus:~/stack-bench/REPORT.md`, measured
  on a chat app: Qt/QML ~150 MB, Electron 470–600 MB.
- One Python core. Every item is a card in a pack, one JSON file per pack: a flashcard, an A–D task or a
  short answer; a task can belong to a passage that is shown beside it. One scheduler for everything,
  FSRS (`fsrs` on PyPI). Progress is an append-only log of answers and due dates are computed from it, so
  devices merge by joining their logs.
- Review keys as he set them in Anki: Space = Again, `,` = Hard, `.` = Good, `-` = Easy. A–D tasks and
  short answers rate themselves: right is Good, wrong is Again.
- Packs: maturita from `data/questions.json` in the thread's worktree
  `e540:~/.t3/worktrees/maturita-prep/t3code-93a9f220`; the rosary from the data that
  `asus:~/.work/katolicky-atlas/deck/build_deck.py` turns into his Anki deck; any `.apkg` through the
  `anki` package, with export back to Anki as the way out. The learn harness writes packs in the same
  format.
- x270 keeps its own database and works offline. The main copy sits on e540 next to the Telegram bot
  (`e540:~/maturita-bot`, system service `maturita-bot`), which becomes the phone side of the same core.
  The bot's code, its README section and NAVRH.md are still uncommitted in that worktree; the running
  copy is `~/maturita-bot/app`.
- Phases: 1 core, packs and the bot on the core (first demo); 2 the KarchiOS app with a Today screen and
  review, checked on a test-VM screenshot; 3 sync x270 ↔ e540 and offline; 4 Anki import and export,
  the learn harness and "explain my mistake".

## Open decisions (also in his inbox)

- Which stack.
- What "learn harness" means. It was found nowhere on e540, asus or dell on 16. 11.; the plan assumes an
  agent that turns material into packs.
- Whether Anki on x270 and the atlas's separate Anki deck go away once the app works.
- The Telegram bot never ran: after he creates a bot with @BotFather he runs
  `ssh -t e540 ~/maturita-bot/set-token.sh`.

## Removing this skill

When the app is built or he drops the idea, delete this folder and its README row, then commit and push,
so it stops loading.
