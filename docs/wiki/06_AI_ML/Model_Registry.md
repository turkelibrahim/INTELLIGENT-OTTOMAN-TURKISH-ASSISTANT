---
type: module
status: partial
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/models/processing_outputs.py
  - backend/app/services/document_processing/confidence.py
  - backend/app/services/document_processing/ocr_engine.py
test_paths:
  - backend/tests/test_confidence_model_registry.py
  - backend/tests/test_ocr_engine.py
tags: [ai, models, task-022]
---

# Model Registry

**Ozet:** TASK-010 ile `ModelRegistryEntry` tablosu, TASK-017 ile OCR metadata, TASK-022 ile idempotent model descriptor/registry service eklendi. OCR, transliteration, modernization ve NER operasyonlari icin model/method/provider metadata'si testlidir; ayrik admin API henuz yoktur.

**Kutuphaneler:** SQLAlchemy, torch, transformers, pytest.

**Baglantilar:** [[Confidence_Management]], [[Processing_Job_State_Machine]], [[OCR_Service]], [[Transliteration_Service]], [[Modernization_Service]], [[NER_Service]]

## Sorumluluklar
- Model/metot/provider adi, tur, surum, source, license ve config bilgisini izlenebilir kilmak.
- Aynı model descriptor icin idempotent `ModelRegistryEntry` kaydi saglamak.
- Operation metadata'sini confidence policy ile birlikte tasimak.

## Girdiler
- OCR adapter `model_metadata()`.
- Transliteration method version.
- Modernization provider/prompt version/mode.
- NER method version.

## Ciktilar
- `ModelRegistryEntry` DB satiri.
- `ModelDescriptor`.
- `build_operation_metadata(...)` model metadata.

## Bagimliliklar
- [[Confidence_Management]], `ModelRegistryEntry`.

## Veri Akisi
- Operation metadata -> `ModelRegistryService.descriptor_for_operation` -> `ensure_entry`.

## Hata Durumlari
- Desteklenmeyen operation `ValueError` uretir ve testlidir.

## Guvenlik ve Gizlilik
- Secret veya model credential saklanmaz.
- Harici model lisans/source alanlari release oncesi dogrulanmalidir.

## Testler ve Kabul Kriterleri
- `backend/tests/test_confidence_model_registry.py::test_model_registry_service_is_idempotent`.
- `backend/tests/test_confidence_model_registry.py::test_ai_operations_have_model_and_confidence_metadata`.
- `backend/tests/test_confidence_model_registry.py::test_unsupported_operation_is_explicit_error`.
- Kanit: `evidence/environment_gate/backend_pytest_task022_confidence_initial.txt` -> 4 passed.
- Kanit: `evidence/environment_gate/backend_pytest_task022_initial.txt` -> 48 passed.
- Kanit: `evidence/environment_gate/doctor_task022_full.txt` -> `DOCTOR_FAILED=0`.

## Kod Kanitlari
- `backend/app/models/processing_outputs.py` -> `ModelRegistryEntry`.
- `backend/app/services/document_processing/confidence.py` -> `ModelRegistryService`, `ModelDescriptor`.
- `backend/app/services/document_processing/ocr_engine.py` -> `model_metadata`.

## Bilinen Eksikler
- Model registry admin/list API yok.
- Runtime pipeline henuz her ciktida registry id persist etmiyor.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
- 2026-07-28: TASK-010 sirasinda `ModelRegistryEntry` modeli eklendi.
- 2026-07-28: TASK-017 sirasinda OCR adapter metadata kaniti eklendi.
- 2026-07-28: TASK-022 ile idempotent registry service ve operation metadata tests eklendi.
