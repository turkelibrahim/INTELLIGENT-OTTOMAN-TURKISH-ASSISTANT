from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import requests

try:
    import pypdfium2 as pdfium
except Exception:
    pdfium = None

try:
    from openpyxl import load_workbook
except Exception:
    load_workbook = None


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.historical_rag import HistoricalCorpusIngestor

try:
    from app.services.ai.ollama_provider import OllamaProvider
except Exception:
    OllamaProvider = None


DATA_ROOT = PROJECT_ROOT / "datasets" / "historical_knowledge"
MANIFEST_PATH = DATA_ROOT / "00_sources" / "ottoman_open_sources_manifest_v1.json"
RAW_DIR = DATA_ROOT / "01_raw" / "overnight"
STRUCTURED_DIR = DATA_ROOT / "02_structured" / "overnight"
CHUNKS_DIR = DATA_ROOT / "03_chunks" / "overnight"
REJECTED_DIR = DATA_ROOT / "04_rejected" / "overnight"
REPORT_DIR = DATA_ROOT / "05_evaluation"
STATE_PATH = DATA_ROOT / "00_sources" / "overnight_state.json"
LOG_PATH = REPORT_DIR / "overnight_corpus_builder.log"
CANDIDATES_PATH = STRUCTURED_DIR / "derived_relation_candidates.jsonl"
INGESTED_PATH = STRUCTURED_DIR / "ingested_chunks.jsonl"

AUTO_TIERS = {"A", "B"}
AUTO_SOURCE_TYPES = {
    "official_archive_publication",
    "official_structured_dataset",
    "public_domain_document_image",
    "public_domain_treaty_compilation",
    "public_domain_ottoman_turkish_book",
}
SKIP_SOURCE_TYPES = {
    "official_archive_index",
    "structured_open_data",
    "historical_turkish_nlp_dataset",
    "historical_turkish_ner_dataset",
}

USER_AGENT = "IntelligentOttomanAssistantCorpusBuilder/1.0 (research corpus builder)"


@dataclass
class ExtractedUnit:
    locator: str
    text: str
    extraction_mode: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    for path in (
        RAW_DIR,
        STRUCTURED_DIR,
        CHUNKS_DIR,
        REJECTED_DIR,
        REPORT_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(path)


def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clean_url(value: str) -> str:
    """
    Accept both normal URLs and an accidentally markdown-wrapped URL:
    [https://example](https://example)
    """
    value = str(value or "").strip()
    match = re.fullmatch(r"\[(https?://[^\]]+)\]\((https?://[^)]+)\)", value)
    if match:
        return match.group(2)
    return value


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value[:120] or "source"


def detect_extension(response: requests.Response, url: str) -> str:
    content_type = (response.headers.get("content-type") or "").lower()
    disposition = response.headers.get("content-disposition") or ""

    filename_match = re.search(
        r'filename\*?=(?:UTF-8\'\')?["\']?([^;"\']+)',
        disposition,
        flags=re.IGNORECASE,
    )
    if filename_match:
        suffix = Path(filename_match.group(1)).suffix.lower()
        if suffix:
            return suffix

    if "application/pdf" in content_type:
        return ".pdf"
    if (
        "spreadsheetml" in content_type
        or "application/vnd.ms-excel" in content_type
    ):
        return ".xlsx"
    if "application/json" in content_type:
        return ".json"
    if "text/plain" in content_type:
        return ".txt"
    if "text/html" in content_type:
        return ".html"

    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".pdf", ".xlsx", ".xls", ".json", ".txt", ".csv", ".html", ".htm"}:
        return suffix

    # Magic-byte fallback.
    prefix = response.content[:8]
    if prefix.startswith(b"%PDF"):
        return ".pdf"
    if prefix.startswith(b"PK"):
        return ".xlsx"

    return ".bin"


def download_source(
    session: requests.Session,
    source: Dict[str, Any],
    timeout: int = 120,
) -> Tuple[Optional[Path], Dict[str, Any]]:
    source_id = source["id"]
    url = clean_url(source.get("url", ""))
    meta: Dict[str, Any] = {
        "source_id": source_id,
        "url": url,
        "downloaded_at": utc_now(),
    }

    if not url.startswith(("http://", "https://")):
        meta["status"] = "invalid_url"
        return None, meta

    response = session.get(
        url,
        timeout=timeout,
        allow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()

    ext = detect_extension(response, response.url)
    filename = f"{safe_name(source_id)}{ext}"
    path = RAW_DIR / filename

    path.write_bytes(response.content)

    meta.update(
        {
            "status": "downloaded",
            "final_url": response.url,
            "content_type": response.headers.get("content-type", ""),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "path": str(path),
            "extension": ext,
        }
    )
    return path, meta


def extract_pdf(path: Path) -> Tuple[List[ExtractedUnit], Dict[str, Any]]:
    if pdfium is None:
        raise RuntimeError("pypdfium2 is not installed.")

    pdf = pdfium.PdfDocument(str(path))
    units: List[ExtractedUnit] = []
    empty_pages: List[int] = []

    try:
        for index in range(len(pdf)):
            page = pdf[index]
            text_page = page.get_textpage()
            try:
                text = text_page.get_text_range() or ""
            finally:
                try:
                    text_page.close()
                except Exception:
                    pass
                try:
                    page.close()
                except Exception:
                    pass

            text = normalize_source_text(text)
            page_number = index + 1

            if len(text) < 80:
                empty_pages.append(page_number)
                continue

            units.append(
                ExtractedUnit(
                    locator=f"page:{page_number}",
                    text=text,
                    extraction_mode="pdf_text_layer",
                )
            )
    finally:
        try:
            pdf.close()
        except Exception:
            pass

    meta = {
        "pages_total": len(pdf) if hasattr(pdf, "__len__") else None,
        "pages_with_text": len(units),
        "pages_needing_ocr": empty_pages,
    }
    return units, meta


def extract_xlsx(path: Path, rows_per_unit: int = 40) -> Tuple[List[ExtractedUnit], Dict[str, Any]]:
    if load_workbook is None:
        raise RuntimeError("openpyxl is not installed.")

    wb = load_workbook(path, read_only=True, data_only=True)
    units: List[ExtractedUnit] = []
    sheets_meta: Dict[str, int] = {}

    try:
        for ws in wb.worksheets:
            rows: List[str] = []
            start_row = 1
            nonempty_count = 0

            def flush(end_row: int) -> None:
                nonlocal rows, start_row
                if not rows:
                    return
                text = "\n".join(rows).strip()
                if text:
                    units.append(
                        ExtractedUnit(
                            locator=f"sheet:{ws.title};rows:{start_row}-{end_row}",
                            text=text,
                            extraction_mode="xlsx_structured",
                        )
                    )
                rows = []
                start_row = end_row + 1

            for row_index, row in enumerate(ws.iter_rows(values_only=True), start=1):
                values = [
                    str(value).strip()
                    for value in row
                    if value is not None and str(value).strip()
                ]
                if values:
                    nonempty_count += 1
                    rows.append(" | ".join(values))

                if len(rows) >= rows_per_unit:
                    flush(row_index)

            flush(ws.max_row or start_row)
            sheets_meta[ws.title] = nonempty_count
    finally:
        wb.close()

    return units, {"sheets": sheets_meta, "units": len(units)}


def extract_text_file(path: Path) -> Tuple[List[ExtractedUnit], Dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    text = normalize_source_text(text)
    if not text:
        return [], {"characters": 0}
    return [
        ExtractedUnit(
            locator="text:1",
            text=text,
            extraction_mode="digital_text",
        )
    ], {"characters": len(text)}


def normalize_source_text(text: str) -> str:
    text = str(text or "").replace("\x00", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text(
    text: str,
    max_chars: int = 3600,
    overlap_chars: int = 450,
) -> List[str]:
    text = normalize_source_text(text)
    if len(text) <= max_chars:
        return [text] if text else []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)

        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            start = 0
            while start < len(paragraph):
                end = min(start + max_chars, len(paragraph))
                part = paragraph[start:end].strip()
                if part:
                    chunks.append(part)
                if end >= len(paragraph):
                    current = ""
                    break
                start = max(end - overlap_chars, start + 1)

    if current:
        chunks.append(current)

    # Add overlap between paragraph-sized chunks without changing source order.
    if overlap_chars > 0 and len(chunks) > 1:
        overlapped: List[str] = [chunks[0]]
        for i in range(1, len(chunks)):
            prefix = chunks[i - 1][-overlap_chars:].strip()
            combined = f"{prefix}\n\n{chunks[i]}".strip()
            overlapped.append(combined[: max_chars + overlap_chars])
        chunks = overlapped

    return chunks


def source_auto_eligible(source: Dict[str, Any], file_path: Path) -> Tuple[bool, str]:
    tier = str(source.get("tier", "")).strip()
    source_type = str(source.get("source_type", "")).strip()

    if source_type in SKIP_SOURCE_TYPES:
        return False, f"source_type={source_type} is discovery/NLP only"

    if tier not in AUTO_TIERS:
        return False, f"tier={tier} is not auto-ingest eligible"

    if file_path.suffix.lower() not in {".pdf", ".xlsx", ".txt", ".json"}:
        return False, f"file_type={file_path.suffix} requires manual handling"

    return True, "eligible"


def make_citation(source: Dict[str, Any], locator: str) -> str:
    title = source.get("title", source.get("id", "Unknown source"))
    url = clean_url(source.get("url", ""))
    return f"{title}; {locator}; {url}"


def build_records(
    source: Dict[str, Any],
    units: List[ExtractedUnit],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    source_id = str(source["id"])
    source_tier = str(source.get("tier", "B"))

    for unit_index, unit in enumerate(units, start=1):
        for chunk_index, chunk in enumerate(split_text(unit.text), start=1):
            chunk_hash = sha256_text(chunk)
            chunk_id = f"{unit_index:05d}-{chunk_index:03d}-{chunk_hash[:12]}"
            records.append(
                {
                    "source_id": source_id,
                    "chunk_id": chunk_id,
                    "title": source.get("title", source_id),
                    "text": chunk,
                    "source_type": source.get("source_type", "historical_source"),
                    "source_tier": source_tier,
                    "citation": make_citation(source, unit.locator),
                    "source_url": clean_url(source.get("url", "")),
                    "aliases": [],
                    "keywords": [],
                    "verified": True,
                    "source_verified": True,
                    "extraction_verified": True,
                    "extraction_mode": unit.extraction_mode,
                    "locator": unit.locator,
                    "license_note": source.get(
                        "license",
                        source.get("rights_note", source.get("rights_note", "")),
                    ),
                }
            )
    return records


def normalized_evidence(value: str) -> str:
    value = str(value or "").strip().strip('"“”‘’')
    return " ".join(value.casefold().split())


def llm_relation_schema() -> Dict[str, Any]:
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


def extract_relation_candidates(
    llm: Any,
    record: Dict[str, Any],
) -> Dict[str, Any]:
    source_text = record["text"]
    response = llm.chat_json(
        messages=[
            {
                "role": "system",
                "content": (
                    "Yalnız verilen kaynak parçasını kullan. Genel tarih bilgini kullanma. "
                    "Kaynakta açıkça olmayan hiçbir ilişki üretme. Her ilişki için "
                    "kaynakta birebir bulunan evidence_quote ver. Bu çıktı sadece aday "
                    "çıkarımıdır; doğrulama kararı verme."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Aşağıdaki tarihî kaynak parçasından kişi, padişah, antlaşma, belge/ferman, "
                    "tarih, yer, kurum ve açık ilişkileri çıkar.\n\n"
                    f"KAYNAK:\n{source_text}"
                ),
            },
        ],
        schema=llm_relation_schema(),
        temperature=0.0,
    )

    normalized_source = normalized_evidence(source_text)
    valid_claims = []
    rejected_claims = []

    for claim in response.get("claims", []):
        evidence = normalized_evidence(claim.get("evidence_quote", ""))
        if evidence and evidence in normalized_source:
            valid_claims.append(claim)
        else:
            rejected_claims.append(claim)

    response["claims"] = valid_claims
    response["rejected_claims"] = rejected_claims
    response["derived_verified"] = False
    response["source_id"] = record["source_id"]
    response["chunk_id"] = record["chunk_id"]
    response["citation"] = record["citation"]
    response["created_at"] = utc_now()
    return response


def process_source(
    source: Dict[str, Any],
    state: Dict[str, Any],
    session: requests.Session,
    ingestor: HistoricalCorpusIngestor,
    deadline: datetime,
    llm: Any,
    max_llm_chunks_remaining: List[int],
) -> Dict[str, Any]:
    source_id = str(source["id"])
    result: Dict[str, Any] = {
        "source_id": source_id,
        "title": source.get("title", ""),
        "started_at": utc_now(),
        "status": "started",
        "records_ingested": 0,
        "llm_candidates": 0,
    }

    source_type = str(source.get("source_type", ""))
    if source_type in SKIP_SOURCE_TYPES:
        result.update(
            {
                "status": "skipped",
                "reason": f"Discovery/NLP source kept out of automatic production ingestion: {source_type}",
                "finished_at": utc_now(),
            }
        )
        return result

    try:
        if datetime.now(timezone.utc) >= deadline:
            result["status"] = "deadline_reached"
            return result

        path, download_meta = download_source(session, source)
        result["download"] = download_meta

        if path is None:
            result["status"] = "download_skipped"
            return result

        eligible, reason = source_auto_eligible(source, path)
        if not eligible:
            result.update({"status": "review_required", "reason": reason})
            append_jsonl(
                REJECTED_DIR / "manual_review_sources.jsonl",
                {
                    **source,
                    "local_path": str(path),
                    "reason": reason,
                    "created_at": utc_now(),
                },
            )
            return result

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            units, extraction_meta = extract_pdf(path)
        elif suffix == ".xlsx":
            units, extraction_meta = extract_xlsx(path)
        elif suffix in {".txt", ".json"}:
            units, extraction_meta = extract_text_file(path)
        else:
            raise RuntimeError(f"Unsupported file type after eligibility check: {suffix}")

        result["extraction"] = extraction_meta

        if not units:
            result["status"] = "review_required_no_text"
            append_jsonl(
                REJECTED_DIR / "ocr_required_sources.jsonl",
                {
                    **source,
                    "local_path": str(path),
                    "reason": "No usable digital text layer; OCR/manual processing required.",
                    "created_at": utc_now(),
                },
            )
            return result

        records = build_records(source, units)
        result["records_created"] = len(records)

        for record in records:
            if datetime.now(timezone.utc) >= deadline:
                result["status"] = "deadline_reached_partial"
                break

            ingestor.ingest_record(record)
            append_jsonl(INGESTED_PATH, record)
            result["records_ingested"] += 1

            if llm is not None and max_llm_chunks_remaining[0] > 0:
                try:
                    candidate = extract_relation_candidates(llm, record)
                    append_jsonl(CANDIDATES_PATH, candidate)
                    result["llm_candidates"] += 1
                except Exception as exc:
                    append_jsonl(
                        REJECTED_DIR / "llm_candidate_errors.jsonl",
                        {
                            "source_id": record["source_id"],
                            "chunk_id": record["chunk_id"],
                            "error": repr(exc),
                            "created_at": utc_now(),
                        },
                    )
                finally:
                    max_llm_chunks_remaining[0] -= 1

        if not str(result.get("status", "")).startswith("deadline"):
            result["status"] = "completed"

        return result

    except Exception as exc:
        logging.exception("Source failed: %s", source_id)
        result.update(
            {
                "status": "failed",
                "error": repr(exc),
            }
        )
        append_jsonl(
            REJECTED_DIR / "source_errors.jsonl",
            {
                "source_id": source_id,
                "title": source.get("title", ""),
                "url": clean_url(source.get("url", "")),
                "error": repr(exc),
                "created_at": utc_now(),
            },
        )
        return result
    finally:
        result["finished_at"] = utc_now()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Checkpointed overnight historical corpus builder."
    )
    parser.add_argument(
        "--hours",
        type=float,
        default=7.0,
        help="Maximum runtime in hours. Default: 7",
    )
    parser.add_argument(
        "--max-sources",
        type=int,
        default=0,
        help="Process at most N sources; 0 = all.",
    )
    parser.add_argument(
        "--llm-extract",
        action="store_true",
        help="Use local Ollama Qwen to create unverified structured relation candidates.",
    )
    parser.add_argument(
        "--max-llm-chunks",
        type=int,
        default=250,
        help="Maximum number of chunks sent to Qwen during this run.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocess sources already marked completed.",
    )
    args = parser.parse_args()

    setup_logging()

    if not MANIFEST_PATH.exists():
        raise SystemExit(f"Manifest not found: {MANIFEST_PATH}")

    manifest = load_json(MANIFEST_PATH, {})
    sources = manifest.get("sources", [])
    if not isinstance(sources, list) or not sources:
        raise SystemExit("Manifest contains no sources.")

    state = load_json(
        STATE_PATH,
        {
            "schema_version": "1.0",
            "created_at": utc_now(),
            "sources": {},
            "runs": [],
        },
    )
    state.setdefault("sources", {})
    state.setdefault("runs", [])

    started = datetime.now(timezone.utc)
    deadline = started + timedelta(hours=max(args.hours, 0.05))
    run_id = started.strftime("%Y%m%dT%H%M%SZ")

    logging.info("OVERNIGHT BUILDER START")
    logging.info("Manifest sources: %s", len(sources))
    logging.info("Deadline UTC: %s", deadline.isoformat())

    session = requests.Session()
    ingestor = HistoricalCorpusIngestor()
    llm = None

    if args.llm_extract:
        if OllamaProvider is None:
            raise SystemExit("OllamaProvider could not be imported.")
        llm = OllamaProvider()
        health = llm.health_check()
        if not health.get("reachable") or not health.get("model_available"):
            raise SystemExit(f"Ollama health check failed: {health}")
        logging.info("LLM candidate extraction enabled: %s", health.get("model"))

    counters = {
        "completed": 0,
        "failed": 0,
        "skipped": 0,
        "review_required": 0,
        "deadline": 0,
        "records_ingested": 0,
        "llm_candidates": 0,
    }
    processed_this_run = 0
    max_llm_chunks_remaining = [max(0, args.max_llm_chunks)]

    try:
        for source in sources:
            if datetime.now(timezone.utc) >= deadline:
                logging.info("Runtime deadline reached.")
                break

            if args.max_sources and processed_this_run >= args.max_sources:
                break

            source_id = str(source.get("id", "")).strip()
            if not source_id:
                continue

            previous = state["sources"].get(source_id, {})
            if previous.get("status") == "completed" and not args.force:
                logging.info("SKIP completed source: %s", source_id)
                continue

            logging.info("PROCESS source: %s | %s", source_id, source.get("title", ""))
            result = process_source(
                source=source,
                state=state,
                session=session,
                ingestor=ingestor,
                deadline=deadline,
                llm=llm,
                max_llm_chunks_remaining=max_llm_chunks_remaining,
            )

            processed_this_run += 1
            state["sources"][source_id] = result
            save_json(STATE_PATH, state)

            status = str(result.get("status", ""))
            if status == "completed":
                counters["completed"] += 1
            elif status == "failed":
                counters["failed"] += 1
            elif status == "skipped":
                counters["skipped"] += 1
            elif "review_required" in status:
                counters["review_required"] += 1
            elif "deadline" in status:
                counters["deadline"] += 1

            counters["records_ingested"] += int(result.get("records_ingested", 0))
            counters["llm_candidates"] += int(result.get("llm_candidates", 0))

        qdrant_count = ingestor.store.count()

        report = {
            "run_id": run_id,
            "started_at": started.isoformat(),
            "finished_at": utc_now(),
            "requested_hours": args.hours,
            "manifest_path": str(MANIFEST_PATH),
            "manifest_source_count": len(sources),
            "processed_this_run": processed_this_run,
            "counters": counters,
            "qdrant_total_points": qdrant_count,
            "llm_extraction_enabled": bool(args.llm_extract),
            "llm_chunks_remaining": max_llm_chunks_remaining[0],
            "state_path": str(STATE_PATH),
            "log_path": str(LOG_PATH),
            "ingested_records_path": str(INGESTED_PATH),
            "candidate_relations_path": str(CANDIDATES_PATH),
            "safety": {
                "derived_llm_candidates_auto_verified": False,
                "discovery_and_nlp_sources_auto_ingested": False,
                "pdf_pages_without_text_sent_to_review_queue": True,
            },
        }

        report_path = REPORT_DIR / f"overnight_corpus_report_{run_id}.json"
        save_json(report_path, report)

        state["runs"].append(
            {
                "run_id": run_id,
                "started_at": started.isoformat(),
                "finished_at": report["finished_at"],
                "report_path": str(report_path),
                "counters": counters,
                "qdrant_total_points": qdrant_count,
            }
        )
        save_json(STATE_PATH, state)

        print()
        print("=== OVERNIGHT CORPUS REPORT ===")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print()
        print("OVERNIGHT_CORPUS_BUILDER_GATE: PASS")
        return 0

    finally:
        try:
            ingestor.close()
        except Exception:
            pass
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
