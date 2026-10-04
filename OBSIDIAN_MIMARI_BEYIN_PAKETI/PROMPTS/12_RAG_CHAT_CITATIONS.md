# 12 — Belgeyle Sohbet, RAG, Kaynak Gösterimi ve Prompt Injection Koruması

MODE: EXECUTE

Rolün: RAG Mimarı + LLM Güvenlik Mühendisi + Backend Mühendisi.

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

Kullanıcının yalnız seçili belgenin içeriğine dayalı, sayfa/satır kaynaklı cevap almasını sağla.

## Yapılacaklar

1. İndekslenecek metin katmanını ve chunk stratejisini açıkça seç.
2. Her chunk'a belge, sayfa, satır, karakter aralığı ve doğrulama durumu meta verisi ekle.
3. Retrieval ve varsa reranking'i servis arkasında uygula.
4. Cevap üretiminde yalnız getirilen kanıtları kullan.
5. Yeterli kanıt yoksa kesin olarak `Belgede bulunamadı` davranışı uygula.
6. Her cevapta en az bir doğrulanabilir citation nesnesi oluştur.
7. Kullanıcı kaynağa tıklayınca ilgili sayfa/satırı açacak konum verisi üret.
8. Düşük güvenli OCR kaynağında uyarı göster.
9. Belge metnindeki talimatları güvenilmeyen veri kabul et.
10. Sohbet geçmişi, silme ve erişim kontrolünü uygula.
11. Test setinde:
    - cevaplanabilir soru
    - cevaplanamaz soru
    - çelişkili chunk
    - prompt injection
    - başka belgeye sızma
    senaryolarını test et.

## Kabul Kriterleri

- Kanıtsız cevap üretilmiyor.
- Citation sayfa/satır konumuna gidiyor.
- Belge dışı soruya kontrollü ret var.
- Prompt injection sistem davranışını değiştirmiyor.
- İzin verilmeyen belge içeriği retrieval'a girmiyor.
