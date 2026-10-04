import pytest
from fastapi.testclient import TestClient
from app.models.user import User
from app.models.ground_truth import GroundTruthStatus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.main import app

@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "ground_truth_test.db"
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

@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_ground_truth_api_auth_and_flow(client: TestClient, db_session):
    # 1. Create two users
    user_a = User(email="usera@example.com", username="usera", password_hash="pw", status="active")
    user_b = User(email="userb@example.com", username="userb", password_hash="pw", status="active")
    db_session.add_all([user_a, user_b])
    db_session.commit()
    db_session.refresh(user_a)
    db_session.refresh(user_b)
    
    # Mocking dependencies for auth
    from app.core.security import get_current_user
    from app.main import app

    def override_get_current_user_a():
        return user_a
        
    def override_get_current_user_b():
        return user_b

    # Start with User A
    app.dependency_overrides[get_current_user] = override_get_current_user_a
    
    # 2. User A creates dataset
    res = client.post("/api/v1/ground-truth/datasets?name=OttomanDataset1")
    assert res.status_code == 200
    dataset_a = res.json()
    dataset_id = dataset_a["id"]

    res = client.get("/api/v1/ground-truth/datasets")
    assert res.status_code == 200
    assert [dataset["id"] for dataset in res.json()] == [dataset_id]
    
    # 3. User B tries to access Dataset A -> 403
    app.dependency_overrides[get_current_user] = override_get_current_user_b
    res = client.get(f"/api/v1/ground-truth/datasets/{dataset_id}")
    assert res.status_code == 403
    
    # 4. User A adds a page
    app.dependency_overrides[get_current_user] = override_get_current_user_a
    res = client.post(f"/api/v1/ground-truth/datasets/{dataset_id}/pages?original_image_hash=dummyhash")
    assert res.status_code == 200
    page_id = res.json()["id"]

    res = client.get(f"/api/v1/ground-truth/datasets/{dataset_id}/pages")
    assert res.status_code == 200
    assert [page["id"] for page in res.json()] == [page_id]
    
    # 5. User B tries to get lines -> 403
    app.dependency_overrides[get_current_user] = override_get_current_user_b
    res = client.get(f"/api/v1/ground-truth/pages/{page_id}/lines")
    assert res.status_code == 403
    res = client.get(f"/api/v1/ground-truth/datasets/{dataset_id}/export")
    assert res.status_code == 403
    
    # 6. User A creates lines (DRAFT)
    app.dependency_overrides[get_current_user] = override_get_current_user_a
    lines_data = [
        {"bounding_box": [0,0,10,10], "reading_order": 0, "text_content": "Merhaba"},
        {"bounding_box": [10,10,20,20], "reading_order": 1, "text_content": "Dunya"}
    ]
    res = client.post(f"/api/v1/ground-truth/pages/{page_id}/lines", json=lines_data)
    assert res.status_code == 200
    assert len(res.json()["lines"]) == 2
    
    # 7. Page-level lock is no longer allowed; dataset-level review workflow is required.
    res = client.post(f"/api/v1/ground-truth/pages/{page_id}/lock")
    assert res.status_code == 400
    assert "dataset-level" in res.json()["detail"]
    
    # 8. User A can still edit because the page was not locked by the review workflow.
    res = client.post(f"/api/v1/ground-truth/pages/{page_id}/lines", json=lines_data)
    assert res.status_code == 200
    
    # 9. Evaluation is rejected until dataset-level lock is complete.
    ocr_texts = ["Merhaba", "Dunya"]
    res = client.post(f"/api/v1/ground-truth/evaluate/{page_id}", json=ocr_texts)
    assert res.status_code == 400

    res = client.get(f"/api/v1/ground-truth/datasets/{dataset_id}/export?format=json")
    assert res.status_code == 200
    exported = res.json()["content"]
    assert exported["dataset"]["id"] == dataset_id
    assert exported["pages"][0]["lines"][0]["text_content"] == "Merhaba"

    res = client.get(f"/api/v1/ground-truth/datasets/{dataset_id}/export?format=txt")
    assert res.status_code == 200
    assert "Merhaba\nDunya" == res.json()["content"]

    # Clean up dependency override
    app.dependency_overrides.clear()
