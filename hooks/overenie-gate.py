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
# a ``` or ~~~ block, closed only by the same marker it opened with
FENCE = re.compile(r"(`{3}|~{3}).*?(?:\1|$)", re.S)
FAILED_IN_REPLY = re.compile(r"(nepreslo|neda sa overit|opravene[\s,\u2013\u2014-]+(?:a\s+)?neoveren)")
# Findings of one verifier section: its numbered checks that did not pass, or its Broken / Unverified lines,
# whichever is more (a failed check usually has its own Broken line).
FAILED_CHECK = re.compile(r"^\s*\d+\.\s*\**(?:failed|unverifiable)", re.M)
OVERALL_FAILED = re.compile(r"^\s*overall:\s*\**(?:failed|unverifiable)", re.M)
FINDING_LINE = re.compile(r"^\s*(?:broken|unverified):", re.M)
# The verdict's own status lines (verifier-agents.md), or the older Slovak verdicts.
FAILED_IN_VERDICT = re.compile(r"(nepreslo|neda sa overit|^\s*(?:overall:|\d+\.)\s*\**(?:failed|unverifiable))", re.M)
PATH = re.compile(r"(?:[^\s`'\"()\[\]<>*,;]{0,300}/)?overenie/[^\s`'\"()\[\]<>*,;]{1,200}")
# an absolute or ~ path that contains spaces, such as ~/Obhajoba práce/overenie/verdikt.md
SPACED_PATH = re.compile(r"(?:~|/)[^\n`'\"<>*]{0,300}?/overenie/[^\n`'\"<>*]{0,200}?(?:verdikt[\w.-]*\.md|index\.html)(?!\.?[\w-])")
# verify.sh takes another verdict name as its second argument: overenie/verdikt-<topic>.md
EVIDENCE_NAME = re.compile(r"(?:verdikt(?:-[\w.-]+)?\.md|index\.html)$")
DONE_WORDS = re.compile(r"\b(hotov\w*|funguje|funguju|funkcn\w*|opraven\w*|opravil\w*|fixnut\w*|fixol|spraven\w*"
                        r"|nasaden\w*|vsetko ide|done|works|fixed)\b")
# The opening is the sentence before the **Hotové:** or **Nehotové:** heading line of AGENTS.md „Koniec odpovede“.
OPENING_END = re.compile(r"(?m)^\s*#*\s*\**(?:ne)?hotove:?\**:?\s*(?:nic(?:\s+nechyba)?\.?|[\u2013\u2014-])?\s*$")
# A Nehotové row whose Kto cell is 🟠 (waits for Karchi's yes), and the verdict line that gave such a step back to him.
# The Kto cell is the last one, so a \ud83d\udfe0 in another column (Ako to opravi\u0165) does not count.
WAITING_ROW = re.compile(r"^[ \t]*\|.*\|[ \t*_]*\U0001F7E0[^|\n]*\|?[ \t]*$", re.M)
# one line per step a verifier gave back, inside its `Na schv\u00e1lenie:` list (the verdict text is norm()ed)
APPROVAL_SECTION = re.compile(r"^[ \t*_]*na schvalenie:[ \t*_]*(?:\(.*\))?[ \t]*$", re.M)
KARCHI_REFERRAL = re.compile(r"^[ \t]*-[ \t]+karchi[ \t]+[\u2013\u2014-][ \t]", re.M)
DASH = re.compile(r"\s[\u2013\u2014-]\s(?!.*\s[\u2013\u2014-]\s)")
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
    """A verdikt.md, verdikt-<topic>.md or index.html under an overenie/ folder, non-empty and written in this turn."""
    for raw in PATH.findall(line) + SPACED_PATH.findall(line):
        if ".." in raw:
            continue
        p = os.path.expanduser(raw.rstrip(".:,;!?"))
        if not os.path.isabs(p) and isinstance(cwd, str):
            p = os.path.join(cwd, p)
        p = os.path.realpath(p)
        if not EVIDENCE_NAME.fullmatch(os.path.basename(p)) or "/overenie/" not in p or "/.claude/" in p:
            continue
        try:
            st = os.stat(p)
        except OSError:
            continue
        if os.path.isfile(p) and st.st_size > 0 and (t0 is None or st.st_mtime >= t0 - 5):
            return p
    return None


def opening(text):
    """The reply's first sentence: all of it before a Hotové / Nehotové heading, else its first 300 characters."""
    parts = OPENING_END.split(norm(text), maxsplit=1)
    return parts[0] if len(parts) > 1 else parts[0][:300]


def marked_rows(text):
    """Rows of a real Markdown table (it has a |---| line) whose Čo cell marks a finding; any cell when no Čo column."""
    count, block = 0, []
    for line in FENCE.sub("", norm(text)).splitlines() + [""]:
        if line.strip().startswith("|"):
            cells = re.sub(r"`[^`\n]*`", lambda m: m.group(0).replace("|", ""), line).replace("\\|", "").strip().strip("|").split("|")
            block.append([c.strip() for c in cells])
            continue
        if len(block) > 2 and all(set(c) <= set("-: ") and "-" in c for c in block[1]):
            names = [re.sub(r"[^a-z#]", "", c) for c in block[0]]
            col = names.index("co") if "co" in names else None
            for row in block[2:]:
                cells = row if col is None else row[col:col + 1]
                count += any(FAILED_IN_REPLY.search(c) for c in cells)
        block = []
    return count


def waiting_without_referral(text, status, t0, cwd):
    """Why the 🟠 rows of the reply may not wait for Karchi yet, or "" when there are none or a verdict gave each back."""
    rows = len(WAITING_ROW.findall(FENCE.sub("", text)))
    if not rows:
        return ""
    ev = evidence(status, t0, cwd) if status else None
    verdict = norm(open(ev, errors="replace").read(200000)) if ev else ""
    # one verifier giving a step to Karchi is enough, so count the distinct steps of all verifiers together
    # ponytail: does not match the steps to the rows; match step texts if agents start gaming the count
    # a step is the text between "- Karchi –" and its last "– <which rule>", whatever dash each verifier typed
    referrals = len({DASH.split(KARCHI_REFERRAL.sub("", line).strip())[0].strip()
                     for part in APPROVAL_SECTION.split(verdict)[1:]
                     for line in part.split("\n#")[0].splitlines() if KARCHI_REFERRAL.match(line)})
    if referrals >= rows:
        return ""
    return (f"the reply has {rows} row(s) waiting for Karchi's yes (🟠), but the verdict of this turn gave only "
            f"{referrals} step(s) back to him under `Na schválenie:`. AGENTS.md „Áno od overovateľa“: he wants the run "
            "finished before he is interrupted. Put each 🟠 step into a brief under `Na schválenie:` (one line per step) "
            "and run verify.sh; each verifier answers `áno` or `Karchi – <why>`. Do every step no verifier gives to "
            "Karchi now and verify it in the next round. Keep 🟠 only for steps a verifier gave back to him, and end "
            "with the path of that verdict.")


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
    orange = waiting_without_referral(text, status, t0, event.get("cwd"))
    problem = ""
    if status:
        ev = evidence(status, t0, event.get("cwd"))
        verdict = norm(open(ev, errors="replace").read(200000)) if ev else ""
        # each verifier section lists the same findings, so the one with the most counts, not their sum
        needed = max([max(len(FAILED_CHECK.findall(part)), len(FINDING_LINE.findall(part)))
                      for part in verdict.split("## overovatel")] or [0])
        if "overall:" not in verdict:  # the older Slovak shape: one finding per line that says it, not its summary
            needed = max([sum(1 for line in part.splitlines() if FAILED_IN_VERDICT.search(line)
                              and not line.lstrip("#*- ").startswith("vysledok"))
                          for part in verdict.split("## overovatel")] or [0])
            if FAILED_IN_VERDICT.search(verdict):
                needed = max(needed, 1)
        elif OVERALL_FAILED.search(verdict):
            needed = max(needed, 1)
        marked = marked_rows(text)
        if ev and needed and marked < needed:
            problem = (f"{ev} records {needed} finding(s) (failed or unverifiable checks, Broken and Unverified lines "
                       f"of one verifier), but the reply's table marks only {marked}. One Nehotové row per finding, "
                       "marked (neprešlo), (nedá sa overiť) or opravené, neoverené; no separate list of findings "
                       "(AGENTS.md „Koniec odpovede“).")
        elif ev and not orange:
            log("pass-evidence", event, evidence=ev)
            return None
        word = STATUS_WORD.match(norm(status))
        if problem:
            pass
        elif word and word.group(1).startswith("neoveren") and DONE_WORDS.search(opening(text)):
            problem = "it says neoverené but its opening still calls the work hotové or funguje"
        elif (word or ev) and orange:
            problem = "-"  # the line itself is fine; only the 🟠 rows are sent back
        elif word:
            log("pass-" + ("neoverene" if word.group(1).startswith("neoveren") else word.group(1)), event,
                status=status[:200])
            return None
    if event.get("stop_hook_active"):
        log("pass-after-block", event, status=status[:200], change=change)
        return None
    log("block-orange" if problem == "-" else "block", event, status=status[:200], change=change, opening=text[:200])
    if problem == "-":
        return {"decision": "block", "reason": "overenie-gate: " + orange}
    why = problem or ("its 'Overenie:' line neither names an overenie/…/verdikt.md written "
                      "in this turn nor starts with neoverené, netreba or prebieha" if status
                      else "it has no 'Overenie:' line")
    return {"decision": "block", "reason": ("overenie-gate: " + orange + "\nAlso: " if orange else "") + (
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
