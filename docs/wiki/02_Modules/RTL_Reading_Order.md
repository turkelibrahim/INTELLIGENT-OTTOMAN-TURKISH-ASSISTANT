---
type: module
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/services/document_processing/layout.py
test_paths:
  - backend/tests/test_layout_analysis.py
tags: [rtl, layout, task-016]
---

# RTL Reading Order

**Ozet:** TASK-016 ile sagdan sola okuma sirasi `LayoutAnalyzer.order_boxes` icinde testlenebilir hale getirildi. Iki sutunlu fixture'da RTL sirasi sag sutun yukaridan asagi, sonra sol sutun yukaridan asagi olarak PASS oldu.

**Kutuphaneler:** OpenCV, NumPy.

**Baglantilar:** [[Layout_Analysis]], [[OCR_Service]]

## Sorumluluklar
- Satir kutularini Osmanlica/RTL belge okuma sirasina gore siralamak.

## Girdiler
- Satir bbox listesi veya image.

## Ciktilar
- `LineRegion.order_index` ve `LineRegion.column_index`.

## Bagimliliklar
- `LayoutAnalyzer._cluster_columns`.

## Veri Akisi
- Detected boxes -> column clustering -> RTL column sort -> top-down line sort.

## Hata Durumlari
- Karma sayfa tasarimi, tablo ve marjinal notlarda heuristic dogruluk sinirlidir.

## Guvenlik ve Gizlilik
- Local koordinat siralama; dis servis yok.

## Testler ve Kabul Kriterleri
- RTL fixture test: `test_rtl_reading_order_is_right_column_then_left_column_top_down`.
- LTR kontrol testi: `test_ltr_reading_order_is_left_column_then_right_column_top_down`.
- Kanit: `evidence/environment_gate/backend_pytest_task016_layout_initial.txt` -> 3 passed.

## Kod Kanitlari
- `backend/app/services/document_processing/layout.py` -> `LayoutAnalyzer.order_boxes`.

## Bilinen Eksikler
- OCR line storage ve review UI entegrasyonu henuz yok.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda planned olarak olusturuldu.
- 2026-07-28: TASK-016 sirasinda RTL order fixture testleri eklendi.
