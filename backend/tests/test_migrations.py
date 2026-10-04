from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_initial_migration_upgrade_and_downgrade(tmp_path):
    db_path = tmp_path / "migration_gate.db"
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")

    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    tables = set(inspect(engine).get_table_names())
    assert {
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
        "alembic_version",
    }.issubset(tables)
    engine.dispose()

    command.downgrade(config, "base")
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    tables_after_rollback = set(inspect(engine).get_table_names())
    assert tables_after_rollback == {"alembic_version"}
    engine.dispose()
