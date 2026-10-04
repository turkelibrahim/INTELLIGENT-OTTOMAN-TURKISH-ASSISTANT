---
type: gap_register
status: verified
last_verified: 2026-08-02
owners: []
source_paths:
  - docs/wiki/08_Testing/Requirements_Traceability_Matrix.md
  - docs/wiki/08_Testing/Acceptance_Criteria_Map.md
  - evidence/verify_live_state_20260802/FINAL_VERIFY_LIVE_STATE_AND_EVALUATION_REPORT.md
test_paths: []
tags: [srs, quality, ocr, gap]
---

# SRS Gap Register

**Ozet:** SRS ve kabul haritalarinda sayisal OCR kalite esigi bulunamayan gereksinim bosluklarini kaydeder. Bu sayfa [[Evaluation_Service]], [[Test_Strategy]] ve [[Current_State]] ile baglantilidir. Esik uydurulmaz; gercek metrikler raporlanir.

**Kutuphaneler:** Yok.

**Baglantilar:** [[Evaluation_Service]], [[Test_Strategy]], [[Current_State]], [[Requirements_Traceability_Matrix]]

## GAP-SRS-OCR-QUALITY-001 - OCR Kabul Esigi Eksik

- **Durum:** OPEN
- **Tarih:** 2026-08-02
- **Kapsam:** OCR kalite kabul/ret karari icin sayisal CER/WER/line-F1 esigi.
- **Kanit:** `docs/wiki/08_Testing/Requirements_Traceability_Matrix.md` icinde FR-EVAL-001 CER/WER hesaplamayi ister; sayisal kabul esigi belirtmez. `docs/wiki/08_Testing/Acceptance_Criteria_Map.md` icinde de sayisal OCR quality threshold bulunmadi.
- **Canli Metrikler:** Strict CER `0.4648786717752235`, strict WER `0.7807757166947723`, line F1 `0.3371824480369515`.
- **Karar:** Esik uydurulmadigi icin teknik pipeline PASS, OCR accuracy `FAIL_NEEDS_MODEL_IMPROVEMENT`, proje kabul karari `PARTIAL`.
- **Sonraki Adim:** Urun/akademik kabul icin hedef CER/WER/line-F1 esikleri kullanici veya SRS tarafindan tanimlanmali.
