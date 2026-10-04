---
type: module
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/services/export_service.py
  - backend/app/api/routes/export.py
test_paths:
  - backend/tests/test_export.py
tags: [export, csv, json, txt, traceability]
---

# Export Service

**Özet:** İşlenmiş belgeleri, OCR sonuçlarını, çevirileri, varlıkları ve citation'ları kullanıcıya dışa aktarmak için (TXT, JSON, CSV formatında) kullanılan servistir.

**Kütüphaneler:** FastAPI, SQLAlchemy, json, csv.

**Bağlantılar:** [[Document_Workspace]], [[OCR_Service]], [[Transliteration_Service]], [[NER_Service]]

## Sorumluluklar
- Ham OCR, düzeltilmiş OCR, Latin, Modern Türkçe ve Özet metinleri TXT formatında dışa aktarmak.
- Sayfa, satır, bounding box, entity ve citation'ları tam bir yapısal JSON ağacı olarak aktarmak.
- Bulunan varlıkları (Entity) CSV formatında dışa aktarmak.
- Her dışa aktarımı (ExportRecord) ve yetkilendirmeyi denetleyip Audit Log tutmak.

## Girdiler
- `document_id`: Dışa aktarılacak belgenin ID'si.
- `version_type`: Hangi metin versiyonunun aktarılacağı (`raw_ocr`, `latin`, vb.).
- `current_user`: Erişim kontrolü için.

## Çıktılar
- Uygulama içi `exports/` dizinine kaydedilmiş fiziksel dosya (JSON, TXT, CSV).
- API dönüşünde içeriğin kendisi (veya gelecekte dosya indirme linki).

## Bağımlılıklar
- Document, Page, OCRResult, TextVersion, Entity, Citation, ExportRecord.
- AuditLog

## Veri Akışı
1. Kullanıcı `GET /export/txt/{id}?version_type=...` (veya `json`, `csv`) çağrısı yapar.
2. `ExportService._verify_access` belge sahipliğini doğrular.
3. İstenilen formata göre veri DB'den toplanır (TXT için satırlar, JSON için sayfa bazlı ağaç, CSV için entity dizisi).
4. Veri bellekte formatlanır ve disk üzerinde `exports/doc_{id}_{type}.ext` dosyasına yazılır.
5. Veritabanına bir `ExportRecord` eklenir.
6. İşlem bir `AuditLog` kaydıyla belgelenir.
7. Oluşturulan içerik API yanıtı olarak istemciye döner.

## Hata Durumları
- `403 Forbidden`: Kullanıcı kendisine ait olmayan belgeyi dışa aktarmaya çalışırsa.
- `404 Not Found`: Belge bulunamazsa (veya erişim hakkı yoksa gizlenir, şu an 403 atıyor).

## Güvenlik ve Gizlilik
- IDOR koruması mevcuttur. Sadece `doc.user_id == current_user.id` erişebilir.
- Dosya yolları Path Traversal'a karşı güvendedir, sadece backend'in `exports/` dizini altına statik ID ile yazılır.

## Testler ve Kabul Kriterleri
- TXT aktarımı (raw_ocr ve diğer text versiyonları) PASS.
- JSON tam ağaç (sayfalar, çizgiler, varlıklar, citations) aktarımı PASS.
- CSV (Entity) aktarımı PASS.
- Yetkisiz erişim denemesinde (IDOR) HTTP 403 PASS.
- ExportRecord ve AuditLog oluşturulduğu testlerde doğrulandı PASS.

## Kod Kanıtları
- `backend/app/services/export_service.py` → `ExportService`
- `backend/app/api/routes/export.py` → `/export/txt`, `/export/json`, `/export/csv/entities`
- `backend/tests/test_export.py` → `test_export_json_full`, vb.

## Bilinen Eksikler
- PDF/DOCX şeklinde akademik rapor oluşturulması şu an desteklenmemektedir (Gelecekte Pandoc veya ReportLab ile entegre edilebilir).
- API doğrudan JSON formatında string döndürüyor; frontend `FileResponse` ile header'larda dosya indirmesi tetiklemek isteyebilir (MVP'de JSON body kabul edildi).

## Değişiklik Geçmişi
- 2026-07-28: Başlangıç (TASK-024) ile TXT, JSON, CSV export servisleri ve testleri kuruldu.
