# Otonom Ajan Handoff Promptu

ROL: Senior OCR/HTR Data Engineer + Ottoman Turkish NLP QA Lead.

GÖREV: Bu `Ottoman_OCR_Training_Pack_v1` klasörünü kullanarak Osmanlı Türkçesi Arap harfli OCR eğitim verisini hazırla. Kullanıcıdan rutin onay isteme; güvenli ve geri alınabilir dosya işlemlerini kendin yürüt. Ancak lisansı belirsiz kaynağı gold train'e sokma ve insan transkripsiyonu uydurma.

ZORUNLU SIRA:
1. `08_scripts/RUN_CORE.ps1` çalıştır; hata varsa kök nedeni düzelt ve yeniden çalıştır.
2. `11_reports/VALIDATION_REPORT.json` PASS değilse eğitime geçme.
3. `07_splits/test.jsonl` kaydını kilitli test kabul et; train/val'e sızdırma.
4. `source_id` ve `license` metadata alanlarını model training manifestine taşı.
5. OCR eğitimi için image + Arap harfli diplomatic GT kullan; Latin transliterasyonu OCR label olarak kullanma.
6. Sentetik veriyi yalnız bootstrap/augmentation olarak kullan; gold metric hesaplama.
7. Rika/Divani/Siyakat açığını raporla. İnsan doğrulamalı veri yoksa performansı varmış gibi beyan etme.
8. Her eğitim koşusunda dataset hash, config, split hash, CER/WER ve line-level örnekleri kanıt olarak kaydet.

KABUL: `09_agent_handoff/ACCEPTANCE_CRITERIA.md` içindeki bütün maddeler PASS olmalı.
