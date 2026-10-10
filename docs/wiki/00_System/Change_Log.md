---
type: change_log
status: verified
last_verified: 2026-08-13
owners: []
source_paths: []
tags: [changelog]
---

# Change Log

## 2026-10-06 TASK-20261006-FIX-12-ANALYSIS-BUTTON
- Fixed a frontend bug where the Dashboard "Analiz Et" button appeared to do nothing because the UI instantly reverted to the upload form.
- The `isProcessing` flag in `frontend/src/app/(app)/dashboard/hooks.ts` was overly restrictive (`UPLOADING` || `PREPROCESSING`). It was updated to cover all active analysis stages (`OCR`, `TRANSLITERATION`, etc.).
- Verified the fix by running the full backend pipeline with `test_image.png`, ensuring the processing banner correctly stays on screen and transitions to the `COMPLETE` state successfully.
- Added `BUG_12_ANALYSIS_BUTTON_FIX.md` report.
- Started local runtime with `scripts/runtime_launcher.ps1 -Action Restart`.
- Verified backend `/health` HTTP 200 and frontend `/login` HTTP 200.
- Verified status: Backend ONLINE, Frontend ONLINE, Database READY, WSL Ubuntu ONLINE, Kraken READY, CUDA True, Model VERIFIED.
- Runtime PIDs: backend `19388`, frontend `5076`, worker `16784`.

## 2026-08-21 Performance Audit 1B
- Added `backend/scripts/performance_audit_1b.py` for environment, baseline/optimized benchmark, stage timing, call graph, RAG/DB/memory/edge/profiler evidence generation.
- Added `evidence/performance_audit/PERFORMANCE_REPORT.md`, `comparison.json`, `baseline.json`, `optimized.json`, stage/resource/profile/call graph/DB/edge evidence files.
- Optimized `backend/app/services/document_analysis_pipeline.py` to reuse document-level transliteration/modernization lines only when output line count exactly matches OCR line count, preserving line provenance and falling back to existing per-line behavior otherwise.
- Removed dead `DocIntelligenceEngine(use_mock=True)` allocation from `backend/app/services/chat/rag_service.py`.
- Added regression coverage in `backend/tests/test_unknown_document_pipeline.py` proving line reuse preserves `line_id` and reduces provider calls in aligned output.
- Verification: backend targeted regression `44 passed, 1 skipped`; frontend lint `0 errors / 14 warnings`; frontend build PASS.
- Status: `PARTIAL_SCOPED_PASS_REAL_STAGE_AND_SYNTHETIC_BULK_BENCHMARK`; full real HTTP/browser 5/10 document benchmark remains open.

## 2026-08-20 Algorithm Audit 1A
- Added `evidence/performance_audit/ALGORITHM_AUDIT.md` with Critical/High/Medium/Low bugs, inefficiencies, assumptions, dead code, edge cases, fixed issues and remaining issues.
- Fixed `backend/app/services/document_analysis_pipeline.py` logger fallback crash and iterable page handling.
- Fixed `backend/app/services/document_processing/preprocessor.py` so OCR-safe deskew is skipped when text preservation loss is detected.
- Added/updated regression tests in `backend/tests/test_unknown_document_pipeline.py` and `backend/tests/test_processing_pipeline.py`.
- Hardened `frontend/src/app/(app)/dashboard/page.tsx` against duplicate analyze submissions while busy.
- Verification: backend targeted audit tests `43 passed, 1 skipped`; frontend lint `0 errors / 14 warnings`; frontend build PASS.

## 2026-08-20 Final Partial To Verified Pass Closure
- Added `backend/scripts/final_closure_evidence_audit.py` to close the remaining real-document runtime gates without restarting recovery phases 01-18.
- Added real OCR review UI/API wiring through `frontend/src/lib/api.ts` and `frontend/src/app/(app)/dashboard/page.tsx`.
- Added dashboard controls for document search, OCR correction save, modern text edit, rotate/download, and supporting CSS in `frontend/src/app/globals.css`.
- Ran live final closure audit against backend/frontend; result `VERIFIED_PASS`, failed gates `[]`.
- Evidence: `evidence/recovery/final_audit/final_closure_report.json`, `actual_text_outputs.json`, `line_traceability.json`, and screenshots `00_real_document_identity.png` through `10_responsive_mobile.png`.
- Verification: `python -m py_compile backend/scripts/final_closure_evidence_audit.py` PASS; `npm.cmd run lint` PASS with 0 errors / 14 warnings; `npm.cmd run build` PASS.

## 2026-08-20 Critical False Pass Correction
- Invalidated previous `PROJECT COMPLETED` / `FINAL VERDICT: PASS` claims after user-provided false-pass correction.
- Quarantined root synthetic `silah-atmama-ilani_ahmed-vefik-pasa.jpg` to `evidence/invalid_synthetic_inputs/silah-atmama-ilani_ahmed-vefik-pasa_SYNTHETIC_INVALID.jpg`.
- Added `evidence/recovery/false_pass_incident/incident.md`.
- Updated `backend/scripts/final_evidence_audit.py` to resolve real DB-backed document paths, reject synthetic hashes/dimensions, stop counting mock human review as PASS, save `api_response_snapshot.json`, and compute strict quality gates.
- Ran corrected runtime audit against live backend/frontend; result `VERIFIED_PARTIAL`, not PASS.

## 2026-08-14 TASK-20260814-FIX-BEFORE-AFTER-MASK-OVERLAY-SYSTEM
- `frontend/src/app/(app)/image-processing-lab/page.tsx` Before/After comparison viewer ortak intrinsic image coordinate sistemine alindi; `naturalWidth/naturalHeight`, `ResizeObserver`, shared `zoom/pan/split`, pointer drag slider handle ve geometry mismatch fallback eklendi.
- Maske katmanlari backend kaynakli vector data olmadikca disabled hale getirildi; onceki sahte hardcoded SVG rect/ellipse demo overlayleri production render akışindan kaldirildi.
- `frontend/src/app/globals.css` compare transform layer, gold divider handle, disabled mask controls, 0-100 opacity ve `Teknik Tanilama` details stilleriyle guncellendi.
- Debug `Gercek API Kaniti` normal kullanici akışindan details icine alindi.
- Kanitlar `evidence/before_after_mask_gate/` altina kaydedildi.
- Test: `npm.cmd run lint` PASS, 0 errors / 12 existing warnings; `npm.cmd run build` PASS; runtime restart ONLINE; `/image-processing` HTTP 200; backend `/health` HTTP 200.
- Sonuc: `BEFORE_AFTER_MASK_SYSTEM_GATE_PARTIAL`; mevcut backend gercek maske payload'i dondurmedigi ve bu oturumda full browser pointer/screenshot E2E kosulamadigi icin PASS iddia edilmedi.

## 2026-08-13 - TASK-HISTORICAL-ANALYSIS-RAG-DASHBOARD-PRODUCTION-INTEGRATION
- Added `frontend/src/app/(app)/historical-analysis/page.tsx` production Tarihsel Analiz screen.
- Updated `frontend/src/app/(app)/dashboard/page.tsx` to persist the real `POST /api/v1/document/analyze-full` response for cross-screen reuse.
- Updated `frontend/src/components/dashboard/Sidebar.tsx` with `/historical-analysis` navigation.
- Extended `frontend/src/app/globals.css` with responsive `ha-*` historical analysis dashboard styles.
- Backend/RAG/Kraken/Ollama/Qdrant/document-analysis pipeline remained frozen.
- Verification: real HTTP endpoint PASS with real Ottoman PNG, HTTP 200, `ocr.engine=kraken`, `fallback_used=false`, 22 document evidence, 5 verified external evidence, 6 model inference records.
- Verification: browser E2E PASS for route/sidebar, source cards, provenance, document/external/model separation, uncertainty, relationship unavailable state, citation copy, no raw path leak and no console errors.
- Verification: frontend lint PASS 0 errors / 11 existing warnings; frontend build PASS; backend unknown-document pipeline regression 3 passed.
- Evidence: `evidence/historical_analysis_dashboard_gate/`.

## 2026-08-13 - TASK-IMAGE-PROCESSING-LAB-PRODUCTION-INTEGRATION
- Added `frontend/src/app/(app)/image-processing-lab/page.tsx` dedicated Image Processing Lab screen.
- Added lab CSS in `frontend/src/app/globals.css` and sidebar entry in `frontend/src/components/dashboard/Sidebar.tsx`.
- Updated `frontend/src/lib/api.ts` `ImageVariantResponse` to include real preprocessing `parameters`.
- Updated `backend/app/api/routes/preprocessing.py` to expose existing stored `parameters`/`page_id` metadata in preprocessing responses and variant list responses.
- Updated `backend/tests/test_document_upload_integration.py` to assert preprocessing response parameters.
- Verification: real Playwright E2E PASS with real document and real preprocessing endpoint; frontend lint/build PASS; backend targeted preprocessing tests 18 passed.
- Evidence: `evidence/image_processing_lab_gate/`.

## 2026-08-13 - TASK-PRODUCTION-MAIN-DASHBOARD-INTEGRATION
- Added `analysisApi.analyzeFull` in `frontend/src/lib/api.ts` for real multipart `POST /api/v1/document/analyze-full` calls with upload progress and auth token support.
- Replaced `frontend/src/app/(app)/dashboard/page.tsx` with a production document analysis workspace: upload/preview, real endpoint execution, Ottoman OCR, transliteration, modern Turkish, entities, historical analysis, confidence, uncertainty, document evidence and external historical sources.
- Extended `frontend/src/app/globals.css` with responsive production dashboard styles.
- Fixed frontend lint errors in `frontend/src/components/auth/AuthShell.tsx` and `frontend/src/components/dashboard/Header.tsx`.
- Verification: Playwright real HTTP E2E PASS, 22 checks; HTTP 200; `ocr.engine=kraken`; `fallback_used=false`; document evidence 22 and external historical evidence 5 rendered.
- Verification: `npm.cmd run lint` PASS with 0 errors / 11 existing warnings; `npm.cmd run build` PASS.
- Evidence: `evidence/main_dashboard_gate/dashboard_integration_report.json`, `api_request_evidence.json`, `api_response_snapshot.json`, `dashboard_screenshot.png`, `frontend_build.txt`, `frontend_tests.txt`.

## 2026-08-13 - TASK-UNKNOWN-DOC-PIPELINE
- Added `backend/app/services/document_analysis_pipeline.py` production orchestration service.
- Added `backend/app/api/routes/document_analysis.py` with `POST /api/v1/document/analyze-full`.
- Added `backend/app/schemas/document_analysis.py` structured response schema.
- Updated `backend/app/api/router.py` to include the new document analysis route.
- Updated `backend/app/services/transliteration_service.py` so LLM transliteration uses existing `OllamaProvider` instead of TODO/NotImplemented.
- Updated `backend/app/services/document_processing/ocr_engine.py` with a narrow low-confidence digit-noise line filter repair required by existing OCR regression tests.
- Added `backend/tests/test_unknown_document_pipeline.py` with endpoint integration and evidence filtering tests.
- Updated `backend/pytest.ini` marker registration.
- Verification: baseline targeted 23 passed; final relevant backend set 55 passed; final unknown/OCR/FAISS set 16 passed; Ollama health PASS; Qdrant verified-only count/search PASS.

## 2026-08-13 - TASK-KRAKEN-DEFAULT-LIVE-HTTP-GATE
- Ran real Uvicorn server for `POST /api/v1/document/analyze-full`.
- Used real Ottoman input `backend/uploads/originals/9/pages/page_1.png`.
- Captured evidence under `backend/evidence/kraken_live_http_gate/`.
- Verified response `ocr.engine=kraken`, `ocr.fallback_used=false`, OCR text length 1148, 23 lines, transliteration length 1273, modern Turkish length 1271, historical evidence count 5.
- Verified regression command `python -m pytest tests/test_unknown_document_pipeline.py tests/test_ocr_engine.py tests/test_faiss_security.py tests/test_kraken_integration.py -q` -> 22 passed.
- No code changes were made for this gate. Production DB was copied to evidence DB; Qdrant data and OCR models were not modified.
- Risk recorded: OpenCV `imread` failed on non-ASCII workspace upload path in first attempt; final gate used ASCII test upload dir without changing OCR default.

## 2026-08-11 Manual Runtime Start
- `LOCAL_RUNTIME_ONLINE`: Backend, frontend ve OCR worker calistirildi.
- Kanit: Backend `/health` HTTP 200; frontend `/login` HTTP 200; worker startup logu mevcut.
- Kod degisikligi yok; `frontend/.next` production build artefakti yeniden uretildi.

## 2026-08-11 GPU Runtime Optimization
- `KRAKEN_CUDA_BRIDGE_PASS`: `backend/scripts/kraken_wsl_bridge.py` CUDA runtime ayarlari ve GPU metadata'si ile guncellendi.
- Kanit: Direct bridge smoke `status=success`, `device=cuda`, `cuda_available=true`, `cuda_device_name=NVIDIA GeForce RTX 4050 Laptop GPU`.
- Test: `tests/test_kraken_integration.py` PASS, 6 passed.

**Ozet:** Bu oturumda yalniz wiki Markdown dosyalari olusturuldu. Kaynak kod, konfig, bagimlilik, veritabani ve kullanici verisi degistirilmedi. Degisiklikler [[Index]] uzerinden erisilebilir.

**Kutuphaneler:** Yok.

**Baglantilar:** [[Index]], [[Latest_Handoff]], [[Task_Queue]]

## 2026-07-28
- `/docs/wiki` klasor yapisi olusturuldu.
- Sistem wiki dosyalari olusturuldu/guncellendi.
- Mimari ve kaynak haritalari yazildi.
- Risk ve acik soru kayitlari yazildi.
- Bagimlilik sirali gorev kuyruÄŸu yazildi.

## Kod Degisiklikleri
- Yok.

## BASELINE-001
- 2026-07-28: RECOVER baseline calistirildi.
- `evidence/recover_baseline/` altinda envanter, ortam, git, dependency, import, lint, build ve pipeline smoke kanitlari saklandi.
- `TASK-008 - Gereksinim Izlenebilirlik Matrisi` READY yapildi.
- Sonraki prompt `PROMPTS/02_REQUIREMENTS_TRACEABILITY.md` olarak belirlendi.

## TASK-008
- 2026-07-28: `PROMPTS/02_REQUIREMENTS_TRACEABILITY.md` partial olarak uygulandi.
- `docs/wiki/08_Testing/Requirements_Traceability_Matrix.md` olusturuldu.
- `docs/wiki/08_Testing/Acceptance_Criteria_Map.md` olusturuldu.
- `docs/wiki/09_Decisions/ADR-001_NextJS_Frontend.md` proposed olarak olusturuldu.
- [[Image_Preprocessing]] ve [[Database_Model]] status degerleri baseline celiskilerine gore `partial` yapildi.
- `docs/wiki/00_System/Task_Queue.md` gereksinim bagimlilik sirasina gore yeniden yazildi.
- SRS PDF tam metni cikarilamadigi icin TASK-008 BLOCKED kaldi; gelistirme promptuna gecilmedi.

## TASK-009
- 2026-07-28: Environment ve test gate tamamlandi.
- `backend/requirements-dev.txt`, `backend/tests/test_smoke.py` ve `scripts/doctor.ps1` eklendi.
- Backend pytest, frontend lint/build ve doctor kanitlari `evidence/environment_gate/` altinda saklandi.

## TASK-010
- 2026-07-28: Data storage/versioning gate tamamlandi.
- Alembic initial migration eklendi.
- OCR sonucu, text version, entity, chat, citation, export ve model registry icin temel SQLAlchemy modelleri eklendi.
- Migration upgrade/downgrade ve metadata izlenebilirlik testleri PASS oldu.

## TASK-011
- 2026-07-28: Auth, rol/belge izolasyonu, file security unit testleri ve dependency audit gate tamamlandi.
- `backend/tests/test_auth_security.py` ve `backend/tests/test_file_security.py` eklendi.
- `frontend/package.json` ve `frontend/package-lock.json` security overrides ile guncellendi.
- Backend pytest 14 PASS, doctor full PASS, frontend lint/build PASS ve npm audit high 0 vulnerability kanitlandi.

## TASK-012
- 2026-07-28: Belge yukleme, dosya guvenligi, page/thumbnail, delete cleanup, audit ve preprocessing integration gate tamamlandi.
- `backend/tests/test_document_upload_integration.py` eklendi.
- `backend/app/api/routes/preprocessing.py` response model `created_at` tipi datetime olarak duzeltildi.
- Backend pytest 19 PASS ve doctor full PASS kanitlandi.

## TASK-013
- 2026-07-28: PDF sayfalama ve thumbnail gate tamamlandi.
- Poppler yoklugunda Windows-native calisma icin `pypdfium2==5.12.1` fallback eklendi.
- Iki sayfali PDF fixture upload, page order ve thumbnail uretimi testlendi.
- Backend pytest 20 PASS ve doctor full PASS kanitlandi.

## TASK-015
- 2026-07-28: Preprocessing pipeline sozlesmesi tamamlandi.
- `ImagePreprocessor.process(image, profile)` eklendi ve ortak preprocessing mantigi `_apply_params` altina alindi.
- `backend/tests/test_processing_pipeline.py` eklendi.
- Backend pytest 22 PASS ve doctor full PASS kanitlandi.

## TASK-016
- 2026-07-28: Layout line detection ve RTL reading order gate tamamlandi.
- `backend/app/services/document_processing/layout.py` eklendi.
- `backend/tests/test_layout_analysis.py` eklendi.
- Backend pytest 25 PASS ve doctor full PASS kanitlandi.

## TASK-017
- 2026-07-28: OCR adapter ve model dependency gate tamamlandi.
- `OCREngine` metadata/fallback adapter haline getirildi.
- `backend/tests/test_ocr_engine.py` eklendi.
- Backend pytest 28 PASS ve doctor full PASS kanitlandi.

## TASK-018
- 2026-07-28: OCR review ve duzeltme audit akisi backend API olarak tamamlandi.
- `backend/app/api/routes/ocr_review.py` eklendi ve router'a baglandi.
- `backend/tests/test_ocr_review.py` eklendi.
- Ham OCR korunarak `TextVersion(version_type="ocr_correction")` uzerinden duzeltme gecmisi tutuldu.
- `AuditLog(action="ocr.correction.create")` eski/yeni metin kanitiyla testlendi.
- Backend pytest 31 PASS ve doctor full PASS kanitlandi.

## TASK-019
- 2026-07-28: Transliterasyon servisi source-mapped ve testlenebilir hale getirildi.
- `Translator.transliterate_line` OCR satir id, line no, ambiguity candidates, confidence ve method version dondurur.
- `POST /api/v1/transliteration/ocr-results/{ocr_result_id}` Latin ciktiyi ham OCR'den ayri `TextVersion(version_type="transliteration")` olarak kaydeder.
- Correction history `previous_text` ve `source_version_id` ile testlendi.
- Fixture evaluation icin CER/WER/chrF metrikleri eklendi.
- Backend pytest 36 PASS ve doctor full PASS kanitlandi.

## TASK-020
- 2026-07-28: Modernizasyon ve ozetleme backend fallback akisi eklendi.
- Faithful/plain/summary modlari ayri `TextVersion` turleriyle saklandi.
- Kaynak text version baglantisi, prompt-injection warning, okunamayan alan isareti ve audit testlendi.
- Backend pytest 40 PASS ve doctor full PASS kanitlandi.

## TASK-021
- 2026-07-28: NER, tarih normalizasyonu ve glossary backend fallback akisi eklendi.
- `NERExtractor` rule-based PER/LOC/ORG/DATE/GLOSSARY ciktisi, offset, confidence ve metadata uretir.
- `POST /api/v1/analysis/text-versions/{text_version_id}/entities` entity storage ve user correction audit akisini saglar.
- Precision/recall/F1 smoke ve OCR impact report testlendi.
- Backend pytest 44 PASS ve doctor full PASS kanitlandi.

## TASK-022
- 2026-07-28: Confidence policy ve model registry service eklendi.
- `ConfidenceManager` skor clamp/label/fallback politikasi uretir.
- `ModelRegistryService` OCR, transliteration, modernization ve NER descriptorlarini idempotent kaydeder.
- Operation metadata confidence ve model bilgisiyle testlendi.
- Backend pytest 48 PASS ve doctor full PASS kanitlandi.

## RECOVER-20260802
- 2026-08-02: Release gate yeniden dogrulandi; onceki `V1.1.0 RELEASED` iddiasi `PARTIAL` olarak duzeltildi.
- `frontend/src/lib/api.ts`, `frontend/src/app/documents/[id]/page.tsx` ve `frontend/src/app/settings/page.tsx` TypeScript lint/build hatalari icin dar kapsamda duzeltildi.
- `scripts/doctor.ps1` backend test adimi `pytest tests` kullanacak sekilde duzeltildi.
- `backend/requirements.txt` icinde `easyocr==1.7.2`, `pytest-asyncio==1.4.0` ve `chromadb==1.5.9` kaydi netlestirildi.
- `easyocr` ve `pytest-asyncio` proje venv ortaminda kuruldu; `pip` 26.2'ye yukseltildi.
- Kanitlar: `python -m pytest tests -q` PASS (70 passed), `npm.cmd run lint` PASS (0 error, 1 warning), `npm.cmd run build` PASS, `scripts/doctor.ps1` PASS (`DOCTOR_FAILED=0`), live `/health` PASS, live register/login PASS, `backend/scripts/test_real_ocr.py` PASS.
- Kalan blokaj: `pip-audit` FAIL, `chromadb 1.5.9 / PYSEC-2026-311` ve `ecdsa 0.19.2 / PYSEC-2026-1325`.

## RECOVER-20260802 Security Completion
- 2026-08-02: Dependency audit blokaji kapatildi ve release gate `PASS` durumuna getirildi.
- `backend/app/core/security.py` `python-jose` yerine `PyJWT[crypto]==2.13.0` kullanacak sekilde guncellendi.
- `backend/app/services/chat/embeddings.py` ChromaDB yerine FAISS + sentence-transformers tabanli kalici yerel vector index olarak yeniden uygulandi.
- `backend/requirements.txt` icinden `chromadb` ve `python-jose[cryptography]` kaldirildi; `PyJWT[crypto]==2.13.0` eklendi.
- Venv icinden `chromadb`, `python-jose` ve `ecdsa` kaldirildi; PyJWT 2.13.0 kuruldu.
- `frontend/src/app/layout.tsx` font yukleme uyarisi `next/font/google` ile kapatildi.
- Kanitlar: `python -m pip_audit` PASS (`No known vulnerabilities found`), `npm.cmd audit --audit-level=high` PASS, `python -m pytest tests -q` PASS (70 passed), `scripts/doctor.ps1` PASS, `npm.cmd run lint` PASS, `npm.cmd run build` PASS, live health/auth smoke PASS.

## UI-FIX-20260802
- 2026-08-02: Belge detay ekraninda auth gerektiren sayfa/thumbnail/islenmis gorsel endpointleri icin kirik `<img>` davranisi giderildi.
- `frontend/src/lib/api.ts` icine `fetchAuthenticatedBlobUrl` eklendi; Bearer token ile gorsel/dosya indirip object URL uretir.
- `frontend/src/app/documents/[id]/page.tsx` icinde `AuthenticatedImage` bileseni eklendi; thumbnail, orijinal sayfa ve islenmis varyant gorselleri bu bilesene tasindi.
- OCR sonucu hazir belge sayfasi yenilendiginde `ocrApi.getJobStatus` ile sonuc state'i tekrar doldurulacak sekilde guncellendi.
- `Sonuclari Incele` butonundaki placeholder `alert("Sonuclari incele ekrani")` kaldirildi; buton orta paneldeki OCR/metin/NER sonuc gorunumune geciyor.
- Kanitlar: `npm.cmd run lint` PASS, `npm.cmd run build` PASS, `powershell -ExecutionPolicy Bypass -File scripts/doctor.ps1` PASS (`DOCTOR_FAILED=0`, backend 70 passed).

## GROUND_TRUTH_INFRASTRUCTURE_FINAL_GATE
- 2026-08-02: Ground Truth altyapi final gate onarildi ve dogrulandi.
- `scripts/doctor.ps1` backend unit/regression kapisindan live browser E2E testini ayirdi; browser E2E ayri evidence runner ile dogrulandi.
- EasyOCR model manifesti SHA-256 checksum/butunluk, dosya boyutu, schema ve offline download politikasini zorunlu kontrol edecek sekilde sertlestirildi.
- Ground Truth API owner-scoped list/page/export/save davranislari ve testleri genisletildi.
- Annotation Studio API-backed dataset/page/line editing, save, lock ve export akisina guncellendi.
- Kanitlar: `evidence/ground_truth_final_gate/FINAL_GATE_REPORT.md`, backend active/clean 90 passed, doctor `DOCTOR_FAILED=0`, browser E2E PASS, health/auth smoke PASS.

## GROUND_TRUTH_FINAL_GATE_SUPPLEMENTAL_VERIFICATION
- 2026-08-02: PyTorch CPU wheel pip-audit kapsam acigi tamamlayici provenance, SHA-256 checksum, RECORD hash karsilastirmasi, OSV ve resmi PyTorch advisory kontroluyle kapatildi.
- Git PATH bulunamadigi icin kalici PATH degistirilmedi ve otomatik kurulum yapilmadi; esdeger kaynak envanteri, hash manifesti, secret marker ve buyuk dosya incelemesi uretildi.
- Kanitlar: `evidence/ground_truth_final_gate_supplement/FINAL_SUPPLEMENTAL_REPORT.md`, `torch_provenance_and_hash.txt`, `torch_advisory_verification.md`, `git_discovery.txt`, `secret_and_large_file_review.txt`, `regression_after_changes.txt`.

## GROUND_TRUTH_INFRASTRUCTURE_FINAL_GATE
- 2026-08-02: Final regression gate PASS: backend 91 passed, doctor DOCTOR_FAILED=0, frontend lint/typecheck/build/audit PASS, browser E2E PASS, FAISS/model/worker/migration/real OCR smoke PASS.
- Test harness loop cakismasi giderildi: backend/tests/test_file_security.py, test_ocr_engine.py, test_processing_pipeline.py, test_worker.py.
- Browser E2E mevcut Annotation Studio UI sozlesmesine guncellendi.
- Proje genel durumu PARTIAL/BLOCKED_GROUND_TRUTH_REQUIRED olarak korundu; CER/WER ground-truth olmadan raporlanmadi.

## TASK-034-Q2
- 2026-08-02: Ozgun/izinli ground truth veri hazirlik yapisi olusturuldu: `evidence/ocr_quality_real/input/images`, `input/transcriptions`, `input/metadata.csv`.
- `scripts/validate_ground_truth_dataset.py` eklendi; image/transcription eslesmesi, metadata, SHA-256, UTF-8, empty text, control chars, NFC, tatweel/diacritics, RTL, duplicate hash, low resolution, optional split leakage, optional bbox/reading-order sidecar kontrolleri yapar.
- `backend/tests/test_ground_truth_dataset_validator.py` eklendi; validator 7 test PASS.
- Annotation Studio sol paneline veri hazirlik/ownership ve OCR output kullanmama notu eklendi.
- Proje-kodu warning kaynaklari duzeltildi: Pydantic `orm_mode`, sentence-transformers embedding dimension deprecation fallback, FastAPI 413 status constant, Alembic `path_separator`.
- Kanitlar: validator dry-run `BLOCKED_USER_DATA_REQUIRED`, backend 97 passed/32 third-party warnings, frontend lint 0 warning/build PASS.
- Browser E2E bu oturumda controllable browser olmadigi icin `BLOCKED_BROWSER_UNAVAILABLE`; OCR kalite metrikleri gercek veri olmadan uretilmedi.
- 2026-08-02: Kullanici tarafindan saglanan `ground_truth_osmaluca_pilot_draft.zip` ingest edildi; zip SHA-256 ve internal `MANIFEST.sha256` PASS.
- Paket `evidence/ocr_quality_real/input/` altina alindi: 3 sayfa, 3 transkripsiyon, 73 satir, 300 DPI.
- Validator `ASSISTED_ANNOTATION_DRAFT`, `human_verified=false`, `reviewer=PENDING_HUMAN_REVIEW` durumunu `BLOCKED_HUMAN_REVIEW_REQUIRED` olarak yakalayacak sekilde sertlestirildi.
- Kanitlar: `validator_after_zip_import.txt`, `source_zip_provenance.md`, `source_zip_manifest_verification.json`, `backend_target_tests_after_zip.txt` (15 passed).

## TASK-034-Q3
- 2026-08-02: Human review workflow API/UI/worker kapisi eklendi.
- `backend/app/models/ground_truth.py` review status, review flags ve `GroundTruthReviewAudit` modelini icerir.
- `backend/app/api/routes/ground_truth.py` pilot draft import, progress, authenticated line review, ready-to-lock ve dataset lock endpointleriyle genisletildi.
- `backend/worker.py` `pilot_ocr_evaluation` job tipini isler; job yalniz dataset lock sonrasinda olusur.
- `frontend/src/app/dashboard/annotation-studio/page.tsx` API-backed insan review ekranina donusturuldu; bos dataset durumunda pilot draft otomatik hazirlanir.
- Canli SQLite Alembic revision `20260802_0002` seviyesine getirildi; yarim kalmis Alembic temp tablosu 0 satir oldugu kanitlanarak temizlendi.
- Kanitlar: `evidence/human_review_gate/FINAL_HUMAN_REVIEW_GATE_REPORT.md`, backend targeted tests 4 passed, frontend lint/build PASS, live smoke PASS.

## POST_REVIEW_RECONCILIATION
- 2026-08-02: Stale pre-review snapshot ile canli UI/DB celiskisi canli DB/API sorgulariyla cozuldu.
- Dataset `2` canli DB'de `LOCKED`, `human_verified=true`, review `73/73`, pending `0` olarak dogrulandi.
- Job #1 pending durumdaydi; duplicate job olusturulmadan ayni kayit gercek EasyOCR pilot evaluation ile `completed` durumuna getirildi.
- `backend/worker.py` `pilot_ocr_evaluation` yolu placeholder yerine `pilot_metrics.json`, `pilot_page_metrics.csv`, `pilot_error_analysis.md` uretir hale getirildi.
- OCR karar: `PILOT_FAIL_NEEDS_MODEL_IMPROVEMENT`; strict CER `0.464879`.
- Kanitlar: `evidence/post_review_reconciliation/POST_REVIEW_RECONCILIATION_REPORT.md`, `FINAL_PILOT_OCR_QUALITY_REPORT.md`.


## BOOTSTRAP-REFRESH-20260802
- 2026-08-02: Zorunlu baslangic protokolu tekrar uygulandi ve mevcut wiki/kod envanteri hizalandi.
- `Index.md` icindeki eski planned RAG/export/evaluation satirlari mevcut route/servis/test kanitlarina gore duzeltildi.
- `Architecture_Map.md` icindeki eski "background job yok", "chat/RAG bos" ve statik CORS iddialari guncel kodla hizalandi.
- `Evaluation_Service.md` servis/test kanitlariyla `partial` yapildi; human-verified OCR kalite gate'i blokaj olarak korundu.
- `99_Templates` altinda zorunlu wiki sablonlari eklendi.
- Kod degisikligi: Yok.

## TASK-034-Q4
- 2026-08-02: OCR pipeline diagnosis/optimization v1 tamamlandi.
- `backend/app/services/evaluation/ocr_pipeline_optimization.py` eklendi: IoU, duplicate suppression, RTL grouping, reading-order accuracy ve config freeze helpers.
- `backend/tests/test_ocr_pipeline_optimization.py` eklendi; RTL/IoU/duplicate/config tests PASS.
- `scripts/optimize_ottoman_ocr_pipeline.py` eklendi; locked pilot dataset'i salt-okunur kullanarak recognition-only, detection-only ve full-pipeline metrikleri uretir.
- Evidence: `evidence/ocr_pipeline_optimization_v1/*`; overlay gorselleri uretildi.
- Test split sonucu esikleri gecmedi: normalized WER `0.523707`, line F1 `0.047458`, reading-order `0.0`; karar `PILOT_FAIL_NEEDS_FURTHER_IMPROVEMENT`.

## STARTUP-REFRESH-20260803
- 2026-08-03: `start.bat` guncel live workflow'a gore yenilendi.
- Script artik environment check, Alembic migration, duplicate worker/backend/frontend korumasi, FastAPI/Next.js baslatma ve health/link ozeti verir.
- `README.md` start linkleri, `start.bat --check` dry-run ve guncel OCR karar notuyla guncellendi.
- Kanit: `evidence/start_bat_check_20260803.txt` -> `CHECK_ONLY=PASS`.

## TASK-034-Q5
- 2026-08-03: Line segmentation metric validation ve RTL reconstruction Q5 tamamlandi.
- `backend/app/services/evaluation/ocr_pipeline_optimization.py` logical line clustering, projection-profile bands, hybrid line assembly, raw component coverage ve pairwise reading-order metrics ile genisletildi.
- `backend/tests/test_line_segmentation_q5.py` eklendi; perfect match, fragmented line, RTL order, reversed order, missing/extra/duplicate, one-to-many/many-to-one, deterministic grouping, projection profile, GT leakage ve config freeze testlerini kapsar.
- `scripts/line_segmentation_q5.py` eklendi; locked dataset `2` icin Page 1 development, Page 2-3 pilot_validation ayrimini koruyarak Q5 evidence uretir.
- Secilen strategy `B_projection_profile`; pilot_validation logical line F1 `0.961538`, matched coverage `1.0`, pairwise reading-order `1.0`, normalized CER `0.562557`, normalized WER `0.870690`.
- Karar: `Q5_PARTIAL_FURTHER_IMPROVEMENT_REQUIRED`; satir/okuma sirasi iyilesti, recognition quality halen hedef disi.
- Kanitlar: `evidence/line_segmentation_q5/FINAL_LINE_SEGMENTATION_Q5_REPORT.md`, `targeted_tests.txt` (20 passed), `backend_regression.txt` (119 passed), `doctor_gate.txt` (`DOCTOR_FAILED=0`).

## TASK-034-Q6
- 2026-08-03: Hybrid Ottoman line recognition ve word reconstruction Q6 tamamlandi.
- `backend/app/services/evaluation/ocr_pipeline_optimization.py` component-to-line assignment, RTL word reconstruction, Arabic script ratio ve candidate scoring helpers ile genisletildi.
- `backend/tests/test_hybrid_recognition_q6.py` eklendi; one-to-one assignment, ambiguous tie-break, duplicate suppression, RTL/gap/punctuation/number reconstruction, candidate scoring, leakage ve config hash tests kapsar.
- `scripts/hybrid_recognition_q6.py` eklendi; Q5 frozen projection layout ile Q4 full-page component recognition ciktisini birlestirerek Q6 evidence uretir.
- Secilen config `component_filter_lowconf`; pilot_validation normalized CER `0.130635`, strict CER `0.131555`, logical line F1 `0.961538`, overall reading-order `1.0`, normalized WER `0.706897`.
- Karar: `Q6_PARTIAL_WORD_BOUNDARY_IMPROVEMENT_REQUIRED`; CER hedefleri gecti, WER/word-boundary hedefi gecmedi.
- Kanitlar: `evidence/hybrid_recognition_q6/FINAL_HYBRID_RECOGNITION_Q6_REPORT.md`, `targeted_tests.txt` (28 passed), `backend_regression.txt` (122 passed), `doctor_gate.txt` (`DOCTOR_FAILED=0`).


## 2026-08-02 - VERIFY-LIVE-EVAL-20260802
- Canli DB yolu `backend/ottoman_assistant.db` olarak dogrulandi; root `ottoman_assistant.db` canli DB degil.
- Dataset `2` `LOCKED`, `73/73` text+bbox reviewed ve `73/73` `human_verified=true` olarak dogrulandi.
- Evaluation job `1` duplicate olusturulmadan `completed`/`100.0` olarak dogrulandi; stale result dosyasi DB `result_summary` ile yeniden yazildi.
- `backend/worker.py` icinde `pilot_ocr_evaluation` evidence ciktilari job `result_path` sozlesmesine baglandi; paylasimli `pilot_metrics.json` uzerine yazma riski kapatildi.
- `backend/tests/test_worker_robustness.py` icine job result path kaynak-sozlesme regresyon testi eklendi.
- Test kanitlari: `evidence/verify_live_state_20260802/backend_full_tests.txt`, `frontend_lint.txt`, `frontend_build.txt`, `evaluation_job_smoke.txt`.

## 2026-08-03 TASK-034-Q5 OCR Quality Improvement
- Pilot OCR quality gate PASS: strict CER `0.1264949402023919`, strict WER `0.5493975903614458`, line F1 `0.9615384615384615`, reading-order `1.0`.
- Selected config `recognition_beam_merged`, SHA-256 `d8dd6e820ec10d26af259853fff61d4fd78920c5993fdd073e4fc36caa5ea05a`.
- `backend/app/services/document_processing/ocr_engine.py` now records Q5 config metadata and returns GT-independent merged RTL line outputs from EasyOCR components.
- `backend/app/services/evaluation/ocr_pipeline_optimization.py` gained Q5 component cleanup, nested-box removal and adjacent line merge helpers.
- Regression evidence: `evidence/line_segmentation_q5/backend_full_tests_after_production_bind.txt`, `ocr_q5_unit_tests_after_production_bind.txt`, `layout_rtl_tests.txt`, `evaluation_tests.txt`, `worker_tests.txt`, `frontend_lint.txt`, `frontend_build.txt`, `production_ocr_smoke.txt`, `evidence/ground_truth_final_gate/frontend_browser_e2e.txt`.

## 2026-08-07: TASK-007 Annotation Export API
- ExportRepository ve ExportService ile PAGE XML ve Kraken dışa aktarımı oluşturuldu.
- Path traversal güvenlik denetimi eklendi.
- SQLite şemasında 'annotation_lines' tablosuna 'split_name' alanı eklendi.
- HTTP contract testleri dahil 47/47 pytest testine ulaşıldı.

## 2026-08-09 TASK-008 Reference UI Dilimi
- `frontend/src/app/dashboard/page.tsx`, `frontend/src/app/upload/page.tsx`, `frontend/src/app/settings/page.tsx`, `frontend/src/app/documents/[id]/page.tsx` duplicate route dosyalari kaldirildi; aktif route'lar `(app)` group altinda.
- `frontend/src/app/(app)/layout.tsx` React lint uyumlu hale getirildi.
- `frontend/src/app/(app)/documents/[id]/page.tsx` OCR line/bbox/confidence, transliterasyon, modernizasyon, NER ve ozet state davranislari gercek API alanlariyla hizalandi.
- `frontend/src/lib/api.ts` OCR line/bbox/transliterated/summary alanlariyla genisletildi.
- `evidence/ui_reference_implementation/` altina lint/build/route smoke/API integration/reference comparison raporlari eklendi.
- Test: `npm.cmd run lint` PASS; `npm.cmd run build` PASS.
- Sonuc: UI_FUNCTIONAL_REPAIR_REQUIRED; backend E2E ve screenshot kaniti eksik.

## 2026-08-09 TASK-008 Reference UI Completion Pass
- `frontend/src/app/(app)/documents/[id]/page.tsx` referans gorseldeki uc kolonlu belge analizi duzenine cevrildi.
- `frontend/src/app/globals.css` referans belge analiz ekrani icin grid, viewer, OCR tablo, sag panel, bottom cards, confidence widget ve bbox overlay stilleriyle genisletildi.
- `frontend/src/lib/api.ts` OCR confidence bucket alanlariyla genisletildi.
- Test: `npm.cmd run lint` PASS; `npm.cmd run build` PASS; `/documents/1` HTTP 200.
- Gorsel: Headless Chrome screenshot denemesi `evidence/ui_reference_implementation/screenshots/document-workspace-route.png` uretti, ancak auth olmadigi icin login ekrani yakalandi.
- Sonuc: UI_CODE_READY_BACKEND_E2E_PENDING; backend E2E ve authenticated reference screenshot kaniti eksik.

## 2026-08-09 TASK-008 Complete UI E2E and Visual Acceptance
- Backend timeout root cause bulundu: port 8000'de aktif FastAPI listener yoktu; migration PASS ve Uvicorn startup PASS ile giderildi.
- `backend/.env` icindeki aktif OCR engine `trocr` -> `kraken` yapildi; Kraken model dosyasi degistirilmedi ve SHA dogrulandi.
- `frontend/src/app/(app)/documents/[id]/page.tsx` mevcut completed OCR sonucunu document status'una bagli kalmadan yukleyecek sekilde duzeltildi.
- NER payload normalizasyonu backend'in dict/object sonucunu destekleyecek sekilde duzeltildi.
- `mock-ocr-table` CSS/class adi `ocr-results-table` olarak temizlendi.
- Kanitlar: `evidence/ui_reference_implementation/`; lint PASS; build PASS; real auth/upload/Kraken OCR E2E PASS; Playwright screenshots PASS.
- Sonuc: `REFERENCE_UI_IMPLEMENTATION_PASS`.
## 2026-08-09 Premium Auth UI
- `frontend/src/components/auth/AuthShell.tsx` eklendi.
- `frontend/src/app/login/page.tsx` premium koyu tema login ekranı olarak yeniden yazıldı.
- `frontend/src/app/register/page.tsx` yeni kayıt ekranı olarak eklendi.
- `frontend/src/app/globals.css` auth tasarım sistemi, responsive layout, form, kart ve hero görsel stilleriyle genişletildi.
- `frontend/src/lib/api.ts` remember-me için local/session storage token davranışıyla geriye uyumlu biçimde güncellendi.
- Kanıtlar `evidence/auth_ui_implementation/` altına kaydedildi.

## 2026-08-09 Windows Runtime Launcher
- `scripts/runtime_launcher.ps1` eklendi; START/STOP/RESTART/STATUS/HEALTH aksiyonları ve PID güvenliği merkezi hale getirildi.
- `START_APP.bat`, `STOP_APP.bat`, `RESTART_APP.bat`, `STATUS_APP.bat`, `HEALTH_CHECK.bat`, `START_BACKEND.bat`, `START_FRONTEND.bat`, `FIRST_RUN_SETUP.bat` eklendi.
- `frontend/src/lib/api.ts` default API URL `http://127.0.0.1:8000/api/v1` olacak şekilde hizalandı.
- `HOW_TO_RUN.md` eklendi.
- Kanıtlar `evidence/runtime_launcher/` altına kaydedildi.

## 2026-08-09 Downstream Text Repair
- `backend/app/services/document_processing/translator.py` deterministik v2 transliteration/modernization kurallari, Osmanlica/Turkce kelime sozlugu, duplicate-output guard, unreadable marker korumasi ve summary fallback ile yenilendi.
- `backend/app/services/document_processing/pipeline.py` `modernized_text`, `summary_text` ve `transformation_quality` alanlarini uretecek sekilde hizalandi.
- `backend/app/api/routes/ocr.py` OCR status wrapper icinde `summary_text` ve `transformation_quality` alanlarini frontend `pipeline_results` payload'ina tasir.
- `backend/tests/test_transliteration.py`, `backend/tests/test_modernization.py`, `backend/tests/test_processing_pipeline.py` yeni kalite sozlesmesine guncellendi.
- Kanitlar `evidence/downstream_text_repair/` altina kaydedildi.
- Test: `python -m pytest tests/test_transliteration.py tests/test_modernization.py tests/test_processing_pipeline.py` PASS; `npm.cmd run lint` PASS; `npm.cmd run build` PASS.
- Sonuc: `DOWNSTREAM_TEXT_REPAIR_PASS`.

## 2026-08-09 Line Filter Repair
- `backend/app/services/document_processing/ocr_engine.py` line-filter-v1 kalite kapilari, foreground/connected-component analizi, garbage OCR suppression, decorative/non-Ottoman component filtering ve bbox ink-refinement ile genisletildi.
- Kraken segmenter ciktilari recognition oncesi filtrelenir; recognition sonrasi metin/confidence kapilari ikinci kez uygulanir; EasyOCR/Tesseract/TrOCR fallback yollarinda ayni kalite filtresi kullanilir.
- `backend/app/services/document_processing/pipeline.py` OCR line payload'ina `page_id` ekler; `backend/worker.py` job page id bosken gercek page id tasir.
- `frontend/src/lib/api.ts` ve `frontend/src/app/(app)/documents/[id]/page.tsx` multi-page UI icin selected-page line filtering sozlesmesine hizalandi.
- Gercek Kraken run kaniti: `before_lines.json` 25 line -> `after_lines.json` 23 line; header/footer/dekoratif phantom boxes kaldirildi; `actual_engine=kraken`, `fallback_used=false`.
- Kanitlar `evidence/line_filter_repair/` altina kaydedildi; model SHA degismedi.
- Test: `python -m pytest tests/test_ocr_engine.py tests/test_layout_analysis.py tests/test_processing_pipeline.py` PASS (13 passed); frontend `npm.cmd run lint` PASS; `npm.cmd run build` PASS.
- Sonuc: `LINE_FILTER_REPAIR_PASS`.

## 2026-08-09 Final Text and Segmentation Check
- Line filtering ve downstream text repair birlikte ayni gercek belge sayfasinda dogrulandi.
- `evidence/final_text_and_segmentation_check/final_api_payload.json` API-style `result.pipeline_results` sozlesmesiyle uretildi.
- `final_runtime_metadata.json` -> `line_count=23`, `bbox_count=23`, `blank_line_count=0`, `low_usefulness_line_count=0`, `recognizer=kraken`, `fallback_used=false`.
- `transliterated_text` raw OCR'den farkli; `modernized_text` transliteration kopyasi degil; summary ve NER payload dolu.
- `final_ui_check.txt` document workspace panel mapping'ini OCR/Latin/modern/summary/NER/bbox icin dogrular.
- Test: backend targeted 22 passed; frontend `npm.cmd run lint` PASS; `npm.cmd run build` PASS.
- Sonuc: `TEXT_AND_SEGMENTATION_FINAL_PASS`.

## 2026-08-09 Auth Reference Match
- `frontend/src/components/auth/AuthShell.tsx` kullanicinin login/register referanslarindaki centered premium sahneye gore yeniden yazildi.
- `frontend/src/app/login/page.tsx` temiz Turkce metinler, real login entegrasyonu ve password visibility kontroluyle guncellendi.
- `frontend/src/app/register/page.tsx` referans gorseldeki alan sirasi ve sade kart yogunluguna gore guncellendi; real register entegrasyonu korundu.
- `frontend/src/app/globals.css` koyu/altin auth sahnesi, manuscript OCR motif, mosque silhouette, glass card, ornament line ve responsive stillerle genisletildi.
- Kanitlar `evidence/auth_reference_match/` altina kaydedildi.
- Test: `npm.cmd run lint` PASS; `npm.cmd run build` PASS; Chrome screenshots PASS.
- Sonuc: `AUTH_REFERENCE_MATCH_PASS`.

## 2026-08-13 TASK-NON-ASCII-IMAGE-PATH-HARDENING
- `backend/app/services/image_io.py` merkezi Unicode-safe OpenCV image IO utility olarak eklendi.
- `backend/app/services/document_analysis_pipeline.py` full-analysis page image read icin `read_image_unicode_safe` kullanir.
- `backend/app/services/document_processing/preprocessor.py` preprocessing image loader icin `read_image_unicode_safe` kullanir.
- `backend/app/api/routes/preprocessing.py` processed variant write icin `write_image_unicode_safe` kullanir.
- `backend/tests/test_unicode_image_io.py` Turkish/non-ASCII path, BGR, grayscale, alpha ve failure tests ile eklendi.
- Kanitlar `backend/evidence/non_ascii_path_gate/` altina kaydedildi.
- Test: `python -m pytest tests/test_unicode_image_io.py -q` -> 10 passed.
- Test: `python -m pytest tests/test_unknown_document_pipeline.py tests/test_ocr_engine.py tests/test_kraken_integration.py tests/test_faiss_security.py tests/test_unicode_image_io.py -q` -> 32 passed.
- Live Gate: non-ASCII workspace/upload root ile `POST /api/v1/document/analyze-full` HTTP 200, `ocr.engine=kraken`, `fallback_used=false`.
- Sonuc: `NON_ASCII_IMAGE_PATH_GATE_PASS`.

## 2026-08-13 TASK-BUILD-PRODUCTION-IMAGE-PROCESSING-LAB-UI
- `frontend/src/app/(app)/image-processing-lab/page.tsx` production Image Processing Lab arayuzu olarak Turkce, dark/gold, 3 kolon viewer, action strip, timeline, mask/restoration safety, OCR-safe card and before/after controls ile yeniden duzenlendi.
- `frontend/src/app/(app)/image-processing/page.tsx` dedicated production route olarak eklendi; `/image-processing-lab` legacy route ayni ekrani korur.
- `frontend/src/components/dashboard/Sidebar.tsx` navigation item `Goruntu Isleme` ve `/image-processing` active route olacak sekilde guncellendi.
- `frontend/src/app/globals.css` referans tasarim yonunde lab layout, responsive grid, viewer, timeline, comparison, panel and mobile styles ile guncellendi.
- Kanitlar `evidence/image_processing_lab_gate/` altina yenilendi: `dom_verification.json`, `stage_inventory.json`, `button_functionality_audit.json`, `responsive_audit.json`, desktop/mobile screenshots.
- Test: frontend lint PASS, 0 errors / 11 existing warnings; frontend build PASS; backend regression set 35 passed; Playwright real browser E2E PASS.
- Sonuc: `IMAGE_PROCESSING_LAB_GATE_PASS`.

## 2026-08-13 TASK-FINAL-PRODUCT-INTEGRATION-AND-DEMO-GATE
- `frontend/src/lib/documentContext.ts` shared active document context helper olarak eklendi; safe `documentId`, filename, analysis response ve legacy historical storage uyumlulugu saglandi.
- `frontend/src/app/(app)/dashboard/page.tsx` analysis sonucunu shared context'e kaydeder, aktif belgeyi restore eder, Image Lab/Historical navigation butonlari ve `Yeni Analiz` context reset davranisi ekler.
- `frontend/src/app/(app)/image-processing-lab/page.tsx` aktif context'teki belgeyi yeniden upload istemeden backend `documents/pages/preprocessing` API'leriyle yukler; auto-load effect cancellation defect'i giderildi; aktif filename header'da gorunur.
- `frontend/src/app/(app)/historical-analysis/page.tsx` shared context uzerinden ayni analysis response'u okur ve Dashboard/Image Lab navigation aksiyonlarini gosterir.
- `frontend/src/app/globals.css` cross-screen empty state/nav responsive stilleriyle genisletildi.
- Kanitlar `evidence/final_product_integration_gate/` altina kaydedildi.
- Test: frontend lint PASS 0 errors / 12 existing warnings; frontend build PASS; backend regression 40 passed; real browser full journey PASS.
- Sonuc: `FINAL_PRODUCT_INTEGRATION_GATE_PASS`.

## 2026-08-13 TASK-FINAL-PROFESSOR-DEMO-AND-RELEASE-GATE
- `scripts/pre_demo_check.ps1` preflight kontrolu olarak eklendi; Ollama modelleri, Kraken model SHA, Qdrant corpus, backend imports, frontend build ve storage writable durumunu JSON kanitla dogrular.
- `scripts/start_demo.ps1` production demo launcher olarak eklendi/duzeltildi; backend ve frontend'i ayrik sureclerle baslatir, `NEXT_PUBLIC_API_URL` ve local Ollama env degerlerini ayarlar, readiness kontrolu yapar ve exit code 0 ile doner.
- `scripts/stop_demo.ps1` yalniz kayitli demo PID'lerini ve alt sureclerini durduracak sekilde eklendi.
- `backend/app/core/config.py` release guvenligi icin `DEBUG` varsayilani `False` yapildi.
- `docs/FINAL_DEMO_SCRIPT_TR.md`, `docs/PROFESSOR_QA_TR.md`, `docs/DEMO_RECOVERY_GUIDE_TR.md`, `FINAL_PROJECT_STATUS.md` eklendi.
- `evidence/final_release_gate/` altinda preflight, startup, backend/frontend tests, browser E2E, security/config/performance audit, screenshots ve final release report uretildi.
- Test: backend targeted regression PASS, 55 passed; frontend lint PASS 0 errors / 12 warnings; frontend build PASS; real browser E2E functional PASS.
- Sonuc: `FINAL_RELEASE_GATE_PARTIAL` cunku browser E2E React hydration page errors kaydetti.

## 2026-08-14
- **VERIFY_AND_CLOSE_FULL_IMAGE_PROCESSING_STAGE_GATE**: Backend test ortam hatalari cozuldu, legacy test uyumlulugu saglandi (preprocessor.py fix). Frontend page.tsx uzerindeki Typescript unknown tip ve build hatalari temizlendi. Python verification betigiyle tum mimari ve stage artifact gereksinimlerinin gercekten saglandigi diske yazilan stage imajlarinin ozgunluk hash'leri uzerinden dogrulandi.

## 2026-08-14
- **FIX_CLEAN_DIGITAL_DOCUMENT_OUTPUT**: \preprocessor.py\ icerisindeki \generate_clean_digital_copy\ fonksiyonu, gercek bir arka plan normalizasyonu (morfolojik acilis, bolme) ve renk sapi (color cast) temizligi uygulayacak sekilde bastan yazildi. Leke giderme ve metin maskesi ile sadece metni koruyup arkaplani temizleme eklendi. (Orijinal ile ayni veya OCR'ye benzeme sorunu giderildi).
# 2026-08-20

- `GITHUB_SOURCE_REFRESH_PUSH_PASS`: `_github_publish_clean` yayin aynasi yeniden kuruldu ve GitHub `main` branch'ine `fabe5e07f0bc8cf0015c183f438ff60a1454782a` commit'i push edildi.
- `PROJECT_OVERVIEW.md` eklendi; `docs/wiki` ve diger `.md` dosyalari yayin paketinden haric tutuldu.
- Guvenlik dislamalari dogrulandi: gercek `.env`, DB/yedek DB, model agirliklari, uploads, datasets, vector DB, venv/node_modules ve runtime/evidence artefaktlari yok.

## 2026-08-20 Real Document Recovery Revalidation
- `backend/app/services/document_processing/preprocessor.py`: OCR-safe final icin text-preservation gate eklendi; destructive current pipeline adayi `original_otsu` ile degistirilir. CLEAN_READABLE_DOCUMENT original dark ink koruyacak sekilde ayarlandi.
- `backend/app/services/document_processing/translator.py`: gercek OCR satirlarinda bos modern line uretimini onlemek icin low-evidence fallback ve konuya uygun noisy token sozlukleri eklendi.
- `backend/app/services/document_analysis_pipeline.py`: claim-level `document_claims`, RAG dedup/relevance ve external evidence claim gate eklendi.
- `backend/app/schemas/document_analysis.py`, `frontend/src/lib/api.ts`: `evidence.document_claims` sozlesmesi eklendi.
- Kanit: `silah-atmama-ilani_ahmed-vefik-pasa.jpg` baseline `1` line / after `12` line; browser dashboard screenshot PASS.
- Test: backend targeted `21 passed`; frontend lint/build PASS; final runtime backend/frontend HTTP 200.

# 2026-08-21 Performance Audit 1C

- `backend/app/services/document_analysis_pipeline.py`: structured line batch LLM contract eklendi; `line_id` set validation, same-batch retry, smaller batch retry ve per-line fallback korundu.
- `backend/app/services/ai/ollama_provider.py`: Ollama API payload'ina env kontrollu `keep_alive` eklendi.
- `backend/scripts/kraken_wsl_bridge.py`: Kraken recognition inference `torch.inference_mode()` ile sarildi.
- `frontend/src/app/(app)/dashboard/page.tsx`: analyze action icin same-tick `analyzeInFlightRef` duplicate guard eklendi.
- `backend/tests/test_unknown_document_pipeline.py`: structured batch ve split/fallback regression testleri eklendi.
- `backend/scripts/performance_audit_1c.py`: 1C evidence harness eklendi.
- `evidence/performance_audit/1c/*`: LLM, OCR, GPU, Qdrant, HTTP saturation, frontend duplicate guard ve regression kanitlari kaydedildi.
- Sonuc: `PARTIAL_PASS_P0_LLM_CONTRACT_AND_OCR_PROFILE_FIXED_WITH_HTTP_E2E_BLOCKED`; FULL HTTP e2e PASS yok.

# 2026-08-21 Performance Audit 1D

- `backend/scripts/kraken_wsl_service.py`: persistent local WSL Kraken OCR HTTP service eklendi; model startup'ta bir kez yuklenir, `/health/live`, `/health/ready`, `/ocr`, `/shutdown` endpointleri vardir.
- `backend/app/services/document_processing/kraken_service_client.py`: Windows backend icin persistent OCR service client eklendi; service unavailable ise production OCR engine legacy WSL subprocess fallback'e explicit warning ile doner.
- `backend/app/services/document_processing/ocr_engine.py`: Kraken hot path persistent service'i once kullanacak sekilde guncellendi; service metadata OCR model metadata'ya eklenir.
- `backend/app/api/routes/document_analysis.py`: async `/document/analyze`, `/document/jobs/{job_id}`, `/document/jobs/{job_id}/result` endpointleri eklendi; legacy `/document/analyze-full` korundu.
- `backend/worker.py`: `full_document_analysis` job tipi worker context'inde `DocumentAnalysisPipeline.analyze_document()` calistiracak sekilde eklendi.
- `backend/app/services/job_manager.py`: active job status listesi netlestirildi; completion progress `100.0` yapilir.
- `frontend/src/lib/api.ts` ve `frontend/src/app/(app)/dashboard/page.tsx`: dashboard upload akisi async analyze + polling modeline tasindi.
- `scripts/start_kraken_service.ps1`, `check_kraken_service.ps1`, `stop_kraken_service.ps1`: Kraken service operational scripts eklendi/duzeltildi.
- `scripts/runtime_launcher.ps1`: stop islemi parent `cmd.exe` ile sinirli kalmayip process tree icin `taskkill /T /F` kullanir.
- `backend/tests/test_performance_audit_1d.py`: persistent client, duplicate active job ve worker full-analysis completion regression testleri eklendi.
- `evidence/performance_audit/1d/*`: legacy/persistent OCR benchmark, async live job, health, test/build/lint ve final rapor kanitlari kaydedildi.
- Sonuc: `PARTIAL_PASS_PERSISTENT_OCR_AND_ASYNC_ANALYZE_VERIFIED`; FULL PASS icin 2-job live concurrency ve granular stage progress eksik.
