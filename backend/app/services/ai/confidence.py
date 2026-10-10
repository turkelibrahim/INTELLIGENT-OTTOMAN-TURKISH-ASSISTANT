from typing import Dict, Any, List

def calculate_risk(
    ocr_uncertainty: float,
    character_anomaly: float,
    language_uncertainty: float,
    local_model_disagreement: float,
    rag_disagreement: float,
    translation_uncertainty: float,
    metadata_uncertainty: float
) -> float:
    """Calculates risk based on multiple signals. Returns 0.0 to 1.0"""
    risk = (
        0.25 * ocr_uncertainty +
        0.15 * character_anomaly +
        0.15 * language_uncertainty +
        0.15 * local_model_disagreement +
        0.10 * rag_disagreement +
        0.10 * translation_uncertainty +
        0.10 * metadata_uncertainty
    )
    return min(1.0, max(0.0, risk))

def calculate_confidence(risk: float) -> float:
    return 1.0 - risk

def determine_route(confidence: float) -> str:
    """
    Determines route: 
    LOCAL ONLY if confidence >= 0.75
    VERIFICATION if 0.50 <= confidence < 0.75
    DEEPSEEK if confidence < 0.50
    """
    if confidence >= 0.75:
        return "local_only"
    elif confidence >= 0.50:
        return "selective_verification"
    else:
        return "nvidia_deepseek"
