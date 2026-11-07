#!/usr/bin/env python3
"""Inventory of every recurring or always-on process on Karchi's machines, as JSON rows.

Usage (on asus): python3 inventory.py > procesy.json
Reads only: systemd timers and services, crontabs, docker containers, T3 scheduled tasks
(statev2.sqlite opened read-only), over ssh on each machine. Distro units are
skipped: only units whose file lives in /etc/systemd/system or the user's home count.
What runs AI and on which subscription is not visible from outside, so KNOWN below says it; a
process KNOWN does not name is reported with ai "?" so it shows up as unclassified on the dashboard.
"""
import datetime as dt
import json
import re
import subprocess
import sys

MACHINES = {  # device label -> ssh command prefix ([] = this machine)
    "asus": [],
    "dell": ["ssh", "-o", "ConnectTimeout=6", "-o", "BatchMode=yes", "dell"],
    "e540": ["ssh", "-o", "ConnectTimeout=6", "-o", "BatchMode=yes", "e540"],
    "x270": ["ssh", "-o", "ConnectTimeout=6", "-o", "BatchMode=yes", "x270"],
    "vps": ["ssh", "-o", "ConnectTimeout=6", "-o", "BatchMode=yes", "x270",
            "ssh", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "root@81.2.239.39"],
}

# Runs on each machine; prints one JSON object per line.
REMOTE = r'''
echo '{"kind": "host"}'
emit() { python3 -c 'import json,sys; print(json.dumps(dict(zip(sys.argv[1::2], sys.argv[2::2]))))' "$@"; }
argv() { "$@" 2>/dev/null | grep -o 'argv\[\]=[^;]*' | head -1 | cut -c8-220; }
for t in $(systemctl --user list-timers --all --no-legend 2>/dev/null | awk '{print $(NF-1)}'); do
  s=$(systemctl --user show -p Unit --value $t)
  emit kind timer name "${t%.timer}" when "$(systemctl --user show -p TimersCalendar,TimersMonotonic --value $t | tr '\n' ' ')" \
    cmd "$(argv systemctl --user show -p ExecStart --value $s)" desc "$(systemctl --user show -p Description --value $s)" \
    next "$(systemctl --user show -p NextElapseUSecRealtime --value $t)" scope user
done
for t in $(systemctl list-timers --all --no-legend 2>/dev/null | awk '{print $(NF-1)}'); do
  case "$(systemctl show -p FragmentPath --value $t)" in /etc/*) ;; *) continue;; esac
  s=$(systemctl show -p Unit --value $t)
  emit kind timer name "${t%.timer}" when "$(systemctl show -p TimersCalendar,TimersMonotonic --value $t | tr '\n' ' ')" \
    cmd "$(argv systemctl show -p ExecStart --value $s)" desc "$(systemctl show -p Description --value $s)" \
    next "$(systemctl show -p NextElapseUSecRealtime --value $t)" scope system
done
crontab -l 2>/dev/null | grep -v -E '^\s*(#|$)' | while read -r m h dom mon dow cmd; do
  emit kind cron name "$(basename "${cmd%% *}")" when "$m $h $dom $mon $dow" cmd "$cmd" desc "" scope user
done
for u in $(systemctl --user list-units --type=service --state=running --no-legend 2>/dev/null | awk '{print $1}'); do
  case "$(systemctl --user show -p FragmentPath --value $u)" in "$HOME"/*|*/karchi-*) ;; *) continue;; esac
  emit kind service name "${u%.service}" when "stále" cmd "$(argv systemctl --user show -p ExecStart --value $u)" \
    desc "$(systemctl --user show -p Description --value $u)" scope user
done
for u in $(systemctl list-units --type=service --state=running --no-legend 2>/dev/null | awk '{print $1}'); do
  case "$(systemctl show -p FragmentPath --value $u)" in /etc/systemd/system/*) ;; *) continue;; esac
  emit kind service name "${u%.service}" when "stále" cmd "$(argv systemctl show -p ExecStart --value $u)" \
    desc "$(systemctl show -p Description --value $u)" scope system
done
{ docker ps --format '{{.Names}}|{{.Image}}|{{.Status}}' 2>/dev/null || sudo -n docker ps --format '{{.Names}}|{{.Image}}|{{.Status}}' 2>/dev/null; } |
  while IFS='|' read -r n i st; do emit kind container name "$n" when "stále" cmd "$i" desc "$st" scope docker; done
python3 - <<'PY' 2>/dev/null
import json, os, sqlite3
p = os.path.expanduser("~/.t3/userdata/statev2.sqlite")
if os.path.exists(p):
    c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    for title, en, sch, model, last, runs, nxt in c.execute(
            "select title, enabled, schedule_json, model_selection_json, last_run_status, run_count, next_run_at from scheduled_tasks"):
        m = json.loads(model or "{}")
        eff = [o["value"] for o in m.get("options", []) if o.get("id") == "effort"]
        print(json.dumps({"kind": "t3", "name": title, "when": sch, "cmd": "", "desc": f"last={last} runs={runs}",
                          "model": (m.get("model") or "") + (f" {eff[0]}" if eff else ""), "enabled": str(en), "next": nxt or ""}))
PY
'''

# What each process is, by device and name. ai: "áno" (calls a model), "spúšťa" (starts AI work
# elsewhere), "nie". sub: which subscription or account pays.
CLAUDE = "Claude (administrativa@esyst.sk)"
KNOWN = {
    ("asus", "limit-ping"): ("áno", CLAUDE, "Haiku 5.5", "posúva 5-hodinové okno limitu Claude na 06/11/16/21 h"),
    ("asus", "codex-limit-ping"): ("áno", "Codex (ChatGPT Plus)", "gpt-6-luna", "posúva 5-hodinové okno limitu Codex na 3/4 okna Claude (04:45/09:45/14:45/19:45 h)"),
    ("asus", "reboot-when-idle"): ("nie", "", "", "reštart po aktualizácii, len keď nič nebeží"),
    ("asus", "diktovanie"): ("áno", CLAUDE, "Whisper lokálne + Haiku 5.5", "prepis reči pre voxtype na x270, text čistí Haiku"),
    ("asus", "spevnik-audio"): ("áno", CLAUDE, "Whisper, demucs lokálne + Haiku 5.5", "import piesne z nahrávky (akordy, text, tagy)"),
    ("asus", "prehlad"): ("nie", "", "", "Prehľad dvora: táto stránka, číta stroje každých 30 min"),
    ("asus", "Nočný worker"): ("áno", CLAUDE, None, "revízia inboxu a jedna položka za noc"),
    ("dell", "t3-context"): ("nie", "", "", "export tvojich T3 správ zo všetkých strojov"),
    ("dell", "partsheet-sync"): ("nie", "", "", "Partsheet: piesne zo spevnik.mustangy.sk"),
    ("dell", "spravy-shots-cleanup"): ("nie", "", "", "jednorazové zmazanie screenshotov"),
    ("dell", "lifeos"): ("nie", "", "", "lifeOS: EduPage a kalendár"),
    ("dell", "partsheet-demo"): ("nie", "", "", "partsheet.dvoriste.xyz"),
    ("dell", "t3code"): ("spúšťa", CLAUDE, "", "T3 server dellu (vlákna, plánované úlohy)"),
    ("dell", "cloudflared"): ("nie", "Cloudflare (free)", "", "tunel dvoriste.xyz, beta, import, partsheet"),
    ("dell", "Babysit t3code#24095 + #25585 (8:00)"): ("áno", CLAUDE, None, "sleduje tvoje issue a PR v pingdotgg/t3code"),
    ("dell", "Babysit t3code#24095 + #25585 (18:00)"): ("áno", CLAUDE, None, "sleduje tvoje issue a PR v pingdotgg/t3code"),
    ("x270", "t3-limit-watcher"): ("spúšťa", CLAUDE, "", "po resete 5h limitu pošle prerušeným vláknam „Continue“"),
    ("x270", "t3-limit-report"): ("nie", "", "", "jednorazová správa zo 14. 10."),
    ("x270", "lifeos-kalendarix-sync"): ("nie", "", "", "rozvrh z EduPage do Kalendarixu"),
    ("x270", "spravy-shots-cleanup"): ("nie", "", "", "jednorazové zmazanie screenshotov"),
    ("x270", "voxtype"): ("spúšťa", CLAUDE, "", "diktovanie push-to-talk, prepis na asuse"),
    ("x270", "usb-autopen-ws9"): ("nie", "", "", "otvorí USB kľúč na ploche 9"),
    ("x270", "tailscale-control-tunel"): ("nie", "Tailscale", "", "SSH tunel na VPS pre koordinačný server Tailscale"),
    ("x270", "Dell: overiť spevník po reštarte"): ("áno", CLAUDE, None, "jednorazová kontrola z 30. 10."),
}
PREFIX = [  # (device, name prefix) -> same tuple; first match wins
    (("asus", "matrix-spike-"), ("nie", "", "", "Správy: Matrix server a mosty")),
    (("x270", "karchi-"), ("nie", "", "", "KarchiOS: služba plochy")),
    (("vps", "spotrex-skuska-"), ("nie", "", "", "eSYST SPOTREX: skúšobná kópia")),
    (("vps", "spotrex-vpn-pokus"), ("nie", "", "", "eSYST SPOTREX: pokus s VPN")),
    (("vps", "spotrex-"), ("nie", "", "", "eSYST SPOTREX")),
]

KIND = {"timer": "časovač", "cron": "cron", "service": "služba", "container": "kontajner",
        "t3": "T3 úloha"}


DAYS = {"Mon": "pondelok", "Tue": "utorok", "Wed": "streda", "Thu": "štvrtok", "Fri": "piatok", "Sat": "sobota", "Sun": "nedeľa"}


def human_calendar(cal):
    m = re.fullmatch(r"(?:(\w{3}) )?\*-\*-\* (\d\d):(\d\d):00", cal)
    if m:
        return f"{DAYS.get(m[1], m[1]) if m[1] else 'denne'} {m[2]}:{m[3]}"
    m = re.fullmatch(r"\*-\*-\* \*:00/(\d+):00", cal)
    if m:
        return f"každých {int(m[1])} min"
    m = re.fullmatch(r"(\d{4}-\d\d-\d\d) (\d\d:\d\d):00", cal)
    if m:
        return f"raz {m[1]} {m[2]}"
    return cal


def when_text(r):
    w = r.get("when", "")
    if r["kind"] == "t3":
        s = json.loads(w or "{}")
        return {"fixed_time": f"denne {s.get('timeOfDay')}", "interval": f"každých {int(s.get('everyMs', 0)) // 60000} min",
                "once": f"raz {s.get('runAt', '')[:16]}", "webhook": "webhook"}.get(s.get("type"), w)
    if r["kind"] == "cron":
        m = re.fullmatch(r"(\d+) ([\d,]+) \* \* (\*|1-5)", w.strip())
        if m:
            hours = ", ".join(f"{int(h):02d}:{int(m[1]):02d}" for h in m[2].split(","))
            return f"{'denne' if m[3] == '*' else 'po–pi'} {hours}"
        return f"cron {w}"
    if r["kind"] == "timer":
        cal = w.split("OnCalendar=")[1].split(";")[0].strip() if "OnCalendar=" in w else ""
        mono = [p.split("=")[1].split(";")[0].strip() for p in w.split("{") if "OnUnitActiveUSec=" in p]
        return human_calendar(cal) if cal else (f"každých {mono[0]}" if mono else w.strip())
    return w


def classify(device, r):
    hit = KNOWN.get((device, r["name"]))
    if not hit:
        hit = next((v for (d, p), v in PREFIX if d == device and r["name"].startswith(p)), None)
    return hit


def main():
    now = dt.datetime.now(dt.timezone.utc)
    rows, missing = [], []
    for device, prefix in MACHINES.items():
        cmd = prefix + ["bash", "-s"] if prefix else ["bash", "-s"]
        try:
            out = subprocess.run(cmd, input=REMOTE, capture_output=True, text=True, timeout=90).stdout
        except subprocess.TimeoutExpired:
            out = ""
        got = [json.loads(l) for l in out.splitlines() if l.startswith("{")]
        if not any(r["kind"] == "host" for r in got):
            missing.append(device)
        for r in got:
            if r["kind"] == "host":
                continue
            if r["kind"] == "timer" and r["name"] in ("launchpadlib-cache-clean",):
                continue
            hit = classify(device, r)
            ai, sub, model, purpose = hit if hit else ("?", "?", "", r.get("desc", ""))
            model = r.get("model") if model is None else model
            enabled = r.get("enabled", "1") == "1"
            once = r["kind"] == "timer" and "OnCalendar=20" in r.get("when", "")
            expired = once and not r.get("next")
            state = "vypnuté" if not enabled else ("neplatné" if expired else ("jednorazové" if once else "beží"))
            flag = ""
            if state in ("vypnuté", "neplatné"):
                flag = "zvyšok: už nič nerobí, zmazať"
            elif ai == "?":
                flag = "nezaradené: neviem, čo robí a kto platí"
            elif re.search(r"pokus|skuska|test", r["name"]) and r["kind"] in ("container", "service"):
                flag = "skúšobné, beží natrvalo"
            group = next((v[3] for (d, p), v in PREFIX if d == device and r["name"].startswith(p)), r["name"])
            rows.append({
                "zariadenie": device, "nazov": r["name"], "typ": KIND[r["kind"]], "kedy": when_text(r),
                "ai": ai, "predplatne": sub or "—", "model": model or "—", "na_co": purpose, "stav": state,
                "skupina": group, "chaos": flag, "prikaz": r.get("cmd", "")[:160],
                # Raw schedule for the dashboard, which works out the next run itself.
                "druh": r["kind"], "kedy_raw": r.get("when", ""), "dalsi_raw": r.get("next", ""),
            })
    json.dump({"generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "missing": missing, "rows": rows},
              sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
