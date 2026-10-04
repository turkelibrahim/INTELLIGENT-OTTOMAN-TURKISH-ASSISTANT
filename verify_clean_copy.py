import sys
import os
import cv2
import json
import hashlib
import numpy as np

sys.path.insert(0, os.path.abspath('backend'))
from app.services.document_processing.preprocessor import ImagePreprocessor

def get_hash(img):
    if img is None: return None
    return hashlib.sha256(img.tobytes()).hexdigest()

def get_luminance_stats(img):
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    return np.mean(gray), np.std(gray)

def verify():
    print("VERIFYING CLEAN DIGITAL COPY GENERATION")
    
    sample = "backend/uploads/originals/40/40_b52ad3bb.jpg"
    if not os.path.exists(sample):
        print(f"Sample not found: {sample}")
        return
        
    original_img = cv2.imread(sample)
    orig_hash = get_hash(original_img)
    orig_mean, orig_std = get_luminance_stats(original_img)
    print(f"Original hash: {orig_hash}")
    print(f"Original luminance mean: {orig_mean:.2f}, std: {orig_std:.2f}")
    
    preprocessor = ImagePreprocessor()
    res, params, score = preprocessor.process_with_profile(sample, "temiz_baski", 40, 1)
    
    manifest_path = "uploads/processed/40/page_1/processing_manifest.json"
    if not os.path.exists(manifest_path):
        print(f"Manifest not found at {manifest_path}")
        return
        
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
        
    ocr_safe_path = None
    clean_copy_path = None
    
    for stage in manifest['stages']:
        if stage['status'] == 'COMPLETED':
            path = os.path.join("uploads/processed/40/page_1", stage['file_name'])
            if stage['ocr_safe']:
                ocr_safe_path = path
            if stage['is_clean_copy']:
                clean_copy_path = path
                
    if not ocr_safe_path or not clean_copy_path:
        print("Missing required artifacts!")
        return
        
    ocr_img = cv2.imread(ocr_safe_path)
    clean_img = cv2.imread(clean_copy_path)
    
    ocr_hash = get_hash(ocr_img)
    clean_hash = get_hash(clean_img)
    
    clean_mean, clean_std = get_luminance_stats(clean_img)
    
    print(f"OCR Safe hash: {ocr_hash}")
    print(f"Clean Copy hash: {clean_hash}")
    print(f"Clean Copy luminance mean: {clean_mean:.2f}, std: {clean_std:.2f}")
    
    print("\n--- VALIDATION ---")
    
    if orig_hash == clean_hash:
        print("FAIL: Clean copy is identical to original!")
    else:
        print("PASS: Clean copy is different from original.")
        
    if ocr_hash == clean_hash:
        print("FAIL: Clean copy is identical to OCR Safe!")
    else:
        print("PASS: Clean copy is different from OCR Safe.")
        
    if clean_mean > orig_mean:
        print("PASS: Clean copy is brighter on average.")
    else:
        print("FAIL: Clean copy is darker or equal to original.")
        
    # Calculate Mean Absolute Error
    if original_img.shape == clean_img.shape:
        mae = np.mean(np.abs(original_img.astype(np.int16) - clean_img.astype(np.int16)))
        print(f"Mean Absolute Pixel Difference (MAE): {mae:.2f}")
    else:
        print("Image shapes changed, cannot compute MAE directly.")
        
    os.makedirs('evidence/clean_digital_copy_gate', exist_ok=True)
    with open('evidence/clean_digital_copy_gate/original_hash.txt', 'w') as f:
        f.write(orig_hash)
    with open('evidence/clean_digital_copy_gate/ocr_safe_hash.txt', 'w') as f:
        f.write(ocr_hash)
    with open('evidence/clean_digital_copy_gate/clean_copy_hash.txt', 'w') as f:
        f.write(clean_hash)
        
    # Write report
    report = {
        "original_luminance": {"mean": orig_mean, "std": orig_std},
        "clean_luminance": {"mean": clean_mean, "std": clean_std},
        "artifacts_separated": orig_hash != clean_hash and ocr_hash != clean_hash,
        "mae": float(mae) if original_img.shape == clean_img.shape else None
    }
    with open('evidence/clean_digital_copy_gate/visual_difference.json', 'w') as f:
        json.dump(report, f, indent=2)
        
    cv2.imwrite('evidence/clean_digital_copy_gate/01_original.png', original_img)
    cv2.imwrite('evidence/clean_digital_copy_gate/02_ocr_safe.png', ocr_img)
    cv2.imwrite('evidence/clean_digital_copy_gate/03_clean_digital_copy.png', clean_img)
        
    print("Verification completed successfully. Check evidence/clean_digital_copy_gate/")
    
verify()
