---
name: zadanie
description: Turns Karchi's short ask into a goal file that an agent can finish alone for an hour or a night. Use when he says /goal, na noc, cez noc, nechaj to bežať, priprav prompt, sprav zadanie, or when a task will clearly need many rounds of his feedback (a UI that has to match a reference, a whole app, a migration, an audit across machines).
---

# Zadanie: a goal that runs without Karchi

From 5 Oct to 4 Nov 2026 the median agent turn ran about 2 minutes and 9 in 10 ended within 15.
After each one Karchi sent a one-line correction, often with a screenshot. The Beeper clone took 73
messages, 25 of them on 4 Nov, because what he wanted reached the agent one sentence at a time. Work
runs long only when the agent can tell for itself that it is done. This skill writes that down first.

## 1. Write the goal file

Save `GOAL-<name>.md` in the project (scratch if there is none). Write it in Slovak and keep it to
about one page. First collect everything he has already asked for in the thread (screenshots,
one-line fixes, "nechcem X") and put it in the file, so none of it comes back as another round.

- **Cieľ:** one sentence describing the finished state, not the work.
- **Vzor:** the reference to match: an app, a URL, a screenshot, a line from `taste.md`. For looks
  never write "nice" or "not AI": name a concrete reference, or plan three variants for him to pick.
- **Hotové keď:** a numbered list. Each item says how the agent checks it itself: a command, a test,
  a Playwright run with a screenshot compared to the reference, a query. Drop any item that has no
  check, or turn it into a question for him.
- **Smieš sám:** what the agent decides without asking (names in code, libraries within the stack,
  order of work, small UX calls that follow `taste.md`).
- **Nesmieš:** hard limits: live services, real people (no messages, no sending), deleting data,
  secrets in chat, spending money.
- **Karchiho krok** (a login, token, purchase or taste decision): write it to the inbox (skill
  `priority`), skip that item and go on with the rest. Never stop to wait.
- **Koniec:** stop when every check passes, or after the time limit he gave (default 3 hours of
  work).

## 2. Run it

- If he asked only for the prompt, give him one line to paste:
  `/goal Splň zadanie z <path>. Hotové je, keď prejdú všetky kontroly v sekcii „Hotové keď“.`
- Otherwise do it yourself in this thread. Work through the checks, then verify with the `overenie`
  skill (runnable checks, a fresh verifier on Opus, evidence page) before you report. Heavy work
  belongs on asus (CLAUDE.md, „Kde beží práca“).
- Long runs use Opus 5.5 at high effort. Use Fable only for a part where Opus already failed: it uses up
  his weekly limit 2.5× faster.

## 3. Report

End with the checks as a list (prešlo / neprešlo and why), then exactly three lines:
`Commit: <repo@sha or nič>`, `Beží: <URL or service, or nič>`, `Tvoj krok: <one action, or nič>`.
He asked "takže už to funguje? commitol si?" 28 times this month: answer those questions before he
has to ask them.
