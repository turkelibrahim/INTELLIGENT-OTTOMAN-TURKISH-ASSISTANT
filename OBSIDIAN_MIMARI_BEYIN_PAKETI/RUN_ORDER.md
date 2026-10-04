# Osmanlıca Belge Asistanı — Uçuşa Geçiş Sırası

Bu paket, projeyi mevcut durumundan çalışan ve doğrulanmış bir yayın adayına taşımak için sıralı ajan promptları içerir.

## Kullanım

1. Önce mevcut `OBSIDIAN_MIMARI_BEYIN_PAKETI.zip` içeriğini proje köküne yerleştir.
2. Bu paketteki `PROMPTS` klasörünü de proje köküne kopyala.
3. İlk ajana `00_MASTER_ORCHESTRATOR.md` ver.
4. Orkestratör, `Task_Queue.md` ve kanıtlara göre doğru promptu seçer.
5. Manuel çalıştıracaksan promptları numara sırasıyla kullan.
6. Bir prompt `PASS` olmadan sonraki geliştirme promptuna geçme.
7. `PARTIAL`, `FAIL`, `BLOCKED` veya `REBOOT_REQUIRED` sonucunda aynı aşamanın düzeltme görevi oluşturulur.

## Aşamalar

- 00 — Ana orkestrasyon
- 01 — Kurtarma ve gerçek başlangıç fotoğrafı
- 02 — SRS ve gereksinim izlenebilirliği
- 03 — Windows/WSL/Python/GPU ortam kapısı
- 04 — Mimari iskelet ve modül sınırları
- 05 — Veritabanı, dosya saklama ve sürümleme
- 06 — Belge yükleme ve görüntü ön işleme
- 07 — Layout, satır tespiti ve OCR
- 08 — OCR düzeltme çalışma alanı
- 09 — Osmanlıca transliterasyon
- 10 — Günümüz Türkçesi, sadık aktarım ve özet
- 11 — NER, tarih normalizasyonu ve sözlük
- 12 — RAG sohbet ve kaynak gösterimi
- 13 — Kimlik, yetki, güvenlik ve audit
- 14 — Ölçüm, deney ve otomatik test kapısı
- 15 — Bütünleşik UI/UX
- 16 — Dışa aktarma ve raporlama
- 17 — Performans, güvenilirlik ve hata kurtarma
- 18 — Release Candidate kapısı
- 19 — Yerel/kurumsal yayınlama ve uçuş
- 20 — Yayın sonrası doğrulama ve bakım

## Kesin Kural

Bir sonraki prompt yalnız önceki aşamanın kabul kriterleri kanıtlarla karşılandıysa çalıştırılır.
