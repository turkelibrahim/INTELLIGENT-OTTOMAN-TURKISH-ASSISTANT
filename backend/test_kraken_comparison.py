import cv2
import numpy as np
import sys
import asyncio
import io
sys.path.insert(0, '.')

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load the test image
image = cv2.imread('uploads/originals/1/pages/page_1.png')
print('Image shape: ' + str(image.shape))

from app.services.document_processing.preprocessor import ImagePreprocessor
preprocessor = ImagePreprocessor()
result = preprocessor.process(image)
processed = result[0]
params = result[1]

# Test with Kraken
from app.services.document_processing.ocr_engine import KrakenWSLEngine, OttomanOCREngine
from app.core.config import settings

async def test_kraken():
    print('\n=== TESTING KRAKEN ENGINE ===')
    try:
        kraken = KrakenWSLEngine(
            model_path=settings.OCR_KRAKEN_MODEL_PATH,
            model_sha256=settings.OCR_KRAKEN_MODEL_SHA256,
            distro=settings.OCR_KRAKEN_WSL_DISTRO,
            python_path=settings.OCR_KRAKEN_WSL_PYTHON
        )
        print('Kraken available: ' + str(kraken.available))
        if kraken.available:
            # Need segmenter first
            from app.services.document_processing.ocr_factory import create_ottoman_ocr_engine
            engine = create_ottoman_ocr_engine()
            if 'easyocr' in engine.engines:
                seg_result = await engine.engines['easyocr'].extract(processed)
                print('Segmenter lines: ' + str(len(seg_result.lines)))
                
                kraken_lines, elapsed = await kraken.extract_batch(processed, seg_result.lines)
                print('Kraken lines: ' + str(len(kraken_lines)))
                print('Elapsed: ' + str(elapsed) + ' ms')
                for i, line in enumerate(kraken_lines[:10]):
                    print('  Line ' + str(i+1) + ': conf=' + str(round(line.confidence, 3)) + ' text=[' + line.text + ']')
    except Exception as e:
        print('Kraken test failed: ' + str(e))
        import traceback
        traceback.print_exc()

asyncio.run(test_kraken())

# Also test EasyOCR on original vs preprocessed
print('\n=== EASYOCR ON ORIGINAL IMAGE ===')
from app.services.document_processing.ocr_engine import EasyOCREngine
easyocr_engine = EasyOCREngine(languages=['ar'], gpu=False)

async def test_easyocr_original():
    result = await easyocr_engine.extract(image)
    print('Original image - Lines: ' + str(len(result.lines)))
    print('Page confidence: ' + str(result.page_confidence))
    for i, line in enumerate(result.lines[:10]):
        print('  Line ' + str(i+1) + ': conf=' + str(round(line.confidence, 3)) + ' text=[' + line.text + ']')

asyncio.run(test_easyocr_original())

print('\n=== EASYOCR ON PREPROCESSED IMAGE ===')
async def test_easyocr_processed():
    result = await easyocr_engine.extract(processed)
    print('Processed image - Lines: ' + str(len(result.lines)))
    print('Page confidence: ' + str(result.page_confidence))
    for i, line in enumerate(result.lines[:10]):
        print('  Line ' + str(i+1) + ': conf=' + str(round(line.confidence, 3)) + ' text=[' + line.text + ']')

asyncio.run(test_easyocr_processed())