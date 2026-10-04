---
type: module
status: verified
last_verified: 2026-08-13
owners:
  - Codex
source_paths:
  - backend/app/services/document_analysis_pipeline.py
  - backend/app/api/routes/document_analysis.py
  - backend/app/schemas/document_analysis.py
test_paths:
  - backend/tests/test_unknown_document_pipeline.py
tags: [backend, pipeline, ocr, rag, ollama, qdrant]
---

# Unknown Document Analysis Pipeline

**Ozet:** Yuklenen bilinmeyen Osmanlica belgeyi preprocessing, OCR, transliteration, modern Turkish, NER, verified historical RAG, evidence assembly ve confidence/uncertainty asamalarindan geciren backend orkestrasyonudur. Sonuc `document_evidence`, `historical_external_evidence`, `model_inference` ve `uncertainties` alanlarini ayri tutar. Tarihsel dis kanit yalniz `verified=true` ve `derived_verified != false` Qdrant chunk'larindan uretilir.

**Kutuphaneler:** FastAPI, SQLAlchemy, Pydantic, OpenCV, EasyOCR/Kraken OCR, Ollama, Qdrant.

**Baglantilar:** [[OCR_Service]], [[Image_Preprocessing]], [[Transliteration_Service]], [[Modernization_Service]], [[NER_Service]], [[RAG_Chat_Service]], [[FastAPI_API]], [[Current_State]]

## Sorumluluklar
- Uploaded image/PDF dosyasini mevcut `FileService` ile guvenli kaydetmek.
- Sayfa bazinda preprocessing ve OCR calistirmak.
- OCR sonucunu Latin transliteration ve modern Turkish asamalarina ayri tasimak.
- Entity sonucunu structured response schema'sina normalize etmek.
- Historical Qdrant collection `ottoman_historical_knowledge_v1` icinden sadece verified source material almak.
- Evidence ve model inference alanlarini birbirinden ayirmak.
- Kanit yoksa `Tespit edilemedi` ve explicit uncertainty dondurmek.

## Girdiler
- `POST /api/v1/document/analyze-full`
- Multipart `file`, opsiyonel `title`, opsiyonel `description`
- Authenticated user

## Ciktilar
- `FullDocumentAnalysisResponse`
- `Document`, `Page`, `OCRResult`, `TextVersion`, `Entity`, `AuditLog` DB kayitlari

## Bagimliliklar
- `backend/app/services/file_service.py`
- `backend/app/services/document_processing/preprocessor.py`
- `backend/app/services/document_processing/ocr_factory.py`
- `backend/app/services/transliteration_service.py`
- `backend/app/services/document_intelligence_service.py`
- `backend/app/services/document_processing/ner_extractor.py`
- `backend/app/services/historical_rag/qdrant_store.py`

## Veri Akisi
1. Route dosyayi validate/save eder ve `Document/Page` kayitlari olusturur.
2. `DocumentAnalysisPipeline.analyze_document` her sayfayi `ImagePreprocessor.process` ve `ocr_engine.extract` ile isler.
3. OCR lines `OCRResult` olarak saklanir.
4. `TransliterationEngine` Ollama uzerinden Latin cikti uretir; hata olursa explicit warning ile rule-based fallback kullanilir.
5. `DocIntelligenceEngine` Ollama ile modern Turkish uretir; hata olursa explicit warning ile local rule fallback kullanilir.
6. `NERExtractor` entity cikarir ve `Entity` kayitlarini yazar.
7. `HistoricalQdrantStore.search(..., verified_only=True)` dis kanit getirir.
8. Response evidence/confidence/uncertainty alanlarini ayri dondurur.

## Hata Durumlari
- Dosya validate edilemezse mevcut `FileService` HTTP hatasi doner.
- Page image okunamazsa route 500 ile full analysis hatasi doner ve document kaydi temizlenir.
- Transliteration/modernization LLM hatalari saklanmaz; warning/uncertainty alanina yazilir.
- Verified historical source bulunamazsa historical fields `Tespit edilemedi` kalir.

## Guvenlik ve Gizlilik
- Endpoint `get_current_user` ile auth zorunlu calisir.
- Dosya upload, MIME, magic bytes ve size kontrolleri mevcut `FileService` ile korunur.
- Derived relation candidates with `derived_verified=false` historical evidence olarak kullanilmaz.
- Document-internal FAISS/RAG dosyalari silinmedi veya degistirilmedi.

## Testler ve Kabul Kriterleri
- `python -m pytest tests/test_unknown_document_pipeline.py -q` PASS.
- `python -m pytest tests/test_unknown_document_pipeline.py tests/test_processing_pipeline.py tests/test_transliteration.py tests/test_modernization.py tests/test_analysis.py tests/test_rag_chat.py tests/test_document_upload_integration.py tests/test_file_security.py tests/test_auth_security.py tests/test_smoke.py tests/test_ocr_engine.py tests/test_faiss_security.py -q` PASS, 55 passed.
- Real upload integration test uses existing real sample `backend/uploads/originals/9/pages/page_1.png`, real EasyOCR, real Ollama and real Qdrant.

## Kod Kanitlari
- `backend/app/services/document_analysis_pipeline.py` -> `DocumentAnalysisPipeline`
- `backend/app/api/routes/document_analysis.py` -> `analyze_full_document`
- `backend/app/schemas/document_analysis.py` -> `FullDocumentAnalysisResponse`
- `backend/tests/test_unknown_document_pipeline.py` -> `test_analyze_full_endpoint_with_real_upload_real_ocr_ollama_and_qdrant`

## Bilinen Eksikler
- Production default OCR engine `kraken` korunur; yeni endpoint testinde hiz/izolasyon icin real EasyOCR engine enjekte edilerek smoke calistirildi.
- Combined confidence provisional olarak isaretlenir; kalibre edilmis istatistiksel confidence modeli henuz yok.

## Degisiklik Gecmisi
- 2026-08-13: TASK-UNKNOWN-DOC-PIPELINE kapsaminda olusturuldu ve testlerle dogrulandi.
