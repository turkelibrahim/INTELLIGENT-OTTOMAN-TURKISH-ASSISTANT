from pathlib import Path
import argparse, requests, zipfile, shutil
from tqdm import tqdm
ROOT=Path(__file__).resolve().parents[1]

def dl(url,dst,expected=None):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists() and dst.stat().st_size>1024:
        print('[skip]',dst.name); return dst
    with requests.get(url,stream=True,timeout=(30,120)) as r:
        r.raise_for_status(); total=int(r.headers.get('content-length',0))
        with dst.open('wb') as f, tqdm(total=total,unit='B',unit_scale=True,desc=dst.name) as bar:
            for c in r.iter_content(1024*1024):
                if c: f.write(c); bar.update(len(c))
    return dst

def zenodo(record_id,outdir,select=None):
    meta=requests.get(f'https://zenodo.org/api/records/{record_id}',timeout=60).json()
    got=[]
    for item in meta.get('files',[]):
        name=item.get('key') or item.get('filename')
        if select and not any(s in name for s in select): continue
        url=(item.get('links') or {}).get('content') or (item.get('links') or {}).get('self')
        if url: got.append(dl(url,outdir/name))
    return got
p=argparse.ArgumentParser(); p.add_argument('--extract',action='store_true'); a=p.parse_args()
base=ROOT/'04_layout/openiti_makhzan_full/downloads'
files=zenodo('19861912',base)
latoc=zenodo('19445113',ROOT/'10_sources/latoc_support')
if a.extract:
    zips=[p for p in files if p.suffix.lower()=='.zip']
    for z in zips:
        dst=ROOT/'04_layout/openiti_makhzan_full/extracted'
        marker=dst/'.EXTRACTED_OK'
        if marker.exists(): print('[skip extracted]',z.name); continue
        print('Extracting large archive; disk alanini kontrol edin:',z)
        dst.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(z) as zz: zz.extractall(dst)
        marker.write_text(z.name,encoding='utf-8')
print('FULL_DOWNLOAD_OK')
