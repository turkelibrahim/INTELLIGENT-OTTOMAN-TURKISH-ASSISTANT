# Dataset Card

**Amaç:** Osmanlı Türkçesi Arap harfli belge OCR/HTR, layout analizi ve OCR sonrası dilsel düzeltme için yeniden üretilebilir veri paketi.

**Ana OCR gold veri:** OpenITI MAKHZAN Ottoman Lines — line image + exact Arabic-script transcription.

**Layout kaynağı:** OpenITI MAKHZAN full — page image + line segmentation/transcription in ALTO/XML (FULL profil).

**NLP destek:** Ottoman place-name gazetteer, OTC, HisTR, OTA-BOUN UD, DUDU.

**Sentetik:** Yalnız bootstrap/karakter kapsaması/layout smoke-test amacıyla paket içinde üretilmiştir. Gold değerlendirmeye dahil edilmez.

**Önemli domain gap:** Açık Osmanlıca ground-truth verisinin büyük kısmı Naskh ağırlıklıdır; Riq'a, Divani, Siyakat gibi yazı türleri için insan doğrulamalı ek veri toplamak gerekebilir.
