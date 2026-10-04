from pathlib import Path
import json, shutil
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'06_annotations/kraken'
for split in ['train','val','test']:
  out=DEST/split; out.mkdir(parents=True,exist_ok=True)
  man=ROOT/f'07_splits/{split}.jsonl'
  if not man.exists(): continue
  for line in man.read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    r=json.loads(line); src=ROOT/r['image']; base=out/r['id']
    dst=base.with_suffix('.png'); gt=out/(r['id']+'.gt.txt')
    if not dst.exists(): shutil.copy2(src,dst)
    gt.write_text(r['text'].strip()+'\n',encoding='utf-8')
print('KRAKEN_EXPORT_OK')
