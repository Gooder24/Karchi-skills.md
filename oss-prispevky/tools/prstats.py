#!/usr/bin/env python3
"""How maintainers treat outside PRs, measured on GitHub (needs `gh` logged in).

  prstats.py owner/repo [FROM] [TO] [--new]     one JSON line

PRs created FROM..TO (default 2026-08-01..2026-11-04; end the window two weeks before today so
fresh PRs do not count as ignored). Outside = author association CONTRIBUTOR, FIRST_TIME_CONTRIBUTOR,
FIRST_TIMER or NONE, bots dropped. --new keeps only authors with at most two PRs in the window, which
drops staff whose org membership is private. Reports merged / closed unmerged / still open, the median
hours to the first human comment or review from someone else, and the median hours to merge.
"""
import json, subprocess, sys, statistics
from datetime import datetime

repo = sys.argv[1]
start = sys.argv[2] if len(sys.argv) > 2 else "2026-08-01"
end = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("-") else "2026-11-04"
EXT = {"CONTRIBUTOR", "FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER", "NONE"}
Q = """query($q:String!,$c:String){search(query:$q,type:ISSUE,first:50,after:$c){pageInfo{hasNextPage endCursor}
nodes{... on PullRequest{number title url state createdAt mergedAt closedAt authorAssociation author{login}
comments(first:15){nodes{createdAt author{login} authorAssociation}}
reviews(first:15){nodes{createdAt author{login} authorAssociation}}}}}}"""

def ts(s): return datetime.fromisoformat(s.replace("Z", "+00:00"))
def bot(l): return (not l) or l.endswith("[bot]") or l.endswith("-bot") or l in {"coderabbitai","github-actions","dependabot","renovate","codecov","netlify","vercel","cla-bot","CLAassistant","zed-industries-bot","cla-checker-service","sourcery-ai","gemini-code-assist","copilot-pull-request-reviewer","claude","mergify","bors","bors-servo","servo-wpt-sync","graphite-app","cursor","greptile-apps","ellipsis-dev"}

prs, cur = [], None
for _ in range(3):
    args = ["gh","api","graphql","-f",f"query={Q}","-f",f"q=repo:{repo} is:pr created:{start}..{end} sort:created-desc"]
    if cur: args += ["-f", f"c={cur}"]
    r = json.loads(subprocess.run(args, capture_output=True, text=True, check=True).stdout)["data"]["search"]
    prs += [n for n in r["nodes"] if n]
    if not r["pageInfo"]["hasNextPage"] or len(prs) >= 120: break
    cur = r["pageInfo"]["endCursor"]

ext = [p for p in prs if p["authorAssociation"] in EXT and not bot((p["author"] or {}).get("login"))]
from collections import Counter
cnt = Counter((p["author"] or {}).get("login") for p in ext)
if "--new" in sys.argv: ext = [p for p in ext if cnt[(p["author"] or {}).get("login")] <= 2]
resp, merge_h, merged, closed, openn, noresp = [], [], 0, 0, 0, 0
for p in ext:
    a = (p["author"] or {}).get("login")
    evs = [x for x in p["comments"]["nodes"] + p["reviews"]["nodes"]
           if x["author"] and x["author"]["login"] != a and not bot(x["author"]["login"])]
    if evs:
        resp.append((min(ts(x["createdAt"]) for x in evs) - ts(p["createdAt"])).total_seconds() / 3600)
    else:
        noresp += 1
    if p["mergedAt"]:
        merged += 1; merge_h.append((ts(p["mergedAt"]) - ts(p["createdAt"])).total_seconds() / 3600)
    elif p["state"] == "CLOSED": closed += 1
    else: openn += 1
med = lambda v: round(statistics.median(v), 1) if v else None
print(json.dumps({"repo": repo, "newcomers_only": "--new" in sys.argv, "window": f"{start}..{end}", "prs_total": len(prs), "external": len(ext),
    "ext_merged": merged, "ext_closed_unmerged": closed, "ext_still_open": openn,
    "merge_rate": round(merged / len(ext), 2) if ext else None,
    "first_human_response_median_h": med(resp), "no_human_response": noresp,
    "time_to_merge_median_h": med(merge_h)}))
