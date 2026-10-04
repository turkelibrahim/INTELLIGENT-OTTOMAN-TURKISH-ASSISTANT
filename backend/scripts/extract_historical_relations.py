from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ai.ollama_provider import OllamaProvider


DATA_ROOT = PROJECT_ROOT / "datasets" / "historical_knowledge"
INGESTED_PATH = DATA_ROOT / "02_structured" / "overnight" / "ingested_chunks.jsonl"
OUTPUT_PATH = DATA_ROOT / "02_structured" / "overnight" / "derived_relation_candidates.jsonl"
STATE_PATH = DATA_ROOT / "00_sources" / "relation_extraction_state.json"


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


def normalize(value: str) -> str:
    value = str(value or "").strip().strip('"“”‘’')
    return " ".join(value.casefold().split())


def relation_schema() -> Dict[str, Any]:
    claim = {
        "type": "object",
        "properties": {
            "subject": {"type": "string"},
            "relation": {"type": "string"},
            "object": {"type": "string"},
            "evidence_quote": {"type": "string"},
        },
        "required": ["subject", "relation", "object", "evidence_quote"],
    }
    return {
        "type": "object",
        "properties": {
            "sultans": {"type": "array", "items": {"type": "string"}},
            "treaties": {"type": "array", "items": {"type": "string"}},
            "decrees_or_documents": {"type": "array", "items": {"type": "string"}},
            "dates": {"type": "array", "items": {"type": "string"}},
            "places": {"type": "array", "items": {"type": "string"}},
            "persons": {"type": "array", "items": {"type": "string"}},
            "institutions": {"type": "array", "items": {"type": "string"}},
            "claims": {"type": "array", "items": claim},
        },
        "required": [
            "sultans",
            "treaties",
            "decrees_or_documents",
            "dates",
            "places",
            "persons",
            "institutions",
            "claims",
        ],
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

            key = (
                str(record.get("source_id", "")),
                str(record.get("chunk_id", "")),
            )
            if not all(key) or key in seen:
                continue
            seen.add(key)
            yield record


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract grounded historical relation candidates from already-ingested corpus chunks."
    )
    parser.add_argument("--max-chunks", type=int, default=100)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not INGESTED_PATH.exists():
        raise SystemExit(f"Missing ingested corpus file: {INGESTED_PATH}")

    llm = OllamaProvider()
    health = llm.health_check()
    if not health.get("reachable") or not health.get("model_available"):
        raise SystemExit(f"Ollama health check failed: {health}")

    print("OLLAMA:", health.get("model"))
    print("INPUT:", INGESTED_PATH)
    print("OUTPUT:", OUTPUT_PATH)

    state = load_json(
        STATE_PATH,
        {"processed": {}, "total_success": 0, "total_failed": 0},
    )
    processed = state.setdefault("processed", {})

    success = 0
    failed = 0
    skipped = 0

    for record in iter_unique_records(INGESTED_PATH):
        if success + failed >= args.max_chunks:
            break

        source_id = str(record["source_id"])
        chunk_id = str(record["chunk_id"])
        key = f"{source_id}::{chunk_id}"

        if processed.get(key) == "done" and not args.force:
            skipped += 1
            continue

        text = str(record.get("text", "")).strip()
        if len(text) < 80:
            processed[key] = "too_short"
            skipped += 1
            continue

        try:
            result = llm.chat_json(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Yalnız verilen kaynak metnini kullan. Genel tarih bilgini kullanma. "
                            "Kaynakta açıkça bulunmayan hiçbir kişi, padişah, antlaşma, ferman, tarih, "
                            "yer, kurum veya ilişki üretme. Her ilişki için kaynakta birebir bulunan "
                            "evidence_quote ver. Bu çıktı sadece aday çıkarımıdır; doğrulama kararı verme."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Aşağıdaki tarihî kaynak parçasından padişahlar, antlaşmalar, "
                            "ferman/belgeler, tarihler, yerler, kişiler, kurumlar ve açık ilişkileri çıkar.\n\n"
                            f"KAYNAK:\n{text}"
                        ),
                    },
                ],
                schema=relation_schema(),
                temperature=0.0,
            )

            normalized_source = normalize(text)
            valid_claims = []
            rejected_claims = []

            for claim in result.get("claims", []):
                evidence = normalize(claim.get("evidence_quote", ""))
                if evidence and evidence in normalized_source:
                    valid_claims.append(claim)
                else:
                    rejected_claims.append(claim)

            output = {
                "source_id": source_id,
                "chunk_id": chunk_id,
                "title": record.get("title", ""),
                "citation": record.get("citation", ""),
                "source_url": record.get("source_url", ""),
                "source_verified": bool(record.get("verified", False)),
                "derived_verified": False,
                "sultans": result.get("sultans", []),
                "treaties": result.get("treaties", []),
                "decrees_or_documents": result.get("decrees_or_documents", []),
                "dates": result.get("dates", []),
                "places": result.get("places", []),
                "persons": result.get("persons", []),
                "institutions": result.get("institutions", []),
                "claims": valid_claims,
                "rejected_claims": rejected_claims,
            }

            append_jsonl(OUTPUT_PATH, output)
            processed[key] = "done"
            success += 1

            print(
                f"[{success}/{args.max_chunks}] OK | {source_id} | "
                f"claims={len(valid_claims)} rejected={len(rejected_claims)}"
            )

        except KeyboardInterrupt:
            save_json(STATE_PATH, state)
            print("\nINTERRUPTED: checkpoint saved.")
            return 130
        except Exception as exc:
            processed[key] = f"error:{type(exc).__name__}"
            failed += 1
            print(f"FAIL | {source_id} | {chunk_id} | {exc!r}")

        state["total_success"] = int(state.get("total_success", 0)) + (1 if processed.get(key) == "done" else 0)
        state["total_failed"] = int(state.get("total_failed", 0)) + (1 if str(processed.get(key, "")).startswith("error:") else 0)
        save_json(STATE_PATH, state)

    print()
    print("=== RELATION EXTRACTION REPORT ===")
    print("SUCCESS:", success)
    print("FAILED:", failed)
    print("SKIPPED:", skipped)
    print("STATE:", STATE_PATH)
    print("OUTPUT:", OUTPUT_PATH)

    if success > 0:
        print("HISTORICAL_RELATION_EXTRACTION_GATE: PASS")
        return 0

    print("HISTORICAL_RELATION_EXTRACTION_GATE: FAIL_NO_NEW_RELATIONS")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
