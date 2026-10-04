import os
import sqlite3
import pytest
from pathlib import Path
import shutil
import sys

root = Path(r"c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT")
sys.path.insert(0, str(root / "backend"))
sys.path.insert(0, str(root))

from backend.migrations.annotation import schema_mig
from fastapi.testclient import TestClient

# Real main app
from app.main import app
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User

@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "annotation_test.db"
    conn = sqlite3.connect(fn)
    schema_mig.upgrade(conn)
    conn.close()
    return fn

@pytest.fixture
def db_conn(test_db_path, tmp_path):
    fn = tmp_path / "test.db"
    shutil.copy2(test_db_path, fn)
    conn = sqlite3.connect(fn, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()

@pytest.fixture
def override_db(db_conn):
    # Actually get_db uses SQLAlchemy session. We need to mock get_db to return an sqlite3 connection?
    # Wait, get_db yields a sqlalchemy Session. But my AnnotationService takes an sqlite3 connection!
    # Ah! In the real get_service, does it extract the raw connection from Session?
    pass

@pytest.fixture
def client(db_conn):
    def _override_get_db():
        # The real get_service expects db: Session but AnnotationService(db) uses it as raw?
        # Let's override get_service instead! Because AnnotationService expects sqlite3.Connection.
        from app.api.routes.annotation import get_service
        from app.services.annotation_service import AnnotationService
        return AnnotationService(db_conn)

    def _override_get_current_user():
        u = User()
        u.id = 1
        u.role = "admin"
        u.status = "active"
        return u

    def _override_get_export_service():
        from app.services.export_service import ExportService
        return ExportService(db_conn)

    from app.api.routes.annotation import get_service
    from app.api.routes.export import get_export_service
    app.dependency_overrides[get_service] = _override_get_db
    app.dependency_overrides[get_export_service] = _override_get_export_service
    app.dependency_overrides[get_current_user] = _override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
