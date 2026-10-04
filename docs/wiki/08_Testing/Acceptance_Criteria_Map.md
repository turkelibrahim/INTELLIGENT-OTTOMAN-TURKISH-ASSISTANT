---
type: test_map
status: partial
last_verified: 2026-07-28
owners: []
source_paths:
  - docs/wiki/08_Testing/Requirements_Traceability_Matrix.md
  - evidence/recover_baseline/
tags: [acceptance, testing, task-008]
---

# Acceptance Criteria Map

**Ozet:** Bu sayfa MVP ucus kapisi icin test edilebilir kabul kriterlerini SRS, kod ve wiki gereksinim gruplarina baglar. TASK-008 autonomous turunda SRS PDF metni cikarildi ve [[Requirements_Traceability_Matrix]] 165 gereksinim satirini kapsayacak sekilde guncellendi. Tum kriterler test ve kanit uretilmeden DONE kabul edilemez.

**Kutuphaneler:** pytest planli, ESLint, Next.js build.

**Baglantilar:** [[Requirements_Traceability_Matrix]], [[Test_Strategy]], [[Task_Queue]], [[Risks]]

## Kritik Uc Uca Kabul Senaryosu
1. Kullanici kayit olur veya giris yapar.
2. Kullanici desteklenen bir belge/PDF yukler.
3. Sistem dosya turunu, magic bytes checksum'ini, boyutu ve hash'i dogrular.
4. PDF ise sayfalara ayrilir; her sayfa ve thumbnail kaydedilir.
5. Sayfa on isleme varyanti orijinali degistirmeden olusturulur.
6. Layout ve RTL sirasi satirlari belirler.
7. OCR satir bazli metin ve confidence uretir.
8. Kullanici OCR sonucunu review ekraninda duzeltir; audit kaydi olusur.
9. Sistem transliterasyon, modern Turkce, ozet, NER/tarih/sozluk ciktisi uretir.
10. Kullanici belge uzerinden soru sorar; cevap citation ile doner.
11. Release gate testleri ve guvenlik kontrolleri PASS olur.

## Kabul Kriterleri
- Auth: register/login/me/logout ve rol kontrolleri test DB uzerinde PASS olmali.
- Belge guvenligi: desteklenmeyen dosya, sahte MIME/magic bytes ve tekrar yukleme testleri PASS olmali.
- Veri: temiz DB kurulumu ve migration/rollback yolu kanitlanmali.
- Preprocessing: pipeline ve API ayni `ImagePreprocessor` sozlesmesini kullanmali; orijinal dosya degismemeli.
- Layout/OCR: satir bolgeleri, RTL sirasi, OCR metni ve confidence fixture ile dogrulanmali.
- Review/Audit: her OCR duzeltmesi actor, zaman, eski/yeni deger ve hedef nesne ile kaydedilmeli.
- NLP: transliterasyon, modernizasyon, ozet, NER, tarih ve sozluk ciktisi birbirinden ayri saklanmali.
- RAG/Citation: cevaplar belge baglamina bagli ve en az bir dogrulanabilir citation icermeli.
- Security: secret degeri repo/wiki/log icinde acik metin olmamali; CORS production icin sinirlanmali.
- Test Gate: backend pytest, frontend lint/build ve ana e2e akisi PASS olmadan ucus yapilmamali.

## Blokaj Eslemeleri
- Git PATH yok -> TASK-009.
- pytest yok -> TASK-009.
- `ImagePreprocessor.process` hatasi -> TASK-015.
- `sentencepiece` veya `tiktoken` eksik -> TASK-017.
- Transliteration placeholder -> TASK-019.
- Modernization placeholder -> TASK-020.
- NER placeholder -> TASK-021.
- Layout yok -> TASK-016.
- OCR review yok -> TASK-018.
- RAG chat yok -> TASK-023.
- Citation flow yok -> TASK-023.
- Evaluation runtime yok -> TASK-025.
- Integration/E2E test yok -> TASK-028.

## Bilinen Eksikler
- SRS metni cikarildi, ancak gereksinim satirlarinin uzun tablo/kabul metinleri otomatik parse edildigi icin her satirin insan gozuyle son kalite kontrolu TASK-009/TASK-028 surecinde yapilmalidir.
- Kullanici tarafindan hangi Deferred With Approval gereksinimlerinin ertelenebilecegi onaylanmadi.
