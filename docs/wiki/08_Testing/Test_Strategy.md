---
type: module
status: partial
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/test_import.py
  - backend/tests/
  - backend/requirements-dev.txt
  - frontend/package.json
tags: [testing, pytest, eslint, audit]
---

# Test Strategy

**Ozet:** TASK-009 ile test altyapisi kuruldu; TASK-010/TASK-011 ile backend smoke, migration, auth/security ve file-security testleri eklendi. Backend pytest 14 PASS, frontend lint/build PASS, npm audit high 0 vulnerability. Integration/e2e ve AI pipeline testleri halen eksik oldugu icin genel test stratejisi `partial`tir.

**Kutuphaneler:** pytest, Alembic, FastAPI TestClient, ESLint, npm audit.

**Baglantilar:** [[Task_Queue]], [[FastAPI_API]], [[Document_Workspace]], [[Security_Model]], [[File_Validation]], [[Database_Model]]

## Sorumluluklar
- Auth, upload, preprocessing, AI pipeline, UI ve release akislari icin tekrar edilebilir dogrulama.

## Girdiler
- Test fixture'lari, API client, sample image/PDF, gecici SQLite DB.

## Ciktilar
- Test raporu, lint/build sonucu, dependency audit sonucu.

## Bagimliliklar
- `backend/requirements-dev.txt`.
- `frontend/package.json` scripts.

## Veri Akisi
- Backend pytest -> frontend lint/build -> dependency audit -> release e2e gate.

## Hata Durumlari
- Test yoksa regressions yakalanmaz.
- Frontend lint warning mevcut: custom font warning; build'i bloklamaz.

## Guvenlik ve Gizlilik
- Fixture'larda gercek kullanici verisi olmamali.
- Secret taramasinda `.env` degerleri kopyalanmaz.

## Testler ve Kabul Kriterleri
- Backend import smoke: PASS. Kanit: `evidence/recover_baseline/backend_import_smoke.txt`.
- Backend pytest: PASS, 14 tests. Kanit: `evidence/environment_gate/backend_pytest_task011_full.txt`.
- Doctor full: PASS. Kanit: `evidence/environment_gate/doctor_task011_full.txt`.
- Frontend lint: PASS with warning. Kanit: `evidence/environment_gate/frontend_lint_task011_after_minimatch_override.txt`.
- Frontend build: PASS. Kanit: `evidence/environment_gate/frontend_build_task011_after_minimatch_override.txt`.
- npm audit high: PASS, 0 vulnerability. Kanit: `evidence/environment_gate/npm_audit_high_task011_after_minimatch_override.txt`.
- Pipeline smoke: BROKEN, `AttributeError: 'ImagePreprocessor' object has no attribute 'process'`. Kanit: `evidence/recover_baseline/backend_pipeline_smoke_utf8.txt`.

## Kod Kanitlari
- `backend/test_import.py` -> import smoke.
- `backend/tests/test_smoke.py` -> health ve DB metadata smoke.
- `backend/tests/test_migrations.py` -> Alembic upgrade/downgrade.
- `backend/tests/test_auth_security.py` -> auth ve belge izolasyonu.
- `backend/tests/test_file_security.py` -> file validation guvenlik testleri.
- `scripts/doctor.ps1` -> backend/frontend local gate.
- `frontend/package.json` -> `lint`, `build` scriptleri ve security overrides.

## Bilinen Eksikler
- Upload route, PDF sayfalama, preprocessing endpointleri ve AI pipeline icin integration test eksik.
- E2E/release gate henuz yok.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
- 2026-07-28: BASELINE-001 test/env kanitlari eklendi.
- 2026-07-28: TASK-009/TASK-010/TASK-011 ile pytest, doctor, migration, auth/security, file-security ve npm audit kanitlari eklendi.
