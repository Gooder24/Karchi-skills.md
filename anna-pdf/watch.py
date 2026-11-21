#!/usr/bin/env python3
"""Hermes monitor for new Anna PDF pairs; never sends messages to Anna.

`--watch` (systemd timer anna-pdf-watch, no model) warns Karchi in the Hermes room once per pair that is still
not delivered 30 minutes after it arrived, so a stuck job or a dead model limit cannot stay silent."""
import argparse
import fcntl
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

ROOM = "!tqeWWWNSo2cy8QT5DrjzLVzx0W5PeZosq46LGNT1Ch0"
STATE = Path.home() / ".hermes/state/anna-pdf.json"
ALERT_TO = "matrix:!eK2p6fcTzFQ8MNUtmim8p7_RZzwmXV86W3jkuiKwuq8"
STALE_SECONDS = 30 * 60
JOB_HOURS = range(7, 23)  # the Hermes job runs */5 7-22; outside it nothing is expected to move
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

def stale(state, now):
    """Pairs not done 30 minutes after arrival (counted from 07:00 when it came at night) and not warned yet."""
    when = datetime.fromtimestamp(now)
    if when.hour not in JOB_HOURS:
        return []
    opened = when.replace(hour=7, minute=0, second=0, microsecond=0).timestamp()
    ts = {m["id"]: m.get("ts", 0) / 1000 for m in state["sources"]}
    return [p for p in pairs(state["sources"])
            if state["delivery"].get(p["key"]) != "done" and p["key"] not in state.get("alerts", {})
            and now - max(ts[p["theory"]["id"]], ts[p["worksheet"]["id"]], opened) > STALE_SECONDS]

def alert(pair, uncertain):
    note = "odoslanie je neisté, nič sa neposiela znova, skontroluj chat Anna (WA)" if uncertain else "preklad ešte nevznikol"
    subprocess.run(["hermes", "send", "-t", ALERT_TO,
                    f"⚠️ Zážitok {pair['number']} od Anny: {note} (30 minút od prijatia). Beh a chyby: hermes cron runs 4fd83cfceadd"],
                   check=True, timeout=60)

def save(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temp = STATE.with_suffix(".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    temp.replace(STATE)

def read_chat():
    data = json.loads(subprocess.check_output(
        ["weft", "--json", "read", ROOM, "-n", "200"], text=True, timeout=60))
    assert data["room"] == ROOM, "Wrong room"
    return data["messages"]

def refresh(messages):
    state = json.loads(STATE.read_text())
    ids = [m["id"] for m in messages]
    # shortcut: 200 messages per tick; a missing cursor stops instead of silently losing PDFs.
    if state["anchor"] not in ids:
        raise RuntimeError("Chat cursor missing; recover history before continuing")
    new = messages[ids.index(state["anchor"]) + 1:]
    state["sources"].extend(m for m in new if m.get("me") is False and NAME.search(m.get("text", "")))
    state["anchor"] = messages[-1]["id"]
    save(state)
    return state

def watch():
    """Warn even when the chat cannot be read (Weft down, cursor lost): that is the stuck case itself.
    A failed warning is not recorded and is tried again on the next tick; the unit then ends failed."""
    error = None
    try:
        refresh(read_chat())
    except Exception as e:
        error = e
    state = json.loads(STATE.read_text())
    for pair in stale(state, time.time()):
        try:
            alert(pair, state["delivery"].get(pair["key"]) == "sending")
        except Exception as e:
            error = error or e
            continue
        state.setdefault("alerts", {})[pair["key"]] = datetime.now().isoformat(timespec="seconds")
        save(state)
    if error:
        raise error

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--sending")
    parser.add_argument("--done")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--pairs", action="store_true", help="every known pair with its delivery state, without reading the chat")
    args = parser.parse_args()
    if args.pairs:
        state = json.loads(STATE.read_text())
        print(json.dumps([dict(p, delivery=state["delivery"].get(p["key"])) for p in pairs(state["sources"])], ensure_ascii=False))
        return
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
    if args.watch:
        return watch()
    messages = read_chat()
    if args.init:
        assert not STATE.exists(), "State already exists"
        assert messages, "Cannot baseline an empty response"
        save({"anchor": messages[-1]["id"], "sources": [], "delivery": {}})
        return
    state = refresh(messages)
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
