import numpy as np
from typing import Dict, Any

from .preprocessor import ImagePreprocessor
from .ocr_factory import create_ottoman_ocr_engine
from .translator import Translator
from .ner_extractor import NERExtractor

PIPELINE_VERSION = "2.0.0"

class DocumentProcessingPipeline:
    """
    Belge işleme sürecini baştan sona yöneten orchestrator sınıfı.
    Preprocess -> OCR -> Translation -> NER adımlarını zincirler.
    """
    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.ocr_engine = create_ottoman_ocr_engine()
        self.translator = Translator()
        self.ner_extractor = NERExtractor()

    async def process_document(self, image: np.ndarray, job_id: str = "", document_id: str = "", page_id: str = "") -> Dict[str, Any]:
        """
        Tüm süreci çalıştırır ve nihai JSON cevabını (sözleşmeye uygun) oluşturur.
        """
        # 1. Image Preprocessing
        enhanced_image, preproc_scores = self.preprocessor.process(image)
        input_quality = preproc_scores.get("preprocessing_confidence", 0.0)
        
        # 2. Text Detection & OCR
        ocr_result = await self.ocr_engine.extract(enhanced_image)
        raw_ocr_text = "\n".join([line.text for line in ocr_result.lines])
        ocr_confidence = ocr_result.page_confidence
        
        # Quality Gate
        quality_gate = "PASS"
        if input_quality < 0.4 or ocr_confidence < 0.4:
            quality_gate = "LOW_QUALITY"
        if not raw_ocr_text.strip() or len(raw_ocr_text.strip()) < 2:
            quality_gate = "FAIL"
            
        # Basic nonsense check: if it's too much latin characters when it should be Arabic script
        arabic_chars = sum(1 for c in raw_ocr_text if '\u0600' <= c <= '\u06FF')
        if len(raw_ocr_text.strip()) > 5 and arabic_chars / len(raw_ocr_text) < 0.1:
            quality_gate = "LOW_QUALITY"
            
        # Format lines for UI bounding boxes
        ocr_lines = []
        for idx, line in enumerate(ocr_result.lines):
            ocr_lines.append({
                "id": f"line_{idx}",
                "page_id": str(page_id) if page_id else "",
                "text": line.text,
                "confidence": float(line.confidence),
                "bbox": {
                    "x": line.bbox[0],
                    "y": line.bbox[1],
                    "width": line.bbox[2],
                    "height": line.bbox[3]
                }
            })
        
        # 3. Transliteration & Translation
        if quality_gate != "FAIL" and quality_gate != "LOW_QUALITY":
            translation_results = await self.translator.translate(raw_ocr_text)
            transliterated = translation_results.get("transliterated_text", "")
            modernized = translation_results.get("modernized_text") or translation_results.get("translated_text", "")
            summary = translation_results.get("summary_text", "")
            normalized = translation_results.get("transliteration", {}).get("original_text", raw_ocr_text)
            transformation_flags = translation_results.get("quality_flags", [])
        else:
            transliterated = ""
            modernized = "SKIPPED_LOW_OCR_QUALITY"
            summary = ""
            normalized = raw_ocr_text
            transformation_flags = ["downstream_skipped_low_ocr_quality"]
        
        # 4. NER Extraction
        if quality_gate != "FAIL" and quality_gate != "LOW_QUALITY":
            ner_results = await self.ner_extractor.extract_entities(modernized)
            entities = ner_results.get("extracted_entities", [])
        else:
            entities = []
            
        model_metadata = ocr_result.model_metadata
        primary_engine = model_metadata.get("actual_engine", model_metadata.get("primary_engine", "unknown"))
        fallback_used = model_metadata.get("fallback_used", False)
        
        payload = {
            "job_id": str(job_id),
            "document_id": str(document_id),
            "page_id": str(page_id),
            "status": "COMPLETED" if quality_gate in ["PASS", "LOW_QUALITY"] else "FAILED",
            "pipeline_version": PIPELINE_VERSION,
            "worker_version": "",  # To be filled by worker
            "model_info": {
                "detector": "easyocr" if primary_engine == "trocr" else primary_engine,
                "recognizer": primary_engine,
                "model_revision": ocr_result.engine_version,
                "device": ocr_result.device,
                "fallback_used": fallback_used,
                "fallback_reason": model_metadata.get("fallback_reason", ""),
                "line_filter": model_metadata.get("line_filter", {})
            },
            "quality": {
                "input_quality": float(input_quality),
                "ocr_confidence": float(ocr_confidence),
                "quality_gate": quality_gate
            },
            "raw_ocr_text": raw_ocr_text,
            "normalized_ocr_text": normalized,
            "transliterated_text": transliterated,
            "modernized_text": modernized,
            "summary_text": summary,
            "entities": entities,
            "lines": ocr_lines,
            "errors": [],
            "warnings": [],
            "transformation_quality": {
                "flags": transformation_flags,
                "transliteration_distinct_from_ocr": transliterated.strip() != raw_ocr_text.strip(),
                "modernization_distinct_from_transliteration": modernized.strip() != transliterated.strip()
            }
        }
        
        if quality_gate == "LOW_QUALITY":
            payload["warnings"].append("Document input quality or OCR confidence is low.")
            
        return payload
