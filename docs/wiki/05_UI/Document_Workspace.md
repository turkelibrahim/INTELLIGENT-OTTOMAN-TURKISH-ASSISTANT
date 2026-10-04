---
type: module
status: verified
last_verified: 2026-08-13
owners: []
source_paths:
  - frontend/src/app/page.tsx
  - frontend/src/app/login/page.tsx
  - frontend/src/app/dashboard/page.tsx
  - frontend/src/app/upload/page.tsx
  - frontend/src/app/documents/[id]/page.tsx
  - frontend/src/lib/api.ts
test_paths:
  - scripts/doctor.ps1
tags: [ui, frontend]
---

# Document Workspace

**Ozet:** Next.js App Router UI login/register, dashboard, upload ve belge detay/on isleme/OCR/sohbet ekranlarini icerir. API istemcisi auth, documents, pages, preprocessing, OCR ve chat endpointlerini sarar. Belge detay ekraninda yetki gerektiren gorseller tokenli blob URL ile render edilir.

**Kutuphaneler:** Next.js, React, TypeScript.

**Baglantilar:** [[FastAPI_API]], [[Document_Ingestion]], [[Image_Preprocessing]], [[OCR_Service]], [[Security_Model]], [[Current_State]]

## Sorumluluklar
- Kullanici oturumu, belge listesi, belge yukleme, sayfa goruntuleme, preprocessing kontrolu, OCR sonuc gorunumu ve belge sohbeti.

## Girdiler
- Kullanici form verisi, dosya secimi, token, belge/sayfa secimi, preprocessing profili, OCR/sohbet komutlari.

## Ciktilar
- API istekleri, route yonlendirmeleri, UI state, tokenli blob gorsel URL'leri.

## Bagimliliklar
- `frontend/src/lib/api.ts`, browser localStorage, backend `/api/v1` endpointleri.

## Veri Akisi
- UI -> `frontend/src/lib/api.ts` -> backend JSON endpointleri.
- Yetki isteyen image/file endpointleri -> `fetchAuthenticatedBlobUrl` -> Bearer tokenli fetch -> browser object URL -> `AuthenticatedImage`.
- OCR tamamlaninca `Sonuclari Incele` -> `compareMode="ocr"` -> orta panelde OCR/metin/NER gorunumu.

## Hata Durumlari
- Genel baglanti hatasi mesaji API 500 detayini gizleyebilir.
- Gorsel blob yukleme hatasinda kullaniciya goruntulenebilir fallback metni gosterilir.

## Guvenlik ve Gizlilik
- Access token localStorage'da tutulur.
- Page image, thumbnail ve preprocessing variant endpointleri backend tarafinda auth gerektirir; frontend bunlari ham `<img src>` yerine tokenli fetch ile indirir.

## Testler ve Kabul Kriterleri
- `npm.cmd run lint` PASS, 2026-08-02.
- `npm.cmd run build` PASS, 2026-08-02.
- `powershell -ExecutionPolicy Bypass -File scripts/doctor.ps1` PASS, 2026-08-02, `DOCTOR_FAILED=0`.
- Backend doctor icinde `python -m pytest tests -q` PASS, 70 passed.

## Kod Kanitlari
- `frontend/src/app/login/page.tsx` -> `LoginPage`
- `frontend/src/app/upload/page.tsx` -> `UploadPage`
- `frontend/src/app/documents/[id]/page.tsx` -> `DocumentDetailPage`, `AuthenticatedImage`
- `frontend/src/lib/api.ts` -> `fetchAuthenticatedBlobUrl`, `ocrApi`, `pagesApi`, `preprocessingApi`

## Bilinen Eksikler
- Frontend E2E browser automation test dosyasi bulunamadi; lint/build ve doctor ile dogrulandi.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
- 2026-08-02: Yetki gerektiren belge gorselleri tokenli blob yukleme ile duzeltildi; OCR sonuc inceleme butonu placeholder alert yerine gercek sonuc gorunumune baglandi.

## 2026-08-09 Reference UI Update
- **Durum:** partial.
- **Ozet:** Reference UI dilimi Next.js `(app)` route group uzerinde koyu/altin app shell, dashboard, upload, settings ve document workspace ekranlarini aktif hale getirdi.
- **Kod Kanitlari:**
  - `frontend/src/app/(app)/layout.tsx` -> `AppLayout`, `NavSection`
  - `frontend/src/app/(app)/dashboard/page.tsx` -> `DashboardPage`
  - `frontend/src/app/(app)/upload/page.tsx` -> `UploadPage`
  - `frontend/src/app/(app)/settings/page.tsx` -> `SettingsPage`
  - `frontend/src/app/(app)/documents/[id]/page.tsx` -> `DocumentDetailPage`, `AuthImage`, `getLineBox`
  - `frontend/src/lib/api.ts` -> `OCRPipelineLine`, `OCRJobStatusResponse`
- **Veri Baglantilari:** OCR metni `pipeline_results.original_ocr_text`, Latin transkripsiyon `pipeline_results.transliterated_text`, gunumuz Turkcesi `pipeline_results.modernized_text`, ozet yalniz `pipeline_results.summary_text`, bbox overlay `pipeline_results.lines[].bbox`, line confidence `pipeline_results.lines[].confidence`.
- **Test Kanitlari:** `npm.cmd run lint` PASS; `npm.cmd run build` PASS; local route smoke `/login`, `/dashboard`, `/upload`, `/settings`, `/documents/1` HTTP 200.
- **Eksikler:** Backend `localhost:8000` timeout oldugu icin gercek login/upload/OCR/Kraken UI E2E kosulmadi. Browser/screenshot otomasyonu mevcut olmadigi icin gorsel karsilastirma screenshot kaniti uretilmedi.
- **Evidence:** `evidence/ui_reference_implementation/UI_IMPLEMENTATION_REPORT.md`.

## 2026-08-09 Reference Layout Completion Pass
- **Durum:** partial / authenticated E2E pending.
- **Ozet:** Document workspace sekmeli sonuc yuzeyinden, referans gorseldeki gibi ayni anda gorunen uc kolonlu belge analizi arayuzune cevrildi.
- **UI Kaniti:** `frontend/src/app/(app)/documents/[id]/page.tsx` -> `DocumentDetailPage`; `frontend/src/app/globals.css` -> `.doc-analysis-page`, `.analysis-grid`, `.viewer-card`, `.ocr-results-card`, `.analysis-side-stack`, `.confidence-widget`.
- **Veri Kurali:** Uretim bileseni sahte OCR/summary/bbox uretmez; bbox yalniz `pipeline_results.lines[].bbox`, ozet yalniz `pipeline_results.summary_text`, transkripsiyon yalniz `pipeline_results.transliterated_text`, modern Turkce yalniz `pipeline_results.modernized_text` alanlarindan beslenir.
- **Test Kanitlari:** 2026-08-09 `npm.cmd run lint` PASS; 2026-08-09 `npm.cmd run build` PASS; `/documents/1` HTTP 200.
- **Gorsel Kanit:** `evidence/ui_reference_implementation/screenshots/document-workspace-route.png` olusturuldu, ancak auth token olmadigi icin login ekrani yakalandi; authenticated workspace gorsel karsilastirmasi bekliyor.

## 2026-08-09 Complete UI E2E and Visual Acceptance
- **Durum:** verified.
- **Ozet:** TASK-008 backend, frontend, auth, upload, Kraken OCR, document workspace ve screenshot dogrulamasi ile `REFERENCE_UI_IMPLEMENTATION_PASS` durumuna getirildi.
- **Kod Kaniti:** `frontend/src/app/(app)/documents/[id]/page.tsx` mevcut completed OCR sonucunu belge status'una bagli kalmadan yukler; NER payload object/list sekillerini normalize eder; `frontend/src/app/globals.css` `ocr-results-table` stillerini kullanir.
- **Runtime Kaniti:** `evidence/ui_reference_implementation/e2e_result.json` -> document 7 / job 12 `COMPLETED`.
- **Kraken Kaniti:** `evidence/ui_reference_implementation/kraken_ui_metadata.json` -> `actual_engine=kraken`, `fallback_used=false`, SHA `f5abbba1976e9782ddf5d7185d911722c74558e12b57a12566c96e22a3e3b963`.
- **UI Kaniti:** `evidence/ui_reference_implementation/visual_automation_result.json` -> 25 OCR table rows, 25 bbox boxes, document image, transcription, modern Turkish, NER.
- **Screenshot Kaniti:** `evidence/ui_reference_implementation/screenshots/login.png`, `dashboard.png`, `upload.png`, `document_workspace.png`.

## 2026-08-09 Downstream Text Repair UI Contract
- **Durum:** verified.
- **Ozet:** Belge workspace OCR, Latin transkripsiyon, gunumuz Turkcesi ve ozet panellerini ayri backend alanlarindan besler; sahte bbox veya panel kopyasi uretmez.
- **Veri Kurali:** OCR paneli `pipeline_results.original_ocr_text` ve `pipeline_results.lines[].text`; Latin paneli yalniz `pipeline_results.transliterated_text`; gunumuz Turkcesi paneli yalniz `pipeline_results.modernized_text`; ozet paneli yalniz `pipeline_results.summary_text`; NER paneli `pipeline_results.ner_results`; bbox overlay yalniz gercek `pipeline_results.lines[].bbox`.
- **API Kaniti:** `backend/app/api/routes/ocr.py` `summary_text` ve `transformation_quality` alanlarini `pipeline_results` icine tasir.
- **Runtime Kaniti:** `evidence/downstream_text_repair/ui_render_check.txt` -> Latin OCR'den farkli, modern Latin'den farkli, bbox var, 25 OCR line.
- **Test Kaniti:** 2026-08-09 `npm.cmd run lint` PASS; `npm.cmd run build` PASS.

## 2026-08-09 Line Filter Repair UI Contract
- **Durum:** verified.
- **Ozet:** OCR overlay artik backend filtreli `pipeline_results.lines[].bbox` verisini kullanir ve page-scoped line payload ile secili sayfa disina bbox tasmasini engeller.
- **Backend Kaniti:** `backend/app/services/document_processing/pipeline.py` her line icin `page_id` tasir; `backend/worker.py` ilk islenen sayfanin gercek `Page.id` degerini pipeline'a iletir.
- **Frontend Kaniti:** `frontend/src/lib/api.ts` `OCRPipelineLine.page_id`; `frontend/src/app/(app)/documents/[id]/page.tsx` secili sayfa ile eslesen line'lari render eder, legacy unscoped multi-page payloadlarda page 1 disinda bbox gostermez.
- **Overlay Kaniti:** `evidence/line_filter_repair/after_overlay.png` -> header/footer/dekoratif line yok, ana Osmanlica satir bbox'lari gosteriliyor.
- **Test Kaniti:** 2026-08-09 `npm.cmd run lint` PASS; `npm.cmd run build` PASS.

## 2026-08-13 Production Main Dashboard Integration
- **Durum:** verified.
- **Ozet:** Ana dashboard artik real production full document analysis workspace olarak calisir; upload edilen belge `POST /api/v1/document/analyze-full` endpointine gider ve ayni ekranda image viewer, OCR, transliteration, modern Turkish, metadata, entities, historical analysis, confidence, uncertainty ve evidence kartlari render edilir.
- **Kod Kaniti:** `frontend/src/lib/api.ts` -> `analysisApi.analyzeFull`; `frontend/src/app/(app)/dashboard/page.tsx` -> `DashboardPage`, `handleAnalyze`, `EvidenceColumn`; `frontend/src/app/globals.css` -> `.production-dashboard`, `.pd-main-grid`, `.pd-evidence-grid`.
- **Veri Kurali:** Dashboard mock analysis uretmez; raw JSON gostermez; internal `ocr_safe_image` path'ini UI'da yayinlamaz; response alanlari yoksa `Tespit edilemedi`/empty-state kullanir.
- **Runtime Kaniti:** `evidence/main_dashboard_gate/api_response_snapshot.json` -> HTTP 200 response, `ocr.engine=kraken`, `ocr.fallback_used=false`, OCR line count 23.
- **UI Kaniti:** `evidence/main_dashboard_gate/api_request_evidence.json` -> 22 PASS checks; DOM `panels=3`, `documentEvidenceCards=22`, `externalEvidenceCards=5`, `hasImagePreview=true`.
- **Screenshot Kaniti:** `evidence/main_dashboard_gate/dashboard_screenshot.png`.
- **Test Kaniti:** 2026-08-13 `npm.cmd run lint` PASS, 0 errors / 11 existing warnings; `npm.cmd run build` PASS.

## 2026-08-13 Image Processing Lab
- **Durum:** verified.
- **Ozet:** `/image-processing-lab` dedicated OCR-safe preprocessing lab ekranidir; main dashboard'u kopyalamaz ve mevcut preprocessing API'lerine baglanir.
- **UI Kaniti:** Sol original viewer, merkez selected-stage viewer, sag metadata/safety panel, stage timeline, before/after slider, visual restoration placeholder.
- **Kod Kaniti:** `frontend/src/app/(app)/image-processing-lab/page.tsx`; `frontend/src/app/globals.css`; `frontend/src/components/dashboard/Sidebar.tsx`; `frontend/src/lib/api.ts`.
- **Veri Kurali:** Yalniz real original page image ve real backend ImageVariant OCR-safe final gosterilir; orientation/perspective/stain/mask gibi uretilmeyen asamalar fake preview olmadan unavailable state alir.
- **Runtime Kaniti:** `evidence/image_processing_lab_gate/api_request_evidence.json` -> real document upload, page image fetch, preprocessing POST, variant image fetch and 12 DOM checks PASS.
- **Test Kaniti:** Frontend lint/build PASS; backend targeted preprocessing tests 18 passed.

## 2026-08-13 Production Image Processing Lab UI
- **Durum:** verified.
- **Ozet:** `/image-processing` route'u kullanici referans gorsellerindeki koyu/altin production lab kompozisyonuna yaklastirildi; `/image-processing-lab` legacy route'u ayni bileseni render eder.
- **Kod Kaniti:** `frontend/src/app/(app)/image-processing-lab/page.tsx` -> `ImageProcessingLabPage`, `ImageViewer`, `BeforeAfterComparison`; `frontend/src/app/(app)/image-processing/page.tsx`; `frontend/src/components/dashboard/Sidebar.tsx`.
- **UI Kaniti:** Header, action strip, original viewer, selected stage viewer, stage details, timeline, lower analysis grid, disabled masks, OCR safety card, visual restoration isolation and responsive mobile state render edilir.
- **Veri Kurali:** Original and OCR-safe final use real authenticated blob/object URLs. Per-stage images, masks, text-preservation metrics and restoration are disabled/N/A if backend does not expose real artifacts.
- **Runtime Kaniti:** `evidence/image_processing_lab_gate/dom_verification.json` -> all browser checks true; `api_request_evidence.json` -> real preprocessing response `profile=temiz_baski`, parameters `denoise_h`, `clahe_clip`, `threshold_method`.
- **Screenshot Kaniti:** `evidence/image_processing_lab_gate/image_processing_lab_screenshot.png`; `evidence/image_processing_lab_gate/image_processing_lab_mobile.png`.
- **Test Kaniti:** 2026-08-13 frontend lint PASS, build PASS, backend regression 35 passed.

## 2026-08-14 Dashboard Embedded Image Processing Lab
- **Durum:** verified.
- **Ozet:** Ana dashboard'un mevcut uc ana panel duzeni korunarak, `pd-main-grid` altina ve Latin okunus bolumu ustune gomulu `Goruntu Isleme Laboratuvari` paneli eklendi. Latin Harfli Okunus bolumu baslik satiri kalacak sekilde ac/kapat accordion davranisi kazandi.
- **Kod Kaniti:** `frontend/src/app/(app)/dashboard/page.tsx` -> `DashboardPage`, `imageLabStages`, `showImageLab`, `showTransliteration`; `frontend/src/components/dashboard/Sidebar.tsx` -> `NAV_ITEMS`; `frontend/src/components/Icons.tsx` -> `Icons.flask`; `frontend/src/app/globals.css` -> `.pd-image-lab`, `.pd-transliteration-header`.
- **UI Kurali:** Dashboard ana 3 panel sayisi korunur; yeni lab paneli dort asamali gorsel akis, uc ok, sag durum bolumu ve `Yeniden Isle` aksiyonunu render eder. Sidebar mevcut itemlari silmeden `Goruntu Isleme Labi` linkini Ayarlar altina ekler.
- **Test Kaniti:** 2026-08-14 `npm.cmd run lint` PASS, 0 errors / 12 existing warnings; `npm.cmd run build` PASS; Playwright DOM gate `evidence/dashboard_image_lab_embed/dom_verification.json` -> `all_pass=true`.
- **Screenshot Kaniti:** `evidence/dashboard_image_lab_embed/dashboard_image_lab.png`.
