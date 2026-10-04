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

def verify():
    print("VERIFYING STAGE RECORDER")
    sample = "backend/uploads/originals/40/40_b52ad3bb.jpg"
    if not os.path.exists(sample):
        print(f"Sample not found: {sample}")
        return
        
    original_img = cv2.imread(sample)
    orig_hash = get_hash(original_img)
    print(f"Original hash before: {orig_hash}")
    
    preprocessor = ImagePreprocessor()
    res, params, score = preprocessor.process_with_profile(sample, "temiz_baski", 40, 1)
    
    orig_after_img = cv2.imread(sample)
    orig_after_hash = get_hash(orig_after_img)
    print(f"Original hash after: {orig_after_hash}")
    print(f"ORIGINAL_HASH_BEFORE == ORIGINAL_HASH_AFTER: {orig_hash == orig_after_hash}")
    
    manifest_path = "uploads/processed/40/page_1/processing_manifest.json"
    if not os.path.exists(manifest_path):
        print(f"Manifest not found at {manifest_path}")
        return
        
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
        
    print("MANIFEST INVENTORY:")
    hashes = []
    for stage in manifest['stages']:
        print(f"{stage['order']:02d} {stage['label']} - {stage['status']}")
        if stage['status'] == 'COMPLETED':
            img_path = os.path.join("uploads/processed/40/page_1", stage['file_name'])
            if not os.path.exists(img_path):
                print(f"ERROR: Artifact missing: {img_path}")
            else:
                img = cv2.imread(img_path)
                if img is None:
                    print(f"ERROR: Artifact decode failed: {img_path}")
                else:
                    h = get_hash(img)
                    hashes.append(h)
                    print(f"   -> Valid image: {img.shape}, hash: {h[:8]}")
    
    if len(set(hashes)) == 1:
        print("WARNING: All hashes identical, transformations might be skipped!")
        
verify()
