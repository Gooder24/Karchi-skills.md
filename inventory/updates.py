#!/usr/bin/env python3
"""Update status of every machine and of the custom tools Karchi runs, as JSON rows.

Usage (on asus): python3 updates.py > aktualizacie.json
System: apt on the Debian machines, pacman on x270 (pending count, last upgrade, automatic or not).
Custom tools: what is installed by hand on asus (whisper, demucs, Matrix bridges, Rerun...) against
the newest release on PyPI or GitHub. AI CLIs (Claude Code, Codex) are left out: T3 Code keeps those.
Reads only; GitHub goes through `gh api` so the rate limit is the logged-in one.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inventory import MACHINES  # noqa: E402

HOME = os.path.expanduser("~")

SYSTEM = r'''
if command -v pacman >/dev/null; then
  echo "kind=pacman"
  echo "pending=$(checkupdates 2>/dev/null | wc -l)"
  echo "last=$(grep -h 'starting full system upgrade' /var/log/pacman.log 2>/dev/null | tail -1 | cut -c2-11)"
  echo "auto=0"
else
  echo "kind=apt"
  echo "pending=$(apt list --upgradable 2>/dev/null | grep -c upgradable)"
  echo "last=$(grep -h '^Start-Date' /var/log/apt/history.log 2>/dev/null | tail -1 | awk '{print $2}')"
  if [ "$(systemctl is-enabled unattended-upgrades 2>/dev/null)" = enabled ]; then echo "auto=1"; else echo "auto=0"; fi
  echo "next=$(systemctl show -p NextElapseUSecRealtime --value apt-daily-upgrade.timer 2>/dev/null)"
fi
'''

# (name, project, how to read the installed version, where the newest one is published)
TOOLS = [
    ("faster-whisper (diktovanie)", "diktovanie", ["pip", "diktovanie/venv", "faster-whisper"], ["pypi", "faster-whisper"]),
    ("faster-whisper (spevník import)", "spevnik-import", ["pip", "spevnik-audio/venv", "faster-whisper"], ["pypi", "faster-whisper"]),
    ("demucs (spevník import)", "spevnik-import", ["pip", "spevnik-audio/venv", "demucs"], ["pypi", "demucs"]),
    ("llama (lokálny Qwen)", "lokalne-ai", ["cmd", ".local/bin/llama", "--version"], ["gh", "ggml-org/llama.cpp"]),
    ("mautrix-whatsapp", "matrix", ["cmd", "matrix-spike/bin/mautrix-whatsapp", "--version"], ["gh", "mautrix/whatsapp"]),
    ("mautrix-meta (Messenger, Instagram)", "matrix", ["cmd", "matrix-spike/bin/mautrix-meta", "--version"], ["gh", "mautrix/meta"]),
    ("mautrix-telegram", "matrix", ["cmd", "matrix-spike/bin/mautrix-telegram", "--version"], ["gh", "mautrix/telegram"]),
    ("mautrix-discord", "matrix", ["cmd", "matrix-spike/bin/mautrix-discord", "--version"], ["gh", "mautrix/discord"]),
    ("tuwunel (Matrix server)", "matrix", ["cmd", "matrix-spike/bin/tuwunel", "--version"], ["gh", "matrix-construct/tuwunel"]),
    ("caddy (Správy, Rerun HTTPS)", "stroje", ["cmd", "matrix-spike/bin/caddy", "version"], ["gh", "caddyserver/caddy"]),
    ("cinny (web Správ)", "matrix", ["git", "matrix-spike/cinny"], ["gh", "cinnyapp/cinny"]),
    ("Rerun", "rerun", ["git", "rerun"], ["gh", "rerun-build/rerun"]),
]

SYSTEM_PROJECT = "stroje"


def run(cmd, timeout=60, **kw):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kw).stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def installed(how):
    kind, path, *rest = how
    if kind == "pip":
        out = run([os.path.join(HOME, path, "bin", "pip"), "show", rest[0]])
        m = re.search(r"^Version: (.+)$", out, re.M)
        return (m[1].strip() if m else ""), None
    if kind == "cmd":
        out = run([os.path.join(HOME, path), *rest]).strip().splitlines()
        line = out[0] if out else ""
        built = None
        for pat, fmt in ((r"built at \w+, (\d+ \w+ \d{4})", "%d %b %Y"), (r"\((\w+ \d+ \d{4})", "%b %d %Y")):
            m = re.search(pat, line)
            if m:
                built = dt.datetime.strptime(m[1], fmt).date()
        m = re.search(r"v?(\d+[\d.]*\d)", line.split("(")[0]) or re.search(r"version: (\d+)", line)
        return (m[1] if m else line[:40]), built
    if kind == "git":
        return run(["git", "-C", os.path.join(HOME, path), "describe", "--tags"]).strip(), None
    return "", None


def newest(where):
    kind, name = where
    if kind == "pypi":
        out = run(["curl", "-fsS", "--max-time", "20", f"https://pypi.org/pypi/{name}/json"])
        try:
            d = json.loads(out)
            v = d["info"]["version"]
            up = d["releases"].get(v) or [{}]
            return v, (up[0].get("upload_time") or "")[:10]
        except (ValueError, KeyError):
            return "", ""
    out = run(["gh", "api", f"repos/{name}/releases/latest", "--jq", "[.tag_name, .published_at] | @tsv"])
    if not out.strip():
        out = run(["gh", "api", f"repos/{name}/tags", "--jq", ".[0].name"])
        return out.strip(), ""
    tag, _, date = out.strip().partition("\t")
    return tag, date[:10]


def norm(v):
    return re.sub(r"^v", "", v.split("-")[0]).strip()


def behind(have, have_built, latest, latest_date):
    if not have or not latest:
        return None
    if norm(have) == norm(latest):
        return False
    if have_built and latest_date:
        return dt.date.fromisoformat(latest_date) > have_built
    return True


def main():
    rows = []
    for device, prefix in MACHINES.items():
        out = run(prefix + ["bash", "-s"] if prefix else ["bash", "-s"], input=SYSTEM, timeout=120)
        kv = dict(l.split("=", 1) for l in out.splitlines() if "=" in l)
        if not kv:
            rows.append({"zariadenie": device, "nazov": "systém", "projekt": SYSTEM_PROJECT, "stav": "nedostupné",
                         "ma": "", "najnovsie": "", "caka": None, "auto": False, "posledne": "", "dalsi_raw": ""})
            continue
        pending = int(kv.get("pending") or 0)
        auto = kv.get("auto") == "1"
        rows.append({
            "zariadenie": device, "nazov": f"systém ({kv.get('kind')})", "projekt": SYSTEM_PROJECT,
            "ma": "", "najnovsie": "", "caka": pending, "auto": auto, "posledne": kv.get("last", ""),
            "dalsi_raw": kv.get("next", "") if auto else "",
            "stav": "aktuálne" if pending == 0 else ("čaká na automatiku" if auto else "treba ručne"),
        })
    for name, project, how, where in TOOLS:
        have, built = installed(how)
        latest, date = newest(where)
        b = behind(have, built, latest, date)
        rows.append({
            "zariadenie": "asus", "nazov": name, "projekt": project, "ma": have, "najnovsie": latest,
            "vydane": date, "caka": None, "auto": False, "posledne": "", "dalsi_raw": "",
            "stav": "neviem overiť" if b is None else ("treba ručne" if b else "aktuálne"),
        })
    json.dump({"generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "rows": rows},
              sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
