import unicodedata
import jiwer
import re
from typing import Dict, Any, List

def normalize_ottoman_text(text: str) -> str:
    """
    Applies NFC Unicode normalization and standardizes spaces/punctuation.
    - NFC normalization
    - Removes extra whitespaces
    - Standardizes Arabic tatweel and punctuation
    """
    if not text:
        return ""
    
    # 1. Unicode NFC Normalization
    text = unicodedata.normalize('NFC', text)
    
    # 2. Remove Tatweel (Kashida)
    text = text.replace('\u0640', '')
    
    # 3. Standardize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # 4. Standardize/Strip punctuation (optional, based on policy)
    # For now, we strip basic punctuation for normalized metrics to focus on character accuracy
    punctuation = r'[.,!?;:\'\"()\[\]{}؟،؛]'
    text = re.sub(punctuation, '', text)
    
    return text.strip()

def calculate_metrics(ground_truth: str, hypothesis: str, strict: bool = True) -> Dict[str, Any]:
    """
    Calculates CER (Character Error Rate) and WER (Word Error Rate).
    If strict=False, normalizes the text before calculation.
    """
    if not strict:
        ground_truth = normalize_ottoman_text(ground_truth)
        hypothesis = normalize_ottoman_text(hypothesis)
        
    if not ground_truth:
        return {
            "cer": 1.0 if hypothesis else 0.0,
            "wer": 1.0 if hypothesis else 0.0,
            "hits": 0,
            "substitutions": 0,
            "insertions": len(hypothesis),
            "deletions": 0,
            "total_chars": 0
        }
        
    try:
        # Character-level metrics using jiwer
        # Jiwer computes WER by default, to get CER we treat each character as a "word"
        gt_chars = " ".join(list(ground_truth))
        hyp_chars = " ".join(list(hypothesis))
        
        char_output = jiwer.process_words(gt_chars, hyp_chars)
        
        # Word-level metrics
        word_output = jiwer.process_words(ground_truth, hypothesis)
        
        return {
            "cer": char_output.wer, # wer on characters is CER
            "wer": word_output.wer,
            "hits": char_output.hits,
            "substitutions": char_output.substitutions,
            "insertions": char_output.insertions,
            "deletions": char_output.deletions,
            "total_chars": len(ground_truth),
            "total_words": len(ground_truth.split())
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error calculating metrics: {e}")
        return {
            "cer": 1.0,
            "wer": 1.0,
            "error": str(e)
        }

def evaluate_page(gt_lines: List[str], hyp_lines: List[str]) -> Dict[str, Any]:
    """
    Evaluates a full page by concatenating lines in reading order.
    RTL reading order must be handled before passing the lines here.
    """
    gt_full = "\n".join(gt_lines)
    hyp_full = "\n".join(hyp_lines)
    
    strict_metrics = calculate_metrics(gt_full, hyp_full, strict=True)
    norm_metrics = calculate_metrics(gt_full, hyp_full, strict=False)
    
    return {
        "strict": strict_metrics,
        "normalized": norm_metrics
    }
