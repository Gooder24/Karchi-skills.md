#!/usr/bin/env python3
"""Drive a QEMU VM's keyboard, tablet and screen through its QMP socket.

  qmp.py SOCK key ctrl-shift-n [Return ...]   press combos (qcode names, '-' joins modifiers)
  qmp.py SOCK type 'text'                      type US-layout text
  qmp.py SOCK click X Y [left|right|middle]    move the tablet and click (screen pixels)
  qmp.py SOCK move X Y
  qmp.py SOCK drag X0 Y0 X1 Y1 [STEPS]          press at X0 Y0, move in STEPS steps, release at X1 Y1
  qmp.py SOCK wheel N [down|up] [HZ]           N wheel notches at HZ per second
  qmp.py SOCK shot FILE.png                    screendump
  qmp.py SOCK settle X0 Y0 X1 Y1 [STABLE] [TIMEOUT]
      seconds until the region reaches the look it then keeps for STABLE s (default 1.5)
Screen size comes from QMP_W/QMP_H (default 1366x768).
"""
import json, os, socket, sys, time

W = int(os.environ.get("QMP_W", 1366)); H = int(os.environ.get("QMP_H", 768))

class Qmp:
    def __init__(self, path):
        self.s = socket.socket(socket.AF_UNIX); self.s.connect(path)
        self.f = self.s.makefile("rw")
        json.loads(self.f.readline())
        self.cmd("qmp_capabilities")
    def cmd(self, name, **args):
        self.f.write(json.dumps({"execute": name, "arguments": args} if args else {"execute": name}) + "\n")
        self.f.flush()
        while True:
            r = json.loads(self.f.readline())
            if "event" in r: continue
            if "error" in r: raise SystemExit(f"qmp {name}: {r['error']}")
            return r.get("return")
    def events(self, evs):
        self.cmd("input-send-event", events=evs)

ALIAS = {"ctrl": "ctrl", "shift": "shift", "alt": "alt", "super": "meta_l", "Return": "ret", "Enter": "ret",
         "Escape": "esc", "BackSpace": "backspace", "Delete": "delete", "Home": "home", "End": "end",
         "Up": "up", "Down": "down", "Left": "left", "Right": "right", "Tab": "tab", "space": "spc",
         "Page_Down": "pgdn", "Page_Up": "pgup", ".": "dot", ",": "comma", "/": "slash", "-": "minus"}
for i in range(1, 13): ALIAS[f"F{i}"] = f"f{i}"

PLAIN = {" ": "spc", "-": "minus", "=": "equal", "[": "bracket_left", "]": "bracket_right", ";": "semicolon",
         "'": "apostrophe", "`": "grave_accent", "\\": "backslash", ",": "comma", ".": "dot", "/": "slash"}
SHIFTED = {"_": "minus", "+": "equal", "{": "bracket_left", "}": "bracket_right", ":": "semicolon",
           '"': "apostrophe", "~": "grave_accent", "|": "backslash", "<": "comma", ">": "dot", "?": "slash",
           "!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "^": "6", "&": "7", "*": "8", "(": "9", ")": "0"}

def qkey(code, down):
    return {"type": "key", "data": {"down": down, "key": {"type": "qcode", "data": code}}}

def combo(q, spec, hold=0.03):
    parts = spec.split("-") if spec not in ("-",) else ["-"]
    codes = [ALIAS.get(p, p.lower() if len(p) == 1 else p) for p in parts]
    for c in codes: q.events([qkey(c, True)]); time.sleep(hold)
    for c in reversed(codes): q.events([qkey(c, False)]); time.sleep(hold)

def typ(q, text):
    for ch in text:
        if ch.isalpha() and ch.isascii():
            codes = ["shift", ch.lower()] if ch.isupper() else [ch]
        elif ch.isdigit(): codes = [ch]
        elif ch in PLAIN: codes = [PLAIN[ch]]
        elif ch in SHIFTED: codes = ["shift", SHIFTED[ch]]
        elif ch == "\n": codes = ["ret"]
        else: raise SystemExit(f"cannot type {ch!r}")
        for c in codes: q.events([qkey(c, True)]); time.sleep(0.012)
        for c in reversed(codes): q.events([qkey(c, False)]); time.sleep(0.012)

def move(q, x, y):
    q.events([{"type": "abs", "data": {"axis": "x", "value": int(x * 32767 / (W - 1))}},
              {"type": "abs", "data": {"axis": "y", "value": int(y * 32767 / (H - 1))}}])

def button(q, b, down):
    return {"type": "btn", "data": {"down": down, "button": b}}

def region(q, path, x0, y0, x1, y1):
    q.cmd("screendump", filename=path)  # PPM: P6 W H 255 then RGB
    data = open(path, "rb").read()
    parts = data.split(b"\n", 3); w = int(parts[1].split()[0]); px = parts[3]
    return b"".join(px[(y * w + x0) * 3:(y * w + x1) * 3] for y in range(y0, y1, 2))

def settle(q, x0, y0, x1, y1, stable, timeout):
    path = f"/tmp/qmp-settle-{os.getpid()}.ppm"
    start = time.monotonic(); last = None; changed = start
    try:
        while time.monotonic() - start < timeout:
            now = time.monotonic(); cur = region(q, path, x0, y0, x1, y1)
            if cur != last: last, changed = cur, now
            elif now - changed >= stable: return changed - start
            time.sleep(max(0, 0.1 - (time.monotonic() - now)))
        return float("nan")
    finally:
        if os.path.exists(path): os.unlink(path)

def main():
    q = Qmp(sys.argv[1]); op, args = sys.argv[2], sys.argv[3:]
    if op == "key":
        for spec in args: combo(q, spec); time.sleep(0.05)
    elif op == "type": typ(q, " ".join(args))
    elif op == "move": move(q, float(args[0]), float(args[1]))
    elif op == "click":
        move(q, float(args[0]), float(args[1])); time.sleep(0.15)
        b = args[2] if len(args) > 2 else "left"
        q.events([button(q, b, True)]); time.sleep(0.06); q.events([button(q, b, False)])
    elif op == "drag":
        x0, y0, x1, y1 = map(float, args[:4]); steps = int(args[4]) if len(args) > 4 else 30
        move(q, x0, y0); time.sleep(0.2); q.events([button(q, "left", True)]); time.sleep(0.3)
        for i in range(1, steps + 1):
            move(q, x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps); time.sleep(0.04)
        time.sleep(0.5); q.events([button(q, "left", False)])
    elif op == "dclick":
        move(q, float(args[0]), float(args[1])); time.sleep(0.15)
        for _ in range(2):
            q.events([button(q, "left", True)]); time.sleep(0.04); q.events([button(q, "left", False)]); time.sleep(0.08)
    elif op == "wheel":
        n = int(args[0]); b = "wheel-" + (args[1] if len(args) > 1 else "down"); hz = float(args[2]) if len(args) > 2 else 60
        t = time.monotonic()
        for i in range(n):
            q.events([button(q, b, True)]); q.events([button(q, b, False)])
            t += 1 / hz; time.sleep(max(0, t - time.monotonic()))
    elif op == "shot":
        q.cmd("screendump", filename=os.path.abspath(args[0]), format="png")
    elif op == "settle":
        x0, y0, x1, y1 = map(int, args[:4])
        stable = float(args[4]) if len(args) > 4 else 1.5
        timeout = float(args[5]) if len(args) > 5 else 30
        print(f"settle_s={settle(q, x0, y0, x1, y1, stable, timeout):.2f}")
    else: raise SystemExit(__doc__)

main()
