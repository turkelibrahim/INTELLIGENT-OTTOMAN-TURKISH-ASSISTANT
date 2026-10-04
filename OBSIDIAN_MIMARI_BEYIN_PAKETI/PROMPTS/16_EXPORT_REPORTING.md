# 16 — Dışa Aktarma, Akademik Rapor ve Tekrarlanabilir Sonuç Paketi

MODE: EXECUTE

Rolün: Backend/Reporting Mühendisi + Veri Sözleşmesi Uzmanı.

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

Belge sonuçlarını insan tarafından okunabilir ve makine tarafından işlenebilir biçimde güvenli dışa aktar.

## Yapılacaklar

1. UTF-8 TXT çıktıları:
   - ham OCR
   - düzeltilmiş OCR
   - Latin transliterasyon
   - modern Türkçe
   - özet
2. Yapısal JSON:
   - belge/sayfa/satır
   - koordinatlar
   - skorlar
   - model/sürüm
   - düzeltme durumu
   - varlıklar
   - citation'lar
3. Varlık CSV çıktısı.
4. Mevcut kapsam uygunsa DOCX/PDF akademik rapor.
5. Rapor içinde:
   - kaynak belge meta verisi
   - işlem aşamaları
   - model sürümleri
   - metrikler
   - uyarılar
   - doğrulama durumu
6. Dosya adlandırma, path güvenliği ve izin kontrolü.
7. Büyük çıktı ve başarısız üretim için kontrollü hata.
8. Şema testleri ve örnek export fixture'ları.
9. Export işlemini audit loguna yaz.

## Kabul Kriterleri

- TXT ve JSON zorunlu çıktıları doğru.
- JSON şeması doğrulanıyor.
- Kaynak ve model izlenebilirliği korunuyor.
- Yetkisiz export engelleniyor.
- UTF-8/RTL içerik bozulmuyor.
