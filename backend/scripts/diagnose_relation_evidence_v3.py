from __future__ import annotations

import difflib
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
DATA_ROOT = PROJECT_ROOT / "datasets" / "historical_knowledge"

REL_PATH = DATA_ROOT / "02_structured" / "overnight" / "derived_relation_candidates_v3.jsonl"
CORPUS_PATH = DATA_ROOT / "02_structured" / "overnight" / "ingested_chunks.jsonl"
EXTRACTOR_PATH = BACKEND_ROOT / "scripts" / "extract_historical_relations_v3.py"
OUT_PATH = DATA_ROOT / "05_evaluation" / "relation_quality_v4" / "evidence_mismatch_diagnostics.json"


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
    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                obj["_line_no"] = line_no
                rows.append(obj)
            except json.JSONDecodeError:
                pass
    return rows


def corpus_index(rows: List[Dict[str, Any]]) -> Dict[Tuple[str, str], str]:
    idx = {}
    for r in rows:
        sid = str(r.get("source_id", "")).strip()
        cid = str(r.get("chunk_id", "")).strip()
        text = str(r.get("text", ""))
        if sid and cid and text and (sid, cid) not in idx:
            idx[(sid, cid)] = text
    return idx


def best_excerpt(evidence: str, source: str, window: int = 260) -> Dict[str, Any]:
    ev = canonical(evidence)
    src = canonical(source)

    if not ev or not src:
        return {"ratio": 0.0, "excerpt": ""}

    if ev in src:
        pos = src.find(ev)
        start = max(0, pos - 80)
        end = min(len(src), pos + len(ev) + 80)
        return {"ratio": 1.0, "excerpt": src[start:end]}

    target_len = max(60, min(len(ev) + 100, 700))
    step = max(25, target_len // 4)
    best_ratio = 0.0
    best = ""

    for start in range(0, max(1, len(src) - target_len + 1), step):
        candidate = src[start:start + target_len]
        ratio = difflib.SequenceMatcher(None, ev, candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best = candidate

    return {"ratio": round(best_ratio, 4), "excerpt": best[:window]}


def main() -> int:
    relation_rows = load_jsonl(REL_PATH)
    corpus_rows = load_jsonl(CORPUS_PATH)
    idx = corpus_index(corpus_rows)

    extractor_sha = None
    if EXTRACTOR_PATH.exists():
        extractor_sha = hashlib.sha256(EXTRACTOR_PATH.read_bytes()).hexdigest()

    failures = []
    passes = []
    fail_by_source = defaultdict(int)
    total = 0

    for row in relation_rows:
        sid = str(row.get("source_id", "")).strip()
        cid = str(row.get("chunk_id", "")).strip()
        source = idx.get((sid, cid), "")

        items = []
        for e in row.get("entities", []) or []:
            items.append(("ENTITY", e.get("name", ""), "", e.get("evidence_quote", "")))
        for c in row.get("claims", []) or []:
            items.append(("CLAIM", c.get("subject", ""), c.get("object", ""), c.get("evidence_quote", "")))

        for kind, left, right, evidence in items:
            total += 1
            grounded = bool(source) and canonical(evidence) in canonical(source)

            record = {
                "relation_jsonl_line": row.get("_line_no"),
                "source_id": sid,
                "chunk_id": cid,
                "kind": kind,
                "left": left,
                "right": right,
                "evidence_quote": evidence,
                "evidence_repr": repr(evidence),
                "evidence_length": len(str(evidence)),
                "source_length": len(source),
                "grounded": grounded,
            }

            if grounded:
                if len(passes) < 5:
                    passes.append(record)
            else:
                fail_by_source[sid] += 1
                match = best_excerpt(str(evidence), source)
                record["best_match_ratio"] = match["ratio"]
                record["best_source_excerpt"] = match["excerpt"]
                record["contains_three_dots"] = "..." in str(evidence)
                record["contains_unicode_ellipsis"] = "…" in str(evidence)
                if len(failures) < 20:
                    failures.append(record)

    report = {
        "relation_rows": len(relation_rows),
        "total_accepted_items_rechecked": total,
        "failure_count": sum(fail_by_source.values()),
        "pass_count": total - sum(fail_by_source.values()),
        "extractor_path": str(EXTRACTOR_PATH),
        "extractor_sha256": extractor_sha,
        "fail_by_source": dict(sorted(fail_by_source.items())),
        "first_20_failures": failures,
        "first_5_passes": passes,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=== EVIDENCE MISMATCH DIAGNOSTICS ===")
    print("relation_rows:", report["relation_rows"])
    print("accepted_items_rechecked:", report["total_accepted_items_rechecked"])
    print("pass_count:", report["pass_count"])
    print("failure_count:", report["failure_count"])
    print("extractor_sha256:", report["extractor_sha256"])
    print("FAIL BY SOURCE:")
    for sid, count in report["fail_by_source"].items():
        print(f"  {sid}: {count}")

    print()
    print("FIRST FAILURES:")
    for i, item in enumerate(failures[:8], 1):
        print(f"[{i}] {item['source_id']} | {item['chunk_id']} | {item['kind']}")
        print("EVIDENCE:", item["evidence_repr"][:500])
        print("BEST_MATCH_RATIO:", item.get("best_match_ratio"))
        print("BEST_SOURCE_EXCERPT:", item.get("best_source_excerpt", "")[:500])
        print("THREE_DOTS:", item.get("contains_three_dots"), "| UNICODE_ELLIPSIS:", item.get("contains_unicode_ellipsis"))
        print()

    print("REPORT:", OUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
