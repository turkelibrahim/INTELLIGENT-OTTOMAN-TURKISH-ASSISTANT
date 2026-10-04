from pathlib import Path
import argparse, json
from huggingface_hub import snapshot_download
ROOT=Path(__file__).resolve().parents[1]
SOURCES=[
 ('OttomanNLP/OpenITI-MAKHZAN-Ottoman-Lines', ROOT/'03_lines/openiti_makhzan_ottoman_lines/raw'),
 ('OttomanNLP/ottoman-place-names-gazetteer', ROOT/'02_words/external_text/ottoman-place-names-gazetteer'),
 ('BUCOLIN/OTC-Corpus', ROOT/'02_words/external_text/OTC-Corpus'),
 ('BUCOLIN/HisTR', ROOT/'02_words/external_text/HisTR'),
 ('BUCOLIN/OTA-BOUN_UD_Treebank', ROOT/'02_words/external_text/OTA-BOUN_UD_Treebank'),
 ('enesyila/UD_Ottoman_Turkish-DUDU', ROOT/'02_words/external_text/UD_Ottoman_Turkish-DUDU'),
]
OPTIONAL=[
 ('fatihburakkaragoz/anadolu-ocr-corpus', ROOT/'05_real_sources/review_queue/anadolu-ocr-corpus_UNCLEAR_RIGHTS'),
 ('fatihburakkaragoz/evliya-celebi-seyahatname-ocr', ROOT/'05_real_sources/review_queue/evliya-celebi-seyahatname-ocr_UNCLEAR_RIGHTS'),
]
p=argparse.ArgumentParser(); p.add_argument('--include-unclear-rights',action='store_true'); a=p.parse_args()
for repo,dst in SOURCES + (OPTIONAL if a.include_unclear_rights else []):
    print(f'[HF] {repo} -> {dst}')
    dst.mkdir(parents=True,exist_ok=True)
    snapshot_download(repo_id=repo, repo_type='dataset', local_dir=dst)
print('CORE_DOWNLOAD_OK')
