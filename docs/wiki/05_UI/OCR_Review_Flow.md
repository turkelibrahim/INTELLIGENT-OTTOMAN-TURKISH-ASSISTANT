---
type: module
status: partial
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/api/routes/ocr_review.py
  - backend/app/api/router.py
test_paths:
  - backend/tests/test_ocr_review.py
tags: [ui, api, ocr, review, audit, task-018]
---

# OCR Review Flow

**Ozet:** OCR review backend API akisi TASK-018 kapsaminda dogrulandi. Kullanici sahipligi kontrolu, dusuk guven skoru filtresi, OCR duzeltme surumleme ve audit kaydi testlidir; frontend review workspace ekrani henuz uygulanmadi.

**Kutuphaneler:** FastAPI, Pydantic, SQLAlchemy, pytest.

**Baglantilar:** [[Document_Workspace]], [[OCR_Service]], [[Audit_Log]], [[Transliteration_Service]]

## Sorumluluklar
- Sayfa bazinda OCR satirlarini review icin listelemek.
- Dusuk guven skorlu OCR satirlarini filtrelemek.
- Ham OCR metnini koruyarak kullanici duzeltmesini `TextVersion` kaydi olarak saklamak.
- Her duzeltme icin eski/yeni metin degerleriyle audit kaydi yazmak.
- Belge sahibi veya admin disindaki kullanicilari engellemek.

## Girdiler
- `GET /api/v1/ocr-review/pages/{page_id}/lines`
- `POST /api/v1/ocr-review/ocr-results/{ocr_result_id}/corrections`
- `OCRResult.page_id`, `line_no`, `bbox`, `raw_text`, `confidence_score`.
- Kullanici duzeltmesi: `CorrectionCreate.text`.

## Ciktilar
- `OCRLineResponse` listesi: raw OCR, bbox, confidence ve varsa son duzeltme.
- `TextVersionResponse`: `version_type="ocr_correction"`, yeni metin, onceki metin, kaynak OCR sonucu ve sayfa baglantisi.
- `AuditLog(action="ocr.correction.create", object_type="text_version")`.

## Bagimliliklar
- [[OCR_Service]] tarafindan uretilen `OCRResult` kayitlari.
- [[Database_Model]] icindeki `OCRResult` ve `TextVersion` modelleri.
- [[Security_Model]] icindeki `get_current_user` auth kontrolu.
- [[Audit_Log]] modeli.

## Veri Akisi
1. OCR sonuc satirlari `OCRResult` tablosunda bulunur.
2. Review API sayfa ve belge sahipligini dogrular.
3. Satir listesi `line_no` ve `id` sirasiyla doner.
4. Duzeltme istegi ham OCR metnini degistirmez; yeni satir `TextVersion` olarak eklenir.
5. Sonraki duzeltmede `previous_text`, onceki duzeltmeden gelir.
6. Audit kaydi eski/yeni text snapshot'larini JSON olarak saklar.

## Hata Durumlari
- Sayfa yoksa `404`.
- OCR sonucu yoksa `404`.
- Belge sahibi olmayan kullanici icin `403`.
- Bos duzeltme metni Pydantic `min_length=1` ile reddedilir.

## Guvenlik ve Gizlilik
- Route'lar JWT ile `get_current_user` kullanir.
- Belge sahibi olmayan kullanicilar engellenir; admin rolune izin verilir.
- Ham OCR korunur; kullanici duzeltmeleri ayri surumlenir.

## Testler ve Kabul Kriterleri
- `backend/tests/test_ocr_review.py::test_review_lines_are_scoped_and_low_confidence_filter_works`
- `backend/tests/test_ocr_review.py::test_correction_preserves_raw_ocr_and_creates_text_version_and_audit`
- `backend/tests/test_ocr_review.py::test_second_correction_keeps_correction_history`
- Kanit: `evidence/environment_gate/backend_pytest_task018_review_initial.txt` -> 3 passed.
- Kanit: `evidence/environment_gate/backend_pytest_task018_initial.txt` -> 31 passed.
- Kanit: `evidence/environment_gate/doctor_task018_full.txt` -> `DOCTOR_FAILED=0`.

## Kod Kanitlari
- `backend/app/api/routes/ocr_review.py` -> `list_review_lines`, `create_correction`, `_latest_correction_text`, `_get_authorized_page`.
- `backend/app/api/router.py` -> OCR review router dahil edildi.
- `backend/app/models/processing_outputs.py` -> `OCRResult`, `TextVersion`.
- `backend/app/models/audit_log.py` -> `AuditLog`.

## Bilinen Eksikler
- Frontend OCR review workspace ekrani henuz uygulanmadi.
- OCR satirlarini otomatik runtime pipeline icinden DB'ye yazan tam akis henuz tamamlanmadi.
- Transliterasyon review ve kullanici secimi TASK-019 kapsamindadir.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda planned olarak olusturuldu.
- 2026-07-28: TASK-018 kapsaminda backend OCR review/correction/audit API ve test kanitlariyla `partial` yapildi.
