# 07 — Layout, RTL Okuma Sırası, Satır Tespiti ve OCR Hattı

MODE: EXECUTE

Rolün: OCR/HTR Mühendisi + Bilgisayarlı Görü Uzmanı + ML Platform Mühendisi.

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

Ön işlenmiş sayfadan satır bölgelerini çıkarıp sağdan sola doğru sırada OCR sonucuna dönüştüren güvenilir hattı tamamla.

## Yapılacaklar

1. Layout ve satır tespit servis arayüzünü doğrula.
2. Satır koordinatlarını görüntü boyutuyla birlikte sakla.
3. RTL okuma sırasını ve çok sütunlu sayfa davranışını test et.
4. Seçilen OCR motorunu adaptör arkasında çalıştır.
5. Model dosyası, sürümü, checksum, lisans ve parametrelerini kayıt altına al.
6. Satır bazında:
   - kaynak görüntü
   - ham Unicode Arap harfli çıktı
   - skor
   - süre
   - model
   - hata
   sakla.
7. OCR başarısızlığına retry ve manuel review yolu ekle.
8. CPU/GPU fallback'i doğrula.
9. Düşük güvenli satır işaretleme eşiği ekle.
10. Küçük doğrulanmış fixture kümesi üzerinde CER/WER baseline çıkar.
11. Dış repo kodu kullanma; yalnız kurulu motorun resmî API'sini kullan.

## Kabul Kriterleri

- Satırlar doğru sıra ve koordinatla saklanıyor.
- OCR Unicode çıktısı kopyalanabilir.
- Model ve parametreler izlenebilir.
- Başarısız iş kontrollü `FAILED` durumuna geçiyor.
- En az bir doğrulanmış sayfada CER/WER raporu mevcut.
