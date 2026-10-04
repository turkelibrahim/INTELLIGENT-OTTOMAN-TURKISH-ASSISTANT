---
type: operations
status: blocked_external
last_verified: 2026-08-02
owners: [codex]
source_paths:
  - evidence/ground_truth_input_20260802/db_ground_truth_summary.json
  - evidence/ground_truth_input_20260802/annotation_candidate_summary.json
  - evidence/ground_truth_input_20260802/annotation_candidates.csv
test_paths:
  - evidence/ground_truth_input_20260802/annotation_candidate_generation.txt
tags: [ocr, ground-truth, evaluation, blocked-external]
---

# Ground Truth Input Required

**Ozet:** OCR kalite kapisi icin proje icinde insan tarafindan dogrulanmis/kilitlenmis Osmanlica ground-truth bulunamadi. Mevcut proje orneginden 16 satir adayi cikarildi ve insan transkripsiyonu icin bos sablonlar hazirlandi. OCR onerileri yalniz anotasyonu hizlandirmak icindir; kalite etiketi veya ground-truth sayilamaz.

**Kutuphaneler:** EasyOCR, PyTorch, PIL, SQLite.

**Baglantilar:** [[OCR_Service]], [[Evaluation_Service]], [[Ground_Truth_Annotation_Studio]], [[Markdown_Task_Inventory]], [[Current_State]]

## Kanit

- DB taramasi: `evidence/ground_truth_input_20260802/db_ground_truth_summary.json`
- Ayrintili DB envanteri: `evidence/ground_truth_input_20260802/db_inventory.json`
- Satir adaylari CSV: `evidence/ground_truth_input_20260802/annotation_candidates.csv`
- Satir adaylari JSONL: `evidence/ground_truth_input_20260802/annotation_candidates.jsonl`
- Aday uretim ozeti: `evidence/ground_truth_input_20260802/annotation_candidate_summary.json`
- Calistirma ciktisi: `evidence/ground_truth_input_20260802/annotation_candidate_generation.txt`

## Mevcut Sonuc

- Ana uygulama DB: `ground_truth_pages=0`, `ground_truth_lines=0`.
- Yedek uygulama DB: `ground_truth_pages=0`, `ground_truth_lines=0`.
- E2E test DB'lerinde satirlar var, fakat bunlar sentetik test verisi oldugu icin OCR kalite metrigi icin kullanilmadi.
- Hazirlanan kaynak gorsel: `backend/uploads/processed/1/page_1_226f233e.png`.
- Hazirlanan satir adayi: 16.
- EasyOCR sayfa confidence: 0.12291728311704861. Bu kalite kabul sonucu degildir.

## Tek Manuel Islem

`evidence/ground_truth_input_20260802/annotation_candidates.csv` dosyasindaki her satir icin `ground_truth_text` alanini kaynak gorselle karsilastirarak insan tarafindan dogrulanmis Osmanlica transkripsiyonla doldur; OCR onerilerini aynen kopyalama; ardindan her satirin `status` alanini `HUMAN_VERIFIED` yap ve dosyayi UTF-8/CSV biciminde kaydet.

## Sonraki Otomatik Adim

Insan dogrulamali CSV hazirlandiginda validator/import ve kalite kapisi calistirilir; CER, WER, satir precision, recall ve F1 gercek ground-truth uzerinden raporlanir.
