import argparse
import asyncio
import cProfile
import csv
import io
import json
import os
import pstats
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
OUT = ROOT / "evidence" / "performance_audit"
sys.path.insert(0, str(BACKEND))

from app.db.database import Base
from app.models.document import Document
from app.models.page import Page
from app.models.processing_outputs import OCRResult, TextVersion
from app.models.user import User
from app.services.ai.ollama_provider import OllamaProvider
from app.services.chat.rag_service import RAGService
from app.services.document_analysis_pipeline import DocumentAnalysisPipeline
from app.services.document_intelligence_service import DocIntelligenceEngine
from app.services.document_processing.ner_extractor import NERExtractor
from app.services.document_processing.ocr_engine import OCRLineResult, OCRPageResult
from app.services.document_processing.preprocessor import ImagePreprocessor
from app.services.document_processing.translator import Translator
from app.services.historical_rag import HistoricalQdrantStore
from app.services.image_io import read_image_unicode_safe
from app.services.transliteration_service import TransliterationEngine


OTTOMAN_LINES = [
    "كتاب دولت مكتب تاريخ ١٣٢٧ استانبول",
    "حواله ياپدى قارداش اوغلى اق تيمورى",
    "ياپدى گوردیكم جنگله الماز قريشسنده",
    "فرمان همايون و اعلان عمومى",
    "مجلس مخصوص قرارى موجبince",
]


def write_json(name: str, payload: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    index = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[index]


def process_memory_mb() -> float | None:
    try:
        import psutil

        return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    except Exception:
        if os.name != "nt":
            return None
        try:
            import ctypes
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            ok = ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
            if not ok:
                return None
            return float(counters.WorkingSetSize) / 1024 / 1024
        except Exception:
            return None


def cuda_memory() -> dict[str, Any]:
    try:
        import torch

        if not torch.cuda.is_available():
            return {"available": False}
        return {
            "available": True,
            "allocated": int(torch.cuda.memory_allocated(0)),
            "reserved": int(torch.cuda.memory_reserved(0)),
        }
    except Exception as exc:
        return {"available": False, "error": repr(exc)}


def nvidia_sample() -> dict[str, Any]:
    cmd = [
        "nvidia-smi",
        "--query-gpu=timestamp,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
        "--format=csv,noheader,nounits",
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return {"returncode": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as exc:
        return {"error": repr(exc)}


def write_resource_csv(name: str, rows: list[dict[str, Any]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fields = ["timestamp", "label", "process_rss_mb", "cuda_allocated", "cuda_reserved", "nvidia"]
    with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def resource_row(label: str) -> dict[str, Any]:
    cm = cuda_memory()
    return {
        "timestamp": time.time(),
        "label": label,
        "process_rss_mb": process_memory_mb(),
        "cuda_allocated": cm.get("allocated"),
        "cuda_reserved": cm.get("reserved"),
        "nvidia": json.dumps(nvidia_sample(), ensure_ascii=False),
    }


class StaticPreprocessor:
    def process(self, image):
        return image, {"profile": "static-benchmark", "preprocessing_confidence": 1.0, "warnings": []}


class StaticOCREngine:
    def __init__(self, line_count: int):
        self.line_count = line_count

    async def extract(self, image):
        lines = []
        for index in range(self.line_count):
            text = OTTOMAN_LINES[index % len(OTTOMAN_LINES)]
            lines.append(
                OCRLineResult(
                    text=text,
                    confidence=0.91,
                    bbox=(10, 20 + index * 18, 320, 16),
                    line_index=index,
                    engine_name="static-production-shape",
                    engine_version="benchmark",
                    device="cpu",
                    processing_time_ms=0.2,
                )
            )
        return OCRPageResult(
            lines=lines,
            engine_name="static-production-shape",
            engine_version="benchmark",
            device="cpu",
            page_confidence=0.91 if lines else 0.0,
            processing_time_ms=1.0,
            image_hash="benchmark",
            image_width=512,
            image_height=512,
            model_metadata={"actual_engine": "static-production-shape", "fallback_used": False},
        )


class EmptyHistoricalStore:
    def __init__(self):
        self.calls = []

    def search(self, query: str, limit: int = 5, verified_only: bool = True):
        start = time.perf_counter()
        self.calls.append(
            {
                "query_chars": len(query or ""),
                "limit": limit,
                "verified_only": verified_only,
                "duration_ms": (time.perf_counter() - start) * 1000,
            }
        )
        return []

    def close(self):
        return None


class DummyVisualExtractor:
    def extract(self, image_path: str):
        return {"entities": []}


class CountingProvider:
    def __init__(self, *, real: bool = False, fail: bool = False, model: str = "qwen3.5:4b"):
        self.real = real
        self.fail = fail
        self.model = model
        self.calls: list[dict[str, Any]] = []
        self._provider = OllamaProvider(model=model, timeout_seconds=180) if real else None

    def chat(self, messages, *, schema=None, temperature=0.1, think=False):
        if self.fail:
            raise RuntimeError("simulated provider outage")
        text_in = "\n".join(message.get("content", "") for message in messages)
        category = "transliteration" if "transliteration" in text_in.lower() else "modernization"
        start = time.perf_counter()
        if self.real:
            result = self._provider.chat(messages, schema=schema, temperature=temperature, think=think)
        else:
            source = self._extract_source(text_in)
            lines = source.splitlines() or [source]
            prefix = "latin" if category == "transliteration" else "modern"
            result = "\n".join(f"{prefix}-{index + 1}: {line}" for index, line in enumerate(lines))
        elapsed = (time.perf_counter() - start) * 1000
        self.calls.append(
            {
                "category": category,
                "duration_ms": elapsed,
                "input_chars": len(text_in),
                "output_chars": len(result),
                "input_tokens_approx": round(len(text_in) / 4.0, 2),
                "output_tokens_approx": round(len(result) / 4.0, 2),
                "real": self.real,
            }
        )
        return result

    def chat_json(self, messages, schema, *, temperature=0.1):
        raw = self.chat(messages, schema=schema, temperature=temperature, think=False)
        return {"PERSON": [], "LOCATION": [], "DATE": [], "ORGANIZATION": []}

    def health_check(self):
        if self.fail:
            raise RuntimeError("simulated provider outage")
        if self.real and self._provider:
            return self._provider.health_check()
        return {"provider": "counting", "reachable": True, "model_available": True}

    def _extract_source(self, prompt: str) -> str:
        markers = ["KAYNAK METİN:", "KAYNAK METÄ°N:", "Metin:"]
        source = prompt
        for marker in markers:
            if marker in source:
                source = source.split(marker)[-1]
        for marker in ["MODERN TÜRKÇE:", "MODERN TÃœRKÃ‡E:", "Sade Türkçe Transliterasyon:", "Sade TÃ¼rkÃ§e Transliterasyon:"]:
            if marker in source:
                source = source.split(marker)[0]
        return source.strip()


def make_pipeline(line_count: int, *, real_llm: bool = False, fail_llm: bool = False) -> tuple[DocumentAnalysisPipeline, CountingProvider]:
    provider = CountingProvider(real=real_llm, fail=fail_llm)
    pipeline = DocumentAnalysisPipeline(
        preprocessor=StaticPreprocessor(),
        ocr_engine=StaticOCREngine(line_count),
        transliteration_engine=TransliterationEngine(provider=provider),
        intelligence=DocIntelligenceEngine(provider=provider),
        fallback_translator=Translator(),
        ner_extractor=NERExtractor(enable_hf=False),
        historical_store=EmptyHistoricalStore(),
    )
    pipeline.visual_extractor = DummyVisualExtractor()
    return pipeline, provider


async def run_pipeline_once(line_count: int, *, real_llm: bool = False, fail_llm: bool = False) -> dict[str, Any]:
    pipeline, provider = make_pipeline(line_count, real_llm=real_llm, fail_llm=fail_llm)
    document = Document(
        id=9000 + line_count,
        user_id=1,
        title="Performance Audit Document",
        original_filename="performance_audit.png",
        file_hash="benchmark",
        file_size=1,
        mime_type="image/png",
        page_count=1,
        status="uploaded",
        access_level="private",
    )
    page = Page(id=9100 + line_count, document_id=document.id, page_no=1, original_path=str(sample_image()), status="pending")
    start = time.perf_counter()
    result = await pipeline.analyze_document(document=document, pages=[page], db=None, user_id=1)
    total_ms = (time.perf_counter() - start) * 1000
    calls = provider.calls
    return {
        "line_count": line_count,
        "real_llm": real_llm,
        "total_ms": total_ms,
        "ocr_lines": len(result["ocr"]["lines"]),
        "latin_lines": len(result["transliteration"]["lines"]),
        "modern_lines": len(result["modern_turkish"]["lines"]),
        "llm_calls": len(calls),
        "llm_calls_by_category": {
            "transliteration": sum(1 for call in calls if call["category"] == "transliteration"),
            "modernization": sum(1 for call in calls if call["category"] == "modernization"),
        },
        "input_tokens_approx": round(sum(call["input_tokens_approx"] for call in calls), 2),
        "output_tokens_approx": round(sum(call["output_tokens_approx"] for call in calls), 2),
        "llm_duration_ms": round(sum(call["duration_ms"] for call in calls), 2),
        "calls": calls,
    }


async def run_suite(phase: str, *, real_llm_small: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    resource_rows = [resource_row(f"{phase}_start")]
    runs: dict[str, Any] = {}
    for count in [1, 5, 10]:
        durations = []
        for index in range(count):
            result = await run_pipeline_once(5, real_llm=False)
            durations.append(result["total_ms"])
        runs[f"{count}_sequential_documents"] = {
            "durations_ms": durations,
            "total_ms": sum(durations),
            "p50_ms": percentile(durations, 50),
            "p95_ms": percentile(durations, 95),
            "p99_ms": percentile(durations, 99),
        }
    for concurrency in [2, 4]:
        start = time.perf_counter()
        results = await asyncio.gather(*[run_pipeline_once(5, real_llm=False) for _ in range(concurrency)])
        runs[f"{concurrency}_concurrent_documents"] = {
            "wall_ms": (time.perf_counter() - start) * 1000,
            "per_request_ms": [item["total_ms"] for item in results],
        }
    call_graph_10 = await run_pipeline_once(10, real_llm=False)
    call_graph_30 = await run_pipeline_once(30, real_llm=False)
    call_graph_500 = await run_pipeline_once(500, real_llm=False)
    real_small = await run_pipeline_once(3, real_llm=True) if real_llm_small else None
    resource_rows.append(resource_row(f"{phase}_end"))
    write_resource_csv(f"resource_usage_{phase}.csv", resource_rows)
    benchmark = {
        "phase": phase,
        "synthetic_orchestration_note": "Uses production DocumentAnalysisPipeline with static OCR image-shape output and counting provider; real OCR and real Ollama are profiled separately to avoid destructive/long-running bulk inference.",
        "runs": runs,
        "call_graph_samples": {
            "10_lines": call_graph_10,
            "30_lines": call_graph_30,
            "500_lines": {
                key: value for key, value in call_graph_500.items() if key != "calls"
            },
        },
        "real_llm_3_line_sample": real_small,
    }
    call_graph = {
        "phase": phase,
        "formula_observed": "llm_calls = 2 + (2 * line_count) before optimization unless document-level line reuse is available after optimization.",
        "samples": benchmark["call_graph_samples"],
        "real_llm_3_line_sample": real_small,
    }
    return benchmark, call_graph


def sample_image() -> Path:
    candidates = [
        ROOT / "backend" / "uploads" / "originals" / "82" / "82_191f0506.jpg",
        ROOT / "backend" / "uploads" / "originals" / "9" / "pages" / "page_1.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    fallback = OUT / "synthetic_sample.png"
    fallback.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(fallback), np.full((256, 256, 3), 255, dtype=np.uint8))
    return fallback


def profile_preprocessing(phase: str) -> dict[str, Any]:
    path = sample_image()
    timings: dict[str, float] = {}
    t0 = time.perf_counter()
    image = read_image_unicode_safe(path)
    timings["image_decode_ms"] = (time.perf_counter() - t0) * 1000
    pre = ImagePreprocessor()
    original_gray = None

    t = time.perf_counter()
    original_gray = pre._to_gray(image)
    timings["grayscale_reference_ms"] = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    deskewed, angle = pre.correct_skew_with_angle(image)
    timings["deskew_ms"] = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    current = pre._to_gray(deskewed)
    timings["grayscale_ms"] = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    denoised = cv2.fastNlMeansDenoising(current, h=10, searchWindowSize=21, templateWindowSize=7)
    timings["denoise_ms"] = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35))
    background = cv2.morphologyEx(denoised, cv2.MORPH_DILATE, kernel)
    normalized = cv2.divide(denoised, background, scale=255)
    timings["background_normalization_ms"] = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(normalized)
    timings["clahe_ms"] = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    _, thresholded = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    timings["threshold_ms"] = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    pre.select_ocr_optimized_image(original=image, pipeline_candidate=thresholded)
    timings["ocr_safe_selection_ms"] = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    pre.generate_clean_digital_copy(image)
    timings["clean_digital_copy_ms"] = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    pre.process(image)
    timings["preprocessing_total_ms"] = (time.perf_counter() - t) * 1000

    return {
        "phase": phase,
        "sample": str(path),
        "shape": list(image.shape),
        "deskew_angle": angle,
        "timings_ms": {key: round(value, 3) for key, value in timings.items()},
    }


def profile_rag(phase: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        store = HistoricalQdrantStore()
        init_ms = (time.perf_counter() - start) * 1000
        q0 = time.perf_counter()
        results = store.search("Istanbul devlet ilan", limit=5, verified_only=True)
        search_ms = (time.perf_counter() - q0) * 1000
        status = "ok"
        error = None
    except Exception as exc:
        init_ms = (time.perf_counter() - start) * 1000
        search_ms = 0.0
        results = []
        status = "error"
        error = repr(exc)
    return {
        "phase": phase,
        "path": os.getenv("HISTORICAL_QDRANT_PATH", r"C:\ottoman_ai_data\qdrant"),
        "status": status,
        "error": error,
        "init_ms": round(init_ms, 3),
        "qdrant_search_ms": round(search_ms, 3),
        "result_count": len(results),
        "rrf_present_in_production": False,
        "collection_dimension_expected": 1024,
    }


@contextmanager
def patched_vector_store():
    import app.services.chat.embeddings as embeddings

    original = embeddings.VectorStoreService

    class DummyVectorStore:
        collection = None
        embedding_model = None

        def similarity_search(self, *args, **kwargs):
            return []

    embeddings.VectorStoreService = DummyVectorStore
    try:
        yield
    finally:
        embeddings.VectorStoreService = original


def database_profile(phase: str) -> dict[str, Any]:
    profiles = {}
    for line_count in [100, 500, 1000]:
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        query_stats = {"count": 0, "total_ms": 0.0}

        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.perf_counter()

        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            query_stats["count"] += 1
            query_stats["total_ms"] += (time.perf_counter() - context._query_start_time) * 1000

        db = SessionLocal()
        user = User(id=1, email="perf@example.com", username="perf", password_hash="x", status="active")
        doc = Document(id=1, user_id=1, title="Perf", original_filename="perf.png", file_hash="h", file_size=1, mime_type="image/png", page_count=1, status="ready", access_level="private")
        page = Page(id=1, document_id=1, page_no=1, original_path=str(sample_image()), status="ocr")
        db.add_all([user, doc, page])
        for index in range(line_count):
            db.add(OCRResult(page_id=1, line_no=index + 1, bbox={"x": 0, "y": index, "width": 1, "height": 1}, raw_text=f"satir devlet ilan {index}", confidence_score=0.9))
        db.add(TextVersion(document_id=1, user_id=1, version_type="modernization_faithful", text="devlet ilan " * max(1, line_count // 10), confidence_score=0.8))
        db.commit()
        svc = RAGService(db)
        with patched_vector_store():
            start = time.perf_counter()
            chunks = svc._retrieve_chunks(1, "devlet")
            elapsed = (time.perf_counter() - start) * 1000
        profiles[str(line_count)] = {
            "line_count": line_count,
            "elapsed_ms": round(elapsed, 3),
            "chunks": len(chunks),
            "sql_query_count": query_stats["count"],
            "sql_total_ms": round(query_stats["total_ms"], 3),
            "complexity_observed": "linear scan over OCRResult and TextVersion rows",
        }
        db.close()
        engine.dispose()
    return {"phase": phase, "sql_fallback_profiles": profiles}


def edge_cases() -> dict[str, Any]:
    results: dict[str, Any] = {}

    async def empty_pages():
        pipeline, _ = make_pipeline(0, real_llm=False)
        doc = Document(id=1, user_id=1, title="Empty", original_filename="empty.png", file_hash="h", file_size=0, mime_type="image/png", page_count=0, status="uploaded", access_level="private")
        return await pipeline.analyze_document(document=doc, pages=[], db=None, user_id=1)

    try:
        payload = asyncio.run(empty_pages())
        results["empty_page_set"] = {"status": "controlled", "ocr_text_len": len(payload["ocr"]["ottoman_text"]), "warnings": payload.get("warnings", [])}
    except Exception as exc:
        results["empty_page_set"] = {"status": "error", "error": repr(exc)}

    try:
        payload = asyncio.run(run_pipeline_once(1, fail_llm=True))
        results["ollama_unavailable_simulated"] = {"status": "controlled_fallback", "llm_calls": payload["llm_calls"], "total_ms": payload["total_ms"]}
    except Exception as exc:
        results["ollama_unavailable_simulated"] = {"status": "error", "error": repr(exc)}

    class BrokenStore:
        def search(self, *args, **kwargs):
            raise RuntimeError("simulated qdrant unavailable")

    try:
        pipeline = DocumentAnalysisPipeline.__new__(DocumentAnalysisPipeline)
        pipeline.historical_store = BrokenStore()
        pipeline._retrieve_verified_historical_evidence("query")
        results["qdrant_unavailable_document_pipeline"] = {"status": "unexpected_success"}
    except Exception as exc:
        results["qdrant_unavailable_document_pipeline"] = {
            "status": "explicit_error_not_silent_success",
            "error": repr(exc),
        }

    cm = cuda_memory()
    results["gpu_unavailable_observation"] = {
        "status": "observed" if cm.get("available") else "gpu_unavailable_or_no_torch_cuda",
        "cuda": cm,
    }
    return results


def memory_leak_profile(phase: str) -> dict[str, Any]:
    rows = []
    tracemalloc.start()
    for index in range(20):
        asyncio.run(run_pipeline_once(3, real_llm=False))
        cm = cuda_memory()
        current, peak = tracemalloc.get_traced_memory()
        rows.append(
            {
                "iteration": index + 1,
                "process_rss_mb": process_memory_mb(),
                "tracemalloc_current_mb": round(current / 1024 / 1024, 3),
                "tracemalloc_peak_mb": round(peak / 1024 / 1024, 3),
                "cuda_allocated": cm.get("allocated"),
                "cuda_reserved": cm.get("reserved"),
            }
        )
    tracemalloc.stop()
    return {"phase": phase, "iterations": rows}


def run_cprofile(phase: str) -> str:
    profile = cProfile.Profile()
    profile.enable()
    asyncio.run(run_pipeline_once(10, real_llm=False))
    profile.disable()
    stream = io.StringIO()
    stats = pstats.Stats(profile, stream=stream).sort_stats("cumulative")
    stats.print_stats(40)
    output = stream.getvalue()
    (OUT / f"python_profile_{phase}.txt").write_text(output, encoding="utf-8")
    return output


def one_drive_filesystem_profile() -> dict[str, Any]:
    rows = {}
    sample = sample_image()
    data = sample.read_bytes()
    temp_dir = OUT / "tmp_io"
    temp_dir.mkdir(parents=True, exist_ok=True)
    for size_name, payload in {"sample": data, "one_mb": data * max(1, (1024 * 1024 // max(len(data), 1)))}.items():
        target = temp_dir / f"{size_name}.bin"
        t0 = time.perf_counter()
        target.write_bytes(payload)
        write_ms = (time.perf_counter() - t0) * 1000
        t1 = time.perf_counter()
        _ = target.read_bytes()
        read_ms = (time.perf_counter() - t1) * 1000
        rows[size_name] = {"bytes": len(payload), "write_ms": round(write_ms, 3), "read_ms": round(read_ms, 3)}
    return {
        "project_under_onedrive": "OneDrive" in str(ROOT),
        "root": str(ROOT),
        "io_samples": rows,
        "onedrive_process_note": "See environment.json onedrive_processes for CPU/RSS at snapshot time.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["before", "after"], required=True)
    parser.add_argument("--real-llm-small", action="store_true")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    benchmark, call_graph = asyncio.run(run_suite(args.phase, real_llm_small=args.real_llm_small))
    stage = profile_preprocessing(args.phase)
    rag = profile_rag(args.phase)
    db = database_profile(args.phase)
    memory = memory_leak_profile(args.phase)
    filesystem = one_drive_filesystem_profile()
    run_cprofile(args.phase)

    write_json(f"{'baseline' if args.phase == 'before' else 'optimized'}.json", benchmark)
    write_json(f"llm_call_graph_{args.phase}.json", call_graph)
    write_json(f"stage_timings_{args.phase}.json", {"stage_timings": stage, "rag_profile": rag, "filesystem": filesystem})
    write_json(f"ocr_profile_{args.phase}.json", {"real_ocr_smoke_file": f"real_ocr_smoke_{args.phase}.txt", "note": "Real OCR smoke is run separately because Kraken cold start is expensive."})
    write_json(f"database_profile_{args.phase}.json", db)
    write_json(f"memory_profile_{args.phase}.json", memory)
    if args.phase == "before":
        write_json("edge_case_results.json", edge_cases())


if __name__ == "__main__":
    main()
