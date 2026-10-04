# 09 — Arap Harfli Osmanlıcadan Latin Harfli Osmanlıcaya Transliterasyon

MODE: EXECUTE

Rolün: Osmanlı Türkçesi NLP Mühendisi + Dil Teknolojileri Uzmanı + Test Mühendisi.

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

OCR sonucunu modern Türkçeye çevirmeden önce, kaynak satır bağlantısını koruyan Latin harfli Osmanlıca çıktıya dönüştür.

## Yapılacaklar

1. Transliterasyon ile modernleştirmeyi kesin biçimde ayır.
2. Kural, sözlük ve yapılandırılabilir model/LLM yaklaşımını servis arkasında birleştir.
3. Harf eşleme, ligatür, noktalama, sayı, tarih, unvan ve özel ad kurallarını test et.
4. Eksik ünlü ve çoklu okumalarda tek doğru uydurma:
   - adaylar
   - gerekçe
   - belirsizlik seviyesi
   üret.
5. Her Latin satırı kaynak OCR satırına bağla.
6. Kullanıcı seçimi ve düzeltmesini sürümle.
7. Korunması gereken özel ad/tarih/unvan davranışını ekle.
8. Doğrulanmış küçük paralel veri kümesi oluştur veya mevcut izinli fixture'ı kullan.
9. CER/WER/chrF ve insan değerlendirmesi için ölçüm ekle.
10. Prompt veya kural sürümünü kaydet.

## Kabul Kriterleri

- OCR ve Latin çıktı ayrı saklanıyor.
- Kaynak satıra geri gidilebiliyor.
- Belirsiz okuma açıkça gösteriliyor.
- Düzeltme geçmişi mevcut.
- Test fixture'larında ölçüm raporu var.
