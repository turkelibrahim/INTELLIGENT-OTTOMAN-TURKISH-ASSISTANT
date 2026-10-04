from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'SHA256SUMS'
rows=[]
skip={out.resolve()}
for p in sorted(ROOT.rglob('*')):
  if not p.is_file() or p.resolve() in skip or '.venv' in p.parts: continue
  h=hashlib.sha256()
  with p.open('rb') as f:
    for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
  rows.append(f'{h.hexdigest()}  {p.relative_to(ROOT).as_posix()}')
out.write_text('\n'.join(rows)+'\n',encoding='utf-8')
print('HASHED',len(rows))
