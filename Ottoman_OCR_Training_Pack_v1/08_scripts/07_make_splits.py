from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
M=ROOT/'03_lines/openiti_makhzan_ottoman_lines/manifests/all.jsonl'
if not M.exists(): raise SystemExit('manifest yok')
outs={k:(ROOT/f'07_splits/{k}.jsonl').open('w',encoding='utf-8') for k in ['train','val','test']}
counts={k:0 for k in outs}
seen={k:set() for k in outs}
try:
  for line in M.read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    r=json.loads(line); up=r['upstream_split']
    if up=='test': split='test'
    else:
      # deterministic 10% val; stable id prevents random drift
      bucket=int(hashlib.sha256(r['id'].encode()).hexdigest()[:8],16)%10
      split='val' if bucket==0 else 'train'
    r['split']=split; r['eligible_for_ocr_train']=split in {'train','val'}
    outs[split].write(json.dumps(r,ensure_ascii=False)+'\n'); counts[split]+=1; seen[split].add(r['id'])
finally:
  [f.close() for f in outs.values()]
if (seen['train'] & seen['test']) or (seen['val'] & seen['test']) or (seen['train'] & seen['val']): raise SystemExit('LEAKAGE_DETECTED')
# synthetic separate
s=ROOT/'03_lines/synthetic/manifest.jsonl'; (ROOT/'07_splits/synthetic_only.jsonl').write_text(s.read_text(encoding='utf-8') if s.exists() else '',encoding='utf-8')
print('SPLITS',counts)
