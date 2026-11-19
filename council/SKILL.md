---
name: council
description: Trigger this if the user says 'council', 'rada' or 'konzílium'.
---

# Council

Adapted from tstack (t3dotgg, MIT, see `../LICENSE-tstack`) for Karchi's machines.

Before an audit, address outstanding PR comments, fix known issues, and run
relevant checks. Give council the updated implementation; do not defer known
fixes until reviews return. If the user wants to discard the implementation
and explore new ideas, skip fixes to code being replaced.

## Members (Karchi, 2026-11-17)

Unless Karchi names other members in his request, the council is exactly these
three, one per provider:

| Member | `providerInstanceId` | `model` | `options` |
| --- | --- | --- | --- |
| Claude Opus 5.5 | `claudeAgent` | `claude-opus-5-5` | `{effort: "high"}` |
| GPT Sol 6.2 | `codex` (or `codex_infowork`) | `gpt-6.2-sol` | `{reasoningEffort: "high"}` |
| Kimi K3.1 Pro | `opencode` | `opencode-go/kimi-k3.1-pro` | `{variant: "high"}` |

Check the IDs with `orchestrator_capabilities` (`search` finds a model the
short list omits). The two Codex instances are two accounts; when one is
disabled or out of limit, use the other. Kimi runs on Karchi's OpenCode Go
subscription (account karollupi6, logged in on dell, asus and e540).

## Where each member runs

1. This machine: `delegate_task` with `target` from the table, `role: "review"`,
   all three in parallel. Members are side threads under your thread: never
   `t3_thread_launch` or `create_threads` for them (Karchi, 2026-11-18: council
   threads must not land in his sidebar).
2. A member this machine cannot run (provider disabled, model missing, Codex
   not logged in as on dell): run it as a CLI on asus over ssh, as in step 3.
   Never `delegate_task` with another machine's `target.environmentId`: T3
   makes that child a normal top-level thread in Karchi's sidebar on that
   machine (Sol rounds from dell, 18.–19. 11.).
3. No T3 tools, or step 2: run the member as a CLI on asus over ssh, the brief in the prompt and the material
   as a file. rodinnypcl cannot reach the other machines: report the members
   it cannot run there.

   ```bash
   git diff <base> > /tmp/council.diff && scp /tmp/council.diff asus:/tmp/
   ssh asus 'opencode run --archived -m "opencode-go/kimi-k3.1-pro#high" -f /tmp/council.diff "<brief>"'
   ```

   Sol the same way with `codex exec -m gpt-6.2-sol -c model_reasoning_effort=high`,
   Opus with `claude -p --model claude-opus-5-5 --effort high`.

If a member cannot run anywhere, report which and why instead of substituting
another model. One exception: when OpenCode Go reports its usage limit for
Kimi, run `opencode/deepseek-v4.1-flash-free` (variant high) in its place and
say so in the report. Both limits are shared by every home machine (one Go
account, one public IP for the free model): another machine does not help.
The Go account's DeepSeek models (`opencode-go/deepseek-*`) are hosted outside
the EU and US and fail until Karchi selects Global in the OpenCode console's
privacy settings (not selected as of 2026-11-17); when he asks for DeepSeek,
only the free model runs, and it is often out of its limit.

## Running it

Give each delegate the request and relevant context, in the language of the
material. For review or feedback, keep their work read-only. Collect their
responses and summarize, in Slovak for Karchi, the useful findings,
disagreements, and recommended next steps.

Do not wait idle. When a result arrives, check its findings against the code
at once and decide what to fix while the other delegates run. Do not edit
files while a delegate still reviews the same checkout. If the user's
instructions mark a delegate as non-blocking, do not wait for it; treat a
late result as feedback and do not record its score.

For a code review, ask each delegate for a score out of 10.
Count each full review pass as one round.
A fresh review after fixes starts a new round.

If the work ends in a pull request, put the results in the PR description.
Put this section before the model and harness line at the end:

```markdown
## Council review

Rounds: 2

| Delegate | Round 1 | Round 2 |
| --- | --- | --- |
| Claude Opus 5.5 | 7/10 | 9/10 |
| GPT Sol 6.2 | 8/10 | 10/10 |
| Kimi K3.1 Pro | 7/10 | 9/10 |
```

If a delegate gives no score, write `no score`. Do not invent one.
If the PR is open, edit the description. Do not post a comment for this.
If there is no PR (Karchi's own projects commit straight to `main`), put the
same results in the final reply only.

If you agree with their recommendations, make the changes and request a fresh
review after. Continue this process until all delegates are satisfied with the
outcome.

Do not let repeated reviews result in scope creep. It is your job to fight to
keep scope limited.
