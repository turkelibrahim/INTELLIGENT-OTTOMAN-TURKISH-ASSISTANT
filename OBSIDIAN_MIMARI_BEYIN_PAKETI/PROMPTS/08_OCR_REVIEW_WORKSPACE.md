# 08 — OCR İnceleme, Satır/Görüntü Senkronizasyonu ve İnsan Doğrulaması

MODE: EXECUTE

Rolün: Senior Frontend/Streamlit Mühendisi + UX Uzmanı + Veri Sürümleme Mühendisi.

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

Kullanıcının satır görüntüsünü, ham OCR tahminini ve düzeltmesini güvenli biçimde yönetebildiği çalışma alanını tamamla.

## Yapılacaklar

1. Sayfa görüntüsü, zoom, satır kutusu ve seçili satır senkronizasyonunu uygula.
2. Arap harfli metin alanını RTL biçimde göster.
3. Ham tahmini değişmez tut; düzeltmeyi ayrı sürüm olarak kaydet.
4. Kullanıcı, zaman, eski değer ve yeni değer audit kaydı oluştur.
5. Düşük güvenli satır filtresi ve inceleme kuyruğu ekle.
6. Satır kutusu ekleme/silme/düzeltme akışını güvenli yap.
7. Kaydedilmemiş değişiklik uyarısı ekle.
8. Uzman doğrulama durumunu destekle.
9. Klavye ile temel gezinme ve odak davranışını test et.
10. UI testleri veya servis seviyesinde etkileşim testleri ekle.

## Kabul Kriterleri

- Satır görüntüsü ve metin senkron.
- Düzeltme geçmişi kaybolmuyor.
- Ham OCR sonucu korunuyor.
- Düşük güvenli satırlar bulunabiliyor.
- RTL düzen kullanılabilir.
