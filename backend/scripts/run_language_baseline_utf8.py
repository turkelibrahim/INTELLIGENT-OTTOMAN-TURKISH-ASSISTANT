# -*- coding: utf-8 -*-

from app.services.document_processing.translator import Translator
from pathlib import Path
import json

t = Translator()

samples = [
    "كتاب",
    "مكتب",
    "دولت عليه عثمانيه",
    "بو كتاب",
    "بو كتابدر",
    "معلم",
    "اوقاف",
    "احمد بن محمد",
    "حواله ياپدى قرداش اوغلى اق تيمورى",
    "بسم الله الرحمن الرحيم"
]

results = []

print("=" * 80)
print("CURRENT OTTOMAN LANGUAGE BASELINE - UTF8")
print("=" * 80)

for i, source in enumerate(samples, 1):
    trans = t.transliterate_line(source)

    modern = t.modernize_ottoman_line(
        source,
        trans.transliterated_text,
        line_no=i
    )

    row = {
        "source": source,
        "source_repr": repr(source),
        "transliteration": trans.transliterated_text,
        "transliteration_confidence": trans.confidence,
        "transliteration_method": trans.method_version,
        "modern_turkish": modern.output_text,
        "modernization_provider": modern.provider,
        "modernization_confidence": modern.confidence,
        "warnings": modern.safety_warnings
    }

    results.append(row)

    print()
    print(f"[{i}]")
    print("SOURCE REPR :", repr(source))
    print("OSMANLICA   :", source)
    print("LATIN       :", trans.transliterated_text)
    print("MODERN      :", modern.output_text)
    print("T-CONFIDENCE:", trans.confidence)
    print("M-CONFIDENCE:", modern.confidence)
    print("T-METHOD    :", trans.method_version)
    print("M-PROVIDER  :", modern.provider)
    print("WARNINGS    :", modern.safety_warnings)

out = Path("evidence/language_intelligence_baseline/current_baseline_utf8.json")
out.parent.mkdir(parents=True, exist_ok=True)

out.write_text(
    json.dumps(results, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print()
print("=" * 80)
print("SAVED:", out)
print("=" * 80)
