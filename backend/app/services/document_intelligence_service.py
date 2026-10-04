import json
import logging
from typing import Dict, Any, Optional, List

from app.core.config import settings
from app.services.ai.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


class DocIntelligenceEngine:
    """
    Document Intelligence Service.

    Provides:
    - Modern Turkish conversion
    - Summarization
    - Named Entity Recognition

    Local-first LLM:
    Ollama + Qwen
    """

    def __init__(self, use_mock: bool = False, provider: Optional[Any] = None):
        self.use_mock = use_mock
        self.provider = provider
        
        if not self.use_mock and self.provider is None:
            provider_name = settings.LLM_PROVIDER.strip().lower()
            if provider_name == "ollama":
                from app.services.ai.ollama_provider import OllamaProvider
                self.provider = OllamaProvider(
                    model=settings.LLM_MODEL,
                    base_url=settings.LLM_BASE_URL or "http://127.0.0.1:11434",
                )
            elif provider_name == "gemini":
                from app.services.ai.gemini_provider import GeminiProvider
                self.provider = GeminiProvider(
                    model=settings.LLM_MODEL,
                    api_key=settings.LLM_API_KEY,
                )
            else:
                raise RuntimeError(f"Unsupported active LLM provider: {settings.LLM_PROVIDER}.")

        self.translate_prompt = (
            "Sen Osmanlıca tarihi belgeler ve Türk Dili konusunda uzman kıdemli bir çevirmensin.\n\n"
            "GÖREV: Verilen metni veya transkripsiyonunu DOĞRUDAN GÜNÜMÜZ TÜRKÇESİNE ÇEVİR.\n\n"
            "KESİN KURALLAR:\n"
            "1. ASLA 'Verilen metin...', 'Çeviri yapılamamıştır...', 'Metinde sadece...', 'Osmanlıca belge içermediği için...' gibi robotik asistan açıklamaları veya bahaneler YAZMA. Sadece doğrudan metnin Türkçe anlamını yaz.\n"
            "2. Eğer metin sadece sayılardan/tarihten/numaradan ibaretse: '[Belge Kayıt No / Tarih İbaresi]' yaz.\n"
            "3. Eğer metinde bozuk parantezler, OCR gürültüleri varsa, bunları temizle ve anlamlı, akıcı bir Türkçe cümle kur.\n"
            "4. Format: Yalnızca JSON formatında 'gunumuz_turkcesi' alanında cevabı ver.\n\n"
            "KAYNAK METİN: {text}\n"
        )

        self.summarize_prompt = (
            "Yalnızca aşağıdaki KAYNAK METİN üzerinde çalış. "
            "Dış tarih bilgini KULLANMA. "
            "Kaynakta açıkça yazmayan hiçbir kişi, olay, tarih, yer, kurum veya tarihsel bağlam EKLEME. "
            "Çıkarım yapma. Tamamlama yapma. Tarihsel bilgi tahmin etme. "
            "Her özet iddiası kaynak metindeki açık bir ifadeye dayanmalıdır.\n\n"
            "KAYNAK METİN: {text}"
        )

        self.ner_prompt = (
            "Sen uzman bir NLP asistanısın. "
            "Verilen tarihî metindeki varlıkları çıkar. "
            "Kategoriler: PERSON, LOCATION, DATE, ORGANIZATION. "
            "Metinde açıkça bulunmayan varlıkları uydurma.\n\n"
            "Metin: {text}"
        )

    def health_check(self) -> Dict[str, Any]:
        if self.use_mock:
            return {
                "provider": "mock",
                "reachable": True,
                "model_available": True,
            }

        return self.provider.health_check()

    def _call_llm(self, prompt: str, text: str, mode: str) -> str:
        if self.use_mock:
            return self._mock_response(text, mode)

        if self.provider is None:
            raise RuntimeError("LLM provider is not initialized.")

        if mode == "ner":
            schema = {
                "type": "object",
                "properties": {
                    "PERSON": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "LOCATION": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "DATE": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "ORGANIZATION": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": [
                    "PERSON",
                    "LOCATION",
                    "DATE",
                    "ORGANIZATION"
                ]
            }

            result = self.provider.chat_json(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Sen tarihî belge NER motorusun. "
                            "Yalnız verilen metinde açıkça bulunan varlıkları çıkar. "
                            "Bilgi uydurma."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                schema=schema,
                temperature=0.0,
            )

            return json.dumps(result, ensure_ascii=False)

        system_message = (
            "Sen Osmanlı Türkçesi ve tarihî belgeler konusunda çalışan "
            "yerel bir belge analiz modelisin. "
            "Yalnız verilen metin üzerinde çalış. "
            "Metinde bulunmayan tarihî bilgi ekleme."
        )

        return self.provider.chat(
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0,
            think=False,
        )

    def _mock_response(self, text: str, mode: str) -> str:
        if mode == "translate":
            return (
                "Kardeşinin oğlu Ak Timur'u görevlendirdi; "
                "emrinde çok cesur askerler vardı."
            )

        if mode == "summarize":
            return (
                "Metinde bir görevlendirme ve askerî hareket anlatılmaktadır."
            )

        if mode == "ner":
            return json.dumps(
                {
                    "PERSON": ["Ak Timur"],
                    "LOCATION": [],
                    "DATE": [],
                    "ORGANIZATION": []
                },
                ensure_ascii=False,
            )

        return ""

    def transliterate_text(self, ocr_text: str) -> str:
        prompt = (
            "Sen uzman bir Osmanlıca (Arap harfli) metin okuyucususun.\n"
            "Görevin, sana verilen Osmanlıca metnin Latin harfli okunuşunu (Transliterasyon) yazmaktır.\n"
            "ÖNEMLİ KURAL: Kesinlikle anlamsız Latin harfleri uydurma (halüsinasyon yapma). "
            "Metin çok bozuksa veya okuyamadığın kısımlar varsa oralara sadece '[Okunamadı]' yaz ve atla. "
            "Sadece okunuşu yaz, modern Türkçeye çevirme ve hiçbir açıklama ekleme.\n\n"
            f"OSMANLICA METİN: {ocr_text}\n"
            "LATİN HARFLİ OKUNUŞ:"
        )
        return self._call_llm(prompt, ocr_text, mode="translate")

    def enrich_entities(self, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        if self.use_mock or self.provider is None:
            return []
            
        items_to_enrich = []
        for group in ("persons", "places", "institutions"):
            for item in entities.get(group, []):
                val = item.get("value") or item.get("normalized_value")
                if val and val != "Tespit edilemedi":
                    items_to_enrich.append(f"{group.upper()}: {val}")
                    
        if not items_to_enrich:
            return []
            
        entities_str = ", ".join(items_to_enrich)
        schema = {
            "type": "object",
            "properties": {
                "enrichments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "entity": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["entity", "description"]
                    }
                }
            },
            "required": ["enrichments"]
        }
        
        prompt = (
            "Sen bir Osmanlı tarihi uzmanısın. Aşağıdaki listede verilen kişi, yer ve kurum/antlaşmaların "
            "kim olduklarını, nerede olduklarını veya ne anlama geldiklerini ansiklopedik bir bilgiyle açıkla.\n"
            "Eğer bu bir kişi ise yaşadığı yüzyılı, dahil olduğu savaşları/seferleri; bir yer ise o dönemki tarihi önemini ve o bölgedeki büyük olayları detaylıca sun.\n"
            "Her bir varlık için JSON formatında doyurucu ve bilimsel bir 'description' (açıklama) dön.\n\n"
            f"VARLIKLAR: {entities_str}"
        )
        
        try:
            result = self.provider.chat_json(
                messages=[
                    {"role": "system", "content": "Sen ansiklopedik bir Osmanlı tarihi bilgi motorusun. Sadece JSON dön."},
                    {"role": "user", "content": prompt}
                ],
                schema=schema,
                temperature=0.1
            )
            return result.get("enrichments", [])
        except Exception as e:
            logger.error(f"Failed to enrich entities: {e}")
            return []


    def translate_to_modern_turkish_json(self, simple_latin_text: str) -> dict:
        if self.use_mock:
            return {
                "orijinal_transkripsiyon": simple_latin_text,
                "gunumuz_turkcesi": self._mock_response(simple_latin_text, "translate"),
                "kelime_koken_notlari": None
            }

        if self.provider is None:
            raise RuntimeError("LLM provider is not initialized.")

        formatted_prompt = self.translate_prompt.format(text=simple_latin_text)
        
        schema = {
            "type": "object",
            "properties": {
                "orijinal_transkripsiyon": {"type": "string"},
                "gunumuz_turkcesi": {"type": "string"},
                "kelime_koken_notlari": {"type": "string"}
            },
            "required": ["gunumuz_turkcesi"]
        }

        try:
            return self.provider.chat_json(
                messages=[
                    {"role": "system", "content": "You are a JSON-only Ottoman-to-Turkish modernizer."},
                    {"role": "user", "content": formatted_prompt}
                ],
                schema=schema,
                temperature=0.0
            )
        except Exception as e:
            logger.warning(f"chat_json failed, attempting plain chat fallback: {e}")
            try:
                raw_text = self.provider.chat(
                    messages=[
                        {"role": "system", "content": "Sen kıdemli bir Osmanlıca çevirmenisin. Verilen metni doğrudan akıcı Günümüz Türkçesine çevir."},
                        {"role": "user", "content": f"Aşağıdaki Osmanlıca metni günümüz Türkçesine çevir:\n{simple_latin_text}"}
                    ],
                    temperature=0.1
                ).strip()
                return {"gunumuz_turkcesi": raw_text}
            except Exception as e2:
                logger.error(f"Failed to modernize text: {e2}")
                return {"gunumuz_turkcesi": ""}

    def translate_to_modern_turkish(self, simple_latin_text: str) -> str:
        res = self.translate_to_modern_turkish_json(simple_latin_text)
        return res.get("gunumuz_turkcesi", "")

    def summarize_document(self, full_text: str) -> str:
        if self.use_mock:
            return self._mock_response(full_text, "summarize")

        if self.provider is None:
            raise RuntimeError("LLM provider is not initialized.")

        schema = {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string"
                },
                "claims": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "claim": {"type": "string"},
                            "evidence_quote": {"type": "string"}
                        },
                        "required": [
                            "claim",
                            "evidence_quote"
                        ]
                    }
                },
                "unsupported_or_inferred": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": [
                "summary",
                "claims",
                "unsupported_or_inferred"
            ]
        }

        result = self.provider.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sen kaynak-kilitli tarihî belge özetleme motorusun. "
                        "Yalnız kullanıcı tarafından verilen kaynak metni kullan. "
                        "Dış tarih bilgisi kullanmak kesinlikle yasaktır. "
                        "Her iddia için kaynak metinden evidence_quote ver. "
                        "Kaynakta bulunmayan hiçbir bilgi üretme."
                    )
                },
                {
                    "role": "user",
                    "content": self.summarize_prompt.format(
                        text=full_text
                    )
                }
            ],
            schema=schema,
            temperature=0.0,
        )

        def normalize(value: str) -> str:
            value = value.strip()

            # LLM bazen evidence_quote etrafına yalnızca gösterim amaçlı
            # tırnak işaretleri ekleyebilir. İçerik değişmediği sürece
            # bunları kanıt doğrulamasında yok say.
            value = value.strip('\\\"“”‘’')

            return " ".join(
                value.lower().split()
            )

        normalized_source = normalize(full_text)

        invalid_evidence = []

        for claim in result.get("claims", []):
            evidence = normalize(
                claim.get("evidence_quote", "")
            )

            if not evidence or evidence not in normalized_source:
                invalid_evidence.append(claim)

        unsupported = result.get(
            "unsupported_or_inferred",
            []
        )

        if invalid_evidence or unsupported:
            logger.warning(
                "Grounded summary rejected. "
                "invalid_evidence=%s unsupported=%s",
                invalid_evidence,
                unsupported,
            )

            return (
                "Özet güvenli biçimde üretilemedi; "
                "kaynak metin dışı çıkarım tespit edildi."
            )

        return result["summary"].strip()

    def extract_entities(self, full_text: str) -> Dict[str, Any]:
        formatted_prompt = self.ner_prompt.format(text=full_text)

        raw_json_str = self._call_llm(
            formatted_prompt,
            full_text,
            mode="ner"
        )

        try:
            parsed = json.loads(raw_json_str)

            expected_keys = {
                "PERSON",
                "LOCATION",
                "DATE",
                "ORGANIZATION"
            }

            if set(parsed.keys()) != expected_keys:
                raise ValueError(
                    f"Unexpected NER keys: {parsed.keys()}"
                )

            for key in expected_keys:
                if not isinstance(parsed[key], list):
                    raise ValueError(
                        f"{key} must be a list."
                    )

            return parsed

        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.error(
                "LLM NER output validation failed: %s",
                exc
            )

            return {
                "PERSON": [],
                "LOCATION": [],
                "DATE": [],
                "ORGANIZATION": []
            }

    def answer_question(self, question: str, document_context: str, external_context: str = "") -> str:
        if self.use_mock:
            return "Belgede bulunamadı."
            
        system_prompt = (
            "Sen Osmanlıca belgeleri analiz eden uzman ve nazik bir asistansın.\n"
            "Eğer kullanıcı 'merhaba', 'nasılsın', 'teşekkürler' gibi genel bir sohbet veya selamlama kuruyorsa, belgeden bağımsız olarak asistan kimliğinle nazikçe cevap ver.\n"
            "Eğer kullanıcının sorusu belge veya tarih ile ilgiliyse, yalnızca sağlanan 'Belge İçeriği' ve varsa 'Dış Tarihi Bilgi' metinlerine dayanarak cevap ver.\n"
            "Eğer belgeyle ilgili sorunun cevabı bu metinlerde yoksa, kesinlikle 'Bu bilgi yüklenen belgede bulunamadı.' diyerek cevap ver ve uydurma.\n"
            "Dış tarihi bilgiden yararlandığında, bunu [Dış Bilgi] etiketiyle açıkça belirt."
        )
        
        user_prompt = f"Soru: {question}\n\nBelge İçeriği:\n{document_context}"
        if external_context:
            user_prompt += f"\n\nDış Tarihi Bilgi:\n{external_context}"
            
        result = self._call_llm(
            prompt=user_prompt,
            text=document_context,
            mode="chat"
        )
        
        if not result or result.strip() == "":
            return "Bu bilgi yüklenen belgede bulunamadı."
            
        return result.strip()
