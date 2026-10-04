---
type: module
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/services/chat/rag_service.py
  - backend/app/api/routes/chat.py
test_paths:
  - backend/tests/test_rag_chat.py
tags: [rag, chat, nlp, injection]
---

# RAG Chat Service

**Özet:** Kullanıcının yüklediği belge üzerinde soru sormasını sağlayan, prompt injection korumasına ve düşük güven uyarısına sahip RAG (Retrieval-Augmented Generation) servisidir.

**Kütüphaneler:** FastAPI, SQLAlchemy, regex.

**Bağlantılar:** [[Citation_Flow]], [[OCR_Service]], [[Modernization_Service]], [[Document_Workspace]]

## Sorumluluklar
- Sohbet oturumlarını yönetmek.
- Kullanıcı sorgularına (prompt injection kontrolünden geçirerek) yanıt vermek.
- Sorguyla eşleşen OCR veya TextVersion verilerini bulmak.
- Belgede bulunamayan sorgulara "Belgede bulunamadı." yanıtını dönmek.
- Bulunan kanıtlara dayalı citation (kaynak) nesnelerini üretmek.

## Girdiler
- `ChatSessionCreate`: document_id
- `ChatMessageCreate`: content

## Çıktılar
- `ChatMessageResponse`: mesaj ve citation listesi (sayfa ve satır bilgisiyle).

## Bağımlılıklar
- Document
- Page
- OCRResult
- TextVersion
- ChatMessage
- Citation

## Veri Akışı
1. İstemci `POST /sessions` çağrısı yapar.
2. `POST /sessions/{id}/messages` ile sorgu iletilir.
3. RAGService prompt injection kontrolü yapar.
4. Güvenliyse ilgili belgenin OCR/TextVersion kayıtlarında keyword araması ile chunkları getirir.
5. Chunk yoksa "Belgede bulunamadı." döner.
6. Chunk varsa ilkini kaynak alıp Citation nesnesi oluşturarak yanıt üretir.

## Hata Durumları
- `403 Forbidden`: Başka bir kullanıcının belgesine erişim denemesi.
- `403 Forbidden`: Geçersiz session_id.
- Prompt injection tespit edildiğinde hata atılmaz, ancak uyarı mesajı ile citation'suz yanıt dönülür.

## Güvenlik ve Gizlilik
- Belge izolasyonu (`document.user_id == current_user.id`) ile sıkı korunur.
- LLM prompt injection listesi (`ignore previous`, vs.) kontrol edilir.
- Düşük güvenli OCR kaynakları (confidence < 0.6) açıkça "[UYARI: Düşük güvenli kaynak metin]" öneki ile işaretlenir.

## Testler ve Kabul Kriterleri
- Cevaplanabilir soru (sayfa/satır kaynaklı) PASS.
- Cevaplanamaz soru (Belgede bulunamadı) PASS.
- Prompt injection engelleme PASS.
- Başka belgeye sızma (IDOR / cross-document leakage) engellenir PASS.
- Düşük güven uyarısı PASS.

## Kod Kanıtları
- `backend/app/services/chat/rag_service.py` → `RAGService`
- `backend/app/api/routes/chat.py` → `send_message`
- `backend/tests/test_rag_chat.py` → `test_rag_answerable_question`

## Bilinen Eksikler
- Gerçek LLM entegrasyonu ve Vector DB / Embedding eksiktir; şu an in-memory keyword tabanlı çalışır.
- Reranking uygulanmamıştır.

## Değişiklik Geçmişi
- 2026-07-28: Başlangıç entegrasyonu (TASK-023) ile test destekli sahte veri akışı kuruldu.
