#!/usr/bin/env python3
"""Výkaz práce pre eSYST (duálne štúdium, plat): ~/Work/dual/1.plat/<mesiac>.xlsx na x270.

  vykaz                 zapíše dokončené dni, ktoré ešte zapísané nie sú (vykaz.timer cez deň)
  vykaz ukaz DÁTUM      čo by za deň zapísal teraz (ako znova), nič nemení
  vykaz zapis DÁTUM     zapíše jeden deň (aj už zapísaný: pridá len sedenia, ktoré v súbore ešte nie sú)
  vykaz znova DÁTUM     deň nanovo: svoje nezmenené riadky toho dňa nahradí novým výpočtom (jeho riadky ostanú)
  vykaz vrat [MESIAC]   vráti súbor mesiaca do stavu pred posledným zápisom (záloha)
  vykaz stav            zapísané dni, posledné zálohy, stav zberu okien

Riadok súboru je jedno sedenie: popis | "D.M.RRRR H:MM-H:MM" | "H.MM h" (hodiny.minúty); čas, ktorý nie je na
celú minútu, má aj sekundy ("13:40:30", "1.05.30 h", vždy po pol minúte). Posledný riadok "H.MM h | spolu".
Sedenia skladá z jeho správ v eSYST vláknach T3 na všetkých strojoch (t3-esyst.py) a z času, keď mal na x270
aktívny Outlook, Teams, eSYST vlákno T3 alebo pracovný súbor (okna.py). Čas vo vlastnom vlákne uprostred
sedenia odráta: B je od-do, C čistý čas. Čas na utorkovej praxi (dochadzka) a čas, ktorý už v súbore je, vynechá. Popis napíše Haiku; sedenie, ktoré nie je práca pre eSYST,
vynechá. Pred každou zmenou zálohuje súbor do ~/.local/share/vykaz/zalohy/.
"""
import json, os, re, shutil, subprocess, sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import openpyxl

TZ = ZoneInfo("Europe/Bratislava")
HERE = Path(__file__).resolve().parent
PLAT = Path.home() / "Work/dual/1.plat"
DATA = Path.home() / ".local/share/vykaz"
STAV, ZALOHY, OKNA = DATA / "zapisane.json", DATA / "zalohy", DATA / "okna"
DOCH = Path.home() / "Work/dual/dochadzka/zaznamy"
START = date(2026, 11, 1)  # earlier months were filled by hand
STROJE = ["asus", "dell", "e540"]  # T3 on other machines; x270's own T3 is read locally
CLAUDE = next((p for p in [Path.home() / ".local/share/mise/installs/claude/latest/claude",
                           Path.home() / ".local/bin/claude"] if p.exists()), "claude")
MESIACE = {1: "januar", 2: "februar", 3: "marec", 4: "april", 5: "maj", 6: "jun", 7: "jul", 8: "august",
           9: "September", 10: "oktober", 11: "november", 12: "december"}
# Work is the time he spends in a thread: reading the agent's answer, thinking, typing. Before one of his
# messages that is the time since the answer was ready or since his last message anywhere, at most what reading
# and writing it can take; the agent working afterwards is not his work. Focused windows on x270 count as they are.
CITANIE = 1000   # characters of the agent's answer he reads in a minute
PISANIE = 40     # characters he writes (and thinks over) in a minute
NAD_SPRAVOU = 1, 10  # minutes before one message: at least, at most
PO_SPRAVE = 1    # minutes after sending it
OKNO_MAX = 20    # one focused Outlook/Teams/T3 interval counts at most this long (he may have walked away)
MEDZERA = 2      # events closer than this are one sitting
OSOBNE_MOST = 15  # minutes in his own (non-eSYST) threads that still keep one sitting together; they are subtracted
MIN_SEDENIE = 5  # shorter sittings (their time without his own threads) are dropped
# Projects that are eSYST work as a whole: their messages and threads count without asking the model, so the same
# day always comes out the same. Other projects (Obhajoba práce, No project) are judged message by message.
FIREMNE = ("SPOTREX", "eSYST", "Hurbanova", "partsheet", "eSYSTAK", "enex")
KROK = 30        # seconds: start, end and duration are rounded to the nearest half minute
PRAVIDLA = 4     # raise when the counting changes: days written by older rules are counted again (auto)
ZOBUDENY = range(7, 23)  # the timer writes only by day: no model runs while he sleeps


def subor(d):
    return PLAT / f"{MESIACE[d.month]}.xlsx"


def stav():
    return json.loads(STAV.read_text()) if STAV.exists() else {}


def uloz_stav(s):
    DATA.mkdir(parents=True, exist_ok=True)
    STAV.write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n")


def hm(t):
    return f"{t.hour}:{t.minute:02d}"


def hms(t):
    """'13:40', or '13:40:30' when it is not a whole minute."""
    return hm(t) + (f":{t.second:02d}" if t.second else "")


def trvanie(sekundy):
    """'1.05 h', or '1.05.30 h' with the seconds when it is not whole minutes."""
    h, m, s = sekundy // 3600, sekundy // 60 % 60, sekundy % 60
    return f"{h}.{m:02d}" + (f".{s:02d}" if s else "") + " h"


def sekundy_bunky(v):
    """'1.3h', '2.09h', '2.30 h', '1.05.30 h' or 1.3 -> seconds; after the dot minutes (1.3 = 1:30), then seconds."""
    m = re.match(r"\s*(\d+)(?:[.,](\d{1,2})(?:[.:](\d{1,2}))?)?", str(v or ""))
    if not m:
        return 0
    return int(m[1]) * 3600 + int((m[2] or "0").ljust(2, "0")) * 60 + int(m[3] or 0)


# --- sources ----------------------------------------------------------------

def t3_spravy(d):
    src = (HERE / "t3-esyst.py").read_text()
    out = []
    jobs = [("x270", [sys.executable, "-I", str(HERE / "t3-esyst.py"), str(d), str(d)], None)]
    jobs += [(m, ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", m, "python3", "-", str(d), str(d)], src)
             for m in STROJE]
    procs = [(m, subprocess.Popen(cmd, stdin=subprocess.PIPE if s else subprocess.DEVNULL, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True)) for m, cmd, s in jobs]
    chyby = []
    for (m, p), (_, _, s) in zip(procs, jobs):
        try:
            so, se = p.communicate(s, timeout=120)
            rows = json.loads(so)
        except (ValueError, subprocess.TimeoutExpired):
            p.kill()
            chyby.append(m)
            continue
        for r in rows:
            t = datetime.fromisoformat(r["ts"].replace("Z", "+00:00")).astimezone(TZ)
            if t.date() in (d, d - timedelta(days=1)):  # the evening before only bounds work after midnight
                out.append({"t": t, "stroj": m, **r})
    return sorted(out, key=lambda r: r["t"]), chyby


def okna(d):
    """Focus intervals of Outlook, Teams, T3 threads and work files that day: [(start, end, druh, titul)]."""
    def citaj(x):
        f = OKNA / f"{x}.tsv"
        rows = []
        for line in (f.read_text().splitlines() if f.exists() else []):
            p = line.split("\t")
            if len(p) >= 2:
                rows.append((datetime.fromtimestamp(int(p[0]), TZ), p[1], p[2] if len(p) > 2 else ""))
        return rows
    # a focus that runs over midnight: the day before's last line starts it, the next day's first line ends it
    rows = citaj(d - timedelta(days=1))[-1:] + citaj(d) + citaj(d + timedelta(days=1))[:1]
    zac = datetime.combine(d, datetime.min.time(), TZ)
    kon = zac + timedelta(days=1)
    out = []
    for (t, k, title), nxt in zip(rows, rows[1:] + [None]):
        if k == "-":
            continue
        end = min(nxt[0] if nxt else t, t + timedelta(minutes=OKNO_MAX), kon)
        t = max(t, zac)
        if end > t:  # even a few seconds: the sitting minimum decides what counts
            out.append((t, end, k, title))
    return out


def prax(d):
    """The Tuesday practice interval from dochadzka, which is not paid work."""
    f = DOCH / f"{d}.json"
    if not f.exists():
        return None
    z = json.loads(f.read_text())
    if "od" not in z:
        return None
    c = lambda s: datetime.combine(d, datetime.strptime(s, "%H:%M").time(), TZ)
    return c(z["od"]), c(z["do"])


CAS = re.compile(r"\s*(\d+)\.(\d+)\.(\d{4})\s+(\d+):(\d+)(?::(\d+))?\s*-\s*(\d+):(\d+)(?::(\d+))?")


def interval(cas, d):
    """'19.11.2026 13:40-13:50' or '19.11.2026 13:40:30-13:50' -> (start, end) when it is day d, else None."""
    m = CAS.match(str(cas or ""))
    if not (m and date(int(m[3]), int(m[2]), int(m[1])) == d):
        return None
    a = datetime(d.year, d.month, d.day, int(m[4]), int(m[5]), int(m[6] or 0), tzinfo=TZ)
    b = datetime(d.year, d.month, d.day, int(m[7]), int(m[8]), int(m[9] or 0), tzinfo=TZ)
    return a, b if b > a else b + timedelta(days=1)


def v_subore(ws, d):
    """Intervals already in the sheet for day d (his own rows and earlier writes)."""
    return [iv for r in ws.iter_rows(min_col=2, max_col=2) if (iv := interval(r[0].value, d))]


# --- sittings ---------------------------------------------------------------

def odober(iv, dier):
    """iv minus each interval in dier."""
    for a, b in dier:
        nove = []
        for s, e, x in iv:
            if e <= a or s >= b:
                nove.append((s, e, x))
                continue
            if s < a:
                nove.append((s, a, x))
            if e > b:
                nove.append((b, e, x))
        iv = nove
    return iv


def pred_spravou(r, vsetky):
    """When the work on message r began: reading and writing it, not before the answer it replies to or his
    previous message anywhere (on any machine)."""
    t = r["t"]
    m = NAD_SPRAVOU[0] + r.get("odpoved", 0) / CITANIE + r.get("dlzka", len(r["text"])) / PISANIE
    od = t - timedelta(minutes=min(NAD_SPRAVOU[1], m))
    hore = [x["t"] for x in vsetky if x["t"] < t]
    if r.get("pripravene"):
        hore.append(datetime.fromisoformat(r["pripravene"].replace("Z", "+00:00")).astimezone(TZ))
    hore = [h for h in hore if h < t]
    return max([od] + hore)


def zaokruhli(t):
    """Nearest half minute (KROK)."""
    h = t.replace(minute=0, second=0, microsecond=0)
    return h + timedelta(seconds=KROK * int(((t - h).total_seconds() + KROK / 2) // KROK))


def prekryv(a, b, ivs):
    """Seconds of the intervals ivs inside a..b."""
    return sum(max(0.0, (min(b, e) - max(a, s)).total_seconds()) for s, e in ivs)


def sedenia(d, spravy, okn, vynechat, vsetky=None, osobne=()):
    """Sittings from his eSYST messages and focused work windows. osobne: when one of his own threads had focus;
    that time keeps a sitting together (up to OSOBNE_MOST) but is subtracted from it ("sek")."""
    vsetky = spravy if vsetky is None else vsetky
    iv = [(pred_spravou(r, vsetky), r["t"] + timedelta(minutes=PO_SPRAVE), ("sprava", r)) for r in spravy]
    iv += [(s, e, ("okno", (k, title))) for s, e, k, title in okn]
    iv.sort(key=lambda x: x[0])
    spojene = []
    for s, e, x in iv:
        if spojene:
            medzera = (s - spojene[-1]["do"]).total_seconds()
            vlastne = prekryv(spojene[-1]["do"], s, osobne)
            if medzera - vlastne <= MEDZERA * 60 and vlastne <= OSOBNE_MOST * 60:
                spojene[-1]["do"] = max(spojene[-1]["do"], e)
                spojene[-1]["veci"].append(x)
                continue
        spojene.append({"od": s, "do": e, "veci": [x]})
    out = []
    for sd in spojene:
        if (sd["do"] - sd["od"]).total_seconds() - prekryv(sd["od"], sd["do"], osobne) < MIN_SEDENIE * 60:
            continue  # before rounding, so a quick reply never grows past the minimum by rounding
        # round to the nearest half minute, then cut out practice and what the sheet already has
        a, b = zaokruhli(sd["od"]), zaokruhli(sd["do"])
        a = max(a, datetime.combine(d, datetime.min.time(), TZ))
        b = min(b, datetime.combine(d + timedelta(days=1), datetime.min.time(), TZ))
        for s, e, _ in odober([(a, b, None)], vynechat):
            sek = (e - s).total_seconds() - prekryv(s, e, osobne)
            sek = KROK * int((sek + KROK / 2) // KROK)
            if sek < MIN_SEDENIE * 60:
                continue  # what is left of it beside rows already in the sheet
            out.append({"od": s, "do": e, "sek": sek, "veci": sd["veci"]})
    return out


def podklad(sd):
    lines = []
    for kind, x in sd["veci"]:
        if kind == "sprava":
            lines.append(f"{hm(x['t'])} [{x['projekt']} / {x['vlakno']}] {x['text'][:220]}")
        else:
            k, title = x
            lines.append(f"(okno {k}: {title[:80]})")
    return lines[:40]


PRIKLADY = """Implementovanie účtovacej jednotky do spotrexu
Prihlasovanie na VPN a CRS 40
Pripájanie na CRS 40 do KBF
Automatizovanie Spotrexu, pripravovanie na škálovanie, MQTT konfigurácia
Odpovedanie na nočné úlohy
Spotrex finálne úpravy pred zajtrajšou ponukou a deployom
Balancovanie hardwaru a správneho modelu pre firemné AI
Vytváranie softvérového prototypu na VPS pre testovanie"""


def ciel():
    """The "Čo sa ráta" section of predpoklady.md: what counts as eSYST work, as he can correct it."""
    t = (HERE / "predpoklady.md").read_text()
    return t.split("## Čo sa ráta", 1)[1].split("\n## ", 1)[0].strip()


def haiku(prompt, n):
    """Numbered answers 1..n from Haiku; any gap, empty answer or error stops the run before anything is written."""
    try:
        r = subprocess.run([str(CLAUDE), "-p", "--model", "claude-haiku-5-5", prompt],
                           capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        sys.exit(f"Haiku zlyhal: {e}")
    got = {}
    for line in r.stdout.splitlines():
        m = re.match(r"\s*(\d+)\s*[:.)]\s*(\S.*)", line)
        if m:
            got[int(m[1])] = m[2].strip().rstrip(".")
    if r.returncode != 0 or any(not got.get(i) for i in range(1, n + 1)):
        if re.search(r"login|log in|auth|sign-in|setup-token", r.stdout + r.stderr, re.I):
            notify("Výkaz nezapisuje: Claude na x270 nie je prihlásený (claude setup-token)")
        sys.exit(f"Haiku zlyhal ({r.returncode}): {r.stdout[:300]} {r.stderr[:300]}")
    return [got[i] for i in range(1, n + 1)]


def firemne(d, spravy, vlakna=()):
    """His messages that are eSYST work, judged one by one, so that an unrelated thread in between does not make
    one long paid sitting out of them; and which of the T3 threads he had focused on x270 ("project / thread")
    are eSYST work. Returns (messages, set of thread titles)."""
    isto = [r for r in spravy if r["projekt"].startswith(FIREMNE)]
    spravy = [r for r in spravy if not r["projekt"].startswith(FIREMNE)]
    isto_v = {v for v in vlakna if v.startswith(FIREMNE)}
    vlakna = sorted(set(vlakna) - isto_v)
    if not spravy and not vlakna:
        return isto, isto_v
    zoznam = [f"{hm(r['t'])} [{r['projekt']} / {r['vlakno']}] {r['text'][:220]}" for r in spravy]
    zoznam += [f"(otvorené vlákno, bez správy) [{v}]" for v in vlakna]
    n = len(zoznam)
    prompt = f"""Karol pracuje popri škole pre firmu eSYST s.r.o. a vedie si výkaz odpracovaných hodín. Pri každej jeho správe AI agentovi z {d.day}.{d.month}.{d.year} a pri každom vlákne, ktoré mal otvorené, rozhodni, či je to práca pre eSYST.

{ciel()}

Odpovedz presne {n} riadkami v tvare „ČÍSLO: A“ (práca pre eSYST) alebo „ČÍSLO: N“ (nie), ničím iným. Krátka správa bez obsahu („ok“, „pokračuj“, „/compact“) patrí k vláknu, v ktorom je.

""" + "\n".join(f"{i + 1}: {z}" for i, z in enumerate(zoznam))
    ano = [a.upper().startswith("A") for a in haiku(prompt, n)]
    ano_s = [r for r, a in zip(spravy, ano) if a]
    return sorted(isto + ano_s, key=lambda r: r["t"]), isto_v | {v for v, a in zip(vlakna, ano[len(spravy):]) if a}


def popisy(d, sed):
    """One line per sitting from Haiku, '' for a sitting that is not eSYST work."""
    if not sed:
        return []
    bloky = "\n\n".join(f"SEDENIE {i + 1} ({hm(s['od'])}-{hm(s['do'])}):\n" + "\n".join(podklad(s))
                        for i, s in enumerate(sed))
    prompt = f"""Karol pracuje popri škole (duálne štúdium) pre firmu eSYST s.r.o. v Žiline a vedie si výkaz odpracovaných hodín za plat. Za deň {d.day}.{d.month}.{d.year} máš sedenia: jeho správy AI agentom v T3 Code (čas, [projekt / vlákno], text) a okná, ktoré mal otvorené (Outlook, Teams, vlákna T3).

{ciel()}

Pre každé sedenie napíš jeden riadok do stĺpca popisu: podstatné mená zo slovies, po slovensky, vecne, najviac 12 slov, bez bodky na konci, v štýle týchto starších riadkov:
{PRIKLADY}

Všetko v sedeniach už je firemná práca (osobné vlákna sú vynechané), takže každé sedenie dostane popis. Odpovedz presne {len(sed)} riadkami v tvare „ČÍSLO: text“ a ničím iným.

{bloky}"""
    return ["" if t.upper().startswith("NIC") else t for t in haiku(prompt, len(sed))]


def navrh(d, ws, zmazane=()):
    """zmazane: times of rows vykaz wrote and he deleted; that time is not proposed again."""
    spravy, chyby = t3_spravy(d)
    zm = [iv for c in zmazane if (iv := interval(c, d))]
    vynechat = (v_subore(ws, d) if ws is not None else []) + zm
    p = prax(d)
    if p:
        vynechat.append(p)
    # a message inside a row already in the sheet (his, or one he edited) is counted there, and one inside a row he
    # deleted is work he rejected: neither adds time around it, even where newer rules would start it earlier
    dna = [r for r in spravy if r["t"].date() == d and r.get("esyst", True)
           and not any(a <= r["t"] <= b for a, b in vynechat)]
    okn = okna(d)
    dna_spravy, vlakna = firemne(d, dna, [t for _, _, k, t in okn if k == "t3"])
    # a focused thread that is not eSYST work is his own: subtracted from the sitting around it
    osobne = [(s, e) for s, e, k, t in okn if k == "t3" and t not in vlakna]
    praca = [o for o in okn if o[2] != "t3" or o[3] in vlakna]
    sed = sedenia(d, dna_spravy, praca, vynechat, spravy, osobne)
    txt = popisy(d, sed)
    rows = [(t, s) for t, s in zip(txt, sed) if t]
    return [{"popis": t, "cas": f"{d.day}.{d.month}.{d.year} {hms(s['od'])}-{hms(s['do'])}",
             "sek": int(s["sek"])} for t, s in rows], chyby, len(sed)


# --- the sheet --------------------------------------------------------------

def otvoreny(f):
    return any((f.parent / n).exists() for n in (f".~lock.{f.name}#", f"~${f.name}"))


def nacitaj(f):
    if f.exists():
        return openpyxl.load_workbook(f)
    # a new month: the same plain layout as november.xlsx
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 95, 22
    return wb


def zapis_riadky(f, wb, nove):
    """Insert rows in date order before the "spolu" row and recount spolu."""
    ws = wb.active
    spolu = next((r[0].row for r in ws.iter_rows(min_col=4, max_col=4) if str(r[0].value or "").strip() == "spolu"), None)
    koniec = (spolu or ws.max_row + 1) - 1
    navyse = [ws.cell(spolu, c).value for c in (5, 6)] if spolu else [None, None]  # his notes next to spolu
    riadky = []
    for r in range(1, koniec + 1):
        vals = [ws.cell(r, c).value for c in range(1, 7)]
        if any(v is not None for v in vals):
            riadky.append(vals)
    kluc, out = None, []
    for v in riadky:  # rows without a date stay right after the row they followed
        m = re.match(r"\s*(\d+)\.(\d+)\.(\d{4})\s+(\d+):(\d+)", str(v[1] or ""))
        k = (date(int(m[3]), int(m[2]), int(m[1])), int(m[4]), int(m[5])) if m else kluc or (date.min, 0, 0)
        kluc = k
        out.append((k, len(out), v))
    for n in nove:
        m = re.match(r"(\d+)\.(\d+)\.(\d{4})\s+(\d+):(\d+)", n["cas"])
        k = (date(int(m[3]), int(m[2]), int(m[1])), int(m[4]), int(m[5]))
        out.append((k, len(out), [n["popis"], n["cas"], trvanie(n["sek"]), None, None, None]))
    out.sort(key=lambda x: (x[0], x[1]))
    for r in range(1, max(ws.max_row, len(out) + 2) + 1):
        for c in range(1, 7):
            ws.cell(r, c).value = None
    for i, (_, _, v) in enumerate(out, 1):
        for c, x in enumerate(v, 1):
            ws.cell(i, c).value = x
    # spolu keeps its old place when the rows still fit above it (row 9 in his files)
    rs = max(spolu or 0, len(out) + 1)
    celkom = sum(sekundy_bunky(v[2]) for _, _, v in out)
    ws.cell(rs, 3).value, ws.cell(rs, 4).value = trvanie(celkom), "spolu"
    ws.cell(rs, 5).value, ws.cell(rs, 6).value = navyse
    tmp = f.with_name(f".{f.name}.tmp")
    wb.save(tmp)
    os.replace(tmp, f)
    return celkom


def zaloha(f):
    if not f.exists():
        return None
    ZALOHY.mkdir(parents=True, exist_ok=True)
    z = ZALOHY / f"{f.stem}-{datetime.now():%Y%m%d-%H%M%S-%f}.xlsx"
    shutil.copy2(f, z)
    return z


def notify(text):
    # like dochadzka: straight to the notification daemon, notify-send breaks under T3's LD_LIBRARY_PATH
    try:
        subprocess.run(["gdbus", "call", "--session", "--dest", "org.freedesktop.Notifications", "--object-path",
                        "/org/freedesktop/Notifications", "--method", "org.freedesktop.Notifications.Notify",
                        "Výkaz", "0", "", "Výkaz eSYST", text, "[]", "{}", "0"], check=False, capture_output=True)
    except OSError:
        pass
    print(text)


def novy_den(v):
    """Not written yet (vrat may leave only the rows he deleted)."""
    return v is None or (isinstance(v, dict) and "riadky" not in v)


def spolu_sedi(ws):
    """The "spolu" row holds the sum of the rows above it (or there is none yet)."""
    rs = next((r for r in range(1, ws.max_row + 1) if str(ws.cell(r, 4).value or "").strip() == "spolu"), None)
    if rs is None:
        return True
    return sekundy_bunky(ws.cell(rs, 3).value) == sum(sekundy_bunky(ws.cell(r, 3).value) for r in range(1, rs))


def svoje_riadky(d):
    v = stav().get("dni", {}).get(str(d))
    return list(v.get("riadky", []) if isinstance(v, dict) else v or [])


def odober_svoje(ws, d):
    """Clear the rows vykaz wrote for day d exactly as it wrote them (text, time, duration, no note in D-F);
    a row he wrote or touched in any way stays. Returns the keys cleared."""
    svoje, prec = Counter(svoje_riadky(d)), []
    v = stav().get("dni", {}).get(str(d))
    zapisane = v.get("trvania", {}) if isinstance(v, dict) else {}
    for r in range(1, ws.max_row + 1):
        a, b, c = (ws.cell(r, i).value for i in (1, 2, 3))
        iv = interval(b, d) if CAS.fullmatch(str(b or "").strip()) else None
        if not (a and iv and svoje[f"{b} {a}"] > 0) or any(ws.cell(r, i).value is not None for i in (4, 5, 6)):
            continue
        # the duration it wrote: stored since it subtracts his own threads, else the whole time from B
        cakane = zapisane.get(f"{b} {a}") or trvanie(int((iv[1] - iv[0]).total_seconds()))
        if str(c or "").strip() != cakane:
            continue  # he corrected the duration
        for i in range(1, 7):
            ws.cell(r, i).value = None
        svoje[f"{b} {a}"] -= 1  # his copy of a row it wrote once stays
        prec.append(f"{b} {a}")
    return prec


def zapis_den(d, sucho=False, aj_bez=False, znova=False):
    f = subor(d)
    if otvoreny(f) and not sucho:
        print(f"{f.name} je otvorený, {d} zapíšem nabudúce")
        return None
    pred = f.stat().st_mtime_ns if f.exists() else None
    wb = nacitaj(f)
    # rows it wrote that are gone from the sheet he deleted: that time is not his work, never propose it again
    # (a row whose time is still there is his edit, not a deletion)
    casy = {str(wb.active.cell(r, 2).value).strip() for r in range(1, wb.active.max_row + 1)}
    stary = stav().get("dni", {}).get(str(d))
    zmazane = list(stary.get("zmazane", [])) if isinstance(stary, dict) else []
    zmazane += [c for c in (" ".join(k.split(" ", 2)[:2]) for k in svoje_riadky(d)) if c not in casy]
    spolu_ok = spolu_sedi(wb.active)
    zmazane = sorted(set(zmazane))
    prec = odober_svoje(wb.active, d) if znova or sucho else []  # ukaz shows what znova would write
    nove, chyby, n = navrh(d, wb.active, zmazane)
    if sucho:
        for r in nove:
            print(f"{r['cas']:30} {trvanie(r['sek']):11} {r['popis']}")
        print(f"({n} sedení, {len(nove)} firemných{'; nedostupné: ' + ', '.join(chyby) if chyby else ''})")
        return nove
    if "asus" in chyby or "x270" in chyby or (chyby and not aj_bez):
        # a sleeping machine would lose its part of the day: try again next run
        print(f"{d}: nedostupné {', '.join(chyby)}, skúsim nabudúce")
        return None
    if otvoreny(f) or (f.stat().st_mtime_ns if f.exists() else None) != pred:
        # he opened or saved the file while the model was writing: never write over his edit
        print(f"{f.name} sa medzitým otvoril alebo zmenil, {d} zapíšem nabudúce")
        return None
    s = stav()
    kluce = [r["cas"] + " " + r["popis"] for r in nove]
    z = None
    if sorted(kluce) == sorted(prec) and spolu_ok:
        nove = []  # znova came to the same rows: the file stays as it is
    elif nove or prec or not spolu_ok:
        z = zaloha(f)
        celkom = zapis_riadky(f, wb, nove)
        print(f"{d}: {'-' + str(len(prec)) + ' starých, ' if prec else ''}+{len(nove)} riadkov, "
              f"spolu {trvanie(celkom)} (záloha {z})")
    trvania = {k: trvanie(r["sek"]) for k, r in zip(kluce, nove)}
    if znova or novy_den(stary):
        # its rows now are what it just wrote; a row it could not replace because he changed it is his
        dni = {"riadky": kluce, "pravidla": PRAVIDLA, "trvania": trvania}
    else:
        # zapis adds to a day: the older rows stay its own and keep the rules they were counted by
        dni = {"riadky": svoje_riadky(d) + kluce,
               "pravidla": stary.get("pravidla", 1) if isinstance(stary, dict) else 1,
               "trvania": {**(stary.get("trvania", {}) if isinstance(stary, dict) else {}), **trvania}}
    dni["zaloha"] = z.name if z else (stary.get("zaloha") if isinstance(stary, dict) else None)
    if z and not novy_den(stary):
        dni["pred"] = stary if isinstance(stary, dict) else {"riadky": stary}  # for vrat
    elif not z and isinstance(stary, dict) and "pred" in stary:
        dni["pred"] = stary["pred"]  # nothing written: the last write's undo stays
    if zmazane:
        dni["zmazane"] = zmazane
    s.setdefault("dni", {})[str(d)] = dni
    uloz_stav(s)
    return nove


def auto():
    if datetime.now(TZ).hour not in ZOBUDENY:
        return
    hotove = stav().get("dni", {})
    d, today = START, datetime.now(TZ).date()
    pridane = 0
    while d < today and datetime.now(TZ).hour in ZOBUDENY:
        v = hotove.get(str(d))
        stare = not novy_den(v) and (not isinstance(v, dict) or v.get("pravidla", 1) != PRAVIDLA)
        if novy_den(v) or stare:
            # after two days dell or e540 asleep is left out, so the day gets written; without asus
            # (most of his threads) or the network nothing is written and the next run tries again
            # counting a written day again waits for every machine, so no machine's rows get lost
            r = zapis_den(d, aj_bez=not stare and d < today - timedelta(days=2), znova=stare)
            if r is None and stare:
                d += timedelta(days=1)
                continue  # an older day that cannot be counted again now does not hold up the new ones
            if r is None:
                break
            pridane += len(r)
        d += timedelta(days=1)
    if pridane:
        notify(f"Výkaz: pridal som {pridane} riadkov do {subor(today - timedelta(days=1)).name}")


def vrat(mesiac=None):
    """Back to the file before the last write; that write's days count as not written again."""
    f = PLAT / f"{mesiac}.xlsx" if mesiac else subor(datetime.now(TZ).date() - timedelta(days=1))
    z = sorted(p for p in ZALOHY.glob(f"{f.stem}-2*.xlsx"))
    if not z:
        sys.exit(f"žiadna záloha {f.name}")
    src = z[-1]
    ZALOHY.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, ZALOHY / f"pred-vratenim-{f.stem}-{datetime.now():%Y%m%d-%H%M%S-%f}.xlsx")
    shutil.copy2(src, f)
    s = stav()
    for k, v in list(s.get("dni", {}).items()):
        zal = v.get("zaloha") if isinstance(v, dict) else None
        if not (zal and zal.startswith(f"{f.stem}-2") and zal >= src.name):  # only this month's writes
            continue
        # the day as it was before that write; rows he deleted stay deleted
        pred = dict(v.get("pred") or {})
        zm = sorted(set(pred.get("zmazane", [])) | set(v.get("zmazane", [])))
        if zm:
            pred["zmazane"] = zm
        if pred:
            s["dni"][k] = pred
        else:
            del s["dni"][k]
    src.rename(src.with_name("vratene-" + src.name))  # the next vrat goes one write further back
    uloz_stav(s)
    print(f"{f} <- {src}")


def stav_vypis():
    s = stav().get("dni", {})
    for d, v in sorted(s.items())[-14:]:
        rows = v.get("riadky", []) if isinstance(v, dict) else v
        print(d, f"{len(rows)} riadkov")
        for r in rows:
            print("   ", r)
    print("zálohy:", *[p.name for p in sorted(ZALOHY.glob("*.xlsx"))[-5:]])
    dnes = OKNA / f"{date.today()}.tsv"
    print("okná dnes:", sum(1 for _ in open(dnes)) if dnes.exists() else 0, "zmien")
    subprocess.run(["systemctl", "--user", "--no-pager", "status", "vykaz-okna.service", "vykaz.timer"],
                   check=False)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        auto()
    elif a[0] == "ukaz":
        zapis_den(date.fromisoformat(a[1]), sucho=True)
    elif a[0] == "zapis":
        zapis_den(date.fromisoformat(a[1]))
    elif a[0] == "znova":
        zapis_den(date.fromisoformat(a[1]), znova=True)
    elif a[0] == "vrat":
        vrat(*a[1:2])
    elif a[0] == "stav":
        stav_vypis()
    else:
        sys.exit(__doc__)
