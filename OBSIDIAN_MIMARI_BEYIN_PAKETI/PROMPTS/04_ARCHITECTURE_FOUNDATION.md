# 04 — Mimari İskelet, Modül Sınırları ve Durum Makinesi

MODE: EXECUTE

Rolün: Baş Yazılım Mimarı + Python Platform Mühendisi.

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

Codebase'i SRS işleme hattına uygun, test edilebilir ve birbirinden ayrılmış modüller halinde düzenle. Çalışan kodu gereksiz yeniden yazma.

## Yapılacaklar

1. Mevcut yapıyı incele; hedef katmanları belirle:
   - UI
   - uygulama/use-case
   - domain
   - altyapı
   - AI/ML servis adaptörleri
   - persistence
   - test
2. Ana işleme durum makinesini tanımla:
   `UPLOADED → PREPROCESSING → LAYOUT_ANALYSIS → OCR → OCR_REVIEW → TRANSLITERATION → MODERNIZATION → ANALYSIS → READY`
   ve hata/yeniden deneme yollarını ekle.
3. Servis arayüzlerini/protokollerini tanımla; UI'nin doğrudan model veya veritabanı ayrıntılarına bağlanmasını azalt.
4. Yapılandırmayı merkezileştir; gizli değerleri ayır.
5. Hata tiplerini ve korelasyon kimliği yaklaşımını oluştur.
6. Dependency injection veya açık fabrika düzeniyle servis seçimini test edilebilir yap.
7. Mümkün olan en küçük refactor ile mevcut testleri koru.
8. Mimari sınır testleri veya import kuralları ekle.
9. `Architecture_Map`, ilgili ADR'ler ve modül düğümlerini güncelle.

## Kabul Kriterleri

- Ana modüller ve sorumlulukları açık.
- UI, domain ve altyapı bağımlılık yönleri belgeli.
- Durum geçişleri testli.
- Hatalı/izinsiz geçişler reddediliyor.
- Mevcut temel akış kırılmamış.
