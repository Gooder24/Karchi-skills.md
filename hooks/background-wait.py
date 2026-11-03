#!/usr/bin/env python3
# PostToolUse hook for Bash and Monitor, wired in ~/.claude/settings.json on asus only.
# T3 Code keeps a thread in its sidebar's Working section only for background work the agent
# marks with t3_background_wait; agents often skip that call, so the thread shows Done while its
# tests or build still run (pingdotgg/t3code#25585). Each time a background task starts in a T3
# thread, this reminds the agent to mark it.
import json
import os
import sys

if not os.environ.get("T3CODE_THREAD_ID"):
    sys.exit(0)
try:
    event = json.load(sys.stdin)
except ValueError:
    sys.exit(0)
# Waits on a subagent's own commands are rejected or ignored; only the root agent marks them.
if event.get("agent_id"):
    sys.exit(0)
response = event.get("tool_response")
if not isinstance(response, dict):
    sys.exit(0)
key = "taskId" if event.get("tool_name") == "Monitor" else "backgroundTaskId"
task_id = response.get(key)
if not isinstance(task_id, str) or not task_id:
    sys.exit(0)

context = (
    f"Background task {task_id} is running. If you will act on its result when it ends (tests, "
    f"build, benchmark, CI, deploy, render, a command that timed out into the background), call "
    f'mcp__t3-code__t3_background_wait with taskIds ["{task_id}"] now, before ending your turn. '
    f"Without it T3 Code shows this thread as Done instead of Working. Skip it only for work you "
    f"leave running on purpose (dev server, watcher)."
)
print(
    json.dumps(
        {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}
    )
)
