import pytest
from app.services.export_service import secure_path, EXPORT_ROOT
from fastapi import HTTPException
from pathlib import Path

def test_path_traversal():
    # Attempting to go up a directory
    with pytest.raises(HTTPException) as exc:
        secure_path(EXPORT_ROOT, "../secret.txt")
    assert exc.value.status_code == 400
    
    # Attempting absolute paths
    with pytest.raises(HTTPException) as exc:
        secure_path(EXPORT_ROOT, "/etc/passwd")
    assert exc.value.status_code == 400

    # Windows drive injection
    with pytest.raises(HTTPException) as exc:
        secure_path(EXPORT_ROOT, "C:\\Windows\\System32")
    assert exc.value.status_code == 400
    
    # Normal secure path
    target = secure_path(EXPORT_ROOT, "valid_ds/exp_123")
    assert "valid_ds" in str(target)
    assert str(EXPORT_ROOT) in str(target)
