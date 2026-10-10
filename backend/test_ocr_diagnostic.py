import cv2
import numpy as np
import sys
import asyncio
import io
sys.path.insert(0, '.')

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

image = cv2.imread('backend/uploads/originals/1/pages/page_1.png')
print('Image shape: ' + str(image.shape))

from app.services.document_processing.preprocessor import ImagePreprocessor
preprocessor = ImagePreprocessor()
result = preprocessor.process(image)
processed = result[0]
params = result[1]

from app.services.document_processing.ocr_factory import create_ottoman_ocr_engine
engine = create_ottoman_ocr_engine()

async def run_ocr():
    page_result = await engine.extract(processed)
    print('Engine: ' + page_result.engine_name)
    print('Lines count: ' + str(len(page_result.lines)))
    print('Page confidence: ' + str(page_result.page_confidence))
    for i, line in enumerate(page_result.lines):
        print('  Line ' + str(i+1) + ': conf=' + str(round(line.confidence, 3)) + ' text=[' + line.text + ']')
        print('    bbox: ' + str(line.bbox))

asyncio.run(run_ocr())