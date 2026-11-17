"""Prehľad disku pre Karchiho: priečinky (2 úrovne), počty, veľkosti a typy súborov z úplného zoznamu.
Použitie: prehlad.py <zoznam.jsonl.gz> <výstup.md> <nadpis>   (zoznam: riadky {path, bytes})"""
import gzip, json, sys, collections
from pathlib import Path
src, out, title = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
KIND = {'Fotky': 'jpg jpeg png gif bmp heic nef cr2 tif tiff', 'Videá': 'mp4 mov avi mts m2ts 3gp wmv mpg mpeg mkv vob',
        'Hudba/zvuk': 'mp3 wav wma m4a flac ogg amr', 'Dokumenty': 'doc docx pdf xls xlsx ppt pptx pps txt odt rtf',
        'Archívy': 'zip rar 7z dbk iso'}
EXT = {e: k for k, v in KIND.items() for e in v.split()}
def kind(p): return EXT.get(p.rsplit('.', 1)[-1].lower() if '.' in p.rsplit('/', 1)[-1] else '', 'Iné')
def gb(b): return f'{b/1e9:.1f} GB' if b >= 1e8 else f'{b/1e6:.0f} MB'
rows = [json.loads(l) for l in (gzip.open(src, 'rt') if src.endswith('.gz') else open(src))]
rows = [dict(r, bytes=min(r['bytes'], r.get('alloc', r['bytes']))) for r in rows if 'bytes' in r and r.get('type', 'file') == 'file']  # riedke obrazy: skutočne zabrané miesto
agg = collections.defaultdict(lambda: [0, 0, collections.Counter()])
for r in rows:
    parts = r['path'].split('/')
    for key in {parts[0] if len(parts) > 1 else '(koreň)', '/'.join(parts[:2]) if len(parts) > 2 else None} - {None}:
        a = agg[key]; a[0] += 1; a[1] += r['bytes']; a[2][kind(r['path'])] += 1
tot = [len(rows), sum(r['bytes'] for r in rows), collections.Counter(kind(r['path']) for r in rows)]
def kinds(c): return ', '.join(f'{k} {v}' for k, v in c.most_common() if v)
L = [f'# {title}', '', f'Spolu: {tot[0]} súborov, {gb(tot[1])}. {kinds(tot[2])}.', '', '| Priečinok | Súbory | Veľkosť | Čo tam je |', '|---|---|---|---|']
tops = sorted((k for k in agg if '/' not in k), key=lambda k: -agg[k][1])
for t in tops:
    a = agg[t]; L.append(f'| **{t}** | {a[0]} | {gb(a[1])} | {kinds(a[2])} |')
    subs = [] if t.startswith(('$', 'System Volume')) else sorted((k for k in agg if k.startswith(t + '/')), key=lambda k: -agg[k][1])
    for s in subs[:12]:
        a = agg[s]; L.append(f'| &nbsp;&nbsp;{s.split("/", 1)[1]} | {a[0]} | {gb(a[1])} | {kinds(a[2])} |')
    if len(subs) > 12: L.append(f'| &nbsp;&nbsp;… a ďalších {len(subs)-12} podpriečinkov | | | |')
out.write_text('\n'.join(L) + '\n', encoding='utf-8'); print(out)
