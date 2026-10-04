---
type: module
status: partial
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/services/document_processing/preprocessor.py
  - backend/app/api/routes/preprocessing.py
  - backend/app/models/image_variant.py
test_paths:
  - backend/tests/test_document_upload_integration.py
tags: [ai, image, preprocessing]
---

# Image Preprocessing

**Ozet:** OpenCV tabanli goruntu iyilestirme profilleri ve varyant API kodu vardir. TASK-012 ile preprocessing endpoint'i upload edilen sayfadan `ImageVariant` ve audit kaydi uretme senaryosunda PASS oldu. TASK-015 ile `ImagePreprocessor.process` pipeline sozlesmesi eklendi ve pipeline smoke PASS oldu. OCR/layout akisi henuz tam olmadigi icin modul genel status `partial`tir.

**Kutuphaneler:** OpenCV, NumPy, SQLAlchemy, FastAPI.

**Baglantilar:** [[Document_Workspace]], [[Database_Model]], [[Layout_Analysis]], [[OCR_Service]]

## Sorumluluklar
- Denoise, CLAHE, threshold, skew correction, quality score ve processed image kaydi.

## Girdiler
- Page id, profil, opsiyonel parametreler.

## Ciktilar
- `ImageVariant`, PNG processed dosyasi.

## Bagimliliklar
- `Page`, `Document`, `ImageVariant`, `settings.UPLOAD_DIR`.

## Veri Akisi
- UI -> `preprocessingApi.preprocess` -> `create_preprocess_variant` -> `ImagePreprocessor.process_with_profile`.

## Hata Durumlari
- Goruntu okunamazsa `ValueError` yukselebilir; route bunu ozel HTTP hataya cevirmiyor.

## Guvenlik ve Gizlilik
- Belge sahibi/admin yetki kontrolu var.

## Testler ve Kabul Kriterleri
- Endpoint integration testi PASS: `backend/tests/test_document_upload_integration.py::test_preprocessing_variant_creates_file_db_record_and_audit`.
- Pipeline smoke PASS: `evidence/environment_gate/backend_pytest_task015_pipeline_initial.txt`.
- Kabul: route ve pipeline ayni preprocessor sozlesmesiyle gecmeli; orijinal dosya degismeden variant uretilmeli.

## Kod Kanitlari
- `backend/app/services/document_processing/preprocessor.py` -> `ImagePreprocessor`
- `backend/app/api/routes/preprocessing.py` -> `create_preprocess_variant`
- `backend/app/api/routes/preprocessing.py` -> `ImageVariantResponse.created_at: datetime` TASK-012 response validation fix.

## Bilinen Eksikler
- ProcessingJob ile baglantili job_id set edilmiyor.
- Layout/OCR gercek model hattina bagli full pipeline henuz tamamlanmadi.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
- 2026-07-28: TASK-008 sirasinda status `partial` yapildi; pipeline kirigi kanitla kaydedildi.
- 2026-07-28: TASK-012 sirasinda preprocessing endpoint response validation duzeltildi ve integration test PASS oldu.
- 2026-07-28: TASK-015 sirasinda `ImagePreprocessor.process` sozlesmesi eklendi ve pipeline smoke PASS oldu.
