---
type: ingest_log
status: verified
last_verified: 2026-08-02
owners: []
source_paths:
  - backend/app
  - frontend/src
tags: [ingest, bootstrap]
---

# Ingest Log

**Ozet:** BOOTSTRAP ve ilk INGEST kaydi. Kaynak dosyalar okunarak envanter, mimari harita, riskler ve gorev kuyruÄŸu olusturuldu. Kod degisikligi yapilmadi.

**Kutuphaneler:** rg, PowerShell.

**Baglantilar:** [[Index]], [[Source_Map]], [[Latest_Handoff]]

## 2026-07-28 - BOOTSTRAP/INGEST
- Okunan protokol: kullanici ekindeki pasted-text.
- Kok `AGENTS.md`: bulunamadi.
- Incelenen backend alanlari: `backend/app/main.py`, `api`, `core`, `db`, `models`, `schemas`, `services`.
- Incelenen frontend alanlari: `frontend/src/app`, `frontend/src/lib/api.ts`, `frontend/package.json`, `next.config.ts`, `eslint.config.mjs`, `tsconfig.json`.
- Incelenen konfigurasyon: `backend/requirements.txt`, `backend/.env` hassas deger kopyalanmadan.
- Uretilen wiki dugumleri: [[Index]], [[Current_State]], [[Architecture_Map]], [[Source_Map]], [[Risks]], [[Open_Questions]], [[Task_Queue]], [[Execution_Lock]], [[Decisions]], [[Change_Log]], [[Lint_Report]], [[Latest_Handoff]].
- Kod degisikligi: Yok.

## 2026-08-02 - BOOTSTRAP Refresh
- Okunan zorunlu dosyalar: `AGENTS.md`, [[Index]], [[Current_State]], [[Task_Queue]], [[Execution_Lock]], [[Decisions]], [[Latest_Handoff]], [[Architecture_Map]], [[Source_Map]].
- Incelenen proje envanteri: root dizin, `README.md`, `backend/requirements.txt`, `frontend/package.json`, `backend/app/main.py`, `backend/app/api/router.py`, `backend/worker.py`, `backend/tests`.
- Git durumu: `git` executable PATH uzerinde bulunamadigi icin alinamadi; bu durum onceki evidence ile tutarlidir.
- Guncellenen dugumler: [[Index]], [[Architecture_Map]], [[Evaluation_Service]], [[Source_Map]], [[Current_State]], [[Task_Queue]], [[Change_Log]], [[Latest_Handoff]].
- Olusturulan sablonlar: [[Node_Template]], [[Task_Template]], [[Decision_Template]], [[Handoff_Template]].
- Kod degisikligi: Yok.
- Sonuc: Aktif kod gorevi yok; siradaki kesin adim human-verified ground truth review.

