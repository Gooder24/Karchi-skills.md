#!/bin/bash
# Saves a repo's contribution rules that exist (CONTRIBUTING, AI policy, AGENTS.md, PR template, FUNDING):
#   fetchpolicy.sh owner/repo outdir : saves contribution/AI policy files that exist
r=$1; d=$2; mkdir -p "$d"
for f in CONTRIBUTING.md .github/CONTRIBUTING.md docs/CONTRIBUTING.md AI_POLICY.md AI-POLICY.md .github/AI_POLICY.md AGENTS.md CLAUDE.md .github/pull_request_template.md .github/PULL_REQUEST_TEMPLATE.md .github/FUNDING.yml docs/src/development.md; do
  out="$d/$(echo "$f" | tr / _)"
  if body=$(gh api "repos/$r/contents/$f" -H "Accept: application/vnd.github.raw" 2>/dev/null); then printf '%s\n' "$body" > "$out"; fi
done
