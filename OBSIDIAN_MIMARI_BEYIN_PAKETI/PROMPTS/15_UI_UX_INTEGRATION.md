# 15 — Bütünleşik Streamlit/UI Kullanıcı Deneyimi

MODE: EXECUTE

Rolün: Senior Streamlit/Frontend Mühendisi + Erişilebilirlik Uzmanı + Ürün Tasarımcısı.

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

Bütün servisleri tek ve anlaşılır belge çalışma alanında birleştir; kullanıcının uçtan uca akışı kaybolmadan tamamlamasını sağla.

## Ana Ekranlar

- Giriş
- Ana panel
- Belge yükleme sihirbazı
- Belge çalışma alanı
- Ön işleme karşılaştırması
- OCR editörü
- OCR/Latin/Modern üçlü görünüm
- Analiz ve sözlük
- Belge sohbeti
- Değerlendirme
- Yönetim
- Dışa aktarma

## Yapılacaklar

1. Durum makinesiyle UI aşamalarını senkronize et.
2. Yetkisiz ve hazır olmayan aksiyonları engelle.
3. Uzun işlemlerde aşama/progress ve yeniden deneme göster.
4. Teknik stack trace yerine kullanıcı mesajı, logda korelasyon ID kullan.
5. RTL ve LTR metinleri doğru yönlerde göster.
6. Görüntü/satır/metin/citation senkronizasyonunu tamamla.
7. Düşük güveni renk dışında ikon/metinle göster.
8. Kaydedilmemiş değişiklik ve kritik silme onayı ekle.
9. Klavye erişilebilirliği ve odak görünürlüğünü doğrula.
10. Boş durum, hata durumu ve loading durumlarını test et.
11. Ana kullanıcı yolculuğunu UI smoke/E2E testine bağla.

## Kabul Kriterleri

- Kullanıcı belgeyi yükleyip READY durumuna kadar ilerleyebiliyor.
- Aşama ve hata durumu anlaşılır.
- RTL/LTR doğru.
- Kaynak satıra tıklama çalışıyor.
- Kritik işlemler onaylı.
