---
type: lint_report
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - docs/wiki
tags: [lint, wiki, recover]
---

# Lint Report

**Ozet:** BASELINE-001 sirasinda `docs/wiki/` icin wikilink lint tekrar calisti. 42 Markdown dosyasi, 329 wikilink ve 0 missing hedef bulundu. Kok `AGENTS.md` artik gercek dosya olarak dogrulandigi icin onceki partial blokaj guncel degildir.

**Kutuphaneler:** PowerShell.

**Baglantilar:** [[Index]], [[Task_Queue]], [[Open_Questions]], [[Current_State]]

## Bulgular
- VERIFIED: `docs/wiki/` altinda yalniz Markdown dosyalari var.
- VERIFIED: Bariz kirik Obsidian link hedefi yok.
- VERIFIED: Yetim sayfa bulunmadi.
- VERIFIED: Istenen ana Graph View baglanti zincirleri dogrulandi.
- VERIFIED: Proje kokunde `AGENTS.md` gercek dosya olarak okunabildi.
- PARTIAL: `OBSIDIAN_MIMARI_BEYIN_PAKETI/docs/wiki/` eski/yanlis wiki olarak tespit edildi; kullanici onayi olmadan silinmedi.
- VERIFIED: Kod kaniti olmayan iddialar DOĞRULANMADI, planned veya partial olarak etiketlendi.

## Dogrulanan Ana Zincirler
- [[Index]] -> [[Current_State]]
- [[Index]] -> [[Task_Queue]]
- [[Index]] -> [[Architecture_Map]]
- [[Architecture_Map]] -> [[Document_Ingestion]]
- [[Document_Ingestion]] -> [[Image_Preprocessing]]
- [[Image_Preprocessing]] -> [[Layout_Analysis]]
- [[Layout_Analysis]] -> [[OCR_Service]]
- [[OCR_Service]] -> [[OCR_Review_Flow]]
- [[OCR_Service]] -> [[Transliteration_Service]]
- [[Transliteration_Service]] -> [[Modernization_Service]]
- [[Modernization_Service]] -> [[NER_Service]]
- [[Modernization_Service]] -> [[RAG_Chat_Service]]
- [[RAG_Chat_Service]] -> [[Citation_Flow]]
- [[Evaluation_Service]] -> [[OCR_Service]]
- [[Evaluation_Service]] -> [[NER_Service]]

## BASELINE-001 LINT
- Komut kaniti: `evidence/recover_baseline/wiki_lint_links.txt`.
- Sonuc: 0 missing wikilink.

## TASK-008 LINT
- Komut kaniti: `evidence/requirements_traceability/wiki_lint_links.txt`.
- Sonuc: 45 Markdown dosyasi, 0 missing wikilink.
- Yeni dugumler [[Requirements_Traceability_Matrix]], [[Acceptance_Criteria_Map]] ve [[ADR-001_NextJS_Frontend]] [[Index]] uzerinden erisilebilir.

## Sonraki LINT Isleri
- Eski `OBSIDIAN_MIMARI_BEYIN_PAKETI/docs/wiki/` icin kullanici karari alinmali.
- Zorunlu sayfa basliklari tum modullerde daha ayrintili denetlenmeli.
