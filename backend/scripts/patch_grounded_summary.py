from pathlib import Path

path = Path("app/services/document_intelligence_service.py")
text = path.read_text(encoding="utf-8")

old = '''    def summarize_document(self, full_text: str) -> str:
        formatted_prompt = self.summarize_prompt.format(text=full_text)
        return self._call_llm(
            formatted_prompt,
            full_text,
            mode="summarize"
        )
'''

new = '''    def summarize_document(self, full_text: str) -> str:
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
'''

if old not in text:
    raise SystemExit("SUMMARIZE_FUNCTION_NOT_FOUND")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("GROUNDED_SUMMARY_VALIDATOR_INSTALLED")
