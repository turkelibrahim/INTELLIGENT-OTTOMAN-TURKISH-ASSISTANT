import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class VisualEntityExtractor:
    """
    Extracts visual entities such as seals, signatures, tughras, stamps, and marginal notes.
    Currently, there is no specialized CV model for visual marks, so it returns 'not_assessed'.
    """

    def __init__(self):
        self.supported_types = ["SEAL", "SIGNATURE", "TUGHRA", "STAMP", "MARGINAL_NOTE"]

    def extract(self, image_path: str = "") -> Dict[str, Any]:
        logger.info(f"Visual entity extraction requested for {image_path}. No visual detector available.")
        
        entities = []
        for v_type in self.supported_types:
            entities.append({
                "entity_type": v_type,
                "value": "not_assessed",
                "normalized_value": "not_assessed",
                "status": "not_assessed",
                "confidence_score": 0.0,
                "bbox": None,
                "metadata": {
                    "note": "Visual detector is not implemented yet. Relying on text NER only."
                }
            })
            
        return {
            "entities": entities,
            "method_version": "visual-stub-v1",
            "confidence_score": 0.0
        }
