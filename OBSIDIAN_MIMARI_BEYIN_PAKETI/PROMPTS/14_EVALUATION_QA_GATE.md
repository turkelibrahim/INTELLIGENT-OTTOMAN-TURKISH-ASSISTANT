# 14 — Değerlendirme, Deney Yönetimi ve Otomatik QA Kapısı

MODE: EXECUTE

Rolün: QA Mimarı + ML Değerlendirme Mühendisi + Test Otomasyon Uzmanı.

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

Tüm temel işleme hattının ölçülebilir, tekrarlanabilir ve otomatik doğrulanabilir olmasını sağla.

## Yapılacaklar

1. Unit, integration, contract, security, UI smoke ve end-to-end test katmanlarını haritala.
2. OCR için CER/WER.
3. Layout için mümkünse IoU/F1.
4. Transliterasyon için CER/WER/chrF ve insan puanı.
5. NER için precision/recall/F1.
6. RAG için citation coverage, answerability ve desteksiz cevap oranı.
7. Modernleştirme için anlam koruma ve bilgi eklememe kontrol seti.
8. Her deneyde veri kümesi, model, parametre, donanım, süre ve sonuç kaydı oluştur.
9. Tek komutla çalışan test/quality gate scripti oluştur.
10. Test fixture'larını küçük, lisanslı/izinli ve repoda güvenli biçimde tut.
11. Başarısız örnekleri rapordan çıkarma.
12. Coverage ve kritik yol test kapsamını raporla.

## Kabul Kriterleri

- Tek komut kalite kapısı çalışıyor.
- Kritik ana akış için E2E test var.
- Metrikler yeniden üretilebilir.
- Başarısız testler görev durumunu engelliyor.
- Test kanıtları `evidence/qa_gate/` altında.
