#!/usr/bin/env python3
"""Print, as one JSON object, everything that waits for Karchi: open inbox items, T3 threads with an
unread reply or an open request on every machine.

Each row has "firma": true for company work (inbox lines starting „eSYST“, T3 threads whose project
or title names eSYST, SPOTREX, Hermes or a zákazka), so the page can split the
view into Firma and Osobné without two setups. Read-only everywhere. Prehľad runs it every 10 min.
"""
import datetime as dt, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from inventory import MACHINES  # noqa: E402

FIRMA = re.compile(r"esyst|spotrex|hermes|zákazk|zakazk|hurbanova|firm|firem", re.I)
INBOX = os.path.expanduser("~/inbox/inbox.md")


def inbox():
    rows, prio = [], None
    for line in open(INBOX, encoding="utf-8"):
        if line.startswith("## "):
            prio = {"## P1": "P1", "## P2": "P2"}.get(line[:5])
            continue
        m = re.match(r"- \[ \] (\d{4}-\d\d-\d\d) · (.*)", line.strip())
        if prio and m:
            what, _, why = m[2].partition(" · ")
            rows.append({"zdroj": "inbox", "priorita": prio, "kedy": m[1], "nazov": what, "detail": why[:300],
                         "firma": bool(FIRMA.search(what))})
    return rows


def t3():
    script = open(os.path.join(HERE, "prehlad", "t3-caka.py")).read()
    rows, missing = [], []
    for device, prefix in MACHINES.items():
        cmd = prefix + ["python3", "-"] if prefix else [sys.executable, "-"]
        try:
            out = subprocess.run(cmd, input=script, capture_output=True, text=True, timeout=40).stdout
        except subprocess.TimeoutExpired:
            out = ""
        got = [json.loads(l) for l in out.splitlines() if l.startswith("{")]
        if not got:
            missing.append(device)
        for r in got[1:]:
            rows.append({"zdroj": "t3", "zariadenie": device, "kedy": r["kedy"], "nazov": r["nazov"],
                         "detail": r["preco"] + (" · " + r["posledne"] if r["posledne"] else ""), "projekt_t3": r["projekt"],
                         "firma": device == "vps" or bool(FIRMA.search(" ".join((r["projekt"], r["priecinok"], r["nazov"]))))})
    return rows, missing



def main():
    t3rows, missing = t3()
    print(json.dumps({"generated": dt.datetime.now(dt.timezone.utc).isoformat(), "rows": inbox() + t3rows,
                      "missing": missing}, ensure_ascii=False))


if __name__ == "__main__":
    main()
