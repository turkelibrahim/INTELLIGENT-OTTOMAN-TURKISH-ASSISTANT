---
type: architecture
status: partial
last_verified: 2026-08-02
owners: []
source_paths:
  - backend/app/main.py
  - backend/app/api/router.py
  - backend/app/db/database.py
  - frontend/src/lib/api.ts
tags: [architecture, backend, frontend]
---

# Architecture Map

**Ozet:** Sistem yerel FastAPI API, SQLite/SQLAlchemy veri katmani, dosya sistemi tabanli upload depolama, kalici worker sureci ve Next.js App Router frontend katmanlarindan olusur. AI/ML kodlari backend servisleri ve route'lari altinda bulunur; OCR, NLP, RAG, export, evaluation ve ground truth alanlari farkli olgunluk seviyelerinde uygulanmistir. Nihai OCR kalite karari human-verified ground truth bekledigi icin blokludur.

**Kutuphaneler:** FastAPI, SQLAlchemy, SQLite, Next.js, React, TypeScript, OpenCV, Pillow, pdf2image, torch, transformers.

**Baglantilar:** [[FastAPI_API]], [[Database_Model]], [[Document_Ingestion]], [[Image_Preprocessing]], [[Document_Workspace]]

## Katmanlar
- UI: `frontend/src/app` altinda App Router sayfalari.
- API Client: `frontend/src/lib/api.ts` icinde auth, documents, pages, preprocessing istemcileri.
- API: `backend/app/main.py` ve `backend/app/api/router.py`.
- Route Modulleri: `analysis.py`, `auth.py`, `chat.py`, `documents.py`, `export.py`, `ground_truth.py`, `modernization.py`, `ocr.py`, `ocr_review.py`, `pages.py`, `preprocessing.py`, `transliteration.py`.
- Servisler: `file_service.py`, `job_manager.py`, `export_service.py`, `evaluation_service.py`, `chat/*`, `document_processing/*`, `evaluation/*`.
- Veri: `backend/app/models/*.py`, `backend/app/schemas/*.py`, SQLite dosyasi `backend/ottoman_assistant.db`.
- Dosya Depolama: `backend/uploads` ve `settings.UPLOAD_DIR`.

## Ana Akislar
- Auth Flow: [[Document_Workspace]] login/register -> `authApi` -> [[FastAPI_API]] `/auth/*` -> [[Security_Model]] -> [[Database_Model]] `User`.
- Document Upload Flow: Upload UI -> `documentsApi.upload` -> `/documents` -> [[File_Validation]] -> [[Document_Ingestion]] -> [[Database_Model]] `Document`/`Page` -> [[Audit_Log]].
- Page Viewing Flow: Document detail UI -> `pagesApi` -> `/documents/{id}/pages` ve image/thumbnail endpointleri -> dosya sistemi.
- Preprocessing Flow: Document detail UI -> `preprocessingApi.preprocess` -> `/pages/{page_id}/preprocessing` -> [[Image_Preprocessing]] -> `ImageVariant` -> processed file.

## AI/ML Durumu
- Verified: [[Image_Preprocessing]], [[RAG_Chat_Service]], [[Export_Service]].
- Partial: [[OCR_Service]], [[Transliteration_Service]], [[Modernization_Service]], [[NER_Service]], [[Evaluation_Service]], [[Glossary_Service]], [[Date_Normalization]], [[Model_Registry]].
- Planned/DOGRULANMADI: Production-grade external LLM integration and final OCR quality acceptance without human-verified data.

## Guvenlik
- JWT token localStorage'da tutulur (`frontend/src/lib/api.ts`).
- Backend auth dependency `get_current_user` ile route korumasi yapar (`backend/app/core/security.py`).
- CORS backend'de `settings.CORS_ORIGINS` kullanilir (`backend/app/main.py`).

## Bilinen Mimari Bosluklar
- Final OCR kalite metrikleri human-verified ground truth olmadan PASS yapilamaz.
- OCR baslatma UI butonu var, fakat route baglantisi yok.
- Worker ve OCR route baglantilari mevcuttur; kullanici gorunurlugu ve kalite kabul kapsami gorev bazinda dogrulanmalidir.
- Production deployment mimarisi DOÄžRULANMADI.


## 2026-08-02 Bootstrap Refresh Kanitlari
- `backend/app/api/router.py` -> chat/export/ocr/ground_truth dahil tum route'lar bagli.
- `backend/worker.py` -> `run_worker`, `process_job`, `process_pilot_evaluation_job`.
- `backend/app/services/export_service.py` -> `ExportService`.
- `backend/app/services/evaluation_service.py` -> `EvaluationService`.
- `backend/tests` -> backend unit/integration/e2e test dosyalari mevcut.



