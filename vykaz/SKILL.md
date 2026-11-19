---
name: vykaz
description: Karchi's paid-work log for eSYST (duálne štúdium, plat), ~/Work/dual/1.plat/<mesiac>.xlsx on x270, filled by itself from his eSYST threads in T3 on every machine and from the time Outlook, Teams or an eSYST thread is the focused window on x270, with the `vykaz` command. Use when he asks about his hours or the výkaz/plat file, what he did for eSYST on a day, a row in it that is wrong, or a new month's file. The Tuesday school practice is the separate `dochadzka` tool on x270.
---

# Výkaz práce pre eSYST

Súbor: x270 `~/Work/dual/1.plat/<mesiac>.xlsx` (`november.xlsx`, `december.xlsx`, `januar.xlsx` …; september a
október vyplnil ručne). Riadok je jedno sedenie: A popis, B `D.M.RRRR H:MM-H:MM`, C `H.MM h` (hodiny.minúty,
`1.30 h` = hodina a pol); riadok `H.MM h | spolu` je súčet všetkých riadkov. Jeho ručné riadky a poznámky
(stĺpce D–F) ostávajú, nové riadky sa vložia podľa dátumu a súčet sa prepočíta.

## Ako sa plní

- `okna.py` (`vykaz-okna.service` na x270): udalosti Hyprlandu, žiadne pollovanie. Do
  `~/.local/share/vykaz/okna/<deň>.tsv` zapíše čas, keď je aktívne okno Outlook, Teams alebo T3 s eSYST
  vláknom (titul okna), a „-“, keď prejde inam. Iné tituly neukladá.
- `t3-esyst.py`: jeho vlastné správy (nie agentov) v eSYST vláknach T3 na stroji, iba čítanie projekčných
  tabuliek `statev2.sqlite` (nikdy `auth_*` ani secrets). eSYST = projekty SPOTREX, Obhajoba práce, eSYST…,
  Hurbanova, alebo vlákno či správa, ktorá spomína eSYST, SPOTREX, CRS 40, EUCF, Gondžára, firemné….
- `vykaz.py` (`vykaz.timer` na x270, 12:00 a 20:00, po prebudení dobehne, medzi 23:00 a 7:00 nič nerobí):
  za každý dokončený deň od 1. 11. 2026, ktorý ešte nie je v `~/.local/share/vykaz/zapisane.json`, zoberie
  správy zo všetkých strojov (x270 lokálne, asus, dell, e540 cez ssh) a okná. Správa = 5 min pred a 10 min po,
  okno najviac 20 min, udalosti do 20 min od seba sú jedno sedenie, zaokrúhlené na 5 min, kratšie než 10 min
  vypadnú. Vynechá čas utorkovej praxe (`~/Work/dual/dochadzka/zaznamy/<deň>.json`) a čas, ktorý už v súbore
  je. Popis sedenia napíše Haiku (`claude -p`); sedenie, ktoré nie je práca pre eSYST, vynechá. Čo sa ráta,
  komu súbor ide a ďalšie predpoklady sú v `predpoklady.md` (oprav tam). Bez siete alebo asusu nezapíše nič a
  skúsi to nabudúce; spiaci dell či e540 deň pozdrží, po dvoch dňoch sa zapíše bez neho.
- Pred každou zmenou je záloha v `~/.local/share/vykaz/zalohy/<mesiac>-<čas>.xlsx`. Súbor otvorený v
  OnlyOffice/LibreOffice (zámok `.~lock.…#`) nechá na ďalší beh.

## Príkazy (na x270; inde ten istý príkaz ide cez `ssh x270`)

```
vykaz                 zapíše dokončené dni, ktoré ešte nie sú zapísané (to robí timer)
vykaz ukaz DÁTUM      čo by za deň zapísal, nič nemení
vykaz zapis DÁTUM     deň znova: pridá len sedenia, ktoré v súbore ešte nie sú
vykaz vrat [MESIAC]   vráti súbor do stavu pred posledným zápisom
vykaz stav            zapísané dni, zálohy, dnešné okná a stav jednotiek
```

Riadok, ktorý nesedí, Karchi jednoducho zmaže alebo prepíše v súbore: deň je už v `zapisane.json`, takže sa
znova nepridá. Celý deň nanovo: zmaž jeho riadky v súbore a `vykaz zapis DÁTUM`.

Inštaluje to `install.sh` (len na x270, `uname -n` = `karchi`): venv s openpyxl v
`~/.local/share/vykaz/venv`, jednotky v `~/.config/systemd/user`, `~/.local/bin/vykaz` na každom stroji.
