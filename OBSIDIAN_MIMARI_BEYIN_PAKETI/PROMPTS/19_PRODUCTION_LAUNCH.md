# 19 — Paketleme, Yerel/Kurumsal Yayınlama ve Uçuş

MODE: EXECUTE

Rolün: Release Engineer + DevOps/MLOps Mühendisi + Operasyon Sorumlusu.

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

## Ön Koşul

`18_RELEASE_CANDIDATE_GATE` sonucu kesinlikle `PASS` olmalıdır.

## Amaç

Projeyi hedef kullanım biçimine göre tekrarlanabilir, geri alınabilir ve doğrulanabilir şekilde yayınla.

## Yapılacaklar

1. Hedef dağıtım biçimini mevcut ADR ve kullanıcı kararından oku:
   - Yerel Windows + WSL
   - Docker Compose
   - Kurumsal sunucu
2. Sürüm numarası ve immutable release etiketi oluştur.
3. Gereksiz geliştirme dosyalarını pakete alma.
4. Secret'ları paket dışında tut; `.env.example` yalnız isimleri içersin.
5. Model ve veri dosyaları için checksum doğrulaması ekle.
6. Başlatma/durdurma/yeniden başlatma/health komutlarını doğrula.
7. Migration ve ilk yönetici oluşturma akışını güvenli yap.
8. Yedekleme ve geri alma adımlarını test et.
9. Release notes ve bilinen sınırlamaları yaz.
10. Yayınlanan ortamda smoke test çalıştır.
11. Ana E2E akışından küçük bir üretim doğrulaması yap.
12. Tüm kanıtları `evidence/release/` altında sakla.
13. Wiki'de `Current_State` durumunu RELEASED olarak ancak bütün doğrulamalar PASS ise güncelle.

## Kabul Kriterleri

- Yayın paketi tekrarlanabilir.
- Health check PASS.
- Smoke test PASS.
- Rollback denendi veya güvenli biçimde simüle edildi.
- Secret sızıntısı yok.
- Kullanıcı için tek komut/az adımlı çalıştırma yönergesi mevcut.
