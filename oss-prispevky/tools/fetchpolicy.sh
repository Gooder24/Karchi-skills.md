#!/bin/bash
# Saves a repo's contribution rules that exist (CONTRIBUTING, AI policy, AGENTS.md, PR and issue templates,
# FUNDING), falling back to the org's defaults in owner/.github like GitHub does, then lists the guides
# those files link to: read them too (COSMIC's AI ban sits in pop-os/pop, linked from its PR template).
#   fetchpolicy.sh owner/repo outdir
r=$1; d=$2; mkdir -p "$d"
files=(CONTRIBUTING.md .github/CONTRIBUTING.md docs/CONTRIBUTING.md AI.md AI_POLICY.md AI-POLICY.md .github/AI_POLICY.md
  AGENTS.md CLAUDE.md .github/pull_request_template.md .github/PULL_REQUEST_TEMPLATE.md
  PULL_REQUEST_TEMPLATE.md .github/FUNDING.yml docs/src/development.md)
get() { gh api "repos/$1/contents/$2" -H "Accept: application/vnd.github.raw" 2>/dev/null; }
save() { # repo path prefix
  local body out="$d/$3$(echo "$2" | tr / _)"
  body=$(get "$1" "$2") && printf '%s\n' "$body" > "$out" && echo "$out"
}
for f in "${files[@]}"; do save "$r" "$f" ""; done
# Template folders (several PR or issue templates): repo dir prefix
savedir() {
  gh api "repos/$1/contents/$2" --jq '.[] | select(.type == "file") | .path' 2>/dev/null |
    while read -r f; do save "$1" "$f" "$3"; done
}
for dir in .github/PULL_REQUEST_TEMPLATE .github/ISSUE_TEMPLATE; do savedir "$r" "$dir" ""; done
# Org defaults, used by GitHub for a file the repo does not have.
org=${r%%/*}/.github
for f in CONTRIBUTING.md .github/CONTRIBUTING.md AI.md AI_POLICY.md .github/PULL_REQUEST_TEMPLATE.md \
  .github/pull_request_template.md PULL_REQUEST_TEMPLATE.md; do
  save "$org" "$f" "org-"
done
for dir in .github/PULL_REQUEST_TEMPLATE .github/ISSUE_TEMPLATE PULL_REQUEST_TEMPLATE ISSUE_TEMPLATE; do
  savedir "$org" "$dir" "org-"
done
echo "-- guides linked from these files (read each):"
find "$d" -type f -exec cat {} + | grep -oE 'https?://[^ )>"]+' | grep -iE 'contribut|policy|guide|/ai[-_.]|llm|conduct|develop' |
  sort -u
