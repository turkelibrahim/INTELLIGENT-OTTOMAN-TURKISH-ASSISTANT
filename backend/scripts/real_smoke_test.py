import asyncio
import os
import sys
import numpy as np
import cv2
import json

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.services.document_processing.ocr_factory import create_ottoman_ocr_engine

async def main():
    print("Starting REAL Smoke Test for Kraken OCR...")
    engine = create_ottoman_ocr_engine()
    
    print("Engine created. Primary Engine:", engine._primary_engine)
    if engine._primary_engine != "kraken":
        print("FAIL: Primary engine is not kraken.")
        sys.exit(1)
        
    print("Generating synthetic test image with Arabic text...")
    # Create an image that EasyOCR will detect lines on
    # White background, Arabic text
    from PIL import Image, ImageDraw, ImageFont
    
    img_pil = Image.new('RGB', (800, 400), color=(255, 255, 255))
    d = ImageDraw.Draw(img_pil)
    # Use default font but draw some lines that look like text to a naive segmenter, or just basic text
    d.text((100, 100), "سلام دنیا", fill=(0, 0, 0))
    d.text((100, 200), "مرحبا بكم", fill=(0, 0, 0))
    d.text((100, 300), "This is a test", fill=(0, 0, 0))
    
    img = np.array(img_pil)
    
    # If EasyOCR still fails, we will mock it just for the smoke test to ensure Kraken is invoked.
    # We want to test the Kraken WSL Bridge primarily.
    
    print("Running extraction (This will invoke EasyOCR for segmentation, then Kraken via WSL for recognition)...")
    result = await engine.extract(img)
    
    print("Extraction complete.")
    print(f"Lines found: {len(result.lines)}")
    print(f"Primary Engine reported in metadata: {result.model_metadata.get('primary_engine')}")
    print(f"Actual Engine reported in metadata: {result.model_metadata.get('actual_engine')}")
    print(f"Fallback used: {result.model_metadata.get('fallback_used')}")
    if result.model_metadata.get('fallback_used'):
        print(f"Fallback reason: {result.model_metadata.get('fallback_reason')}")
        print("FAIL: Fallback was triggered instead of Kraken.")
        sys.exit(1)
        
    if result.model_metadata.get("actual_engine") != "kraken":
        print("FAIL: actual_engine is not kraken.")
        sys.exit(1)
        
    print("SMOKE TEST PASS")
    
    # Dump result metadata for evidence
    with open("kraken_smoke_metadata.json", "w", encoding="utf-8") as f:
        json.dump(result.model_metadata, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
