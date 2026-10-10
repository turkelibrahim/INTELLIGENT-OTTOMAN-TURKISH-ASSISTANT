"""
Transliteration Service
Responsible for converting Ottoman Turkish text (Arabic script) into Latin alphabet.
Uses an LLM (Large Language Model) to handle context-dependent vowel inference.
"""
from typing import Optional

from app.core.config import settings
from app.services.ai.ollama_provider import OllamaProvider

class TransliterationEngine:
    def __init__(self, use_mock=False, provider=None):
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
                raise RuntimeError(
                    f"Unsupported active LLM provider for transliteration: {settings.LLM_PROVIDER}. "
                    "Set LLM_PROVIDER=ollama or gemini."
                )
        
        # PROMPTS
        self.academic_prompt = (
            "Sen uzman bir transkripsiyon uzmanısın.\n\n"
            "GÖREV: Aşağıdaki metni, Türk Dil Kurumu ve İSAM standartlarına uygun, Latin Harfli Transkripsiyona dönüştür.\n\n"
            "KURALLAR:\n"
            "1. Yalnızca girdi metninde gördüklerini aktar. Metin modern bir Türkçe alıntıysa, sadece Latin harflerine aktar, tarihi Osmanlı kalıpları uydurma.\n"
            "2. Girdide '[?]' veya '[okunamadı]' gibi belirsizlik işaretleri varsa, bunları aynen koru. Yerlerine kelime UYDURMA.\n"
            "3. Sesli Harf ve Tamlamalar: Osmanlıca ise yazılmayan ünlüleri Türkçe ses uyumuna göre tamamla (Örn: 'emr-i şerîf').\n"
            "4. SATIR KORUMA: Girdi metnindeki satır sayılarını ve satır sonlarını (line breaks) BİREBİR KORU. Asla satırları birleştirip tek bir paragraf yapma.\n"
            "5. Format: Yalnızca JSON nesnesi içinde 'duzeltilmis_okunus' alanında cevabı ver.\n\n"
            "ÖRNEKLER:\n"
            "Girdi: 'بسمله شریف مفتاح ابواب سعادتدر'\n"
            "Çıktı: 'Besmele-i şerîfe miftâh-ı ebvâb-ı sa'âdetdir'\n\n"
            "Girdi: 'انسان عینی آنده [?] روحی هم'\n"
            "Çıktı: 'İnsan aynı anda [?] rûhu hem'\n\n"
            "Metin: {ottoman_text}\n"
        )

        self.simple_prompt = (
            "Sen uzman bir çevirmensin. "
            "Görev: Sana verilen metni, günümüz modern Türk alfabesiyle (sade Latin harfleri) akıcı bir formata çevirmek.\n\n"
            "KURAL 1: Sadece çeviri çıktısını ver, açıklama yapma.\n"
            "KURAL 2: Şapkalı veya noktalı akademik özel harfleri KULLANMA.\n"
            "KURAL 3: Girdi metnindeki kelime sırasını ve anlamını değiştirme. Olmayan bir anlamı ekleme.\n"
            "KURAL 4: Eğer girdide '[?]' veya '[okunamadı]' varsa, çıktıda da bunu koru veya '(okunamadı)' olarak belirt. Asla yerine kelime uydurma.\n"
            "KURAL 5: Eğer metin zaten günümüz Türkçesi ise (sadece Arap harfleriyle yazılmışsa), metni Osmanlıca bir belgeymiş gibi ağırlaştırma, sade Türkçesini ver.\n\n"
            "Metin: {ottoman_text}\n"
            "Sade Türkçe Transliterasyon:"
        )

    def _call_llm(self, prompt: str, text: str, mode: str) -> str:
        """
        Internal function to call the configured local LLM.
        """
        if self.use_mock:
            return self._mock_response(text, mode)

        if self.provider is None:
            raise RuntimeError("OllamaProvider is not initialized for transliteration.")

        result = self.provider.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a source-faithful Ottoman Turkish transliteration engine. "
                        "Return only the Latin transliteration. Do not add historical claims, "
                        "summaries, dates, authors, institutions, or explanations."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.0,
            think=False,
        ).strip()

        if not result:
            raise RuntimeError("Ollama returned empty transliteration.")
        if result.strip() == (text or "").strip():
            raise RuntimeError("Transliteration failed: model returned the OCR source unchanged.")
        return result

    def _mock_response(self, text: str, mode: str) -> str:
        """Mock responses for testing the pipeline."""
        if "ياپدى گورديكم جنگله الماز قريشسنده" in text:
            if mode == "academic":
                return "Yāpdı gördügüm cengle alınmaz karşısında Kıluca ṭarafından bir"
            else:
                return "Yaptı gördüğüm cengle alınmaz karşısında Kıluca tarafından bir"
        elif "حواله ياپدى قرداش اوغلى اق تيمورى" in text:
            if mode == "academic":
                return "Ḥavāle yāpdı ḳarındaş oġlı Aḳ Tīmūr'ı üzerinde ḳodı ġāyet"
            else:
                return "Havale yaptı karındaş oğlu Ak Timur'u üzerinde kodu gayet"
        return f"[MOCK {mode.upper()}] {text}"

    def _call_llm_json(self, prompt: str, text: str, mode: str) -> dict:
        if self.use_mock:
            return {
                "orijinal_ocr_girdisi": text,
                "duzeltilmis_okunus": self._mock_response(text, mode),
                "guven_skoru": 100,
                "notlar": None
            }

        if self.provider is None:
            raise RuntimeError("OllamaProvider is not initialized for transliteration.")

        schema = {
            "type": "object",
            "properties": {
                "orijinal_ocr_girdisi": {"type": "string"},
                "duzeltilmis_okunus": {"type": "string"},
                "guven_skoru": {"type": "integer"},
                "notlar": {"type": "string"}
            },
            "required": ["duzeltilmis_okunus"]
        }

        try:
            result = self.provider.chat_json(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON-only Ottoman transliteration engine."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                schema=schema,
                temperature=0.0
            )
            return result
        except Exception as e:
            raise RuntimeError(f"Transliteration JSON failed: {e}")

    def transliterate_academic_json(self, ottoman_text: str) -> dict:
        """
        Converts Ottoman text to Academic Transcription format and returns strict JSON.
        """
        formatted_prompt = self.academic_prompt.format(ottoman_text=ottoman_text)
        return self._call_llm_json(formatted_prompt, ottoman_text, mode="academic")

    def transliterate_academic(self, ottoman_text: str) -> str:
        """
        Converts Ottoman text to Academic Transcription format.
        Maintains backward compatibility by returning just the string.
        """
        res = self.transliterate_academic_json(ottoman_text)
        return res.get("duzeltilmis_okunus", "")

    def transliterate_simple(self, ottoman_text: str) -> str:
        """
        Converts Ottoman text to Modern Standard Turkish alphabet format.
        """
        formatted_prompt = self.simple_prompt.format(ottoman_text=ottoman_text)
        return self._call_llm(formatted_prompt, ottoman_text, mode="simple")

