---
type: module
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/services/file_service.py
  - backend/requirements.txt
test_paths:
  - backend/tests/test_document_upload_integration.py
tags: [pdf, documents]
---

# PDF Page Splitting

**Ozet:** PDF sayfalama `FileService.split_pdf_to_pages` icinde once `pdf2image.convert_from_path` ile, Poppler yoksa `pypdfium2` fallback'i ile uygulanir. TASK-013 ile iki sayfali PDF fixture upload edildi, sayfa sirasi `[1, 2]`, PNG page output ve thumbnail uretimi testle PASS oldu.

**Kutuphaneler:** pdf2image, pypdfium2, Pillow.

**Baglantilar:** [[Document_Ingestion]], [[File_Validation]], [[Risks]]

## Sorumluluklar
- PDF sayfalarini PNG dosyalarina ayirmak.

## Girdiler
- PDF dosya yolu, document_id.

## Ciktilar
- page_no, image_path, width, height listesi.

## Bagimliliklar
- `pdf2image`, opsiyonel Poppler, `pypdfium2`.

## Veri Akisi
- `upload_document` PDF branch -> `split_pdf_to_pages` -> `Page` kayitlari.

## Hata Durumlari
- Poppler yoksa `pypdfium2` fallback denenir; iki motor da basarisiz olursa bos liste doner.

## Guvenlik ve Gizlilik
- PDF icerigi dosya sistemine goruntu olarak yazilir.

## Testler ve Kabul Kriterleri
- Gercek iki sayfali PDF fixture testi PASS. Kanit: `evidence/environment_gate/backend_pytest_task013_pdf_initial.txt`.
- Full gate PASS. Kanit: `evidence/environment_gate/doctor_task013_full.txt`.

## Kod Kanitlari
- `backend/app/services/file_service.py` -> `split_pdf_to_pages`

## Bilinen Eksikler
- PDFium fallback var; Poppler yoklugu artik Windows native testini bloklamaz.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
- 2026-07-28: TASK-013 sirasinda pypdfium2 fallback eklendi ve PDF sayfa sirasi/thumbnail testi PASS oldu.
