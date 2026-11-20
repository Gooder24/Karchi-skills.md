# Runs t3-links' renewal logic against fake machines (no ssh, no T3): python3 test.py <t3-links>
import importlib.machinery, importlib.util, json, os, sys, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
loader = importlib.machinery.SourceFileLoader("t3links", sys.argv[1])
spec = importlib.util.spec_from_loader("t3links", loader); m = importlib.util.module_from_spec(spec); loader.exec_module(m)
tmp = Path(tempfile.mkdtemp()); m.STATE = str(tmp / "state"); os.makedirs(m.STATE)
m.time.sleep = lambda s: None
fails = []
def check(c, what): print(("ok   " if c else "FAIL ") + what); c or fails.append(what)
URL = {h: u for h, (_, u) in m.MACHINES.items()}

class World:
    """Four fake machines. links[source][url] = dict as `t3 environment list --json` prints it."""
    def __init__(s, now, down=(), expires=None, extra=None):
        s.now, s.down, s.linked, s.cmds = now, set(down), [], []
        s.links = {a: {URL[b]: {"urls": [URL[b]], "status": "reachable", "lastError": None,
                                "expiresAt": (expires or {}).get(f"{a}->{b}", (now + timedelta(days=20)).isoformat())}
                       for b in m.MACHINES if b != a} for a in m.MACHINES}
        for pair, fields in (extra or {}).items():
            a, b = pair.split("->"); s.links[a][URL[b]].update(fields)
    def on(s, host, cmd, timeout=120):
        s.cmds.append(cmd)
        if host in s.down: return 255, "", "ssh: connect to host: timed out"
        if cmd == m.CLI: return 0, "/fake/t3\n", ""
        if cmd.endswith("environment list --json"): return 0, json.dumps(list(s.links[host].values())), ""
        if " pair " in cmd: return 0, "█▀▀ QR █▀▀\nToken: SECRETCODE\n", ""
        if " environment link " in cmd:
            assert "SECRETCODE" in cmd
            url = cmd.split(" environment link ")[1].split()[0]
            until = (s.now + timedelta(days=30)).isoformat()
            s.links[host][url] = {"urls": [url], "status": "reachable", "lastError": None, "expiresAt": until}
            s.linked.append(f"{host}->{url}")
            return 0, f"Linked x (id) with full-access access, until {until}.\n", ""
        raise AssertionError(cmd)

def run(w, everything=False):
    m.on = w.on
    real = m.datetime
    class FakeDT(real):
        @classmethod
        def now(cls, tz=None): return w.now if tz else w.now.astimezone().replace(tzinfo=None)
    m.datetime = FakeDT
    try: return m.run(everything)
    finally: m.datetime = real
def state(): return json.load(open(Path(m.STATE) / "state.json"))
def fresh(): (Path(m.STATE) / "state.json").unlink(missing_ok=True)
t0 = datetime(2026, 11, 20, 11, 30, tzinfo=timezone.utc)

w = World(t0); rc = run(w)
check(w.linked == [] and rc == 0, "nothing due: no relink, exit 0")
w = World(t0, expires={"asus->dell": (t0 + timedelta(days=5)).isoformat()}); rc = run(w)
check(w.linked == ["asus->" + URL["dell"]] and state()["expires"]["asus->dell"] == (t0 + timedelta(days=30)).isoformat(),
      "due within 7 days: only that pair relinked, expiry taken from the link output")
w = World(t0); run(w, everything=True)
check(len(w.linked) == 12, "--all relinks all 12 pairs")
check("SECRETCODE" not in (Path(m.STATE) / "log").read_text(), "pairing code never in the log")
w = World(t0, extra={"dell->e540": {"lastError": "HTTP 401 Unauthorized"}}); run(w)
check(w.linked == ["dell->" + URL["e540"]], "a link whose last use failed (revoked token) is relinked although 20 days are left")
w = World(t0); del w.links["e540"][URL["asus"]]; run(w)
check(w.linked == ["e540->" + URL["asus"]], "a missing link is linked again")

# x270 asleep: no alarm for 3 days, then an alarm (exit 1) that status shows; recovery clears it
fresh()
for day in range(5):
    w = World(t0 + timedelta(days=day), down={"x270"}); rc = run(w)
    if day < 3: check(rc == 0 and not state()["alarms"], f"x270 down day {day}: no alarm yet")
check(rc == 1 and "x270->asus" in state()["alarms"], "x270 down 4+ days with unknown expiry: alarm, exit 1")
w = World(t0 + timedelta(days=5)); rc = run(w)
check(rc == 0 and not state()["alarms"] and not state()["failing_since"], "x270 back: alarm and failing state cleared")
# a known expiry close, target down
fresh()
w = World(t0, down={"e540"}, expires={"asus->e540": (t0 + timedelta(days=1)).isoformat()}); rc = run(w)
check(rc == 1 and state()["alarms"]["asus->e540"].startswith("expires "), "expiry in 1 day, target down: alarm with the date")
check("dell->e540" not in state()["alarms"], "20 days left: no alarm even though the target is down")
# a link deleted while its target is down: the old expiry must not hide it
fresh()
w = World(t0); run(w)
w = World(t0 + timedelta(days=1), down={"dell"}); del w.links["asus"][URL["dell"]]; run(w)
check("asus->dell" not in state()["expires"], "deleted link is not reported with its old expiry")
# a busy database: retried with a fresh code; errors without stack frames or code
fresh()
class Busy(World):
    n = 0
    def on(s, host, cmd, timeout=120):
        if " environment link " in cmd and Busy.n < 2:
            Busy.n += 1
            return 1, "", "ERROR (#2): effect/sql/SqlError: Failed to execute statement\n  [cause]: Error: database is locked\n    at Worker.emit (node:events:514:20)\n  }"
        return super().on(host, cmd, timeout)
w = Busy(t0, expires={"asus->dell": (t0 + timedelta(days=5)).isoformat()}); rc = run(w)
logtext = (Path(m.STATE) / "log").read_text()
check(w.linked == ["asus->" + URL["dell"]] and rc == 0 and "database is locked" in logtext and "Worker.emit" not in logtext,
      "database locked twice: third try links, log has the message without the stack")
# a list that is locked once: retried, no failure
class BusyList(World):
    n = 0
    def on(s, host, cmd, timeout=120):
        if cmd.endswith("environment list --json") and host == "asus" and BusyList.n == 0:
            BusyList.n = 1
            return 1, "", "ERROR: database is locked"
        return super().on(host, cmd, timeout)
fresh(); w = BusyList(t0); rc = run(w)
check(rc == 0 and not state()["failing_since"], "a list locked once is retried")
# a failing link whose output echoes the code
class Echo(World):
    def on(s, host, cmd, timeout=120):
        if " environment link " in cmd: return 1, "bad code SECRETCODE\n", ""
        return super().on(host, cmd, timeout)
fresh(); w = Echo(t0, expires={"asus->dell": (t0 + timedelta(days=1)).isoformat()}); run(w)
check("SECRETCODE" not in (Path(m.STATE) / "log").read_text() + json.dumps(state()), "a code echoed in an error is masked")
# worst case time: every pair fails every try
slept = []
m.time.sleep = slept.append
class Never(World):
    def on(s, host, cmd, timeout=120):
        if " environment link " in cmd: return 1, "", "Error: database is locked"
        return super().on(host, cmd, timeout)
fresh(); w = Never(t0); run(w, everything=True)
check(sum(slept) <= 15 * 60, f"all 12 pairs failing: {sum(slept)} s of retry waits, within the 60 min service timeout")
# the inbox is never touched
check(not any("inbox" in c for c in w.cmds), "no command touches the inbox")
sys.exit(1 if fails else 0)
