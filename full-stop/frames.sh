#!/usr/bin/env bash
# Usage: full-stop/frames.sh <out-dir> <frame.png>...   (frames in the order the user sees them, all one size)
# Makes <out-dir>/flow.gif (1.5 s a frame, loops) and <out-dir>/frames.html, a page that steps through the same
# frames with ←/→, buttons and a slider, each with its file name as caption (name frames like 01-filtre-x.png).
# Needs ffmpeg (asus has it, dell does not). Frames made on another machine than the thread's: run it there, copy
# <out-dir> to the thread's machine and run `frames.sh --html <out-dir>` on it: frames.html names its frames by
# absolute path, which T3 inlines.
set -euo pipefail
html_only=; [ "${1:-}" = --html ] && { html_only=1; shift; }
out=$1; shift
mkdir -p "$out"; out=$(cd "$out" && pwd)
if [ -n "$html_only" ]; then set -- "$out"/[0-9][0-9]-*.png; fi
[ -e "$1" ] || { echo "frames.sh: no frames" >&2; exit 2; }
[ -n "$html_only" ] || command -v ffmpeg >/dev/null || { echo "frames.sh: ffmpeg missing here (run on asus)" >&2; exit 2; }
list=$(mktemp); trap 'rm -f "$list"' EXIT
n=0; names=()
for f in "$@"; do
  n=$((n + 1))
  if [ -n "$html_only" ]; then dest=$f; else dest=$(printf '%s/%02d-%s' "$out" "$n" "$(basename "$f" | sed 's/^[0-9]*-//')"); cp "$f" "$dest"; fi
  names+=("$dest"); printf "file '%s'\nduration 1.5\n" "$dest" >> "$list"
done
printf "file '%s'\n" "${names[-1]}" >> "$list"   # the concat demuxer drops the last duration without this
[ -n "$html_only" ] || ffmpeg -loglevel error -y -f concat -safe 0 -i "$list" \
  -vf "scale='min(960,iw)':-2:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer" \
  -loop 0 "$out/flow.gif"
{
  printf '<!doctype html>\n'
  printf '<div class="fs"><div class="bar"><button id="p">←</button><input id="r" type="range" min="0" max="%d" value="0"><button id="n">→</button><span id="c"></span></div>\n' $((n - 1))
  for i in "${!names[@]}"; do printf '<figure%s><img src="%s"><figcaption>%s</figcaption></figure>\n' "$([ "$i" = 0 ] || echo ' hidden')" "${names[$i]}" "$(basename "${names[$i]}" .png)"; done
  cat <<'HTML'
</div>
<style>
.fs img { width: 100%; height: auto; display: block; border-radius: var(--radius); }
.fs .bar { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; font-family: var(--font-mono); }
.fs .bar input { flex: 1; }
.fs figure { margin: 0; } .fs figcaption { margin-top: 6px; color: var(--muted-foreground); font-family: var(--font-mono); }
</style>
<script>
const figs = [...document.querySelectorAll('.fs figure')], r = document.getElementById('r'), c = document.getElementById('c');
let i = 0;
const show = (k) => { i = Math.max(0, Math.min(figs.length - 1, k)); figs.forEach((f, j) => (f.hidden = j !== i)); r.value = i; c.textContent = `${i + 1} / ${figs.length}`; };
document.getElementById('p').onclick = () => show(i - 1);
document.getElementById('n').onclick = () => show(i + 1);
r.oninput = () => show(Number(r.value));
addEventListener('keydown', (e) => { if (e.key === 'ArrowLeft') show(i - 1); if (e.key === 'ArrowRight') show(i + 1); });
show(0);
</script>
HTML
} > "$out/frames.html"
[ -n "$html_only" ] || echo "$out/flow.gif"
echo "$out/frames.html"
