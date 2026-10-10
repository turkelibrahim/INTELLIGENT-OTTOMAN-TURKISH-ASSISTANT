import asyncio
from pathlib import Path
from app.models.document import Document
from app.models.page import Page
from app.services.document_analysis_pipeline import DocumentAnalysisPipeline
import json

async def main():
    pipeline = DocumentAnalysisPipeline()
    doc = Document(id=9, original_filename='page_1.png', page_count=1)
    page = Page(id=1, document_id=9, page_no=1, original_path='uploads/originals/9/pages/page_1.png')
    res = await pipeline._process_page(page, db=None, document=doc, user_id=1)
    
    latin_text, transliteration_confidence, _ = pipeline._transliterate(res['ocr_text'])
    modern_text, modern_confidence, _ = pipeline._modernize(latin_text)
    
    t_lines, m_lines, _ = pipeline._line_transformations(
        res['lines'], latin_text=latin_text, modern_text=modern_text
    )
    
    out = {
        'ocr_lines': [l['ocr_text'] for l in res['lines']],
        'latin_lines': [l['latin_text'] for l in t_lines],
        'modern_lines': [l['modern_text'] for l in m_lines]
    }
    with open('benchmark_output.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

asyncio.run(main())
