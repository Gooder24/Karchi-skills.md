# Predpoklady výkazu (oprav tu, platí od ďalšieho behu)

Karchi 20. 11. 2026 nechal tieto otázky na agentoch („rozhodni“). Sú to odhady z dát, nie jeho slová. Keď niečo
nesedí, prepíš to tu (alebo povedz agentovi) a zmaž zlé riadky v súbore mesiaca; `vykaz zapis DÁTUM` potom deň
doplní znova. Sekciu „Čo sa ráta“ dostáva model, ktorý píše popisy, doslova.

## Čo sa ráta

Firemná práca: SPOTREX (systém na odpočty meračov tepla a vody pre eSYST, stanice CRS 40, MQTT, VPS,
účtovanie), firemný AI asistent a AI nástroje pre zamestnancov (eSYSŤák, Hermes pre firmu, firemný T3 Code,
tímové účty Claude, lokálne AI a stroj naň, firemné počítače, firemné heslá, GitHub organizácia eSYST), zákazky
eSYST (napr. Hurbanova), EUCF, firemné e-maily a Teams.

Nie je firemná práca: škola (vyučovanie, domáce úlohy, maturita, učenie), samotné písanie školskej práce (SOČ,
obhajoba, kapitoly, prezentácia pre komisiu), vlastný notebook a jeho vzhľad, osobné aplikácie (Weft, Učenie,
kalendár), hudba (aj partsheet, spevník zboru), open source, jeho vlastný výkaz hodín a nástroj, ktorý ho plní (vykaz). Vlákno v projekte „Obhajoba práce“ sa ráta len vtedy, keď v ňom robí niečo pre
eSYST (napr. firemný AI stack, účty, firemný T3 Code), nie keď píše prácu.

## Čas

- Utorková prax (dochadzka, 7 h) do výkazu nepatrí: je to výkaz nadčasov, preto sa jej čas vynecháva, od príchodu
  až do 14:00, aj keď prišiel skôr alebo odišiel skôr (Karchi 24. 11.: v deň praxe sa ráta až po 14:00).
- Čas počas vyučovania sa ráta len vtedy, keď v ňom robil prácu pre eSYST; škola sama nie (pozri vyššie).
- Ráta sa čas, keď je vo vlákne: číta odpoveď agenta, rozmýšľa a píše (Karchi 20. 11.: to je základ výkazu; „skús
  znova“ sa predtým rátalo ako 15 až 20 min, hoci na x270 trvalo 21 s). Pred jeho správou: od chvíle, keď bola
  odpoveď agenta hotová, alebo od jeho poslednej správy kdekoľvek, najviac 1 min + 1 min na 1000 znakov odpovede +
  1 min na 40 znakov jeho správy, nanajvýš 10 min; po odoslaní 1 min. Kým agent pracuje, to nie je jeho práca.
  Správa vnútri riadku, ktorý už v súbore je (jeho, upravený, zmazaný), ďalší čas nepridá. Zaostrené okno eSYST
  vlákna, Outlooku, Teams či pracovného súboru na x270 sa ráta celé, najviac 20 min naraz. Udalosti do 2 min od
  seba sú jedno sedenie. Správy a vlákna projektov SPOTREX, eSYST…, Hurbanova, eSYSTAK a enex sú firemné
  vždy (`FIREMNE` vo `vykaz.py`, aby ten istý deň vyšiel vždy rovnako); ostatné (Obhajoba práce, bez projektu) posúdi
  Haiku po jednej správe a vlákne. Sedenia sa skladajú len z firemných.
- Vlastná práca popri firemnej (Karchi 21. 11.): čas, keď mal na x270 otvorené vlastné vlákno (nie eSYST), sa zo
  sedenia odráta, aj keby trval pár sekúnd. Do 15 min vlastného vlákna sedenie nepreruší: riadok ostane jeden, B je
  od-do celého sedenia a C čistý čas bez vlastného vlákna (C je preto niekedy menej ako B).
- Presnosť (Karchi 23. 11.): začiatok, koniec aj trvanie sa zaokrúhľujú na pol minúty, nie na 5 min. Čas, ktorý nie
  je na celú minútu, má sekundy: „13:40:30-14:02“, „0.21.30 h“. Sedenie kratšie než 5 min čistého času vypadne
  (konštanty na začiatku `vykaz.py`). Keď sa pravidlá zmenia (`PRAVIDLA`), výkaz svoje nezmenené riadky starších dní
  pri ďalšom behu prepočíta sám; riadky, ktoré Karchi napísal alebo upravil, ostanú.
- Okná Outlook a Teams sa rátajú vždy (firemné účty), T3 okno len s eSYST vláknom (vlákno v projekte Obhajoba práce
  posúdi Haiku ako správu), pracovný súbor, keď titul okna nesie meno dokumentu z `~/Work/projekty` (xlsx, docx,
  pptx, pdf, csv, excalidraw a pod.). Ostatné okná sa neukladajú a nerátajú.
- Či sedí pri počítači, výkaz zatiaľ nevie (na x270 nie je hypridle): zaostrené okno sa preto ráta najviac 20 min.
- Zdroje: T3 na asuse, x270, delle a e540. Rodinný PC (Windows, Codex) sa nečíta, eSYST tam nerobí.

## Súbor

- Stĺpec D (napr. 30 pri 12. 11.) a v septembri F (225) sú jeho poznámky, neviem k čomu; ostávajú bez zmeny pri
  svojom riadku.
- Súbor mesiaca dostáva Andrea Hanková (ekonomika@esyst.sk, ekonomika eSYST): september a október jej poslal z
  administrativa@esyst.sk ako prílohu mailu „Nadčasy Karol Ľupták“ (1. 10.) a „Karol Ľupták pracovné hodiny“
  (31. 10.), posledný alebo prvý deň mesiaca. Výkaz nič neposiela, posiela ho Karchi sám.
