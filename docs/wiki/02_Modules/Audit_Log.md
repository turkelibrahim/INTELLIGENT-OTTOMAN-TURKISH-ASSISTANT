---
type: module
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/models/audit_log.py
  - backend/app/api/routes/auth.py
  - backend/app/api/routes/documents.py
  - backend/app/api/routes/preprocessing.py
  - backend/app/api/routes/ocr_review.py
  - backend/app/api/routes/transliteration.py
  - backend/app/api/routes/modernization.py
  - backend/app/api/routes/analysis.py
test_paths:
  - backend/tests/test_auth_security.py
  - backend/tests/test_document_upload_integration.py
  - backend/tests/test_ocr_review.py
  - backend/tests/test_transliteration.py
  - backend/tests/test_modernization.py
  - backend/tests/test_analysis.py
tags: [audit, security, task-021]
---

# Audit Log

**Ozet:** AuditLog modeli ve auth/document/preprocessing/OCR correction/transliteration/modernization/entity olaylarinda audit kaydi yazma kodu mevcuttur. TASK-011, TASK-012, TASK-018, TASK-019, TASK-020 ve TASK-021 ile user/document/text/entity audit kayitlari testlendi. DB seviyesinde append-only garanti henuz uygulanmadi.

**Kutuphaneler:** SQLAlchemy, FastAPI, pytest.

**Baglantilar:** [[Security_Model]], [[Document_Ingestion]], [[Image_Preprocessing]], [[OCR_Review_Flow]], [[Transliteration_Service]], [[Modernization_Service]], [[NER_Service]]

## Sorumluluklar
- Kullanici aksiyonlarini actor, action, object ve eski/yeni degerlerle kaydetmek.
- Duzeltme gibi kritik text degisikliklerinde onceki ve yeni degeri saklamak.

## Girdiler
- Route request, current_user, action verileri.
- OCR correction akisi icin `previous_text` ve yeni duzeltme metni.
- Transliteration/modernization akislarinda method/prompt/provider metadata'si.

## Ciktilar
- `audit_logs` DB satiri.
- Text version uzerinden OCR correction, transliteration, modernization ve entity action kayitlari.

## Bagimliliklar
- `User`, route DB session.
- `TextVersion`, `OCRResult` ve `Entity` text/entity audit akislarinda kullanilir.

## Veri Akisi
- Route islemi sonrasi `AuditLog(...)` -> `db.add` -> `db.commit`.
- Text akislari eski/yeni metin snapshot'larini JSON olarak saklar.

## Hata Durumlari
- Audit commit hatasi islem sonucunu etkileyebilir; retry yok.
- DB seviyesinde append-only veya trigger tabanli koruma yok.

## Guvenlik ve Gizlilik
- IP adresi kaydedilebilir; user_agent modeli var ama route yazimi sinirli.
- Gizli degerler audit/wiki kanitlarina kopyalanmaz.

## Testler ve Kabul Kriterleri
- Auth audit kaniti: `backend/tests/test_auth_security.py`.
- Document/preprocessing audit kaniti: `backend/tests/test_document_upload_integration.py`.
- OCR correction audit kaniti: `backend/tests/test_ocr_review.py`.
- Transliteration audit kaniti: `backend/tests/test_transliteration.py`.
- Modernization audit kaniti: `backend/tests/test_modernization.py`.
- Entity audit kaniti: `backend/tests/test_analysis.py`.
- Kanit: `evidence/environment_gate/backend_pytest_task021_initial.txt` -> 44 passed.
- Doctor kaniti: `evidence/environment_gate/doctor_task021_full.txt` -> `DOCTOR_FAILED=0`.

## Kod Kanitlari
- `backend/app/models/audit_log.py` -> `AuditLog`.
- `backend/app/api/routes/auth.py` -> `user.register`, `user.login`, `user.logout`.
- `backend/app/api/routes/documents.py` -> `document.create`, `document.delete`.
- `backend/app/api/routes/preprocessing.py` -> `page.preprocess`.
- `backend/app/api/routes/ocr_review.py` -> `ocr.correction.create`.
- `backend/app/api/routes/transliteration.py` -> `transliteration.create`, `transliteration.correction.create`.
- `backend/app/api/routes/modernization.py` -> `modernization.create`, `modernization.correction.create`.
- `backend/app/api/routes/analysis.py` -> `entity.extraction.create`, `entity.user_correction.create`.

## Bilinen Eksikler
- Append-only teknik enforcement yok.
- Audit log listeleme/arastirma endpointi yok.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
- 2026-07-28: TASK-011/TASK-012 sirasinda auth, document ve preprocessing audit test kanitlari eklendi.
- 2026-07-28: TASK-018 ile OCR correction audit kanitlari eklendi.
- 2026-07-28: TASK-019 ile transliteration audit kanitlari eklendi.
- 2026-07-28: TASK-020 ile modernization audit kanitlari eklendi.
- 2026-07-28: TASK-021 ile entity extraction ve user correction audit kanitlari eklendi.
