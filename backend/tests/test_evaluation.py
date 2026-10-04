import pytest
from app.services.evaluation.metrics import normalize_ottoman_text, calculate_metrics

def test_nfc_normalization():
    # Example string with decomposed characters
    text1 = "A\u030a"  # A + ring above
    norm = normalize_ottoman_text(text1)
    assert norm == "\u00c5" # Precomposed A with ring above
    
def test_tatweel_removal():
    text = "بـسـم" # With tatweel
    norm = normalize_ottoman_text(text)
    assert norm == "بسم" # Without tatweel

def test_whitespace_and_punctuation():
    text = "  Bu  bir,  deneme!  "
    norm = normalize_ottoman_text(text)
    assert norm == "Bu bir deneme"

def test_calculate_metrics_strict():
    gt = "Bu bir denemedir"
    hyp = "Bu bir denemedir"
    res = calculate_metrics(gt, hyp, strict=True)
    assert res["cer"] == 0.0
    assert res["wer"] == 0.0
    
def test_calculate_metrics_substitution():
    gt = "kelime"
    hyp = "kalima"
    res = calculate_metrics(gt, hyp, strict=True)
    assert res["substitutions"] == 2
    assert res["hits"] == 4
    
def test_calculate_metrics_insertion_deletion():
    gt = "osmanlica metin"
    hyp = "osmanlica yeni metin"
    res = calculate_metrics(gt, hyp, strict=True)
    assert res["insertions"] >= 1
    
    gt2 = "osmanlica eski metin"
    hyp2 = "osmanlica metin"
    res2 = calculate_metrics(gt2, hyp2, strict=True)
    assert res2["deletions"] >= 1

def test_evaluate_rtl():
    # Ensure RTL strings are compared correctly
    gt = "عثمانلیجه"
    hyp = "عتمانلیجه"
    res = calculate_metrics(gt, hyp, strict=True)
    assert res["cer"] > 0
    assert res["substitutions"] == 1
