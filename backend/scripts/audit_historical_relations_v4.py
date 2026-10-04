from __future__ import annotations

import argparse
import csv
import json
import random
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
DATA_ROOT = PROJECT_ROOT / 'datasets' / 'historical_knowledge'
INPUT_PATH = DATA_ROOT / '02_structured' / 'overnight' / 'derived_relation_candidates_v3.jsonl'
CORPUS_PATH = DATA_ROOT / '02_structured' / 'overnight' / 'ingested_chunks.jsonl'
OUT_DIR = DATA_ROOT / '05_evaluation' / 'relation_quality_v4'


def canonical(value: str) -> str:
    value = str(value or '')
    value = value.replace('\u200b', '').replace('\ufeff', '')
    value = value.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    value = value.replace('–', '-').replace('—', '-').replace('‑', '-')
    value = unicodedata.normalize('NFKC', value)
    value = re.sub(r'\s+', ' ', value).strip().casefold()
    return value


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open('r', encoding='utf-8-sig') as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                print(f'WARN invalid JSONL line {line_no}: {path}')
    return rows


def build_corpus_index(rows: List[Dict[str, Any]]) -> Tuple[Dict[Tuple[str, str], List[str]], int, int]:
    idx: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    raw_counts: Dict[Tuple[str, str], int] = defaultdict(int)
    for r in rows:
        sid = str(r.get('source_id', '')).strip()
        cid = str(r.get('chunk_id', '')).strip()
        text = str(r.get('text', ''))
        if not sid or not cid or not text:
            continue
        key = (sid, cid)
        raw_counts[key] += 1
        if text not in idx[key]:
            idx[key].append(text)
    duplicate_keys = sum(1 for n in raw_counts.values() if n > 1)
    multi_variant_keys = sum(1 for texts in idx.values() if len(texts) > 1)
    return idx, duplicate_keys, multi_variant_keys


def grounded(evidence: str, variants: List[str]) -> bool:
    ev = canonical(evidence)
    return bool(ev) and any(ev in canonical(text) for text in variants)


def entity_flags(entity: Dict[str, Any]) -> List[str]:
    flags = []
    typ = str(entity.get('type', ''))
    name = str(entity.get('name', '')).strip()
    n = canonical(name)
    if not name:
        flags.append('empty_name')
    if typ == 'SULTAN':
        if re.fullmatch(r'\(?\d{3,4}\s*-\s*\d{3,4}\)?', name):
            flags.append('date_range_as_sultan')
        if any(x in n for x in ['devleti', 'antlaşması', 'muahede', 'nezareti']):
            flags.append('non_person_as_sultan')
    if typ == 'INSTITUTION' and any(x in n for x in ['antlaşması', 'muahede', 'fermanı', 'beratı']):
        flags.append('document_or_treaty_as_institution')
    if typ in {'PERSON', 'RULER', 'SULTAN'} and any(x in n for x in ['kalesi', 'vilayeti', 'antlaşması', 'defteri', 'ordusu']):
        flags.append('non_person_as_person')
    return flags


def claim_flags(claim: Dict[str, Any], evidence: str) -> List[str]:
    flags = []
    subject = str(claim.get('subject', '')).strip()
    obj = str(claim.get('object', '')).strip()
    relation = str(claim.get('relation', '')).strip()
    ev = canonical(evidence)
    if not subject:
        flags.append('empty_subject')
    if not obj:
        flags.append('empty_object')
    if not relation:
        flags.append('empty_relation')
    if subject and canonical(subject) not in ev:
        flags.append('subject_not_literal_in_evidence')
    if obj and canonical(obj) not in ev:
        flags.append('object_not_literal_in_evidence')
    return flags


def main() -> int:
    ap = argparse.ArgumentParser(description='Duplicate-aware V4 quality audit for v3 historical relations.')
    ap.add_argument('--sample-size', type=int, default=50)
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()

    relation_rows = load_jsonl(INPUT_PATH)
    corpus_rows = load_jsonl(CORPUS_PATH)
    corpus_idx, duplicate_corpus_keys, multi_variant_keys = build_corpus_index(corpus_rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total_entities = total_claims = 0
    evidence_fail_entities = evidence_fail_claims = 0
    heuristic_entity_flags = heuristic_claim_flags = 0
    duplicate_entities = duplicate_claims = 0
    rows_missing_source_text = empty_output_rows = 0
    entity_seen, claim_seen = set(), set()
    sample_pool = []
    source_counts = defaultdict(int)

    for row in relation_rows:
        sid = str(row.get('source_id', '')).strip()
        cid = str(row.get('chunk_id', '')).strip()
        source_counts[sid] += 1
        variants = corpus_idx.get((sid, cid), [])
        if not variants:
            rows_missing_source_text += 1

        entities = row.get('entities', []) or []
        claims = row.get('claims', []) or []
        if not entities and not claims:
            empty_output_rows += 1

        for e in entities:
            total_entities += 1
            evidence = str(e.get('evidence_quote', ''))
            ok = grounded(evidence, variants)
            if not ok:
                evidence_fail_entities += 1
            flags = entity_flags(e)
            heuristic_entity_flags += len(flags)
            key = (sid, cid, canonical(e.get('type', '')), canonical(e.get('name', '')), canonical(evidence))
            if key in entity_seen:
                duplicate_entities += 1
            else:
                entity_seen.add(key)
            sample_pool.append({'kind':'ENTITY','source_id':sid,'chunk_id':cid,'title':row.get('title',''),'type_or_relation':e.get('type',''),'subject_or_name':e.get('name',''),'object':'','evidence_quote':evidence,'evidence_grounded':ok,'heuristic_flags':';'.join(flags)})

        for c in claims:
            total_claims += 1
            evidence = str(c.get('evidence_quote', ''))
            ok = grounded(evidence, variants)
            if not ok:
                evidence_fail_claims += 1
            flags = claim_flags(c, evidence)
            heuristic_claim_flags += len(flags)
            key = (sid, cid, canonical(c.get('subject','')), canonical(c.get('relation','')), canonical(c.get('object','')), canonical(evidence))
            if key in claim_seen:
                duplicate_claims += 1
            else:
                claim_seen.add(key)
            sample_pool.append({'kind':'CLAIM','source_id':sid,'chunk_id':cid,'title':row.get('title',''),'type_or_relation':c.get('relation',''),'subject_or_name':c.get('subject',''),'object':c.get('object',''),'evidence_quote':evidence,'evidence_grounded':ok,'heuristic_flags':';'.join(flags)})

    total = total_entities + total_claims
    failed = evidence_fail_entities + evidence_fail_claims
    evidence_pass_rate = ((total - failed) / total * 100.0) if total else 0.0

    rng = random.Random(args.seed)
    by_source = defaultdict(list)
    for item in sample_pool:
        by_source[item['source_id']].append(item)
    sample = []
    sources = sorted(by_source)
    per_source = max(1, args.sample_size // len(sources)) if sources else 0
    for sid in sources:
        items = by_source[sid][:]
        rng.shuffle(items)
        sample.extend(items[:per_source])
    if len(sample) < args.sample_size:
        remaining = [x for x in sample_pool if x not in sample]
        rng.shuffle(remaining)
        sample.extend(remaining[:args.sample_size-len(sample)])
    sample = sample[:args.sample_size]

    csv_path = OUT_DIR / 'manual_review_sample.csv'
    with csv_path.open('w', newline='', encoding='utf-8-sig') as f:
        fields = ['kind','source_id','chunk_id','title','type_or_relation','subject_or_name','object','evidence_quote','evidence_grounded','heuristic_flags','human_correct','human_note']
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for item in sample:
            out = dict(item)
            out['human_correct'] = ''
            out['human_note'] = ''
            w.writerow(out)

    report = {
        'relation_rows': len(relation_rows),
        'source_count': len(source_counts),
        'total_entities': total_entities,
        'total_claims': total_claims,
        'evidence_fail_entities': evidence_fail_entities,
        'evidence_fail_claims': evidence_fail_claims,
        'evidence_pass_rate': round(evidence_pass_rate, 2),
        'duplicate_corpus_keys': duplicate_corpus_keys,
        'multi_text_variant_corpus_keys': multi_variant_keys,
        'duplicate_entities': duplicate_entities,
        'duplicate_claims': duplicate_claims,
        'rows_missing_source_text': rows_missing_source_text,
        'empty_output_rows': empty_output_rows,
        'heuristic_entity_flags': heuristic_entity_flags,
        'heuristic_claim_flags': heuristic_claim_flags,
        'manual_review_sample_size': len(sample),
        'manual_review_csv': str(csv_path),
        'source_distribution': dict(sorted(source_counts.items())),
    }
    report_path = OUT_DIR / 'relation_quality_report_v4.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    print('=== RELATION QUALITY AUDIT V4 ===')
    for k, v in report.items():
        if k != 'source_distribution':
            print(f'{k}: {v}')
    print('SOURCE DISTRIBUTION:')
    for sid, count in report['source_distribution'].items():
        print(f'  {sid}: {count}')
    if evidence_pass_rate >= 99.0 and rows_missing_source_text == 0:
        print('RELATION_QUALITY_EVIDENCE_GATE_V4: PASS')
    else:
        print('RELATION_QUALITY_EVIDENCE_GATE_V4: FAIL')
    print('NOTE: heuristic flags are review signals, not automatic factual failures.')
    print('NOTE: V4 checks evidence against ALL corpus text variants sharing the same source_id/chunk_id.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
