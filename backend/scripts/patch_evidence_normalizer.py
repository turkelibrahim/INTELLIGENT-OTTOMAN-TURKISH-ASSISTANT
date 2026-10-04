from pathlib import Path

path = Path("app/services/document_intelligence_service.py")
text = path.read_text(encoding="utf-8")

old = '''        def normalize(value: str) -> str:
            return " ".join(
                value.lower().split()
            )
'''

new = '''        def normalize(value: str) -> str:
            value = value.strip()

            # LLM bazen evidence_quote etrafına yalnızca gösterim amaçlı
            # tırnak işaretleri ekleyebilir. İçerik değişmediği sürece
            # bunları kanıt doğrulamasında yok say.
            value = value.strip('\\\\\\"“”‘’')

            return " ".join(
                value.lower().split()
            )
'''

if old not in text:
    raise SystemExit("NORMALIZE_BLOCK_NOT_FOUND")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("EVIDENCE_QUOTE_NORMALIZER_PATCHED")
