# 03 — Windows, WSL, Python, GPU ve Bağımlılık Uçuş Kapısı

MODE: EXECUTE

Rolün: Windows/WSL Sistem Mühendisi + Python Ortam Uzmanı + MLOps Mühendisi.

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

Projeyi tekrarlanabilir biçimde çalıştıracak temiz ve doğrulanmış geliştirme ortamını kur. Bu aşamada uygulama özelliği geliştirme.

## Güvenlik Sınırları

- WSL dağıtımı silme, unregister etme veya kullanıcı verisini kaldırma.
- İşletim sistemi özelliğini kullanıcı izni olmadan kapatma.
- Yönetici yetkisi yoksa yönetici gerektiren işlemi zorlamaya çalışma.
- Dış repo klonlama.
- Rastgele internet scripti çalıştırma.
- Mevcut çalışan sanal ortamı kanıtsız biçimde silme.

## Yapılacaklar

1. Yönetici durumunu ilk adımda doğrula.
2. Windows sürümü, GPU, sürücü, CUDA uygunluğu, RAM ve disk alanını kaydet.
3. WSL/Ubuntu durumunu güvenli komutlarla doğrula.
4. `REBOOT_REQUIRED` oluşursa kanıtları yaz ve dur.
5. Proje için tek kanonik Python sürümü ve sanal ortam yolu belirle.
6. Bağımlılık dosyalarını incele; sürümleri sabitle veya eksik lock görevini oluştur.
7. Resmî paket yöneticisiyle gerekli bağımlılıkları kur.
8. En az şu import/başlatma smoke testlerini çalıştır:
   - uygulama giriş noktası
   - Streamlit
   - FastAPI varsa API
   - SQLAlchemy/veri katmanı
   - OpenCV/Pillow
   - PyTorch/CUDA kullanılıyorsa GPU görünürlüğü
   - OCR motoru
9. `.env.example` oluşturulmuşsa gizli değer içermediğini doğrula.
10. `scripts/doctor` veya eşdeğer tek komutlu ortam teşhis aracı mevcut değilse görev kapsamı içinde oluştur.
11. Kurulum ve teşhis çıktısını `evidence/environment_gate/` altında kaydet.

## Kabul Kriterleri

- Kanonik Python ortamı belgelenmiş.
- Gerekli import smoke testleri PASS.
- GPU kullanılacaksa görünür ve uygun; kullanılmayacaksa CPU fallback belgeli.
- WSL gerekliyse çalışır; değilse mimari karar kayıtlı.
- Temiz terminalde uygulama başlangıç komutu biliniyor.
- `doctor` çıktısı kanıt olarak mevcut.
