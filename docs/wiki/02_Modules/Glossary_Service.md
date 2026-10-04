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
tags: [glossary, task-021]
---

# Glossary Service

**Ozet:** TASK-021 ile local glossary fallback eklendi. Glossary entry word, variants, meaning, part_of_speech, example, source ve approved alanlarini tasir; merkezi editable glossary veritabani henuz yoktur.

**Kutuphaneler:** Python, pytest.

**Baglantilar:** [[NER_Service]], [[Date_Normalization]], [[Modernization_Service]]

## Sorumluluklar
- Arkaik kelimeleri ve varyantlarini bulmak.
- Hover/kart UI icin meaning/source/approved metadata'si uretmek.

## Girdiler
- Modern veya translitere metin.

## Ciktilar
- `GlossaryEntry` listesi ve `Entity(entity_type="GLOSSARY")`.

## Bagimliliklar
- [[NER_Service]] extraction akisi.

## Testler ve Kabul Kriterleri
- Kanit: `backend/tests/test_analysis.py`.
- Kanit: `evidence/environment_gate/backend_pytest_task021_analysis_initial.txt` -> 4 passed.

## Kod Kanitlari
- `backend/app/services/document_processing/ner_extractor.py` -> `GlossaryEntry`, `_matched_glossary_entries`, `_extract_glossary`.

## Bilinen Eksikler
- Kullanici tarafindan yonetilen glossary CRUD yok.
- Kaynak sozluk corpus'u yok; local fixture seviyesi.

## Degisiklik Gecmisi
- 2026-07-28: TASK-021 ile partial olarak uygulandi.
