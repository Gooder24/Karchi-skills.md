#!/usr/bin/env python3
"""Accessibility check for Markdown documentation (Open Source Accessibility Framework, Testing 1 and 5).

Usage: python3 .github/scripts/check-docs.py [--update-baseline]   (run in the repository root)

Checks every *.md file git knows or would add (tracked, or new and not ignored) for:
  heading-skip    a heading that skips a level (## followed by ####)
  heading-empty   a heading without text
  img-alt         an image without alt text (![](x) or <img> without alt)
  link-text       a link whose text says nothing on its own ("here", "click here", "link", "tu", "sem", ...)

Known problems live in .github/a11y-baseline.json and do not fail the check; anything new does.
--update-baseline rewrites that file from the current state. Exits 1 on a new problem.
Needs only Python 3.8+ and git.
"""
import json, re, subprocess, sys
from pathlib import Path

BASELINE = Path(".github/a11y-baseline.json")
VAGUE = {"here", "click here", "link", "this link", "read more", "more", "this", "click",
         "tu", "sem", "tu.", "kliknite sem", "klikni sem", "viac", "odkaz", "tento odkaz"}
HEADING = re.compile(r"^(#{1,6})(?:\s+(.*?))?\s*#*\s*$")
IMG_MD = re.compile(r"!\[([^\]]*)\]\(")
IMG_HTML = re.compile(r"<img\b[^>]*>", re.I)
LINK_MD = re.compile(r"(?<!!)\[([^\]]+)\]\([^)]+\)")
LINK_HTML = re.compile(r"<a\b[^>]*>(.*?)</a>", re.I)


def markdown_files():
    out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "*.md"], capture_output=True, text=True, check=True).stdout
    return sorted(p for p in out.split("\0") if p and Path(p).is_file())


def problems(path):
    level = 0
    fence = None
    for n, line in enumerate(Path(path).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        stripped = line.strip()
        m = re.match(r"^(```+|~~~+)", stripped)
        if m:
            fence = None if fence and stripped.startswith(fence) else (fence or m.group(1))
            continue
        if fence:
            continue
        text = re.sub(r"`[^`]*`", "", line)
        h = HEADING.match(line)
        if h and not line.startswith("#!"):
            new = len(h.group(1))
            if not (h.group(2) or "").strip():
                yield n, "heading-empty", stripped
            if level and new > level + 1:
                yield n, "heading-skip", stripped
            level = new
        for alt in IMG_MD.findall(text):
            if not alt.strip():
                yield n, "img-alt", stripped
        for tag in IMG_HTML.findall(text):
            if not re.search(r"\balt\s*=", tag, re.I):
                yield n, "img-alt", stripped
        for label in LINK_MD.findall(text) + LINK_HTML.findall(text):
            plain = re.sub(r"<[^>]+>|[*_`]", "", label).strip().lower()
            if plain in VAGUE:
                yield n, "link-text", stripped


def key(path, rule, snippet):
    return f"{path} | {rule} | {snippet}"


def main():
    found = [(p, n, rule, snip) for p in markdown_files() for n, rule, snip in problems(p)]
    keys = sorted({key(p, r, s) for p, _, r, s in found})
    if "--update-baseline" in sys.argv:
        BASELINE.parent.mkdir(exist_ok=True)
        BASELINE.write_text(json.dumps(keys, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"baseline: {len(keys)} known problem(s) written to {BASELINE}")
        return 0
    known = set(json.loads(BASELINE.read_text(encoding="utf-8"))) if BASELINE.exists() else set()
    new = [(p, n, r, s) for p, n, r, s in found if key(p, r, s) not in known]
    for p, n, r, s in new:
        print(f"{p}:{n}: {r}: {s}")
    fixed = known - set(keys)
    print(f"{len(markdown_files())} file(s), {len(found)} problem(s), {len(found) - len(new)} in baseline, "
          f"{len(new)} new" + (f", {len(fixed)} baseline entr(y/ies) no longer present: run --update-baseline" if fixed else ""))
    return 1 if new else 0


if __name__ == "__main__":
    sys.exit(main())
