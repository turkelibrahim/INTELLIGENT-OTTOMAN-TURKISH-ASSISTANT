---
type: module
status: partial
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/services/document_processing/ner_extractor.py
  - backend/app/api/routes/analysis.py
test_paths:
  - backend/tests/test_analysis.py
tags: [dates, task-021]
---

# Date Normalization

**Ozet:** TASK-021 ile Hicri, Rumi ve Miladi yil ifadeleri icin ham tarihi koruyan rule-based normalizasyon eklendi. Hicri/Rumi donusumleri yaklasik yil toplami olarak isaretlenir; tam takvim donusumu henuz yoktur.

**Kutuphaneler:** Python regex, pytest.

**Baglantilar:** [[NER_Service]], [[Glossary_Service]], [[Evaluation_Service]]

## Sorumluluklar
- Ham tarih degerini kaybetmeden calendar, normalized_value ve method alanlari uretmek.
- DATE entity metadata'si icinde donusum yontemini saklamak.

## Girdiler
- `Hicri 1327`, `Rumi 1330`, `1327` benzeri yil ifadeleri.

## Ciktilar
- `metadata_json.date.raw_value`, `calendar`, `normalized_value`, `method`.

## Bagimliliklar
- [[NER_Service]] date extraction.

## Testler ve Kabul Kriterleri
- Kanit: `backend/tests/test_analysis.py`.
- Kanit: `evidence/environment_gate/backend_pytest_task021_analysis_initial.txt` -> 4 passed.

## Kod Kanitlari
- `backend/app/services/document_processing/ner_extractor.py` -> `normalize_date`, `_extract_dates`.

## Bilinen Eksikler
- Gun/ay hassasiyetli Hicri/Rumi donusum yok.
- Takvim kutuphanesi kullanilmiyor.

## Degisiklik Gecmisi
- 2026-07-28: TASK-021 ile partial olarak uygulandi.
