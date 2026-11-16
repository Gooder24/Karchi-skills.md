---
name: ucenie
description: Karchi's learning system "Učenie" (flashcards like Anki, maturita, sidequest decks, notes, EduPage homework and a "learn harness" in one app built like Weft), planned and built in an e540 thread. Use only when Karchi himself talks about that system: building, choosing or changing a learning or study app or system, putting his flashcards and quizzes in one place, a learn harness, new cards or quizzes for a school subject, homework drafts, or the maturita quiz and its Telegram bot. Never for work on one existing deck or project that merely uses Anki, such as the Katolický atlas rosary deck.
---

# Učenie: the plan and the build already exist

On 16. 11. 2026 Karchi asked for one app for all his learning: Anki-style review, a learn harness, sidequest
decks (rosary decades, Meitei numbers), notes, EduPage (and later his university's system) "like Weft", with
homework solved into drafts that he submits. The plan and the build live in this thread, project „Učenie“
(e540 `~/.t3/projects/ucenie`, the goal is `GOAL-ucenie.md` there, its build was scheduled for 17. 11. 1:00):

[celý systém ako budem mať svoje učenie pod kontrol...](t3-thread://v2/93bab4d1-e3e8-41f6-a853-20b3b844f477/c183bd0d-b31a-4c8b-87eb-88715762d123)
on e540, T3 environment `93bab4d1-e3e8-41f6-a853-20b3b844f477`, thread `c183bd0d-b31a-4c8b-87eb-88715762d123`.

The first plan (QML app, 16. 11. afternoon) is in the e540 thread `d48da998-18e1-4ae9-bf76-5d96673c0255`;
the goal file replaces it.

## When it applies

Only when Karchi's own message is about the learning system itself (see the description). A thread that
works on one deck or app and merely uses Anki is not that: on 16. 11. the Katolický atlas thread, asked to
redo the rosary cards, woke the snoozed plan ten minutes after he snoozed it. Then do nothing: no
sentence, no wake.

1. Start your reply with one sentence saying the system exists, with the thread link above.
2. If that thread is snoozed, wake it once: `t3_thread_organize` with `action: "unsnooze"`, its `threadId`
   and the `environmentId` above, then `action: "mark_unread"`. Outside T3, or when the call fails, say
   once that the thread is on e540 and go on.
3. Build on `GOAL-ucenie.md` and the code in that project. When his new ask changes it, say what changes
   and change that file; never start a second plan beside it.

## Open decisions (also in his inbox)

- Which university system comes after EduPage.
- The first real homework submission from a draft: he tries it once himself.
- Whether Anki on x270 and the atlas's separate Anki deck go away once the app works.
- The Telegram bot never ran: after he creates a bot with @BotFather he runs
  `ssh -t e540 ~/maturita-bot/set-token.sh`.

## Removing this skill

When the app is built and in use, or he drops the idea, delete this folder and its README row, then commit
and push, so it stops loading.
