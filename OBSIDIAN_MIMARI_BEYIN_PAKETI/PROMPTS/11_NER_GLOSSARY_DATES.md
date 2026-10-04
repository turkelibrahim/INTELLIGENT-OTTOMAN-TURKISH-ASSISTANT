# 11 — Varlık Çıkarımı, Tarih Normalizasyonu ve Arkaik Sözlük

MODE: EXECUTE

Rolün: NLP/NER Mühendisi + Osmanlıca Sözlük Sistemleri Uzmanı.

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

Latin ve modern metin üzerinde kişi, yer, kurum, tarih, unvan ve arkaik kelimeleri çıkarıp kullanıcı düzeltmesine aç.

## Yapılacaklar

1. PER, LOC, ORG, MISC ve gerekli alan etiketlerini yapılandır.
2. Varlıkları metin konumu, kaynak satır ve skorla sakla.
3. Kullanıcı ekleme/silme/etiket değiştirme akışını sürümle.
4. Hicrî, Rûmî ve Miladî tarihlerin ham değerini koru; dönüşüm yöntemini açıkla.
5. Aynı varlığın farklı yazımlarını kanonik kayda bağlama altyapısı ekle.
6. Sözlük kaydı için kelime, varyant, anlam, tür, örnek, kaynak ve onay alanlarını uygula.
7. Arkaik kelime hover/kart görünümü için servis API'si veya UI verisi üret.
8. NER skoru kesin doğruluk gibi gösterilmesin.
9. Precision, recall ve F1 testleri ekle.
10. OCR hatasının NER'e etkisini raporla.

## Kabul Kriterleri

- Varlıklar kaynak konumla bağlı.
- Kullanıcı düzeltmeleri saklanıyor.
- Ham tarih kaybolmuyor.
- Sözlük kaynak ve onay bilgisi içeriyor.
- NER değerlendirme raporu mevcut.
