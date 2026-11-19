#!/usr/bin/env python3
"""Výkaz práce pre eSYST (duálne štúdium, plat): ~/Work/dual/1.plat/<mesiac>.xlsx na x270.

  vykaz                 zapíše dokončené dni, ktoré ešte zapísané nie sú (vykaz.timer cez deň)
  vykaz ukaz DÁTUM      čo by zapísal za deň, nič nemení
  vykaz zapis DÁTUM     zapíše jeden deň (aj už zapísaný: pridá len sedenia, ktoré v súbore ešte nie sú)
  vykaz vrat [MESIAC]   vráti súbor mesiaca do stavu pred posledným zápisom (záloha)
  vykaz stav            zapísané dni, posledné zálohy, stav zberu okien

Riadok súboru je jedno sedenie: popis | "D.M.RRRR H:MM-H:MM" | "H.MM h" (hodiny.minúty); posledný riadok
"H.MM h | spolu". Sedenia skladá z jeho správ v eSYST vláknach T3 na všetkých strojoch (t3-esyst.py) a z času,
keď mal na x270 aktívny Outlook, Teams alebo eSYST vlákno T3 (okna.py). Čas na utorkovej praxi
(dochadzka) a čas, ktorý už v súbore je, vynechá. Popis napíše Haiku; sedenie, ktoré nie je práca pre eSYST,
vynechá. Pred každou zmenou zálohuje súbor do ~/.local/share/vykaz/zalohy/.
"""
import json, os, re, shutil, subprocess, sys
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
SPRAVA = 5, 10   # minutes of work before and after one of his messages
OKNO_MAX = 20    # one focused Outlook/Teams/T3 interval counts at most this long (he may have walked away)
MEDZERA = 20     # events closer than this are one sitting
MIN_SEDENIE = 10  # shorter sittings are dropped
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


def trvanie(minuty):
    return f"{minuty // 60}.{minuty % 60:02d} h"


def minuty_bunky(v):
    """'1.3h', '2.09h', '2.30 h' or 1.3 -> minutes; the part after the dot is minutes (1.3 = 1:30)."""
    m = re.match(r"\s*(\d+)(?:[.,](\d{1,2}))?", str(v or ""))
    if not m:
        return 0
    return int(m[1]) * 60 + int((m[2] or "0").ljust(2, "0"))


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
            if t.date() == d:
                out.append({"t": t, "stroj": m, **r})
    return sorted(out, key=lambda r: r["t"]), chyby


def okna(d):
    """Focus intervals of Outlook/Teams/eSYST T3 that day: [(start, end, druh, titul)]."""
    f = OKNA / f"{d}.tsv"
    if not f.exists():
        return []
    rows = []
    for line in f.read_text().splitlines():
        p = line.split("\t")
        if len(p) >= 2:
            rows.append((datetime.fromtimestamp(int(p[0]), TZ), p[1], p[2] if len(p) > 2 else ""))
    out = []
    for (t, k, title), nxt in zip(rows, rows[1:] + [None]):
        if k == "-":
            continue
        end = min(nxt[0] if nxt else t, t + timedelta(minutes=OKNO_MAX))
        if (end - t).total_seconds() >= 60:
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


def v_subore(ws, d):
    """Intervals already in the sheet for day d (his own rows and earlier writes)."""
    out = []
    for r in ws.iter_rows(min_col=2, max_col=2):
        m = re.match(r"\s*(\d+)\.(\d+)\.(\d{4})\s+(\d+):(\d+)\s*-\s*(\d+):(\d+)", str(r[0].value or ""))
        if m and date(int(m[3]), int(m[2]), int(m[1])) == d:
            a = datetime(d.year, d.month, d.day, int(m[4]), int(m[5]), tzinfo=TZ)
            b = datetime(d.year, d.month, d.day, int(m[6]), int(m[7]), tzinfo=TZ)
            out.append((a, b if b > a else b + timedelta(days=1)))
    return out


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


def sedenia(d, spravy, okn, vynechat):
    iv = [(r["t"] - timedelta(minutes=SPRAVA[0]), r["t"] + timedelta(minutes=SPRAVA[1]), ("sprava", r)) for r in spravy]
    iv += [(s, e, ("okno", (k, title))) for s, e, k, title in okn]
    iv.sort(key=lambda x: x[0])
    spojene = []
    for s, e, x in iv:
        if spojene and s - spojene[-1]["do"] <= timedelta(minutes=MEDZERA):
            spojene[-1]["do"] = max(spojene[-1]["do"], e)
            spojene[-1]["veci"].append(x)
        else:
            spojene.append({"od": s, "do": e, "veci": [x]})
    out = []
    for sd in spojene:
        # round to 5 minutes outward, then cut out practice and what the sheet already has
        a = sd["od"].replace(minute=sd["od"].minute // 5 * 5, second=0, microsecond=0)
        b = sd["do"] + timedelta(minutes=(-sd["do"].minute) % 5)
        b = b.replace(second=0, microsecond=0)
        a = max(a, datetime.combine(d, datetime.min.time(), TZ))
        b = min(b, datetime.combine(d, datetime.max.time(), TZ).replace(second=0, microsecond=0))
        for s, e, _ in odober([(a, b, None)], vynechat):
            if (e - s).total_seconds() / 60 >= MIN_SEDENIE:
                out.append({"od": s, "do": e, "veci": sd["veci"]})
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


def popisy(d, sed):
    """One line per sitting from Haiku, '' for a sitting that is not eSYST work."""
    if not sed:
        return []
    bloky = "\n\n".join(f"SEDENIE {i + 1} ({hm(s['od'])}-{hm(s['do'])}):\n" + "\n".join(podklad(s))
                        for i, s in enumerate(sed))
    prompt = f"""Karol pracuje popri škole (duálne štúdium) pre firmu eSYST s.r.o. v Žiline a vedie si výkaz odpracovaných hodín za plat. Za deň {d.day}.{d.month}.{d.year} máš sedenia: jeho správy AI agentom v T3 Code (čas, [projekt / vlákno], text) a okná, ktoré mal otvorené (Outlook, Teams, vlákna T3).

Firemná práca: SPOTREX (systém na odpočty meračov tepla a vody pre eSYST, stanice CRS 40, MQTT, VPS, účtovanie), firemný AI asistent a AI nástroje pre zamestnancov (eSYSŤák, Hermes, firemný T3 Code, tímové účty Claude, lokálne AI, firemné počítače, heslá, GitHub organizácia eSYST), zákazky eSYST (napr. Hurbanova), EUCF, firemné e-maily a Teams. Nie je firemná práca: vlastný notebook a jeho vzhľad, osobné aplikácie (Weft, Učenie, kalendár), škola a samotné písanie školskej práce (SOČ, obhajoba), hudba, open source.

Pre každé sedenie napíš jeden riadok do stĺpca popisu: podstatné mená zo slovies, po slovensky, vecne, najviac 12 slov, bez bodky na konci, v štýle týchto starších riadkov:
{PRIKLADY}

Ak sedenie nie je firemná práca, napíš NIC. Odpovedz presne {len(sed)} riadkami v tvare „ČÍSLO: text“ a ničím iným.

{bloky}"""
    try:
        r = subprocess.run([str(CLAUDE), "-p", "--model", "claude-haiku-5-5", prompt],
                           capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        sys.exit(f"popis sa nepodaril: {e}")
    got = {}
    for line in r.stdout.splitlines():
        m = re.match(r"\s*(\d+)\s*[:.)]\s*(.+)", line)
        if m:
            got[int(m[1])] = m[2].strip().rstrip(".")
    if r.returncode != 0 or len(got) != len(sed):
        sys.exit(f"popis sa nepodaril ({r.returncode}): {r.stdout[:300]} {r.stderr[:300]}")
    return ["" if got[i + 1].upper().startswith("NIC") else got[i + 1] for i in range(len(sed))]


def navrh(d, ws):
    spravy, chyby = t3_spravy(d)
    vynechat = v_subore(ws, d) if ws is not None else []
    p = prax(d)
    if p:
        vynechat.append(p)
    sed = sedenia(d, spravy, okna(d), vynechat)
    txt = popisy(d, sed)
    rows = [(t, s) for t, s in zip(txt, sed) if t]
    return [{"popis": t, "cas": f"{d.day}.{d.month}.{d.year} {hm(s['od'])}-{hm(s['do'])}",
             "min": int((s["do"] - s["od"]).total_seconds() // 60)} for t, s in rows], chyby, len(sed)


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
        out.append((k, len(out), [n["popis"], n["cas"], trvanie(n["min"]), None, None, None]))
    out.sort(key=lambda x: (x[0], x[1]))
    for r in range(1, max(ws.max_row, len(out) + 2) + 1):
        for c in range(1, 7):
            ws.cell(r, c).value = None
    for i, (_, _, v) in enumerate(out, 1):
        for c, x in enumerate(v, 1):
            ws.cell(i, c).value = x
    # spolu keeps its old place when the rows still fit above it (row 9 in his files)
    rs = max(spolu or 0, len(out) + 1)
    celkom = sum(minuty_bunky(v[2]) for _, _, v in out)
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
    z = ZALOHY / f"{f.stem}-{datetime.now():%Y%m%d-%H%M%S}.xlsx"
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


def zapis_den(d, sucho=False, aj_bez=False):
    f = subor(d)
    if otvoreny(f) and not sucho:
        print(f"{f.name} je otvorený, {d} zapíšem nabudúce")
        return None
    wb = nacitaj(f)
    nove, chyby, n = navrh(d, wb.active)
    if sucho:
        for r in nove:
            print(f"{r['cas']:24} {trvanie(r['min']):8} {r['popis']}")
        print(f"({n} sedení, {len(nove)} firemných{'; nedostupné: ' + ', '.join(chyby) if chyby else ''})")
        return nove
    if chyby and not aj_bez:
        # a sleeping machine would lose its part of the day: try again next run
        print(f"{d}: nedostupné {', '.join(chyby)}, skúsim nabudúce")
        return None
    s = stav()
    if nove:
        z = zaloha(f)
        celkom = zapis_riadky(f, wb, nove)
        print(f"{d}: +{len(nove)} riadkov, spolu {trvanie(celkom)} (záloha {z})")
    s.setdefault("dni", {})[str(d)] = [r["cas"] + " " + r["popis"] for r in nove]
    uloz_stav(s)
    return nove


def auto():
    if datetime.now(TZ).hour not in ZOBUDENY:
        return
    hotove = stav().get("dni", {})
    d, today = START, datetime.now(TZ).date()
    pridane = 0
    while d < today:
        if str(d) not in hotove:
            # after two days a machine that still sleeps is left out, so the day gets written
            r = zapis_den(d, aj_bez=d < today - timedelta(days=2))
            pridane += len(r or [])
        d += timedelta(days=1)
    if pridane:
        notify(f"Výkaz: pridal som {pridane} riadkov do {subor(today - timedelta(days=1)).name}")


def vrat(mesiac=None):
    f = PLAT / f"{mesiac}.xlsx" if mesiac else subor(datetime.now(TZ).date() - timedelta(days=1))
    z = sorted(ZALOHY.glob(f"{f.stem}-*.xlsx"))
    if not z:
        sys.exit(f"žiadna záloha {f.name}")
    zaloha(f)
    shutil.copy2(z[-1], f)
    print(f"{f} <- {z[-1]}")


def stav_vypis():
    s = stav().get("dni", {})
    for d, rows in sorted(s.items())[-14:]:
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
    elif a[0] == "vrat":
        vrat(*a[1:2])
    elif a[0] == "stav":
        stav_vypis()
    else:
        sys.exit(__doc__)
