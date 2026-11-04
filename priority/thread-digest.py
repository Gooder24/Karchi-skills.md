#!/usr/bin/env python3
"""Print what happened in this machine's T3 threads since a time, for reconciling the inbox.

Usage: thread-digest.py [--since ISO] [--hours N]   (default: last 26 hours)
       thread-digest.py --thread <id> [--messages N]   (one thread, its last N messages in full)
Reads ~/.t3/userdata/statev2.sqlite read-only; never writes. One block per top-level thread with
user messages: title, project folder, run state, the first and last user message and the last
assistant reply, cut short. Pipe it over ssh: `ssh dell python3 - --hours 26 < thread-digest.py`.
"""
import datetime as dt
import json
import os
import socket
import sqlite3
import sys

args = sys.argv[1:]
hours = 26
since = None
if "--hours" in args:
    hours = float(args[args.index("--hours") + 1])
if "--since" in args:
    since = args[args.index("--since") + 1]
if since is None:
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")

db = os.path.expanduser("~/.t3/userdata/statev2.sqlite")
if not os.path.exists(db):
    sys.exit(f"{socket.gethostname()}: no T3 database")
c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)


def cut(text, n):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def local(ts):
    t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    return t.strftime("%m-%d %H:%M")


if "--thread" in args:  # one thread in full: its last N messages (default 12), uncut
    tid = args[args.index("--thread") + 1]
    n = int(args[args.index("--messages") + 1]) if "--messages" in args else 12
    rows = c.execute(
        "select role, created_at, payload_json from orchestration_v2_projection_messages "
        "where thread_id = ? order by created_at desc limit ?",
        (tid, n),
    ).fetchall()
    for role, ts, j in reversed(rows):
        print(f"\n### {role} {local(ts)}\n{json.loads(j).get('text') or ''}")
    sys.exit(0)

projects = {}
for pid, title, root in c.execute(
    "select project_id, title, payload_json from orchestration_v2_projection_projects"
    if c.execute("select 1 from sqlite_master where name='orchestration_v2_projection_projects'").fetchone()
    else "select project_id, title, workspace_root from projection_projects"
):
    projects[pid] = title

threads = c.execute(
    """select thread_id, project_id, title, created_at, updated_at, archived_at, deleted_at, payload_json
       from orchestration_v2_projection_threads where updated_at >= ? and deleted_at is null
       order by updated_at""",
    (since,),
).fetchall()

print(f"# {socket.gethostname()}: T3 threads updated since {since}Z ({len(threads)})")
for tid, pid, title, created, updated, archived, _deleted, payload in threads:
    p = json.loads(payload or "{}")
    if (p.get("lineage") or {}).get("parentThreadId"):
        continue  # subagent or delegated child: its parent covers it
    msgs = c.execute(
        "select role, created_at, payload_json from orchestration_v2_projection_messages "
        "where thread_id = ? order by created_at",
        (tid,),
    ).fetchall()
    users = [(t, json.loads(j).get("text") or "") for r, t, j in msgs if r == "user"]
    replies = [(t, json.loads(j).get("text") or "") for r, t, j in msgs if r == "assistant"]
    if not users:
        continue
    run = c.execute(
        "select status from orchestration_v2_projection_runs where thread_id = ? order by ordinal desc limit 1",
        (tid,),
    ).fetchone()
    state = run[0] if run else "?"
    flags = [f for f, on in (("archived", archived), ("settled", p.get("settledAt") or p.get("settledOverride"))) if on]
    print(f"\n## {cut(title, 80)}")
    print(f"- id {tid} · project {projects.get(pid, pid)} · {local(created)} → {local(updated)} · "
          f"{len(users)} user msgs · last run {state}" + (f" · {', '.join(flags)}" if flags else ""))
    if p.get("worktreePath"):
        print(f"- folder {p['worktreePath']}")
    print(f"- first ask ({local(users[0][0])}): {cut(users[0][1], 400)}")
    if len(users) > 1:
        print(f"- last ask ({local(users[-1][0])}): {cut(users[-1][1], 300)}")
    if replies:
        print(f"- last reply ({local(replies[-1][0])}): {cut(replies[-1][1], 600)}")
