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
DATA_ROOT = PROJECT_ROOT / "datasets" / "historical_knowledge"

INPUT_PATH = DATA_ROOT / "02_structured" / "overnight" / "derived_relation_candidates_v3.jsonl"
CORPUS_PATH = DATA_ROOT / "02_structured" / "overnight" / "ingested_chunks.jsonl"
OUT_DIR = DATA_ROOT / "05_evaluation" / "relation_quality_v3"


def canonical(value: str) -> str:
    value = str(value or "")
    value = value.replace("\u200b", "").replace("\ufeff", "")
    value = value.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    value = value.replace("–", "-").replace("—", "-").replace("‑", "-")
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"\s+", " ", value).strip().casefold()
    return value


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def corpus_index(rows: List[Dict[str, Any]]) -> Dict[Tuple[str, str], str]:
    idx = {}
    for r in rows:
        sid = str(r.get("source_id", "")).strip()
        cid = str(r.get("chunk_id", "")).strip()
        text = str(r.get("text", ""))
        if sid and cid and text:
            idx[(sid, cid)] = text
    return idx


def entity_sanity(entity: Dict[str, Any]) -> List[str]:
    issues = []
    et = str(entity.get("type", ""))
    name = str(entity.get("name", "")).strip()
    n = canonical(name)

    if not name:
        issues.append("empty_name")

    if et == "SULTAN":
        if re.fullmatch(r"\(?\d{3,4}\s*-\s*\d{3,4}\)?", name):
            issues.append("date_range_as_sultan")
        if any(x in n for x in ["devleti", "antlaşması", "muahede", "nezareti"]):
            issues.append("non_person_as_sultan")

    if et == "INSTITUTION":
        if any(x in n for x in ["antlaşması", "muahede", "fermanı", "beratı", "defteri"]):
            issues.append("document_or_treaty_as_institution")

    if et in {"PERSON", "RULER", "SULTAN"}:
        if any(x in n for x in ["kalesi", "vilayeti", "antlaşması", "defteri", "ordusu"]):
            issues.append("non_person_as_person")

    return issues


def claim_sanity(claim: Dict[str, Any], evidence: str) -> List[str]:
    issues = []
    subject = str(claim.get("subject", "")).strip()
    obj = str(claim.get("object", "")).strip()
    relation = str(claim.get("relation", "")).strip()

    if not subject:
        issues.append("empty_subject")
    if not obj:
        issues.append("empty_object")
    if not relation:
        issues.append("empty_relation")

    ev = canonical(evidence)
    if subject and canonical(subject) not in ev:
        issues.append("subject_not_literal_in_evidence")
    if obj and canonical(obj) not in ev:
        issues.append("object_not_literal_in_evidence")

    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic quality audit for v3 historical relation extraction.")
    ap.add_argument("--sample-size", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rows = load_jsonl(INPUT_PATH)
    corpus_rows = load_jsonl(CORPUS_PATH)
    cidx = corpus_index(corpus_rows)

    if not rows:
        raise SystemExit(f"No relation rows found: {INPUT_PATH}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total_entities = 0
    total_claims = 0
    evidence_fail_entities = 0
    evidence_fail_claims = 0
    heuristic_entity_flags = 0
    heuristic_claim_flags = 0
    duplicate_entity_count = 0
    duplicate_claim_count = 0
    rows_missing_source = 0
    empty_output_rows = 0

    entity_seen = set()
    claim_seen = set()
    sample_pool = []
    source_counts = defaultdict(int)

    for row in rows:
        sid = str(row.get("source_id", ""))
        cid = str(row.get("chunk_id", ""))
        source_counts[sid] += 1
        source_text = cidx.get((sid, cid), "")

        if not source_text:
            rows_missing_source += 1

        entities = row.get("entities", []) or []
        claims = row.get("claims", []) or []
        if not entities and not claims:
            empty_output_rows += 1

        for e in entities:
            total_entities += 1
            evidence = str(e.get("evidence_quote", ""))
            grounded = bool(source_text) and canonical(evidence) in canonical(source_text)
            if not grounded:
                evidence_fail_entities += 1

            flags = entity_sanity(e)
            heuristic_entity_flags += len(flags)

            key = (
                sid, cid,
                canonical(e.get("type", "")),
                canonical(e.get("name", "")),
                canonical(evidence),
            )
            if key in entity_seen:
                duplicate_entity_count += 1
            else:
                entity_seen.add(key)

            sample_pool.append({
                "kind": "ENTITY",
                "source_id": sid,
                "chunk_id": cid,
                "title": row.get("title", ""),
                "type_or_relation": e.get("type", ""),
                "subject_or_name": e.get("name", ""),
                "object": "",
                "evidence_quote": evidence,
                "evidence_grounded": grounded,
                "heuristic_flags": ";".join(flags),
            })

        for c in claims:
            total_claims += 1
            evidence = str(c.get("evidence_quote", ""))
            grounded = bool(source_text) and canonical(evidence) in canonical(source_text)
            if not grounded:
                evidence_fail_claims += 1

            flags = claim_sanity(c, evidence)
            heuristic_claim_flags += len(flags)

            key = (
                sid, cid,
                canonical(c.get("subject", "")),
                canonical(c.get("relation", "")),
                canonical(c.get("object", "")),
                canonical(evidence),
            )
            if key in claim_seen:
                duplicate_claim_count += 1
            else:
                claim_seen.add(key)

            sample_pool.append({
                "kind": "CLAIM",
                "source_id": sid,
                "chunk_id": cid,
                "title": row.get("title", ""),
                "type_or_relation": c.get("relation", ""),
                "subject_or_name": c.get("subject", ""),
                "object": c.get("object", ""),
                "evidence_quote": evidence,
                "evidence_grounded": grounded,
                "heuristic_flags": ";".join(flags),
            })

    rng = random.Random(args.seed)

    by_source = defaultdict(list)
    for item in sample_pool:
        by_source[item["source_id"]].append(item)

    sample = []
    sources = sorted(by_source)
    if sources:
        per_source = max(1, args.sample_size // len(sources))
        for sid in sources:
            candidates = by_source[sid][:]
            rng.shuffle(candidates)
            sample.extend(candidates[:per_source])

    if len(sample) < args.sample_size:
        remaining = [x for x in sample_pool if x not in sample]
        rng.shuffle(remaining)
        sample.extend(remaining[: args.sample_size - len(sample)])

    sample = sample[:args.sample_size]

    csv_path = OUT_DIR / "manual_review_sample.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        fieldnames = [
            "kind", "source_id", "chunk_id", "title", "type_or_relation",
            "subject_or_name", "object", "evidence_quote",
            "evidence_grounded", "heuristic_flags",
            "human_correct", "human_note",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for item in sample:
            row = dict(item)
            row["human_correct"] = ""
            row["human_note"] = ""
            w.writerow(row)

    evidence_total = total_entities + total_claims
    evidence_fail_total = evidence_fail_entities + evidence_fail_claims
    evidence_pass_rate = (
        (evidence_total - evidence_fail_total) / evidence_total * 100.0
        if evidence_total else 0.0
    )

    report = {
        "input_rows": len(rows),
        "source_count": len(source_counts),
        "total_entities": total_entities,
        "total_claims": total_claims,
        "evidence_fail_entities": evidence_fail_entities,
        "evidence_fail_claims": evidence_fail_claims,
        "evidence_pass_rate": round(evidence_pass_rate, 2),
        "heuristic_entity_flags": heuristic_entity_flags,
        "heuristic_claim_flags": heuristic_claim_flags,
        "duplicate_entities": duplicate_entity_count,
        "duplicate_claims": duplicate_claim_count,
        "rows_missing_source_text": rows_missing_source,
        "empty_output_rows": empty_output_rows,
        "manual_review_sample_size": len(sample),
        "manual_review_csv": str(csv_path),
        "source_distribution": dict(sorted(source_counts.items())),
    }

    report_path = OUT_DIR / "relation_quality_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=== RELATION QUALITY AUDIT ===")
    for k, v in report.items():
        if k != "source_distribution":
            print(f"{k}: {v}")
    print("SOURCE DISTRIBUTION:")
    for sid, count in report["source_distribution"].items():
        print(f"  {sid}: {count}")

    if evidence_pass_rate == 100.0 and rows_missing_source == 0:
        print("RELATION_QUALITY_EVIDENCE_GATE: PASS")
    else:
        print("RELATION_QUALITY_EVIDENCE_GATE: FAIL")

    print("NOTE: heuristic flags are review signals, not automatic factual failures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
