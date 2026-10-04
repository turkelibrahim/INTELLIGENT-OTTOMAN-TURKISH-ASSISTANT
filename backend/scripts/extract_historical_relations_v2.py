from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ai.ollama_provider import OllamaProvider


DATA_ROOT = PROJECT_ROOT / "datasets" / "historical_knowledge"
INGESTED_PATH = DATA_ROOT / "02_structured" / "overnight" / "ingested_chunks.jsonl"
OUTPUT_PATH = DATA_ROOT / "02_structured" / "overnight" / "derived_relation_candidates_v2.jsonl"
STATE_PATH = DATA_ROOT / "00_sources" / "relation_extraction_state_v2.json"

ENTITY_TYPES = [
    "SULTAN",
    "RULER",
    "PERSON",
    "TREATY",
    "DOCUMENT",
    "INSTITUTION",
    "PLACE",
    "DATE",
    "TITLE_OR_OFFICE",
]

RELATION_TYPES = [
    "ISSUED_BY",
    "SIGNED_OR_CONCLUDED_BY",
    "PARTY_TO",
    "SENT_TO",
    "SENT_BY",
    "RULED_DURING",
    "DATED",
    "LOCATED_IN",
    "SERVED_AS",
    "ESTABLISHED",
    "PUBLISHED_BY",
    "RELATED_TO",
]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def canonical(value: str) -> str:
    value = str(value or "")
    value = value.replace("\u200b", "").replace("\ufeff", "")
    value = value.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    value = value.replace("–", "-").replace("—", "-").replace("‑", "-")
    value = unicodedata.normalize("NFKC", value)
    value = value.strip().strip('"').strip("'")
    value = re.sub(r"\s+", " ", value)
    return value.casefold()


def evidence_in_source(evidence: str, source_text: str) -> bool:
    ev = canonical(evidence)
    src = canonical(source_text)
    return bool(ev) and ev in src


def extraction_schema() -> Dict[str, Any]:
    entity = {
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ENTITY_TYPES},
            "name": {"type": "string"},
            "evidence_quote": {"type": "string"},
        },
        "required": ["type", "name", "evidence_quote"],
    }

    claim = {
        "type": "object",
        "properties": {
            "subject": {"type": "string"},
            "relation": {"type": "string", "enum": RELATION_TYPES},
            "object": {"type": "string"},
            "evidence_quote": {"type": "string"},
        },
        "required": ["subject", "relation", "object", "evidence_quote"],
    }

    return {
        "type": "object",
        "properties": {
            "entities": {"type": "array", "items": entity},
            "claims": {"type": "array", "items": claim},
        },
        "required": ["entities", "claims"],
    }


def iter_unique_records(path: Path) -> Iterable[Dict[str, Any]]:
    seen = set()

    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            source_id = str(record.get("source_id", "")).strip()
            chunk_id = str(record.get("chunk_id", "")).strip()

            if not source_id or not chunk_id:
                continue

            key = (source_id, chunk_id)
            if key in seen:
                continue

            seen.add(key)
            yield record


def chunk_priority(record: Dict[str, Any]) -> int:
    text = str(record.get("text", "")).casefold()

    terms = [
        "antlaşma",
        "muahede",
        "muâhede",
        "ferman",
        "berat",
        "hatt-ı hümayun",
        "hatt-ı hümâyun",
        "padişah",
        "sultan",
        "şah",
        "nezaret",
        "paşa",
        "elçi",
        "ahid",
        "ahidname",
        "ahidnâme",
        "imzalan",
        "tarih",
    ]

    score = sum(3 for term in terms if term in text)
    score += min(len(re.findall(r"\b(?:1[4-9]\d{2}|20\d{2})\b", text)), 4)

    # Front matter / bibliographic chunks are useful but lower priority.
    if any(term in text for term in ["isbn", "matbaa", "kapak", "editör", "yayın no"]):
        score -= 4

    return score


def balanced_records(path: Path) -> List[Dict[str, Any]]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for record in iter_unique_records(path):
        text = str(record.get("text", "")).strip()
        if len(text) < 120:
            continue
        groups[str(record["source_id"])].append(record)

    for source_id in groups:
        groups[source_id].sort(key=chunk_priority, reverse=True)

    queues = {
        source_id: deque(records)
        for source_id, records in sorted(groups.items())
        if records
    }

    result: List[Dict[str, Any]] = []

    while queues:
        emptied = []

        for source_id in list(queues):
            queue = queues[source_id]

            if queue:
                result.append(queue.popleft())

            if not queue:
                emptied.append(source_id)

        for source_id in emptied:
            queues.pop(source_id, None)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Balanced, evidence-grounded historical relation extraction from existing corpus."
    )
    parser.add_argument("--max-chunks", type=int, default=30)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not INGESTED_PATH.exists():
        raise SystemExit(f"Missing corpus file: {INGESTED_PATH}")

    llm = OllamaProvider()
    health = llm.health_check()

    if not health.get("reachable") or not health.get("model_available"):
        raise SystemExit(f"Ollama health check failed: {health}")

    print("OLLAMA:", health.get("model"))
    print("INPUT:", INGESTED_PATH)
    print("OUTPUT:", OUTPUT_PATH)

    state = load_json(
        STATE_PATH,
        {
            "processed": {},
            "totals": {
                "success": 0,
                "failed": 0,
                "valid_entities": 0,
                "valid_claims": 0,
                "rejected_entities": 0,
                "rejected_claims": 0,
            },
        },
    )

    processed = state.setdefault("processed", {})
    totals = state.setdefault("totals", {})

    success = 0
    failed = 0
    skipped = 0
    run_valid_entities = 0
    run_valid_claims = 0
    run_rejected_entities = 0
    run_rejected_claims = 0
    source_counts: Dict[str, int] = defaultdict(int)

    for record in balanced_records(INGESTED_PATH):
        if success + failed >= args.max_chunks:
            break

        source_id = str(record["source_id"])
        chunk_id = str(record["chunk_id"])
        key = f"{source_id}::{chunk_id}"

        if processed.get(key) == "done" and not args.force:
            skipped += 1
            continue

        text = str(record.get("text", "")).strip()

        try:
            result = llm.chat_json(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Sen kanıt-kilitli Osmanlı tarih kaynak çıkarım motorusun. "
                            "YALNIZ verilen kaynak parçasını kullan. Genel tarih bilgini kullanma. "
                            "Bir varlığı yalnız metinde açıkça geçiyorsa çıkar. "
                            "SULTAN sadece Osmanlı padişahları içindir; devlet, tarih aralığı veya başka hükümdarları SULTAN yapma. "
                            "RULER Osmanlı dışındaki şah, kral, han vb. hükümdarlar içindir. "
                            "INSTITUTION sadece gerçek kurum/teşkilat/devlet kuruluşu olmalıdır; soyut kavramları veya antlaşmaları kurum yapma. "
                            "TREATY yalnız antlaşma/muahede/protokol/mukavelename türü uluslararası anlaşmalardır. "
                            "DOCUMENT ferman, berat, hatt-ı hümayun, mektup, talimat, defter gibi belge türleri veya tekil belgelerdir. "
                            "Her entity ve claim için KAYNAKTA BİREBİR geçen kısa evidence_quote ver. "
                            "Boş subject/object üretme. Relation yalnız şemadaki seçeneklerden biri olmalı."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Aşağıdaki tarihî kaynak parçasından yalnız açıkça desteklenen varlıkları ve ilişkileri çıkar.\n\n"
                            f"KAYNAK:\n{text}"
                        ),
                    },
                ],
                schema=extraction_schema(),
                temperature=0.0,
            )

            valid_entities = []
            rejected_entities = []

            for entity in result.get("entities", []):
                name = str(entity.get("name", "")).strip()
                evidence = str(entity.get("evidence_quote", "")).strip()

                if name and evidence_in_source(evidence, text):
                    valid_entities.append(entity)
                else:
                    rejected_entities.append(entity)

            valid_claims = []
            rejected_claims = []

            for claim in result.get("claims", []):
                subject = str(claim.get("subject", "")).strip()
                obj = str(claim.get("object", "")).strip()
                evidence = str(claim.get("evidence_quote", "")).strip()

                if (
                    subject
                    and obj
                    and evidence_in_source(evidence, text)
                ):
                    valid_claims.append(claim)
                else:
                    rejected_claims.append(claim)

            output = {
                "schema_version": "2.0",
                "source_id": source_id,
                "chunk_id": chunk_id,
                "title": record.get("title", ""),
                "citation": record.get("citation", ""),
                "source_url": record.get("source_url", ""),
                "source_verified": bool(record.get("verified", False)),
                "derived_verified": False,
                "entities": valid_entities,
                "claims": valid_claims,
                "rejected_entities": rejected_entities,
                "rejected_claims": rejected_claims,
            }

            append_jsonl(OUTPUT_PATH, output)

            processed[key] = "done"
            success += 1
            source_counts[source_id] += 1

            run_valid_entities += len(valid_entities)
            run_valid_claims += len(valid_claims)
            run_rejected_entities += len(rejected_entities)
            run_rejected_claims += len(rejected_claims)

            print(
                f"[{success}/{args.max_chunks}] OK | {source_id} | "
                f"entities={len(valid_entities)} claims={len(valid_claims)} | "
                f"rejected_entities={len(rejected_entities)} rejected_claims={len(rejected_claims)}"
            )

        except KeyboardInterrupt:
            save_json(STATE_PATH, state)
            print("\nINTERRUPTED: checkpoint saved.")
            return 130
        except Exception as exc:
            processed[key] = f"error:{type(exc).__name__}"
            failed += 1
            print(f"FAIL | {source_id} | {chunk_id} | {exc!r}")

        totals["success"] = int(totals.get("success", 0)) + (1 if processed.get(key) == "done" else 0)
        totals["failed"] = int(totals.get("failed", 0)) + (1 if str(processed.get(key, "")).startswith("error:") else 0)
        totals["valid_entities"] = int(totals.get("valid_entities", 0)) + len(valid_entities if 'valid_entities' in locals() else [])
        totals["valid_claims"] = int(totals.get("valid_claims", 0)) + len(valid_claims if 'valid_claims' in locals() else [])
        totals["rejected_entities"] = int(totals.get("rejected_entities", 0)) + len(rejected_entities if 'rejected_entities' in locals() else [])
        totals["rejected_claims"] = int(totals.get("rejected_claims", 0)) + len(rejected_claims if 'rejected_claims' in locals() else [])
        save_json(STATE_PATH, state)

    print()
    print("=== BALANCED RELATION EXTRACTION REPORT ===")
    print("SUCCESS:", success)
    print("FAILED:", failed)
    print("SKIPPED:", skipped)
    print("VALID ENTITIES:", run_valid_entities)
    print("VALID CLAIMS:", run_valid_claims)
    print("REJECTED ENTITIES:", run_rejected_entities)
    print("REJECTED CLAIMS:", run_rejected_claims)
    print("SOURCE DISTRIBUTION:")

    for source_id, count in sorted(source_counts.items()):
        print(f"  {source_id}: {count}")

    print("STATE:", STATE_PATH)
    print("OUTPUT:", OUTPUT_PATH)

    if success > 0:
        print("BALANCED_HISTORICAL_RELATION_GATE: PASS")
        return 0

    print("BALANCED_HISTORICAL_RELATION_GATE: FAIL_NO_NEW_RELATIONS")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
