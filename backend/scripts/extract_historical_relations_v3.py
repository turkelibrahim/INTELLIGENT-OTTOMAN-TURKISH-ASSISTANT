from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, Iterable, List

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ai.ollama_provider import OllamaProvider


DATA_ROOT = PROJECT_ROOT / "datasets" / "historical_knowledge"
INGESTED_PATH = DATA_ROOT / "02_structured" / "overnight" / "ingested_chunks.jsonl"
OUTPUT_PATH = DATA_ROOT / "02_structured" / "overnight" / "derived_relation_candidates_v3.jsonl"
STATE_PATH = DATA_ROOT / "00_sources" / "relation_extraction_state_v3.json"

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
        "additionalProperties": False,
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
        "additionalProperties": False,
    }

    return {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "items": entity,
                "maxItems": 8,
            },
            "claims": {
                "type": "array",
                "items": claim,
                "maxItems": 5,
            },
        },
        "required": ["entities", "claims"],
        "additionalProperties": False,
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
        "antlaşma", "muahede", "muâhede", "ferman", "berat",
        "hatt-ı hümayun", "hatt-ı hümâyun", "padişah", "sultan",
        "şah", "nezaret", "paşa", "elçi", "ahid", "ahidname",
        "ahidnâme", "imzalan", "tarih", "mühimme", "reisülküttap",
    ]

    score = sum(3 for term in terms if term in text)
    score += min(len(re.findall(r"\b(?:1[3-9]\d{2}|20\d{2})\b", text)), 4)

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
            q = queues[source_id]
            if q:
                result.append(q.popleft())
            if not q:
                emptied.append(source_id)

        for source_id in emptied:
            queues.pop(source_id, None)

    return result


def compact_window(text: str, max_chars: int = 1800) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()

    if len(text) <= max_chars:
        return text

    # Prefer a historically dense window instead of blindly taking the beginning.
    keywords = [
        "antlaşma", "muahede", "ferman", "berat", "hatt-ı hümayun",
        "padişah", "sultan", "şah", "imzalan", "elçi", "paşa", "tarih",
    ]

    lower = text.casefold()
    positions = [lower.find(k) for k in keywords if lower.find(k) >= 0]
    center = min(positions) if positions else 0

    start = max(0, center - max_chars // 4)
    end = min(len(text), start + max_chars)

    window = text[start:end]

    if start > 0:
        first_space = window.find(" ")
        if first_space > 0:
            window = window[first_space + 1:]

    return window.strip()


def validate_result(result: Dict[str, Any], source_text: str):
    valid_entities = []
    rejected_entities = []

    for entity in result.get("entities", [])[:8]:
        name = str(entity.get("name", "")).strip()
        evidence = str(entity.get("evidence_quote", "")).strip()

        if name and evidence_in_source(evidence, source_text):
            valid_entities.append(entity)
        else:
            rejected_entities.append(entity)

    valid_claims = []
    rejected_claims = []

    for claim in result.get("claims", [])[:5]:
        subject = str(claim.get("subject", "")).strip()
        obj = str(claim.get("object", "")).strip()
        evidence = str(claim.get("evidence_quote", "")).strip()

        if subject and obj and evidence_in_source(evidence, source_text):
            valid_claims.append(claim)
        else:
            rejected_claims.append(claim)

    return valid_entities, rejected_entities, valid_claims, rejected_claims


def call_model(llm: OllamaProvider, text: str) -> Dict[str, Any]:
    return llm.chat_json(
        messages=[
            {
                "role": "system",
                "content": (
                    "Sen kanıt-kilitli Osmanlı tarih kaynak çıkarım motorusun. "
                    "SADECE verilen kaynak metnini kullan; dış bilgi kullanma. "
                    "En fazla 8 varlık ve en fazla 5 ilişki çıkar. "
                    "Yalnız tarihsel açıdan anlamlı ve açıkça desteklenen öğeleri seç. "
                    "SULTAN yalnız Osmanlı padişahıdır. "
                    "RULER Osmanlı dışı şah/kral/han gibi hükümdardır. "
                    "PERSON kişi; INSTITUTION gerçek devlet kurumu/teşkilatıdır. "
                    "TREATY antlaşma/muahede/protokol/mukavelenamedir. "
                    "DOCUMENT ferman, berat, hatt-ı hümayun, ahidname, mektup, telhis, takrir, defter gibi belgedir. "
                    "PLACE yer adıdır; DATE tarihtir; TITLE_OR_OFFICE unvan veya görevdir. "
                    "Soyut kavramları kurum/kişi yapma. Bir devlet adını padişah yapma. "
                    "Her evidence_quote kaynakta BİREBİR geçen, kısa ve tek cümlelik/ifadelik alıntı olsun. "
                    "Boş subject/object üretme. Aynı ilişkiyi tekrar etme."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Bu kaynak parçasından en önemli tarihsel varlıkları ve açık ilişkileri çıkar.\n\n"
                    f"KAYNAK:\n{text}"
                ),
            },
        ],
        schema=extraction_schema(),
        temperature=0.0,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="V3: balanced, compact, retrying historical relation extraction."
    )
    parser.add_argument("--max-chunks", type=int, default=20)
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
                "retries": 0,
                "valid_entities": 0,
                "valid_claims": 0,
            },
        },
    )

    processed = state.setdefault("processed", {})
    totals = state.setdefault("totals", {})

    success = 0
    failed = 0
    skipped = 0
    retries = 0
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

        original_text = str(record.get("text", "")).strip()
        text = compact_window(original_text, 1800)

        try:
            try:
                result = call_model(llm, text)
                used_text = text
                retry_used = False
            except RuntimeError as first_exc:
                # Main known failure mode: oversized/truncated JSON.
                if "invalid JSON" not in str(first_exc):
                    raise

                retries += 1
                retry_used = True
                used_text = compact_window(original_text, 900)
                result = call_model(llm, used_text)

            (
                valid_entities,
                rejected_entities,
                valid_claims,
                rejected_claims,
            ) = validate_result(result, used_text)

            output = {
                "schema_version": "3.0",
                "source_id": source_id,
                "chunk_id": chunk_id,
                "title": record.get("title", ""),
                "citation": record.get("citation", ""),
                "source_url": record.get("source_url", ""),
                "source_verified": bool(record.get("verified", False)),
                "derived_verified": False,
                "retry_used": retry_used,
                "input_chars": len(used_text),
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
                f"chars={len(used_text)} retry={retry_used} | "
                f"entities={len(valid_entities)} claims={len(valid_claims)} | "
                f"rejE={len(rejected_entities)} rejC={len(rejected_claims)}"
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
        totals["retries"] = int(totals.get("retries", 0)) + (1 if 'retry_used' in locals() and retry_used else 0)
        totals["valid_entities"] = int(totals.get("valid_entities", 0)) + (len(valid_entities) if 'valid_entities' in locals() else 0)
        totals["valid_claims"] = int(totals.get("valid_claims", 0)) + (len(valid_claims) if 'valid_claims' in locals() else 0)
        save_json(STATE_PATH, state)

    json_success_rate = (success / (success + failed) * 100.0) if (success + failed) else 0.0

    print()
    print("=== V3 RELATION EXTRACTION REPORT ===")
    print("SUCCESS:", success)
    print("FAILED:", failed)
    print("SKIPPED:", skipped)
    print("RETRIES:", retries)
    print("JSON SUCCESS RATE:", f"{json_success_rate:.1f}%")
    print("VALID ENTITIES:", run_valid_entities)
    print("VALID CLAIMS:", run_valid_claims)
    print("REJECTED ENTITIES:", run_rejected_entities)
    print("REJECTED CLAIMS:", run_rejected_claims)
    print("SOURCE DISTRIBUTION:")

    for source_id, count in sorted(source_counts.items()):
        print(f"  {source_id}: {count}")

    print("STATE:", STATE_PATH)
    print("OUTPUT:", OUTPUT_PATH)

    if success + failed >= 10 and json_success_rate >= 95.0 and len(source_counts) >= 3:
        print("HISTORICAL_RELATION_V3_GATE: PASS")
        return 0

    print("HISTORICAL_RELATION_V3_GATE: FAIL_QUALITY_THRESHOLD")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
