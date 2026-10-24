---
name: github
description: How to write on GitHub for Karchi - commit messages, branches, pull requests, issues and comments. Use before any git commit or push, any gh pr or gh issue command, and before writing a PR description or a reply to a review.
---

# Writing on GitHub

## Where changes go

- Karchi's personal projects (karchi-os, karchi-skills) are committed straight to `main` and pushed.
  No branches or pull requests.
- Work projects do not have an agreed workflow yet. Ask before creating a branch or a PR.
- Never open a pull request unless Karchi explicitly asks. One request is one PR.

## Commits and pull requests

- Conventional commit titles in plain language: `fix(web): new threads no longer spike CPU`.
- PR body: the problem in a sentence or two, then how you fixed it. End with the model and harness
  that did the work.
- UI changes need before/after images; motion or timing needs a short video. Upload them to GitHub
  (PR body or comment); never commit screenshots or assets that only the PR needs.
- Never commit secrets or tokens.

## Babysitting a PR

- Look only at checks and comments newer than the last push. Verify each bot finding against the
  source, fix the real ones, dismiss false positives with a written reason.
- Stay quiet when nothing is new. Stop when the bots are green on the latest commit.
