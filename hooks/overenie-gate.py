#!/usr/bin/env python3
# Stop hook, wired in ~/.claude/settings.json on asus, x270, dell and e540.
# Karchi was burned again and again by "hotové" from the agent that built the change: on 7. 11. 2026 an
# audit of 343 T3 threads found him finding the breakage himself after a done-claim at least 20 times,
# while the independent verifier of the overenie skill, when it ran, caught errors the builder missed.
#
# Contract: a reply that ends a turn in which something was changed carries one line
#   Overenie: <path to overenie/.../verdikt.md or index.html written in this turn>
#   Overenie: neoverené – <what Karchi should try and what he should then see>
#   Overenie: netreba – <why: a research note, an internal file he will not use>
#   Overenie: prebieha – <what is still running>
# so he sees at a glance whether he has to look himself. Guessing done-claims from wording failed (a
# first version let "Opravené ... stará adresa už nefunguje" through), so the line is required, not
# inferred. A turn without it is sent back once. Decisions go to ~/.claude/overenie-gate.jsonl.
import json
import os
import re
import sys
import unicodedata
from datetime import datetime

LOG = os.environ.get("OVERENIE_GATE_LOG") or os.path.expanduser("~/.claude/overenie-gate.jsonl")

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit", "RemoteTrigger", "CronCreate", "CronDelete",
              "Workflow", "SendMessage", "PushNotification", "TaskStop"}
READONLY_AGENTS = {"Explore", "Plan", "claude-code-guide", "statusline-setup"}
# words in an MCP tool name (t3_thread_read, list_artifacts) that mark it as one that only looks
READONLY_MCP = {"read", "list", "get", "search", "status", "query", "guide", "wait", "capabilities",
                "describe", "snapshot", "screenshot", "find", "fetch", "resolve", "whoami", "usage",
                "profiles", "pending", "render"}
SEG = r"(?:^|[\s;&|(`'\"])(?:sudo\s+(?:-\S+\s+)*)?"
ARG = r"[^\n;|&]{0,400}?"  # bounded, so a pathological command line cannot make the regex slow
CHANGING_BASH = re.compile(
    SEG + r"(cp|mv|rm|rmdir|mkdir|touch|chmod|chown|ln|tee|truncate|patch|rsync|scp|pkill|reboot|unzip"
    r"|wrangler|live\.sh|land\.sh|nohup|systemd-run)(\s|$)"
    + r"|" + SEG + r"kill\s+(?!-0\b)\S"
    + r"|" + SEG + r"make(\s+(?!-n\b)\S|\s*$)"
    + r"|" + SEG + r"crontab\s+(?!-l\b)[-\w./~]"
    + r"|" + SEG + r"\./\S*(install|setup|deploy|land|live)\S*"
    + r"|" + SEG + r"git\s+(-[Cc]\s+(\"[^\"]*\"|'[^']*'|\S+)\s+)*(commit|push|merge|reset|rebase|checkout|switch|pull|clone"
    r"|rm|mv|add|apply|am|cherry-pick|revert|restore|worktree\s+add|branch\s+-[dDmM]|tag\s+(?!-l\b)[\w.-]"
    r"|stash(?!\s+(list|show)))"
    + r"|" + SEG + r"gh\s+(pr\s+(merge|create|edit|close|review)|issue\s+(create|close|edit|comment)|workflow\s+run"
    r"|release\s+create|repo\s+(create|edit|delete)|api\s" + ARG + r"(-X\s*(POST|PUT|PATCH|DELETE)|--method\s+(POST|PUT|PATCH|DELETE)|\s-[fF]\s))"
    + r"|" + SEG + r"systemctl\s+(--user\s+)?(--now\s+)?(start|restart|enable|disable|reload|stop|mask|daemon-reload)"
    + r"|" + SEG + r"(pm2\s+(restart|start|stop|delete|reload)|docker\s+(compose\s+)?(up|run|restart|build|rm|stop)"
    r"|(npm|pnpm|yarn|vp|bun)\s+(i|install|add|remove|publish|run\s+(build|deploy|migrate)|(run\s+)?(dev|start|serve))\b"
    r"|pip3?\s+install|uv\s+(add|pip\s+install|sync)|apt(-get)?\s+(install|remove|purge|upgrade|autoremove|dist-upgrade)"
    r"|pacman\s+-(S(?![ispg])|R|U)|yay\s+-S(?![ispg])|flatpak\s+(install|uninstall)|cargo\s+install|install\s+-\w"
    r"|hyprctl\s+(keyword|reload|dispatch\s+exec)|tailscale\s+(serve|funnel|up|set|cert)|gsettings\s+set"
    r"|loginctl\s+enable|ufw\s+(allow|deny|enable)|claude\s+mcp\s+(add|remove)|tar\s+-?\w*x|dd\s" + ARG + r"of=)"
    + r"|\bcurl" + ARG + r"(\s-X\s*(POST|PUT|PATCH|DELETE)|\s-\w*d|--data|--json|\s-F\s|--form|\s-o\s*(?!/dev/null)\S)"
    + r"|\bwget" + ARG + r"\s-O\s*(?!-|/dev/null)\S|\bfind" + ARG + r"\s-delete\b|writeFileSync|appendFileSync"
    + r"|(?i:(sqlite3|psql|mysql)\s" + ARG + r"\b(insert|update|delete|drop|alter|create)\b)|\s--apply\b|dennik\s+add"
    + r"|Stop-Process|Remove-Item|Set-Content|schtasks\s+/(Create|Delete|Change)"
    + r"|sed\s+(-\w*\s+)*-i|perl\s+-\w*i|open\([^)]{0,300}['\"][wax]b?\+?['\"]|\.write_text\(|\.write_bytes\("
    r"|json\.dump\("
    + r"|(?<![\d&>=<\-|])>>?\s*(?!/dev/|&)[~/.$\"'A-Za-z_]",
    re.M,
)
STATUS_LINE = re.compile(r"^[ \t>*_`#-]*overenie[ \t*]*[:\u2013\u2014-][ \t*]*([^\n]*)$", re.I | re.M)
# the status word must open the line: "Overenie: všetko beží a funguje" is not a status
# netreba needs a reason after a dash: "Overenie: netreba – len poznámky pre mňa"
STATUS_WORD = re.compile(r"^[`*_ ]*(neoveren\w*|prebieha|netreba(?=\s*[\u2013\u2014:-]\s*\S+\s+\S+\s+\S+))")
FENCE = re.compile(r"```.*?(```|$)", re.S)
FAILED_IN_REPLY = re.compile(r"(nepreslo|neda sa overit)")
# The verdict's own status lines (verifier-agents.md), or the older Slovak verdicts.
FAILED_IN_VERDICT = re.compile(r"(nepreslo|neda sa overit|^\s*(?:overall:|\d+\.)\s*\**(?:failed|unverifiable))", re.M)
PATH = re.compile(r"(?:[^\s`'\"()\[\]<>*,;]{0,300}/)?overenie/[^\s`'\"()\[\]<>*,;]{1,200}")
EVIDENCE_NAMES = {"verdikt.md", "index.html"}
DONE_WORDS = re.compile(r"\b(hotov\w*|funguje|funguju|funkcn\w*|opraven\w*|opravil\w*|fixnut\w*|fixol|spraven\w*"
                        r"|nasaden\w*|vsetko ide|done|works|fixed)\b")
NOT_A_USER_TURN = ("<task-notification", "this session is being continued", "<command-", "caveat:",
                   "[system notification", "background command", "monitor \"")


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def log(outcome, event, **extra):
    try:
        with open(LOG, "a") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"), "outcome": outcome,
                                "session": event.get("session_id"), "cwd": event.get("cwd"),
                                "thread": os.environ.get("T3CODE_THREAD_ID"), **extra},
                               ensure_ascii=False) + "\n")
    except OSError:
        pass


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except (AttributeError, TypeError, ValueError):
        return None


def user_text(o):
    """The text of a real message from Karchi, or None for tool results, notifications and meta lines."""
    if o.get("type") != "user" or o.get("isMeta") or o.get("isSidechain") or o.get("isCompactSummary"):
        return None
    c = (o.get("message") or {}).get("content")
    if isinstance(c, list):
        if not c or not all(isinstance(x, dict) and x.get("type") in ("text", "image") for x in c):
            return None
        c = " ".join(x.get("text", "") for x in c if x.get("type") == "text")
    if not isinstance(c, str) or norm(c.lstrip()[:40]).startswith(NOT_A_USER_TURN):
        return None
    return c


def read_turn(path):
    """(turn_start_epoch, tool_uses, final_text) since Karchi's last real message."""
    lines = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if isinstance(o, dict):
                lines.append(o)
    start = 0
    for i, o in enumerate(lines):
        if user_text(o) is not None:
            start = i
    turn = lines[start:]
    t0 = parse_ts(turn[0].get("timestamp")) if turn else None
    tools, texts = [], []
    for o in turn:
        if o.get("type") != "assistant" or o.get("isSidechain"):
            continue
        content = (o.get("message") or {}).get("content")
        for x in content if isinstance(content, list) else []:
            if not isinstance(x, dict):
                continue
            if x.get("type") == "tool_use":
                inp = x.get("input")
                tools.append((str(x.get("name")), inp if isinstance(inp, dict) else {}))
                texts = []  # only the text after the last tool call is the reply he reads
            elif x.get("type") == "text" and isinstance(x.get("text"), str):
                texts.append(x["text"])
    return t0, tools, "\n".join(texts)


def changed_something(tools):
    for name, inp in tools:
        if name in EDIT_TOOLS:
            return name
        if name in ("Agent", "Task") and inp.get("subagent_type") not in READONLY_AGENTS:
            return name
        if name.startswith("mcp__") and not READONLY_MCP & set(re.split(r"[_\-]", name.split("__")[-1].lower())):
            return name
        if name == "Bash" and CHANGING_BASH.search(str(inp.get("command", ""))):
            return "Bash: " + str(inp.get("command", ""))[:120]
    return None


def evidence(line, t0, cwd):
    """A verdikt.md or index.html under an overenie/ folder, non-empty and written in this turn."""
    for raw in PATH.findall(line):
        if ".." in raw:
            continue
        p = os.path.expanduser(raw.rstrip(".:"))
        if not os.path.isabs(p) and isinstance(cwd, str):
            p = os.path.join(cwd, p)
        p = os.path.realpath(p)
        if os.path.basename(p) not in EVIDENCE_NAMES or "/overenie/" not in p or "/.claude/" in p:
            continue
        try:
            st = os.stat(p)
        except OSError:
            continue
        if os.path.isfile(p) and st.st_size > 0 and (t0 is None or st.st_mtime >= t0 - 5):
            return p
    return None


def decide(event):
    if os.environ.get("OVERENIE_VERIFIER") or event.get("agent_id"):
        return None
    path = event.get("transcript_path")
    if not isinstance(path, str) or not os.path.isfile(path):
        return None
    t0, tools, text = read_turn(path)
    last = event.get("last_assistant_message")
    if isinstance(last, str) and last.strip():
        text = last
    change = changed_something(tools)
    if not change:
        return None
    lines = STATUS_LINE.findall(FENCE.sub("", text[-4000:]))
    status = lines[-1].strip()[:500] if lines else ""
    problem = ""
    if status:
        ev = evidence(status, t0, event.get("cwd"))
        if ev and FAILED_IN_VERDICT.search(norm(open(ev, errors="replace").read(200000))) \
                and not FAILED_IN_REPLY.search(norm(text)):
            problem = (f"{ev} records checks that failed or could not be verified, and the reply does not "
                       "say which (write neprešlo / nedá sa overiť for each in the reply)")
        elif ev:
            log("pass-evidence", event, evidence=ev)
            return None
        word = STATUS_WORD.match(norm(status))
        if problem:
            pass
        elif word and word.group(1).startswith("neoveren") and DONE_WORDS.search(norm(text[:300])):
            problem = "it says neoverené but its opening still calls the work hotové or funguje"
        elif word:
            log("pass-" + ("neoverene" if word.group(1).startswith("neoveren") else word.group(1)), event,
                status=status[:200])
            return None
    if event.get("stop_hook_active"):
        log("pass-after-block", event, status=status[:200], change=change)
        return None
    log("block", event, status=status[:200], change=change, opening=text[:200])
    why = problem or ("its 'Overenie:' line neither names an overenie/…/verdikt.md written "
                      "in this turn nor starts with neoverené, netreba or prebieha" if status
                      else "it has no 'Overenie:' line")
    return {"decision": "block", "reason": (
        f"overenie-gate: this turn changed something ({change[:80]}), but {why}. Karchi has been burned "
        "many times by 'hotové' from the agent that built the change, so every reply after a change "
        "ends with one line he can trust at a glance. Add exactly one, truthfully:\n"
        "- `Overenie: <full path to …/overenie/verdikt.md>` only after the independent verifier (skill overenie, "
        "verify.sh) wrote it in this turn;\n"
        "- `Overenie: neoverené – <what he should try and what he should then see>` when you did not "
        "or could not (then do not call it hotové or funguje anywhere in the reply);\n"
        "- `Overenie: netreba – <why, in a few words>` only when the change is nothing he will see or use;\n"
        "- `Overenie: prebieha – <what still runs>` only for work outside this thread, never for the verifier: "
        "wait for its verdict in this turn.\n"
        "Do not touch an overenie file just to pass this check."
    )}


def main():
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            return
        out = decide(event)
    except Exception:  # never break the session over this hook
        return
    if out:
        print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
