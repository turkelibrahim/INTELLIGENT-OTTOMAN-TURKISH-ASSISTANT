# 18 — Release Candidate ve Son Uçuşa Elverişlilik Kapısı

MODE: VERIFY

Rolün: Bağımsız Release Manager + QA Lideri + Güvenlik Denetçisi.

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

Projeyi geliştiren ajanlardan bağımsız biçimde doğrula. Bu aşamada yalnız zorunlu düzeltme görevi aç; büyük yeni özellik ekleme.

## Doğrulama

1. Temiz kurulum dokümanını uygula.
2. Ortam doctor çıktısını kontrol et.
3. Migration'ı boş veri tabanında çalıştır.
4. Uygulamayı temiz terminalde başlat.
5. Ana E2E senaryosunu çalıştır:
   - giriş
   - belge yükleme
   - sayfalama
   - ön işleme
   - layout/OCR
   - OCR düzeltme
   - transliterasyon
   - modern Türkçe
   - NER/sözlük
   - RAG soru
   - citation açma
   - dışa aktarma
6. Yetki ve güvenlik negatif testlerini çalıştır.
7. Bütün otomatik kalite kapısını çalıştır.
8. Açık P0/P1 bug, veri kaybı veya güvenlik açığı ara.
9. SRS MUST izlenebilirlik matrisini kontrol et.
10. Wiki ve kod sapmasını lint et.
11. Release kanıt paketini oluştur:
    - sürüm
    - commit/hash
    - ortam
    - test raporları
    - bilinen sınırlamalar
    - rollback
    - çalıştırma komutları

## PASS Koşulu

Aşağıdakilerden biri varsa PASS verme:
- Kritik test başarısız
- Veri kaybı riski
- Yetkisiz erişim
- Kanıtsız temel özellik
- Temiz kurulumda başlatamama
- Ana E2E akışının tamamlanmaması
- Açık P0/P1 hata

PASS ise `RC_VERSION` oluştur ve yalnız `19_PRODUCTION_LAUNCH` görevini READY yap.
