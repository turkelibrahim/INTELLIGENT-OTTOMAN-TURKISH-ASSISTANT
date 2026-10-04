from sqlalchemy.orm import Session
from app.models.processing_outputs import ChatSession, ChatMessage, Citation, TextVersion, OCRResult
from app.models.document import Document
from app.models.page import Page
import re
from app.services.historical_rag import HistoricalQdrantStore
from app.services.document_intelligence_service import DocIntelligenceEngine

class RAGService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, document_id: int, user_id: int, title: str = "New Chat") -> ChatSession:
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError("Document not found")
        if doc.user_id != user_id:
            raise ValueError("Unauthorized access to document")
            
        session = ChatSession(document_id=document_id, user_id=user_id, title=title)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
        
    def _detect_prompt_injection(self, query: str) -> bool:
        forbidden = ["ignore previous", "system prompt", "bypass", "you are now"]
        query_lower = query.lower()
        return any(f in query_lower for f in forbidden)

    def _retrieve_chunks(self, document_id: int, query: str):
        results = []
        
        # Gerçek ChromaDB kullanımı
        from app.services.chat.embeddings import VectorStoreService
        import logging
        logger = logging.getLogger(__name__)
        
        vector_service = VectorStoreService()
        if vector_service.collection is not None and vector_service.embedding_model is not None:
            # RAG araması
            filter_dict = {"document_id": document_id}
            search_results = vector_service.similarity_search(query, k=4, filter_dict=filter_dict)
            
            for res in search_results:
                results.append({
                    "type": res.get("chunk_type", "version"),
                    "text": res.get("text"),
                    "page_id": res.get("page_id"),
                    "id": res.get("db_id"),
                    "confidence": res.get("confidence"),
                    "line_no": res.get("line_no")
                })
                
        # Eğer ChromaDB boşsa veya test modundaysak SQL fallback kullan
        if not results:
            logger.info("ChromaDB returned no results, falling back to SQL text search for tests/legacy")
            words = set(re.findall(r'\w+', query.lower()))
            if not words:
                return results
                
            # 1. OCR Results
            pages = self.db.query(Page).filter(Page.document_id == document_id).all()
            page_ids = [p.id for p in pages]
            
            if page_ids:
                ocr_results = self.db.query(OCRResult).filter(OCRResult.page_id.in_(page_ids)).all()
                for ocr in ocr_results:
                    ocr_words = set(re.findall(r'\w+', ocr.raw_text.lower()))
                    if words.intersection(ocr_words):
                        results.append({
                            "type": "ocr",
                            "text": ocr.raw_text,
                            "page_id": ocr.page_id,
                            "id": ocr.id,
                            "confidence": ocr.confidence_score,
                            "line_no": ocr.line_no
                        })
                    
            # 2. Text Versions (modernized, etc.)
            text_versions = self.db.query(TextVersion).filter(TextVersion.document_id == document_id).all()
            for tv in text_versions:
                tv_words = set(re.findall(r'\w+', tv.text.lower()))
                if words.intersection(tv_words):
                    results.append({
                        "type": "version",
                        "text": tv.text,
                        "page_id": tv.page_id,
                        "id": tv.id,
                        "version_type": tv.version_type,
                        "confidence": tv.confidence_score
                    })
                    
        return results
        
    def send_message(self, session_id: int, user_id: int, content: str) -> dict:
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or unauthorized")
            
        # Add user message
        user_msg = ChatMessage(session_id=session.id, role="user", content=content)
        self.db.add(user_msg)
        self.db.commit()
        
        # Check prompt injection
        if self._detect_prompt_injection(content):
            assistant_msg = ChatMessage(session_id=session.id, role="assistant", content="Sistem politikası ihlali tespit edildi. Lütfen sadece belge içeriği ile ilgili sorular sorun.")
            self.db.add(assistant_msg)
            self.db.commit()
            self.db.refresh(assistant_msg)
            return {"message": assistant_msg, "citations": []}
            
        # Retrieve chunks
        chunks = self._retrieve_chunks(session.document_id, content)
        
        doc_context = ""
        if chunks:
            doc_context = "\n".join(
                [f"Satır {c.get('line_no', '?')}: {c.get('text', '')}" for c in chunks if c.get("type") == "ocr" or c.get("type") == "version"]
            )
        
        # Check external historical knowledge
        try:
            qdrant_store = HistoricalQdrantStore()
            historical_items = qdrant_store.search(query=content, limit=2, verified_only=True)
            external_context = "\n".join([item.get("text", "") for item in historical_items if item.get("text")])
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Qdrant search failed: {e}")
            external_context = ""
            
        has_low_confidence = any(c.get("confidence") is not None and c.get("confidence") < 0.6 for c in chunks)
        warning_prefix = "[UYARI: Düşük güvenli kaynak metin] " if has_low_confidence else ""

        intelligence = DocIntelligenceEngine()
        answer_text = intelligence.answer_question(content, doc_context, external_context)
        
        final_answer = warning_prefix + answer_text
        
        assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=final_answer)
        self.db.add(assistant_msg)
        self.db.flush()
        
        # Create citation for the first relevant chunk
        top_chunk = chunks[0]
        citation = Citation(
            message_id=assistant_msg.id,
            document_id=session.document_id,
            page_id=top_chunk.get("page_id"),
            text_version_id=top_chunk.get("id") if top_chunk["type"] == "version" else None,
            quote=top_chunk['text'],
            locator=f"Satır: {top_chunk.get('line_no')}" if top_chunk["type"] == "ocr" else "Versiyon Metni"
        )
        self.db.add(citation)
        self.db.commit()
        
        self.db.refresh(assistant_msg)
        self.db.refresh(citation)
        return {"message": assistant_msg, "citations": [citation]}
