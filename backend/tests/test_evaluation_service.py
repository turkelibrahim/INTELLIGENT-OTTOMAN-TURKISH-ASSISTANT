from app.services.evaluation_service import EvaluationService

def test_evaluation_service_exact_match():
    ref = "bu bir test metnidir"
    hyp = "bu bir test metnidir"
    
    result = EvaluationService.evaluate_text(ref, hyp)
    
    assert result.exact_match is True
    assert result.cer == 0.0
    assert result.wer == 0.0

def test_evaluation_service_with_errors():
    ref = "bu bir test metnidir"
    hyp = "bu bir test metn" # 'idir' eksik
    
    result = EvaluationService.evaluate_text(ref, hyp)
    
    assert result.exact_match is False
    assert result.cer > 0.0
    assert result.wer > 0.0

def test_evaluation_batch():
    refs = ["merhaba dunya", "test bir iki ucb"]
    hyps = ["merhaba dunya", "test bir iki uc"]
    
    results = EvaluationService.evaluate_batch(refs, hyps)
    
    assert results["exact_match_ratio"] == 0.5
    assert results["cer_mean"] > 0.0
    assert results["wer_mean"] > 0.0
