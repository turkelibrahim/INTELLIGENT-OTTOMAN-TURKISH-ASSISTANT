# 06 — Belge Yükleme, Doğrulama, PDF Sayfalama ve Görüntü Ön İşleme

MODE: EXECUTE

Rolün: Backend Mühendisi + Görüntü İşleme Uzmanı + Güvenlik Mühendisi.

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

Güvenli belge yükleme ve OCR'a uygun görüntü varyantı üretme akışını uçtan uca tamamla.

## Yapılacaklar

1. JPG, JPEG, PNG, TIFF ve PDF yüklemeyi doğrula.
2. Uzantı, MIME, dosya imzası, boyut, sayfa sayısı ve bozuk dosya kontrolleri uygula.
3. Hash tabanlı yinelenme uyarısı ekle.
4. PDF sayfalarını sıra ve meta veriyi koruyarak ayır.
5. Orijinal dosyayı salt okunur mantıkla koru.
6. Görüntü ön işleme fonksiyonlarını saf ve test edilebilir yap:
   - gri tonlama
   - kontrast/CLAHE
   - gürültü azaltma
   - global/adaptif/Otsu threshold
   - deskew
   - güvenli crop
7. İşlem parametrelerini ve parent varyantı kaydet.
8. En az temiz baskı ve lekeli/eğik sayfa profili oluştur.
9. Önce/sonra karşılaştırma çıktısı üret.
10. Bozuk ve zararlı dosya testleri ekle.

## Kabul Kriterleri

- Desteklenen formatlar doğru kabul ediliyor.
- Sahte uzantı ve bozuk dosya reddediliyor.
- PDF sayfa sırası korunuyor.
- Orijinal dosya değişmiyor.
- Ön işleme varyantı ve parametreleri izlenebilir.
- Görsel regresyon veya ölçülebilir kalite testi mevcut.
