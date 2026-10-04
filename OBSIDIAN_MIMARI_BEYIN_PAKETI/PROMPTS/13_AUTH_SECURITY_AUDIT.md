# 13 — Kimlik Doğrulama, Yetkilendirme, Güvenlik ve Audit

MODE: EXECUTE

Rolün: Uygulama Güvenliği Mühendisi + Backend Güvenlik Uzmanı.

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

Kullanıcı, Uzman ve Yönetici rollerini; belge izolasyonunu; güvenli dosya işlemlerini; secret yönetimini ve audit kayıtlarını uçuş seviyesine getir.

## Yapılacaklar

1. Oturum açma/kapatma ve zaman aşımı davranışını doğrula.
2. Parola saklama ve hata mesajlarını güvenli hale getir.
3. Kullanıcı/Uzman/Yönetici yetki matrisini uygula.
4. IDOR ve başka kullanıcının belge/verisine erişim testleri ekle.
5. Dosya yükleme için path traversal, zip bomb benzeri kaynak tüketimi, MIME spoof ve boyut sınırı kontrollerini doğrula.
6. API varsa auth/role middleware'i uygula.
7. Secret'ların log, hata ve UI'de maskelendiğini doğrula.
8. Kritik değişiklik, silme, model seçimi ve düzeltme işlemlerini audit et.
9. Rate limit veya kötüye kullanım korumasını risk düzeyine göre ekle.
10. Bağımlılık ve konfigürasyon güvenlik taraması çalıştır.
11. Kritik bulguları düzeltmeden uçuş kapısına geçme.

## Kabul Kriterleri

- Roller ve belge izolasyonu testli.
- Secret sızıntısı yok.
- Yükleme saldırı testleri mevcut.
- Audit kritik olayları kapsıyor.
- Açık P0/P1 güvenlik bulgusu yok.
