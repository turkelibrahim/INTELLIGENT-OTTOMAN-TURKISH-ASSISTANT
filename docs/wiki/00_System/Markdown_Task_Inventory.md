---
type: task_inventory
status: verified
last_verified: 2026-08-02
owners: [codex]
source_paths:
  - docs/wiki/00_System/Task_Queue.md
  - PROMPTS/
  - docs/wiki/
tags: [markdown, tasks, inventory]
---

# Markdown Task Inventory

**Ozet:** Bu envanter aktif proje Markdown kaynaklarindaki uygulanabilir gorevleri tek listede birlestirir. Ucuncu taraf paket klasorleri, sanal ortamlar ve uretilmis cache klasorleri gorev kaynagi olarak dislanmistir. Eski paket kopyalari aktif kok talimatlarla `SUPERSEDED` sinifindadir.

**Kutuphaneler:** rg, PyTest, Playwright, FastAPI, Next.js.

**Baglantilar:** [[Task_Queue]], [[Current_State]], [[Requirements_Traceability_Matrix]], [[Latest_Handoff]]

## Kapsam

- Taranan proje Markdown dosyasi: 158
- Dosya listesi kaniti: `evidence/markdown_inventory/markdown_files_project_scoped.txt`
- Uygulanabilir tekil gorev sayisi: 34

## Durum Dagilimi

- `VERIFIED`: 31
- `PENDING`: 0
- `IN_PROGRESS`: 0
- `BLOCKED_EXTERNAL`: 1
- `SUPERSEDED`: 1

## Gorevler

### UI-FIX-20260802 - Belge Gorsel Goruntuleme ve OCR Sonuc Ekrani
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Yetki isteyen page image, thumbnail ve preprocessing variant image URL'leri tokenli fetch ile yuklenir.; Ana belge goruntusu ve sol sayfa thumbnail'i ham `<img src>` ile authsiz endpoint cagirmadi.; OCR sonucu tamamlandiginda `Sonuclari Incele` browser alert acmaz; OCR/metin/NER gorunumune gecer.; Sayfa yenilendiginde hazir OCR sonucu backend status endpointinden tekrar yuklenir.; Frontend lint/build PASS.; Genel doctor PASS.; `npm.cmd run lint` -> PASS.; `npm.cmd run build` -> PASS.
- **Ilgili kod:** `frontend/src/lib/api.ts`, `frontend/src/app/documents/[id]/page.tsx`, `docs/wiki/00_System/*`, `docs/wiki/05_UI/Document_Workspace.md`, `docs/wiki/10_Handoffs/Latest_Handoff.md`.
- **Test:** - [x] `npm.cmd run lint` -> PASS.
- **Kanit:** Bakiniz Task_Queue ve ilgili test/kanit satirlari.
- **Engel:** Yok.

### RECOVER-20260802 - Release Gate Reverification and Fixes
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Backend `pytest tests` PASS.; Frontend lint/build PASS.; Doctor script PASS.; Live backend health PASS.; Live register/login smoke PASS.; Real OCR smoke PASS.; Dependency security audit kritik/yuksek bulgu yok.; `python -m pytest tests -q` -> 70 passed.
- **Ilgili kod:** `frontend/src/lib/api.ts`, `frontend/src/app/documents/[id]/page.tsx`, `frontend/src/app/settings/page.tsx`, `scripts/doctor.ps1`, `backend/requirements.txt`, `docs/wiki/00_System/*`, `docs/wiki/10_Handoffs/Latest_Handoff.md`.
- **Test:** - [x] `python -m pytest tests -q` -> 70 passed.
- **Kanit:** evidence/task034_real_ocr/real_ocr_result.json
- **Engel:** Yok.

### TASK-001 - Kok AGENTS.md Anayasasini Netlestir
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** `AGENTS.md` okunur.; `PROMPTS/` listelenir.; Wiki koku `docs/wiki/` dogrulanir.; Dosya okuma kontrolleri.
- **Ilgili kod:** `docs/wiki/00_System/*`
- **Test:** - [x] Dosya okuma kontrolleri.
- **Kanit:** Bakiniz Task_Queue ve ilgili test/kanit satirlari.
- **Engel:** Yok.

### TASK-008 - Gereksinim Izlenebilirlik Matrisi
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Kod/wiki/prompt/baseline kanitlariyla matris olusturuldu.; Baseline status celiskileri duzeltildi.; Next.js icin proposed ADR olusturuldu.; SRS PDF tam metni cikarildi ve yakalanan tum SRS requirement ID'leri matrise eklendi.; Requirement ID scan.; Wiki link lint.; SRS text extraction.
- **Ilgili kod:** `docs/wiki/08_Testing/Requirements_Traceability_Matrix.md`, `docs/wiki/08_Testing/Acceptance_Criteria_Map.md`, sistem wiki dosyalari.
- **Test:** - [x] Requirement ID scan.
- **Kanit:** evidence/requirements_traceability/srs_extract_log_autonomous.txt
- **Engel:** Yok.

### TASK-009 - Environment ve Test Gate
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Git status alinamadigi icin alternatif versiyon kaniti `source_hash_manifest.txt` ile tanimlandi.; Backend test runner calisir.; Frontend lint/build komutlari gate olarak belgelenir.; Backend pytest/smoke.; Frontend lint/build.
- **Ilgili kod:** DOÃ„Å¾RULANMADI; muhtemel docs/evidence ve test dependency karari.
- **Test:** - [x] Backend pytest/smoke.
- **Kanit:** evidence/environment_gate/doctor_full.txt
- **Engel:** Yok.

### TASK-010 - Database Migration ve Rollback Gate
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Temiz DB init testi.; Migration/rollback stratejisi.; Kullanici verisi korunur: testler gecici SQLite DB uzerinde calisti; `backend/ottoman_assistant.db` ve `backend/uploads/` degistirilmedi.
- **Ilgili kod:** `backend/alembic.ini`, `backend/alembic/`, `backend/app/models/processing_outputs.py`, `backend/tests/test_migrations.py`, `backend/tests/test_smoke.py`.
- **Test:** DB init/rollback smoke.
- **Kanit:** evidence/environment_gate/backend_pytest_after_traceability_columns.txt
- **Engel:** Yok.

### TASK-011 - Auth, Roller ve Belge Izolasyonu Testleri
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** `backend/tests/test_auth_security.py`, `backend/tests/test_file_security.py`, `frontend/package.json`, `frontend/package-lock.json`.
- **Test:** Auth integration tests, file security unit tests, dependency audit.
- **Kanit:** evidence/environment_gate/backend_pytest_task011_full.txt
- **Engel:** Yok.

### TASK-012 - Belge Yukleme, Dosya Guvenligi ve Audit
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** `backend/tests/test_document_upload_integration.py`, `backend/app/api/routes/preprocessing.py`.
- **Test:** Upload positive/negative tests, delete/audit cleanup, preprocessing variant integration.
- **Kanit:** evidence/environment_gate/backend_pytest_task012_after_fix.txt
- **Engel:** Yok.

### TASK-013 - PDF Sayfalama ve Thumbnail Gate
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** `backend/app/services/file_service.py`, `backend/requirements.txt`, `backend/tests/test_document_upload_integration.py`.
- **Test:** PDF fixture integration test.
- **Kanit:** evidence/environment_gate/backend_pytest_task013_pdf_initial.txt
- **Engel:** Yok.

### TASK-015 - Preprocessing Pipeline Sozlesmesi
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** `backend/app/services/document_processing/pipeline.py`, muhtemel testler.
- **Test:** Pipeline unit/integration test.
- **Kanit:** evidence/environment_gate/backend_pytest_task015_pipeline_initial.txt
- **Engel:** Yok.

### TASK-016 - Layout, Satir Tespiti ve RTL Sirasi
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** `backend/app/services/document_processing/layout.py`, `backend/tests/test_layout_analysis.py`.
- **Test:** Layout/RTL tests.
- **Kanit:** evidence/environment_gate/backend_pytest_task016_layout_initial.txt
- **Engel:** Yok.

### TASK-017 - OCR Adapter ve Model Dependency Gate
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** `backend/app/services/document_processing/ocr_engine.py`, `backend/tests/test_ocr_engine.py`.
- **Test:** OCR unit/smoke.
- **Kanit:** evidence/environment_gate/backend_pytest_task017_ocr_initial.txt
- **Engel:** Yok.

### TASK-018 - OCR Review ve Duzeltme Audit Akisi
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** DOÃ„Å¾RULANMADI.
- **Test:** Review/audit integration.
- **Kanit:** evidence/environment_gate/backend_pytest_task018_review_initial.txt
- **Engel:** Yok.

### TASK-019 - Transliterasyon Servisi
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** DOÃ„Å¾RULANMADI.
- **Test:** Transliteration unit/API tests.
- **Kanit:** evidence/environment_gate/backend_pytest_task019_transliteration_after_metrics.txt
- **Engel:** Yok.

### TASK-020 - Modernizasyon ve Ozetleme
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** DOÃ„Å¾RULANMADI.
- **Test:** Modernization/summary unit/API tests.
- **Kanit:** evidence/environment_gate/backend_pytest_task020_modernization_after_fix.txt
- **Engel:** Yok.

### TASK-021 - NER, Tarih Normalizasyonu ve Glossary
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** DOÃ„Å¾RULANMADI.
- **Test:** NER/date/glossary unit/API tests.
- **Kanit:** evidence/environment_gate/backend_pytest_task021_analysis_initial.txt
- **Engel:** Yok.

### TASK-022 - Confidence ve Model Registry
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** DOÃ„Å¾RULANMADI.
- **Test:** Metadata/confidence registry tests.
- **Kanit:** evidence/environment_gate/backend_pytest_task022_confidence_initial.txt
- **Engel:** Yok.

### TASK-023 - RAG Chat ve Citation Flow
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** DOÃ„Å¾RULANMADI.
- **Test:** RAG/citation integration tests.
- **Kanit:** Bakiniz Task_Queue ve ilgili test/kanit satirlari.
- **Engel:** Yok.

### TASK-024 - Export ve Raporlama
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** DOÃ„Å¾RULANMADI.
- **Test:** Export tests.
- **Kanit:** Bakiniz Task_Queue ve ilgili test/kanit satirlari.
- **Engel:** Yok.

### TASK-025 - Evaluation ve Deney Yonetimi
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** DOÃ„Å¾RULANMADI.
- **Test:** Evaluation smoke.
- **Kanit:** Bakiniz Task_Queue ve ilgili test/kanit satirlari.
- **Engel:** Yok.

### TASK-026 - Security Audit ve Secret Hygiene
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** `backend/.env` kullanici izni gerekir; digerleri DOÃ„Å¾RULANMADI.
- **Test:** Security/authz tests.
- **Kanit:** Bakiniz Task_Queue ve ilgili test/kanit satirlari.
- **Engel:** Yok.

### TASK-027 - Performance ve Reliability
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** DOÃ„Å¾RULANMADI.
- **Test:** Reliability tests.
- **Kanit:** Bakiniz Task_Queue ve ilgili test/kanit satirlari.
- **Engel:** Yok.

### TASK-028 - Integration, E2E ve Release Gate
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** `backend/tests/e2e/test_full_e2e_flow.py`
- **Test:** Full smoke/e2e/release checks.
- **Kanit:** Bakiniz Task_Queue ve ilgili test/kanit satirlari.
- **Engel:** Yok.

### TASK-029 - Production Launch (v1.0.0-RC1)
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** Task_Queue ilgili dosya kapsaminda.
- **Test:** Ilgili pytest/frontend/evidence komutlari.
- **Kanit:** Bakiniz Task_Queue ve ilgili test/kanit satirlari.
- **Engel:** Yok.

### TASK-030 - Post-Launch Hardening
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Task_Queue kabul kriterleri ve ilgili wiki sayfalarindaki gereksinimler.
- **Ilgili kod:** Task_Queue ilgili dosya kapsaminda.
- **Test:** Ilgili pytest/frontend/evidence komutlari.
- **Kanit:** Bakiniz Task_Queue ve ilgili test/kanit satirlari.
- **Engel:** Yok.

### GROUND_TRUTH_INFRASTRUCTURE_FINAL_GATE - Full Regression Repair and Verify
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** FAISS security tests PASS.; Active and clean backend full regression PASS.; Active and clean security audits PASS or findings reported.; Frontend lint/typecheck/build PASS.; Browser E2E PASS.; Model checksum tamper and offline OCR smoke verified.; Migration temp DB roundtrip verified.; Worker recovery verified.
- **Ilgili kod:** evidence/ground_truth_final_gate/*, docs/wiki/00_System/*, docs/wiki/10_Handoffs/Latest_Handoff.md; onarim gerekirse ilgili kaynak/test dosyalari.
- **Test:** Ekli kullanici talimatindaki tum gate komutlari.
- **Kanit:** evidence/ground_truth_final_gate/FINAL_GATE_REPORT.md
- **Engel:** Yok.

### GROUND_TRUTH_FINAL_GATE_SUPPLEMENTAL_VERIFICATION - Close Remaining Verification Gaps
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Active ve clean PyTorch ortam/provenance/hash kaydi var.; PyTorch tamamlayici advisory kontrolu yapildi.; pip-audit kapsam siniri aciklandi.; Git discovery ve status/diff check veya esdeger dosya denetimi tamamlandi.; Secret ve buyuk dosya incelemesi tamamlandi.; Degisiklik yapildiysa ilgili regresyon yeniden gecti.; Final supplemental report yazildi.
- **Ilgili kod:** `evidence/ground_truth_final_gate_supplement/*`, `docs/wiki/00_System/*`, `docs/wiki/10_Handoffs/Latest_Handoff.md`.
- **Test:** Ekli kullanici talimatindaki supplemental gate komutlari.
- **Kanit:** evidence/ground_truth_final_gate_supplement/; evidence/ground_truth_final_gate_supplement/*; evidence/ground_truth_final_gate_supplement/FINAL_SUPPLEMENTAL_REPORT.md
- **Engel:** Yok.

### TASK-034-Q2 - Original Ground Truth Dataset and Real OCR Quality Evaluation
- **Kaynak .md:** docs/wiki/00_System/Task_Queue.md
- **Durum:** `BLOCKED_EXTERNAL`
- **Kabul kriteri:** Veri yoksa hazirlik dosyalari olusturulur ve sonuc `BLOCKED_USER_DATA_REQUIRED` olur.; Metadata sablonu ve hazirlama rehberi vardir.; Validator image/transcription eslesmesi, UTF-8, metadata, hash, duplikasyon, resolution, optional split leakage ve line sidecar kontrollerini yapar.; Import/validation dry-run testi PASS olur.; Proje-kodu warning kaynaklari temizlenir; kalan third-party warning'ler siniflanir.; Frontend lint warning 0 olur.; Gercek veri yokken OCR kalite metrigi uydurulmaz.; Kullanici tarafindan saglanan pilot zip teknik olarak ingest edilir ve hash/provenance dogrulanir.
- **Ilgili kod:** `scripts/validate_ground_truth_dataset.py`, `backend/tests/test_ground_truth_dataset_validator.py`, `frontend/src/app/dashboard/annotation-studio/page.tsx`, `backend/app/api/routes/chat.py`, `backend/app/services/chat/embeddings.py`, `backend/app/services/file_service.py`, `backend/alembic.ini`, `evidence/ocr_quality_real/*`, `docs/wiki/00_System/*`, `docs/wiki/10_Handoffs/Latest_Handoff.md`.
- **Test:** - [x] `python scripts/validate_ground_truth_dataset.py --write-evidence` -> `BLOCKED_USER_DATA_REQUIRED`.
- **Kanit:** evidence/ocr_quality_real/; evidence/ocr_quality_real/*; evidence/ocr_quality_real/FINAL_OCR_QUALITY_REPORT.md
- **Engel:** Ozgun insan dogrulamali ground-truth verisi veya gorevde belirtilen dis kosul eksik.

### AUDIT-TEST-STRENGTH - Onceki test degisikliklerinin zayiflatma olmadigini bagimsiz denetle
- **Kaynak .md:** Aktif kullanici talimati
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Bes belirtilen test dosyasi okunur; browser E2E baslik kontroluyle sinirli kalmaz.
- **Ilgili kod:** backend/tests/test_file_security.py; backend/tests/test_ocr_engine.py; backend/tests/test_processing_pipeline.py; backend/tests/test_worker.py; backend/tests/e2e/test_ground_truth_browser.py
- **Test:** venv\Scripts\python.exe -m pytest ...; live browser E2E
- **Kanit:** evidence/independent_audit/focused_backend_regression.txt; evidence/ground_truth_final_gate/frontend_browser_e2e.txt
- **Engel:** Yok.

### AUDIT-MD-INVENTORY - Butun uygulanabilir Markdown gorevlerini tek envantere al
- **Kaynak .md:** Aktif kullanici talimati
- **Durum:** `VERIFIED`
- **Kabul kriteri:** Markdown listesi taranir; gorev dagilimi raporlanir.
- **Ilgili kod:** docs/wiki/00_System/Markdown_Task_Inventory.md
- **Test:** rg --files -g '*.md' ...
- **Kanit:** evidence/markdown_inventory/markdown_files_project_scoped.txt; docs/wiki/00_System/Markdown_Task_Inventory.md
- **Engel:** Yok.

### GATE-CLEAN-ENV-20260802 - Kisa yollu temiz sanal ortamda kurulum ve smoke dogrulama
- **Kaynak .md:** Aktif kullanici talimati
- **Durum:** `VERIFIED`
- **Kabul kriteri:** pip install, pip check, backend tests, migration, imports, backend/worker start, frontend build, smoke.
- **Ilgili kod:** backend/requirements.txt; backend/alembic; frontend/package.json
- **Test:** clean venv verification; pytest; frontend build; health/auth smoke
- **Kanit:** evidence/clean_env_20260802/clean_env_verification.txt; evidence/clean_env_20260802/clean_env_verification_rerun.txt
- **Engel:** Yok.

### GATE-GPU-CUDA-20260802 - RTX 4050 icin CUDA destekli PyTorch ve OCR CPU/GPU karsilastirmasi
- **Kaynak .md:** Aktif kullanici talimati
- **Durum:** `VERIFIED`
- **Kabul kriteri:** nvidia-smi, driver, torch CUDA availability, resmi PyTorch kurulumu, CPU/GPU OCR sure/bellek karsilastirmasi.
- **Ilgili kod:** backend/app/services/document_processing/ocr_engine.py
- **Test:** torch cuda smoke; OCR benchmark
- **Kanit:** evidence/gpu_cuda_20260802/nvidia_smi.txt; evidence/gpu_cuda_20260802/gpu_torch_install.txt; evidence/gpu_cuda_20260802/ocr_cpu_benchmark.json; evidence/gpu_cuda_20260802/ocr_gpu_benchmark.json
- **Engel:** Yok.

### GATE-OCR-QUALITY-GT-20260802 - Gercek ground-truth varsa CER/WER/line metrics uret; yoksa GT giris paketini hazirla
- **Kaynak .md:** Aktif kullanici talimati
- **Durum:** `BLOCKED_EXTERNAL`
- **Kabul kriteri:** Sahte GT uretilmez; mevcut DB ve annotation kayitlari aranir; GT yoksa adaylar ve manuel talimat hazirlanir.
- **Ilgili kod:** app/services/evaluation; ground truth API/UI; docs/wiki/08_Testing/GROUND_TRUTH_INPUT_REQUIRED.md
- **Test:** DB inspection; annotation candidate generation
- **Kanit:** evidence/ground_truth_input_20260802/db_ground_truth_summary.json; evidence/ground_truth_input_20260802/annotation_candidates.csv; evidence/ground_truth_input_20260802/OCR_QUALITY_GATE_RESULT.md
- **Engel:** Insan tarafindan dogrulanmis ozgun Osmanlica ground-truth satirlari eksik.

### SUPERSEDED-LEGACY-MD-PACKAGES - Eski/ikincil ajan, prompt ve wiki paketleri aktif kok AGENTS.md ve PROMPTS tarafindan superseded
- **Kaynak .md:** frontend\AGENTS.md; frontend\CLAUDE.md; OBSIDIAN_MIMARI_BEYIN_PAKETI\AGENTS.md; OBSIDIAN_MIMARI_BEYIN_PAKETI\docs\wiki\00_System\Architecture_Map.md; OBSIDIAN_MIMARI_BEYIN_PAKETI\docs\wiki\00_System\Change_Log.md; OBSIDIAN_MIMARI_BEYIN_PAKETI\docs\wiki\00_System\Current_State.md; OBSIDIAN_MIMARI_BEYIN_PAKETI\docs\wiki\00_System\Decisions.md; OBSIDIAN_MIMARI_BEYIN_PAKETI\docs\wiki\00_System\Execution_Lock.md; OBSIDIAN_MIMARI_BEYIN_PAKETI\docs\wiki\00_System\Ingest_Log.md; OBSIDIAN_MIMARI_BEYIN_PAKETI\docs\wiki\00_System\Lint_Report.md; OBSIDIAN_MIMARI_BEYIN_PAKETI\docs\wiki\00_System\Open_Questions.md; OBSIDIAN_MIMARI_BEYIN_PAKETI\docs\wiki\00_System\Risks.md; ...
- **Durum:** `SUPERSEDED`
- **Kabul kriteri:** Aktif baglayici kok AGENTS.md, docs/wiki ve PROMPTS kullanilir; eski paketler gorev kaynagi olarak uygulanmaz.
- **Ilgili kod:** Yok.
- **Test:** Markdown tarama ve Decisions.md baglayici karar kontrolu.
- **Kanit:** docs/wiki/00_System/Decisions.md; evidence/markdown_inventory/markdown_files_project_scoped.txt
- **Engel:** Yok.

## 2026-08-02 Live Evaluation Inventory Update
- `VERIFY-LIVE-EVAL-20260802`: VERIFIED/DONE.
- `TASK-034-Q2`: Human review blokaji kalkti; evaluation tamamlandi, OCR accuracy FAIL_NEEDS_MODEL_IMPROVEMENT.
- `TASK-034-Q3`: Human review/lock tamamlandi; dataset `2` LOCKED, 73/73 human verified.
- Kalan ana is: OCR model/pipeline iyilestirmesi ve SRS sayisal kalite esigi karari.
- Kanit: `evidence/verify_live_state_20260802/FINAL_VERIFY_LIVE_STATE_AND_EVALUATION_REPORT.md`.

## 2026-08-03 TASK-034-Q5 Inventory Update
- TASK-034-Q5 DONE: Q5 pilot OCR engineering kapilari PASS; production SLA degil.
- Ana kanit: evidence/line_segmentation_q5/FINAL_Q5_OCR_QUALITY_REPORT.md.

