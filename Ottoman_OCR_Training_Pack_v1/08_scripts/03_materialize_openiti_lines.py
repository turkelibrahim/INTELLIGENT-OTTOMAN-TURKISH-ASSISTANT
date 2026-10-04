from pathlib import Path
from io import BytesIO
import json, hashlib
import pyarrow.parquet as pq
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'03_lines/openiti_makhzan_ottoman_lines/raw'
IMG=ROOT/'03_lines/openiti_makhzan_ottoman_lines/images'
GT=ROOT/'03_lines/openiti_makhzan_ottoman_lines/gt'
MAN=ROOT/'03_lines/openiti_makhzan_ottoman_lines/manifests/all.jsonl'
parquets=list(RAW.rglob('*.parquet'))
if not parquets: raise SystemExit('ERROR: parquet bulunamadi; once 01_download_core.py calistirin.')
for p in (IMG,GT,MAN.parent): p.mkdir(parents=True,exist_ok=True)
count=0
with MAN.open('w',encoding='utf-8') as mf:
    for pf in sorted(parquets):
        n=pf.name.lower()
        split='test' if 'test' in n else ('train' if 'train' in n else 'train')
        q=pq.ParquetFile(pf)
        for batch in q.iter_batches(batch_size=64):
            for row in batch.to_pylist():
                text=row.get('text') or row.get('transcription') or row.get('label')
                image=row.get('image')
                if not text or image is None: continue
                if isinstance(image,dict):
                    b=image.get('bytes'); path=image.get('path')
                    if b is not None: im=Image.open(BytesIO(b)).convert('RGB')
                    elif path:
                        pp=Path(path); pp=pp if pp.is_absolute() else pf.parent/pp
                        im=Image.open(pp).convert('RGB')
                    else: continue
                elif isinstance(image,(bytes,bytearray)): im=Image.open(BytesIO(image)).convert('RGB')
                else: continue
                uid=hashlib.sha256((str(pf.relative_to(RAW))+'|'+str(count)+'|'+text).encode('utf-8')).hexdigest()[:20]
                idir=IMG/split; gdir=GT/split; idir.mkdir(parents=True,exist_ok=True); gdir.mkdir(parents=True,exist_ok=True)
                ip=idir/f'{uid}.png'; gp=gdir/f'{uid}.gt.txt'
                im.save(ip,optimize=True); gp.write_text(text.strip()+'\n',encoding='utf-8')
                rec={'id':uid,'image':str(ip.relative_to(ROOT)).replace('\\','/'),'gt':str(gp.relative_to(ROOT)).replace('\\','/'),'text':text.strip(),'upstream_split':split,'source_id':'openiti_ottoman_lines','license':'CC BY-NC-SA','synthetic':False,'human_verified':True,'eligible_for_ocr_train':split=='train','eligible_for_gold_eval':True}
                mf.write(json.dumps(rec,ensure_ascii=False)+'\n'); count+=1
print('MATERIALIZED',count)
if count < 3000: raise SystemExit(f'ERROR: beklenenden az line materyalize edildi: {count}')
