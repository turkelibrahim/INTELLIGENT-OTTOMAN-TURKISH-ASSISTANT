import cv2
import numpy as np
from typing import List, Dict, Any
from app.services.evaluation.metrics import evaluate_page
from app.services.document_processing.ocr_engine import OttomanOCREngine

def preprocess_grayscale(image: np.ndarray) -> np.ndarray:
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image

def preprocess_clahe(image: np.ndarray) -> np.ndarray:
    gray = preprocess_grayscale(image)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)

def preprocess_denoise(image: np.ndarray) -> np.ndarray:
    # fastNlMeansDenoising expects grayscale
    gray = preprocess_grayscale(image)
    return cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

def preprocess_threshold(image: np.ndarray) -> np.ndarray:
    gray = preprocess_grayscale(image)
    # Otsu's thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def preprocess_best_profile(image: np.ndarray) -> np.ndarray:
    # Combining operations for the 'best' profile
    gray = preprocess_grayscale(image)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    denoised = cv2.fastNlMeansDenoising(clahe, None, 10, 7, 21)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

# Dictionary of available preprocessing profiles
PREPROCESSING_PROFILES = {
    "none": lambda img: img,
    "grayscale": preprocess_grayscale,
    "clahe": preprocess_clahe,
    "denoise": preprocess_denoise,
    "threshold": preprocess_threshold,
    "best_profile": preprocess_best_profile
}

async def run_preprocessing_ablation(
    engine: OttomanOCREngine, 
    image: np.ndarray, 
    ground_truth_lines: List[str]
) -> List[Dict[str, Any]]:
    """
    Runs the image through multiple preprocessing profiles and evaluates CER/WER against the ground truth.
    """
    results = []
    
    for profile_name, preprocessor in PREPROCESSING_PROFILES.items():
        try:
            processed_image = preprocessor(image.copy())
            
            # Run OCR
            ocr_result = await engine.extract(processed_image)
            hyp_lines = [line.text for line in sorted(ocr_result.lines, key=lambda x: x.line_index)]
            
            metrics = evaluate_page(ground_truth_lines, hyp_lines)
            
            results.append({
                "profile": profile_name,
                "metrics": metrics,
                "lines_detected": len(hyp_lines),
                "page_confidence": ocr_result.page_confidence,
                "error": None
            })
        except Exception as e:
            results.append({
                "profile": profile_name,
                "error": str(e)
            })
            
    return results
