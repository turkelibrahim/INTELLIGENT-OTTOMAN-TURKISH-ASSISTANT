import cv2
import numpy as np
import sys
import asyncio
import io
import json
sys.path.insert(0, '.')

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.services.document_analysis_pipeline import DocumentAnalysisPipeline
from app.models.document import Document
from app.models.page import Page
from app.db.database import SessionLocal

async def run_full_analysis():
    # Load the test image
    image = cv2.imread('uploads/originals/1/pages/page_1.png')
    print('Image shape: ' + str(image.shape))
    
    # Create mock document and page
    document = Document()
    document.id = 1
    document.original_filename = 'page_1.png'
    document.page_count = 1
    
    page = Page()
    page.id = 1
    page.page_no = 1
    page.original_path = 'uploads/originals/1/pages/page_1.png'
    
    # Create pipeline
    pipeline = DocumentAnalysisPipeline()
    
    # Run analysis
    result = await pipeline.analyze_document(
        document=document,
        pages=[page],
        db=None,
        user_id=1
    )
    
    print('\n=== FULL ANALYSIS RESULT ===')
    print('Document: ' + str(result['document']))
    print('\nOCR Engine: ' + result['ocr']['engine'])
    print('OCR Confidence: ' + str(result['ocr']['confidence']))
    print('OCR Fallback Used: ' + str(result['ocr']['fallback_used']))
    print('OCR Lines Count: ' + str(len(result['ocr']['lines'])))
    
    print('\n=== OCR TEXT ===')
    print(result['ocr']['ottoman_text'])
    
    print('\n=== TRANSLITERATION ===')
    print('Latin Text: ' + result['transliteration']['latin_text'])
    print('Confidence: ' + str(result['transliteration']['confidence']))
    print('Method: ' + result['transliteration']['method'])
    print('Lines: ' + str(len(result['transliteration']['lines'])))
    for i, line in enumerate(result['transliteration']['lines'][:5]):
        print('  Line ' + str(i+1) + ': [' + line.get('latin_text', '') + ']')
    if len(result['transliteration']['lines']) > 5:
        print('  ... and ' + str(len(result['transliteration']['lines']) - 5) + ' more lines')
    
    print('\n=== MODERN TURKISH ===')
    print('Modern Text: ' + result['modern_turkish']['text'])
    print('Confidence: ' + str(result['modern_turkish']['confidence']))
    print('Provider: ' + result['modern_turkish']['provider'])
    print('Lines: ' + str(len(result['modern_turkish']['lines'])))
    for i, line in enumerate(result['modern_turkish']['lines'][:5]):
        print('  Line ' + str(i+1) + ': [' + line.get('modern_text', '') + ']')
    if len(result['modern_turkish']['lines']) > 5:
        print('  ... and ' + str(len(result['modern_turkish']['lines']) - 5) + ' more lines')
    
    print('\n=== HISTORICAL ANALYSIS ===')
    print('Document Type: ' + result['historical_analysis']['document_type'])
    print('Context: ' + result['historical_analysis']['historical_context'][:500])
    print('Confidence: ' + str(result['historical_analysis']['confidence']))
    
    print('\n=== CONFIDENCE ===')
    for k, v in result['confidence'].items():
        print('  ' + k + ': ' + str(v))
    
    print('\n=== WARNINGS ===')
    for w in result['warnings']:
        print('  - ' + w)
    
    print('\n=== UNCERTAINTIES ===')
    for u in result['uncertainties']:
        print('  - ' + u)
    
    # Save full result for inspection
    with open('backend/pipeline_test_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print('\nFull result saved to backend/pipeline_test_result.json')

asyncio.run(run_full_analysis())