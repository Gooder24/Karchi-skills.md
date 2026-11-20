#!/usr/bin/env bash
# The CLI lookup of t3-links on this machine against fake T3 homes: usage test-cli.sh <t3-links>.
# Downloads one real release CLI (about 190 MB) from GitHub.
set -u
cli=$(python3 -c "import importlib.machinery as m,sys;print(m.SourceFileLoader('t',sys.argv[1]).load_module().CLI)" "$1")
fails=0
check() { if eval "$2"; then echo "ok   $1"; else echo "FAIL $1"; fails=1; fi; }
home() { local h; h=$(mktemp -d); mkdir -p "$h/.t3/userdata"; printf '{"serverVersion": "%s"}' "$1" > "$h/.t3/userdata/server-runtime.json"; echo "$h"; }
V=0.1.11-nightly.20261119.4928
h=$(home "$V"); mkdir -p "$h/.local/share/t3-links/cli/0.1.0-old"
out=$(HOME=$h bash -c "$cli" 2>&1); rc=$?
check "missing CLI is downloaded, checked and kept" '[ $rc = 0 ] && [ "$out" = "$h/.local/share/t3-links/cli/$V/t3" ] && "$out" --version | grep -qxF "t3 v$V"'
check "older downloaded versions are removed, no temp dir left" '[ "$(ls -A "$h/.local/share/t3-links/cli")" = "$V" ]'
out2=$(HOME=$h bash -c "$cli" 2>&1)
check "second run reuses it" '[ "$out2" = "$out" ]'
h2=$(home "$V"); mkdir -p "$h2/.t3/bin"; printf '#!/bin/sh\necho "t3 v0.1.11-nightly.20261119.4954"\n' > "$h2/.t3/bin/t3"; chmod +x "$h2/.t3/bin/t3"
mkdir -p "$h2/.local/share/t3-links/cli"; cp -r "$h/.local/share/t3-links/cli/$V" "$h2/.local/share/t3-links/cli/"
out=$(HOME=$h2 bash -c "$cli" 2>&1)
check "newer ~/.t3/bin/t3 (the x270 case) is not used" '[ "$out" = "$h2/.local/share/t3-links/cli/$V/t3" ]'
h5=$(home "$V"); mkdir -p "$h5/.t3/bin" "$h5/.local/share/t3-links/cli/0.1.0-old"
printf '#!/bin/sh\necho "t3 v%s"\n' "$V" > "$h5/.t3/bin/t3"; chmod +x "$h5/.t3/bin/t3"
out=$(HOME=$h5 bash -c "$cli" 2>&1)
check "app restarted on the installed version: its CLI is used, the old download is removed" '[ "$out" = "$h5/.t3/bin/t3" ] && [ -z "$(ls -A "$h5/.local/share/t3-links/cli")" ]'
rm -rf "$h5"
h3=$(home '1.0; touch /tmp/pwned-t3links'); out=$(HOME=$h3 bash -c "$cli" 2>&1); rc=$?
check "odd version string refused" '[ $rc != 0 ] && [ ! -e /tmp/pwned-t3links ] && grep -q "unexpected server version" <<<"$out"'
h4=$(home 0.0.0-nightly.19990101.1); out=$(HOME=$h4 bash -c "$cli" 2>&1); rc=$?
check "version without a release fails, leaves nothing behind" '[ $rc != 0 ] && [ -z "$(ls -A "$h4/.local/share/t3-links/cli")" ]'
rm -rf "$h" "$h2" "$h3" "$h4"
exit $fails
