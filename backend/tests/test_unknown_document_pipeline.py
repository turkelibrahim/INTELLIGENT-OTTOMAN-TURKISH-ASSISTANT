import shutil
import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.routes.document_analysis import get_document_analysis_pipeline
from app.core.security import get_current_user
from app.db.database import Base, get_db
from app.main import app
from app.models.user import User
from app.services.document_analysis_pipeline import DocumentAnalysisPipeline
from app.services.document_intelligence_service import DocIntelligenceEngine
from app.models.document import Document
from app.models.page import Page
from app.services.document_processing.ocr_engine import OCRLineResult, OCRPageResult, OttomanOCREngine
from app.services.document_processing.ner_extractor import NERExtractor
from app.services.document_processing.translator import Translator
from app.services.file_service import file_service
from app.services.historical_rag import HistoricalQdrantStore
from app.services.transliteration_service import TransliterationEngine


class EmptyHistoricalStore:
    def search(self, query: str, limit: int = 5, verified_only: bool = True):
        assert verified_only is True
        return []

    def close(self):
        return None


class MixedHistoricalStore:
    def search(self, query: str, limit: int = 5, verified_only: bool = True):
        assert verified_only is True
        return [
            {
                "id": 1,
                "source_id": "UNVERIFIED-REL",
                "title": "Derived relation candidate",
                "text": "This must not become evidence.",
                "verified": True,
                "derived_verified": False,
                "score": 999.0,
            },
            {
                "id": 2,
                "source_id": "SRC-VERIFIED",
                "title": "Verified source",
                "citation": "Verified source citation",
                "source_type": "corpus_chunk",
                "source_tier": "primary",
                "chunk_id": "chunk-2",
                "text": "Verified historical source text.",
                "verified": True,
                "score": 12.0,
            },
            {
                "id": 3,
                "source_id": "UNVERIFIED-SOURCE",
                "title": "Unverified source",
                "text": "This must not become evidence either.",
                "verified": False,
                "score": 998.0,
            },
        ]

    def close(self):
        return None


class StaticPreprocessor:
    def process(self, image):
        return image, {"profile": "static-test", "preprocessing_confidence": 1.0}


class StaticOCREngine:
    async def extract(self, image):
        lines = [
            OCRLineResult(
                text=text,
                confidence=0.91 + (index * 0.01),
                bbox=(10, 20 + index * 30, 180, 24),
                line_index=index,
                engine_name="static-ocr",
                engine_version="test",
                device="cpu",
                processing_time_ms=1.0,
            )
            for index, text in enumerate(["كتاب", "دولت", "مكتب", "تاريخ ١٣٢٧", "استانبول"])
        ]
        return OCRPageResult(
            lines=lines,
            engine_name="static-ocr",
            engine_version="test",
            device="cpu",
            page_confidence=0.93,
            processing_time_ms=5.0,
            image_hash="static",
            image_width=200,
            image_height=200,
            model_metadata={"actual_engine": "static-ocr", "fallback_used": False},
        )


class StaticTransliterationEngine:
    def transliterate_simple(self, text):
        return "\n".join(f"latin-{index + 1}" for index, _ in enumerate(text.splitlines()))


class CountingStaticTransliterationEngine:
    def __init__(self):
        self.calls = 0

    def transliterate_simple(self, text):
        self.calls += 1
        return "\n".join(f"latin-{index + 1}" for index, _ in enumerate(text.splitlines()))


class FailingTransliterationEngine:
    def transliterate_simple(self, text):
        raise RuntimeError("simulated transliteration provider outage")


class StaticIntelligence:
    def translate_to_modern_turkish(self, text):
        return "\n".join(f"modern-{index + 1}" for index, _ in enumerate(text.splitlines()))


class CountingStaticIntelligence:
    def __init__(self):
        self.calls = 0

    def translate_to_modern_turkish(self, text):
        self.calls += 1
        return "\n".join(f"modern-{index + 1}" for index, _ in enumerate(text.splitlines()))


class StructuredLineProvider:
    def __init__(self, fail_large_batches: bool = False):
        self.fail_large_batches = fail_large_batches
        self.calls = []

    def chat_json(self, messages, schema, *, temperature=0.1):
        user_content = messages[-1]["content"]
        marker = "Input lines JSON:\n"
        payload = json.loads(user_content.split(marker, 1)[1])
        self.calls.append([item["line_id"] for item in payload])
        if self.fail_large_batches and len(payload) > 10:
            raise RuntimeError("batch too large")
        return {
            "lines": [
                {
                    "line_id": item["line_id"],
                    "transliteration": f"structured-latin-{item['line_no']}",
                    "modern_turkish": f"structured-modern-{item['line_no']}",
                    "uncertain": False,
                }
                for item in payload
            ]
        }


class ProviderBackedFailingTransliterationEngine:
    def __init__(self, provider):
        self.provider = provider
        self.calls = 0

    def transliterate_simple(self, text):
        self.calls += 1
        raise RuntimeError("per-line transliteration should not be called")


class ProviderBackedFailingIntelligence:
    def __init__(self, provider):
        self.provider = provider
        self.calls = 0

    def translate_to_modern_turkish(self, text):
        self.calls += 1
        raise RuntimeError("per-line modernization should not be called")


def _test_user() -> User:
    return User(id=1, email="unknown-pipeline@example.com", username="unknownpipeline", password_hash="x", status="active")


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "unknown_pipeline.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    user = _test_user()
    db.add(user)
    db.commit()
    db.close()

    upload_dir = tmp_path / "uploads"
    for subdir in ["originals", "thumbnails", "processed"]:
        (upload_dir / subdir).mkdir(parents=True, exist_ok=True)
    old_upload_dir = file_service.upload_dir
    file_service.upload_dir = upload_dir

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    def override_current_user():
        return _test_user()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    file_service.upload_dir = old_upload_dir
    shutil.rmtree(upload_dir, ignore_errors=True)


def test_historical_evidence_filters_unverified_and_derived_relation_candidates():
    pipeline = DocumentAnalysisPipeline.__new__(DocumentAnalysisPipeline)
    pipeline.historical_store = MixedHistoricalStore()

    evidence = pipeline._retrieve_verified_historical_evidence("Osman Bursa")

    assert [item["source_id"] for item in evidence] == ["SRC-VERIFIED"]
    assert evidence[0]["chunk_id"] == "chunk-2"
    assert evidence[0]["retrieval_score"] == 12.0


def test_empty_historical_evidence_returns_structured_uncertainty():
    pipeline = DocumentAnalysisPipeline.__new__(DocumentAnalysisPipeline)
    pipeline.historical_store = EmptyHistoricalStore()

    evidence = pipeline._retrieve_verified_historical_evidence("no evidence query")
    analysis = pipeline._historical_analysis(evidence, {"institutions": []})

    assert evidence == []
    assert analysis["possible_period"] == "Tespit edilemedi"
    assert analysis["historical_context"] == "Tespit edilemedi"
    assert analysis["confidence"] == 0.0


@pytest.mark.asyncio
async def test_full_analysis_preserves_line_id_through_ocr_latin_modern_and_evidence(tmp_path):
    db_path = tmp_path / "traceability.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        user = _test_user()
        db.add(user)
        db.commit()

        image_path = tmp_path / "real_page.png"
        from PIL import Image

        Image.fromarray(np.full((100, 100, 3), 255, dtype=np.uint8)).save(image_path)
        document = Document(
            user_id=user.id,
            title="Traceability Doc",
            original_filename="traceability.png",
            file_hash="traceability-hash",
            file_size=image_path.stat().st_size,
            mime_type="image/png",
            page_count=1,
            status="uploaded",
            access_level="private",
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        page = Page(document_id=document.id, page_no=1, original_path=str(image_path), status="pending")
        db.add(page)
        db.commit()
        db.refresh(page)

        pipeline = DocumentAnalysisPipeline(
            preprocessor=StaticPreprocessor(),
            ocr_engine=StaticOCREngine(),
            transliteration_engine=StaticTransliterationEngine(),
            intelligence=StaticIntelligence(),
            historical_store=EmptyHistoricalStore(),
        )

        payload = await pipeline.analyze_document(document=document, pages=(item for item in [page]), db=db, user_id=user.id)

        ocr_lines = payload["ocr"]["lines"]
        latin_lines = payload["transliteration"]["lines"]
        modern_lines = payload["modern_turkish"]["lines"]
        evidence_lines = [
            item for item in payload["evidence"]["document_evidence"]
            if item.get("source") == "uploaded_document"
        ]

        assert len(ocr_lines) >= 5
        assert len(latin_lines) == len(ocr_lines)
        assert len(modern_lines) == len(ocr_lines)
        assert len(evidence_lines) >= 5

        ocr_ids = [line["line_id"] for line in ocr_lines[:5]]
        assert all(line_id.startswith("ocr_result:") for line_id in ocr_ids)
        assert [line["line_id"] for line in latin_lines[:5]] == ocr_ids
        assert [line["line_id"] for line in modern_lines[:5]] == ocr_ids
        assert [line["line_id"] for line in evidence_lines[:5]] == ocr_ids
        assert all(line.get("latin_text") for line in latin_lines[:5])
        assert all(line.get("modern_text") is not None for line in modern_lines[:5])
        assert all(line.get("bbox") for line in evidence_lines[:5])
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_line_transformations_fall_back_when_llm_transliteration_fails():
    pipeline = DocumentAnalysisPipeline.__new__(DocumentAnalysisPipeline)
    pipeline.transliteration_engine = FailingTransliterationEngine()
    pipeline.fallback_translator = Translator()
    pipeline.intelligence = StaticIntelligence()
    pipeline.ner_extractor = NERExtractor(enable_hf=False)

    lines = [
        {
            "line_id": "ocr_result:1",
            "page_id": 1,
            "page_no": 1,
            "line_no": 1,
            "ocr_result_id": 1,
            "ocr_text": "كتاب",
            "confidence": 0.73,
            "bbox": {"x": 1, "y": 2, "width": 3, "height": 4},
        }
    ]

    latin_lines, modern_lines, _ = pipeline._line_transformations(lines)

    assert latin_lines[0]["line_id"] == "ocr_result:1"
    assert latin_lines[0]["latin_text"]
    assert latin_lines[0]["method"].startswith("rule-based")
    assert modern_lines[0]["line_id"] == "ocr_result:1"
    assert "modern_text" in modern_lines[0]


def test_line_transformations_use_structured_batch_when_document_lines_misaligned():
    provider = StructuredLineProvider()
    transliteration = ProviderBackedFailingTransliterationEngine(provider)
    intelligence = ProviderBackedFailingIntelligence(provider)
    pipeline = DocumentAnalysisPipeline.__new__(DocumentAnalysisPipeline)
    pipeline.transliteration_engine = transliteration
    pipeline.fallback_translator = Translator()
    pipeline.intelligence = intelligence
    pipeline.ner_extractor = NERExtractor(enable_hf=False)

    lines = [
        {
            "line_id": f"p1_l{index}",
            "page_id": 1,
            "page_no": 1,
            "line_no": index,
            "ocr_text": f"ottoman-{index}",
            "confidence": 0.8,
            "bbox": {"x": 1, "y": index, "width": 3, "height": 4},
        }
        for index in range(1, 4)
    ]

    latin_lines, modern_lines, _ = pipeline._line_transformations(
        lines,
        latin_text="collapsed latin",
        modern_text="collapsed modern",
    )

    assert len(provider.calls) == 1
    assert transliteration.calls == 0
    assert intelligence.calls == 0
    assert [line["line_id"] for line in latin_lines] == ["p1_l1", "p1_l2", "p1_l3"]
    assert all(line["method"] == "ollama-structured-batch" for line in latin_lines)
    assert all(line["provider"] == "ollama-structured-batch" for line in modern_lines)
    assert [line["latin_text"] for line in latin_lines] == [
        "structured-latin-1",
        "structured-latin-2",
        "structured-latin-3",
    ]


def test_structured_batch_splits_failed_large_batch_without_reprocessing_successes():
    provider = StructuredLineProvider(fail_large_batches=True)
    transliteration = ProviderBackedFailingTransliterationEngine(provider)
    intelligence = ProviderBackedFailingIntelligence(provider)
    pipeline = DocumentAnalysisPipeline.__new__(DocumentAnalysisPipeline)
    pipeline.transliteration_engine = transliteration
    pipeline.fallback_translator = Translator()
    pipeline.intelligence = intelligence
    pipeline.ner_extractor = NERExtractor(enable_hf=False)

    lines = [
        {
            "line_id": f"p1_l{index}",
            "page_id": 1,
            "page_no": 1,
            "line_no": index,
            "ocr_text": f"ottoman-{index}",
            "confidence": 0.8,
            "bbox": {"x": 1, "y": index, "width": 3, "height": 4},
        }
        for index in range(1, 13)
    ]

    latin_lines, modern_lines, _ = pipeline._line_transformations(
        lines,
        latin_text="collapsed latin",
        modern_text="collapsed modern",
    )

    assert len(provider.calls) == 4
    assert len(provider.calls[0]) == 12
    assert len(provider.calls[1]) == 12
    assert len(provider.calls[2]) == 10
    assert len(provider.calls[3]) == 2
    assert transliteration.calls == 0
    assert intelligence.calls == 0
    assert len(latin_lines) == 12
    assert len(modern_lines) == 12
    assert all(line["method"] == "ollama-structured-batch" for line in latin_lines)


@pytest.mark.asyncio
async def test_full_analysis_reuses_document_level_line_transformations_when_aligned(tmp_path):
    image_path = tmp_path / "page.png"
    from PIL import Image

    Image.fromarray(np.full((100, 100, 3), 255, dtype=np.uint8)).save(image_path)
    document = Document(
        id=99,
        user_id=1,
        title="Reuse Doc",
        original_filename="reuse.png",
        file_hash="reuse-hash",
        file_size=image_path.stat().st_size,
        mime_type="image/png",
        page_count=1,
        status="uploaded",
        access_level="private",
    )
    page = Page(id=100, document_id=document.id, page_no=1, original_path=str(image_path), status="pending")
    transliteration = CountingStaticTransliterationEngine()
    intelligence = CountingStaticIntelligence()
    pipeline = DocumentAnalysisPipeline(
        preprocessor=StaticPreprocessor(),
        ocr_engine=StaticOCREngine(),
        transliteration_engine=transliteration,
        intelligence=intelligence,
        historical_store=EmptyHistoricalStore(),
    )

    payload = await pipeline.analyze_document(document=document, pages=[page], db=None, user_id=1)

    assert transliteration.calls == 1
    assert intelligence.calls == 1
    assert len(payload["ocr"]["lines"]) == len(payload["transliteration"]["lines"])
    assert len(payload["ocr"]["lines"]) == len(payload["modern_turkish"]["lines"])
    assert all(line["method"] == "document-level-line-reuse" for line in payload["transliteration"]["lines"])
    assert all(line["provider"] == "document-level-line-reuse" for line in payload["modern_turkish"]["lines"])
    assert [line["line_id"] for line in payload["ocr"]["lines"]] == [
        line["line_id"] for line in payload["transliteration"]["lines"]
    ]
    assert [line["line_id"] for line in payload["ocr"]["lines"]] == [
        line["line_id"] for line in payload["modern_turkish"]["lines"]
    ]


@pytest.mark.integration
def test_analyze_full_endpoint_with_real_upload_real_ocr_ollama_and_qdrant(client):
    sample = Path("uploads/originals/9/pages/page_1.png")
    if not sample.exists():
        pytest.skip("Real Ottoman sample page is not available.")

    ocr_engine = OttomanOCREngine(
        enable_kraken=False,
        enable_easyocr=True,
        enable_trocr=False,
        enable_tesseract=False,
        gpu=False,
    )
    pipeline = DocumentAnalysisPipeline(
        ocr_engine=ocr_engine,
        transliteration_engine=TransliterationEngine(use_mock=False),
        intelligence=DocIntelligenceEngine(use_mock=False),
        historical_store=HistoricalQdrantStore(),
    )

    app.dependency_overrides[get_document_analysis_pipeline] = lambda: pipeline
    try:
        with sample.open("rb") as handle:
            response = client.post(
                "/api/v1/document/analyze-full",
                files={"file": ("real_ottoman_page.png", handle, "image/png")},
                data={"title": "Unknown Ottoman Pipeline Smoke"},
            )
    finally:
        pipeline.close()
        app.dependency_overrides.pop(get_document_analysis_pipeline, None)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["document"]["filename"] == "real_ottoman_page.png"
    assert payload["document"]["language"] == "Ottoman Turkish"
    assert payload["ocr"]["ottoman_text"].strip()
    assert payload["ocr"]["engine"] in {"easyocr", "kraken"}
    assert "[FALLBACK_OCR]" not in payload["ocr"]["ottoman_text"]
    assert "Ornek Osmanlica" not in payload["ocr"]["ottoman_text"]
    assert payload["transliteration"]["latin_text"].strip()
    assert payload["modern_turkish"]["text"].strip()
    assert len(payload["ocr"]["lines"]) >= 5
    assert len(payload["transliteration"]["lines"]) == len(payload["ocr"]["lines"])
    assert len(payload["modern_turkish"]["lines"]) == len(payload["ocr"]["lines"])
    real_line_ids = [line["line_id"] for line in payload["ocr"]["lines"][:5]]
    assert [line["line_id"] for line in payload["transliteration"]["lines"][:5]] == real_line_ids
    assert [line["line_id"] for line in payload["modern_turkish"]["lines"][:5]] == real_line_ids
    assert all(line.get("latin_text") for line in payload["transliteration"]["lines"][:5])
    assert all("modern_text" in line for line in payload["modern_turkish"]["lines"][:5])
    document_evidence = payload["evidence"]["document_evidence"]
    assert [item["line_id"] for item in document_evidence[:5]] == real_line_ids
    assert all(item.get("bbox") for item in document_evidence[:5])
    assert set(payload["entities"]) == {"persons", "places", "institutions", "dates", "titles", "document_marks"}
    assert "document_evidence" in payload["evidence"]
    assert "historical_external_evidence" in payload["evidence"]
    assert "model_inference" in payload["evidence"]
    for item in payload["evidence"]["historical_external_evidence"]:
        assert item["verified"] is True
        assert item["source_id"]
        assert item["chunk_id"]
        assert "retrieval_score" in item
        assert item["evidence_text"] is not None
    assert payload["confidence"]["combined_provisional"] is True
