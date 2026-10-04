# Web Research Report — 2026-08-07

## En uygun açık OCR/HTR kaynağı
**OpenITI MAKHZAN Ottoman Lines**: 3,654 line-level image/text pair; 3,512 train + 142 OOD test; yaklaşık 566 MB. Metin Osmanlı Türkçesi Arap harfli ground truth'tur. Dataset kartına göre örneklerin yaklaşık %95'i Naskh'tır.

## Full page/layout
**OpenITI MAKHZAN 2026.1.2**: yaklaşık 1,497 sayfa, 208 doküman, 7 dil, ~20 script/mixed script; ALTO/XML + PNG/JPG. Zenodo ana ZIP'i yaklaşık 6.1 GB. Osmanlı Türkçesinde 241 manuscript page; raporlanan script dağılımında 229 Naskh, 5 Ta'liq, 5 Divani ve 2 Other vardır.

## NLP destek kaynakları
- Ottoman place-name gazetteer: ~44.8k Osmanlıca Arap harfi -> transliterasyon eşleşmesi.
- BUCOLIN OTC: ~1.21M tarihî Türkçe/Osmanlıca translitere satır.
- HisTR: 25,306 NER satırı.
- OTA-BOUN ve DUDU: morfoloji/sözdizimi desteği.
- LATOC v5: 143 kitap / 13.25M kelimeyi tarif eder; telif nedeniyle raw metni Zenodo paketi içinde dağıtmaz, pipeline sağlar.

## Benchmark referansları
- Transkribus OttomanTurkish_Print_1: 386 training page, 23,758 line, 180,854 word, 7.2% CER, model ID 52502.
- Transkribus OttomanTurkish_generic: 789 training page, 25,480 line, 201,096 word, 11.6% CER, model ID 56496.

## Gerçek eksik
Açık veri Naskh ağırlıklı. Rika/Riq'a, Divani ve özellikle Siyakat için açık ve insan doğrulamalı yeterli miktarda Osmanlıca GT bulunmadığından bu stillerde üretim kalitesi için ayrıca hakları temiz, insan doğrulamalı veri toplama gerekir. Paket bunu `05_real_sources/review_queue/` ile açıkça ayırır; eksikliği sentetik veriyle gizlemez.
