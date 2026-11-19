#!/usr/bin/env python3
"""Logs when Outlook, Teams or an eSYST thread in T3 Code is the focused window on x270 (Hyprland).

Stdlib only, event-driven: it sleeps on Hyprland's event socket and writes one line per focus change, so it
costs nothing while he works. vykaz-okna.service runs it; vykaz turns the lines into work time.
Lines: ~/.local/share/vykaz/okna/YYYY-MM-DD.tsv  "epoch<TAB>druh<TAB>titul", druh = outlook|teams|t3|-
("-" = something else got focus, which ends the interval before it; other titles are not stored).
"""
import json, os, re, socket, subprocess, sys, time
from pathlib import Path

OUT = Path.home() / ".local/share/vykaz/okna"
T3_ESYST = re.compile(r"spotrex|obhajoba|esyst|hurbanov|eucf|crs ?40|firemn|zamestnanc", re.I)


def druh(cls, title):
    t = title or ""
    if re.search(r"\bOutlook\b", t) or cls.lower() in ("outlook", "ms-outlook"):
        return "outlook"
    if re.search(r"Microsoft Teams|\| Teams\b", t) or "teams" in cls.lower():
        return "teams"
    if cls == "com.t3tools.T3Code" and T3_ESYST.search(t):
        return "t3"
    return "-"


def aktivne():
    try:
        w = json.loads(subprocess.run(["hyprctl", "activewindow", "-j"], capture_output=True, text=True,
                                      timeout=5).stdout or "{}")
    except (ValueError, subprocess.SubprocessError):
        return "-", ""
    d = druh(w.get("class", ""), w.get("title", ""))
    return d, (w.get("title", "") if d != "-" else "")


def zapis(d, title):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / f"{time.strftime('%Y-%m-%d')}.tsv", "a") as f:
        f.write(f"{int(time.time())}\t{d}\t{title.replace(chr(9), ' ')[:160]}\n")


def main():
    run = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    if not sig:
        sig = max(os.listdir(f"{run}/hypr"), key=lambda s: os.path.getmtime(f"{run}/hypr/{s}"))
        os.environ["HYPRLAND_INSTANCE_SIGNATURE"] = sig
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(f"{run}/hypr/{sig}/.socket2.sock")
    last, addr = None, b""
    zapis(*aktivne())
    buf = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            sys.exit("Hyprland socket closed")  # systemd restarts it with the next session
        buf += chunk
        *lines, buf = buf.split(b"\n")
        # focus moved, or the focused window changed its title (another thread in T3, another mail);
        # title changes of other windows (terminal spinners, music) are ignored
        hit = False
        for l in lines:
            if l.startswith(b"activewindowv2>>"):
                addr, hit = l[16:], True
            elif l.startswith(b"windowtitlev2>>") and l[15:].split(b",", 1)[0] == addr:
                hit = True
        if not hit:
            continue
        cur = aktivne()
        if cur != last:
            zapis(*cur)
            last = cur


if __name__ == "__main__":
    main()
