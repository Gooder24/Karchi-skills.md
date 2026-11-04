#!/usr/bin/env python3
"""Print, as JSON lines, this machine's T3 threads that wait for Karchi. Reads the T3 DB read-only.

A thread waits when it is not archived, settled or snoozed, nothing runs in it, and either a request
(approval, question) is open or its last change is newer than his last visit (an unread reply).
Pipe it over ssh: `ssh dell python3 - < t3-caka.py`. Subagent and night-worker threads are left out.
"""
import datetime as dt, json, os, re, socket, sqlite3, sys

db = os.path.expanduser("~/.t3/userdata/statev2.sqlite")
if not os.path.exists(db):
    sys.exit(0)
c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
now = dt.datetime.now(dt.timezone.utc)
since = (now - dt.timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%S")
projects = {pid: (title, root) for pid, title, root in c.execute("select project_id, title, workspace_root from projection_projects")}
pending = {t for (t,) in c.execute("select distinct thread_id from orchestration_v2_projection_runtime_requests where status = 'pending'")}
running = {t for (t,) in c.execute("select distinct thread_id from orchestration_v2_projection_runs where status in ('queued','starting','running','preparing')")}


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


print(json.dumps({"host": socket.gethostname()}))
for tid, pid, title, updated, payload in c.execute(
        "select thread_id, project_id, title, updated_at, payload_json from orchestration_v2_projection_threads "
        "where deleted_at is null and archived_at is null and updated_at >= ?", (since,)):
    p = json.loads(payload)
    ptitle, root = projects.get(pid, ("", ""))
    if tid.startswith("thread:provider:") or ptitle == "Nočný worker" or p.get("settledAt") or p.get("settledOverride"):
        continue
    snooze = ts(p.get("snoozedUntil"))
    if snooze and snooze > now:
        continue
    seen = ts(p.get("lastVisitedAt"))
    unread = seen is None or ts(updated) > seen + dt.timedelta(seconds=2)
    if tid in running or not (tid in pending or unread):
        continue
    last = c.execute("select payload_json from orchestration_v2_projection_messages where thread_id = ? and role = 'assistant' "
                     "order by created_at desc limit 1", (tid,)).fetchone()
    text = " ".join(((json.loads(last[0]).get("text") or "") if last else "").split())
    text = re.sub(r"[*#`]+", "", text).strip()  # plain text: the page shows it raw
    print(json.dumps({"vlakno": tid, "nazov": title, "projekt": ptitle, "priecinok": root, "kedy": updated,
                      "preco": "čaká na odpoveď" if tid in pending else "neprečítaná odpoveď", "posledne": text[:220]}, ensure_ascii=False))
