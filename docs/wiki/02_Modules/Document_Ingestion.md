---
type: module
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/api/routes/documents.py
  - backend/app/services/file_service.py
  - backend/app/models/document.py
  - backend/app/models/page.py
test_paths:
  - backend/tests/test_document_upload_integration.py
tags: [documents, ingestion]
---

# Document Ingestion

**Ozet:** Belge yukleme `/documents` POST endpointi ile baslar, dosya dogrulanir, kaydedilir ve `Document`/`Page` kayitlari olusturulur. TASK-012 ile PNG upload, sayfa/thumbnail erisimi, magic-byte spoof reddi, delete cleanup ve audit akisi integration testle PASS oldu. PDF sayfalama [[PDF_Page_Splitting]] altinda TASK-013 icin partial kalir.

**Kutuphaneler:** FastAPI UploadFile, SQLAlchemy, Pillow, pdf2image.

**Baglantilar:** [[FastAPI_API]], [[File_Validation]], [[PDF_Page_Splitting]], [[Database_Model]], [[Image_Preprocessing]]

## Sorumluluklar
- Dosya alma, metadata kaydi, sayfa kaydi, audit log yazma.

## Girdiler
- Form data: file, title, description, source, period, access_level.

## Ciktilar
- `DocumentResponse`, `Document`, `Page`, upload dosyalari.

## Bagimliliklar
- `file_service`, `get_current_user`, `get_db`.

## Veri Akisi
- Upload UI -> `documentsApi.upload` -> `upload_document` -> `FileService`.

## Hata Durumlari
- Gecersiz dosya, buyuk dosya, PDF sayfalama bos donerse page_count fallback davranisi riskli olabilir.

## Guvenlik ve Gizlilik
- Kullanici dependency ile korunur; silme islemi dosya sistemini de temizler.

## Testler ve Kabul Kriterleri
- `backend/tests/test_document_upload_integration.py` upload auth, PNG upload, spoof rejection, page image/thumbnail ve delete cleanup testlerini icerir.
- Kanit: `evidence/environment_gate/backend_pytest_task012_after_fix.txt` -> 19 passed.

## Kod Kanitlari
- `backend/app/api/routes/documents.py` -> `upload_document`, `delete_document`
- `backend/app/services/file_service.py` -> `save_upload`

## Bilinen Eksikler
- Duplicate kontrolu sadece `pass` ile uyari uretmiyor.
- PDF sayfalama gercek PDF fixture ile henuz dogrulanmadi; TASK-013.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
- 2026-07-28: TASK-012 sirasinda upload/page/thumbnail/delete integration test kanitlari eklendi.
