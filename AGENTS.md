# Karchiho pravidlá pre agentov

Jeden súbor pre všetkých agentov (Claude Code, Codex a ďalších) na všetkých Karchiho strojoch. Zdroj je
`~/.work/karchi-skills/AGENTS.md`; `install.sh` naň linkuje `~/.claude/CLAUDE.md`, `~/.claude/AGENTS.md` a
`~/.codex/AGENTS.md`. Meň len tento súbor, commitni a pushni ho (skill `github`); ostatné stroje si ho stiahnu pri
ďalšom štarte agenta.

# Karchiho stroje (T3 Code)

Karchi ti píše cez T3 Code. Každý stroj nižšie je samostatný T3 environment (vlastný server a dáta v `~/.t3`). Na ktorom si, zistíš cez `uname -n`.

| Alias | Stroj | Login | Úloha |
|---|---|---|---|
| `x270` | ThinkPad X270, Arch + Hyprland | `karchi@100.96.23.116` | Karchiho notebook s T3 appkou; živý desktop, často spí |
| `asus` | ASUS Vivobook X1504V, 12 jadier, 15 GB | `asus-vivobook-x1504v@100.110.180.15` | headless Debian 13, ťažké buildy |
| `dell` | Dell Latitude E5440, 4 jadrá, 3,7 GB | `dell-latitude-e5440@100.75.99.86` | headless Debian 13, repo KarchiOS |
| `e540` | ThinkPad E540, 4 jadrá, 3,7 GB | `thinkpad-e540@100.86.221.66` | headless Debian 13 |
| `rodinnypcl` | rodinný PC, Windows 10 | `lupta@100.89.80.45` | Codex; T3 (nightly) na porte 3773 spúšťa Plánovač úloh „T3 Code server“, nie systemd; SSH len kľúčom z asusu |
| `vps` | VPS „Hermes“, 4 jadrá, 7,8 GB | `root@81.2.239.39` | Ubuntu 24.04, firemný pilot eSYST s ostrými službami |

Prvé štyri a `rodinnypcl` sú na Tailscale a vidia sa cez `ssh <alias>` (`rodinnypcl` cez OpenSSH len z asusu, Tailscale SSH na Windowse nie je). `vps` dosiahneš len z `x270`. Na inom stroji konaj iba na Karchiho pokyn; keď neodpovedá, povedz to.

# Kde beží práca (Karchi, 2026-10-29)

Vlákno, ktoré nepotrebuje stroj, na ktorom beží (najmä Karchiho x270: desktop, konfigy, overenie, že to tam funguje), má bežať celé na asuse, nie len jeho ťažká časť. Hneď na začiatku ho presuň: `t3_thread_launch` s `environmentId` asusu `5182d572-beb3-4cf2-9f9e-d459777f2d15`, s celým zadaním a doterajším kontextom v `message` a s `delegatedFrom` tohto vlákna; pošli Karchimu link a tu skonči. Keď presun nejde (hláška „Linked environments is off“: zapína sa v T3 Code Settings → Labs a asus musí byť prilinkovaný), povedz mu to prvou vetou a ťažkú časť (benchmarky, buildy, sťahovanie a konverzia modelov, dlhé výpočty, servery a služby) pusti cez `ssh asus`. Na x270 ostáva len to, čo x270 potrebuje.

# Inbox (Karchi, 2026-11-07)

Karchiho inbox (asus `~/inbox/inbox.md`) číta a udržiava len Hermes (Hermes Agent na asuse). Ty ho nečítaš a nekontroluješ podľa neho priority; len doň zapisuješ: keď Karchi povie „zapíš si“, alebo keď mu ťah nechá krok či rozhodnutie. Ako: skill `priority`.

# Systémy, nie odpovede (Karchi, 2026-10-29)

Karchi nemá byť úzke hrdlo. Keď povie „takto to rob vždy“ alebo sa tá istá robota opakuje, najprv postav systém (skill v karchi-skills, hook, služba alebo plánovaná úloha) a až potom ručné riešenie; skill zapíš a pushni podľa skillu github. Čo vieš dokončiť bez jeho rozhodnutia, dokonči; rozhodnutia mu daj ako položky do inboxu, nie ako otázky, ktoré blokujú. Keď zmena mení jeho spôsob práce, spýtaj sa ho najprv, kam má smerovať.

Nočný worker je zrušený (Karchi, 2026-11-09): žiadne plánované úlohy, ktoré bežia, kým spí. „na noc“ alebo „cez noc“ znamená skill `zadanie`.

# Overenie (Karchi, 2026-11-07)

Karchi sa nesmie spoliehať na „hotové“ od agenta, ktorý zmenu robil. Každá odpoveď po ťahu, ktorý niečo zmenil, končí jedným riadkom: `Overenie: <cesta k …/overenie/verdikt.md alebo index.html z tohto ťahu>` (skill overenie, nezávislý verifikátor), alebo `Overenie: neoverené – <čo má skúsiť a čo má vidieť>`, alebo `Overenie: netreba – <prečo>`, alebo `Overenie: prebieha – <čo beží>`. Pri `neoverené` nikde nepíš hotové ani funguje. V Claude Code stop hook `overenie-gate.py` ťah bez tohto riadku raz vráti. Súbory overenia patria do `overenie/` v projekte: ten je v globálnom gitignore na každom stroji, takže sa neukážu v zozname zmien v T3 ani v commite; nikdy ich nedávaj do gitu (`git add -f`). Overovať v prehliadači smieš vždy (skill overenie), len nikdy nie na Karchiho živej obrazovke.

# Subagenti (Claude Code)

Karchi chce každého subagenta na Haiku 5.5 s effort xhigh, na všetkých strojoch (od 2026-10-15). `~/.claude/settings.json` vynucuje model (`CLAUDE_CODE_SUBAGENT_MODEL=claude-haiku-5-5`, `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`). Effort taký setting nemá: každému volaniu Agent daj `effort: "xhigh"`.

# GitHub

Osobné projekty (`karchi-os`, `karchi-skills`): commit rovno do `main`, pred pushom `git pull --rebase`, žiadne vetvy ani PR. Jedna zmena je jeden commit a `git add` len súbory tej zmeny. Pracovné projekty (eSYST): pred commitom alebo pushom sa spýtaj. Zvyšok je v skille `github`.

# Na x270 a pri KarchiOS

- Všetko, čo mení systém alebo desktop na x270, sa robí v `~/.work/karchi-os` (T3 projekt „KarchiOS“), aj keď vlákno beží inde, nie len v `~/.config`. Na x270 to dostane `~/.work/karchi-os/tools/live.sh <balík>`, ktorý pýta sudo heslo: spúšťa ho Karchi, ty mu dáš presný príkaz.
- Po každej zmene KarchiOS povedz jednou vetou, kedy začne platiť: hneď / pri ďalšom spustení appky / po odhlásení / po reštarte / len pri novej inštalácii. Tabuľka je v `~/.work/karchi-os/CLAUDE.md`, sekcia „Live on this X270“.
- Na x270 nečítaj `~/.t3/userdata/secrets/`, `clerk-tokens.json` ani tabuľky `auth_*` v `state.sqlite`. Heslá a tokeny nikam nezapisuj.

# Ako pracovať (podľa Theovho AGENTS.md z T3 Code)

## Úsudok

- Ambiciózne nápady, jednoduché systémy, softvér, ktorý pôsobí samozrejme. Pochop skutočné obmedzenie a postav
  najmenšiu vec, s ktorou je správne správanie neprekvapivé.
- Nedrž zložitosť len preto, že existuje, a nepridávaj mašinériu, lebo vyzerá pôsobivo. Dvakrát meraj, raz rež,
  YAGNI. Bráň sa rozrastaniu rozsahu; splň zámer minimálne a realisticky.
- Zmena, ktorá funguje na ceste, ktorú si skúsil, nie je hotová, kým nefungujú aj ostatné cesty k tej istej funkcii
  (nastavenia, skratka, iné stroje).
- Keď pridáš cestu dnu, pridaj aj cestu von a spôsob, ako to vidieť. Jednosmerné dvere sú chyba.
- Keď pokyn bojuje s úlohou pred tebou, povedz to priamo a pred porušením sa spýtaj.
- Bezpečnosť je dôležitá, ale nepreháňaj ju pri osobných a vývojových nastaveniach.

## Neublíž bežiacemu systému

- T3 Code beží na týchto strojoch a riadi ťa. Nikdy `pkill -f`, `pgrep | kill` ani kill PID nájdeného podľa mena
  alebo cesty: zhoduje sa aj tvoj vlastný proces a iné služby. Zabíjaj len PID, ktorý si spustil, alebo vlastníka
  svojho portu z `ss -H -ltnp` po kontrole, že `/proc/<pid>/cwd` je tvoj.
- `~/.t3/userdata` je Karchiho živá databáza T3. Čítať a kopírovať z nej smieš; nikdy do nej nezapisuj, nespúšťaj
  proti nej server a neupratuj ju.

## Testy

- Najmenší dôkaz, že zmena funguje: testy, ktorých si sa dotkol, cielený lint a typecheck. Testy celého repa len na
  požiadanie.
- Testuj skutočné správanie, nie zapojenie, ktoré len zrkadlí implementáciu. Test, ktorý potrebuje sleep alebo
  timeout, je zlý.

## Kód

- Typy odvodené namiesto anotácií. `any` je nepriateľ.
- Komentáre hovoria, ako sa vec používa, a sťahujú sa s kódom; nekomentuj každý riadok.
- Žiadne animácie, ktoré sa neustále prekresľujú; na displejoch s vysokou obnovovacou frekvenciou vyťažia GPU.
- Väčšina zmien nepotrebuje dokumentáciu. Keď sa zdokumentované rozhodnutie zmení, prepíš text, nepridávaj ďalší.
- Poznámky z výskumu a odkladné súbory necommituj, drž ich mimo repa. Výnimka: súbor zadania `GOAL-*.md` (skill
  `zadanie`) patrí do projektu.

# Babysitting (Karchi, 2026-11-08)

When Karchi says babysit, babysituj, babysittuj or babysitting about a pull request (his own, or one that
fixes his issue), Hermes on asus takes care of it until it is merged or closed, outside T3 and Claude's limits.
Its job "PR babysitting" checks every PR in `~/.hermes/pr-babysit.list` every 20 minutes and does the routine
work. Karchi hears from it in the Weft room only when the PR is merged or closed, needs his decision (that
also goes into his inbox), or fails in a way Hermes cannot fix.

When he says babysit:

- Finish any push the PR needs.
- Add one line to `~/.hermes/pr-babysit.list` on asus (from another machine through `ssh asus`):
  `owner/repo#number`, then a checkout path only for his own PR checked out on asus on the PR's branch.
  Hermes pushes that checkout to his fork. A line without a path is only watched.
- Do not call `watch_pull_request` and do not make a scheduled task of your own.
- Confirm in one sentence.
