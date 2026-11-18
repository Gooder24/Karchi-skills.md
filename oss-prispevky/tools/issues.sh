#!/bin/bash
# issues.sh owner/repo "<search terms>" [n] : open issues sorted by reactions
n=${3:-8}
echo "### $1 :: $2"
gh api -X GET search/issues -f q="repo:$1 is:issue is:open $2" -f sort=reactions -f per_page=$n --jq '.items[] | "#\(.number) [\(.comments)c +\(.reactions["+1"]) upd \(.updated_at[:10]) created \(.created_at[:10])] \(.title[:95]) {\([.labels[].name]|join(","))[:70]}"'
