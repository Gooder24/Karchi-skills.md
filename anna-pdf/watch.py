#!/usr/bin/env python3
"""Hermes monitor for new Anna PDF pairs; never sends messages."""
import argparse
import fcntl
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOM = "!tqeWWWNSo2cy8QT5DrjzLVzx0W5PeZosq46LGNT1Ch0"
STATE = Path.home() / ".hermes/state/anna-pdf.json"
NAME = re.compile(r"\[Súbor: (Experience[ -](\d+)[ -](Theory|Worksheet)(?=[ .(_-])[^\]\n]*\.pdf)\]", re.I)

def pairs(messages):
    groups = {}
    for m in messages:
        match = NAME.search(m.get("text", ""))
        if m.get("me") is not False or not match:
            continue
        filename, number, role = match.groups()
        group = groups.setdefault(number, {"theory": [], "worksheet": []})
        group[role.lower()].append({"id": m["id"], "filename": filename})
    result = []
    for number, group in groups.items():
        for theory, worksheet in zip(group["theory"], group["worksheet"]):
            key = hashlib.sha256((theory["id"] + "\n" + worksheet["id"]).encode()).hexdigest()[:24]
            result.append({"key": key, "number": number, "theory": theory, "worksheet": worksheet})
    return result

def save(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temp = STATE.with_suffix(".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    temp.replace(STATE)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--sending")
    parser.add_argument("--done")
    args = parser.parse_args()
    if args.sending or args.done:
        state = json.loads(STATE.read_text())
        key = args.sending or args.done
        assert key in {p["key"] for p in pairs(state["sources"])}, "Unknown pair"
        old = state["delivery"].get(key)
        if args.sending:
            assert old is None, "Already sent or uncertain; do not retry automatically"
            state["delivery"][key] = "sending"
        else:
            assert old == "sending", "Mark sending before delivery"
            state["delivery"][key] = "done"
        save(state)
        return
    data = json.loads(subprocess.check_output(
        ["weft", "--json", "read", ROOM, "-n", "200"], text=True, timeout=60))
    assert data["room"] == ROOM, "Wrong room"
    messages = data["messages"]
    if args.init:
        assert not STATE.exists(), "State already exists"
        assert messages, "Cannot baseline an empty response"
        save({"anchor": messages[-1]["id"], "sources": [], "delivery": {}})
        return
    state = json.loads(STATE.read_text())
    ids = [m["id"] for m in messages]
    # shortcut: 200 messages per tick; a missing cursor stops instead of silently losing PDFs.
    if state["anchor"] not in ids:
        raise RuntimeError("Chat cursor missing; recover history before continuing")
    new = messages[ids.index(state["anchor"]) + 1:]
    state["sources"].extend(m for m in new if m.get("me") is False and NAME.search(m.get("text", "")))
    state["anchor"] = messages[-1]["id"]
    save(state)
    found = pairs(state["sources"])
    print(json.dumps({
        "pending": [p for p in found if p["key"] not in state["delivery"]],
        "uncertain": [p for p in found if state["delivery"].get(p["key"]) == "sending"],
    }, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with STATE.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        main()
