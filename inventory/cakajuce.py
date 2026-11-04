#!/usr/bin/env python3
"""Print, as one JSON object, everything that waits for Karchi: open inbox items, T3 threads with an
unread reply or an open request on every machine, and Rerun coworkers that asked him something.

Each row has "firma": true for company work (inbox lines starting „eSYST“, T3 threads whose project
or title names eSYST, SPOTREX, Hermes or a zákazka, everything in Rerun), so the page can split the
view into Firma and Osobné without two setups. Read-only everywhere. Prehľad runs it every 10 min.
"""
import datetime as dt, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from inventory import MACHINES  # noqa: E402

FIRMA = re.compile(r"esyst|spotrex|hermes|zákazk|zakazk|hurbanova|firm|firem", re.I)
INBOX = os.path.expanduser("~/inbox/inbox.md")
DB = ["docker", "exec", "-i", "supabase_db_rerun-oss", "psql", "-U", "postgres", "-At", "-F", "\t"]


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


def rerun():
    # The latest notification of each coworker session decides: a question or approval still open
    # is the last thing it said. Rerun never marks them read until he opens the app, so read_at alone lies.
    q = """select distinct on (n.engine_session_id) n.kind, coalesce(a.name, 'Rerun'), n.message, n.created_at, n.read_at is null
           from notifications n left join agents a on a.id = n.agent_id
           where n.created_at > now() - interval '7 days'
           order by n.engine_session_id, n.created_at desc"""
    try:
        out = subprocess.run(DB, input=q, capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.TimeoutExpired):
        return [], ["rerun"]
    rows = []
    for line in out.splitlines():
        kind, agent, msg, created, unread = (line.split("\t") + [""] * 5)[:5]
        if kind in ("question", "approval", "error", "connector") and unread == "t":
            rows.append({"zdroj": "rerun", "kedy": created.replace(" ", "T")[:19] + "Z", "nazov": agent,
                         "detail": {"question": "pýta sa", "approval": "čaká na schválenie", "error": "chyba",
                                    "connector": "chce pripojenie"}[kind] + " · " + " ".join(msg.split())[:220], "firma": True})
    return rows, []


def main():
    t3rows, missing = t3()
    rr, rmiss = rerun()
    print(json.dumps({"generated": dt.datetime.now(dt.timezone.utc).isoformat(), "rows": inbox() + t3rows + rr,
                      "missing": missing + rmiss}, ensure_ascii=False))


if __name__ == "__main__":
    main()
