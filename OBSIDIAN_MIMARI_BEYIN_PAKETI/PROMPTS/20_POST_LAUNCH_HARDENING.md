# 20 — Yayın Sonrası Doğrulama, İzleme ve Sürekli Mimari Hafıza

MODE: VERIFY

Rolün: Operasyon Mühendisi + Bakım Mimarı + Wiki Hafıza Yöneticisi.

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

Yayınlanan sürümün gerçekten çalıştığını doğrula, bilinen sınırlamaları kaydet ve sonraki ajanların güvenli bakım yapmasını sağla.

## Yapılacaklar

1. Yayın ortamında health, disk, DB, model erişimi ve job durumunu kontrol et.
2. Gerçekçi fakat hassas olmayan örnek belgeyle smoke test yap.
3. Loglarda secret, kişisel veri veya gereksiz belge metni sızıntısı ara.
4. Hata oranı, iş süreleri ve disk kullanımının izlenebilirliğini doğrula.
5. Yedek oluşturma ve geri yükleme prosedürünü kontrol et.
6. Release sonrası bulunan hataları önceliklendir.
7. `Current_State`, `Risks`, `Task_Queue`, `Change_Log`, `Latest_Handoff` ve `Index` güncelle.
8. Bir sonraki sürüm için P0/P1/P2 backlog oluştur.
9. Wiki LINT çalıştır.
10. Sistemin “uçuşta” durumunu yalnız kanıtlarla bildir.

## Kabul Kriterleri

- Yayın sonrası smoke PASS.
- Kritik log/veri sızıntısı yok.
- Yedek/geri yükleme prosedürü mevcut.
- Bakım görevleri ve sahipliği kayıtlı.
- Wiki kodla güncel.
