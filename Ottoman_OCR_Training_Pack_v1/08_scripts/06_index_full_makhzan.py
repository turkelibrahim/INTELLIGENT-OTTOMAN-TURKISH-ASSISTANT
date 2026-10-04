from pathlib import Path
import csv,json,re
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'04_layout/openiti_makhzan_full'
files=[p for p in (BASE/'extracted').rglob('*') if p.is_file()]
meta_files=list((BASE/'downloads').glob('*Metadata*.tsv'))
report={'files_indexed':len(files),'images':0,'xml_or_alto':0,'metadata_files':[str(p.relative_to(ROOT)) for p in meta_files],'ottoman_metadata_rows':0,'warning':'Training code should use language/script metadata and not assume every file in the full archive is Ottoman Turkish.'}
for p in files:
    if p.suffix.lower() in {'.png','.jpg','.jpeg','.tif','.tiff'}: report['images']+=1
    if p.suffix.lower()=='.xml' or 'alto' in p.name.lower(): report['xml_or_alto']+=1
for m in meta_files:
    try:
      with m.open(encoding='utf-8-sig',errors='replace',newline='') as f:
        r=csv.DictReader(f,delimiter='\t')
        for row in r:
          blob=' '.join(str(v) for v in row.values()).lower()
          if 'ottoman' in blob or 'turkish ottoman' in blob: report['ottoman_metadata_rows']+=1
    except Exception as e: report.setdefault('errors',[]).append(str(e))
(ROOT/'11_reports/FULL_MAKHZAN_INDEX.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
