from fastapi.testclient import TestClient

from app.db.database import Base
from app.main import app


def test_app_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_database_metadata_has_core_tables():
    expected = {
        "users",
        "documents",
        "pages",
        "processing_jobs",
        "image_variants",
        "audit_logs",
        "model_registry_entries",
        "ocr_results",
        "text_versions",
        "entities",
        "chat_sessions",
        "chat_messages",
        "citations",
        "export_records",
    }
    assert expected.issubset(set(Base.metadata.tables.keys()))


def test_database_metadata_has_traceability_columns():
    checks = {
        "documents": {"file_hash", "original_filename", "status", "access_level"},
        "processing_jobs": {"model_name", "model_version", "parameters", "confidence_score"},
        "model_registry_entries": {"name", "model_type", "version", "checksum", "config"},
        "ocr_results": {"page_id", "job_id", "model_id", "raw_text", "confidence_score"},
        "text_versions": {
            "document_id",
            "page_id",
            "ocr_result_id",
            "version_type",
            "text",
            "previous_text",
            "source_version_id",
        },
        "entities": {"document_id", "text_version_id", "entity_type", "value", "metadata_json"},
        "citations": {"message_id", "document_id", "page_id", "text_version_id", "locator"},
        "audit_logs": {"actor_id", "action", "object_type", "object_id", "old_value", "new_value", "created_at"},
    }

    for table_name, expected_columns in checks.items():
        actual_columns = set(Base.metadata.tables[table_name].columns.keys())
        assert expected_columns.issubset(actual_columns)
