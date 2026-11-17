# Contributing

This repository holds personal skills for Claude Code and Codex. Each folder is one skill, and the README explains how they are installed.

## Before you start

- Read [ACCESSIBILITY.md](ACCESSIBILITY.md). It lists the checks, the expectations for Markdown, and how to report a barrier.
- For a larger change, open an issue first, so the owner can say whether it fits.
- `AGENTS.md` is linked into the owner's machines, and the existing skills are in use. The owner reviews changes to them before they are merged.

## Making a change

1. Keep a pull request to one change, and keep it small.
2. Run the checks from the repository root:

   ```sh
   node --test avoid-ai-design/scripts/detect.test.mjs
   python3 anna-pdf/test_watch.py
   python3 .github/scripts/check-docs.py
   ```

3. Open a pull request and complete the checklist in the template.

## Good first issues

Issues labelled `good first issue` have a small scope and a clear done-when. If something in one is unclear, ask in the issue before you start.
