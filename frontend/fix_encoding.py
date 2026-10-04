import os

replacements = {
    "Ã¼": "ü",
    "Ã¶": "ö",
    "Ã§": "ç",
    "Ä±": "ı",
    "ÅŸ": "ş",
    "ÄŸ": "ğ",
    "Ãœ": "Ü",
    "Ã–": "Ö",
    "Ã‡": "Ç",
    "Ä°": "İ",
    "Åž": "Ş",
    "Äž": "Ğ",
    "Ã¢": "â",
    "Ã®": "î",
    "Ã»": "û",
    "â€¦": "…",
    "â€”": "—",
}

def fix_encoding(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith((".ts", ".tsx", ".css")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    original_content = content
                    for bad, good in replacements.items():
                        content = content.replace(bad, good)
                    
                    if content != original_content:
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(content)
                        print(f"Fixed {filepath}")
                except Exception as e:
                    print(f"Failed {filepath}: {e}")

fix_encoding("src")
