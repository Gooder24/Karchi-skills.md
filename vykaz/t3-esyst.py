#!/usr/bin/env python3
"""What Karchi himself wrote in this machine's T3 between two days (UTC, a day of margin), eSYST threads marked.

Stdlib only, read-only on T3's database (only the projection tables; never auth_* or secrets), so vykaz
can run it on any machine as `ssh <box> python3 - FROM TO < t3-esyst.py`.
Usage: t3-esyst.py YYYY-MM-DD YYYY-MM-DD  ->  JSON [{"ts": ISO UTC, "projekt", "vlakno", "text", "esyst",
  "dlzka": his characters, "pripravene": when the agent's last answer before it ended, "odpoved": its characters}]
Every message comes back, so vykaz knows when he was busy elsewhere; only "esyst" ones count as work.
"""
import json, os, re, sqlite3, sys

# eSYST work: these projects, or a thread whose title or message names eSYST work.
PROJEKTY = ("SPOTREX", "Obhajoba práce", "eSYST", "Hurbanova", "partsheet", "eSYSTAK", "enex")
SLOVA = re.compile(r"esyst|spotrex|hurbanov|eucf|gondž|gondz|crs ?40|enex|esysťák|esystak|odpoč", re.I)
TITUL = re.compile(SLOVA.pattern + r"|firemn|zamestnanc", re.I)
# Agent-made "user" turns that are not his typing.
SKIP = ("<", "Stop hook", "Delegated task", "Context handoff", "[Request interrupted", "You are in a side chat")


def main(od, do):
    db = os.path.expanduser("~/.t3/userdata/statev2.sqlite")
    if not os.path.exists(db):
        sys.exit(f"{db} chýba")  # a failure, not a day without work
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=30)
    rows = con.execute(
        """select m.thread_id, m.created_at, coalesce(p.title, ''), t.title, json_extract(m.payload_json, '$.text'),
                  a.updated_at, length(json_extract(a.payload_json, '$.text'))
           from orchestration_v2_projection_messages m
           join orchestration_v2_projection_threads t on t.thread_id = m.thread_id
           left join projection_projects p on p.project_id = t.project_id
           left join orchestration_v2_projection_messages a on a.message_id = (
             select x.message_id from orchestration_v2_projection_messages x
             where x.thread_id = m.thread_id and x.role = 'assistant' and x.streaming = 0
               and x.updated_at < m.created_at
             order by x.updated_at desc limit 1)
           where m.role = 'user' and m.streaming = 0
             and coalesce(json_extract(m.payload_json, '$.createdBy'), 'user') = 'user'
             and coalesce(json_extract(t.payload_json, '$.lineage.relationshipToParent'), '') != 'subagent'
             and m.created_at >= date(?, '-1 day') and m.created_at < date(?, '+1 day')
           order by m.created_at""", (od, do)).fetchall()
    rows = [(ts, pr, vl, " ".join((tx or "").split()), hot, odp) for _, ts, pr, vl, tx, hot, odp in rows]
    rows = [r for r in rows if r[3] and not r[3].startswith(SKIP)]
    # a whole thread counts when its project or title is eSYST work, else only his messages that name it
    out = [{"ts": ts, "projekt": pr, "vlakno": vl, "text": tx[:300], "dlzka": len(tx), "pripravene": hot,
            "odpoved": odp or 0, "esyst": bool(pr.startswith(PROJEKTY) or TITUL.search(vl) or SLOVA.search(tx[:3000]))}
           for ts, pr, vl, tx, hot, odp in rows]
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:3])
