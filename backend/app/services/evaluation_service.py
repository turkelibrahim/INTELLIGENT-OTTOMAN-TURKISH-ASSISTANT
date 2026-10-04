import jiwer
from typing import Dict, List, Union
from pydantic import BaseModel

class EvaluationResult(BaseModel):
    cer: float
    wer: float
    exact_match: bool
    reference: str
    hypothesis: str

class EvaluationService:
    """
    Model çıktılarını değerlendirmek için metrik servisi.
    """
    
    @staticmethod
    def evaluate_text(reference: str, hypothesis: str) -> EvaluationResult:
        """
        Referans metni ve tahmin edilen metni (hypothesis) karşılaştırır.
        CER (Character Error Rate) ve WER (Word Error Rate) hesaplar.
        """
        # Boş metin kontrolleri
        if not reference.strip() and not hypothesis.strip():
            return EvaluationResult(
                cer=0.0,
                wer=0.0,
                exact_match=True,
                reference=reference,
                hypothesis=hypothesis
            )
        
        if not reference.strip():
            return EvaluationResult(
                cer=1.0,
                wer=1.0,
                exact_match=False,
                reference=reference,
                hypothesis=hypothesis
            )
            
        if not hypothesis.strip():
            return EvaluationResult(
                cer=1.0,
                wer=1.0,
                exact_match=False,
                reference=reference,
                hypothesis=hypothesis
            )

        # WER hesapla
        wer = jiwer.wer(reference, hypothesis)
        
        # CER hesapla
        cer = jiwer.cer(reference, hypothesis)
        
        # Exact match
        exact_match = reference.strip() == hypothesis.strip()
        
        return EvaluationResult(
            cer=float(cer),
            wer=float(wer),
            exact_match=exact_match,
            reference=reference,
            hypothesis=hypothesis
        )
        
    @staticmethod
    def evaluate_batch(references: List[str], hypotheses: List[str]) -> Dict[str, float]:
        """
        Toplu değerlendirme yapar ve ortalama CER, WER değerlerini döndürür.
        """
        if len(references) != len(hypotheses):
            raise ValueError("References and hypotheses must have the same length.")
            
        if not references:
            return {"cer_mean": 0.0, "wer_mean": 0.0, "exact_match_ratio": 1.0}
            
        results = [
            EvaluationService.evaluate_text(ref, hyp) 
            for ref, hyp in zip(references, hypotheses)
        ]
        
        cer_mean = sum(r.cer for r in results) / len(results)
        wer_mean = sum(r.wer for r in results) / len(results)
        exact_match_ratio = sum(1 for r in results if r.exact_match) / len(results)
        
        return {
            "cer_mean": float(cer_mean),
            "wer_mean": float(wer_mean),
            "exact_match_ratio": float(exact_match_ratio)
        }
