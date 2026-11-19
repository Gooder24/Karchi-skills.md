---
name: ucenie
description: Karchi's learning app Učenie (Anki-style cards, maturita, sidequest decks like the rosary or Meitei numbers, notes, EduPage homework with agent drafts, the learn harness), with the `ucenie` command on every machine. Use when Karchi talks about his learning system or wants something in it: new cards or a pack for a subject, cards from homework material or a note, a homework draft, what is due, importing or exporting an Anki deck, the maturita quiz and its Telegram bot, or changing the app. Never for work on one existing deck or project that merely uses Anki, such as the Katolický atlas rosary deck itself.
---

# Učenie

Karchi's one place for learning (built 17. 11. 2026, plan and history in the e540 thread
[celý systém ako budem mať svoje učenie pod kontrol...](t3-thread://v2/93bab4d1-e3e8-41f6-a853-20b3b844f477/c183bd0d-b31a-4c8b-87eb-88715762d123),
goal `GOAL-ucenie.md`). Code: github.com/Gooder24/ucenie, checkout e540 `~/.t3/projects/ucenie`; it runs on asus
(unit `ucenie`, data `~/ucenie/data`, https://asus-vivobook-x1504v.taila3702d.ts.net:8451/), x270 opens it from the
launcher (karchi-os `karchi-ucenie`, a Helium app window). A change to the app goes into that repo and out with its
`tools/deploy`; never start a second learning app or plan beside it.

## For agents: `ucenie`

`ucenie` (in `~/.local/bin` on every machine; it runs on asus, elsewhere over `ssh asus`):

```
ucenie dnes                          what is due per pack, homework, tests
ucenie balicky | ucenie ulohy        packs (and those waiting for approval) | homework with its draft state
ucenie koncept ULOHA                 the agent writes a draft for that homework (stored in the app, never sent)
ucenie make-pack --uloha ID | --poznamka PREDMET/NAZOV.md | --subor PATH  [--nazov N] [--predmet P] [--druh D]
ucenie pridaj-balik PACK.json        a pack you wrote yourself (validated); waits for approval unless --hned
ucenie import FILE.apkg [--druh ...] | ucenie export BALIK OUT.apkg
ucenie anki-historia KOLEKCIA BALIK [--zaloha F.colpkg ...] [--alias STARE=NOVE]   Anki answers into the log
```

A pack is one JSON: `{"id", "nazov", "druh": "skola|maturita|sidequest", "predmet", "karty": [...]}`, a card is
`{"id", "typ": "karticka", "otazka", "odpoved"}`, `{"typ": "ad", "moznosti": {"A": ...}, "spravne": "B"}` or
`{"typ": "kratka", "varianty": [...]}`, optionally `"ukazka"` (a key of the pack's `"ukazky"`, shown beside it).
When Karchi asks for cards on something, write the pack (facts only from a source you name in `"zdroj"`) and add it
with `ucenie pridaj-balik`; it waits in Balíky for him to accept.

## Rules

- Nothing goes to EduPage: drafts stay in Učenie until Karchi submits them himself. „Odovzdať…“ shows the exact
  text, copies it, saves it as a .txt in Downloads and opens EduPage (whole path checked 20. 11. by
  `overenie/submit.cjs`). EduPage homework without an answer card (`etestAnswerCards: 0`, most of his) is handed in as
  a reply with an attachment under the homework, which is a message to the teacher in his name; homework with answer
  cards is filled in EduPage's own player. Neither is automated, by decision: it stays his click.
- The answer log is his progress: tests run against a throwaway instance (`overenie/test-server.sh` in the repo),
  never against `~/ucenie/data`.
- The learn harness drafts new homework by itself only 7:00–22:00, a few a day, each homework once.

## Decisions (Karchi let the agent decide, 20. 11. 2026)

- University system: no adapter yet. He is in III. A of a business academy, so a university is over a year away
  and its system (AIS2 at most Slovak public universities, MAIS at TUKE, Moodle for courses) is not known. The empty
  „Vysoká škola“ box stays; the adapter is built for his school once he is admitted and has a login.
- Anki: keep it installed, untouched, but stop reviewing in it. Učenie is the only scheduler; two would set
  different due dates. His last Anki review was 16. 11.; 25 of those 30 answers are in Učenie's log (5 belonged to
  cards that existed only between Anki backups and cannot be matched). `.apkg` import and export stay the way in and out.
