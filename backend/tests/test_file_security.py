import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException

from app.services.file_service import FileService


def run_async(coro):
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()


class FakeUpload:
    def __init__(self, filename, content_type, content):
        self.filename = filename
        self.content_type = content_type
        self._content = content
        self._offset = 0

    async def read(self, size=-1):
        if self._offset >= len(self._content):
            return b""
        if size is None or size < 0:
            size = len(self._content) - self._offset
        chunk = self._content[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


def test_validate_file_rejects_unsupported_extension():
    service = FileService()
    upload = FakeUpload("payload.exe", "application/octet-stream", b"MZ")

    with pytest.raises(HTTPException) as exc:
        service.validate_file(upload)

    assert exc.value.status_code == 400


def test_validate_file_rejects_mime_spoof_before_save():
    service = FileService()
    upload = FakeUpload("scan.png", "text/plain", b"not-an-image")

    with pytest.raises(HTTPException) as exc:
        service.validate_file(upload)

    assert exc.value.status_code == 400


def test_save_upload_rejects_magic_byte_spoof_and_cleans_file(tmp_path):
    service = FileService()
    service.upload_dir = tmp_path
    upload = FakeUpload("scan.png", "image/png", b"not-a-real-png")

    with pytest.raises(HTTPException) as exc:
        run_async(service.save_upload(upload, document_id=42))

    assert exc.value.status_code == 400
    assert list(tmp_path.rglob("*.*")) == []


def test_save_upload_enforces_size_limit_and_cleans_file(tmp_path):
    service = FileService()
    service.upload_dir = tmp_path
    service.max_size = 4
    upload = FakeUpload("scan.png", "image/png", b"\x89PNG" + b"x" * 10)

    with pytest.raises(HTTPException) as exc:
        run_async(service.save_upload(upload, document_id=43))

    assert exc.value.status_code == 413
    assert list(tmp_path.rglob("*.*")) == []


def test_save_upload_neutralizes_path_traversal_filename(tmp_path):
    service = FileService()
    service.upload_dir = tmp_path
    upload = FakeUpload("../scan.png", "image/png", b"\x89PNG\r\n\x1a\n")

    saved_path, file_hash, file_size = run_async(service.save_upload(upload, document_id=44))

    assert file_hash
    assert file_size == 8
    assert str(tmp_path.resolve()) in str((tmp_path / "originals" / "44").resolve())
    assert ".." not in saved_path


