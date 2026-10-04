"""Live browser E2E for auth, document processing, OCR, and ground-truth isolation.

This test intentionally requires running backend, frontend, and worker services. Regular
unit/regression runs should invoke it with PLAYWRIGHT_LIVE_E2E=1 only when those services
are started against the same database.
"""

import hashlib
import io
import os
import time

import pytest
from PIL import Image, ImageDraw
try:
    from playwright.sync_api import Page, expect
except ImportError:
    pytest.skip("Playwright not installed, skipping browser tests.", allow_module_level=True)


pytestmark = [pytest.mark.e2e, pytest.mark.live]

API = os.environ.get("E2E_API_URL", "http://127.0.0.1:8000/api/v1")
WEB = os.environ.get("E2E_WEB_URL", "http://localhost:3000")
PASSWORD = "Password123!"
OTTOMAN_LINE_1 = "\u0645\u0631\u062d\u0628\u0627 \u0639\u062b\u0645\u0627\u0646\u0644\u0649"
OTTOMAN_LINE_2 = "\u062f\u0646\u06cc\u0627 \u0633\u0627\u0637\u0631"


def _require_live_e2e():
    if os.environ.get("PLAYWRIGHT_LIVE_E2E") != "1":
        pytest.skip("Requires PLAYWRIGHT_LIVE_E2E=1 with live backend, frontend, and worker")


def _sample_png() -> bytes:
    image = Image.new("RGB", (420, 180), "white")
    draw = ImageDraw.Draw(image)
    # Deliberately use dark text-like strokes so OCR/layout work on real image bytes.
    draw.rectangle((40, 45, 380, 75), fill="black")
    draw.rectangle((90, 105, 340, 130), fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _register_via_ui(page: Page, email: str, username: str) -> str:
    page.on("console", lambda msg: print(f"BROWSER_CONSOLE[{msg.type}]: {msg.text}"))
    page.on("pageerror", lambda exc: print(f"BROWSER_PAGEERROR: {exc}"))
    page.on("response", lambda response: print(f"BROWSER_RESPONSE[{response.status}]: {response.url}") if response.status >= 400 else None)
    page.on("requestfailed", lambda request: print(f"BROWSER_REQUEST_FAILED: {request.url} {request.failure}"))
    page.goto(f"{WEB}/login#register")
    expect(page.locator("#email")).to_be_visible(timeout=15000)
    expect(page.locator("#username")).to_be_visible(timeout=15000)
    page.locator("#email").fill(email)
    page.locator("#username").fill(username)
    page.locator("#fullName").fill(username)
    page.locator("#password").fill(PASSWORD)
    page.locator("button[type='submit']").click()
    page.wait_for_url("**/dashboard", timeout=15000)
    expect(page.get_by_text("Belgelerim")).to_be_visible(timeout=15000)
    token = page.evaluate("localStorage.getItem('access_token')")
    assert token, "registration/login did not store access token"
    return token


def _api_get(page: Page, path: str, token: str):
    response = page.request.get(f"{API}{path}", headers={"Authorization": f"Bearer {token}"})
    assert response.ok, response.text()
    return response


def _api_post(page: Page, path: str, token: str, **kwargs):
    response = page.request.post(f"{API}{path}", headers={"Authorization": f"Bearer {token}"}, **kwargs)
    assert response.ok, response.text()
    return response


def test_ground_truth_browser_full_document_worker_flow(page: Page):
    _require_live_e2e()
    stamp = str(int(time.time()))
    email_a = f"gt_live_a_{stamp}@example.com"
    email_b = f"gt_live_b_{stamp}@example.com"
    png_bytes = _sample_png()
    image_hash = hashlib.sha256(png_bytes).hexdigest()

    token_a = _register_via_ui(page, email_a, f"gtlivea{stamp}")

    upload = _api_post(
        page,
        "/documents",
        token_a,
        multipart={
            "title": "Live browser E2E scan",
            "description": "Uploaded by Playwright live E2E",
            "file": {"name": "ottoman-live-e2e.png", "mimeType": "image/png", "buffer": png_bytes},
        },
    )
    document_id = upload.json()["id"]

    page.goto(f"{WEB}/dashboard")
    expect(page.get_by_text("Live browser E2E scan")).to_be_visible(timeout=15000)

    pages_response = _api_get(page, f"/documents/{document_id}/pages", token_a).json()
    assert pages_response["total"] == 1
    document_page_id = pages_response["pages"][0]["id"]

    job = _api_post(page, f"/documents/{document_id}/ocr", token_a).json()
    assert job["status"] == "QUEUED"
    job_id = job["job_id"]

    status_payload = None
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        status_response = _api_get(page, f"/documents/{document_id}/ocr/status", token_a)
        status_payload = status_response.json()
        if status_payload["status"] == "completed":
            break
        assert status_payload["status"] not in {"failed"}, status_payload
        time.sleep(2)
    assert status_payload is not None
    assert status_payload["status"] == "completed", {
        "job_id": job_id,
        "last_status": status_payload,
        "reason": "Worker did not acquire and complete the OCR job within timeout",
    }
    assert "result" in status_payload
    assert "pipeline_results" in status_payload["result"]

    page.goto(f"{WEB}/dashboard/annotation-studio")
    expect(page.get_by_text("Ground Truth Human Review")).to_be_visible(timeout=15000)
    expect(page.get_by_alt_text("Review page")).to_be_visible(timeout=15000)

    datasets = _api_get(page, "/ground-truth/datasets", token_a).json()
    assert datasets, "annotation studio did not prepare a dataset"
    dataset_id = datasets[0]["id"]
    pages = _api_get(page, f"/ground-truth/datasets/{dataset_id}/pages", token_a).json()
    assert pages, "annotation studio dataset has no pages"
    gt_page_id = pages[0]["id"]

    page.locator("textarea[dir='rtl']").first.fill(OTTOMAN_LINE_1)
    page.get_by_label("Metni kontrol ettim").check()
    page.get_by_label("Satir kutusunu kontrol ettim").check()
    page.get_by_role("button", name="Kaydet", exact=True).click()
    expect(page.get_by_text("Satir kaydedildi")).to_be_visible(timeout=15000)

    page.reload()
    expect(page.get_by_text("Ground Truth Human Review")).to_be_visible(timeout=15000)
    expect(page.get_by_alt_text("Review page")).to_be_visible(timeout=15000)
    expect(page.locator("textarea[dir='rtl']").first).to_have_value(OTTOMAN_LINE_1, timeout=15000)
    assert page.get_by_label("Metni kontrol ettim").is_checked()
    assert page.get_by_label("Satir kutusunu kontrol ettim").is_checked()

    export_a = _api_get(page, f"/ground-truth/datasets/{dataset_id}/export?format=json", token_a).json()
    exported = str(export_a["content"])
    assert OTTOMAN_LINE_1 in exported
    page.evaluate("localStorage.removeItem('access_token')")
    token_b = _register_via_ui(page, email_b, f"gtliveb{stamp}")
    denied_dataset = page.request.get(
        f"{API}/ground-truth/datasets/{dataset_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert denied_dataset.status in (403, 404), denied_dataset.text()
    denied_page_image = page.request.get(
        f"{API}/ground-truth/pages/{gt_page_id}/image",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert denied_page_image.status in (403, 404), denied_page_image.text()
    anonymous = page.request.get(f"{API}/ground-truth/datasets/{dataset_id}")
    assert anonymous.status in (401, 403), anonymous.text()






