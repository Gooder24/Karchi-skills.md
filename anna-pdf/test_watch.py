#!/usr/bin/env python3
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
spec = importlib.util.spec_from_file_location("watch", Path(__file__).resolve().parent / "watch.py")
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)
def msg(id, number=3, role="Theory", me=False):
    return {"id": id, "me": me, "text": f"[Súbor: Experience-{number}-{role}.pdf] ↷ Forwarded"}
assert watch.pairs([msg("a")]) == []
assert watch.pairs([msg("a"), msg("b", 4, "Worksheet")]) == []
assert watch.pairs([msg("a", me=True), msg("b", role="Worksheet")]) == []
assert len(watch.pairs([msg("b", role="Worksheet"), msg("a")])) == 1
assert len(watch.pairs([msg("a"), msg("b", role="Worksheet"), msg("c"), msg("d", role="Worksheet")])) == 2
assert watch.pairs([msg("a", role="Theorycraft"), msg("b", role="Worksheet")]) == []
assert watch.pairs([msg("a"), msg("b", role="WorksheetBackup")]) == []
assert len(watch.pairs([msg("a"), msg("b", role="Worksheet PRACTICE")])) == 1
assert len(watch.pairs([msg("a"), msg("b", role="Worksheet (1)")])) == 1
with tempfile.TemporaryDirectory() as tmp:
    watch.STATE = Path(tmp) / "state.json"
    history = [msg("historical"), msg("anchor", role="Worksheet")]
    def run(*args):
        with patch.object(sys, "argv", ["watch.py", *args]), patch.object(watch.subprocess, "check_output", return_value=json.dumps({"room": watch.ROOM, "messages": history})), contextlib.redirect_stdout(io.StringIO()) as output:
            watch.main()
        return json.loads(output.getvalue()) if output.getvalue() else None
    run("--init")
    assert run() == {"pending": [], "uncertain": []}
    history.append(msg("new-theory"))
    assert not run()["pending"]
    history.append(msg("new-worksheet", role="Worksheet"))
    pending = run()["pending"]
    assert len(pending) == 1
    assert run()["pending"] == pending
    key = pending[0]["key"]
    try:
        run("--done", key)
        raise RuntimeError("done must require sending")
    except AssertionError:
        pass
    run("--sending", key)
    assert not run()["pending"] and run()["uncertain"][0]["key"] == key
    try:
        run("--sending", key)
        raise RuntimeError("sending must refuse retry")
    except AssertionError:
        pass
    run("--done", key)
    assert run() == {"pending": [], "uncertain": []}
    assert len(json.loads(watch.STATE.read_text())["sources"]) == 2
    history = [msg("lost-cursor")]
    try:
        run()
        raise AssertionError("missing anchor must fail")
    except RuntimeError as error:
        assert "cursor missing" in str(error)
# --watch: one warning per pair, only after 30 minutes, never for a done pair, never outside the job hours
from datetime import datetime
day = datetime(2026, 11, 15, 12, 0).timestamp()
src = [dict(msg("t"), ts=day * 1000), dict(msg("w", role="Worksheet"), ts=day * 1000 + 5000)]
state = {"sources": src, "delivery": {}}
assert watch.stale(state, day + 29 * 60) == []
assert len(watch.stale(state, day + 31 * 60)) == 1
state["delivery"][watch.pairs(src)[0]["key"]] = "sending"
assert len(watch.stale(state, day + 31 * 60)) == 1
state["delivery"][watch.pairs(src)[0]["key"]] = "done"
assert watch.stale(state, day + 31 * 60) == []
state["delivery"] = {}
state["alerts"] = {watch.pairs(src)[0]["key"]: "x"}
assert watch.stale(state, day + 31 * 60) == []
night = datetime(2026, 11, 15, 23, 30).timestamp()
state = {"sources": [dict(m, ts=(night - 3600) * 1000) for m in src], "delivery": {}}
assert watch.stale(state, night) == []
morning = datetime(2026, 11, 16, 7, 20).timestamp()
assert watch.stale(state, morning) == []
assert len(watch.stale(state, datetime(2026, 11, 16, 7, 31).timestamp())) == 1
with tempfile.TemporaryDirectory() as tmp:
    watch.STATE = Path(tmp) / "state.json"
    sent = []
    watch.save({"anchor": "w", "sources": [dict(m, ts=day * 1000) for m in src], "delivery": {}})
    history = [msg("t"), msg("w", role="Worksheet")]
    with patch.object(sys, "argv", ["watch.py", "--watch"]), patch.object(watch.time, "time", return_value=day + 40 * 60), \
         patch.object(watch.subprocess, "check_output", return_value=json.dumps({"room": watch.ROOM, "messages": history})), \
         patch.object(watch.subprocess, "run", side_effect=lambda *a, **k: sent.append(a[0])):
        watch.main(); watch.main()
    assert len(sent) == 1 and sent[0][:3] == ["hermes", "send", "-t"] and "Zážitok 3" in sent[0][-1]
# the watchdog must still warn when the chat cannot be read, and one failed warning must not hide the next pair
with tempfile.TemporaryDirectory() as tmp:
    watch.STATE = Path(tmp) / "state.json"
    two = src + [dict(msg("t2", 5), ts=day * 1000), dict(msg("w2", 5, "Worksheet"), ts=day * 1000)]
    watch.save({"anchor": "w", "sources": two, "delivery": {}})
    sent = []
    def flaky(args, **kw):
        if "Zážitok 3" in args[-1]:
            raise subprocess.CalledProcessError(1, args)
        sent.append(args)
    def down(*a, **k):
        raise subprocess.CalledProcessError(1, "weft")
    with patch.object(sys, "argv", ["watch.py", "--watch"]), patch.object(watch.time, "time", return_value=day + 40 * 60), \
         patch.object(watch.subprocess, "check_output", side_effect=down), patch.object(watch.subprocess, "run", side_effect=flaky):
        try:
            watch.main()
            raise RuntimeError("a failed read or warning must fail the unit")
        except subprocess.CalledProcessError:
            pass
    assert len(sent) == 1 and "Zážitok 5" in sent[0][-1]
    assert list(json.loads(watch.STATE.read_text())["alerts"]) == [watch.pairs(two)[1]["key"]]
print("PASS: pairing, baseline, incremental reads, dedupe, persisted send guard, cursor gap, stale warning, chat down, failed warning")
