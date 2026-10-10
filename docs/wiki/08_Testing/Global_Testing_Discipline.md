---
type: module
status: verified
last_verified: 2026-10-06
owners: []
source_paths: []
test_paths: []
tags: [testing, regression, global-rule, engineering-standards]
---

# Global Testing Discipline

**Özet:** Bu doküman, projede kod değişikliklerinin ardından uyulması zorunlu olan test ve regresyon disiplinini tanımlar. Hiçbir görev, testleri koşulmadan ve gerekli regresyon testleri yazılmadan "tamamlanmış" (PASS) kabul edilemez.

**Bağlantılar:** [[Index]], [[Task_Queue]], [[Current_State]]

## 1. Temel Kural
Kod değiştirip testleri atlamak kabul edilemez.
Her değişiklik şu akışla tamamlanmalıdır:
1. Kod değişikliği
2. Mevcut testleri inceleme
3. Etkilenen testleri güncelleme
4. Gerekiyorsa yeni test (özellikle regression test) yazma
5. İlgili testleri çalıştırma
6. Regresyon testlerini çalıştırma
7. Build / Lint / Type Check
8. Gerçek runtime doğrulaması
9. Final rapor

## 2. Değişiklik Öncesi İnceleme
Bir dosyayı değiştirmeden önce ilgili test dosyaları incelenmelidir:
- Backend için: Unit, integration, API, fixture, mock vb.
- Frontend için: Component, interaction, API mock, route, browser/e2e vb.
Mevcut test yoksa, açıkça raporlanmalıdır.

## 3. Etkilenen Testleri Tespit
Değişikliğin hangi mevcut davranışları etkileyebileceği öngörülüp (örn. OCR değişikliğinin analysis endpoint'lerini etkileyebileceği) testler çalıştırılmalıdır.

## 4. Yeni Test (Regression) Yazımı
Bir bug düzeltiliyorsa yalnızca kod düzeltilmemeli, bug'ın tekrar oluşmasını engelleyecek **regression test** eklenmelidir.
- Örnek: 
ot_assessed hatası için UI'da "Değerlendirilemedi" çıktısını teyit eden bir test yazılmalıdır.
- Örnek: "NVIDIA timeout" durumunda "local fallback" senaryosu test edilmelidir.

## 5. Test Silme / Zayıflatma
Bir test sadece başarısız olduğu için silinemez veya assertion anlamsız (generic) hale getirilemez. Davranış değişikliği nedeniyle güncelleniyorsa, final raporda nedeni açıklanmalıdır.

## 6. Frontend ve Backend Test Zorunluluğu
Backend (OCR, Transliteration, NER, RAG, vb.) ve Frontend (State, API mapping, empty state vb.) değişikliklerinde test çalıştırılması ve gerekli yeni logic'lerin test edilmesi zorunludur.

## 7. Browser Doğrulaması
Sadece unit test yeterli değildir. Belge Yükleme, Analiz Et, Chat, Historical Analysis vb. kritik akışlarda browser/e2e doğrulaması yapılmalıdır. Automation çalışmıyorsa "Browser verification yapılamadı: ..." şeklinde açıkça belirtilmeli, sahte rapor verilmemelidir.

## 8. Test Raporu Zorunlu Formatı
Görev final raporunda aşağıdaki matris doldurulmalı ve gerçek değerler yazılmalıdır:
| Test | Durum (PASS/FAIL/BLOCKED) | Sonuç |
| --- | --- | --- |
| Unit tests | | |
| Integration tests | | |
| API tests | | |
| Regression tests | | |
| Frontend tests | | |
| Browser tests | | |
| TypeScript | | |
| ESLint | | |
| Production build | | |

## 9. Test Dosyaları ve Geçici Scriptler
- Scratch (scratch/) içinde oluşturulan ve kalıcı olması gereken testler, proje test dizinlerine (	ests/unit/, rontend/__tests__/ vb.) taşınmalıdır.
- Geçici (temporary) script'ler raporda açıkça 	emporary verification script olarak işaretlenmelidir.
- Gerçek domain'e uygun fixture'lar kullanılmalı ve daha önce çözülmüş hataların (Mektep / مكتب) regression testleri korunmalıdır.

## 10. API Contract ve Çevre Değişkenleri
- Frontend-Backend contract değişimlerinde iki taraf birlikte test edilmelidir.
- .env veya provider / model / özellik bayrağı değişimlerinde, çalışma zamanı ve fallback testleri mutlaka koşulmalıdır.

## 11. Testler Başarısızken PASS İlan Etmeme
Eğer bir test (özellikle core functionality) başarısız ise görev FINAL STATUS: PASS olamaz.
Duruma göre FAIL, BLOCKED, PASS WITH WARNINGS kullanılmalıdır. Başarısızlık durumunda loglar incelenmeli, kod düzeltilmeli ve test yeniden geçirilmelidir.

Bu kural, projede yer alan tüm görev ve geliştirmeler için **zorunlu global engineering standardıdır**.
