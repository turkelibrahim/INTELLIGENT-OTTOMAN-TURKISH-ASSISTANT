import app.models  # noqa: F401
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.processing_outputs import ModelRegistryEntry
from app.services.document_processing.confidence import (
    ConfidenceManager,
    ModelRegistryService,
    build_operation_metadata,
)
from app.services.document_processing.ner_extractor import NERExtractor
from app.services.document_processing.ocr_engine import OCREngine
from app.services.document_processing.translator import Translator


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "confidence.db"
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = testing_session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_confidence_policy_labels_and_clamps_scores():
    manager = ConfidenceManager()

    assert manager.assess(1.5).score == 1.0
    assert manager.assess(0.9).label == "high"
    assert manager.assess(0.7).label == "medium"
    assert manager.assess(0.2).label == "low"
    assert manager.assess(None).label == "unknown"
    assert manager.assess(0.92, fallback=True).label == "fallback"


def test_model_registry_service_is_idempotent(db_session):
    service = ModelRegistryService()
    descriptor = service.descriptor_for_operation(
        "transliteration",
        {"method_version": Translator.METHOD_VERSION},
    )

    first = service.ensure_entry(db_session, descriptor)
    second = service.ensure_entry(db_session, descriptor)

    assert first.id == second.id
    assert db_session.query(ModelRegistryEntry).count() == 1
    assert first.model_type == "transliteration"
    assert first.config["registry_version"] == service.REGISTRY_VERSION


def test_ai_operations_have_model_and_confidence_metadata():
    ocr_engine = OCREngine(
        enable_easyocr=True,
        enable_trocr=False,
        enable_tesseract=False,
        gpu=False,
    )
    ocr_metadata = ocr_engine.model_metadata()
    transliteration = Translator().transliterate_line("كتاب")
    modernization = Translator().modernize("ktab", mode="faithful")
    ner = NERExtractor().extract("Ahmed Pasa 1327")

    outputs = [
        build_operation_metadata(
            "ocr",
            confidence_score=0.0,
            model_metadata=ocr_metadata,
            fallback=False,
        ),
        build_operation_metadata(
            "transliteration",
            confidence_score=transliteration.confidence,
            model_metadata={"method_version": transliteration.method_version},
        ),
        build_operation_metadata(
            "modernization",
            confidence_score=modernization.confidence,
            model_metadata={
                "provider": modernization.provider,
                "prompt_version": modernization.prompt_version,
                "mode": modernization.mode,
            },
        ),
        build_operation_metadata(
            "ner",
            confidence_score=ner["confidence_score"],
            model_metadata={"method_version": ner["method_version"]},
        ),
    ]

    assert {item["operation"] for item in outputs} == {"ocr", "transliteration", "modernization", "ner"}
    assert all("score" in item["confidence"] for item in outputs)
    assert all(item["confidence"]["policy_version"] == ConfidenceManager.POLICY_VERSION for item in outputs)
    assert all(item["model"]["version"] for item in outputs)


def test_unsupported_operation_is_explicit_error():
    with pytest.raises(ValueError, match="Unsupported operation"):
        ModelRegistryService().descriptor_for_operation("rag", {})
