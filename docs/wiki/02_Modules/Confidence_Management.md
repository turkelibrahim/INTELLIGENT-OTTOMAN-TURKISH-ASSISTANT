---
type: module
status: partial
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/services/document_processing/confidence.py
  - backend/app/models/processing_outputs.py
test_paths:
  - backend/tests/test_confidence_model_registry.py
tags: [confidence, model-registry, task-022]
---

# Confidence Management

**Ozet:** TASK-022 ile merkezi confidence policy servisi eklendi. Skorlar `[0, 1]` araligina normalize edilir, high/medium/low/unknown/fallback etiketleri uretilir ve confidence kesin dogruluk olarak sunulmaz. Runtime entegrasyonu servis seviyesinde testlidir; UI gosterimi henuz yoktur.

**Kutuphaneler:** SQLAlchemy, pytest.

**Baglantilar:** [[Model_Registry]], [[OCR_Service]], [[Transliteration_Service]], [[Modernization_Service]], [[NER_Service]]

## Sorumluluklar
- Confidence skorlarini merkezi politika ile normalize etmek.
- Confidence label ve policy version uretmek.
- Fallback outputlari acikca etiketlemek.
- AI operasyon metadata'si icinde confidence ve model bilgisini birlikte tasimak.

## Girdiler
- OCR, transliteration, modernization ve NER confidence skorlari.
- Fallback flag.

## Ciktilar
- `ConfidenceAssessment`.
- `build_operation_metadata(...)` ile operation/model/confidence metadata yapisi.

## Bagimliliklar
- [[Model_Registry]] descriptor servisi.
- AI servislerinin confidence skor alanlari.

## Hata Durumlari
- `None` skor `unknown` olarak etiketlenir.
- Fallback skor yuksek olsa bile `fallback` label'i alir.

## Guvenlik ve Gizlilik
- Gizli deger kullanmaz.
- Confidence aciklamasi kullaniciya kesinlik iddiasi olarak sunulmamalidir.

## Testler ve Kabul Kriterleri
- `backend/tests/test_confidence_model_registry.py::test_confidence_policy_labels_and_clamps_scores`.
- `backend/tests/test_confidence_model_registry.py::test_ai_operations_have_model_and_confidence_metadata`.
- Kanit: `evidence/environment_gate/backend_pytest_task022_confidence_initial.txt` -> 4 passed.
- Kanit: `evidence/environment_gate/backend_pytest_task022_initial.txt` -> 48 passed.
- Kanit: `evidence/environment_gate/doctor_task022_full.txt` -> `DOCTOR_FAILED=0`.

## Kod Kanitlari
- `backend/app/services/document_processing/confidence.py` -> `ConfidenceManager`, `ConfidenceAssessment`, `build_operation_metadata`.

## Bilinen Eksikler
- Existing runtime API responses henuz tum metadata'yi otomatik expose etmiyor.
- UI confidence badge/policy aciklamasi yok.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda partial olarak olusturuldu.
- 2026-07-28: TASK-022 ile merkezi confidence policy testli hale getirildi.
