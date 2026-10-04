---
type: module
status: verified
last_verified: 2026-08-09
owners: []
source_paths:
  - backend/app/services/document_processing/layout.py
test_paths:
  - backend/tests/test_layout_analysis.py
tags: [layout, ocr, task-016]
---

# Layout Analysis

**Ozet:** TASK-016 ile OpenCV tabanli satir bolgesi tespiti icin `LayoutAnalyzer` servisi eklendi. 2026-08-09 line filter repair ile runtime OCR hattinda EasyOCR/Kraken line filtering, component suppression ve bbox ink-refinement eklendi. Fixture testlerinde iki sutunlu sayfadan dort satir bolgesi koordinatla cikarildi ve okuma sirasi dogrulandi.

**Kutuphaneler:** OpenCV, NumPy.

**Baglantilar:** [[Planned_Features]], [[RTL_Reading_Order]], [[OCR_Service]], [[Document_Ingestion]]

## Sorumluluklar
- On islenmis veya ham sayfadan line-like bolgeler tespit etmek.
- Satir bbox koordinatlarini image coordinate sisteminde dondurmek.
- Runtime OCR satirlarinda bos/gurultu/dekoratif/header/footer komponentlerini filtrelemek.
- Genis satir bbox'larinda izole marj kumelerini ink projection ile temizlemek.

## Girdiler
- OpenCV `np.ndarray` image.

## Ciktilar
- `LineRegion` listesi: `x`, `y`, `width`, `height`, `order_index`, `column_index`.

## Bagimliliklar
- `cv2.threshold`, morphology close, contour detection.

## Veri Akisi
- Sayfa goruntusu -> `LayoutAnalyzer.detect_lines` -> `LineRegion` sirali liste -> OCR line input.

## Hata Durumlari
- Cok karmasik el yazmasi veya dekoratif sayfa layout'unda heuristic eksik kalabilir; fixture kapsami sinirlidir.

## Guvenlik ve Gizlilik
- Belge icerigi dis servise gonderilmez; local image array uzerinde calisir.

## Testler ve Kabul Kriterleri
- `backend/tests/test_layout_analysis.py` line region coordinates, RTL order ve LTR order fixture testlerini icerir.
- `backend/tests/test_ocr_engine.py` line filter, component filter ve bbox refinement regresyon testlerini icerir.
- 2026-08-09 kanit: `python -m pytest tests/test_ocr_engine.py tests/test_layout_analysis.py tests/test_processing_pipeline.py` -> 13 passed.
- 2026-08-09 real overlay kaniti: `evidence/line_filter_repair/before_overlay.png`, `after_overlay.png`.
- Kanit: `evidence/environment_gate/backend_pytest_task016_layout_initial.txt` -> 3 passed.
- Full gate: `evidence/environment_gate/doctor_task016_full.txt` -> `DOCTOR_FAILED=0`.

## Kod Kanitlari
- `backend/app/services/document_processing/layout.py` -> `LayoutAnalyzer`, `LineRegion`.
- `backend/app/services/document_processing/ocr_engine.py` -> `LineFilterConfig`, `analyze_line_candidate`, `filter_ocr_lines`, `refine_line_bbox_to_text_ink`, `is_non_ottoman_component_text`.

## Bilinen Eksikler
- Runtime OCR payload bbox'lari filtreli uretilir; kalici DB `ocr_results` entegrasyonu yine OCR review akisi kapsaminda ayrica genisletilebilir.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda planned olarak olusturuldu.
- 2026-07-28: TASK-016 sirasinda layout analyzer ve fixture testleri eklendi.
- 2026-08-09: LINE_FILTER_REPAIR ile backend OCR line filtering, component suppression, bbox refinement ve real overlay evidence eklendi.
