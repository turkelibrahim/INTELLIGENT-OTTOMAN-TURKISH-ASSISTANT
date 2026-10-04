# 01 — Kurtarma, Envanter ve Gerçek Başlangıç Fotoğrafı

MODE: RECOVER

Rolün: Baş Mimar + Adli Kod Analisti.

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

Projede gerçekte neyin bulunduğunu, neyin çalıştığını ve hangi değişikliklerin yarım kaldığını kesinleştir. Bu aşamada özellik geliştirme yapma.

## Yapılacaklar

1. Proje kökü, giriş noktaları, `src`, `app`, `tests`, `scripts`, `config`, `docs`, `models`, `data` ve benzeri klasörleri envanterle.
2. Git varsa `status`, son commit, diff ve branch bilgisini kaydet. Git yoksa dosya hash/zamanlarına dayalı durum çıkar.
3. Python sürümünü, sanal ortamları, paket yöneticisini ve lock/requirements dosyalarını belirle.
4. Ana modüllerin import edilebilirliğini kontrol et.
5. Mevcut testleri keşfet; değiştirmeden çalıştırılabilen temel testleri çalıştır.
6. Çalışan, kısmen çalışan, uygulanmamış ve bozuk bileşenleri ayır.
7. Yarım değişiklikleri aktif görevlerle eşleştir.
8. Wiki ile gerçek kod arasındaki sapmaları kaydet.
9. `Current_State`, `Architecture_Map`, `Source_Map`, `Risks`, `Open_Questions` ve `Task_Queue` dosyalarını gerçek duruma göre güncelle.
10. Sonraki aşama olarak yalnız uygun ise `02_REQUIREMENTS_TRACEABILITY` görevini READY yap.

## Kabul Kriterleri

- Proje dosya ve modül envanteri mevcut.
- Çalıştırılabilir giriş noktaları belirtilmiş.
- Test başlangıç tablosu mevcut.
- Aktif blokajlar gerçek hata kanıtlarıyla kayıtlı.
- Yarım görev varsa tam kaldığı adım belirlenmiş.
- Hiçbir kaynak kod değiştirilmemiş.
