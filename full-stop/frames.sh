#!/usr/bin/env bash
# Usage: full-stop/frames.sh <out-dir> <frame.png>...   (frames in the order the user sees them)
# Makes <out-dir>/flow.gif (1.5 s a frame, loops) and <out-dir>/frames.html, a page that steps through the same
# frames with ←/→, buttons and a slider, each with its file name as caption (name frames like 01-filtre-x.png).
# Needs ffmpeg (asus has it, dell does not). Frames made on another machine than the thread's: run it there, copy
# <out-dir> to the thread's machine and run `frames.sh --html <out-dir>` on it: frames.html names its frames by
# absolute path, which T3 inlines. The last line it prints is the height for html_render.
set -euo pipefail
html_only=; [ "${1:-}" = --html ] && { html_only=1; shift; }
out=${1:-}; [ -n "$out" ] || { echo "usage: frames.sh [--html] <out-dir> <frame.png>..." >&2; exit 2; }; shift
mkdir -p "$out"; out=$(cd "$out" && pwd)
if [ -n "$html_only" ]; then set -- "$out"/[0-9][0-9]-*.png; fi
[ -e "${1:-}" ] || { echo "frames.sh: no frames" >&2; exit 2; }
[ -n "$html_only" ] || command -v ffmpeg >/dev/null || { echo "frames.sh: ffmpeg missing here (run on asus)" >&2; exit 2; }
work=$(mktemp -d); list=$work/list; trap 'rm -rf "$work"' EXIT
esc() { sed 's/&/\&amp;/g; s/</\&lt;/g; s/"/\&quot;/g' <<<"$1"; }
url() { esc "$(sed 's/%/%25/g; s/#/%23/g; s/?/%3F/g' <<<"$1")"; }
# Frames of another size (a phone width) are fitted into the first frame's size for the GIF: a size change inside
# ffmpeg's concat restarts the palette and drops the frames before it.
[ -n "$html_only" ] || size=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$1")
n=0; names=()
for f in "$@"; do
  n=$((n + 1))
  if [ -n "$html_only" ]; then dest=$f; else dest=$(printf '%s/%02d-%s' "$out" "$n" "$(basename "$f" | sed 's/^[0-9]*-//')"); [ "$f" -ef "$dest" ] || cp "$f" "$dest"; fi
  names+=("$dest")
  if [ -z "$html_only" ]; then
    fit=$(printf '%s/%02d.png' "$work" "$n"); w=${size%x*} h=${size#*x}
    ffmpeg -loglevel error -y -i "$dest" -vf "scale=$w:$h:force_original_aspect_ratio=decrease,pad=$w:$h:(ow-iw)/2:(oh-ih)/2" "$fit"
    printf "file '%s'\nduration 1.5\n" "$fit" >> "$list"
  fi
done
[ -n "$html_only" ] || printf "file '%s'\n" "$fit" >> "$list"   # the concat demuxer drops the last duration without this
[ -n "$html_only" ] || ffmpeg -loglevel error -y -f concat -safe 0 -i "$list" \
  -vf "scale='min(960,iw)':-2:flags=lanczos,split[a][b];[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=bayer" \
  -loop 0 "$out/flow.gif"
{
  printf '<!doctype html>\n'
  printf '<div class="fs"><div class="bar"><button id="p">←</button><input id="r" type="range" min="0" max="%d" value="0"><button id="n">→</button><span id="c"></span></div>\n' $((n - 1))
  for i in "${!names[@]}"; do printf '<figure%s><img src="%s"><figcaption>%s</figcaption></figure>\n' "$([ "$i" = 0 ] || echo ' hidden')" "$(url "${names[$i]}")" "$(esc "$(basename "${names[$i]}" .png)")"; done
  cat <<'HTML'
</div>
<style>
.fs img { max-width: 100%; max-height: 900px; height: auto; display: block; margin: 0 auto; border-radius: var(--radius); }
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
# The height html_render needs: the tallest frame at T3's 728 px (at most 900 px each) plus the bar and caption.
tall=0
for f in "${names[@]}"; do
  read -r w h < <(file -b "$f" | grep -oE '[0-9]+ x [0-9]+' | tr -d x)
  t=$(( (w > 728 ? 728 * h / w : h) )); [ "$t" -le 900 ] || t=900; [ "$t" -le "$tall" ] || tall=$t
done
[ -n "$html_only" ] || echo "$out/flow.gif"
echo "$out/frames.html"
echo "html_render height: $((tall + 70))"
