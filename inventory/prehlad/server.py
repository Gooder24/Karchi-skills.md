#!/usr/bin/env python3
"""Prehľad: one page with every recurring job on Karchi's machines and what needs an update.

Run on asus as the user service prehlad.service: python3 server.py [port]. It listens on 127.0.0.1
only; Caddy puts it at /prehlad next to Rerun. Every 30 minutes it reruns ../inventory.py, every
6 hours ../updates.py, every 10 minutes ../cakajuce.py (what waits for Karchi), and keeps the last good result in ~/.cache/prehlad. Colours live in
~/.config/prehlad/farby.json, which the page edits through POST api/farby.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.expanduser("~/.cache/prehlad")
CONFIG = os.path.expanduser("~/.config/prehlad/farby.json")
TZ = ZoneInfo("Europe/Bratislava")
REFRESH = {"inventory.py": 30 * 60, "updates.py": 6 * 3600, "cakajuce.py": 10 * 60}
STATIC = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/style.css": ("style.css", "text/css; charset=utf-8"),
          "/DepartureMono-Regular.woff2": ("DepartureMono-Regular.woff2", "font/woff2")}
lock = threading.Lock()


def cached(script):
    try:
        with open(os.path.join(CACHE, script.replace(".py", ".json"))) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"rows": [], "generated": None}


def refresh_loop(script):
    while True:
        out = subprocess.run([sys.executable, os.path.join(ROOT, script)], capture_output=True, text=True, timeout=900).stdout
        try:
            json.loads(out)
            os.makedirs(CACHE, exist_ok=True)
            with open(os.path.join(CACHE, script.replace(".py", ".json.tmp")), "w") as f:
                f.write(out)
            os.replace(os.path.join(CACHE, script.replace(".py", ".json.tmp")), os.path.join(CACHE, script.replace(".py", ".json")))
        except ValueError:
            pass  # keep the last good result; the page shows its age
        time.sleep(REFRESH[script])


def colours():
    path = CONFIG if os.path.exists(CONFIG) else os.path.join(HERE, "farby.default.json")
    with open(path) as f:
        return json.load(f)


def project_of(cfg, device, name):
    for dev, prefix, project in cfg["pravidla"]:
        if dev in ("*", device) and name.startswith(prefix):
            return project
    return None


def cron_field(spec, lo, hi):
    out = set()
    for part in spec.split(","):
        step = 1
        if "/" in part:
            part, step = part.split("/")
            step = int(step)
        if part == "*":
            a, b = lo, hi
        elif "-" in part:
            a, b = map(int, part.split("-"))
        else:
            a = b = int(part)
        out.update(range(a, b + 1, step))
    return out


def cron_next(expr, now):
    """Next run of a five-field cron line in Bratislava time; None for anything it cannot read."""
    try:
        m, h, dom, mon, dow = expr.split()
        mins, hours = cron_field(m, 0, 59), cron_field(h, 0, 23)
        doms, mons, dows = cron_field(dom, 1, 31), cron_field(mon, 1, 12), {d % 7 for d in cron_field(dow, 0, 7)}
    except ValueError:
        return None
    t = now.replace(second=0, microsecond=0) + dt.timedelta(minutes=1)
    for _ in range(8 * 24 * 60):
        if t.minute in mins and t.hour in hours and t.day in doms and t.month in mons and (t.isoweekday() % 7) in dows:
            return t
        t += dt.timedelta(minutes=1)
    return None


def parse_next(row, now):
    raw = row.get("dalsi_raw") or ""
    m = re.search(r"(\d{4}-\d\d-\d\d) (\d\d:\d\d:\d\d)", raw)
    if m:
        return dt.datetime.fromisoformat(f"{m[1]}T{m[2]}").replace(tzinfo=TZ)
    if re.match(r"\d{4}-\d\d-\d\dT", raw):
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(TZ)
    if row.get("druh") in ("cron", "rerun") and row.get("kedy_raw"):
        return cron_next(row["kedy_raw"], now)
    return None


def data():
    now = dt.datetime.now(TZ)
    cfg = colours()
    inv, upd = cached("inventory.py"), cached("updates.py")
    rows = []
    for r in inv["rows"]:
        nxt = parse_next(r, now)
        r = {k: v for k, v in r.items() if k not in ("kedy_raw", "dalsi_raw")}
        r["projekt"] = project_of(cfg, r["zariadenie"], r["nazov"])
        r["dalsi"] = nxt.isoformat() if nxt else None
        rows.append(r)
    updates = []
    for u in upd["rows"]:
        nxt = parse_next(u, now)
        u = {k: v for k, v in u.items() if k != "dalsi_raw"}
        u["dalsi"] = nxt.isoformat() if nxt else None
        updates.append(u)
    return {"teraz": now.isoformat(), "inventar": inv.get("generated"), "aktualizacie_z": upd.get("generated"),
            "chyba": inv.get("missing", []), "procesy": rows, "aktualizacie": updates, "farby": cfg,
            "caka": cached("cakajuce.py")}


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, ctype="application/json; charset=utf-8"):
        body = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/data":
            return self.send(200, json.dumps(data(), ensure_ascii=False))
        if path in STATIC:
            name, ctype = STATIC[path]
            with open(os.path.join(HERE, name), "rb") as f:
                return self.send(200, f.read(), ctype)
        self.send(404, '{"chyba": "nenájdené"}')

    def do_POST(self):
        # The custom header forces a CORS preflight, so another site cannot post here from a browser.
        if self.path != "/api/farby" or self.headers.get("X-Prehlad") != "1":
            return self.send(403, '{"chyba": "zakázané"}')
        try:
            cfg = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            assert isinstance(cfg.get("rodiny"), dict) and isinstance(cfg.get("projekty"), dict) and isinstance(cfg.get("pravidla"), list)
            for r in cfg["rodiny"].values():
                assert re.fullmatch(r"#[0-9a-fA-F]{6}", r["farba"])
        except (ValueError, AssertionError, KeyError, TypeError):
            return self.send(400, '{"chyba": "neplatné farby"}')
        with lock:
            os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
            with open(CONFIG + ".tmp", "w") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=1)
            os.replace(CONFIG + ".tmp", CONFIG)
        self.send(200, '{"ok": true}')

    def log_message(self, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3460
    for script in REFRESH:
        threading.Thread(target=refresh_loop, args=(script,), daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
