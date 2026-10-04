---
type: flow
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/models/processing_outputs.py
  - backend/app/services/chat/rag_service.py
test_paths:
  - backend/tests/test_rag_chat.py
tags: [citation, rag, traceability]
---

# Citation Flow

**Özet:** RAG sohbeti sırasında LLM tarafından üretilen veya çıkarılan yanıtların orijinal belge metinlerine (OCR veya çeviri versiyonları) doğrudan bağlanmasını sağlayan izlenebilirlik akışıdır.

**Kütüphaneler:** FastAPI, SQLAlchemy.

**Bağlantılar:** [[RAG_Chat_Service]], [[Document_Workspace]]

## Sorumluluklar
- Yapay zeka yanıtının hangi belgenin hangi sayfasına/satırına dayandığını kaydetmek.
- Son kullanıcıya tıkladığında belgedeki ilgili yeri göstermek için gerekli lokasyon (`locator`) bilgisini sağlamak.

## Girdiler
- `ChatMessage` ID'si
- İlgili chunk verisi (metin, sayfa, satır, vb.)

## Çıktılar
- `Citation` nesneleri dizisi.

## Bağımlılıklar
- `Citation` modeli.
- `RAGService.send_message`.

## Veri Akışı
1. `RAGService`, kullanıcı mesajını aldıktan sonra belge içi chunk'ları bulur.
2. Bu chunk'lara dayanarak yanıt metnini (`ChatMessage`) oluşturur ve DB'ye kaydeder.
3. Eşleşen en ilgili chunk (veya chunk'lar) için `Citation` nesnesi oluşturur.
4. `Citation` içine `document_id`, `page_id`, kaynak `text_version_id` veya `ocr_result_id` referanslarını ekler.
5. Kullanıcıya dönen yanıtta `citations` dizisi bulunur, içerikte `locator` (örneğin "Satır: X") mevcuttur.

## Hata Durumları
- Chunk bulunamadığında citation üretilmez (yanıt boş veya hata mesajıdır).

## Güvenlik ve Gizlilik
- Citationlar, mesajı oluşturan kullanıcının yetkisi altındaki belgelerle sınırlıdır. Çapraz belge citation sızması yasaktır ve IDOR engellemesiyle korunur.

## Testler ve Kabul Kriterleri
- Her kanıt destekli yanıtla birlikte en az bir citation döner: PASS.
- Citation içinde sayfa ve satır lokatörü yer alır: PASS.
- Başka belgeye citation yapılamaz: PASS.

## Kod Kanıtları
- `backend/app/models/processing_outputs.py` → `Citation` class
- `backend/app/services/chat/rag_service.py` → `Citation(...)` creation
- `backend/tests/test_rag_chat.py` → `assert data["citations"][0]["locator"] == "Satır: 1"`

## Bilinen Eksikler
- Frontend UI entegrasyonu henüz yoktur. Sadece API ve DB tarafı implemente edilmiştir.

## Değişiklik Geçmişi
- 2026-07-28: Başlangıç (TASK-023) ile testli citation akışı kuruldu.
