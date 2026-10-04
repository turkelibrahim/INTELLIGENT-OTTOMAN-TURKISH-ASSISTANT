---
type: source_map
status: verified
last_verified: 2026-08-13
owners: []
source_paths:
  - backend/app
  - frontend/src
tags: [evidence, source-map]
---

# Source Map

**Ozet:** Bu sayfa wiki iddialarini kod, config veya komut kanitlarina baglar. Hassas degerler ve kullanici verisi kopyalanmamistir. Detayli durum icin [[Current_State]] ve mimari icin [[Architecture_Map]] kullanilir.

**Kutuphaneler:** rg, PowerShell, FastAPI, Next.js, SQLAlchemy.

**Baglantilar:** [[Index]], [[Current_State]], [[Risks]]

## Kanit Haritasi

## 2026-08-21 Runtime Start Success
- **Claim:** Local runtime basarili sekilde ayakta. **Kanit:** `runtime/logs/runtime_start_latest.txt` -> `SYSTEM READY`.
- **Claim:** Backend saglikli. **Kanit:** `Invoke-WebRequest http://127.0.0.1:8000/health` -> HTTP `200`, `{"status":"healthy","version":"1.0.0"}`.
- **Claim:** Frontend login route erisilebilir. **Kanit:** `Invoke-WebRequest http://127.0.0.1:3000/login` -> HTTP `200`.
- **Claim:** OCR runtime hazir. **Kanit:** `scripts/runtime_launcher.ps1 -Action Status` -> WSL Ubuntu ONLINE, Kraken READY, CUDA True, Model VERIFIED.

## 2026-08-21 Performance Audit 1B
- **Claim:** 1B performance audit kanit seti olusturuldu. **Kanit:** `evidence/performance_audit/PERFORMANCE_REPORT.md`; `evidence/performance_audit/comparison.json`.
- **Claim:** 1A HIGH/MEDIUM fixleri korunuyor. **Kanit:** `backend/app/services/document_analysis_pipeline.py:24`, `backend/app/services/document_analysis_pipeline.py:61`, `backend/app/services/document_processing/preprocessor.py:138`, `frontend/src/app/(app)/dashboard/page.tsx:224`.
- **Claim:** LLM call graph double-call darboğazi olculdu ve document-level line reuse ile azaltilmaya baslandi. **Kanit:** `evidence/performance_audit/llm_call_graph_before.json` -> 500 line `1002` calls; `llm_call_graph_after.json` -> aligned case `2` calls; real 3-line sample `8 -> 5` calls in `comparison.json`.
- **Claim:** Line provenance korunuyor. **Kanit:** `backend/tests/test_unknown_document_pipeline.py` reuse regression; `evidence/performance_audit/reuse_regression_test.txt` -> `5 passed, 1 skipped`.
- **Claim:** Real Kraken OCR stage profillendi. **Kanit:** `evidence/performance_audit/real_ocr_smoke_before.txt`; `real_ocr_smoke_after.txt`; `ocr_profile_before.json`; `ocr_profile_after.json`.
- **Claim:** RAG production path RRF icermiyor ve Qdrant/BM25 timing olculdu. **Kanit:** `backend/app/services/historical_rag/qdrant_store.py`; `evidence/performance_audit/stage_timings_before.json`; `stage_timings_after.json`.
- **Claim:** Chat RAG dead allocation kaldirildi. **Kanit:** `backend/app/services/chat/rag_service.py`; `rg` sonucu `DocIntelligenceEngine(use_mock=True)` production dosyada yok.
- **Claim:** Regression kapisi gecti. **Kanit:** `evidence/performance_audit/regression_tests.txt` -> `44 passed, 1 skipped`; `frontend_lint_1b.txt`; `frontend_build_1b.txt`.

## 2026-08-20 Algorithm Audit 1A
- **Claim:** Full algorithm audit kaniti olusturuldu. **Kanit:** `evidence/performance_audit/ALGORITHM_AUDIT.md`.
- **Claim:** LLM transliteration provider failure artik fallback yolunu `NameError` ile kirmiyor. **Kanit:** `backend/app/services/document_analysis_pipeline.py:24` logger; `backend/tests/test_unknown_document_pipeline.py:264`; `evidence/performance_audit/backend_algorithm_audit_tests.txt` -> `43 passed, 1 skipped`.
- **Claim:** `DocumentAnalysisPipeline.analyze_document` generic iterable page girdisini destekler. **Kanit:** `backend/app/services/document_analysis_pipeline.py:61` `ordered_pages`; generator-based test `backend/tests/test_unknown_document_pipeline.py:228`.
- **Claim:** OCR-safe preprocessing destructive deskew'i skip eder. **Kanit:** `backend/app/services/document_processing/preprocessor.py:138`; `backend/tests/test_processing_pipeline.py:82`.
- **Claim:** Dashboard duplicate analyze event'i busy durumda reddedilir. **Kanit:** `frontend/src/app/(app)/dashboard/page.tsx:224`, `frontend/src/app/(app)/dashboard/page.tsx:505`; frontend lint/build evidence.
- **Claim:** RAG production path'te RRF yok; Qdrant lexical rerank higher-is-better sort kullaniyor. **Kanit:** `backend/app/services/historical_rag/qdrant_store.py:243`, `backend/app/services/historical_rag/qdrant_store.py:352`; embedding dimension guard `backend/app/services/historical_rag/embedding_provider.py:49`.

## 2026-08-20 Final Partial To Verified Pass Closure
- **Claim:** Final closure gercek DB-backed belge uzerinde PASS oldu. **Kanit:** `evidence/recovery/final_audit/final_closure_report.json` -> `final_verdict=VERIFIED_PASS`, `failed_gates=[]`, runtime document ID `83`.
- **Claim:** Kullanilan belge sentetik degil. **Kanit:** `final_closure_report.json` -> selected source `backend/uploads/originals/82/82_191f0506.jpg`, SHA-256 `719f5f81c0e60cc6b24a7fb1fd8654217ff5d9b2d8920b6255f526363946dd90`, dimensions `[477,640]`, `synthetic_rejected=false`.
- **Claim:** Actual OCR/Latin/Modern Turkish content gercek API response'tan kaydedildi. **Kanit:** `evidence/recovery/final_audit/actual_text_outputs.json`; `final_closure_report.json` -> `ocr_actual_lines`, `transliteration_actual_lines`, `modern_actual_lines` each `12`.
- **Claim:** Ilk 5 satir image bbox -> OCR -> Latin -> Modern Turkish izlenebilirligi var. **Kanit:** `evidence/recovery/final_audit/line_traceability.json`; screenshot `evidence/recovery/final_audit/06_line_sync.png`.
- **Claim:** Real human review E2E mock degil. **Kanit:** `final_closure_report.json` -> `human_review_e2e.save_http_status=201`, `database_updated=true`, `audit_record_id=284`, regenerated text versions `83` and `84`.
- **Claim:** Browser evidence kapilari kapali. **Kanit:** `final_closure_report.json` -> screenshots `11`, button matrix `31/31 PASS`, console errors `0`, network `4xx=0`, `5xx=0`, failed `0`.
- **Claim:** Frontend closure UI/API derlenebilir. **Kanit:** `frontend/src/lib/api.ts` -> `ocrReviewApi.createCorrection`; `frontend/src/app/(app)/dashboard/page.tsx` -> search/edit/save/download controls; commands `npm.cmd run lint` PASS and `npm.cmd run build` PASS.

## 2026-08-20 Critical False Pass Correction
- **Claim:** Kokteki `silah-atmama-ilani_ahmed-vefik-pasa.jpg` sentetik/invalid input idi. **Kanit:** `evidence/invalid_synthetic_inputs/silah-atmama-ilani_ahmed-vefik-pasa_SYNTHETIC_INVALID.jpg`, dimensions `800x600`, size `9560`, SHA-256 `862bdffcfb6d75043ed248fec48861023d25d18a8fddb80070208ae28e23d008`.
- **Claim:** Gercek belge DB/storage mapping ile bulundu. **Kanit:** `backend/ottoman_assistant.db` documents/pages query; corrected metrics selected real hash `719f5f81c0e60cc6b24a7fb1fd8654217ff5d9b2d8920b6255f526363946dd90`, dimensions `477x640`.
- **Claim:** DB-managed sentetik upload contamination kayitlari var. **Kanit:** `evidence/recovery/final_audit/metrics.json` -> `synthetic_rejection.rejected_candidates` count `5`, document IDs `70`-`74`.
- **Claim:** Corrected audit script sentetik input fallback'i ve mock PASS davranisini reddeder. **Kanit:** `backend/scripts/final_evidence_audit.py` -> `resolve_real_document_path`, `SYNTHETIC_HASHES`, `human_correction.status = NOT_EXECUTED_REAL_API_REQUIRED`, `quality_gates`.
- **Claim:** Son runtime sonucu PASS degil. **Kanit:** `evidence/recovery/final_audit/metrics.json` -> `final_verdict=VERIFIED_PARTIAL`, failed gates `human_review_real`, `screenshots_min_10`, `button_matrix_min_25`.
- **Claim:** Real runtime OCR/Latin/Modern non-empty. **Kanit:** `evidence/recovery/final_audit/metrics.json` -> OCR `12` line / `563` chars / confidence `0.8719`, transliteration `12` line / `657` chars, modern `12` line / `737` chars.
- FastAPI uygulamasi: `backend/app/main.py` -> `app`, `lifespan`, `root`, `health_check`.
- API router: `backend/app/api/router.py` -> `api_router.include_router(...)`.
- Auth API: `backend/app/api/routes/auth.py` -> `register`, `login`, `get_me`, `logout`.
- Security: `backend/app/core/security.py` -> `verify_password`, `get_password_hash`, `create_access_token`, `get_current_user`, `get_current_admin`, `get_current_expert`.
- Config: `backend/app/core/config.py` -> `Settings`.
- Database: `backend/app/db/database.py` -> `engine`, `SessionLocal`, `Base`, `get_db`, `init_db`.
- Document API: `backend/app/api/routes/documents.py` -> `upload_document`, `list_documents`, `get_document`, `update_document`, `delete_document`.
- Page API: `backend/app/api/routes/pages.py` -> `list_pages`, `get_page`, `get_page_image`, `get_page_thumbnail`.
- Preprocessing API: `backend/app/api/routes/preprocessing.py` -> `PreprocessRequest`, `ImageVariantResponse`, `create_preprocess_variant`, `list_variants`, `get_variant_image`.
- File service: `backend/app/services/file_service.py` -> `FileService.validate_file`, `save_upload`, `validate_magic_bytes`, `calculate_hash`, `split_pdf_to_pages`, `create_thumbnail`, `delete_document_files`.
- Image preprocessing: `backend/app/services/document_processing/preprocessor.py` -> `ImagePreprocessor.PROFILES`, `process_with_profile`, `correct_skew`, `_calculate_confidence`.
- OCR partial: `backend/app/services/document_processing/ocr_engine.py` -> `OCREngine.extract_text`; fallback mock metin kaniti.
- Translation partial: `backend/app/services/document_processing/translator.py` -> `Translator.translate`, `_transliterate`, `_translate_to_modern`; placeholder kaniti.
- NER partial: `backend/app/services/document_processing/ner_extractor.py` -> `NERExtractor.extract_entities`; placeholder kaniti.
- Pipeline risk: `backend/app/services/document_processing/pipeline.py` -> `DocumentProcessingPipeline.process_document` icinde `self.preprocessor.process(image)` cagrisi; `ImagePreprocessor` icinde `process` sembolu bulunamadi.
- Data models: `backend/app/models/user.py` -> `User`; `document.py` -> `Document`; `page.py` -> `Page`; `processing_job.py` -> `ProcessingJob`; `image_variant.py` -> `ImageVariant`; `audit_log.py` -> `AuditLog`.
- Schemas: `backend/app/schemas/user.py`, `document.py`, `page.py` -> Pydantic response/request modelleri.
- Frontend root layout: `frontend/src/app/layout.tsx` -> `metadata`, `RootLayout`.
- Frontend redirect: `frontend/src/app/page.tsx` -> `Home`.
- Login UI: `frontend/src/app/login/page.tsx` -> `LoginPage`.
- Dashboard UI: `frontend/src/app/dashboard/page.tsx` -> `DashboardPage`.
- Upload UI: `frontend/src/app/upload/page.tsx` -> `UploadPage`.
- Document workspace UI: `frontend/src/app/documents/[id]/page.tsx` -> `DocumentDetailPage`, `AuthenticatedImage`.
- Frontend API client: `frontend/src/lib/api.ts` -> `authApi`, `documentsApi`, `pagesApi`, `preprocessingApi`, `fetchAuthenticatedBlobUrl`, `API_BASE_URL`.
- Frontend package scripts: `frontend/package.json` -> `dev`, `build`, `start`, `lint`.
- Backend dependencies: `backend/requirements.txt`.
- Smoke import file: `backend/test_import.py`; real test suite bulunamadi.

## Komut Kanitlari
- `rg --files -g '!frontend/node_modules/**' -g '!backend/venv/**' ...` ile proje envanteri alindi.
- `rg "^(class|def|async def) " backend\app -g "*.py"` ile backend sembolleri listelendi.
- `rg "^(export default function|export const|export interface...)" frontend\src` ile frontend sembolleri listelendi.
- Test aramasi `rg "pytest|unittest|describe\(|it\(|test\(" ...` sonucunda sadece uygulama kodundaki string/commit benzeri eslesmeler goruldu; dogrulanmis test dosyasi bulunamadi.
- 2026-08-02 UI-FIX-20260802: `npm.cmd run lint` PASS; `npm.cmd run build` PASS; `powershell -ExecutionPolicy Bypass -File scripts/doctor.ps1` PASS, `DOCTOR_FAILED=0`, backend 70 passed.
- 2026-08-02 GROUND_TRUTH_INFRASTRUCTURE_FINAL_GATE: `evidence/ground_truth_final_gate/FINAL_GATE_REPORT.md` -> final gate kanit matrisi.
- 2026-08-02 GROUND_TRUTH_INFRASTRUCTURE_FINAL_GATE: `evidence/ground_truth_final_gate/backend_full_tests_active.txt` ve `backend_full_tests_clean.txt` -> backend active/clean regression PASS, 90 passed.
- 2026-08-02 GROUND_TRUTH_INFRASTRUCTURE_FINAL_GATE: `evidence/ground_truth_final_gate/doctor_quality_gate.txt` -> doctor PASS, `DOCTOR_FAILED=0`.
- 2026-08-02 GROUND_TRUTH_INFRASTRUCTURE_FINAL_GATE: `evidence/ground_truth_final_gate/frontend_browser_e2e.txt`, `browser_mobile.png`, `browser_desktop.png` -> live browser E2E PASS.
- 2026-08-02 GROUND_TRUTH_INFRASTRUCTURE_FINAL_GATE: `evidence/ground_truth_final_gate/health_auth_smoke.txt` -> `/health`, register/login token ve unauthorized auth smoke PASS.
- 2026-08-02 GROUND_TRUTH_INFRASTRUCTURE_FINAL_GATE: `backend/app/api/routes/ground_truth.py`, `backend/tests/test_ground_truth_api.py`, `frontend/src/app/dashboard/annotation-studio/page.tsx`, `frontend/src/lib/api.ts` -> API-backed Ground Truth Studio kaniti.
- 2026-08-02 GROUND_TRUTH_INFRASTRUCTURE_FINAL_GATE: `backend/app/services/document_processing/ocr_engine.py`, `scripts/generate_easyocr_manifest.py`, `backend/tests/test_model_verification.py` -> EasyOCR SHA-256 checksum/butunluk ve tamper test kaniti.
- 2026-08-02 GROUND_TRUTH_FINAL_GATE_SUPPLEMENTAL_VERIFICATION: `evidence/ground_truth_final_gate_supplement/FINAL_SUPPLEMENTAL_REPORT.md` -> supplemental verification karar kaniti.
- 2026-08-02 GROUND_TRUTH_FINAL_GATE_SUPPLEMENTAL_VERIFICATION: `torch_environment_active.txt`, `torch_environment_clean.txt`, `torch_provenance_and_hash.txt`, `torch_official_download_log.txt`, `osv_torch_query.txt`, `torch_advisory_verification.md` -> PyTorch provenance/checksum/advisory kaniti.
- 2026-08-02 GROUND_TRUTH_FINAL_GATE_SUPPLEMENTAL_VERIFICATION: `git_discovery.txt`, `git_status.txt`, `git_diff_check.txt`, `secret_and_large_file_review.txt` -> Git yoklugunda esdeger degisiklik, secret ve buyuk dosya denetimi kaniti.
- 2026-08-02 GROUND_TRUTH_FINAL_GATE_SUPPLEMENTAL_VERIFICATION: `regression_after_changes.txt` -> pip check, FAISS, model verification, backend regression ve frontend lint/typecheck/build PASS kaniti.

## BASELINE-001 Evidence
- `evidence/recover_baseline/file_inventory.txt` -> gercek dosya/klasor envanteri.
- `evidence/recover_baseline/root_listing.txt` ve `root_listing_post.txt` -> kok dizin kaniti.
- `evidence/recover_baseline/environment.txt` ve `env_dirs.txt` -> Python/Node/npm/venv kaniti.
- `evidence/recover_baseline/git_status.txt` -> git komutunun PATH uzerinde bulunamadigi kaniti.
- `evidence/recover_baseline/dependency_config_snapshot.txt` ve `backend_config_listing.txt` -> requirements/package/config dosya kaniti.
- `evidence/recover_baseline/backend_symbols.txt`, `backend_app_files.txt`, `source_key_snippets.txt`, `document_processing_sources.txt`, `implementation_markers.txt` -> backend modulleri ve placeholder/kirik akis kaniti.
- `evidence/recover_baseline/frontend_symbols.txt`, `frontend_src_files.txt` -> frontend giris noktalari ve API istemcisi kaniti.
- `evidence/recover_baseline/backend_import_smoke.txt` -> backend import smoke PASS.
- `evidence/recover_baseline/backend_pytest.txt` -> pytest BLOCKED, `No module named pytest`.
- `evidence/recover_baseline/frontend_lint.txt` -> frontend lint PASS with warning.
- `evidence/recover_baseline/frontend_build.txt` -> frontend build PASS.
- `evidence/recover_baseline/backend_pipeline_smoke_utf8.txt`, `pipeline_mismatch_evidence.txt`, `preprocessor_methods.txt` -> pipeline BROKEN kaniti.
- `evidence/recover_baseline/env_key_presence.txt` -> `.env` key varligi kaniti; gizli degerler kaydedilmedi.

## TASK-008 Evidence
- `docs/wiki/08_Testing/Requirements_Traceability_Matrix.md` -> partial gereksinim matrisi.
- `docs/wiki/08_Testing/Acceptance_Criteria_Map.md` -> kabul kriteri ve release gate haritasi.
- `docs/wiki/09_Decisions/ADR-001_NextJS_Frontend.md` -> Streamlit/Next.js teknoloji ayrimi icin proposed ADR.
- `evidence/requirements_traceability/srs_extract_log.txt` -> SRS PDF bulundu ama `pypdf` yok.
- `evidence/requirements_traceability/srs_extract_log_autonomous.txt` -> SRS PDF 26 sayfa olarak cikarildi.
- `evidence/requirements_traceability/srs_extracted_text.txt` -> SRS metin kaniti.
- `evidence/requirements_traceability/srs_requirements_parsed.tsv` -> SRS requirement ID/priority/status parse kaniti.
- `evidence/requirements_traceability/matrix_summary_autonomous.txt` -> 165 requirement summary.

## TASK-009 Evidence
- `evidence/environment_gate/windows_system.txt` -> admin durumu, Windows/RAM/disk.
- `evidence/environment_gate/tool_versions.txt` -> Python/venv/Node/npm/git durumu.
- `evidence/environment_gate/nvidia_smi.txt` -> RTX 4050 GPU gorunurlugu.
- `evidence/environment_gate/backend_pytest_smoke.txt` -> pytest 2 passed.
- `evidence/environment_gate/frontend_lint.txt` -> lint PASS with warning.
- `evidence/environment_gate/frontend_build.txt` -> Next build PASS.
- `evidence/environment_gate/doctor_full.txt` -> doctor full PASS.
- `evidence/environment_gate/source_hash_manifest.txt` -> git yoklugunda alternatif kaynak manifesti.
- `backend/tests/test_smoke.py` -> health ve DB metadata smoke tests.
- `backend/requirements-dev.txt` -> dev/test evidence tooling.
- `evidence/requirements_traceability/python_pdf_modules_check.txt`, `venv_pdf_modules_check.txt`, `pdf_tools_check.txt` -> PDF metin cikarma araci yok.
- `evidence/requirements_traceability/requirement_ids_scan.txt` -> kod/wiki/prompt icindeki FR/DR/MLR/NFR izleri.
- `evidence/requirements_traceability/code_requirement_snippets.txt` -> requirement id bulunan kod parcasi snapshot.
- `evidence/requirements_traceability/wiki_module_snapshot.txt` -> modul wiki snapshot.
- `evidence/requirements_traceability/prompt_scope_snapshot.txt` -> sonraki prompt kapsamlarindan gereksinim kaniti.

## TASK-010 Evidence
- `backend/app/models/processing_outputs.py` -> model registry, OCR result, text version, entity, chat, citation ve export temel modelleri.
- `backend/app/models/__init__.py` -> yeni modellerin `Base.metadata` icine kaydi.
- `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/20260728_0001_initial_schema.py` -> Alembic initial migration ve rollback yapisi.
- `backend/tests/test_migrations.py` -> gecici SQLite DB uzerinde `upgrade head` ve `downgrade base` testi.
- `backend/tests/test_smoke.py` -> FastAPI health, metadata tablo ve izlenebilirlik kolon testleri.
- `evidence/environment_gate/backend_pytest_after_traceability_columns.txt` -> backend pytest 4 passed.
- `evidence/environment_gate/doctor_after_traceability_columns.txt` -> doctor PASS, `DOCTOR_FAILED=0`.

## TASK-011 Evidence
- `backend/tests/test_auth_security.py` -> register/login/me/logout audit flow, generic invalid login, expired/missing token, belge IDOR ve belge liste scoping testleri.
- `backend/tests/test_file_security.py` -> unsupported extension, MIME spoof, magic-byte spoof cleanup, size limit cleanup ve path traversal filename testleri.
- `frontend/package.json` ve `frontend/package-lock.json` -> security overrides: `@eslint/config-array`, `minimatch`, `brace-expansion`, `postcss`, `sharp`.
- `evidence/environment_gate/backend_pytest_task011_full.txt` -> backend pytest 14 passed.
- `evidence/environment_gate/doctor_task011_full.txt` -> doctor full PASS, `DOCTOR_FAILED=0`.
- `evidence/environment_gate/npm_audit_high_task011_after_minimatch_override.txt` -> npm audit high PASS, 0 vulnerabilities.
- `evidence/environment_gate/secret_pattern_scan_task011.txt` -> secret pattern scan; `.env` dislandi, secret degerleri kopyalanmadi.

## TASK-012 Evidence
- `backend/tests/test_document_upload_integration.py` -> auth-required upload, PNG upload document/page/thumbnail/hash/audit, magic-byte spoof cleanup, page image/thumbnail access, delete cleanup, preprocessing variant integration.
- `backend/app/api/routes/preprocessing.py` -> `ImageVariantResponse.created_at` datetime response validation fix.
- `evidence/environment_gate/backend_pytest_task012_upload_after_fix.txt` -> document upload integration 5 passed.
- `evidence/environment_gate/backend_pytest_task012_after_fix.txt` -> backend pytest 19 passed.
- `evidence/environment_gate/doctor_task012_full.txt` -> doctor full PASS, `DOCTOR_FAILED=0`.

## TASK-013 Evidence
- `backend/app/services/file_service.py` -> `split_pdf_to_pages` once Poppler/pdf2image, sonra `pypdfium2` fallback kullanir.
- `backend/requirements.txt` -> `pypdfium2==5.12.1`.
- `backend/tests/test_document_upload_integration.py` -> iki sayfali PDF fixture upload, page order `[1, 2]`, rendered PNG output ve thumbnail assertion.
- `evidence/environment_gate/pip_install_pypdfium2_task013.txt` ve `pip_show_pypdfium2_task013.txt` -> dependency kurulum/versiyon kaniti.
- `evidence/environment_gate/backend_pytest_task013_pdf_initial.txt` -> document upload integration 6 passed.
- `evidence/environment_gate/backend_pytest_task013_initial.txt` -> backend pytest 20 passed.
- `evidence/environment_gate/doctor_task013_full.txt` -> doctor full PASS, `DOCTOR_FAILED=0`.

## TASK-015 Evidence
- `backend/app/services/document_processing/preprocessor.py` -> `ImagePreprocessor.process(image, profile)` pipeline contract and shared `_apply_params`.
- `backend/tests/test_processing_pipeline.py` -> preprocessor process contract and `DocumentProcessingPipeline.process_document` smoke with stubbed AI components.
- `evidence/environment_gate/backend_pytest_task015_pipeline_initial.txt` -> pipeline tests 2 passed.
- `evidence/environment_gate/backend_pytest_task015_initial.txt` -> backend pytest 22 passed.
- `evidence/environment_gate/doctor_task015_full.txt` -> doctor full PASS, `DOCTOR_FAILED=0`.

## TASK-016 Evidence
- `backend/app/services/document_processing/layout.py` -> `LayoutAnalyzer`, `LineRegion`, line box detection, column clustering, RTL/LTR ordering.
- `backend/tests/test_layout_analysis.py` -> line coordinate, RTL order and LTR order fixture tests.
- `evidence/environment_gate/backend_pytest_task016_layout_initial.txt` -> layout tests 3 passed.
- `evidence/environment_gate/backend_pytest_task016_initial.txt` -> backend pytest 25 passed.
- `evidence/environment_gate/doctor_task016_full.txt` -> doctor full PASS, `DOCTOR_FAILED=0`.

## TASK-017 Evidence
- `backend/app/services/document_processing/ocr_engine.py` -> `OCRPrediction`, `OCREngine.extract`, `extract_text`, `model_metadata`, deterministic fallback.
- `backend/tests/test_ocr_engine.py` -> metadata, fallback prediction and legacy tuple tests.
- `evidence/environment_gate/ocr_dependency_versions_task017.txt` -> torch/transformers and CPU fallback evidence.
- `evidence/environment_gate/backend_pytest_task017_ocr_initial.txt` -> OCR tests 3 passed.
- `evidence/environment_gate/backend_pytest_task017_initial.txt` -> backend pytest 28 passed.
- `evidence/environment_gate/doctor_task017_full.txt` -> doctor full PASS, `DOCTOR_FAILED=0`.

## TASK-018 Evidence
- `backend/app/api/routes/ocr_review.py` -> `list_review_lines`, `create_correction`, `_latest_correction_text`, `_get_authorized_page`.
- `backend/app/api/router.py` -> OCR review router API v1 altina dahil edildi.
- `backend/app/models/processing_outputs.py` -> `OCRResult` ve `TextVersion` review/correction storage modelleri.
- `backend/tests/test_ocr_review.py` -> ownership/low-confidence filter, raw OCR preservation, text versioning, audit and correction history tests.
- `evidence/environment_gate/backend_pytest_task018_review_initial.txt` -> OCR review tests 3 passed.
- `evidence/environment_gate/backend_pytest_task018_initial.txt` -> backend pytest 31 passed.
- `evidence/environment_gate/doctor_task018_full.txt` -> doctor full PASS, `DOCTOR_FAILED=0`.

## TASK-019 Evidence
- `backend/app/services/document_processing/translator.py` -> `Translator`, `TransliterationResult`, source mapping, ambiguity candidates, CER/WER/chrF fixture metrics.
- `backend/app/api/routes/transliteration.py` -> OCR-result scoped transliteration creation, correction history and audit.
- `backend/app/api/router.py` -> transliteration router API v1 altina dahil edildi.
- `backend/tests/test_transliteration.py` -> source mapping, ambiguity, metrics, separate storage, correction history and ownership tests.
- `evidence/environment_gate/backend_pytest_task019_transliteration_initial.txt` -> initial failure evidence, Pydantic candidate model validation.
- `evidence/environment_gate/backend_pytest_task019_transliteration_after_metrics.txt` -> transliteration tests 5 passed.
- `evidence/environment_gate/backend_pytest_task019_after_metrics.txt` -> backend pytest 36 passed.
- `evidence/environment_gate/doctor_task019_after_metrics.txt` -> doctor full PASS, `DOCTOR_FAILED=0`.

## TASK-020 Evidence
- `backend/app/services/document_processing/translator.py` -> `ModernizationResult`, faithful/plain/summary fallback, unreadable marker and prompt-injection data warning.
- `backend/app/api/routes/modernization.py` -> source TextVersion scoped modernization creation, correction history and audit.
- `backend/app/api/router.py` -> modernization router API v1 altina dahil edildi.
- `backend/tests/test_modernization.py` -> mode separation, source mapping, unreadable handling, prompt-injection safety, separate storage, audit, ownership tests.
- `evidence/environment_gate/backend_pytest_task020_modernization_initial.txt` -> initial failure evidence.
- `evidence/environment_gate/backend_pytest_task020_modernization_after_fix.txt` -> modernization tests 4 passed.
- `evidence/environment_gate/backend_pytest_task020_initial.txt` -> backend pytest 40 passed.
- `evidence/environment_gate/doctor_task020_full.txt` -> doctor full PASS, `DOCTOR_FAILED=0`.

## TASK-021 Evidence
- `backend/app/services/document_processing/ner_extractor.py` -> `NERExtractor`, `EntityPrediction`, `GlossaryEntry`, date normalization, precision/recall/F1, OCR impact report.
- `backend/app/api/routes/analysis.py` -> TextVersion scoped entity extraction, user correction storage and audit.
- `backend/app/api/router.py` -> analysis router API v1 altina dahil edildi.
- `backend/tests/test_analysis.py` -> entity/date/glossary metrics, OCR impact, API storage/audit and ownership tests.
- `evidence/environment_gate/backend_pytest_task021_analysis_initial.txt` -> analysis tests 4 passed.
- `evidence/environment_gate/backend_pytest_task021_initial.txt` -> backend pytest 44 passed.
- `evidence/environment_gate/doctor_task021_full.txt` -> doctor full PASS, `DOCTOR_FAILED=0`.

## TASK-022 Evidence
- `backend/app/services/document_processing/confidence.py` -> `ConfidenceManager`, `ModelRegistryService`, `build_operation_metadata`.
- `backend/tests/test_confidence_model_registry.py` -> confidence label/clamp, registry idempotency, OCR/transliteration/modernization/NER metadata and unsupported operation tests.
- `backend/app/models/processing_outputs.py` -> `ModelRegistryEntry`.
- `evidence/environment_gate/backend_pytest_task022_confidence_initial.txt` -> confidence/model registry tests 4 passed.
- `evidence/environment_gate/backend_pytest_task022_initial.txt` -> backend pytest 48 passed.
- `evidence/environment_gate/doctor_task022_full.txt` -> doctor full PASS, `DOCTOR_FAILED=0`.

## GROUND_TRUTH_INFRASTRUCTURE_FINAL_GATE Evidence
- evidence/ground_truth_final_gate/FINAL_GATE_REPORT.md -> final gate karar raporu.
- evidence/ground_truth_final_gate/backend_full_tests_final_rerun.txt -> backend 91 passed.
- evidence/ground_truth_final_gate/doctor_rerun.txt -> DOCTOR_FAILED=0.
- evidence/ground_truth_final_gate/browser_e2e_annotation_studio_rerun.txt -> Annotation Studio browser E2E PASS.
- evidence/ground_truth_final_gate/real_ocr_smoke_rerun.txt -> real EasyOCR smoke PASS, 16 lines, confidence 0.1229.
- evidence/ground_truth_final_gate/migration_roundtrip_backend_cwd_pythonpath_rerun.txt -> seeded migration downgrade/upgrade PASS.

## TASK-034-Q2 Evidence
- `scripts/validate_ground_truth_dataset.py` -> original ground truth input validator, dry-run evidence writer, blocked-without-data decision.
- `backend/tests/test_ground_truth_dataset_validator.py` -> no-data blocked, valid pair PASS, unmatched files, invalid UTF-8, low resolution, duplicate hash, split leakage tests.
- `evidence/ocr_quality_real/GROUND_TRUTH_DATA_PREPARATION_GUIDE.md` -> data ownership and Annotation Studio preparation instructions.
- `evidence/ocr_quality_real/input/metadata.csv` -> required metadata header template.
- `evidence/ocr_quality_real/input_validation.json` and `dataset_manifest.json` -> current pilot draft data present, `BLOCKED_HUMAN_REVIEW_REQUIRED`, 3 pages, 73 lines.
- `evidence/ocr_quality_real/backend_tests.txt` -> backend venv regression PASS, 97 passed, 32 third-party warnings.
- `evidence/ocr_quality_real/frontend_tests.txt`, `frontend_lint.txt`, `frontend_build.txt` -> frontend lint 0 warnings and build PASS.
- `evidence/ocr_quality_real/warning_audit.md` -> project warning cleanup and remaining third-party warning classification.
- `evidence/ocr_quality_real/browser_e2e.txt` -> `BLOCKED_BROWSER_UNAVAILABLE`; local ports reachable but no controllable browser surface exposed.
- `evidence/ocr_quality_real/FINAL_OCR_QUALITY_REPORT.md` -> OCR quality remains `QUALITY_UNVERIFIED`; no CER/WER fabricated.
- `c:\Users\ibrah\Downloads\ground_truth_osmaluca_pilot_draft.zip` -> user-provided pilot draft archive, SHA-256 `4FB8A12A2D30B5B0E900F89ED879728317DF0DAF7A663830E657121524BB41E8`.
- `evidence/ocr_quality_real/source_zip_provenance.md` -> source zip intake, rights/review status, and block decision.
- `evidence/ocr_quality_real/source_zip_manifest_verification.json` -> internal package `MANIFEST.sha256` verification PASS.
- `evidence/ocr_quality_real/validator_after_zip_import.txt` -> validator result `BLOCKED_HUMAN_REVIEW_REQUIRED`, 3 pages, 73 lines, `PILOT_EVALUATION_ONLY`.
- `evidence/ocr_quality_real/backend_target_tests_after_zip.txt` -> validator/evaluation target tests PASS, 15 passed.

## TASK-034-Q3 Evidence
- `backend/app/models/ground_truth.py` -> review statuses, line review flags and `GroundTruthReviewAudit`.
- `backend/app/models/processing_job.py` -> nullable `document_id`, `progress`, `result_path` for dataset-scoped pilot evaluation jobs.
- `backend/alembic/versions/20260802_0002_human_review_workflow.py` -> human review workflow migration and live SQLite recovery-safe guards.
- `backend/app/api/routes/ground_truth.py` -> pilot draft import, review progress, authenticated line review, dataset ready-to-lock, dataset lock and idempotent job creation.
- `backend/worker.py` -> `pilot_ocr_evaluation` processing path.
- `backend/tests/test_human_review_gate.py` -> import integrity, user isolation, fake reviewer rejection, review audit, lock idempotency, locked immutability and worker job completion tests.
- `frontend/src/lib/api.ts` -> human review API client methods.
- `frontend/src/app/dashboard/annotation-studio/page.tsx` -> API-backed human review UI and empty-dataset pilot import.
- `evidence/human_review_gate/FINAL_HUMAN_REVIEW_GATE_REPORT.md` -> final Q3 status `WAITING_FOR_HUMAN_CONTENT_REVIEW`.
- `evidence/human_review_gate/review_api_tests.txt` -> targeted backend tests PASS, 4 passed.
- `evidence/human_review_gate/frontend_lint.txt`, `frontend_build.txt`, `frontend_typecheck.txt` -> frontend gate PASS.
- `evidence/human_review_gate/alembic_schema_verify.txt` -> live SQLite revision `20260802_0002`, `document_id` nullable, no leftover Alembic temp table.
- `evidence/human_review_gate/live_smoke.txt` -> backend health/OpenAPI and frontend Annotation Studio HTTP 200.
- `evidence/human_review_gate/browser_e2e.txt` -> `BLOCKED_BROWSER_UNAVAILABLE`; no Playwright/browser tool in session.


## 2026-08-02 Bootstrap Refresh Evidence
- `AGENTS.md` okundu; operasyon modu `BOOTSTRAP`.
- `docs/wiki/Index.md`, `Current_State.md`, `Task_Queue.md`, `Execution_Lock.md`, `Decisions.md`, `Latest_Handoff.md`, `Architecture_Map.md`, `Source_Map.md` okundu.
- `git status --short` calistirilamadi: Git executable PATH uzerinde bulunamadi.
- `README.md` -> `scripts/bootstrap.ps1` ve `start.bat` calisma komutlari.
- `backend/requirements.txt` -> FastAPI, SQLAlchemy, torch, EasyOCR, FAISS, sentence-transformers, jiwer.
- `frontend/package.json` -> Next.js 16.2.11, React 19.2.4, lint/build scripts.
- `backend/app/api/router.py` -> 12 route modulu bagli.
- `backend/worker.py` -> worker ve pilot evaluation akisi.
- `backend/app/services/export_service.py` -> `ExportService`.
- `backend/app/services/evaluation_service.py` -> `EvaluationService`.
- `backend/tests` -> 30 Python test dosyasi goruldu.

## TASK-034-Q4 Evidence
- `backend/app/services/evaluation/ocr_pipeline_optimization.py` -> IoU, duplicate suppression, RTL grouping, reading order and config freeze helpers.
- `backend/tests/test_ocr_pipeline_optimization.py` -> RTL ordering, box matching, duplicate suppression and config freeze tests.
- `scripts/optimize_ottoman_ocr_pipeline.py` -> locked pilot OCR diagnosis/optimization runner.
- `evidence/ocr_pipeline_optimization_v1/ground_truth_integrity_before.json` and `ground_truth_integrity_after.json` -> unchanged GT combined SHA-256.
- `evidence/ocr_pipeline_optimization_v1/recognition_only_baseline.json` -> recognition-only crop metrics from locked GT boxes.
- `evidence/ocr_pipeline_optimization_v1/detection_only_baseline.json` -> IoU detection-only metrics and box counts.
- `evidence/ocr_pipeline_optimization_v1/dev_metrics.json`, `test_metrics.json`, `pilot_metrics_v2.json` -> dev/test/all split metrics after config freeze.
- `evidence/ocr_pipeline_optimization_v1/selected_config.json` and `selected_config.sha256` -> dev-selected frozen config and checksum.
- `evidence/ocr_pipeline_optimization_v1/overlays/*.png` -> GT/detection overlay images.
- `evidence/ocr_pipeline_optimization_v1/targeted_tests.txt` -> targeted tests PASS, 14 passed.
- `evidence/ocr_pipeline_optimization_v1/backend_regression.txt` -> backend regression PASS, 108 passed.
- `evidence/ocr_pipeline_optimization_v1/doctor_gate.txt` -> doctor gate PASS, `DOCTOR_FAILED=0`.
- `evidence/ocr_pipeline_optimization_v1/FINAL_OCR_PIPELINE_OPTIMIZATION_REPORT.md` -> final Q4 decision `PILOT_FAIL_NEEDS_FURTHER_IMPROVEMENT`.

## STARTUP-REFRESH-20260803 Evidence
- `start.bat` -> updated Windows startup orchestration with checks, migration, duplicate process guard, worker/backend/frontend launch and current links.
- `README.md` -> updated run instructions and current pilot OCR status.
- `evidence/start_bat_check_20260803.txt` -> dry-run prerequisite check PASS.

## TASK-034-Q5 Evidence
- `backend/app/services/evaluation/ocr_pipeline_optimization.py` -> `logical_line_items`, `projection_profile_line_boxes`, `hybrid_line_items`, `component_coverage_metrics`, `reading_order_metrics`.
- `backend/tests/test_line_segmentation_q5.py` -> synthetic metric validation, fragmented line reconstruction, RTL ordering, projection-profile detection, GT leakage guard and config freeze tests.
- `scripts/line_segmentation_q5.py` -> locked pilot dataset Q5 runner; Page 1 development and Page 2-3 pilot_validation split enforcement.
- `evidence/line_segmentation_q5/ground_truth_integrity_before.json` and `ground_truth_integrity_after.json` -> unchanged GT combined SHA-256 `59288698485deae4fb618a1554c43bb827745ca6ee3a6566e3d34c994dc44527`.
- `evidence/line_segmentation_q5/existing_metric_audit.md` -> Q4 metric representation audit; raw component boxes were labelled line F1, one-to-one double-count bug not found.
- `evidence/line_segmentation_q5/metric_definition_v2.md` -> Q5 metric definitions and prediction representation labels.
- `evidence/line_segmentation_q5/line_strategy_ablation.csv` -> Page 1 strategy comparison; selected `B_projection_profile`.
- `evidence/line_segmentation_q5/selected_line_strategy.json` and `selected_line_strategy.sha256` -> frozen Q5 config and checksum.
- `evidence/line_segmentation_q5/development_metrics.json` -> development logical line F1 `0.938776`, overall reading-order `1.0`, normalized CER `0.625261`.
- `evidence/line_segmentation_q5/pilot_validation_metrics.json` -> pilot_validation logical line F1 `0.961538`, overall reading-order `1.0`, normalized CER `0.562557`, normalized WER `0.870690`.
- `evidence/line_segmentation_q5/raw_component_metrics.json` and `logical_line_metrics.json` -> raw component vs logical line split metrics.
- `evidence/line_segmentation_q5/reading_order_metrics.json` -> matched-line coverage, pairwise, adjacent and overall reading-order metrics.
- `evidence/line_segmentation_q5/line_matches.csv`, `unmatched_lines.csv`, `overlays/*.png` -> visual and tabular alignment evidence.
- `evidence/line_segmentation_q5/targeted_tests.txt` -> targeted tests PASS, 20 passed.
- `evidence/line_segmentation_q5/backend_regression.txt` -> backend regression PASS, 119 passed.
- `evidence/line_segmentation_q5/doctor_gate.txt` -> doctor gate PASS, `DOCTOR_FAILED=0`.
- `evidence/line_segmentation_q5/FINAL_LINE_SEGMENTATION_Q5_REPORT.md` -> final Q5 decision `Q5_PARTIAL_FURTHER_IMPROVEMENT_REQUIRED`.

## TASK-034-Q6 Evidence
- `backend/app/services/evaluation/ocr_pipeline_optimization.py` -> `assign_components_to_lines`, `reconstruct_rtl_line_text`, `score_recognition_candidate`, `arabic_script_ratio`.
- `backend/tests/test_hybrid_recognition_q6.py` -> Q6 assignment, RTL reconstruction, candidate scoring, leakage and config freeze/hash tests.
- `scripts/hybrid_recognition_q6.py` -> Q6 locked pilot runner; Q5 frozen config verification and Page 1 development / Page 2-3 pilot_validation split enforcement.
- `evidence/hybrid_recognition_q6/ground_truth_integrity_before.json` and `ground_truth_integrity_after.json` -> unchanged GT combined SHA-256 `59288698485deae4fb618a1554c43bb827745ca6ee3a6566e3d34c994dc44527`.
- `evidence/hybrid_recognition_q6/q5_config_integrity.json` -> Q5 frozen config canonical SHA-256 `310d5a33874e38194d31101a26a83b0bb2c415af6a3209fb4c15d61fa9316373`.
- `evidence/hybrid_recognition_q6/q5_cer_regression_analysis.md` -> Q5 direct line-crop OCR regression analysis.
- `evidence/hybrid_recognition_q6/crop_quality_diagnostics.csv`, `component_assignment_metrics.json`, `component_assignments.csv` -> Q6 assignment and crop diagnostics.
- `evidence/hybrid_recognition_q6/word_gap_ablation.csv`, `recognition_candidate_ablation.csv` -> Page 1 development-only config selection evidence.
- `evidence/hybrid_recognition_q6/selected_hybrid_config.json` and `selected_hybrid_config.sha256` -> frozen Q6 config `component_filter_lowconf`, checksum `50bb99ece97b5f9b50833011bea28424ada7075d88953497ed2031e27bcaabc1`.
- `evidence/hybrid_recognition_q6/development_metrics.json` -> development normalized CER `0.136743`, normalized WER `0.696517`, line F1 `0.938776`, overall reading-order `1.0`.
- `evidence/hybrid_recognition_q6/pilot_validation_metrics.json` -> pilot_validation normalized CER `0.130635`, normalized WER `0.706897`, line F1 `0.961538`, overall reading-order `1.0`.
- `evidence/hybrid_recognition_q6/candidate_decision_trace.jsonl` -> per-line candidate trace and selected source candidate.
- `evidence/hybrid_recognition_q6/oracle_diagnostic.json` -> `DIAGNOSTIC_ONLY_NOT_PRODUCTION` comparison.
- `evidence/hybrid_recognition_q6/q4_q5_q6_comparison.md` -> Q4/Q5/Q6 metric-context comparison.
- `evidence/hybrid_recognition_q6/line_error_analysis.csv`, `overlays/*.png` -> line-level errors and visual overlays.
- `evidence/hybrid_recognition_q6/targeted_tests.txt` -> targeted tests PASS, 28 passed.
- `evidence/hybrid_recognition_q6/backend_regression.txt` -> backend regression PASS, 122 passed.
- `evidence/hybrid_recognition_q6/doctor_gate.txt` -> doctor gate PASS, `DOCTOR_FAILED=0`.
- `evidence/hybrid_recognition_q6/FINAL_HYBRID_RECOGNITION_Q6_REPORT.md` -> final Q6 decision `Q6_PARTIAL_WORD_BOUNDARY_IMPROVEMENT_REQUIRED`.


## VERIFY-LIVE-EVAL-20260802 Evidence Map
- `backend/.env` -> selected non-secret runtime settings; `DATABASE_URL=sqlite:///./ottoman_assistant.db`.
- `backend/ottoman_assistant.db` -> live SQLite database used for dataset/job verification.
- `evidence/verify_live_state_20260802/live_state.json` -> dataset `2`, lock, review counters, audit count, and job `1` state.
- `evidence/verify_live_state_20260802/pilot_metrics_live_verified.json` -> locked human-verified OCR metrics.
- `evidence/verify_live_state_20260802/LIVE_OCR_EVALUATION_REPORT.md` -> page metrics, best/worst lines, common error categories, and acceptance decision.
- `backend/worker.py` -> `process_pilot_evaluation_job` now honors `job.result_path` and uses per-job CSV/report evidence names.
- `backend/tests/test_worker_robustness.py` -> `test_pilot_evaluation_uses_job_result_path_source_contract` prevents regression to shared hard-coded metrics output.
- `evidence/verify_live_state_20260802/backend_full_tests.txt`, `frontend_lint.txt`, `frontend_build.txt`, `evaluation_job_smoke.txt` -> regression and smoke evidence.

## TASK-034-Q5 Evidence Map
- `evidence/line_segmentation_q5/ground_truth_integrity_before.json` and `ground_truth_integrity_after.json` -> GT before/after hash `59288698485deae4fb618a1554c43bb827745ca6ee3a6566e3d34c994dc44527`.
- `evidence/line_segmentation_q5/split_manifest.json` -> existing split preserved: validation page `[1]`, test pages `[2, 3]`, train `[]`.
- `evidence/line_segmentation_q5/candidate_validation_results.csv` -> 8 controlled candidate validation results across detection/box merging, preprocessing and recognition/normalization families.
- `evidence/line_segmentation_q5/test_metrics_q5.json` -> untouched test metrics for `recognition_beam_merged`.
- `evidence/line_segmentation_q5/FINAL_Q5_OCR_QUALITY_REPORT.md` -> final pilot engineering PASS decision.
- `backend/app/services/evaluation/ocr_pipeline_optimization.py` -> Q5 geometry helpers: `clean_component_boxes`, `remove_nested_boxes`, `merge_adjacent_line_boxes`.
- `backend/app/services/document_processing/ocr_engine.py` -> `EasyOCREngine.Q5_CONFIG_VERSION`, `Q5_CONFIG_SHA256`, `Q5_READTEXT_CONFIG`, and merged RTL line output in `extract`.
- `backend/tests/test_line_segmentation_q5.py` and `backend/tests/test_ocr_engine.py` -> Q5 helper and production metadata regression tests.

## 2026-08-09 TASK-008 Reference UI Evidence
- **Claim:** Frontend stack Next.js 16.2.11 + React 19.2.4 + TypeScript + Tailwind CSS 4.
  - **Evidence:** `frontend/package.json`; `evidence/ui_reference_implementation/frontend_stack.txt`.
- **Claim:** Duplicate route build failure repaired by removing old root pages and using `(app)` group pages as active route surface.
  - **Evidence:** `frontend/src/app/(app)/dashboard/page.tsx`; `frontend/src/app/(app)/upload/page.tsx`; `frontend/src/app/(app)/settings/page.tsx`; `frontend/src/app/(app)/documents/[id]/page.tsx`; `evidence/ui_reference_implementation/build_result.txt`.
- **Claim:** Document workspace no longer uses estimated bbox overlay and reads OCR bbox/confidence from API result lines.
  - **Evidence:** `frontend/src/app/(app)/documents/[id]/page.tsx` -> `getLineBox`, `pipeline_results.lines`; `frontend/src/lib/api.ts` -> `OCRPipelineLine`.
- **Claim:** Transcription and modern Turkish are separated in UI data binding.
  - **Evidence:** `frontend/src/app/(app)/documents/[id]/page.tsx` -> `transcriptionText`, `modernText`; `frontend/src/lib/api.ts` -> `transliterated_text`, `modernized_text`.
- **Claim:** Summary card does not reuse modern Turkish text as summary.
  - **Evidence:** `frontend/src/app/(app)/documents/[id]/page.tsx` -> `summaryText`; `frontend/src/lib/api.ts` -> `summary_text`.
- **Claim:** Frontend lint and production build pass.
  - **Evidence:** `evidence/ui_reference_implementation/lint_result.txt`; `evidence/ui_reference_implementation/build_result.txt`.
- **Claim:** Full backend E2E is not verified in this run.
  - **Evidence:** `evidence/ui_reference_implementation/api_integration_check.txt`; backend `localhost:8000` requests timed out.
- **Claim:** Document workspace matches the reference layout in source structure.
  - **Evidence:** `frontend/src/app/(app)/documents/[id]/page.tsx` -> `DocumentDetailPage`, `transcriptionText`, `modernText`, `summaryText`, `getLineBox`; `frontend/src/app/globals.css` -> `.analysis-grid`, `.viewer-card`, `.ocr-results-card`, `.analysis-side-stack`, `.bottom-info-card`, `.confidence-widget`.
- **Claim:** Authenticated visual comparison is still pending.
  - **Evidence:** `evidence/ui_reference_implementation/screenshots/document-workspace-route.png`; screenshot shows login/auth state because no browser token was available.

## 2026-08-09 TASK-008 Complete UI E2E Evidence
- **Claim:** Backend connectivity repaired.
  - **Evidence:** `evidence/ui_reference_implementation/backend_health.txt`, `backend_startup_log.txt`, `frontend_backend_connection.txt`.
- **Claim:** Real auth/upload/OCR flow passed.
  - **Evidence:** `evidence/ui_reference_implementation/auth_e2e.json`, `upload_e2e.json`, `e2e_result.json`.
- **Claim:** Kraken was the actual runtime engine and fallback was not used.
  - **Evidence:** `evidence/ui_reference_implementation/kraken_ui_metadata.json`, `kraken_model_hash.txt`, `worker_log.txt`.
- **Claim:** Document workspace rendered real OCR results and visual reference layout.
  - **Evidence:** `evidence/ui_reference_implementation/visual_automation_result.json`, `document_workspace_result.json`, `screenshots/document_workspace.png`.
## 2026-08-09 Premium Auth UI
- **Claim:** Login ve register ekranlari premium koyu tema, altin vurgu ve Osmanlica belge/OCR hero sahnesiyle uygulandi.
  - **Evidence:** `frontend/src/components/auth/AuthShell.tsx`; `frontend/src/app/login/page.tsx`; `frontend/src/app/register/page.tsx`; `frontend/src/app/globals.css`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Login/register gerçek frontend auth API katmanini kullanir.
  - **Evidence:** `frontend/src/app/login/page.tsx` → `authApi.login`; `frontend/src/app/register/page.tsx` → `authApi.register`; `frontend/src/lib/api.ts` → `setToken`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Auth UI lint/build/route/screenshot gate'lerinden gecti.
  - **Evidence:** `evidence/auth_ui_implementation/lint_result.txt`; `build_result.txt`; `route_status.json`; `screenshot_result.json`; `screenshots/login.png`; `screenshots/register.png`.
  - **Evidence Class:** VERIFIED.

## 2026-08-09 Windows Runtime Launcher
- **Claim:** Windows launcher sistemi backend, worker ve frontend servislerini PID guvenligiyle baslatip durdurur.
  - **Evidence:** `scripts/runtime_launcher.ps1`; `START_APP.bat`; `STOP_APP.bat`; `RESTART_APP.bat`; `evidence/runtime_launcher/start_test.txt`; `stop_test.txt`; `restart_test.txt`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Runtime config `127.0.0.1:3000` frontend ve `127.0.0.1:8000/api/v1` backend API standardina getirildi.
  - **Evidence:** `frontend/src/lib/api.ts`; `scripts/runtime_launcher.ps1`; `evidence/runtime_launcher/frontend_health.txt`; `backend_health.txt`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Kraken runtime acceptance gecti.
  - **Evidence:** `evidence/runtime_launcher/model_hash.txt`; `wsl_check.txt`; `kraken_runtime_metadata.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Auth/upload/document workspace/OCR smoke tests gecti.
  - **Evidence:** `evidence/runtime_launcher/auth_smoke.txt`; `upload_smoke.txt`; `document_workspace_result.json`; `document_ui_smoke.json`.
  - **Evidence Class:** VERIFIED.

## 2026-08-09 Downstream Text Repair Evidence
- **Claim:** Transliteration no longer returns only raw consonant skeletons for common Ottoman formulae and history narrative words.
  - **Evidence:** `backend/app/services/document_processing/translator.py`; `backend/tests/test_transliteration.py`; `evidence/downstream_text_repair/transliteration_before_after.txt`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Modernization no longer copies transliteration when quality rules cannot produce a distinct result.
  - **Evidence:** `backend/app/services/document_processing/translator.py` -> `_is_distinct_modernization`, `_quality_flags`; `backend/tests/test_modernization.py`; `evidence/downstream_text_repair/modernization_before_after.txt`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Pipeline/API expose separate OCR, Latin, modern Turkish and summary fields.
  - **Evidence:** `backend/app/services/document_processing/pipeline.py`; `backend/app/api/routes/ocr.py`; `frontend/src/app/(app)/documents/[id]/page.tsx`; `frontend/src/lib/api.ts`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Real document run used Kraken and did not fall back.
  - **Evidence:** `evidence/downstream_text_repair/api_payload.json` -> `model_info.recognizer=kraken`, `model_info.fallback_used=false`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Frontend document workspace field binding is correct for this contract.
  - **Evidence:** `evidence/downstream_text_repair/ui_render_check.txt`; `frontend/src/app/(app)/documents/[id]/page.tsx` -> `ocrText`, `transcriptionText`, `modernText`, `summaryText`, `getLineBox`.
  - **Evidence Class:** VERIFIED.

## 2026-08-09 Line Filter Repair Evidence
- **Claim:** Backend OCR line filtering rejects empty, decorative, low-ink, low-component and garbage OCR candidates before they reach persisted OCR lines.
  - **Evidence:** `backend/app/services/document_processing/ocr_engine.py` -> `LineFilterConfig`, `analyze_line_candidate`, `filter_ocr_lines`, `refine_line_bbox_to_text_ink`; `evidence/line_filter_repair/filter_rules.txt`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Real Kraken OCR run no longer includes the top printed title/header and bottom instruction/footer phantom boxes.
  - **Evidence:** `evidence/line_filter_repair/before_overlay.png`; `evidence/line_filter_repair/after_overlay.png`; `evidence/line_filter_repair/before_lines.json`; `evidence/line_filter_repair/after_lines.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Line count became cleaner without changing the recognition model or falling back from Kraken.
  - **Evidence:** `evidence/line_filter_repair/after_lines.json` -> `line_filter.segmenter_input_count=25`, `segmenter_kept_count=23`, `actual_engine=kraken`, `fallback_used=false`; `models/recognition/ottoman_recognition_final_v1.mlmodel` SHA `f5abbba1976e9782ddf5d7185d911722c74558e12b57a12566c96e22a3e3b963`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Pipeline and UI prevent multi-page bbox leakage by carrying real page ids and rendering only selected-page lines.
  - **Evidence:** `backend/app/services/document_processing/pipeline.py`; `backend/worker.py`; `frontend/src/lib/api.ts`; `frontend/src/app/(app)/documents/[id]/page.tsx`; `evidence/line_filter_repair/pipeline_after.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Regression checks passed for backend OCR/layout/pipeline and frontend lint/build.
  - **Evidence:** `evidence/line_filter_repair/LINE_FILTER_REPAIR_REPORT.md`; command results recorded in report.
  - **Evidence Class:** VERIFIED.

## 2026-08-09 Final Text and Segmentation Check Evidence
- **Claim:** Final integrated OCR payload has clean line/bbox output on the real document page.
  - **Evidence:** `evidence/final_text_and_segmentation_check/final_runtime_metadata.json` -> `line_count=23`, `bbox_count=23`, `blank_line_count=0`, `low_usefulness_line_count=0`.
  - **Evidence Class:** VERIFIED.
- **Claim:** OCR, Latin transliteration and modern Turkish modernization are populated and distinct.
  - **Evidence:** `evidence/final_text_and_segmentation_check/final_runtime_metadata.json` -> `transliteration_distinct_from_ocr=true`, `modernization_distinct_from_transliteration=true`; `final_api_payload.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Frontend API/UI field mapping remains aligned with the repaired payload contract.
  - **Evidence:** `evidence/final_text_and_segmentation_check/final_ui_check.txt`; `frontend/src/app/(app)/documents/[id]/page.tsx`; `frontend/src/lib/api.ts`; `backend/app/api/routes/ocr.py`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Final runtime uses Kraken without fallback and keeps the final model unchanged.
  - **Evidence:** `evidence/final_text_and_segmentation_check/final_runtime_metadata.json` -> `recognizer=kraken`, `fallback_used=false`, model SHA `f5abbba1976e9782ddf5d7185d911722c74558e12b57a12566c96e22a3e3b963`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Regression checks passed across line filtering, downstream text processing and frontend compilation.
  - **Evidence:** `evidence/final_text_and_segmentation_check/FINAL_TEXT_AND_SEGMENTATION_REPORT.md` -> backend 22 passed, frontend lint PASS, frontend build PASS.
  - **Evidence Class:** VERIFIED.

## 2026-08-09 Auth Reference Match Evidence
- **Claim:** Login and register screens now use the supplied dark/gold centered premium visual direction.
  - **Evidence:** `frontend/src/components/auth/AuthShell.tsx`; `frontend/src/app/globals.css`; `evidence/auth_reference_match/screenshots/login.png`; `evidence/auth_reference_match/screenshots/register.png`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Real auth API integration was preserved.
  - **Evidence:** `frontend/src/app/login/page.tsx` -> `authApi.login`, `setToken`; `frontend/src/app/register/page.tsx` -> `authApi.register`, `setToken`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Frontend quality gates pass after the visual update.
  - **Evidence:** `evidence/auth_reference_match/AUTH_REFERENCE_MATCH_REPORT.md` -> `npm.cmd run lint` PASS, `npm.cmd run build` PASS, `/login` and `/register` HTTP 200.
  - **Evidence Class:** VERIFIED.

## 2026-08-13 Unknown Document Pipeline Evidence
- **Claim:** Full unknown document backend analysis endpoint exists and accepts real uploads.
  - **Evidence:** `backend/app/api/routes/document_analysis.py` -> `analyze_full_document`; `backend/app/api/router.py` -> `document_analysis_router`; `backend/tests/test_unknown_document_pipeline.py` -> `test_analyze_full_endpoint_with_real_upload_real_ocr_ollama_and_qdrant`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Pipeline orchestrates preprocessing, OCR, transliteration, modern Turkish, NER, verified historical RAG and response assembly.
  - **Evidence:** `backend/app/services/document_analysis_pipeline.py` -> `DocumentAnalysisPipeline.analyze_document`, `_process_page`, `_transliterate`, `_modernize`, `_retrieve_verified_historical_evidence`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Structured response separates document evidence, historical external evidence, model inference and uncertainties.
  - **Evidence:** `backend/app/schemas/document_analysis.py` -> `FullDocumentAnalysisResponse`, `EvidenceInfo`, `HistoricalAnalysisInfo`, `ConfidenceInfo`; `backend/app/services/document_analysis_pipeline.py` response assembly.
  - **Evidence Class:** VERIFIED.
- **Claim:** Transliteration TODO/NotImplemented path now uses local Ollama instead of pending API keys.
  - **Evidence:** `backend/app/services/transliteration_service.py` -> `TransliterationEngine._call_llm`, `OllamaProvider.chat`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Historical external evidence excludes unverified sources and `derived_verified=false` relation candidates.
  - **Evidence:** `backend/app/services/document_analysis_pipeline.py` -> `_retrieve_verified_historical_evidence`; `backend/tests/test_unknown_document_pipeline.py` -> `test_historical_evidence_filters_unverified_and_derived_relation_candidates`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Existing document-internal FAISS/RAG and OCR regressions still pass.
  - **Evidence:** `python -m pytest tests/test_unknown_document_pipeline.py tests/test_processing_pipeline.py tests/test_transliteration.py tests/test_modernization.py tests/test_analysis.py tests/test_rag_chat.py tests/test_document_upload_integration.py tests/test_file_security.py tests/test_auth_security.py tests/test_smoke.py tests/test_ocr_engine.py tests/test_faiss_security.py -q` -> 55 passed.
  - **Evidence Class:** VERIFIED.
- **Claim:** Local Ollama and historical Qdrant infrastructure are reachable.
  - **Evidence:** `$env:PYTHONPATH='.'; $env:PYTHONIOENCODING='utf-8'; python scripts/smoke_local_llm.py` -> `LOCAL_BACKEND_LLM_GATE: PASS`; direct Qdrant count/search -> `HISTORICAL_QDRANT_COUNT 9541`, `ALL_VERIFIED True`.
  - **Evidence Class:** VERIFIED.

## 2026-08-13 Kraken Default Live HTTP Gate Evidence
- **Claim:** Real FastAPI HTTP endpoint `/api/v1/document/analyze-full` works with default Kraken OCR.
  - **Evidence:** `backend/evidence/kraken_live_http_gate/http_response.json` -> HTTP 200; response `ocr.engine=kraken`, `ocr.fallback_used=false`, OCR output length 1148.
  - **Evidence Class:** VERIFIED.
- **Claim:** Kraken model and runtime were used, not only configured.
  - **Evidence:** `backend/evidence/kraken_live_http_gate/kraken_runtime_evidence.txt`; `server_log.txt`; `server_err.txt`; `config_snapshot.json` -> model SHA and WSL CUDA probe.
  - **Evidence Class:** VERIFIED.
- **Claim:** Historical external evidence remained verified-only and provenance-preserving.
  - **Evidence:** `backend/evidence/kraken_live_http_gate/gate_report.json` -> checks `historical_evidence_verified_only=true`, `historical_provenance_present=true`, historical evidence count 5.
  - **Evidence Class:** VERIFIED.
- **Claim:** Required regressions passed after live gate.
  - **Evidence:** `backend/evidence/kraken_live_http_gate/regression_tests.txt` -> `tests/test_unknown_document_pipeline.py`, `tests/test_ocr_engine.py`, `tests/test_faiss_security.py`, `tests/test_kraken_integration.py`, 22 passed.
  - **Evidence Class:** VERIFIED.
- **Claim:** Non-ASCII upload working path is a separate Windows/OpenCV risk discovered during gate.
  - **Evidence:** `backend/evidence/kraken_live_http_gate/http_response.json` earlier failure detail and `server_err.txt` OpenCV `imread` warning; final gate used ASCII runtime upload dir in `config_snapshot.json`.
  - **Evidence Class:** VERIFIED.

## 2026-08-13 Non-ASCII Image Path Hardening Evidence
- **Claim:** Production OpenCV image loading/writing no longer depends on Windows path-string support.
  - **Evidence:** `backend/app/services/image_io.py` -> `read_image_unicode_safe`, `write_image_unicode_safe`; `backend/app/services/document_analysis_pipeline.py` -> `DocumentAnalysisPipeline._process_page`; `backend/app/services/document_processing/preprocessor.py` -> `ImagePreprocessor.process_with_profile`; `backend/app/api/routes/preprocessing.py` -> `create_preprocess_variant`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Unicode-safe image IO preserves BGR, grayscale, alpha, dtype and dimensions on Turkish/non-ASCII paths.
  - **Evidence:** `backend/tests/test_unicode_image_io.py`; `backend/evidence/non_ascii_path_gate/unicode_image_io_tests.txt` -> 10 passed.
  - **Evidence Class:** VERIFIED.
- **Claim:** Real HTTP full-analysis endpoint now works without an ASCII `UPLOAD_DIR` workaround under `Masaüstü`.
  - **Evidence:** `backend/evidence/non_ascii_path_gate/http_response.json`; `gate_report.json` -> HTTP 200, `upload_dir_overridden=false`, non-ASCII upload root true.
  - **Evidence Class:** VERIFIED.
- **Claim:** Kraken executed after the Unicode path fix and did not fall back to EasyOCR/mock OCR.
  - **Evidence:** `backend/evidence/non_ascii_path_gate/kraken_runtime_evidence.txt`; `gate_report.json` -> `ocr_engine=kraken`, `ocr_fallback_used=false`, OCR output length 1148, line count 23.
  - **Evidence Class:** VERIFIED.
- **Claim:** Required regression tests passed after hardening.
  - **Evidence:** `backend/evidence/non_ascii_path_gate/regression_tests.txt` -> `tests/test_unknown_document_pipeline.py`, `tests/test_ocr_engine.py`, `tests/test_kraken_integration.py`, `tests/test_faiss_security.py`, `tests/test_unicode_image_io.py`, 32 passed.
  - **Evidence Class:** VERIFIED.

## 2026-08-13 Production Main Dashboard Integration Evidence
- **Claim:** Main dashboard calls the production full-analysis endpoint instead of mock or list-only behavior.
  - **Evidence:** `frontend/src/lib/api.ts` -> `analysisApi.analyzeFull`; `frontend/src/app/(app)/dashboard/page.tsx` -> `handleAnalyze`; `evidence/main_dashboard_gate/api_request_evidence.json` -> endpoint `/api/v1/document/analyze-full`, HTTP 200.
  - **Evidence Class:** VERIFIED.
- **Claim:** Dashboard renders real Ottoman OCR, transliteration, modern Turkish, historical analysis, uncertainty and evidence from the backend response.
  - **Evidence:** `frontend/src/app/(app)/dashboard/page.tsx` -> OCR/Modern/Transliteration/Evidence render sections; `evidence/main_dashboard_gate/api_request_evidence.json` -> all UI checks true.
  - **Evidence Class:** VERIFIED.
- **Claim:** Kraken actually executed and no EasyOCR/mock fallback was used by the integration run.
  - **Evidence:** `evidence/main_dashboard_gate/api_response_snapshot.json` -> `ocr.engine=kraken`, `ocr.fallback_used=false`, 23 OCR lines.
  - **Evidence Class:** VERIFIED.
- **Claim:** Historical evidence is separated into document evidence and external historical sources in the dashboard.
  - **Evidence:** `evidence/main_dashboard_gate/api_request_evidence.json` -> `documentEvidenceCards=22`, `externalEvidenceCards=5`; `frontend/src/app/(app)/dashboard/page.tsx` -> `EvidenceColumn`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Frontend quality gates pass after dashboard integration.
  - **Evidence:** `evidence/main_dashboard_gate/frontend_tests.txt` -> lint PASS, 0 errors / 11 existing warnings; `evidence/main_dashboard_gate/frontend_build.txt` -> Next.js production build PASS.
  - **Evidence Class:** VERIFIED.

## 2026-08-13 Image Processing Lab Evidence
- **Claim:** Dedicated Image Processing Lab screen exists and uses real preprocessing APIs.
  - **Evidence:** `frontend/src/app/(app)/image-processing-lab/page.tsx` -> `ImageProcessingLabPage`, `runLab`; `frontend/src/lib/api.ts` -> `documentsApi`, `pagesApi`, `preprocessingApi`, `fetchAuthenticatedBlobUrl`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Current backend preprocessing pipeline exposes only final ImageVariant artifacts, not per-stage intermediate images.
  - **Evidence:** `backend/app/services/document_processing/preprocessor.py`; `backend/app/api/routes/preprocessing.py`; `backend/app/models/image_variant.py`; `evidence/image_processing_lab_gate/pipeline_audit.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Read-only preprocessing metadata is exposed without changing OCR/Kraken behavior.
  - **Evidence:** `backend/app/api/routes/preprocessing.py` -> `ImageVariantResponse.parameters`, list variants metadata; `backend/tests/test_document_upload_integration.py` response parameters assertion.
  - **Evidence Class:** VERIFIED.
- **Claim:** Lab renders original image, real OCR-safe final image, unavailable states for missing stages and before/after slider.
  - **Evidence:** `evidence/image_processing_lab_gate/api_request_evidence.json` -> 12 DOM checks PASS; `image_processing_lab_screenshot.png`.
  - **Evidence Class:** VERIFIED.
- **Claim:** No fake/generated restoration is used as OCR input.
  - **Evidence:** `frontend/src/app/(app)/image-processing-lab/page.tsx` -> Visual Restoration placeholder; `evidence/image_processing_lab_gate/no_mock_audit.txt`; `image_processing_lab_report.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Frontend and backend gates passed.
  - **Evidence:** `evidence/image_processing_lab_gate/frontend_build.txt`; `frontend_tests.txt`; `backend_tests.txt` -> 18 passed.
  - **Evidence Class:** VERIFIED.

## 2026-08-13 Build Production Image Processing Lab UI Evidence
- **Claim:** `/image-processing` is the production Image Processing Lab route and sidebar active state works.
  - **Evidence:** `frontend/src/app/(app)/image-processing/page.tsx`; `frontend/src/components/dashboard/Sidebar.tsx`; `evidence/image_processing_lab_gate/dom_verification.json` -> `route_opens=true`, `sidebar_active=true`.
  - **Evidence Class:** VERIFIED.
- **Claim:** The screen uses real upload/page/preprocessing APIs and renders real original/final images.
  - **Evidence:** `frontend/src/app/(app)/image-processing-lab/page.tsx` -> `runLab`; `evidence/image_processing_lab_gate/api_request_evidence.json` -> real requests and `preprocessing_response`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Missing intermediate stages, masks and visual restoration are not fabricated.
  - **Evidence:** `evidence/image_processing_lab_gate/pipeline_audit.json`; `stage_inventory.json`; `button_functionality_audit.json`; `dom_verification.json` -> unavailable stages 8, disabled masks true, restoration isolated true.
  - **Evidence Class:** VERIFIED.
- **Claim:** Viewer controls and comparison controls work in browser.
  - **Evidence:** `evidence/image_processing_lab_gate/dom_verification.json` -> zoom, reset, pan, before/after slider, side-by-side and sync zoom true; screenshots `image_processing_lab_screenshot.png`, `image_processing_lab_mobile.png`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Frontend and backend regressions pass after UI hardening.
  - **Evidence:** `evidence/image_processing_lab_gate/frontend_tests.txt` -> lint PASS 0 errors / 11 existing warnings; `frontend_build.txt` -> build PASS; `backend_tests.txt` -> 35 passed.
  - **Evidence Class:** VERIFIED.

## 2026-08-13 Historical Analysis RAG Dashboard Evidence
- **Claim:** `/historical-analysis` is a dedicated production route and sidebar active state works.
  - **Evidence:** `frontend/src/app/(app)/historical-analysis/page.tsx`; `frontend/src/components/dashboard/Sidebar.tsx`; `evidence/historical_analysis_dashboard_gate/dom_verification.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** The screen uses real full-analysis backend data, not hardcoded historical results.
  - **Evidence:** `frontend/src/app/(app)/dashboard/page.tsx` sessionStorage persistence after `analysisApi.analyzeFull`; `evidence/historical_analysis_dashboard_gate/api_response_snapshot.json` -> real HTTP 200 from `/api/v1/document/analyze-full`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Kraken executed and no OCR fallback was used in the source response.
  - **Evidence:** `evidence/historical_analysis_dashboard_gate/kraken_runtime_evidence.txt` -> `ocr_engine: kraken`, `fallback_used: False`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Document evidence, verified external evidence, model inference and uncertainty are rendered separately.
  - **Evidence:** `frontend/src/app/(app)/historical-analysis/page.tsx`; `evidence/historical_analysis_dashboard_gate/dom_verification.json` -> document/external/inference/uncertainty pill counts and source/model card counts.
  - **Evidence Class:** VERIFIED.
- **Claim:** `derived_verified=false` relation candidates are not presented as confirmed facts.
  - **Evidence:** `frontend/src/app/(app)/historical-analysis/page.tsx` relationship graph unavailable panel; `evidence/historical_analysis_dashboard_gate/evidence_source_audit.json` -> no returned external evidence has `derived_verified=false`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Frontend quality and browser E2E gates pass.
  - **Evidence:** `evidence/historical_analysis_dashboard_gate/frontend_tests.txt`; `frontend_build.txt`; `dom_verification.json`; `historical_dashboard_screenshot.png`; `historical_dashboard_report.json`.
  - **Evidence Class:** VERIFIED.

## 2026-08-13 Final Product Integration Gate Evidence
- **Claim:** The three production screens share one safe active document context without storing secrets or filesystem paths in frontend storage.
  - **Evidence:** `frontend/src/lib/documentContext.ts`; `evidence/final_product_integration_gate/cross_screen_state_audit.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Real browser journey uploads a real Ottoman document, receives HTTP 200 from `/api/v1/document/analyze-full`, and Kraken executes without fallback.
  - **Evidence:** `evidence/final_product_integration_gate/http_response.json`; `final_product_report.json`; `main_dashboard_e2e.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Same document context is preserved from Main Dashboard to Image Processing Lab to Historical Analysis and back, with no duplicate full-analysis request.
  - **Evidence:** `evidence/final_product_integration_gate/navigation_e2e.json`; `image_processing_lab_e2e.json`; `historical_analysis_e2e.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Direct navigation, unsupported file, failed request, partial/no historical result and new analysis reset are safe.
  - **Evidence:** `evidence/final_product_integration_gate/negative_tests.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** UI does not leak local filesystem paths, model paths, Qdrant paths, API keys or stack traces across the three screens.
  - **Evidence:** `evidence/final_product_integration_gate/security_audit.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Required frontend and backend regression gates passed.
  - **Evidence:** `evidence/final_product_integration_gate/frontend_tests.txt`; `frontend_build.txt`; `backend_regression.txt`; screenshots `01_main_dashboard.png`, `02_image_processing_lab.png`, `03_historical_analysis.png`, `04_mobile_view.png`.
  - **Evidence Class:** VERIFIED.

## 2026-08-13 Final Professor Demo and Release Gate Evidence
- **Claim:** One-command pre-demo health and startup work on the local Windows demo environment.
  - **Evidence:** `scripts/pre_demo_check.ps1`; `scripts/start_demo.ps1`; `evidence/final_release_gate/pre_demo_health.json`; `startup_test.txt`; `startup_state.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Real browser demo hit the live full-analysis endpoint and completed downstream OCR/translation/RAG flow.
  - **Evidence:** `evidence/final_release_gate/browser_demo_e2e.json` -> HTTP 200, `ocr_engine=kraken`, `fallback_used=false`, modern Turkish chars 1271, verified external evidence count 5.
  - **Evidence Class:** VERIFIED.
- **Claim:** Release config and security audits passed after hardening `DEBUG` default.
  - **Evidence:** `backend/app/core/config.py`; `evidence/final_release_gate/release_config_audit.json`; `security_audit.json`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Required regression gates pass.
  - **Evidence:** `evidence/final_release_gate/backend_tests.txt` -> 55 passed; `frontend_build.txt` -> build PASS; `frontend_lint.txt` -> 0 errors / 12 warnings.
  - **Evidence Class:** VERIFIED.
- **Claim:** Final release gate is partial, not pass, because production browser emitted hydration page errors.
  - **Evidence:** `evidence/final_release_gate/final_release_report.json`; `browser_demo_e2e.json`.
  - **Evidence Class:** VERIFIED.

## 2026-08-14 Dashboard Embedded Image Processing Lab Evidence
- **Claim:** Main dashboard preserves the existing three-panel result grid while adding an embedded image-processing lab below it.
  - **Evidence:** `frontend/src/app/(app)/dashboard/page.tsx` -> `DashboardPage`, `.pd-main-grid`, `.pd-image-lab`; Playwright DOM check `main_grid_three_panels=true`, `image_lab_panel=true`.
  - **Evidence Class:** VERIFIED.
- **Claim:** The embedded lab renders four stages, arrows, status copy and the `Yeniden Isle` action.
  - **Evidence:** `frontend/src/app/(app)/dashboard/page.tsx` -> `imageLabStages`; `frontend/src/app/globals.css` -> `.pd-image-lab-flow`; `evidence/dashboard_image_lab_embed/dom_verification.json` -> `stage_count=true`, `arrow_count=true`, `reprocess_button=true`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Sidebar contains the added `Goruntu Isleme Labi` entry under existing navigation styling without deleting existing items.
  - **Evidence:** `frontend/src/components/dashboard/Sidebar.tsx` -> `NAV_ITEMS`; `frontend/src/components/Icons.tsx` -> `Icons.flask`; `evidence/dashboard_image_lab_embed/dom_verification.json` -> `sidebar_lab_link=true`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Latin Harfli Okunus section is collapsible and re-openable.
  - **Evidence:** `frontend/src/app/(app)/dashboard/page.tsx` -> `showTransliteration`, `.pd-transliteration-header`; `evidence/dashboard_image_lab_embed/dom_verification.json` -> `latin_collapses=true`, `latin_reopens=true`.
  - **Evidence Class:** VERIFIED.
- **Claim:** Frontend quality gates pass after the UI addition.
  - **Evidence:** `npm.cmd run lint` -> PASS, 0 errors / 12 existing warnings; `npm.cmd run build` -> PASS.
  - **Evidence Class:** VERIFIED.
# 2026-08-20 GitHub Source Publish Refresh Evidence

- `VERIFIED`: `_github_publish_clean/PROJECT_OVERVIEW.md` -> proje amaci, ne yapar ve nasil calisir aciklamasi.
- `VERIFIED`: `_github_publish_clean/.gitignore` -> wiki, genel Markdown, env, DB, model, data ve runtime artefakt dislama kurallari.
- `VERIFIED`: Komut `PUBLISH_CONTENT_GATE_PASS` -> yayin paketinde yalniz `PROJECT_OVERVIEW.md` Markdown olarak kaldi; `docs/wiki`, gercek env, DB/model artefakti bulunmadi.
- `VERIFIED`: Komut `git push origin main` -> remote `main` branch `fabe5e07f0bc8cf0015c183f438ff60a1454782a` commit'ine guncellendi.

# 2026-08-20 Real Document Recovery Revalidation Evidence

- `VERIFIED`: `backend/uploads/originals/62/62_a8da8b91.jpg` DB kaydi `original_filename=silah-atmama-ilani_ahmed-vefik-pasa.jpg` ile gercek kullanici belgesidir.
- `VERIFIED`: `evidence/recovery_real_document_revalidation/baseline_summary.json` -> eski live runtime baseline `ocr_line_count=1`, `ocr_confidence=0.2813`, `ocr_text_chars=1`.
- `VERIFIED`: `evidence/recovery_real_document_revalidation/variant_forensic/variant_ocr_metrics.json` -> ORIGINAL/GRAYSCALE/OTSU varyantlari 12-14 line uretirken CURRENT_TEMIZ_BASKI tek line uretir.
- `VERIFIED`: `backend/app/services/document_processing/preprocessor.py` -> `select_ocr_optimized_image`, `_preservation_metrics`, CLEAN_READABLE_DOCUMENT ink-preserving update.
- `VERIFIED`: `backend/app/services/document_processing/translator.py` -> low-evidence modern line fallback and Ottoman/Turkish noisy token lexicon additions.
- `VERIFIED`: `backend/app/services/document_analysis_pipeline.py` -> claim-level `document_claims`, RAG dedup/relevance and external-evidence claim gate.
- `VERIFIED`: `backend/app/schemas/document_analysis.py` and `frontend/src/lib/api.ts` -> `evidence.document_claims` response contract.
- `VERIFIED`: `evidence/recovery_real_document_revalidation/verified_api_summary.json` -> fresh API document `67`, OCR 12 lines, transliteration 12 lines, modern 12 non-empty lines, RAG 0.
- `VERIFIED`: `evidence/recovery_real_document_revalidation/browser/browser_dashboard_summary.json` and `dashboard_real_document_after_fix.png` -> real dashboard browser upload HTTP 200 with Kraken/OCR/Latin/Modern rendered.
- `VERIFIED`: Backend targeted tests `21 passed`; frontend lint PASS `0 errors / 13 warnings`; frontend build PASS.

# 2026-08-21 Performance Audit 1C Evidence

- `VERIFIED`: `backend/app/services/document_analysis_pipeline.py` -> structured LLM line contract, exact `line_id` set validation, dynamic retry/split/fallback.
- `VERIFIED`: `backend/tests/test_unknown_document_pipeline.py` -> structured batch success and failed-large-batch split tests.
- `VERIFIED`: `backend/app/services/ai/ollama_provider.py` -> Ollama `keep_alive` payload support.
- `VERIFIED`: `backend/scripts/kraken_wsl_bridge.py` -> Kraken inference wrapped in `torch.inference_mode()` when available.
- `VERIFIED`: `frontend/src/app/(app)/dashboard/page.tsx` -> `analyzeInFlightRef` same-tick duplicate request guard.
- `VERIFIED`: `evidence/performance_audit/1c/llm_batch_benchmark.json` -> real Ollama 3/10/30 structured outputs preserve all line IDs.
- `VERIFIED`: `evidence/performance_audit/1c/ocr_deep_profile_after.json` and `gpu_sampling_after.csv` -> real Kraken OCR 13 lines, fallback false, GPU/VRAM sampled.
- `VERIFIED`: `evidence/performance_audit/1c/http_benchmark.json` -> live HTTP full e2e blocked by runtime saturation; no FULL PASS claim.
- `VERIFIED`: `evidence/performance_audit/1c/regression_tests.txt`; `frontend_lint_1c.txt`; `frontend_build_1c.txt` -> regression gates PASS.

# 2026-08-21 Performance Audit 1D Evidence

- `VERIFIED`: `backend/scripts/kraken_wsl_service.py` -> persistent WSL Kraken service loads model once and exposes health/ocr/shutdown endpoints.
- `VERIFIED`: `scripts/start_kraken_service.ps1`; `scripts/check_kraken_service.ps1`; `scripts/stop_kraken_service.ps1` -> service operational lifecycle scripts.
- `VERIFIED`: `backend/app/services/document_processing/kraken_service_client.py` and `backend/app/services/document_processing/ocr_engine.py` -> production OCR hot path uses persistent service first and logs explicit legacy fallback.
- `VERIFIED`: `evidence/performance_audit/1d/persistent_ocr_5_warm.json` -> 5 real warm OCR requests, `model_load_count=1`, `request_count=5`.
- `VERIFIED`: `evidence/performance_audit/1d/ocr_comparison_summary.json` -> legacy vs persistent OCR text hash and bbox order equal, improvement `90.31%`.
- `VERIFIED`: `backend/app/api/routes/document_analysis.py`, `backend/worker.py`, `backend/app/services/job_manager.py` -> async analyze job API and worker execution path.
- `VERIFIED`: `evidence/performance_audit/1d/live_async_result_after_completion.json` -> live job `38` completed, progress `100`, result endpoint PASS.
- `VERIFIED`: `evidence/performance_audit/1d/live_async_enqueue_after_tree_fix.json` -> POST analyze `202`, health samples during job P50/P95 recorded.
- `VERIFIED`: `scripts/runtime_launcher.ps1` -> process tree stop fix after orphan worker root cause.
- `VERIFIED`: `backend/tests/test_performance_audit_1d.py`; `backend_tests_1d.txt`; `frontend_lint_1d.txt`; `frontend_build_1d.txt` -> regression gates PASS.
- `PARTIAL`: 2-job live concurrency benchmark and fine-grained internal stage progress are not yet verified.
