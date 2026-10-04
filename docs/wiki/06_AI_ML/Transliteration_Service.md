---
type: module
status: partial
last_verified: 2026-08-09
owners: []
source_paths:
  - backend/app/services/document_processing/translator.py
  - backend/app/api/routes/transliteration.py
  - backend/app/api/router.py
test_paths:
  - backend/tests/test_transliteration.py
tags: [ai, transliteration, task-019]
---

# Transliteration Service

**Ozet:** TASK-019 ile Arap harfli Osmanlica OCR satirindan Latin harfli Osmanlica cikti ureten deterministik transliterasyon sozlesmesi eklendi. 2026-08-09 downstream repair ile `rule-based-ottoman-latin-v2` satir bazli normalizasyon, ortak Osmanlica kelime/kalip sozlugu ve kopya cikti kalite kontrolleri eklendi. OCR ve Latin cikti `TextVersion(version_type="transliteration")` ile ayri saklanir, kaynak `OCRResult` satirina geri gidilebilir ve fixture metrikleri testlidir.

**Kutuphaneler:** FastAPI, Pydantic, SQLAlchemy, pytest.

**Baglantilar:** [[OCR_Service]], [[OCR_Review_Flow]], [[Modernization_Service]], [[Audit_Log]], [[Evaluation_Service]]

## Sorumluluklar
- OCR ham metnini modern Turkceye cevirmeden once Latin harfli Osmanlica metne donusturmek.
- `source_ocr_result_id`, `line_no`, confidence ve ambiguity bilgilerini korumak.
- Belirsiz Osmanlica karakter okumalarini aday ve gerekce olarak raporlamak.
- Kullanici secimi veya duzeltmesini yeni `TextVersion` olarak surumlemek.
- Kucuk fixture seti icin CER, WER ve chrF metrikleri uretmek.
- Osmanlica/Turkce tarih anlatimi ve vakfiye kaliplari icin okunabilir Latin cikti uretmek; cok bozuk satirda bos/kontrollu fallback kullanmak.

## Girdiler
- `OCRResult.raw_text`, `OCRResult.id`, `OCRResult.line_no`.
- Opsiyonel kullanici metni: `TransliterationRequest.text`.

## Ciktilar
- `TransliterationResult`: original text, Latin text, source OCR id, line no, candidates, ambiguity, confidence, method version.
- `TextVersion(version_type="transliteration")`.
- `AuditLog(action="transliteration.create" | "transliteration.correction.create")`.

## Bagimliliklar
- [[OCR_Service]] sonuc satirlari.
- [[OCR_Review_Flow]] tarafindan uretilen son OCR correction metni.
- [[Database_Model]] icindeki `OCRResult` ve `TextVersion`.
- [[Security_Model]] belge sahipligi kontrolu.

## Veri Akisi
1. `POST /api/v1/transliteration/ocr-results/{ocr_result_id}` OCR satirini bulur.
2. Route belge sahibi/admin kontrolu yapar.
3. Kaynak metin once payload text, sonra son OCR correction, sonra raw OCR olacak sekilde secilir.
4. `Translator.transliterate_line` Latin cikti, ambiguity ve candidate bilgisi uretir.
5. Latin cikti ham OCR'yi degistirmeden `TextVersion` olarak kaydedilir.
6. Ikinci transliterasyon kaydi `previous_text` ve `source_version_id` ile onceki transliterasyona baglanir.
7. Audit kaydi method version ve ambiguity metadata'si ile yazilir.

## Hata Durumlari
- OCR sonucu yoksa `404`.
- Sayfa/belge yoksa `404`.
- Belge sahibi olmayan kullanici icin `403`.
- Bos payload text Pydantic tarafindan reddedilir.

## Guvenlik ve Gizlilik
- JWT auth zorunludur.
- Belge izolasyonu testlidir.
- Harici model veya API cagrisi yoktur; gizli deger kullanmaz.

## Testler ve Kabul Kriterleri
- `backend/tests/test_transliteration.py::test_transliterator_reports_source_mapping_and_ambiguity`.
- `backend/tests/test_transliteration.py::test_transliteration_fixture_metrics_report`.
- `backend/tests/test_transliteration.py::test_transliteration_api_stores_latin_text_separately_and_preserves_ocr`.
- `backend/tests/test_transliteration.py::test_transliteration_uses_latest_ocr_correction_and_keeps_history`.
- `backend/tests/test_transliteration.py::test_transliteration_api_enforces_document_ownership`.
- 2026-08-09 kanit: `python -m pytest tests/test_transliteration.py tests/test_modernization.py tests/test_processing_pipeline.py` -> 11 passed.
- 2026-08-09 gercek belge kaniti: `evidence/downstream_text_repair/api_payload.json` -> Kraken 25 satir, `transliterated_text` dolu ve OCR'den farkli.
- Kanit: `evidence/environment_gate/backend_pytest_task019_transliteration_after_metrics.txt` -> 5 passed.
- Kanit: `evidence/environment_gate/backend_pytest_task019_after_metrics.txt` -> 36 passed.
- Kanit: `evidence/environment_gate/doctor_task019_after_metrics.txt` -> `DOCTOR_FAILED=0`.

## Kod Kanitlari
- `backend/app/services/document_processing/translator.py` -> `Translator`, `TransliterationResult`, `TransliterationCandidate`, `transliterate_line`, `evaluate_fixture`.
- `backend/app/api/routes/transliteration.py` -> `create_transliteration`, `_latest_transliteration`, `_latest_correction_text`.
- `backend/app/api/router.py` -> transliteration router dahil edildi.
- `backend/app/models/processing_outputs.py` -> `OCRResult`, `TextVersion`.

## Bilinen Eksikler
- Tam akademik transkripsiyon modeli yok; `rule-based-ottoman-latin-v2` deterministik ve sozluk kapsamiyla sinirli.
- Frontend transliterasyon workspace ayrintili duzeltme akisi henuz yok.
- Metrik raporu servis metodunda var, operasyonel evaluation pipeline henuz TASK-025 kapsaminda.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda placeholder/partial olarak olusturuldu.
- 2026-07-28: TASK-019 ile source-mapped transliteration API, correction history, audit ve fixture metric tests eklendi.
- 2026-08-09: Downstream text repair ile v2 transliteration, gercek Kraken payload evidence ve kopya/bozuk cikti kalite kontrolleri eklendi.
