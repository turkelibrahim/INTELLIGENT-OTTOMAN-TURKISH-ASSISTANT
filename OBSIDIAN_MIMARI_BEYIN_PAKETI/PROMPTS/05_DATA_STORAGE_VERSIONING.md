# 05 — Veritabanı, Dosya Deposu, Sürümleme ve Audit Temeli

MODE: EXECUTE

Rolün: Kıdemli Veri Mimarı + Backend Mühendisi.

## Değişmez Çalışma Kuralları

1. Proje kökündeki `AGENTS.md` bağlayıcıdır. Önce onu ve aşağıdaki hafıza dosyalarını oku:
   - `/docs/wiki/Index.md`
   - `/docs/wiki/00_System/Current_State.md`
   - `/docs/wiki/00_System/Task_Queue.md`
   - `/docs/wiki/00_System/Execution_Lock.md`
   - `/docs/wiki/00_System/Decisions.md`
   - `/docs/wiki/10_Handoffs/Latest_Handoff.md`
2. Sohbet geçmişini tek doğruluk kaynağı kabul etme; kod, test ve wiki kanıtlarını esas al.
3. Başka ajanın aktif kilidi varsa çakışan dosyalara dokunma.
4. Dış GitHub/GitLab deposu klonlama, hazır proje kodu kopyalama veya vendor etme. Gerekli standart bağımlılıklar yalnız resmî paket yöneticilerinden kurulabilir; kaynak, sürüm ve lisans `[[Model_Registry]]` veya ilgili wiki düğümüne yazılır.
5. Orijinal belge ve kullanıcı verilerinin üzerine yazma.
6. Gizli değerleri koda, loga veya wiki'ye açık metin olarak yazma.
7. Değişiklikleri küçük, geri alınabilir ve test edilebilir dilimlerde yap.
8. Test edilmemiş davranışı tamamlanmış sayma.
9. Görev kapsamı dışında refactor yapma.
10. Gerçek hata kodlarını ve başarısız testleri saklama.
11. Her aşama sonunda:
    - İlgili modül düğümlerini,
    - `Current_State.md`,
    - `Task_Queue.md`,
    - `Source_Map.md`,
    - `Change_Log.md`,
    - `Latest_Handoff.md`
    güncelle.
12. `REBOOT_REQUIRED` oluşursa başka kurulum veya geliştirme adımına geçme. Durumu kaydet ve dur.
13. Sonuç yalnız şu değerlerden biri olmalıdır: `PASS`, `PARTIAL`, `FAIL`, `BLOCKED`, `REBOOT_REQUIRED`.

## Zorunlu Sonuç Raporu

```markdown
MODE: ...
TASK: ...

## Sonuç
PASS | PARTIAL | FAIL | BLOCKED | REBOOT_REQUIRED

## Okunan Hafıza ve Kaynaklar

## Başlangıç Durumu

## Yapılan Değişiklikler
Yalnız gerçekten yapılanlar.

## Değiştirilen Dosyalar

## Çalıştırılan Komutlar

## Test Sonuçları
| Test | Sonuç | Kanıt |
|---|---|---|

## Kabul Kriterleri
- [ ] ...

## Güvenlik ve Veri Bütünlüğü Kontrolü

## Kalan Hatalar ve Blokajlar
Gerçek hata mesajı/kodu ile.

## Wiki Güncellemeleri

## Geri Alma Bilgisi

## Sonraki Kesin Adım
Bir sonraki prompt numarası ve ilk yapılacak işlem.

## Kanıt Dosyaları
Tam dosya yolları.
```

## Amaç

Belge, sayfa, işleme işi, görüntü varyantı, OCR sonucu, düzeltme, transliterasyon, modernleştirme, varlık, sohbet, kaynak ve audit kayıtlarını güvenli ve izlenebilir biçimde sakla.

## Yapılacaklar

1. Mevcut veri modellerini SRS veri varlıklarıyla karşılaştır.
2. Eksik temel modelleri minimum kapsamla ekle.
3. Orijinal dosya hash'i, değişmezlik ve türetilmiş varyant ilişkisini uygula.
4. Tahmin ve kullanıcı düzeltmesini ayrı sakla.
5. Model adı/sürümü/parametre/checksum bağlantısını sonuçlara ekle.
6. SQLite MVP ise güvenli migration yaklaşımı kur; PostgreSQL geçişini soyutla.
7. Büyük ikili dosyaları dosya deposunda, meta verileri DB'de tut.
8. Audit kaydında aktör, işlem, nesne, eski/yeni değer ve zaman bilgisini sakla.
9. Silme ve retention davranışını test et.
10. Migration, rollback ve veri bütünlüğü testleri ekle.
11. Hassas verilerin loglara sızmadığını kontrol et.

## Kabul Kriterleri

- Ana veri zinciri ilişkilendirilebilir.
- Orijinal dosya üzerine yazılmıyor.
- Kullanıcı düzeltmeleri geri izlenebilir.
- Migration temiz veritabanında çalışıyor.
- Rollback veya kurtarma prosedürü belgeli.
