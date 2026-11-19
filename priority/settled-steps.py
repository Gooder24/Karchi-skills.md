#!/usr/bin/env python3
"""Monitor for the Hermes job „Settled kroky“ (skill priority, Karchi 2026-11-19).

Karchi's rule: a thread that is not settled is one he still means to finish, so it has no inbox line;
a settled thread that left him a step he did not do belongs in the inbox. This script prints, stably,
  - every top-level T3 thread on asus, dell, e540 and x270 that was settled and is not judged yet
    (not in ~/.hermes/settled-steps.judged as `<thread id> <settledAt>`) and has no inbox line with its
    `#<last 8 chars>`, with Karchi's last message and the last reply;
  - every open inbox line whose `#id` thread is unsettled again.
It only reads (T3 databases read-only, the inbox). The job's agent writes the inbox and the judged file.
A machine that does not answer keeps its last answer from ~/.cache/settled-steps/, so a sleeping x270
does not change the output. The first answer from a machine (no cache yet) marks what it has settled
already as judged: the job starts from now, not from every old thread.

Installed on asus as ~/.hermes/scripts/settled-steps.py, a three-line runpy wrapper of this file
(Hermes refuses a symlink there), with the job „Settled kroky“ (`hermes cron list`, stop it with
`hermes cron pause <id>`).
"""
import json, os, re, subprocess, sys
from pathlib import Path

HOME = Path.home()
INBOX = HOME / "inbox/inbox.md"
JUDGED = HOME / ".hermes/settled-steps.judged"
CACHE = HOME / ".cache/settled-steps"
HOSTS = ["asus", "dell", "e540", "x270"]

# Runs on each machine: settled and open top-level threads with the last user and assistant text.
REMOTE = r'''
import sqlite3, json, os
db = os.path.expanduser("~/.t3/userdata/statev2.sqlite")
c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
out = []
for tid, title, pj in c.execute("select thread_id, title, payload_json from orchestration_v2_projection_threads where archived_at is null and deleted_at is null"):
    p = json.loads(pj)
    if (p.get("lineage") or {}).get("relationshipToParent"):
        continue
    t = {"id": tid, "title": title, "settledAt": p.get("settledAt") if p.get("settledOverride") == "settled" else None}
    if t["settledAt"]:
        for role in ("user", "assistant"):
            r = c.execute("select json_extract(payload_json,'$.text') from orchestration_v2_projection_messages where thread_id=? and role=? and streaming=0 and coalesce(json_extract(payload_json,'$.creationSource'),'')!='provider' order by created_at desc limit 1", (tid, role)).fetchone()
            t[role] = (r[0] or "") if r else ""
    out.append(t)
print(json.dumps(out, ensure_ascii=False))
'''


def threads(host):
    cache = CACHE / f"{host}.json"
    cmd = [sys.executable, "-"] if host == "asus" else ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, "python3", "-"]
    try:
        r = subprocess.run(cmd, input=REMOTE, capture_output=True, text=True, timeout=60)
        data = json.loads(r.stdout)
        if not cache.exists():  # first answer from this machine: what is settled already is the baseline
            with JUDGED.open("a") as f:
                f.write("".join(f'{t["id"]} {t["settledAt"]}\n' for t in data if t["settledAt"]))
        CACHE.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data, ensure_ascii=False))
        return data
    except Exception:
        return json.loads(cache.read_text()) if cache.exists() else []


def short(text, n):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[:n] + " …"


def main():
    all_threads = {h: threads(h) for h in HOSTS}
    judged = set(JUDGED.read_text().split("\n")) if JUDGED.exists() else set()
    inbox = INBOX.read_text() if INBOX.exists() else ""
    ids_in_inbox = set(re.findall(r"#([0-9a-f]{8})\b", inbox))
    out = []
    for host, ts in all_threads.items():
        for t in sorted(ts, key=lambda t: t["id"]):
            if not t["settledAt"] or f'{t["id"]} {t["settledAt"]}' in judged or t["id"][-8:] in ids_in_inbox:
                continue
            out.append(f'## settled {host} {t["id"]} {t["settledAt"]} „{t["title"]}“')
            out.append(f'Karchi naposledy: {short(t.get("user"), 400)}')
            out.append(f'Posledná odpoveď: {short(t.get("assistant"), 1500)}')
    open_ids = {t["id"][-8:]: (h, t) for h, ts in all_threads.items() for t in ts if not t["settledAt"]}
    for line in inbox.split("\n"):
        m = re.search(r"#([0-9a-f]{8})\b", line)
        if line.startswith("- [ ]") and m and m.group(1) in open_ids:
            h, t = open_ids[m.group(1)]
            out.append(f'## reopened {h} {t["id"]} „{t["title"]}“')
            out.append(f"Riadok: {line}")
    print("\n".join(out) if out else "nič nové")


if __name__ == "__main__":
    main()
