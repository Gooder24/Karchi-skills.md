"""Úplný zoznam súborov pripojeného disku (len čítanie): inventar.py <koreň> <zoznam.jsonl.gz>. Riadky {path, bytes, mtime}."""
import gzip, json, os, sys
root, out = sys.argv[1], sys.argv[2]; n = 0
with gzip.open(out, 'xt', encoding='utf-8') as f:
    for d, _, files in os.walk(root):
        for name in files:
            p = os.path.join(d, name)
            try: st = os.lstat(p); f.write(json.dumps(dict(path=os.path.relpath(p, root), bytes=st.st_size, alloc=st.st_blocks * 512, mtime=int(st.st_mtime)), ensure_ascii=False) + '\n'); n += 1
            except OSError as e: f.write(json.dumps(dict(path=os.path.relpath(p, root), error=str(e)), ensure_ascii=False) + '\n')
print(n, 'súborov ->', out)
