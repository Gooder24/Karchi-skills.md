#!/usr/bin/env python3
"""Timing from a Wayland client's WAYLAND_DEBUG=1 log (written for Atlas, works for any client). Newer libwayland (Arch) prints wall-clock [HH:MM:SS.us];
libwayland 1.23 (Debian 13) prints [ ms.us], the wall clock in microseconds modulo 2^32 (wraps every
~71.6 min). Both are read; times from the short form are unwrapped and compared modulo the wrap.

  wdlog.py LOG first-frame START_EPOCH     seconds from START to the first buffer attach, and to the
                                           end of the first burst of commits (UI settled)
  wdlog.py LOG after-key KEYCODE [N]       from the Nth-last press of KEYCODE to the end of the commit
                                           burst that follows it (evdev codes: 28 Enter)
  wdlog.py LOG scroll                      frames (buffer attaches) per second and frame gaps while
                                           wheel events arrive
A burst ends at the first gap of GAP seconds (default 1.5) without a commit.
"""
import os, re, statistics, sys, datetime as dt

GAP = float(os.environ.get("GAP", 1.5))
ts_re = re.compile(r"^\[(\d\d):(\d\d):(\d\d)\.(\d{6})\]")
ms_re = re.compile(r"^\[\s*(\d+)\.(\d{3})\]")
WRAP = 2**32 / 1e6  # seconds; period of the [ ms.us] form
short = False

def load(path):
    global short
    rows, offset, prev = [], 0.0, None
    with open(path, errors="replace") as f:
        for line in f:
            m = ts_re.match(line)
            if m:
                h, mi, s, us = map(int, m.groups())
                rows.append((h * 3600 + mi * 60 + s + us / 1e6, line))
                continue
            m = ms_re.match(line)
            if m:
                short = True
                t = int(m[1]) / 1e3 + int(m[2]) / 1e6
                if prev is not None and t < prev - WRAP / 2: offset += WRAP
                prev = t
                rows.append((t + offset, line))
    return rows

def commits(rows):
    return [t for t, l in rows if "-> wl_surface#" in l and ".commit()" in l]

def burst_end(times, start):
    last = None
    for t in times:
        if t < start: continue
        if last is not None and t - last > GAP: break
        last = t
    return last

def day_seconds(epoch):
    if short:
        return (float(epoch) * 1e6 % 2**32) / 1e6
    d = dt.datetime.fromtimestamp(float(epoch), dt.timezone.utc)
    return d.hour * 3600 + d.minute * 60 + d.second + d.microsecond / 1e6

def main():
    rows = load(sys.argv[1]); op = sys.argv[2]
    cs = commits(rows)
    if op == "first-frame":
        start = day_seconds(sys.argv[3])
        attach = next(t for t, l in rows if ".attach(wl_buffer" in l)
        end = burst_end(cs, attach)
        since = (lambda t: (t - start) % WRAP) if short else (lambda t: t - start)
        print(f"first_frame_s={since(attach):.3f} settled_s={since(end):.3f}")
    elif op == "after-key":
        code = sys.argv[3]; nth = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        presses = [t for t, l in rows if re.search(r"wl_keyboard#\d+\.key\(\d+, \d+, %s, 1\)" % code, l)]
        t0 = presses[-nth]
        end = burst_end(cs, t0)
        print(f"took_s={(end or t0) - t0:.3f} commits={sum(1 for t in cs if t0 <= t <= (end or t0))}")
    elif op == "scroll":
        axis = [t for t, l in rows if "wl_pointer#" in l and (".axis(" in l or ".axis_value120(" in l or ".axis_discrete(" in l)]
        if not axis: raise SystemExit("no wheel events in log")
        a, b = axis[0], axis[-1]
        # Frames are buffer attaches: GNOME/mutter sees two commits per frame (one without a
        # buffer), sway one, so counting commits doubled the rate on GNOME.
        frames = [t for t, l in rows if "-> wl_surface#" in l and ".attach(wl_buffer" in l]
        win = [t for t in frames if a <= t <= b + 0.1]
        gaps = [y - x for x, y in zip(win, win[1:])]
        dur = b - a
        p95 = sorted(gaps)[int(len(gaps) * 0.95)] if gaps else 0
        print(f"wheel_s={dur:.2f} fps={len(win) / dur:.1f} gap_median_ms={statistics.median(gaps) * 1000:.1f} "
              f"gap_p95_ms={p95 * 1000:.1f} gap_max_ms={max(gaps) * 1000:.1f}")
    else:
        raise SystemExit(__doc__)

main()
