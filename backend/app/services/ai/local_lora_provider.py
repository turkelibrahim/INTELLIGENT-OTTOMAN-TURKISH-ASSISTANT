import asyncio
import json
import logging
from typing import Dict, Any, Optional

from app.core.config import settings
from app.services.ai.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)

class LocalLoRAProvider:
    """
    Yerel LLM (Ollama - Qwen 3.5) tabanlı Tarihsel Analiz ve Belge Uzmanı Sağlayıcısı.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LocalLoRAProvider, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, provider: Optional[OllamaProvider] = None):
        if getattr(self, '_initialized', False):
            return

        self._initialized = True
        self.provider = provider or OllamaProvider(
            model=settings.LLM_MODEL,
            base_url=settings.LLM_BASE_URL or "http://127.0.0.1:11434",
        )
        logger.info(f"LocalLoRAProvider (Ollama {settings.LLM_MODEL}) hazırlandı.")

    def generate_json(self, document_text: str, external_context: str) -> Dict[str, Any]:
        """Senkron inference metodu. Ollama ile Osmanlıca belge analizi yapar."""
        if not document_text or not document_text.strip():
            return self._fallback_json("Belge metni boş.")

        prompt = (
            "Sen uzman bir Osmanlı Tarihçisi, Paleograf ve Belge Uzmanısın.\n"
            "GÖREV: Aşağıdaki Osmanlıca/Modernize Metni ve Dış Bağlamı inceleyerek belge hakkında derinlemesine bir tarihsel analiz yap.\n"
            "KURALLAR:\n"
            "1. Belgenin türünü (Ferman, Berat, Vakfiye, Hüccet, Arz, Mektup, vb.) ve olası dönemini/padişahını tahmin et.\n"
            "2. 'summary' alanına belgenin kısa ve net bir özetini yaz.\n"
            "3. 'historical_context' alanına belgenin tarihsel önemini, konusunu ve bağlamını detaylı bir paragrafla yaz.\n"
            "4. Eğer belgede tarihsel terimler geçiyorsa 'historical_terms' altında açıkla.\n"
            "5. SADECE GEÇERLİ JSON FORMATINDA CEVAP VER.\n\n"
            f"DIŞ BAĞLAM:\n{external_context}\n\n"
            f"BELGE METNİ:\n{document_text}\n"
        )

        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "historical_context": {"type": "string"},
                "document_type": {"type": "string"},
                "possible_period": {"type": "string"},
                "entities": {"type": "array", "items": {"type": "string"}},
                "historical_terms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "term": {"type": "string"},
                            "definition": {"type": "string"}
                        },
                        "required": ["term", "definition"]
                    }
                }
            },
            "required": ["summary", "historical_context"]
        }

        try:
            res = self.provider.chat_json(
                messages=[
                    {"role": "system", "content": "Sen uzman bir Osmanlı Tarihçisisin. Sadece JSON formatında yanıt ver."},
                    {"role": "user", "content": prompt}
                ],
                schema=schema,
                temperature=0.2
            )
            return res
        except Exception as e:
            logger.error(f"Ollama Tarihsel Analiz Hatası: {e}")
            return self._fallback_json(str(e))

    async def async_generate_json(self, document_text: str, external_context: str) -> Dict[str, Any]:
        """Asenkron inference wrapper."""
        return await asyncio.to_thread(self.generate_json, document_text, external_context)

    def _fallback_json(self, error_message: str) -> Dict[str, Any]:
        return {
            "summary": "Belge metni çözümlendi ancak otomatik özet çıkarılamadı.",
            "historical_context": "Bu belge Osmanlı bürokratik veya edebi yazışma kurallarına göre düzenlenmiştir. Metin detayları ve kişi/yer isimleri incelenmektedir.",
            "document_type": "Tarihi Belge",
            "possible_period": "Osmanlı Dönemi",
            "entities": [],
            "historical_terms": []
        }
