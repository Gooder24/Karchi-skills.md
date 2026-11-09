#!/usr/bin/env python3
"""Turns a verifier's `claude -p --output-format json` result into verifier-output.txt and one usage line.

Usage: python3 -I usage.py overenie/verifier-output.json
Writes the verifier's reply next to it as verifier-output.txt (what the skill reads) and appends one line to
~/.claude/overenie-usage.jsonl: project, time, duration, turns, tokens by kind and the API-priced cost the CLI reports.
That cost is the API price, not how much of Karchi's subscription limit the run used; the CLI does not report that.
"""
import json, os, sys, time
src = sys.argv[1]
raw = open(src, errors="replace").read()
try:
    r = json.loads(raw)
except ValueError:           # limit hit, crash: keep the raw text so the skill still sees it
    open(os.path.join(os.path.dirname(src), "verifier-output.txt"), "w").write(raw); sys.exit(0)
open(os.path.join(os.path.dirname(src), "verifier-output.txt"), "w").write(r.get("result") or raw)
u = r.get("usage") or {}
line = {"time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "project": os.getcwd(), "error": r.get("is_error"),
        "duration_s": round((r.get("duration_ms") or 0) / 1000), "turns": r.get("num_turns"),
        "input": u.get("input_tokens"), "cache_write": u.get("cache_creation_input_tokens"),
        "cache_read": u.get("cache_read_input_tokens"), "output": u.get("output_tokens"),
        "api_cost_usd": r.get("total_cost_usd")}
with open(os.path.expanduser("~/.claude/overenie-usage.jsonl"), "a") as f:
    f.write(json.dumps(line) + "\n")
