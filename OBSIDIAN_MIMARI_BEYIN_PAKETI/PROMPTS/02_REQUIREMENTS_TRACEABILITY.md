# 02 — SRS Gereksinim İzlenebilirliği ve Kapsam Sabitleme

MODE: PLAN

Rolün: Kıdemli Gereksinim Mühendisi + Sistem Mimarı + QA Lideri.

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

SRS'deki bütün MUST/SHOULD gereksinimlerini gerçek codebase, testler ve görevlerle eşleştir. Uygulanmamış gereksinimleri görünür hale getir ve uçuş için zorunlu kapsamı sabitle.

## Yapılacaklar

1. SRS, README, kullanıcı kararları ve mevcut wiki düğümlerini oku.
2. Her FR/DR/MLR/NFR gereksinimi için:
   - Durum: implemented / partial / planned / blocked / out-of-scope
   - Kod kanıtı
   - Test kanıtı
   - İlgili wiki düğümü
   - İlgili görev ID
   kaydet.
3. MVP uçuş kapısını MUST gereksinimleri üzerinden tanımla.
4. Kullanıcı talimatıyla kaldırılmış kapsamları açıkça işaretle.
5. Dış repo kullanmama kuralını mimari kısıt olarak kaydet.
6. En kritik kullanıcı akışını uçtan uca kabul senaryosuna dönüştür.
7. `Acceptance_Criteria_Map.md` ve gereksinim izlenebilirlik matrisi oluştur.
8. Görev kuyruğunu bağımlılık sırasına göre yeniden düzenle.
9. Henüz kod değiştirme.

## Kabul Kriterleri

- Tüm MUST gereksinimler görev ve testlerle eşlenmiş.
- Uçuş için kesin kapsam tanımlanmış.
- Belirsiz gereksinimler `Open_Questions` içinde.
- Sonraki prompt için ortam ön koşulları açık.
