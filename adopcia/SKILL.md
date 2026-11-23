---
name: adopcia
description: Give away an idea or side project Karchi will not continue, so someone else can take it - written up in English in his public repo Gooder24/napady with its research, cleaned of personal data, where it waits until he names a place to send his ideas. Use when he says adopcia, daj na adopciu, tomuto sa už nebudem venovať, sidequest pre nikoho/pre niekoho iného, nech sa toho niekto ujme, asks where to put an idea so someone uses it, or names a place to send the collected ideas.
---

# Adopcia: an idea up for adoption

Karchi's rule (2026-11-23): a side project or idea he drops is not thrown away. Its idea, research and state go
public in **`Gooder24/napady`** (checkout `~/napady` on asus; clone it elsewhere), where anyone may take it. The first one was Ownbeat (`~/napady/ownbeat/`).

His words "daj na adopciu" or "tomuto sa už nebudem venovať" are his yes to publish the write-up in `napady`. Making
a private code repo public needs its own yes: ask in one line at the end of the reply, unless he already said so
("aj s kódom"). Work projects (eSYST: `spotrex`, `eSYSTAK`, `enex-crz-email-mvp` and anything for a client) never go
here.

## 1. Write it up (English)

One folder per idea: `~/napady/<slug>/README.md`, a short slug from the idea's name. Read the whole project first:
the thread, plans, research notes, the code's README. The README has:

1. One bold sentence: what it is. Then a paragraph.
2. **Why it could matter**: the problem, with a concrete fact from the research.
3. **What sets it apart**: what existing tools do not do. Name the closest existing projects.
4. **What exists**: plans, research, code and how far it got, with links. Facts that drift (prices, APIs, vendor
   terms) carry the month they were checked.
5. **If you take it over**: where to start, the cheapest first step, the known risks (name not trademark-checked,
   legal limits, what was never tested).
6. The date it stopped.

Long research goes into files beside the README (translated, not summarised away: compare section by section with
the original, every claim and number stays): the research is the point. Keep it in `napady` even when the project
has its own public repo, and link the code from there: a dropped repo often gets archived, and then nothing in it
can be fixed.

Then add one row to the table in `~/napady/README.md`, and one line to the project's own README (and plan, if it has
one) that it is no longer pursued, with a link.

## 2. Clean it before anything goes public

Nothing personal leaves: his real name, emails (`esyst.sk` above all), phone numbers, people he writes with, his
health, school or work data, device serial numbers, tokens and passwords. "Karchi" and "Gooder24" are already public.
The write-up says "the author" and leaves out his machines, Tailscale addresses and private services (Weft,
Kalendarix, Hermes): they are noise to a stranger, though not secret.

```sh
rg -n 'esyst|@gmail|\+421|token|password|secret|serial|\b100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.' <files>
rg -n '<serial of each of his devices, from the project data>' <files>
```

For a code repo going public, check its whole history, not only the tree: `git log -p --all | rg -n '<same pattern>'`
and `git log --format='%ae' | sort -u` (only the GitHub noreply address is fine). Data files (databases, exports,
FIT, photos) in history block publishing: tell him and do not publish. A serial number or a Tailscale address that is
only in old history may stay; say so in the reply. Add a licence before flipping it: MIT, unless the code takes code
under a copyleft licence (then that one). Text in `napady` is CC0.

## 3. Publish

`napady` and the project repo are personal repos: commit to `main`, `git pull --rebase`, push (skill `github`).
`gh repo edit <repo> --visibility public --accept-visibility-change-consequences` only after the yes for code.

## 4. Announce: not by default

Karchi (2026-11-23): he will not post the ideas himself, so by default the work ends at `napady`, where they wait
together. Agents cannot post them for him either: Hacker News has no API for posting and bans automated submissions,
Reddit removes automated posts from new accounts, and both would need his password. Never mail anyone about an idea.

When he later names a place for the collected ideas, check how it takes submissions. Where an agent can submit
without his login (an API, a public form, a pull request to a list on GitHub), his naming the place is the yes:
submit every idea in `napady` that is not there yet and note the place in the idea's README. Where it needs his
account, tell him so in one sentence.

Only when he asks for links to post himself: prefilled submit forms, Show HN only when there is code people can try.

```sh
bun ~/.work/karchi-skills/adopcia/odkazy.ts '<title>' '<url>' '<two short paragraphs>' [subreddit]
```

## 5. Reply

The usual end of a reply (AGENTS.md): what is public with its URL, and what stayed private and why.
