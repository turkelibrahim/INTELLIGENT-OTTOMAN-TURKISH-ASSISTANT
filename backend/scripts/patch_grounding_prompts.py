from pathlib import Path

path = Path("app/services/document_intelligence_service.py")
text = path.read_text(encoding="utf-8-sig")

old_translate = '''self.translate_prompt = (
            "Sen uzman bir tarihçi ve dilbilimcisin. "
            "Görev: Sana verilen Latin harfli Osmanlıca/Eski Türkçe metnin tarihi bağlamını koruyarak, "
            "sadece arkaik ve eski kelimeleri günümüz modern Türkçesine çevir. "
            "Metnin ana kurgusunu bozma, metne yorum katma ve sadece çeviri çıktısı ver.\\n\\n"
            "Metin: {text}\\n"
            "Günümüz Türkçesi:"
        )'''

new_translate = '''self.translate_prompt = (
            "Görevin yalnızca verilen tarihî metni modern Türkçede daha anlaşılır hale getirmektir. "
            "KAYNAK METİN DIŞINDA HİÇBİR BİLGİ EKLEME. "
            "Kişi adlarını, yer adlarını, kurum adlarını ve tarihleri AYNEN KORU. "
            "Özel isimlerin yazımını değiştirme. "
            "Tarihsel bağlam tahmini yapma. "
            "Kaynakta olmayan kişi, olay, kurum, tarih veya yer ekleme. "
            "Emin olmadığın ifadeyi değiştirmek yerine koru. "
            "Sadece modernleştirilmiş metni döndür.\\n\\n"
            "KAYNAK METİN: {text}\\n"
            "MODERN TÜRKÇE:"
        )'''

old_summary = '''self.summarize_prompt = (
            "Sen uzman bir tarihçi ve arşivcisin. "
            "Görev: Sana verilen tarihi metnin ana konusunu ve bahsedilen olayı "
            "en fazla 3 cümle ile, tarafsız, net ve anlaşılır bir şekilde özetle. "
            "Yorum yapma.\\n\\n"
            "Metin: {text}\\n"
            "Özet:"
        )'''

new_summary = '''self.summarize_prompt = (
            "Yalnızca aşağıdaki KAYNAK METİN üzerinde çalış. "
            "Dış tarih bilgini KULLANMA. "
            "Kaynakta açıkça yazmayan hiçbir kişi, olay, tarih, yer, kurum veya tarihsel bağlam EKLEME. "
            "Çıkarım yapma. Tamamlama yapma. Tarihsel bilgi tahmin etme. "
            "Her özet iddiası kaynak metindeki açık bir ifadeye dayanmalıdır.\\n\\n"
            "KAYNAK METİN: {text}"
        )'''

if old_translate not in text:
    raise SystemExit("TRANSLATE_BLOCK_NOT_FOUND")

if old_summary not in text:
    raise SystemExit("SUMMARY_BLOCK_NOT_FOUND")

text = text.replace(old_translate, new_translate)
text = text.replace(old_summary, new_summary)

path.write_text(text, encoding="utf-8")

print("GROUNDING_PROMPTS_PATCHED")
