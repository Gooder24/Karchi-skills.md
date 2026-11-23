---
name: stylizacia
description: How to word a Slovak business text the way Karchi's business-correspondence teacher (OBK, Kubišová) corrects it, for eSYST customers and for school. Use before writing or rewriting any Slovak text a customer or business partner of eSYST will read (e-mail, letter, offer, order confirmation, reply to a complaint, payment reminder, apology), for OBK homework „štylizácia“ or „preštylizuj“, and when he asks for pevné medzery or Ctrl+Shift+Space.
---

# Štylizácia obchodného textu

The rules come from his OBK class (teacher Andrea Kubišová, 3rd year): her corrections of the class's
restyled letters (tasks 1–10, November 2026) and STN 01 6910. They hold for eSYST customers too.

## How the sentence is built

- The firm writes: 1st person plural („objednávame“, „upozorňujeme Vás“). The reader is „Vy, Vás, Váš, Vám“
  with a capital V, the same way in the whole text.
- The first words say the matter: „Reklamujeme montáž…“, „Upozorňujeme Vás, že faktúra…“,
  „Na základe Vašej ponuky zo dňa 18. novembra 2026 objednávame…“. No warm-up („Dovoľujeme si…“, „Týmto…“).
- Keep every fact from the source: invoice number, sum, date, goods, quantities, place, deadline.
  Add nothing that is not there: the teacher struck invented deadlines, court threats and extra
  polite requests. Ask Karchi when a fact is missing; for school fill a plausible date before today.
- Short: one thought per sentence, usually 2–3 sentences. Fold a relative clause into a participle
  („faktúru … vystavenú za dodávku…“ rather than „ktorú sme Vám vystavili za dodávku…“).
- Name the fact plainly: „Opakovane Vás upozorňujeme na skutočnosť, že faktúra č. 543/2026 splatná
  10. 10. 2026 nebola k dnešnému dňu uhradená.“
- Plain standard Slovak: „ak“ (not „v prípade, že“), „o, týkajúce sa“ (not „ohľadom“), „na“ (not
  „za účelom“), „uhradiť“ (not „zaplatiť“ in a reminder). Comma before „že, ktorý, aby, ak“.

## Openings by kind of text

| Kind | Opening |
|---|---|
| dopyt | Žiadame Vás o bližšie informácie o… / Na základe Vašej ponuky Vás žiadame o… |
| ponuka | Ponúkame Vám… / Na Váš dopyt zo dňa … Vám ponúkame… |
| objednávka | Na základe Vašej ponuky zo dňa … objednávame… |
| zmena objednávky | Meníme našu objednávku… Namiesto … objednávame… |
| urgencia dodávky | Upozorňujeme Vás, že termín dodania … bol dňa… |
| reklamácia | Reklamujeme…, ktorá je… Žiadame o… |
| 1. upomienka | Upozorňujeme Vás, že do dnešného dňa ste neuhradili faktúru č. … vo výške … |
| 2. a 3. upomienka | Opakovane Vás upozorňujeme na skutočnosť, že faktúra č. … |
| odpoveď na urgenciu | Ďakujeme za Vašu urgenciu a ospravedlňujeme sa za meškanie s… |

## Numbers and pevné medzery

Dates „10. novembra 2026“ (month in lower case) or „10. 11. 2026“; sums „1 560 eur“, „1 800,00 €“;
„10 %“; „č. 567/2026“. A non-breaking space (Word: Ctrl+Shift+Space, U+00A0) goes after one-letter words
(a, i, k, o, s, u, v, z), after „č.“ and titles, between day and month, inside a number with thousands,
between a number and its unit, and inside „s. r. o.“. Do not type them by hand:

```sh
bun ~/.work/karchi-skills/stylizacia/pevne-medzery.ts text.txt > hotovy.txt   # puts them in
bun ~/.work/karchi-skills/stylizacia/pevne-medzery.ts --check text.txt          # lists the missing ones
```

In a docx put them into the `<w:t>` of the new text only, and leave the source text as it was.

## For eSYST

eSYST is his paid work: a text for a customer is a draft that Karchi sends himself. Never send it on
his behalf without his yes in the thread.
