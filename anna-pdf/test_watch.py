#!/usr/bin/env python3
import contextlib
import importlib.util
import io
import json
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
print("PASS: pairing, baseline, incremental reads, dedupe, persisted send guard, cursor gap")
