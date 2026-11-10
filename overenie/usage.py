#!/usr/bin/env python3
"""Turns one verifier run's machine output into verifier-output.txt and one usage line.

Usage: python3 -I usage.py <overenie/verifier-output.json | overenie/verifier-codex.jsonl> [start epoch seconds]
Reads `claude -p --output-format json` or `codex exec --json`. Writes the verifier's reply next to it as
verifier-output.txt (what the skill reads) and appends one line to ~/.claude/overenie-usage.jsonl: verifier, project,
time, duration, turns, tokens by kind and, for Claude, the API-priced cost the CLI reports. That cost is the API
price, not how much of Karchi's subscription limit the run used; neither CLI reports that.
"""
import json, os, sys, time
src = sys.argv[1]
start = float(sys.argv[2]) if len(sys.argv) > 2 else None
raw = open(src, errors="replace").read()
out = os.path.join(os.path.dirname(src), "verifier-output.txt")
line = {"time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "project": os.getcwd()}

events = []
for l in raw.splitlines():
    try:
        events.append(json.loads(l))
    except ValueError:
        pass
if events and events[0].get("type") == "thread.started":            # codex exec --json
    text, usage, error, steps = "", {}, None, 0
    for e in events:
        t = e.get("type")
        if t == "item.completed":
            steps += 1
            if e.get("item", {}).get("type") == "agent_message":
                text = e["item"].get("text", "")
        elif t == "turn.completed":
            usage = e.get("usage") or {}
        elif t in ("error", "turn.failed"):
            error = e.get("message") or (e.get("error") or {}).get("message")
    open(out, "w").write(text or error or raw)
    line.update(verifier="codex", error=bool(error), message=error, steps=steps,
                input=usage.get("input_tokens"), cache_read=usage.get("cached_input_tokens"),
                output=usage.get("output_tokens"), reasoning=usage.get("reasoning_output_tokens"))
else:                                                               # claude -p --output-format json
    try:
        r = json.loads(raw)
    except ValueError:       # limit hit, crash: keep the raw text so the skill still sees it
        open(out, "w").write(raw)
        r = {"is_error": True}
    else:
        open(out, "w").write(r.get("result") or raw)
    u = r.get("usage") or {}
    line.update(verifier="claude", error=r.get("is_error"), turns=r.get("num_turns"),
                input=u.get("input_tokens"), cache_write=u.get("cache_creation_input_tokens"),
                cache_read=u.get("cache_read_input_tokens"), output=u.get("output_tokens"),
                api_cost_usd=r.get("total_cost_usd"))
if os.environ.get("OVERENIE_ACCOUNT"):
    line["account"] = os.environ["OVERENIE_ACCOUNT"]
if start:
    line["duration_s"] = round(time.time() - start)
with open(os.path.expanduser("~/.claude/overenie-usage.jsonl"), "a") as f:
    f.write(json.dumps(line) + "\n")
