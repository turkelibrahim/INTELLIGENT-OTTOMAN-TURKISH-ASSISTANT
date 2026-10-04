---
type: module
status: partial
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/services/document_processing/ner_extractor.py
  - backend/app/api/routes/analysis.py
  - backend/app/api/router.py
test_paths:
  - backend/tests/test_analysis.py
tags: [ai, ner, dates, glossary, task-021]
---

# NER Service

**Ozet:** TASK-021 ile rule-based fallback NER, tarih normalizasyonu, glossary ve entity storage API eklendi. Entity ciktilari kaynak `TextVersion` ile baglanir, ham tarih kaybolmaz, kullanici entity eklemeleri audit ile saklanir ve precision/recall/F1 smoke raporu testlidir. Gercek token classification modeli henuz yoktur.

**Kutuphaneler:** FastAPI, Pydantic, SQLAlchemy, pytest, Python regex.

**Baglantilar:** [[Modernization_Service]], [[Date_Normalization]], [[Glossary_Service]], [[Evaluation_Service]], [[Audit_Log]]

## Sorumluluklar
- PER, LOC, ORG, DATE, GLOSSARY ve MISC tipleri icin entity ciktisi uretmek.
- Entity start/end offset, kaynak text version ve confidence skoru tasimak.
- Hicri/Rumi/Miladi tarih ham degerini ve donusum metodunu saklamak.
- Glossary entry kaynak ve onay alanlarini dondurmek.
- OCR belirsizliginin NER etkisini raporlamak.

## Girdiler
- Modernization/transliteration kaynakli `TextVersion.text`.
- Opsiyonel kullanici entity eklemeleri.

## Ciktilar
- `Entity` DB satirlari.
- `EntityExtractionResponse` icinde entities, glossary, evaluation ve ocr_impact.
- Audit action: `entity.extraction.create`, `entity.user_correction.create`.

## Bagimliliklar
- [[Modernization_Service]] text version ciktisi.
- [[Database_Model]] icindeki `Entity` ve `TextVersion`.
- [[Security_Model]] belge sahipligi kontrolu.

## Veri Akisi
1. `POST /api/v1/analysis/text-versions/{text_version_id}/entities` kaynak text version'i bulur.
2. Belge sahibi/admin kontrolu yapilir.
3. `NERExtractor.extract` entity/date/glossary ciktisi uretir.
4. Ciktilar `Entity` tablosuna `text_version_id` ile kaydedilir.
5. Kullanici eklemeleri metadata `source="user_correction"` ile saklanir.
6. Audit kayitlari yazilir.

## Hata Durumlari
- Kaynak text version yoksa `404`.
- Belge yoksa `404`.
- Yetkisiz kullanici icin `403`.
- NER skoru kesin dogruluk degil confidence olarak sunulur.

## Guvenlik ve Gizlilik
- Harici servis yok; secret kullanilmaz.
- Belge izolasyonu testlidir.

## Testler ve Kabul Kriterleri
- `backend/tests/test_analysis.py::test_ner_extracts_entities_dates_glossary_and_metrics`.
- `backend/tests/test_analysis.py::test_ocr_impact_report_flags_uncertain_tokens`.
- `backend/tests/test_analysis.py::test_analysis_api_stores_entities_user_correction_and_audit`.
- `backend/tests/test_analysis.py::test_analysis_api_enforces_ownership`.
- Kanit: `evidence/environment_gate/backend_pytest_task021_analysis_initial.txt` -> 4 passed.
- Kanit: `evidence/environment_gate/backend_pytest_task021_initial.txt` -> 44 passed.
- Kanit: `evidence/environment_gate/doctor_task021_full.txt` -> `DOCTOR_FAILED=0`.

## Kod Kanitlari
- `backend/app/services/document_processing/ner_extractor.py` -> `NERExtractor`, `EntityPrediction`, `GlossaryEntry`.
- `backend/app/api/routes/analysis.py` -> `extract_entities_for_text_version`.
- `backend/app/models/processing_outputs.py` -> `Entity`.

## Bilinen Eksikler
- Gercek model tabanli NER yok.
- Entity delete/label-change icin ayri update/delete endpointleri henuz yok; kullanici ekleme audit ile saklanir.
- Kanonik entity registry tablosu yok.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda placeholder/partial olarak olusturuldu.
- 2026-07-28: TASK-021 ile rule-based NER/date/glossary API ve tests eklendi.
