---
type: index
status: verified
last_verified: 2026-08-13
owners: []
source_paths:
  - backend/app
  - frontend/src
  - backend/requirements.txt
  - frontend/package.json
tags: [bootstrap, recover, index, release-gate]
---

# Index

## 2026-08-21 Runtime Start
- [[Current_State]] - verified - Local runtime ONLINE; frontend/backend/worker ayakta, Kraken/CUDA/model hazir.
- [[Task_Queue]] - done - `TASK-20260821-RUNTIME-START` DONE / `LOCAL_RUNTIME_ONLINE`.
- [[Latest_Handoff]] - verified - Kullaniciya verilecek link `http://127.0.0.1:3000/login`.

## 2026-08-21 Performance Audit 1B
- [[Current_State]] - partial - 1B runtime profiling/optimization PARTIAL_SCOPED_PASS; real stage kanitlari ve synthetic bulk benchmark var, full real HTTP bulk acik.
- [[Task_Queue]] - review - `TASK-20260821-PERFORMANCE-AUDIT-1B` REVIEW / `PARTIAL_SCOPED_PASS_REAL_STAGE_AND_SYNTHETIC_BULK_BENCHMARK`.
- [[Source_Map]] - verified - LLM call reuse, RAG dead allocation cleanup, real OCR/LLM/RAG/DB/preprocessing benchmark kanitlari eklendi.
- [[Latest_Handoff]] - verified - Bir sonraki kesin adim live HTTP/browser 1/5/10 document benchmark.
- [[Unknown_Document_Analysis_Pipeline]] - partial - Document-level line reuse optimization testli; structured modern-line batching henuz acik risk.
- [[RAG_Chat_Service]] - verified - Dead mock engine allocation kaldirildi.

## 2026-08-20 Algorithm Audit 1A
- [[Current_State]] - verified - Performance optimizasyonu oncesi algoritmik/mantiksal audit PASS; kalan riskler dusuk/benchmark fazina tasindi.
- [[Task_Queue]] - done - `TASK-20260820-ALGORITHM-AUDIT-1A` DONE / `ALGORITHM_AUDIT_1A_PASS_WITH_REMAINING_LOW_RISKS`.
- [[Source_Map]] - verified - Fixlenen logger fallback, iterable pages, OCR-safe deskew ve frontend duplicate guard kanitlari eklendi.
- [[Latest_Handoff]] - verified - Bir sonraki kesin adim 1B real benchmark/profiling.
- [[Image_Preprocessing]] - verified - Deskew text-preservation guard gercekten skip edecek sekilde testlendi.
- [[Unknown_Document_Analysis_Pipeline]] - verified - LLM transliteration fallback ve iterable page input edge-case testlendi.

## 2026-08-20 Final Partial To Verified Pass Closure
- [[Current_State]] - verified - Kalan final closure kapilari gercek runtime kanitiyla kapandi; `final_closure_report.json` -> `VERIFIED_PASS`.
- [[Task_Queue]] - done - `Critical False Pass Correction Real Document Only` gorevi `DONE / VERIFIED_PASS_FINAL_CLOSURE`.
- [[Source_Map]] - verified - Real document identity, actual text outputs, 5-line traceability, human review E2E, screenshot/button/network kanitlari eklendi.
- [[Latest_Handoff]] - verified - Son durum failed gates `[]`, aktif blokaj yok.
- [[OCR_Service]] - verified - Final closure belgesi uzerinde OCR `12` actual line ve human correction E2E kanitlandi.

## 2026-08-20 Critical False Pass Correction
- [[Current_State]] - partial - Onceki `FINAL VERDICT: PASS` iptal edildi; corrected runtime audit `VERIFIED_PARTIAL` verdi.
- [[Task_Queue]] - partial - `Critical False Pass Correction Real Document Only` gorevi REVIEW durumunda; real human correction, 10 screenshot ve 25 button matrix kapilari acik.
- [[Source_Map]] - verified - Sentetik karantina, DB storage identity, corrected audit script ve final metrics kanitlari eklendi.
- [[Latest_Handoff]] - partial - Bir sonraki kesin adim corrected final audit gate eksiklerini tamamlamak.
- [[OCR_Service]] - partial - Real document OCR 12 line, confidence 0.8719; final acceptance PASS degil.

**Ozet:** Bu wiki, Intelligent Ottoman Turkish Assistant projesinin tek dogru Obsidian hafizasidir ve yalniz `docs/wiki/` altinda tutulur. 2026-08-02 canli dogrulamada dataset `2` `LOCKED`, 73/73 satir human-verified ve evaluation job `1` completed olarak kanitlandi. Genel durum `PARTIAL_ACCEPTANCE_INFRASTRUCTURE_PASS_OCR_QUALITY_FAIL`: teknik pipeline PASS, OCR accuracy FAIL_NEEDS_MODEL_IMPROVEMENT.

**Kutuphaneler:** FastAPI, SQLAlchemy, Pydantic, Next.js, React, TypeScript, OpenCV, Pillow, pdf2image, transformers, torch.

**Baglantilar:** [[Current_State]], [[Architecture_Map]], [[Source_Map]], [[Task_Queue]], [[Latest_Handoff]]

## 00_System
- [[Current_State]] - verified - Projenin gercek calisma ve uygulama durumu.
- [[Architecture_Map]] - verified - Backend, frontend, veri, dosya ve AI/ML katmanlari.
- [[Source_Map]] - verified - Teknik iddialarin dosya ve sembol kanitlari.
- [[Task_Queue]] - verified - Bagimlilik sirali gorev kuyrugu.
- [[Execution_Lock]] - verified - Aktif otonom gorev kilidi.
- [[Decisions]] - verified - Protokol kararlari ve proposed ADR baglantilari.
- [[Risks]] - verified - Guvenlik, dogruluk ve operasyon riskleri.
- [[Open_Questions]] - verified - Belirsiz kalan karar ve gereksinimler.
- [[Ingest_Log]] - verified - BOOTSTRAP/INGEST/RECOVER kaydi.
- [[Change_Log]] - verified - Wiki degisiklik ozeti.
- [[Lint_Report]] - verified - Wiki saglik ve RECOVER/TASK-008 LINT notlari.

## 01_Architecture
- [[FastAPI_API]] - verified - Backend API giris noktasi ve router yapisi.
- [[Deployment_Architecture]] - partial - Yerel dev calisma yapisi belgeli; production DOÄžRULANMADI.

## 02_Modules
- [[Audit_Log]] - verified - Auth, document ve preprocessing olay kayitlari.
- [[Confidence_Management]] - partial - Merkezi confidence policy servis ve operation metadata tests var; UI entegrasyonu yok.
- [[Date_Normalization]] - partial - Rule-based Hicri/Rumi/Miladi yil normalizasyonu testli; tam takvim donusumu yok.
- [[Document_Ingestion]] - verified - Belge yukleme, dosya kaydetme, sayfa/thumbnail ve audit kaydi.
- [[Export_Service]] - verified - TXT, JSON ve CSV export servis/route/test kanitlari var.
- [[File_Validation]] - verified - Uzanti, MIME, magic bytes, boyut ve path traversal dosya adi kontrolleri.
- [[Glossary_Service]] - partial - Local glossary fallback ve metadata testli; merkezi CRUD yok.
- [[Image_Preprocessing]] - partial - Varyant API ve pipeline smoke PASS; layout/OCR tam hatti eksik.
- [[Layout_Analysis]] - verified - Line region detection ve coordinate fixture testli.
- [[PDF_Page_Splitting]] - verified - PDFium fallback ile PDF sayfalama, sayfa sirasi ve thumbnail testli.
- [[Planned_Features]] - planned - Kod kaniti olmayan baslangic dugumlerini toplar.
- [[Processing_Job_State_Machine]] - documented - Model var; API is akisi ile entegrasyon DOÄžRULANMADI.
- [[RTL_Reading_Order]] - verified - Sagdan sola sutun/satir sirasi fixture testli.
- [[Security_Model]] - verified - JWT, bcrypt/passlib, rol ve belge izolasyonu testleri.

## 03_Data
- [[Database_Model]] - verified - SQLAlchemy modelleri, Alembic migration ve rollback gate.

## 04_Flows
- [[Unknown_Document_Analysis_Pipeline]] - verified - Uploaded unknown Ottoman document full backend analysis flow with separated evidence, verified historical RAG and provisional confidence.

## 05_UI
- [[Document_Workspace]] - verified - Login, dashboard, upload ve belge detay Next.js ekranlari.
- [[OCR_Review_Flow]] - partial - Backend review/correction/audit API testli; frontend workspace henuz yok.
- [[Streamlit_UI]] - planned - Kodda Streamlit bulunamadi.

## 06_AI_ML
- [[Model_Registry]] - partial - ModelRegistryEntry ve idempotent registry service testli; admin API yok.
- [[Modernization_Service]] - partial - Faithful/plain/summary backend fallback API testli; gercek LLM/model entegrasyonu yok.
- [[NER_Service]] - partial - Rule-based NER/date/glossary API ve evaluation smoke testli; gercek model yok.
- [[OCR_Service]] - partial - TrOCR adapter metadata/fallback testli; gercek model/API entegrasyonu eksik.
- [[RAG_Chat_Service]] - verified - Chat router ve testli RAGService mevcut; gercek LLM/vector entegrasyonu sinirli.
- [[Transliteration_Service]] - partial - Source-mapped rule-based transliteration API, correction history ve fixture metrics testli; gercek model/sozluk yok.

## 07_API_Integrations
- [[Citation_Flow]] - planned - Citation/RAG kaynak gosterme akisi kodda bulunamadi.

## 08_Testing
- [[Evaluation_Service]] - partial - Jiwer tabanli CER/WER servisi ve test dosyalari mevcut; human-verified OCR kalite gate'i bloklu.
- [[Test_Strategy]] - partial - Backend smoke/migration/auth/file tests ve frontend lint/build/audit kanitlari var; upload/preprocessing/e2e eksik.
- [[Requirements_Traceability_Matrix]] - verified - SRS/wiki/kod gereksinim matrisi; 165 SRS gereksinimi izlendi.
- [[Acceptance_Criteria_Map]] - verified - Release blocker ve MVP kabul kriterleri haritasi.

## 09_Decisions
- [[ADR-001_NextJS_Frontend]] - proposed - Streamlit/Next.js teknoloji-fonksiyon ayrimi.
- [[ADR-002_Windows_Native_Dev_Gate]] - accepted - Windows-native environment/test gate karari.

## 10_Handoffs
- [[Latest_Handoff]] - verified - Son RECOVER devir notu.

## 11_Sources
- Ayrintili kaynak sayfasi yok; kaynak eslemeleri [[Source_Map]] icindedir.

## 12_Operations
- Ayrintili operasyon sayfasi yok; operasyon riskleri [[Risks]] icindedir.

## 99_Templates
- [[Node_Template]] - verified - Modul/mimari wiki sayfasi sablonu.
- [[Task_Template]] - verified - Gorev kaydi sablonu.
- [[Decision_Template]] - verified - ADR kaydi sablonu.
- [[Handoff_Template]] - verified - Oturum devir notu sablonu
## Recent Verification Nodes
- [[Current_State]] - Live verification confirms dataset `2` is `LOCKED` with `73/73` human-verified lines; OCR evaluation job `1` is `completed`, while OCR quality remains below acceptance needs.
- [[Task_Queue]] - TASK-034-Q2 contains the original ground truth dataset/evaluation gate and remaining data dependency.
- [[Source_Map]] - TASK-034-Q2 evidence paths include validator, tests, warning audit, and final OCR quality report.
- [[Latest_Handoff]] - Latest handoff lists the next exact step: add permitted real page/transcription pairs and rerun validator/evaluation.

- [[Markdown_Task_Inventory]] - Project-scoped Markdown task inventory and terminal status distribution.

- [[GROUND_TRUTH_INPUT_REQUIRED]] - Manual human transcription input required for final OCR quality metrics.


## 2026-08-02 Bootstrap Refresh
- [[Current_State]] - verified - Zorunlu baslangic dosyalari tekrar okundu; aktif kod gorevi yok, ana blokaj human review.
- [[Architecture_Map]] - partial - Eski bootstrap iddialari worker/chat/export/evaluation varligi ile hizalanacak sekilde guncellendi.
- [[Source_Map]] - verified - Router, worker, test ve template kanitlari eklendi.


## 2026-08-02 Live Evaluation Completion
- [[Current_State]] - verified - Dataset `2` LOCKED, 73/73 human verified, job `1` completed.
- [[Evaluation_Service]] - verified/partial - Gercek metrikler uretildi; OCR accuracy fail.
- [[SRS_Gap_Register]] - verified - Sayisal kalite esigi eksigi kaydedildi.
- [[Latest_Handoff]] - verified - Sonraki kesin adim OCR model/pipeline iyilestirmesi.

## 2026-08-03 TASK-034-Q5 Line Segmentation
- [[Current_State]] - verified - Q5 line segmentation sonucu `Q5_PARTIAL_FURTHER_IMPROVEMENT_REQUIRED`; GT hash unchanged.
- [[Task_Queue]] - verified - TASK-034-Q5 DONE, sonraki kesin adim hybrid recognition reconstruction.
- [[Source_Map]] - verified - Q5 helper/test/script/evidence ve overlay kanitlari eklendi.
- [[Latest_Handoff]] - verified - Q5 metrikleri, testleri ve sonraki gorev kaydedildi.

## 2026-08-03 TASK-034-Q6 Hybrid Recognition
- [[Current_State]] - verified - Q6 sonucu `Q6_PARTIAL_WORD_BOUNDARY_IMPROVEMENT_REQUIRED`; CER hedefi gecti, WER hedefi kaldi.
- [[Task_Queue]] - verified - TASK-034-Q6 DONE, sonraki kesin adim word-boundary Q7.
- [[Source_Map]] - verified - Q6 helper/test/script/evidence ve overlay kanitlari eklendi.
- [[Latest_Handoff]] - verified - Q6 metrikleri, testleri ve sonraki gorev kaydedildi.



## 2026-08-03 Q5 OCR Pilot Pass
- [[Evaluation_Service]] - Q5 ecognition_beam_merged pilot kapilari gecti: strict CER .1264949402023919, strict WER .5493975903614458, line F1 .9615384615384615, reading-order 1.0.
- [[Task_Queue]] - TASK-034-Q5 DONE; production SLA degil, veri siniri kayitli.


## 2026-08-09 TASK-008 Reference UI
- [[Document_Workspace]] - partial - Reference UI dilimi `(app)` shell/dashboard/upload/settings/document workspace ile build ve lint PASS; backend E2E ve screenshot kaniti eksik.
- [[Current_State]] - partial - UI_FUNCTIONAL_REPAIR_REQUIRED durumu ve blokajlar kaydedildi.
- [[Task_Queue]] - partial - TASK-008 icin backend/browser dogrulama eksigi BLOCKED notu eklendi.
- [[Source_Map]] - verified - UI stack, route repair, OCR line/bbox binding ve test kanitlari eklendi.

## 2026-08-09 TASK-008 Reference UI Completion Pass
- [[Document_Workspace]] - partial - Document workspace uc kolonlu referans duzene cevrildi; backend E2E ve authenticated screenshot kaniti eksik.
- [[Current_State]] - partial - UI_CODE_READY_BACKEND_E2E_PENDING durumu kaydedildi.
- [[Source_Map]] - verified - Reference layout source ve authenticated screenshot blokaji kanitlari eklendi.

## 2026-08-09 TASK-008 Complete UI E2E
- [[Document_Workspace]] - verified - Reference UI real backend/auth/upload/Kraken OCR/browser screenshot akisiyle PASS.
- [[Current_State]] - verified - `REFERENCE_UI_IMPLEMENTATION_PASS` kaydedildi.
- [[Source_Map]] - verified - Backend health, auth/upload/OCR, Kraken metadata ve screenshot kanitlari eklendi.

## 2026-08-09 Premium Auth UI
- [[Auth_UI]] - verified - Premium dark/gold login ve register ekranlari, gercek auth API entegrasyonu, lint/build/route/screenshot kanitlariyla PASS.
- [[Current_State]] - verified - `AUTH_UI_IMPLEMENTATION_PASS` kaydedildi.
- [[Source_Map]] - verified - Auth UI kaynaklari ve evidence yolları eklendi.

## 2026-08-09 Windows Runtime Launcher
- [[Windows_Runtime_Launcher]] - verified - START/STOP/RESTART/STATUS/HEALTH Windows launcher sistemi, PID guvenligi, WSL/Kraken/model check ve real auth/upload/OCR smoke ile PASS.
- [[Current_State]] - verified - `WINDOWS_ONE_CLICK_RUNTIME_PASS` kaydedildi.
- [[Source_Map]] - verified - Runtime launcher evidence yollari eklendi.

## 2026-08-09 Downstream Text Repair
- [[OCR_Service]] - verified - Kraken OCR sonrasi transliteration/modernization payload ayrimi ve kalite kontrolleri `DOWNSTREAM_TEXT_REPAIR_PASS` ile kaydedildi.
- [[Document_Workspace]] - verified - OCR/Latin/modern/summary alanlari ayri UI panellerinde dogrulandi.
- [[Source_Map]] - verified - Downstream text repair evidence yollari eklendi.

## 2026-08-09 Line Filter Repair
- [[Layout_Analysis]] - verified - OCR line-filter-v1 header/footer/dekoratif/garbage adaylari backend katmaninda filtreler.
- [[OCR_Service]] - verified - Gercek Kraken run 25 -> 23 temiz line, `actual_engine=kraken`, `fallback_used=false`.
- [[Document_Workspace]] - verified - Overlay sadece selected-page gercek bbox line payload'ini kullanir; multi-page page_id sozlesmesi kaydedildi.
- [[Current_State]] - verified - `LINE_FILTER_REPAIR_PASS` kaydedildi.
- [[Source_Map]] - verified - Before/after overlay, line JSON ve test kanitlari eklendi.

## 2026-08-09 Final Text and Segmentation Check
- [[OCR_Service]] - verified - Final integrated payload `TEXT_AND_SEGMENTATION_FINAL_PASS`: 23 line, 23 bbox, blank/low-usefulness line 0, Kraken fallback yok.
- [[Document_Workspace]] - verified - API-style `pipeline_results` mapping OCR/Latin/modern/summary/NER/bbox alanlariyla dogrulandi.
- [[Current_State]] - verified - Final text and segmentation acceptance kaydedildi.
- [[Source_Map]] - verified - Final API payload, runtime metadata, UI check ve report evidence yollari eklendi.

## 2026-08-09 Auth Reference Match
- [[Auth_UI]] - verified - Login/register ekranlari kullanici referanslarindaki koyu/altin centered premium sahneye yaklastirildi.
- [[Current_State]] - verified - `AUTH_REFERENCE_MATCH_PASS` kaydedildi.
- [[Source_Map]] - verified - Auth reference screenshots, lint/build ve route kanitlari eklendi.

## 2026-08-13 Unknown Document Pipeline
- [[Unknown_Document_Analysis_Pipeline]] - verified - `POST /api/v1/document/analyze-full` real upload + real OCR/Ollama/Qdrant backend flow PASS.
- [[Current_State]] - verified - `UNKNOWN_DOCUMENT_PIPELINE_GATE: PASS` kaydedildi.
- [[Source_Map]] - verified - Pipeline, route, schema, tests, Ollama and Qdrant evidence eklendi.

## 2026-08-13 Kraken Default Live HTTP Gate
- [[Unknown_Document_Analysis_Pipeline]] - verified - Real Uvicorn multipart HTTP gate with default Kraken OCR PASS.
- [[Current_State]] - verified - `KRAKEN_DEFAULT_LIVE_HTTP_GATE: PASS` kaydedildi.
- [[Source_Map]] - verified - Kraken runtime, HTTP response, evidence safety and regression artifacts linked.

## 2026-08-13 Non-ASCII Image Path Hardening
- [[Unknown_Document_Analysis_Pipeline]] - verified - Non-ASCII Windows upload path now works through Unicode-safe OpenCV image IO.
- [[Image_Preprocessing]] - verified - Preprocessing image read/write path calls are centralized through Unicode-safe utility.
- [[OCR_Service]] - verified - Kraken live HTTP gate still returns `ocr.engine=kraken` and no fallback.
- [[Current_State]] - verified - `NON_ASCII_IMAGE_PATH_GATE: PASS` kaydedildi.
- [[Source_Map]] - verified - Audit, utility, tests, live HTTP and regression evidence linked.

## 2026-08-13 Production Main Dashboard Integration
- [[Document_Workspace]] - verified - Main dashboard is now the production full-analysis workspace backed by real `POST /api/v1/document/analyze-full`.
- [[Unknown_Document_Analysis_Pipeline]] - verified - Frontend integration uses the live full-analysis endpoint and renders separated evidence.
- [[OCR_Service]] - verified - Dashboard E2E response rendered `ocr.engine=kraken` with no fallback.
- [[Current_State]] - verified - `MAIN_DASHBOARD_INTEGRATION_GATE: PASS` kaydedildi.
- [[Source_Map]] - verified - Frontend source, HTTP response, DOM checks, screenshot, lint and build evidence linked.

## 2026-08-13 Image Processing Lab
- [[Document_Workspace]] - verified - Dedicated `/image-processing-lab` OCR-safe preprocessing lab route PASS.
- [[Image_Preprocessing]] - verified - Current implemented/partial/missing preprocessing stages audited and evidence-linked.
- [[OCR_Service]] - verified - OCR-safe final is marked while visual restoration is not generated or used for OCR input.
- [[Current_State]] - verified - `IMAGE_PROCESSING_LAB_GATE: PASS` kaydedildi.
- [[Source_Map]] - verified - Lab source, preprocessing API, E2E, screenshot and test evidence linked.

## 2026-08-13 Production Image Processing Lab UI
- [[Document_Workspace]] - verified - `/image-processing` production lab UI reference direction, real preprocessing integration and browser E2E PASS.
- [[Image_Preprocessing]] - verified - Stage inventory records available final artifact and unavailable non-fabricated intermediate stages.
- [[Current_State]] - verified - `IMAGE_PROCESSING_LAB_GATE: PASS` latest UI hardening kaydedildi.
- [[Source_Map]] - verified - DOM verification, screenshots, lint/build/backend regression evidence linked.

## 2026-08-13 Historical Analysis RAG Dashboard
- [[Document_Workspace]] - verified - `/historical-analysis` production Tarihsel Analiz route, sidebar active state and browser E2E PASS.
- [[Unknown_Document_Analysis_Pipeline]] - verified - Screen consumes real `POST /api/v1/document/analyze-full` response and preserves evidence separation.
- [[RAG_Chat_Service]] - verified - Verified external historical evidence provenance is rendered without promoting unverified relation candidates.
- [[Current_State]] - verified - `HISTORICAL_ANALYSIS_DASHBOARD_GATE: PASS` kaydedildi.
- [[Source_Map]] - verified - API snapshot, source audit, DOM verification, lint/build and screenshot evidence linked.

## 2026-08-13 Final Product Integration Gate
- [[Document_Workspace]] - verified - Main Dashboard, Image Lab and Historical Analysis share one active document context and pass real browser demo flow.
- [[Image_Preprocessing]] - verified - Image Lab same-document auto-load renders original and OCR-safe final without re-upload.
- [[Unknown_Document_Analysis_Pipeline]] - verified - Browser gate uses real `POST /api/v1/document/analyze-full`, HTTP 200, Kraken/no fallback.
- [[RAG_Chat_Service]] - verified - Historical Analysis reuses separated document/external/model/uncertainty evidence from the real response.
- [[Current_State]] - verified - `FINAL_PRODUCT_INTEGRATION_GATE: PASS` kaydedildi.
- [[Source_Map]] - verified - Final E2E, negative/security, screenshots, frontend/backend regression evidence linked.

## 2026-08-13 Final Professor Demo and Release Gate
- [[Document_Workspace]] - partial - Final professor demo browser flow passes functionally but production hydration page errors remain.
- [[OCR_Service]] - verified - Browser release demo confirms `ocr.engine=kraken` and `fallback_used=false`.
- [[RAG_Chat_Service]] - verified - Release demo returns 5 verified historical external evidence items.
- [[Current_State]] - partial - `FINAL_RELEASE_GATE: PARTIAL` kaydedildi.
- [[Source_Map]] - verified - Preflight, startup, tests, browser E2E, config/security/performance and screenshot evidence linked.

## 2026-08-14 Dashboard Embedded Image Processing Lab
- [[Document_Workspace]] - verified - Main dashboard preserves the three primary panels and embeds `Goruntu Isleme Laboratuvari` between the result grid and Latin section.
- [[Image_Preprocessing]] - verified - UI shows the OCR preparation flow without changing backend preprocessing/OCR code.
- [[Current_State]] - verified - `DASHBOARD_IMAGE_LAB_EMBED_PASS` kaydedildi.
- [[Source_Map]] - verified - Dashboard/sidebar/CSS/browser DOM/lint/build evidence linked.

## 2026-08-20 GitHub Source Publish Refresh
- [[Current_State]] - verified - GitHub `main` branch `fabe5e07f0bc8cf0015c183f438ff60a1454782a` commit'ine guncel temiz kaynak paketi push edildi.
- [[Task_Queue]] - verified - `GITHUB_SOURCE_REFRESH_PUSH_PASS` yayin notu DONE olarak kaydedildi.
- [[Source_Map]] - verified - `PROJECT_OVERVIEW.md`, `.gitignore`, publish content gate ve remote push kanitlari eklendi.
- [[Latest_Handoff]] - verified - Bir sonraki ajan icin yayin kapsami ve haric tutulacak alanlar kaydedildi.

## 2026-08-20 Real Document Recovery Revalidation
- [[Current_State]] - partial - `silah-atmama-ilani_ahmed-vefik-pasa.jpg` gercek belge OCR/preprocessing/downstream/RAG revalidation `VERIFIED_PARTIAL` olarak kaydedildi.
- [[Task_Queue]] - partial - `RECOVERY_REAL_DOCUMENT_REVALIDATION_AND_OCR_REPAIR` review durumunda; dedicated claim UI eksigi kaldi.
- [[Source_Map]] - verified - Real API/browser/preprocessing A-B/test kanitlari `evidence/recovery_real_document_revalidation/` altina eklendi.
- [[Latest_Handoff]] - partial - Runtime link, degisen dosyalar, testler ve kalan riskler guncellendi.
