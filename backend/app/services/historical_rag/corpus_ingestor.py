import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from app.services.historical_rag.qdrant_store import HistoricalQdrantStore


class HistoricalCorpusIngestor:

    REQUIRED_FIELDS = {
        "source_id",
        "chunk_id",
        "title",
        "text",
        "source_type",
        "source_tier",
        "citation",
        "verified",
    }

    ALLOWED_TIERS = {"A", "B", "C"}

    def __init__(self, store: HistoricalQdrantStore | None = None):
        self.store = store or HistoricalQdrantStore()

    @staticmethod
    def _stable_point_id(source_id: str, chunk_id: str) -> int:
        raw = f"{source_id}::{chunk_id}".encode("utf-8")

        digest = hashlib.blake2b(
            raw,
            digest_size=8
        ).digest()

        value = int.from_bytes(
            digest,
            byteorder="big",
            signed=False
        )

        # Signed 63-bit range içinde tut.
        return value & 0x7FFFFFFFFFFFFFFF

    def _validate(self, record: Dict[str, Any]) -> None:

        missing = self.REQUIRED_FIELDS - set(record)

        if missing:
            raise ValueError(
                f"Missing required fields: {sorted(missing)}"
            )

        if record["verified"] is not True:
            raise ValueError(
                "Only verified=true records may enter the production corpus."
            )

        if record["source_tier"] not in self.ALLOWED_TIERS:
            raise ValueError(
                f"Invalid source_tier: {record['source_tier']}"
            )

        for key in (
            "source_id",
            "chunk_id",
            "title",
            "text",
            "source_type",
            "citation",
        ):
            if not str(record[key]).strip():
                raise ValueError(
                    f"{key} must not be empty."
                )

    @staticmethod
    def _searchable_text(record: Dict[str, Any]) -> str:

        aliases = record.get("aliases", [])
        keywords = record.get("keywords", [])

        parts = [
            record["title"],
            " ".join(str(x) for x in aliases),
            " ".join(str(x) for x in keywords),
            record["text"],
        ]

        return "\n".join(
            part.strip()
            for part in parts
            if part and part.strip()
        )

    def ingest_record(
        self,
        record: Dict[str, Any]
    ) -> int:

        self._validate(record)

        point_id = self._stable_point_id(
            str(record["source_id"]),
            str(record["chunk_id"]),
        )

        searchable_text = self._searchable_text(record)

        payload = {
            "source_id": str(record["source_id"]),
            "chunk_id": str(record["chunk_id"]),
            "title": record["title"],
            "source_type": record["source_type"],
            "source_tier": record["source_tier"],
            "citation": record["citation"],
            "source_url": record.get("source_url", ""),
            "aliases": record.get("aliases", []),
            "keywords": record.get("keywords", []),
            "verified": True,
            "license_note": record.get("license_note", ""),
            "published_year": record.get("published_year"),
            "ingested_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self.store.upsert(
            item_id=point_id,
            text=searchable_text,
            payload=payload,
        )

        return point_id

    def ingest_jsonl(
        self,
        path: str | Path
    ) -> Dict[str, Any]:

        path = Path(path)

        accepted = 0
        rejected = 0
        errors = []

        with path.open(
            "r",
            encoding="utf-8-sig"
        ) as handle:

            for line_number, line in enumerate(
                handle,
                start=1
            ):
                line = line.strip()

                if not line:
                    continue

                try:
                    record = json.loads(line)

                    self.ingest_record(record)

                    accepted += 1

                except Exception as exc:
                    rejected += 1

                    errors.append({
                        "line": line_number,
                        "error": str(exc),
                    })

        return {
            "file": str(path),
            "accepted": accepted,
            "rejected": rejected,
            "errors": errors,
        }

    def close(self):
        self.store.close()
