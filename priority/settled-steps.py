#!/usr/bin/env python3
"""Monitor for the Hermes job „Settled kroky“ (skill priority, Karchi 2026-11-19).

Karchi's rule: a thread that is not settled is one he still means to finish, so it has no inbox line;
a settled thread that left him a step he did not do belongs in the inbox. This script prints, stably,
  - every top-level T3 thread on asus, dell, e540 and x270 settled after SINCE and not judged yet
    (not in ~/.hermes/settled-steps.judged as `<thread id> <settledAt>`) and with no open inbox line
    carrying its `#<last 8 chars>`, with Karchi's last message and the last reply;
  - every open inbox line whose thread is unsettled again: found by `#id`, or for an older line by
    `<machine> vlákno „<title>“` when exactly one thread there has that title.
It only reads (T3 databases read-only, the inbox). The job's agent writes the inbox and the judged file.
A machine that does not answer keeps its last answer from ~/.cache/settled-steps/, so a sleeping x270
does not change the output. Threads settled before SINCE (the job's start) were sorted by hand.

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
SINCE = "2026-11-19T16:45:00Z"

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
            r = c.execute("select json_extract(payload_json,'$.text') from orchestration_v2_projection_messages where thread_id=? and role=? and streaming=0 and (role='assistant' or not (json_extract(payload_json,'$.createdBy')='agent' and json_extract(payload_json,'$.creationSource') in ('provider','server'))) order by created_at desc limit 1", (tid, role)).fetchone()
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
    open_lines = [l for l in inbox.split("\n") if l.startswith("- [ ]")]
    ids_in_inbox = {m for l in open_lines for m in re.findall(r"#([0-9a-f]{8})\b", l)}
    out = []
    for host, ts in all_threads.items():
        for t in sorted(ts, key=lambda t: t["id"]):
            if (not t["settledAt"] or t["settledAt"] < SINCE or f'{t["id"]} {t["settledAt"]}' in judged
                    or t["id"][-8:] in ids_in_inbox):
                continue
            out.append(f'## settled {host} {t["id"]} {t["settledAt"]} „{t["title"]}“')
            out.append(f'Karchi naposledy: {short(t.get("user"), 400)}')
            out.append(f'Posledná odpoveď: {short(t.get("assistant"), 1500)}')
    by_id = {t["id"][-8:]: (h, t) for h, ts in all_threads.items() for t in ts}
    for line in open_lines:
        m = re.search(r"#([0-9a-f]{8})\b", line)
        hit = by_id.get(m.group(1)) if m else None
        if not m:
            mt = re.search(r"\b(asus|dell|e540|x270)\b,? vlákn\w* „([^“]+)“", line)
            same = [t for t in all_threads.get(mt.group(1), []) if t["title"] == mt.group(2)] if mt else []
            hit = (mt.group(1), same[0]) if len(same) == 1 else None
        if hit and not hit[1]["settledAt"]:
            h, t = hit
            out.append(f'## reopened {h} {t["id"]} „{t["title"]}“')
            out.append(f"Riadok: {line}")
    print("\n".join(out) if out else "nič nové")


if __name__ == "__main__":
    main()
