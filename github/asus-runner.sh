#!/usr/bin/env bash
# A GitHub Actions runner on asus for one of Karchi's repos, under the user github-runner.
#   asus-runner.sh <repo>            add it; jobs with `runs-on: asus` in that repo then run on asus
#   asus-runner.sh --remove <repo>   take it away again
# See them: systemctl list-units 'actions.runner.*' on asus, or the repo's Settings > Actions > Runners.
# A job from a fork's pull request never runs here: reject-forks.sh fails it before its first step.
set -euo pipefail

if [ "$(uname -n)" != asus-vivobook-x1504v ]; then
  exec ssh asus bash -s -- "$(printf '%q ' "$@")" <"$0"
fi

remove=
[ "${1:-}" = --remove ] && { remove=1; shift; }
repo=${1:?usage: asus-runner.sh [--remove] <repo>}
home=/var/lib/github-runner
dir=$home/$(tr 'A-Z.' 'a-z-' <<<"$repo")
name=asus-$(basename "$dir")
# $home is private to github-runner, so everything inside it runs through sudo.
as_runner() { sudo -u github-runner -H bash -c 'cd "$0" && "$@"' "$dir" "$@"; }
as_root() { sudo bash -c 'cd "$0" && "$@"' "$dir" "$@"; }

if [ -n "$remove" ]; then
  token=$(gh api -X POST "repos/Gooder24/$repo/actions/runners/remove-token" -q .token)
  as_root ./svc.sh stop
  as_root ./svc.sh uninstall
  as_runner ./config.sh remove --token "$token"
  sudo rm -rf "$dir"
  echo "removed $name from Gooder24/$repo"
  exit
fi

sudo tee "$home/reject-forks.sh" >/dev/null <<'EOF'
#!/bin/sh
# Job-started hook of every runner on asus: a pull request from a fork is someone else's code,
# so it fails here (the workflows send such jobs to GitHub's own machines).
exec python3 - "$GITHUB_EVENT_PATH" <<'PY'
import json, sys
event = json.load(open(sys.argv[1]))
pr = event.get("pull_request")
if pr and ((pr.get("head") or {}).get("repo") or {}).get("full_name") != event["repository"]["full_name"]:
    sys.exit("A pull request from a fork does not run on asus; route it to a GitHub-hosted runner.")
PY
EOF
sudo chmod 755 "$home/reject-forks.sh"

if ! sudo test -x "$dir/run.sh"; then
  url=$(gh api repos/actions/runner/releases/latest \
    -q '.assets[] | select(.name | test("actions-runner-linux-x64-.*\\.tar\\.gz$")) | .browser_download_url')
  sudo install -d -o github-runner -g github-runner "$dir"
  curl -fsSL "$url" | as_runner tar -xz
fi

if ! as_runner test -f .runner; then
  token=$(gh api -X POST "repos/Gooder24/$repo/actions/runners/registration-token" -q .token)
  as_runner ./config.sh --unattended --replace --url "https://github.com/Gooder24/$repo" \
    --token "$token" --name "$name" --labels asus
fi
printf 'LANG=C.UTF-8\nACTIONS_RUNNER_HOOK_JOB_STARTED=%s\n' "$home/reject-forks.sh" | as_runner tee .env >/dev/null
as_runner test -f .service || as_root ./svc.sh install github-runner >/dev/null
as_root ./svc.sh stop >/dev/null; as_root ./svc.sh start >/dev/null
echo "$name runs jobs of Gooder24/$repo (runs-on: asus)"
