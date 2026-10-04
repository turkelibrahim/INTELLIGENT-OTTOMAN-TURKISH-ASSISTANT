---
type: module
status: partial
last_verified: 2026-08-09
owners: []
source_paths:
  - backend/app/services/document_processing/translator.py
  - backend/app/api/routes/modernization.py
  - backend/app/api/router.py
test_paths:
  - backend/tests/test_modernization.py
tags: [ai, modernization, summary, task-020]
---

# Modernization Service

**Ozet:** TASK-020 ile transliterasyondan ayri modern Turkce aktarim ve belge ozeti backend akisi eklendi. 2026-08-09 downstream repair ile `rule-based-modernization-v2`, Latin kopyasini reddeden kalite kontrolleri, Osmanlica/Turkce sozluk normalizasyonu ve gercek payload `summary_text` akisi eklendi. `faithful`, `plain` ve `summary` modlari ayri `TextVersion` kayitlari olarak saklanir, kaynak transliteration version'a baglanir ve prompt-injection benzeri metin veri olarak islenir.

**Kutuphaneler:** FastAPI, Pydantic, SQLAlchemy, pytest.

**Baglantilar:** [[Transliteration_Service]], [[NER_Service]], [[RAG_Chat_Service]], [[Audit_Log]], [[Evaluation_Service]]

## Sorumluluklar
- Transliterasyon ciktisindan modern Turkce sadik aktarim uretmek.
- Plain/sadelestirilmis aktarim uretmek.
- Belge metnine dayali kisa ozet uretmek.
- Kaynak `TextVersion`, OCR line ve document baglantisini korumak.
- Okunamayan alanlari `[okunamadi]` olarak isaretlemek.
- Prompt injection benzeri metni talimat degil belge verisi kabul etmek.
- Modern Turkce paneline transliterasyonu aynen kopyalamamak; kalite dusukse controlled empty/fallback ve warning uretmek.

## Girdiler
- `TextVersion(version_type="transliteration")` veya kullanici tarafindan verilen duzeltme text'i.
- Mode: `faithful`, `plain`, `summary`.

## Ciktilar
- `ModernizationResult`.
- `TextVersion(version_type="modernization_faithful" | "modernization_plain" | "modernization_summary")`.
- `AuditLog(action="modernization.create" | "modernization.correction.create")`.

## Bagimliliklar
- [[Transliteration_Service]] kaynak text version uretir.
- [[Database_Model]] icindeki `TextVersion` ve `OCRResult`.
- [[Security_Model]] belge sahipligi kontrolu.

## Veri Akisi
1. `POST /api/v1/modernization/text-versions/{source_version_id}` kaynak text version'i bulur.
2. Belge sahibi/admin kontrolu yapilir.
3. Mode'a gore local rule-based fallback calisir.
4. Output ayri `TextVersion` olarak kaydedilir.
5. Correction history `previous_text` ve `source_version_id` ile korunur.
6. Audit kaydi provider, prompt version, safety warning ve preserved terms ile yazilir.

## Hata Durumlari
- Kaynak text version yoksa `404`.
- Belge yoksa `404`.
- Yetkisiz kullanici icin `403`.
- Gecersiz mode Pydantic pattern ile reddedilir.

## Guvenlik ve Gizlilik
- Harici saglayici yok; secret kullanilmaz.
- Prompt injection benzeri metinler `prompt_injection_like_text_treated_as_document_data` warning'i ile veri kabul edilir.
- Belgede olmayan bilgi uretmemek icin summary yalniz kaynak metnin ilk cumlesini kullanir.

## Testler ve Kabul Kriterleri
- `backend/tests/test_modernization.py::test_modernization_modes_are_separate_and_source_mapped`.
- `backend/tests/test_modernization.py::test_modernization_marks_unreadable_and_treats_prompt_injection_as_data`.
- `backend/tests/test_modernization.py::test_modernization_api_stores_outputs_separately_and_audits`.
- `backend/tests/test_modernization.py::test_modernization_correction_history_and_ownership`.
- 2026-08-09 kanit: `python -m pytest tests/test_transliteration.py tests/test_modernization.py tests/test_processing_pipeline.py` -> 11 passed.
- 2026-08-09 gercek belge kaniti: `evidence/downstream_text_repair/api_payload.json` -> `modernized_text` dolu, `transformation_quality.modernization_distinct_from_transliteration=true`.
- Kanit: `evidence/environment_gate/backend_pytest_task020_modernization_after_fix.txt` -> 4 passed.
- Kanit: `evidence/environment_gate/backend_pytest_task020_initial.txt` -> 40 passed.
- Kanit: `evidence/environment_gate/doctor_task020_full.txt` -> `DOCTOR_FAILED=0`.

## Kod Kanitlari
- `backend/app/services/document_processing/translator.py` -> `ModernizationResult`, `modernize`, `modernize_text`.
- `backend/app/api/routes/modernization.py` -> `create_modernization`, `_latest_modernization`.
- `backend/app/api/router.py` -> modernization router dahil edildi.
- `backend/app/models/processing_outputs.py` -> `TextVersion`.

## Bilinen Eksikler
- Gercek LLM/model/prompt provider entegrasyonu yok.
- Ozetleme ve modernizasyon rule-based; akademik kalite icin ileride uzman model/sozluk genisletmesi gerekir.
- Frontend modernizasyon duzeltme workflow'u henuz yok.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda placeholder/partial olarak olusturuldu.
- 2026-07-28: TASK-020 ile faithful/plain/summary mode, source mapping, safety warning, audit ve tests eklendi.
- 2026-08-09: Downstream text repair ile v2 modernization, summary payload mapping, duplicate-output guard ve gercek Kraken evidence eklendi.
