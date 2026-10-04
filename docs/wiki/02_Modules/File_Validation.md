---
type: module
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/services/file_service.py
  - backend/app/core/config.py
test_paths:
  - backend/tests/test_file_security.py
tags: [files, validation]
---

# File Validation

**Ozet:** Dosya uzantisi, MIME tipi, boyut limiti ve magic bytes kontrolu `FileService` icinde uygulanmistir. TASK-011 ile uzanti, MIME spoof, magic-byte spoof, boyut limiti ve path traversal dosya adi unit testleri PASS oldu. Kabul edilen turler jpg/jpeg/png/tiff/tif/pdf olarak ayarlanmistir. [[Document_Ingestion]] bu servise baglidir.

**Kutuphaneler:** FastAPI, Pillow, hashlib.

**Baglantilar:** [[Document_Ingestion]], [[Risks]], [[Database_Model]]

## Sorumluluklar
- Upload dosyasinin tipini, icerigini ve boyutunu dogrulamak.

## Girdiler
- `UploadFile`, dosya yolu.

## Ciktilar
- MIME/extension tuple, SHA-256 hash, kaydedilmis dosya.

## Bagimliliklar
- `settings.ALLOWED_EXTENSIONS`, `settings.MAX_FILE_SIZE_MB`.

## Veri Akisi
- `validate_file` -> `save_upload` -> `validate_magic_bytes` -> `calculate_hash`.

## Hata Durumlari
- MIME client tarafindan saglanir; magic bytes sonradan kontrol edilir.

## Guvenlik ve Gizlilik
- Sahte uzanti kontrolu var; dosya isimleri UUID parcasi ile benzersizlestirilir.

## Testler ve Kabul Kriterleri
- `backend/tests/test_file_security.py` sahte uzanti, MIME spoof, magic-byte spoof temizligi, boyut limiti temizligi ve path traversal dosya adi testlerini icerir.
- Kanit: `evidence/environment_gate/backend_pytest_task011_full.txt` -> 14 passed.

## Kod Kanitlari
- `backend/app/services/file_service.py` -> `ALLOWED_MIME_TYPES`, `MAGIC_BYTES`, `validate_file`, `validate_magic_bytes`

## Bilinen Eksikler
- Antivirus/sandbox taramasi yok.
- Upload route integration, PDF fixture ve thumbnail testleri TASK-012 kapsaminda genisletilmeli.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
- 2026-07-28: TASK-011 sirasinda file security unit test kanitlari eklendi.
