---
type: module
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/db/database.py
  - backend/app/models/user.py
  - backend/app/models/document.py
  - backend/app/models/page.py
  - backend/app/models/processing_job.py
  - backend/app/models/image_variant.py
  - backend/app/models/audit_log.py
  - backend/app/models/processing_outputs.py
  - backend/alembic.ini
  - backend/alembic/versions/20260728_0001_initial_schema.py
test_paths:
  - backend/tests/test_smoke.py
  - backend/tests/test_migrations.py
tags: [database, sqlalchemy, alembic, task-010]
---

# Database Model

**Ozet:** Veri katmani SQLAlchemy declarative modelleri, SQLite default `DATABASE_URL` ve Alembic initial migration ile tanimlidir. User, Document, Page, ProcessingJob, ImageVariant, AuditLog, ModelRegistryEntry, OCRResult, TextVersion, Entity, ChatSession, ChatMessage, Citation ve ExportRecord modelleri mevcuttur. Temiz DB migration ve rollback testi PASS oldugu icin veri model/migration kapisi `verified`tir.

**Kutuphaneler:** SQLAlchemy, SQLite, Alembic.

**Baglantilar:** [[Architecture_Map]], [[Document_Ingestion]], [[Security_Model]], [[Audit_Log]], [[Model_Registry]], [[OCR_Service]], [[Citation_Flow]]

## Sorumluluklar
- ORM modellerini, session lifecycle'ini, migration/rollback temelini ve AI ciktilari icin izlenebilir veri zincirini saglamak.
- Orijinal belge metadata'sini DB'de, buyuk ikili dosyalari dosya deposunda tutmak.

## Girdiler
- DB URL, route/service DB islemleri, belge metadata'si, isleme ciktilari.

## Ciktilar
- SQLAlchemy session, metadata tablolari ve Alembic migration.

## Bagimliliklar
- `settings.DATABASE_URL`.
- `backend/alembic.ini` ve `backend/alembic/env.py`.

## Veri Akisi
- `get_db` dependency route'lara session verir; `init_db` startup'ta tablolari olusturur.
- Alembic initial migration temiz veritabaninda `users -> documents/pages/jobs -> output/version/entity/chat/citation/export` veri zincirini kurar.
- `documents.file_hash` orijinal dosya hash'ini saklar.
- `ocr_results` ham OCR satirlarini page/job/model baglantisiyla saklar.
- `text_versions` OCR duzeltmesi, transliterasyon, modernizasyon ve ozet gibi metin surumlerini kaynak surumle iliskilendirebilir.
- `model_registry_entries` model adi, tip, surum, checksum ve config metadata'sini tutar.
- `citations` chat mesajlarini belge, sayfa ve text version kanitina baglar.

## Hata Durumlari
- Release oncesi gercek production DB gecisinde mevcut SQLite dosyasi yedeklenmeli ve Alembic upgrade ayri kosulmalidir.
- Runtime servisleri yeni OCR/text/entity/chat/citation/export tablolarini henuz kullanmiyor; bu entegrasyon sonraki TASK-017..024 kapsaminda.

## Guvenlik ve Gizlilik
- SQLite dosyasi proje icinde; testler gecici SQLite dosyasi uzerinde calisir ve kullanici DB/dosya deposuna dokunmaz.
- Gizli degerler migration veya wiki icine yazilmadi.

## Testler ve Kabul Kriterleri
- `backend/tests/test_smoke.py` metadata tablo ve kritik izlenebilirlik kolonlarini dogrular.
- `backend/tests/test_migrations.py` temiz SQLite DB uzerinde Alembic `upgrade head` ve `downgrade base` akisini dogrular.
- Kanit: `evidence/environment_gate/backend_pytest_after_traceability_columns.txt` -> 4 passed.
- Doctor kaniti: `evidence/environment_gate/doctor_after_traceability_columns.txt` -> `DOCTOR_FAILED=0`.

## Kod Kanitlari
- `backend/app/db/database.py` -> `Base`, `engine`, `get_db`, `init_db`.
- `backend/app/models/*.py` -> temel model siniflari.
- `backend/app/models/processing_outputs.py` -> `ModelRegistryEntry`, `OCRResult`, `TextVersion`, `Entity`, `ChatSession`, `ChatMessage`, `Citation`, `ExportRecord`.
- `backend/alembic/versions/20260728_0001_initial_schema.py` -> initial schema migration ve rollback.

## Bilinen Eksikler
- Delete/retention davranisinin runtime entegrasyon testi TASK-012 ve TASK-026 icinde genisletilmeli.
- PostgreSQL production gecisi henuz uygulanmadi; Alembic yapisi bu gecis icin temel saglar.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
- 2026-07-28: TASK-008 sirasinda status `partial` yapildi.
- 2026-07-28: TASK-010 sirasinda Alembic initial migration, rollback testi ve cikti modelleri eklenerek status `verified` yapildi.
