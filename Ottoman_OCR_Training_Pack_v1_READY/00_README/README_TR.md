# Ottoman OCR Training Pack v1 — Hazır Veri Toplama ve Eğitim Paketi

Bu paket **Osmanlı Türkçesi Arap harfli OCR/HTR** projesi için hazırlanmıştır. Klasör yapısı istenen yapıyla aynıdır ve üç veri katmanı içerir:

1. **Gold / gerçek görüntü + insan doğrulamalı metin:** OpenITI MAKHZAN Ottoman line-level veri seti. Eğitim ve test için ana kaynak budur.
2. **Destek NLP verileri:** Osmanlıca yer adları, tarihî Türkçe metin, NER ve UD treebank veri setleri. Bunlar OCR görüntü eğitimi yerine sözlük, post-correction, dil modeli, NER ve morfoloji için kullanılır.
3. **Sentetik bootstrap verisi:** Bu ZIP'in içinde hazır gelir. Alfabe, bağlamsal karakter örnekleri, satır örnekleri ve layout sayfaları içerir. **Gerçek gold verinin yerine geçmez.**

## En hızlı kullanım (Windows)
PowerShell'i bu klasörde açıp:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\08_scripts\RUN_CORE.ps1
```

CORE profili yaklaşık **0.8–1+ GB** indirme yapabilir (Hugging Face sürümlerine göre değişebilir) ve ana OCR line datasetini materyalize eder.

Daha sonra, sayfa + ALTO/XML layout verilerini de indirmek için:

```powershell
.\08_scripts\RUN_FULL.ps1
```

FULL profili OpenITI MAKHZAN'ın yaklaşık **6.1 GB** arşivini de indirir. Arşiv + açılmış dosyalar + ara dosyalar nedeniyle en az **20–25 GB boş disk** önerilir.

## Kritik kurallar
- OpenITI MAKHZAN/Ottoman Lines lisansı **CC BY-NC-SA**: ticari kullanım için otomatik olarak uygun kabul edilmemelidir.
- CORE içindeki bazı destek metinleri **CC BY-NC 4.0**'dır. Lisanslar `10_sources/sources.csv` ve `10_sources/rights_manifest.csv` içinde ayrı tutulur.
- Upstream `test` split'i **asla train'e karıştırılmaz**.
- Arap harfli ground truth, Latin transliterasyondan ayrı tutulur.
- Sentetik veri, test/benchmark için kullanılmaz.
- `license: other`/belirsiz kaynaklar gold train havuzuna otomatik eklenmez.

## Sonuç dosyaları
CORE tamamlandığında özellikle şunları kontrol edin:
- `03_lines/openiti_makhzan_ottoman_lines/manifests/all.jsonl`
- `07_splits/train.jsonl`, `val.jsonl`, `test.jsonl`
- `06_annotations/kraken/`
- `02_words/generated/word_lexicon.tsv`
- `11_reports/VALIDATION_REPORT.json`
