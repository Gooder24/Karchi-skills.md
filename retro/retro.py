#!/usr/bin/env python3
"""Morning prompt retro: the settled T3 thread that cost Karchi the most rounds, reviewed by Opus.

Cron on asus, 07:05 Mon-Fri, before Rerun's 07:30 "Ranný prehľad":
    5 7 * * 1-5 python3 -I ~/.work/karchi-skills/retro/retro.py
Reads every machine's T3 database read-only over ssh (this file runs itself there with --extract),
picks the thread settled in the last 24 h (72 h on Monday) where Karchi wrote the most messages
(at least MIN_ROUNDS), asks `claude -p` with prompt.md for the retro, saves it to
~/inbox/retro/<date>.md and copies it into Rerun Chief of Staff notes/retro/. No thread, no retro.
Options: --dry (print the chosen thread, no Claude call), --hours N, --min-rounds N, --thread <id>.
"""
import datetime as dt
import json
import os
import socket
import sqlite3
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOSTS = {"asus": "asus-vivobook", "dell": "dell-latitude", "e540": "thinkpad-e540", "x270": "karchi"}
MIN_ROUNDS = 5
NOISE = ("Continue where you left off.", ".", "pokračuj", "/compact", "/clear", "/autocompact")
RERUN_NOTES = "/data/agents/x8j38cwag1625bjbuk6od/workspace/notes/retro"
args = sys.argv[1:]


def opt(name, default):
    return type(default)(args[args.index(name) + 1]) if name in args else default


def extract():
    """Runs on each machine: JSON list of settled threads with Karchi's messages and the last replies."""
    since, only = opt("--since", ""), opt("--thread", "")
    db = os.path.expanduser("~/.t3/userdata/statev2.sqlite")
    if not os.path.exists(db):
        print("[]")
        return
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    out = []
    for tid, title, pj in c.execute(
        "select thread_id, title, payload_json from orchestration_v2_projection_threads where deleted_at is null"
    ):
        p = json.loads(pj or "{}")
        if only and tid != only:
            continue
        if not only and ((p.get("lineage") or {}).get("parentThreadId") or (p.get("settledAt") or "") < since):
            continue
        mine, replies = [], []
        for role, ts, mj in c.execute(
            "select role, created_at, payload_json from orchestration_v2_projection_messages "
            "where thread_id = ? order by created_at", (tid,)
        ):
            m = json.loads(mj)
            text = (m.get("text") or "").strip()
            if role == "user" and m.get("createdBy") == "user" and text and not text.startswith(NOISE):
                mine.append({"t": ts[:16], "text": text[:3000], "att": len(m.get("attachments") or [])})
            elif role == "assistant" and len(text) > 200:
                replies.append({"t": ts[:16], "text": text[:2500]})
        if mine:
            out.append({"host": socket.gethostname(), "id": tid, "title": title,
                        "settled": p.get("settledAt"), "mine": mine, "replies": replies[-4:]})
    print(json.dumps(out, ensure_ascii=False))


def collect(since, only):
    src = open(os.path.abspath(__file__), "rb").read()
    found = []
    for h, name in HOSTS.items():
        cmd = ["python3", "-I", "-", "--extract", "--since", since] + (["--thread", only] if only else [])
        if not socket.gethostname().startswith(name):
            cmd = ["ssh", "-o", "ConnectTimeout=6", "-o", "BatchMode=yes", h, " ".join(cmd)]
        try:
            r = subprocess.run(cmd, input=src, capture_output=True, timeout=60)
            found += json.loads(r.stdout or b"[]")
        except Exception as e:  # a sleeping x270 must not stop the retro
            print(f"{h}: skipped ({e.__class__.__name__})", file=sys.stderr)
    return found


def main():
    now = dt.datetime.now(dt.timezone.utc)
    hours = opt("--hours", 72 if now.astimezone().weekday() == 0 else 24)
    since = (now - dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")
    only = opt("--thread", "")
    threads = collect(since, only)
    threads = [t for t in threads if only or len(t["mine"]) >= opt("--min-rounds", MIN_ROUNDS)]
    if not threads:
        print(f"no settled thread with {MIN_ROUNDS}+ rounds since {since}Z")
        return
    t = max(threads, key=lambda t: len(t["mine"]))
    misses = os.path.expanduser("~/inbox/overenie-chyby.md")
    context = {
        "thread": t,
        "verification_misses": open(misses).read()[-3000:] if os.path.exists(misses) else "",
    }
    if "--dry" in args:
        print(f"{t['host']} {t['id']} · {len(t['mine'])} rounds · {t['title']}")
        return
    prompt = open(os.path.join(HERE, "prompt.md")).read() + "\n\n```json\n" + json.dumps(context, ensure_ascii=False) + "\n```"
    r = subprocess.run(
        [os.path.expanduser("~/.local/bin/claude") if os.path.exists(os.path.expanduser("~/.local/bin/claude")) else "claude",
         "-p", prompt, "--model", "claude-opus-5-5", "--effort", "high", "--tools", "",
         "--strict-mcp-config", "--disable-slash-commands", "--no-session-persistence"],
        capture_output=True, text=True, timeout=900,
    )
    if r.returncode or not r.stdout.strip():
        sys.exit(f"claude failed: {r.stderr[-500:]}")
    day = now.astimezone().strftime("%Y-%m-%d")
    head = f"# Retro {day}: {t['title']}\n\n{t['host']} · vlákno {t['id']} · {len(t['mine'])} tvojich správ\n\n"
    path = os.path.expanduser(f"~/inbox/retro/{day}.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(head + r.stdout.strip() + "\n")
    subprocess.run(["docker", "exec", "-u", "rerun", "rerun-engine-1", "mkdir", "-p", RERUN_NOTES])
    with open(path, "rb") as f:
        subprocess.run(["docker", "exec", "-i", "-u", "rerun", "rerun-engine-1", "sh", "-c",
                        f"cat > '{RERUN_NOTES}/{day}.md'"], stdin=f)
    print(path)


extract() if "--extract" in args else main()
