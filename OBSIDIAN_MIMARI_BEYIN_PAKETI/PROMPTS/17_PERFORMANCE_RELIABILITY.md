# 17 — Performans, Güvenilirlik, Kuyruk, Retry ve Kurtarma

MODE: EXECUTE

Rolün: Site Reliability Engineer + Performans Mühendisi + Backend Uzmanı.

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

16 GB RAM ve RTX 4050 hedef ortamında uygulamayı çökmeden, izlenebilir ve tekrar denenebilir biçimde çalıştır.

## Yapılacaklar

1. En pahalı işlem aşamalarını profil et.
2. Çok sayfalı belgede bellek kullanımını sınırla.
3. Uzun OCR/NLP işlerini job mantığıyla yönet.
4. Idempotency ve çift çalıştırma koruması ekle.
5. Retry yapılabilir ve yapılamaz hata sınıflarını ayır.
6. İş iptali ve güvenli yeniden deneme davranışı ekle.
7. Geçici dosya temizliği ve disk kotası davranışını doğrula.
8. Uygulama çökmesi sonrası yarım işlerin kurtarılmasını test et.
9. Loglara korelasyon/job/document ID ekle.
10. Sağlık kontrolü ve hazır olma kontrolü oluştur.
11. Küçük, orta ve sınır boyutlu belge performans ölçümü yap.
12. Performans hedeflerini SRS/ortam gerçekliğine göre belgeleyip aşırı iddiadan kaçın.

## Kabul Kriterleri

- Ana akış bellek taşması olmadan tamamlanıyor.
- Retry idempotent.
- Çökme sonrası yarım iş görünür ve kurtarılabilir.
- Health/doctor kontrolleri çalışıyor.
- Performans kanıt raporu mevcut.
