from pathlib import Path
import argparse,json,re,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('--full',action='store_true'); a=p.parse_args()
report={'status':'PASS','checks':{},'errors':[],'warnings':[]}
ids={}
for split in ['train','val','test']:
  man=ROOT/f'07_splits/{split}.jsonl'; rows=[]
  if man.exists():
    for ln in man.read_text(encoding='utf-8').splitlines():
      if ln.strip(): rows.append(json.loads(ln))
  report['checks'][f'{split}_count']=len(rows); ids[split]={r['id'] for r in rows}
  for r in rows:
    ip=ROOT/r['image']
    if not ip.exists(): report['errors'].append(f'missing_image:{r["id"]}')
    if not r.get('text','').strip(): report['errors'].append(f'empty_gt:{r["id"]}')
    if r.get('synthetic') and split=='test': report['errors'].append(f'synthetic_in_gold_test:{r["id"]}')
    if not r.get('source_id') or not r.get('license'): report['errors'].append(f'missing_provenance:{r["id"]}')
if (ids.get('train',set())&ids.get('test',set())) or (ids.get('val',set())&ids.get('test',set())) or (ids.get('train',set())&ids.get('val',set())): report['errors'].append('split_leakage')
real=sum(report['checks'].get(f'{s}_count',0) for s in ['train','val','test'])
report['checks']['real_total']=real
if real and real<3000: report['errors'].append('real_dataset_too_small')
if report['checks'].get('test_count',0) and report['checks']['test_count']<100: report['warnings'].append('unexpectedly_small_upstream_test')
# built-in synthetic checks
syn=list((ROOT/'01_alphabet/synthetic/images').glob('*.png')); report['checks']['synthetic_glyph_images']=len(syn)
if len(syn)<100: report['errors'].append('synthetic_alphabet_missing')
if a.full:
  marker=ROOT/'04_layout/openiti_makhzan_full/extracted/.EXTRACTED_OK'
  if not marker.exists(): report['errors'].append('full_archive_not_extracted')
if report['errors']: report['status']='FAIL'
out=ROOT/'11_reports/VALIDATION_REPORT.json'; out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if report['status']!='PASS': raise SystemExit(2)
