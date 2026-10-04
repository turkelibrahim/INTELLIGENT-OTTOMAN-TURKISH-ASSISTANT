from pathlib import Path
from collections import Counter
import json,re,csv
ROOT=Path(__file__).resolve().parents[1]
M=ROOT/'03_lines/openiti_makhzan_ottoman_lines/manifests/all.jsonl'
OUT=ROOT/'02_words/generated/word_lexicon.tsv'
pat=re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
c=Counter()
if M.exists():
  for line in M.read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    t=json.loads(line)['text']
    for tok in pat.findall(t):
      if any(ch.isalpha() for ch in tok): c[tok]+=1
OUT.parent.mkdir(parents=True,exist_ok=True)
with OUT.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f,delimiter='\t'); w.writerow(['word','frequency','source']);
  for word,n in c.most_common(): w.writerow([word,n,'openiti_ottoman_lines'])
print('LEXICON_WORD_TYPES',len(c))
