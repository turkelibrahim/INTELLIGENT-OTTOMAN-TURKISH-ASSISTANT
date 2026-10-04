---
type: module
status: partial
last_verified: 2026-08-09
owners: []
source_paths:
  - backend/app/services/document_processing/ocr_engine.py
test_paths:
  - backend/tests/test_ocr_engine.py
tags: [ai, ocr, task-017]
---

# OCR Service

**Ozet:** TASK-017 ile OCR adapter metadata/fallback sozlesmesi eklendi. 2026-08-09 runtime sisteminde Kraken primary OCR, EasyOCR segmenter ve `line-filter-v1` ile bos/dekoratif/gurultu satir suppression dogrulandi. Kraken recognition modeli degistirilmeden korunur.

**Kutuphaneler:** torch, transformers, Pillow, NumPy.

**Baglantilar:** [[Image_Preprocessing]], [[Layout_Analysis]], [[OCR_Review_Flow]], [[Transliteration_Service]], [[Model_Registry]], [[Task_Queue]]

## Sorumluluklar
- Goruntuden OCR metni cikarmak.
- Model/fallback metadata'sini izlenebilir yapmak.
- OCR line bbox'larini filtreli, page image coordinate sisteminde ve UI overlay ile tutarli uretmek.
- Bos/garbage/dekoratif line adaylarini Kraken recognition oncesi ve sonrasi elemek.

## Girdiler
- NumPy image.

## Ciktilar
- `OCRPageResult`: line listesi, bbox, confidence, model metadata, line filter metadata.
- `OCRLineResult`: text, confidence, bbox, line_index, engine metadata.

## Bagimliliklar
- HuggingFace TrOCR model dosyalari, torch device.
- CPU fallback dogrulandi: `torch.cuda.is_available()` False.

## Veri Akisi
- Pipeline -> `OCREngine.extract_text` veya adapter olarak `OCREngine.extract`.

## Hata Durumlari
- Model yukleme kapaliysa veya basarisizsa deterministic fallback doner; confidence `0.0` ve text `[FALLBACK_OCR]` prefix'i tasir.

## Guvenlik ve Gizlilik
- Testler model indirme yapmaz; belge dis servise gonderilmez.
- Production model indirme/cache politikasi henuz ayrica belirlenmeli.

## Testler ve Kabul Kriterleri
- `backend/tests/test_ocr_engine.py` metadata, fallback prediction ve legacy tuple contract testlerini icerir.
- 2026-08-09: `python -m pytest tests/test_ocr_engine.py tests/test_layout_analysis.py tests/test_processing_pipeline.py` -> 13 passed.
- 2026-08-09 real Kraken evidence: `evidence/line_filter_repair/after_lines.json` -> 23 line, `actual_engine=kraken`, `fallback_used=false`.
- 2026-08-09 overlay evidence: `evidence/line_filter_repair/before_overlay.png`, `after_overlay.png`.
- Kanit: `evidence/environment_gate/backend_pytest_task017_ocr_initial.txt` -> 3 passed.
- Full gate: `evidence/environment_gate/doctor_task017_full.txt` -> `DOCTOR_FAILED=0`.

## Kod Kanitlari
- `backend/app/services/document_processing/ocr_engine.py` -> `OttomanOCREngine`, `EasyOCREngine`, `KrakenWSLEngine`, `OCRPageResult`, `OCRLineResult`, `LineFilterConfig`, `filter_ocr_lines`.

## Bilinen Eksikler
- Akademik OCR accuracy halen model/veri kalitesiyle sinirlidir; line filter sadece bos/gurultu/dekorasyon kaynakli false line problemini azaltir.
- Kalici `ocr_results` tablo dolumu OCR review akisi icin ayrica genisletilebilir.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
- 2026-07-28: TASK-017 sirasinda OCR adapter metadata/fallback sozlesmesi ve tests eklendi.
- 2026-08-09: LINE_FILTER_REPAIR ile EasyOCR component filter, OCR line quality filter, bbox refinement, page_id payload ve overlay evidence eklendi.
