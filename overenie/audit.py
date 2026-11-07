#!/usr/bin/env python3
"""How often Karchi finds a "hotové" broken, per week, from the T3 threads on every machine.

Run on asus: python3 -I ~/.work/karchi-skills/overenie/audit.py
Reads each machine's T3 database from a copy (never the live file) over ssh, then counts replies that
opened with a done-claim and were followed by his complaint ("nejde", "stále", "neklame" ...). Also
prints the Stop hook's decisions from ~/.claude/overenie-gate.jsonl on each machine. Read-only.
"""
import collections, json, re, socket, subprocess, sys, unicodedata

HOSTS = ["local", "x270", "dell", "e540"]
REMOTE = r'''
import sqlite3, json, os, glob, shutil, tempfile
home = os.path.expanduser("~"); out = {"threads": {}, "gate": []}
db = home + "/.t3/userdata/statev2.sqlite"
if os.path.exists(db):
    tmp = tempfile.mkdtemp()
    for suf in ("", "-wal", "-shm"):
        if os.path.exists(db + suf): shutil.copy2(db + suf, tmp + "/s" + suf)
    c = sqlite3.connect(tmp + "/s")
    for tid, role, ca, pj in c.execute("select thread_id, role, created_at, payload_json from orchestration_v2_projection_messages order by created_at"):
        if not tid[:8].strip("0123456789abcdef") == "" or "-" not in tid[:9]: continue
        try: t = json.loads(pj).get("text", "")
        except ValueError: t = ""
        out["threads"].setdefault(tid, []).append((ca, role, t[:600]))
    shutil.rmtree(tmp)
g = home + "/.claude/overenie-gate.jsonl"
if os.path.exists(g):
    for l in open(g, errors="replace"):
        try: out["gate"].append(json.loads(l))
        except ValueError: pass
print(json.dumps(out))
'''

def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")

CLAIM = re.compile(r"\b(hotov\w*|funguj\w*|opraven\w*|opravil\w*|fixnut\w*|nasaden\w*|nasadil\w*|preslo|overil\w*)")
COMPLAINT = re.compile(r"(nefunguj\w*|\bnejde\b|\bstale\b|\bzase\b|neklam\w*|halucin\w*|neverifik\w*|nevidim|"
                       r"nezobraz\w*|buguje|nie je to (dobre|fixnut)|404|uz to funguje\?|si si isty)")

def fetch(host):
    cmd = ["python3", "-I", "-"] if host == "local" else ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", host, "python3 -I -"]
    try:
        r = subprocess.run(cmd, input=REMOTE, capture_output=True, text=True, timeout=120)
        return json.loads(r.stdout)
    except (subprocess.TimeoutExpired, ValueError):
        return None

weeks = collections.defaultdict(lambda: [0, 0]); gate = collections.Counter(); down = []
for h in HOSTS:
    d = fetch(h)
    if d is None: down.append(h); continue
    for msgs in d["threads"].values():
        last = None
        for ts, role, text in msgs:
            if role == "assistant": last = text; continue
            if role != "user" or not last: continue
            if norm(text).startswith(("presunut", "background command", "monitor \"", "delegated task")): continue
            if CLAIM.search(norm(last[:400])):
                wk = __import__("datetime").date.fromisoformat(ts[:10]).isocalendar()
                k = f"{wk[0]}-W{wk[1]:02d}"
                weeks[k][0] += 1
                weeks[k][1] += bool(COMPLAINT.search(norm(text)))
            last = None
    for e in d["gate"]: gate[e.get("outcome") if isinstance(e, dict) else "?"] += 1

print("týždeň    odpovede s 'hotové'   po nich tvoja sťažnosť")
for k in sorted(weeks):
    n, bad = weeks[k]; print(f"{k}  {n:>8}              {bad:>3}  ({100*bad//max(n,1)} %)")
print("\nStop hook overenie-gate:", dict(gate) or "zatiaľ žiadne rozhodnutia")
if gate:
    print("  pass-netreba = bez dôkazu so zdôvodnením, pass-after-block = druhý pokus po bloku; dôvody sú v ~/.claude/overenie-gate.jsonl")
if down: print("nedostupné:", ", ".join(down))
