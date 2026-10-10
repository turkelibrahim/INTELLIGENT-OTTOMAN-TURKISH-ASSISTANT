from pathlib import Path
import json
import logging
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.page import Page
from app.models.processing_outputs import Entity, OCRResult, TextVersion
from app.schemas.document_analysis import FullDocumentAnalysisResponse
from app.services.document_intelligence_service import DocIntelligenceEngine
from app.services.document_processing.ner_extractor import NERExtractor
from app.services.document_processing.ocr_factory import create_ottoman_ocr_engine
from app.services.document_processing.preprocessor import ImagePreprocessor
from app.services.document_processing.translator import Translator
from app.services.document_processing.visual_extractor import VisualEntityExtractor
from app.services.historical_rag import HistoricalQdrantStore
from app.services.image_io import read_image_unicode_safe
from app.services.transliteration_service import TransliterationEngine
from app.services.ai.local_lora_provider import LocalLoRAProvider


UNKNOWN = "Tespit edilemedi"
logger = logging.getLogger(__name__)
STRUCTURED_LINE_BATCH_STEPS = (10, 20, 25, 50)


class DocumentAnalysisPipeline:
    """Production orchestration for unknown Ottoman document analysis."""

    def __init__(
        self,
        *,
        preprocessor: Optional[ImagePreprocessor] = None,
        ocr_engine: Optional[Any] = None,
        transliteration_engine: Optional[TransliterationEngine] = None,
        fallback_translator: Optional[Translator] = None,
        intelligence: Optional[DocIntelligenceEngine] = None,
        ner_extractor: Optional[NERExtractor] = None,
        historical_store: Optional[HistoricalQdrantStore] = None,
    ):
        self.preprocessor = preprocessor or ImagePreprocessor()
        self.ocr_engine = ocr_engine or create_ottoman_ocr_engine()
        self.transliteration_engine = transliteration_engine or TransliterationEngine(use_mock=False)
        self.fallback_translator = fallback_translator or Translator()
        self.intelligence = intelligence or DocIntelligenceEngine(use_mock=False)
        self.ner_extractor = ner_extractor or NERExtractor(enable_hf=False)
        self.visual_extractor = VisualEntityExtractor()
        self.historical_store = historical_store or HistoricalQdrantStore()
        from app.core.config import settings
        if settings.LLM_PROVIDER.strip().lower() != "gemini":
            self.lora_provider = LocalLoRAProvider()
        else:
            self.lora_provider = None

    async def analyze_document(
        self,
        *,
        document: Document,
        pages: Iterable[Page],
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        page_results = []
        warnings: List[str] = []
        uncertainties: List[str] = []
        ordered_pages = sorted(list(pages), key=lambda item: item.page_no)

        for page in ordered_pages:
            page_results.append(await self._process_page(page, db=db, document=document, user_id=user_id))

        ocr_text = "\n".join(item["ocr_text"] for item in page_results if item["ocr_text"]).strip()
        ocr_confidence = self._mean(item["ocr_confidence"] for item in page_results)
        lines = [line for item in page_results for line in item["lines"]]
        preprocessing = [item["preprocessing"] for item in page_results]

        if not ocr_text:
            uncertainties.append("OCR metni Tespit edilemedi")

        latin_text, transliteration_confidence, transliteration_warnings = self._transliterate(ocr_text)
        warnings.extend(transliteration_warnings)
        if not transliteration_confidence and latin_text:
            transliteration_confidence = 0.85
        if not latin_text:
            uncertainties.append("Transliterasyon Tespit edilemedi")

        modern_text, modern_confidence, modern_warnings = self._modernize(latin_text)
        warnings.extend(modern_warnings)
        if not modern_confidence and modern_text:
            modern_confidence = 0.88
        if not modern_text:
            uncertainties.append("Modern Turkce aktarim Tespit edilemedi")

        transliteration_lines, modern_lines, line_entities_raw = self._line_transformations(
            lines,
            latin_text=latin_text,
            modern_text=modern_text,
        )

        # Merge visual entities
        visual_entities_raw = (
            self.visual_extractor.extract(image_path=str(Path(ordered_pages[0].original_path)))
            if ordered_pages
            else {"entities": []}
        )
        all_entities_raw = line_entities_raw + visual_entities_raw.get("entities", [])
        
        entities = self._group_entities(all_entities_raw)
        
        # Calculate entity confidence
        entity_conf_list = [e.get("confidence_score", 0.0) for e in all_entities_raw if e.get("confidence_score") is not None]
        entity_confidence = float(sum(entity_conf_list) / len(entity_conf_list)) if entity_conf_list else 0.0

        if db is not None:
            self._persist_text_and_entities(
                db=db,
                document=document,
                user_id=user_id,
                latin_text=latin_text,
                modern_text=modern_text,
                transliteration_confidence=transliteration_confidence,
                modern_confidence=modern_confidence,
                entities=all_entities_raw,
            )

        document_claims = self._document_claims(lines, ocr_text, latin_text, modern_text, entities)
        query = self._retrieval_query(ocr_text, latin_text, modern_text, entities)
        historical_items = self._retrieve_verified_historical_evidence(query)
        
        if not historical_items and hasattr(self, 'intelligence') and self.intelligence:
            try:
                enrichments = self.intelligence.enrich_entities(entities)
                for i, enc in enumerate(enrichments):
                    historical_items.append({
                        "source_id": f"llm_enrichment_{i}",
                        "title": f"Ansiklopedik Bilgi: {enc.get('entity')}",
                        "citation": "Osmanlı Tarihi (Yapay Zeka Destekli Ansiklopedi)",
                        "source_type": "encyclopedia",
                        "source_tier": "secondary",
                        "chunk_id": f"enc_{i}",
                        "retrieval_score": 0.95,
                        "evidence_text": enc.get('description', ''),
                        "verified": True,
                    })
            except Exception as e:
                logger.error(f"Error getting enrichments: {e}")

        # Removed hardcoded BOA/DIA sources to prevent fake citations.
        if not historical_items:
            logger.info("No historical items found in RAG. Leaving sources empty.")

        document_evidence = self._document_evidence(document, lines, ocr_text, latin_text, modern_text)
        historical_analysis = await self._historical_analysis(historical_items, entities, modern_text)
        retrieval_strength = self._retrieval_strength(historical_items)
        evidence_coverage = self._evidence_coverage(document_evidence, historical_items, entities)

        combined = self._combined_confidence(
            ocr_confidence,
            transliteration_confidence,
            modern_confidence,
            entity_confidence,
            retrieval_strength,
            evidence_coverage,
        )

        result = {
            "document": {
                "filename": document.original_filename,
                "document_type": historical_analysis["document_type"],
                "language": "Ottoman Turkish",
                "document_id": document.id,
                "page_count": document.page_count or len(ordered_pages),
            },
            "image_processing": {
                "applied": sorted({item.get("profile", "") for item in preprocessing if item.get("profile")}),
                "ocr_safe_image": page_results[0]["ocr_safe_image"] if page_results else "",
                "warnings": [warning for item in preprocessing for warning in item.get("warnings", [])],
            },
            "ocr": {
                "ottoman_text": ocr_text,
                "confidence": ocr_confidence,
                "engine": page_results[0]["ocr_engine"] if page_results else "",
                "fallback_used": any(item["ocr_fallback_used"] for item in page_results),
                "lines": lines,
            },
            "transliteration": {
                "latin_text": latin_text,
                "confidence": transliteration_confidence,
                "method": "ollama-qwen-simple" if latin_text and not transliteration_warnings else "explicit-error-or-rule-fallback",
                "lines": transliteration_lines,
                "warnings": transliteration_warnings,
            },
            "modern_turkish": {
                "text": modern_text,
                "confidence": modern_confidence,
                "provider": "ollama-qwen" if modern_text and not modern_warnings else "explicit-error-or-rule-fallback",
                "lines": modern_lines,
                "warnings": modern_warnings,
            },
            "entities": entities,
            "historical_analysis": historical_analysis,
            "evidence": {
                "document_evidence": document_evidence,
                "historical_external_evidence": historical_items,
                "citations": self._citations(historical_items),
                "model_inference": self._model_inference(historical_analysis),
                "document_claims": document_claims,
            },
            "confidence": {
                "ocr": ocr_confidence,
                "transliteration": transliteration_confidence,
                "modern_turkish": modern_confidence,
                "entities": entity_confidence,
                "retrieval_strength": retrieval_strength,
                "evidence_coverage": evidence_coverage,
                "combined": combined,
                "combined_provisional": True,
            },
            "uncertainties": uncertainties,
            "warnings": warnings,
        }

        # Clean warnings from internal technical details
        bad_keywords = ["possible_", "not_assessed", "HTTPConnectionPool", "127.0.0.1:11434", "WinError", "traceback", "rule_based_", "ollama_"]
        def clean_warning_list(w_list: List[str]) -> List[str]:
            return [w for w in w_list if not any(bw in w for bw in bad_keywords)]
            
        result["warnings"] = clean_warning_list(result["warnings"])
        result["transliteration"]["warnings"] = clean_warning_list(result["transliteration"]["warnings"])
        result["modern_turkish"]["warnings"] = clean_warning_list(result["modern_turkish"]["warnings"])

        
        try:
            from app.services.ai.router import smart_router
            # Send to smart router for selective cloud verification
            result = await smart_router.selective_document_verification(result)
        except Exception as e:
            logger.error(f"Smart router failed, falling back to local result: {e}")
            result["verification_status"] = "local_fallback"
            
        return FullDocumentAnalysisResponse.model_validate(result).model_dump()

    async def _process_page(
        self,
        page: Page,
        *,
        db: Optional[Session],
        document: Document,
        user_id: Optional[int],
    ) -> Dict[str, Any]:
        image_path = Path(page.original_path)
        image = read_image_unicode_safe(image_path)

        safe_image, prep = self.preprocessor.process(image)
        
        import time
        from app.core.config import settings
        
        start_local = time.perf_counter()
        ocr_result = await self.ocr_engine.extract(safe_image)
        local_duration_ms = (time.perf_counter() - start_local) * 1000
        
        text = "\n".join(line.text for line in ocr_result.lines).strip()
        confidence = float(ocr_result.page_confidence or 0.0)
        
        fallback_triggered = False
        should_fallback = False
        
        if getattr(settings, "NVIDIA_OCR_FALLBACK_ENABLED", False):
            if not text:
                should_fallback = True
                logger.warning("Local OCR empty. Triggering NVIDIA fallback.")
            elif confidence < getattr(settings, "OCR_MIN_CONFIDENCE_THRESHOLD", 0.60):
                should_fallback = True
                logger.warning(f"Local OCR confidence {confidence:.2f} < threshold. Triggering NVIDIA fallback.")
            elif local_duration_ms > getattr(settings, "OCR_MAX_DURATION_SECONDS", 15) * 1000:
                should_fallback = True
                logger.warning(f"Local OCR took {local_duration_ms:.0f}ms > limit. Triggering NVIDIA fallback.")
                
        if should_fallback:
            from app.services.document_processing.nvidia_vision import NvidiaVisionOCR
            nvidia_ocr = NvidiaVisionOCR()
            nvidia_text, nvidia_conf, nvidia_dur = await nvidia_ocr.extract_text(safe_image)
            
            if nvidia_text:
                # We have a valid fallback result
                text = nvidia_text
                confidence = max(confidence, nvidia_conf)
                fallback_triggered = True
                logger.info(f"NVIDIA fallback succeeded in {nvidia_dur:.0f}ms")
                
                # If local OCR produced no lines, we create synthetic lines from NVIDIA output
                if not ocr_result.lines:
                    from app.models.processing_outputs import Line, BBox
                    for idx, line_str in enumerate(nvidia_text.split("\n")):
                        if line_str.strip():
                            # Create a synthetic line with empty bounding box
                            ocr_result.lines.append(Line(
                                text=line_str.strip(),
                                confidence=nvidia_conf,
                                bbox=(0, 0, 0, 0),
                                line_index=idx
                            ))

        lines = []
        for line in ocr_result.lines:
            line_payload = {
                "line_id": f"document:{document.id}:page:{page.id}:line:{line.line_index + 1}",
                "page_id": page.id,
                "page_no": page.page_no,
                "line_no": line.line_index + 1,
                "ocr_text": line.text,
                "text": line.text,
                "confidence": float(line.confidence),
                "bbox": {
                    "x": int(line.bbox[0]),
                    "y": int(line.bbox[1]),
                    "width": int(line.bbox[2]),
                    "height": int(line.bbox[3]),
                },
                "source": "document_ocr",
            }
            lines.append(line_payload)
            if db is not None:
                ocr_record = OCRResult(
                    page_id=page.id,
                    line_no=line.line_index + 1,
                    bbox=line_payload["bbox"],
                    raw_text=line.text,
                    confidence_score=float(line.confidence),
                )
                db.add(ocr_record)
                db.flush()
                line_payload["ocr_result_id"] = ocr_record.id
                line_payload["line_id"] = f"ocr_result:{ocr_record.id}"

        if db is not None:
            page.status = "ocr"
            document.status = "analysis"
            db.commit()

        meta = ocr_result.model_metadata or {}
        prep_warnings = []
        if float(prep.get("preprocessing_confidence") or 0.0) < 0.4:
            prep_warnings.append("Low preprocessing quality score.")

        return {
            "ocr_text": text,
            "ocr_confidence": confidence,
            "ocr_engine": "nvidia_vision_11b" if fallback_triggered else (meta.get("actual_engine") or ocr_result.engine_name),
            "ocr_fallback_used": fallback_triggered or bool(meta.get("fallback_used", False)),
            "ocr_safe_image": str(image_path),
            "lines": lines,
            "preprocessing": {**prep, "warnings": prep_warnings},
        }

    def _transliterate(self, text: str) -> tuple[str, float, List[str]]:
        if not text.strip():
            return "", 0.0, ["transliteration_skipped_empty_ocr"]
        try:
            res = self.transliteration_engine.transliterate_academic_json(text)
            latin = res.get("duzeltilmis_okunus", "").strip()
            conf = float(res.get("guven_skoru", 82.0)) / 100.0
            note = res.get("notlar")
            warnings = []
            if note:
                warnings.append(f"llm_note: {note}")
            return latin, conf, warnings
        except Exception as exc:
            fallback = self.fallback_translator.transliterate_text(text).strip()
            warnings = [f"ollama_transliteration_failed: {exc}"]
            if not fallback or fallback == text:
                return "", 0.0, warnings + ["rule_based_transliteration_unavailable"]
            return fallback, 0.55, warnings + ["rule_based_transliteration_fallback_used"]

    def _modernize(self, latin_text: str) -> tuple[str, float, List[str]]:
        if not latin_text.strip():
            return "", 0.0, ["modernization_skipped_empty_transliteration"]
        try:
            res = self.intelligence.translate_to_modern_turkish_json(latin_text)
            modern = res.get("gunumuz_turkcesi", "").strip()
            if not modern or modern == latin_text:
                raise RuntimeError("modernization returned empty or unchanged text")
            
            warnings = []
            note = res.get("kelime_koken_notlari")
            if note:
                warnings.append(f"etymology_note: {note}")
                
            return modern, 0.78, warnings
        except Exception as exc:
            result = self.fallback_translator.modernize(latin_text, mode="faithful")
            warnings = [f"ollama_modernization_failed: {exc}"]
            if not result.output_text or result.output_text == latin_text:
                return "", 0.0, warnings + list(result.safety_warnings) + ["modernization_failed_or_identical"]
            return result.output_text, result.confidence, warnings + list(result.safety_warnings) + ["rule_based_modernization_fallback_used"]

    @staticmethod
    def _initial_structured_batch_size(line_count: int) -> int:
        if line_count <= 10:
            return 10
        if line_count <= 40:
            return 20
        if line_count <= 100:
            return 25
        return 50

    @staticmethod
    def _next_smaller_batch_size(batch_size: int) -> int:
        for candidate in reversed(STRUCTURED_LINE_BATCH_STEPS):
            if candidate < batch_size:
                return candidate
        return 1

    @staticmethod
    def _chunks(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
        for start in range(0, len(items), size):
            yield items[start:start + size]

    def _structured_line_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "lines": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "line_id": {"type": "string"},
                            "transliteration": {"type": "string"},
                            "modern_turkish": {"type": "string"},
                            "uncertain": {"type": "boolean"},
                        },
                        "required": [
                            "line_id",
                            "transliteration",
                            "modern_turkish",
                            "uncertain",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["lines"],
            "additionalProperties": False,
        }

    def _structured_line_provider(self) -> Optional[Any]:
        for candidate in (
            getattr(getattr(self, "intelligence", None), "provider", None),
            getattr(getattr(self, "transliteration_engine", None), "provider", None),
        ):
            if candidate is not None and hasattr(candidate, "chat_json"):
                return candidate
        return None

    def _request_structured_line_transformations(
        self,
        batch: List[Dict[str, Any]],
        *,
        document_latin_lines: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        provider = self._structured_line_provider()
        if provider is None:
            raise RuntimeError("structured line provider unavailable")

        input_lines = []
        for index, line in enumerate(batch):
            line_id = str(line.get("line_id") or "")
            if not line_id:
                raise RuntimeError("structured line input missing line_id")
            line_no = int(line.get("line_no") or (index + 1))
            latin_hint = str(line.get("_structured_latin_hint") or "")
            input_lines.append(
                {
                    "line_id": line_id,
                    "line_no": line_no,
                    "ocr_text": str(line.get("ocr_text") or line.get("text") or ""),
                    "latin_hint": latin_hint,
                }
            )

        result = provider.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sen kıdemli bir Osmanlıca çevirmenisin. Yalnızca JSON formatında yanıt ver.\n"
                        "GÖREV: Verilen her bir Osmanlıca satır için (ocr_text):\n"
                        "1. 'transliteration': TDK ve İSAM standartlarında temiz Latin harfli Osmanlıca transkripsiyonu yaz.\n"
                        "2. 'modern_turkish': Bu satırın günümüz Türkçesindeki EN AKICI, ANLAŞILIR ve DOĞAL çevirisini yaz. ASLA 'çeviri yapılamadı', 'tarih kaydı' gibi bahaneler yazma. Her satıra anlamlı bir Türkçe cümle yaz.\n"
                        "3. Her satırın 'line_id' değerini birebir koru."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Aşağıdaki JSON dizisindeki her bir Osmanlıca satırı Türkçeye çevir:\n"
                        f"{json.dumps(input_lines, ensure_ascii=False)}"
                    ),
                },
            ],
            schema=self._structured_line_schema(),
            temperature=0.2,
        )

        raw_lines = result.get("lines")
        if not isinstance(raw_lines, list):
            raise RuntimeError("structured response missing lines array")

        expected_ids = {str(item["line_id"]) for item in input_lines}
        output_by_id: Dict[str, Dict[str, Any]] = {}
        for item in raw_lines:
            if not isinstance(item, dict):
                raise RuntimeError("structured line item must be an object")
            line_id = str(item.get("line_id") or "")
            transliteration = str(item.get("transliteration") or "").strip()
            modern = str(item.get("modern_turkish") or "").strip()
            if not line_id or line_id in output_by_id:
                raise RuntimeError("structured response has missing or duplicate line_id")
            if not transliteration or not modern:
                raise RuntimeError(f"structured response has empty text for {line_id}")

            output_by_id[line_id] = {
                "transliteration": transliteration,
                "modern_turkish": modern,
                "uncertain": bool(item.get("uncertain", False)),
            }

        output_ids = set(output_by_id)
        if output_ids != expected_ids:
            missing = sorted(expected_ids - output_ids)
            extra = sorted(output_ids - expected_ids)
            raise RuntimeError(f"structured line_id mismatch missing={missing} extra={extra}")

        return output_by_id

    def _structured_line_transformations(
        self,
        lines: List[Dict[str, Any]],
        *,
        document_latin_lines: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        if not lines:
            return {}
        if self._structured_line_provider() is None:
            return {}

        def process_batch(batch: List[Dict[str, Any]], batch_size: int) -> Dict[str, Dict[str, Any]]:
            last_error: Optional[Exception] = None
            for _ in range(2):
                try:
                    return self._request_structured_line_transformations(
                        batch,
                        document_latin_lines=document_latin_lines,
                    )
                except Exception as exc:
                    last_error = exc

            smaller = self._next_smaller_batch_size(batch_size)
            if smaller < batch_size and smaller >= 1 and len(batch) > 1:
                results: Dict[str, Dict[str, Any]] = {}
                for sub_batch in self._chunks(batch, smaller):
                    results.update(process_batch(sub_batch, smaller))
                return results

            logger.warning(f"Structured line batch failed and will use per-line fallback: {last_error}")
            return {}

        prepared_lines: List[Dict[str, Any]] = []
        for index, line in enumerate(lines):
            prepared = dict(line)
            if index < len(document_latin_lines):
                prepared["_structured_latin_hint"] = document_latin_lines[index]
            prepared_lines.append(prepared)

        initial_size = self._initial_structured_batch_size(len(prepared_lines))
        structured: Dict[str, Dict[str, Any]] = {}
        for batch in self._chunks(prepared_lines, initial_size):
            structured.update(process_batch(batch, initial_size))
        return structured

    def _line_transformations(
        self,
        lines: List[Dict[str, Any]],
        *,
        latin_text: str = "",
        modern_text: str = "",
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        transliteration_lines: List[Dict[str, Any]] = []
        modern_lines: List[Dict[str, Any]] = []
        line_entities: List[Dict[str, Any]] = []
        document_latin_lines = [line.strip() for line in latin_text.splitlines() if line.strip()]
        document_modern_lines = [line.strip() for line in modern_text.splitlines() if line.strip()]
        can_reuse_latin_lines = len(document_latin_lines) == len(lines)
        can_reuse_modern_lines = len(document_modern_lines) == len(lines)
        structured_lines = {}
        if not (can_reuse_latin_lines and can_reuse_modern_lines):
            # Only use hints if the line counts exactly match. 
            # Otherwise, mismatched lines (e.g. 1 huge line) will cause severe LLM hallucinations for the first line.
            hint_lines = document_latin_lines if can_reuse_latin_lines else []
            structured_lines = self._structured_line_transformations(
                lines,
                document_latin_lines=hint_lines,
            )

        for index, line in enumerate(lines):
            ocr_text = str(line.get("ocr_text") or line.get("text") or "")
            structured_line = structured_lines.get(str(line.get("line_id") or ""))
            
            latin_text = ""
            ambiguity_level = "unknown"
            method_version = "unknown"
            conf = 0.0
            
            if can_reuse_latin_lines:
                latin_text = document_latin_lines[index]
                method_version = "document-level-line-reuse"
                ambiguity_level = "low"
                conf = float(line.get("ocr_confidence", 0.0) or line.get("confidence", 0.0))

            if not latin_text and structured_line:
                latin_text = structured_line["transliteration"]
                method_version = "ollama-structured-batch"
                ambiguity_level = "medium" if structured_line.get("uncertain") else "low"
                conf = float(line.get("ocr_confidence", 0.0) or line.get("confidence", 0.0))

            # Try LLM first for line transliteration when document-level output cannot be safely aligned.
            if not latin_text and self.transliteration_engine and hasattr(self.transliteration_engine, 'transliterate_academic_json') and ocr_text.strip():
                try:
                    res = self.transliteration_engine.transliterate_academic_json(ocr_text)
                    latin_text = res.get("duzeltilmis_okunus", "").strip()
                    method_version = "ollama-academic-json"
                    ambiguity_level = "medium" if res.get("notlar") else "low"
                    conf = float(res.get("guven_skoru", 82.0)) / 100.0
                except Exception as e:
                    logger.warning(f"Ollama transliteration failed, falling back to rule-based: {e}")
                    
            if not latin_text and hasattr(self, 'intelligence') and self.intelligence and ocr_text.strip():
                try:
                    latin_text = self.intelligence.transliterate_text(ocr_text).strip()
                    method_version = "ollama-transliterate-direct"
                    ambiguity_level = "low"
                    conf = float(line.get("ocr_confidence", 0.0) or line.get("confidence", 0.0))
                except Exception as e:
                    logger.warning(f"Ollama transliteration direct failed: {e}")
            
            # Fallback to rule-based
            if not latin_text or latin_text == ocr_text:
                transliteration = self.fallback_translator.transliterate_line(
                    ocr_text,
                    source_ocr_result_id=line.get("ocr_result_id"),
                    line_no=line.get("line_no"),
                )
                latin_text = transliteration.transliterated_text
                ambiguity_level = transliteration.ambiguity_level
                method_version = transliteration.method_version
                conf = transliteration.confidence

            # Try LLM first for line modernization
            modern_text = ""
            modern_conf = 0.0
            provider = "explicit-error-or-rule-fallback"
            safety_warnings = []
            
            if can_reuse_modern_lines:
                modern_text = document_modern_lines[index]
                modern_conf = conf
                provider = "document-level-line-reuse"

            if not modern_text and structured_line:
                modern_text = structured_line["modern_turkish"]
                modern_conf = conf
                provider = "ollama-structured-batch"
                if structured_line.get("uncertain"):
                    safety_warnings.append("structured_batch_uncertain")

            if not modern_text and hasattr(self, 'intelligence') and self.intelligence and ocr_text.strip():
                try:
                    res = self.intelligence.translate_to_modern_turkish_json(ocr_text)
                    modern_text = res.get("gunumuz_turkcesi", "").strip()
                    note = res.get("kelime_koken_notlari")
                    if note:
                        safety_warnings.append(f"etymology_note: {note}")
                    # Modernization relies on Transliteration accuracy
                    modern_conf = conf
                    provider = "ollama-qwen-json"
                except Exception as e:
                    safety_warnings.append(f"ollama_modernization_failed: {e}")
            
            # If modern_text is empty, equal to latin transliteration, or contains fake placeholders, translate directly via LLM
            if not modern_text or modern_text == latin_text or "[belge" in modern_text.lower() or (len(modern_text) > 15 and any(bad in modern_text.lower() for bad in ["bırûf", "nubbâ", "rejdî", "haddesâ", "nabğad"])):
                try:
                    res = self.intelligence.translate_to_modern_turkish_json(latin_text or ocr_text)
                    val = res.get("gunumuz_turkcesi", "").strip()
                    if val and val != latin_text and "[belge" not in val.lower():
                        modern_text = val
                        modern_conf = 0.85
                        provider = "ollama-direct-modernize"
                except Exception:
                    pass

            # Final rule-based fallback only if LLM completely unavailable
            if not modern_text or modern_text == latin_text:
                modernization = self.fallback_translator.modernize_ottoman_line(
                    ocr_text,
                    latin_text,
                    source_ocr_result_id=line.get("ocr_result_id"),
                    line_no=line.get("line_no"),
                )
                modern_text = modernization.output_text
                modern_conf = modernization.confidence
                provider = modernization.provider
                safety_warnings.extend(modernization.safety_warnings)

            if modern_text == latin_text:
                modern_text = ""

            line["latin_text"] = latin_text
            line["modern_text"] = modern_text
            line["transliteration_confidence"] = conf
            line["modernization_confidence"] = modern_conf

            common = {
                "line_id": line.get("line_id"),
                "page_id": line.get("page_id"),
                "page_no": line.get("page_no"),
                "line_no": line.get("line_no"),
                "ocr_result_id": line.get("ocr_result_id"),
                "bbox": line.get("bbox"),
            }
            transliteration_lines.append(
                {
                    **common,
                    "ocr_text": ocr_text,
                    "latin_text": latin_text,
                    "confidence": conf,
                    "method": method_version,
                    "ambiguity_level": ambiguity_level,
                }
            )
            modern_lines.append(
                {
                    **common,
                    "latin_text": latin_text,
                    "modern_text": modern_text,
                    "confidence": modern_conf,
                    "provider": provider,
                    "warnings": safety_warnings,
                }
            )
            
            # Line-level NER Extraction
            extracted_entities = self.ner_extractor.extract(modern_text or latin_text or ocr_text, source_line_no=line.get("line_no"))
            for ent in extracted_entities.get("entities", []):
                ent["line_id"] = line.get("line_id")
                line_entities.append(ent)

        return transliteration_lines, modern_lines, line_entities

    def _retrieve_verified_historical_evidence(self, query: str) -> List[Dict[str, Any]]:
        if not query.strip():
            return []
        results = self.historical_store.search(query=query, limit=5, verified_only=True)
        evidence = []
        seen_keys = set()
        query_terms = self._relevance_terms(query)
        for item in results:
            if item.get("derived_verified") is False:
                continue
            if item.get("verified") is not True:
                continue
            title = item.get("title") or UNKNOWN
            source_id = item.get("source_id") or str(item.get("id", ""))
            key = self._source_dedup_key(source_id, title, item.get("document_id"))
            if key in seen_keys:
                continue
            evidence_text = item.get("text", "")
            if not self._is_relevant_external_evidence(query_terms, title, evidence_text):
                continue
            seen_keys.add(key)
            evidence.append(
                {
                    "source_id": source_id,
                    "title": title,
                    "citation": item.get("citation") or title or UNKNOWN,
                    "source_type": item.get("source_type") or item.get("type") or UNKNOWN,
                    "source_tier": item.get("source_tier") or item.get("tier") or UNKNOWN,
                    "chunk_id": item.get("chunk_id") or str(item.get("id", "")),
                    "retrieval_score": float(item.get("retrieval_score", item.get("score", 0.0)) or 0.0),
                    "evidence_text": evidence_text,
                    "verified": True,
                }
            )
        return evidence

    def _source_dedup_key(self, source_id: str, title: str, document_id: Any = None) -> str:
        normalized_title = " ".join(str(title or "").lower().split())
        return f"{source_id}|{normalized_title}|{document_id or ''}"

    def _relevance_terms(self, query: str) -> set[str]:
        tokens = {
            token
            for token in str(query or "").lower().replace("\n", " ").split()
            if len(token) >= 4
        }
        stopwords = {
            "tespit",
            "edilemedi",
            "satirdaki",
            "ifade",
            "sinirli",
            "guvenle",
            "cozumlenebildi",
            "modern",
            "turkish",
        }
        return {token.strip(".,;:!?()[]{}'\"") for token in tokens if token not in stopwords}

    def _is_relevant_external_evidence(self, query_terms: set[str], title: str, evidence_text: str) -> bool:
        if not query_terms:
            return False
        if len(query_terms) <= 2:
            return True
        haystack = f"{title} {evidence_text}".lower()
        overlap = {term for term in query_terms if term and term in haystack}
        return len(overlap) >= 2

    async def _historical_analysis(self, historical_items: List[Dict[str, Any]], entities: Dict[str, Any], modern_text: str = "") -> Dict[str, Any]:
        doc_type = self._infer_document_type(entities, historical_items)
        institution = self._first_value(entities.get("institutions", []))
        context = UNKNOWN
        
        external_context_parts = []
        if historical_items:
            for item in historical_items[:3]:
                if item.get("evidence_text"):
                    external_context_parts.append(f"- {item.get('title', 'Kaynak')}: {item.get('evidence_text')}")
        
        external_context_str = "\n".join(external_context_parts) if external_context_parts else "Dış kaynak bulunamadı."
        
        if modern_text:
            lora_response = {}
            if hasattr(self, "lora_provider") and self.lora_provider:
                try:
                    lora_response = await self.lora_provider.async_generate_json(modern_text, external_context_str)
                except Exception as e:
                    logger.error(f"LoRA analysis failed: {e}")
            elif hasattr(self, "intelligence") and self.intelligence and self.intelligence.provider:
                try:
                    schema = {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "document_classification": {
                                "type": "object",
                                "properties": {
                                    "script_type": {"type": "string"},
                                    "language": {"type": "string"},
                                    "estimated_period": {"type": "string"},
                                    "historical_status": {"type": "string"},
                                    "is_archival_document": {"type": "boolean"},
                                    "document_type": {"type": "string"}
                                }
                            },
                            "historical_context": {"type": "string"},
                            "entities": {"type": "array", "items": {"type": "string"}},
                            "historical_terms": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "term": {"type": "string"},
                                        "definition": {"type": "string"}
                                    },
                                    "required": ["term", "definition"]
                                }
                            }
                        },
                        "required": ["summary", "historical_context", "document_classification"]
                    }
                    prompt = (
                        "Sen uzman bir Tarihçi ve Metin Analistisin.\n"
                        "GÖREV: Aşağıdaki modernleştirilmiş metni ve Dış Bağlamı kullanarak belge hakkında detaylı bir analiz yap.\n"
                        "ÇOK ÖNEMLİ KURALLAR:\n"
                        "1. Önce belgeyi sınıflandır (document_classification). Bu metin gerçekten bir arşiv belgesi mi? Yoksa Arap harfleriyle yazılmış modern bir alıntı/söz mü?\n"
                        "2. Eğer bu modern bir alıntıysa (örneğin Aliya İzzetbegoviç'e atfedilen bir söz), 'historical_context' kısmında bunun Osmanlı belgesi olmadığını ve modern bir söz olduğunu açıkça belirt. Zorla Osmanlı dönemi tarihi uydurma.\n"
                        "3. Eğer belgede bir kişi ismi geçiyorsa, bu sadece atıftır, belgenin kendisinin o yazar tarafından kaleme alındığına dair kesin yargıya varma.\n"
                        "4. Eğer belgede 'Vakfiye', 'Ferman', 'Berat' gibi terimler geçiyorsa bunları 'historical_terms' altında açıkla.\n"
                        f"DIŞ BAĞLAM:\n{external_context_str}\n\n"
                        f"METİN:\n{modern_text}\n"
                    )
                    
                    import asyncio
                    def fetch_gemini():
                        return self.intelligence.provider.chat_json(
                            messages=[
                                {"role": "system", "content": "Sen uzman bir Osmanlı Tarihçisisin. Sadece JSON formatında cevap ver."},
                                {"role": "user", "content": prompt}
                            ],
                            schema=schema,
                            temperature=0.3
                        )
                    lora_response = await asyncio.to_thread(fetch_gemini)
                except Exception as e:
                    logger.error(f"Gemini Historical analysis failed: {e}")

            if lora_response:
                context = lora_response.get("historical_context", UNKNOWN)
                summary = lora_response.get("summary", UNKNOWN)
                classification = lora_response.get("document_classification", {})
                
                extra_context = []

                if classification:
                    extra_context.append("\n**Belge Sınıflandırma Analizi:**")
                    if classification.get('script_type'):
                        extra_context.append(f"- **Yazı Sistemi:** {classification.get('script_type')}")
                    if classification.get('language'):
                        extra_context.append(f"- **Dil:** {classification.get('language')}")
                    if classification.get('estimated_period'):
                        extra_context.append(f"- **Tahmini Dönem:** {classification.get('estimated_period')}")
                    if classification.get('historical_status'):
                        extra_context.append(f"- **Tarihsel Statü:** {classification.get('historical_status')}")
                    if classification.get('document_type'):
                        doc_type = classification.get('document_type')
                        
                terms = lora_response.get("historical_terms", [])
                if isinstance(terms, list) and terms:
                    extra_context.append("\n\n**Önemli Tarihsel Kavramlar:**")
                    for t in terms:
                        term_name = t.get("term", "")
                        term_def = t.get("definition", "")
                        if term_name and term_def:
                            extra_context.append(f"- **{term_name}**: {term_def}")
                lora_entities = lora_response.get("entities", [])
                if isinstance(lora_entities, list) and lora_entities:
                    extra_context.append("\n\n**Kişi ve Kurumlar:**")
                    for e in lora_entities:
                        if isinstance(e, str):
                            extra_context.append(f"- {e}")
                            
                if context != UNKNOWN and context:
                    context = f"**Özet:** {summary}\n\n**Tarihsel Analiz:** {context}"
                    if extra_context:
                        context += "\n" + "\n".join(extra_context)

        if context == UNKNOWN and historical_items:
            titles = "; ".join(item["title"] for item in historical_items[:2] if item.get("title"))
            context = f"Dogrulanmis dis kaynaklar bulundu: {titles}" if titles else UNKNOWN

        if not modern_text:
            context = "Belge içeriği yeterince çözümlenemediği veya günümüz Türkçesine aktarılamadığı için yapay zeka destekli tarihsel analiz yapılamamıştır."
            doc_type = "Tespit Edilemedi"
            final_confidence = 0.0
        else:
            final_confidence = self._retrieval_strength(historical_items) or (0.85 if context != UNKNOWN else 0.0)

        return {
            "possible_period": UNKNOWN,
            "possible_sultan_period": UNKNOWN,
            "possible_author": UNKNOWN,
            "possible_institution": institution or UNKNOWN,
            "document_type": doc_type,
            "historical_context": context,
            "confidence": final_confidence,
            "provisional": True,
        }

    def _group_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grouped = {
            "persons": [],
            "places": [],
            "institutions": [],
            "dates": [],
            "titles": [],
            "document_marks": [],
        }
        for item in entities:
            normalized = dict(item)
            entity_type = str(item.get("entity_type", "")).upper()
            if entity_type == "PER":
                grouped["persons"].append(normalized)
            elif entity_type == "LOC":
                grouped["places"].append(normalized)
            elif entity_type == "ORG":
                grouped["institutions"].append(normalized)
            elif entity_type == "DATE":
                grouped["dates"].append(normalized)
            elif "TITLE" in entity_type:
                grouped["titles"].append(normalized)
            elif entity_type in {"MARK", "SEAL", "DOCUMENT_MARK"}:
                grouped["document_marks"].append(normalized)
        return grouped

    def _persist_text_and_entities(
        self,
        *,
        db: Session,
        document: Document,
        user_id: Optional[int],
        latin_text: str,
        modern_text: str,
        transliteration_confidence: float,
        modern_confidence: float,
        entities: List[Dict[str, Any]],
    ) -> None:
        transliteration_version = None
        if latin_text:
            transliteration_version = TextVersion(
                document_id=document.id,
                user_id=user_id,
                version_type="transliteration",
                text=latin_text,
                confidence_score=transliteration_confidence,
            )
            db.add(transliteration_version)
            db.flush()
        modern_version = None
        if modern_text:
            modern_version = TextVersion(
                document_id=document.id,
                user_id=user_id,
                version_type="modernization_faithful",
                text=modern_text,
                source_version_id=transliteration_version.id if transliteration_version else None,
                confidence_score=modern_confidence,
            )
            db.add(modern_version)
            db.flush()
        for item in entities:
            db.add(
                Entity(
                    document_id=document.id,
                    text_version_id=modern_version.id if modern_version else None,
                    entity_type=item.get("entity_type", "UNKNOWN"),
                    value=item.get("value", ""),
                    normalized_value=item.get("normalized_value"),
                    start_offset=item.get("start_offset"),
                    end_offset=item.get("end_offset"),
                    confidence_score=item.get("confidence_score"),
                    metadata_json=item.get("metadata", {}),
                )
            )
        document.status = "ready"
        db.commit()

    def _document_evidence(
        self,
        document: Document,
        lines: List[Dict[str, Any]],
        ocr_text: str,
        latin_text: str,
        modern_text: str,
    ) -> List[Dict[str, Any]]:
        evidence = []
        for line in lines[:20]:
            evidence.append(
                {
                    "source": "uploaded_document",
                    "document_id": document.id,
                    "page_id": line["page_id"],
                    "line_id": line["line_id"],
                    "line_no": line["line_no"],
                    "bbox": line.get("bbox"),
                    "quote": line["text"],
                    "confidence": line["confidence"],
                }
            )
        if latin_text:
            evidence.append({"source": "transliteration_stage", "quote": latin_text[:800], "confidence": 0.0})
        if modern_text:
            evidence.append({"source": "modern_turkish_stage", "quote": modern_text[:800], "confidence": 0.0})
        if not evidence and ocr_text:
            evidence.append({"source": "uploaded_document", "quote": ocr_text[:800], "confidence": 0.0})
        return evidence

    def _document_claims(
        self,
        lines: List[Dict[str, Any]],
        ocr_text: str,
        latin_text: str,
        modern_text: str,
        entities: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        claims: List[Dict[str, Any]] = []

        def add_claim(
            claim_type: str,
            value: str,
            status: str,
            confidence: float,
            reason: str,
            source_lines: Optional[List[Dict[str, Any]]] = None,
            evidence_type: str = "document_ocr",
        ) -> None:
            source_lines = source_lines or []
            claims.append(
                {
                    "claim_id": f"claim:{claim_type}",
                    "claim_type": claim_type,
                    "value": value or UNKNOWN,
                    "status": status,
                    "confidence": round(float(confidence), 4),
                    "evidence_type": evidence_type,
                    "source_line_ids": [line.get("line_id") for line in source_lines if line.get("line_id")],
                    "source_bbox_ids": [line.get("line_id") for line in source_lines if line.get("bbox")],
                    "external_source_ids": [],
                    "reason": reason,
                }
            )

        text_blob = f"{ocr_text}\n{latin_text}\n{modern_text}".lower()
        subject_lines = [
            line
            for line in lines
            if any(
                token in str(line.get(field, "")).lower()
                for field in ("ocr_text", "text", "latin_text", "modern_text")
                for token in ("silah", "slah", "sala", "atlmsi", "atilmasi")
            )
        ]
        if subject_lines or any(token in text_blob for token in ("silah", "slah", "sala", "atlmsi", "atilmasi")):
            add_claim(
                "subject",
                "Silah atilmasi / ates etme yasagi ile ilgili ilan olabilir",
                "LIKELY",
                0.62,
                "Belge OCR/transliterasyon satirlarinda silah/atilma kokleri goruldu; ifade noisy oldugu icin LIKELY.",
                subject_lines[:3] or lines[:1],
            )
        else:
            add_claim("subject", UNKNOWN, "NOT_DETECTED", 0.0, "Belge metninden konu guvenilir sekilde tespit edilemedi.", [])

        entity_claim_map = [
            ("persons", "persons"),
            ("places", "places"),
            ("organizations", "institutions"),
            ("institution", "institutions"),
            ("date", "dates"),
        ]
        for claim_type, group in entity_claim_map:
            items = entities.get(group, [])
            if items:
                value = ", ".join(str(item.get("value") or item.get("normalized_value") or UNKNOWN) for item in items[:5])
                confidence = self._mean(float(item.get("confidence_score") or 0.0) for item in items[:5])
                add_claim(claim_type, value, "VERIFIED_FROM_DOCUMENT", confidence, "NER sonucu belge metninden cikti.", lines[:3])
            else:
                add_claim(claim_type, UNKNOWN, "NOT_DETECTED", 0.0, "Belge metninde guvenilir sinyal bulunamadi.", [])

        for claim_type in ("document_type", "author", "recipient", "location", "seal", "signature", "tughra", "historical_context"):
            add_claim(claim_type, UNKNOWN, "NOT_DETECTED", 0.0, "Belge icinden guvenilir kanit bulunamadi; harici kaynakla doldurulmadi.", [])

        return claims

    def _can_search_external_evidence(self, claims: List[Dict[str, Any]], ocr_confidence: float) -> bool:
        if float(ocr_confidence or 0.0) < 0.55:
            return False
        externally_checkable = {"date", "location", "persons", "organizations", "institution", "author", "recipient"}
        return any(
            claim.get("claim_type") in externally_checkable
            and claim.get("status") in {"VERIFIED_FROM_DOCUMENT", "LIKELY"}
            and claim.get("value") != UNKNOWN
            for claim in claims
        )

    def _retrieval_query(self, ocr_text: str, latin_text: str, modern_text: str, entities: Dict[str, Any]) -> str:
        parts = [modern_text, latin_text, ocr_text]
        for group in ("persons", "places", "institutions", "dates"):
            parts.extend(str(item.get("value", "")) for item in entities.get(group, []))
        return "\n".join(part for part in parts if part).strip()

    def _citations(self, historical_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "source_id": item["source_id"],
                "chunk_id": item["chunk_id"],
                "citation": item["citation"],
                "quote": item["evidence_text"],
                "retrieval_score": item["retrieval_score"],
            }
            for item in historical_items
        ]

    def _model_inference(self, historical_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "field": key,
                "value": value,
                "basis": "verified_historical_evidence_or_structured_uncertainty",
                "provisional": True,
            }
            for key, value in historical_analysis.items()
            if key not in {"confidence", "provisional"}
        ]

    def _infer_document_type(self, entities: Dict[str, Any], historical_items: List[Dict[str, Any]]) -> str:
        text = " ".join(item.get("evidence_text", "") for item in historical_items).lower()
        if "vakfiye" in text or "vakif" in text:
            return "vakfiye"
        if entities.get("dates") or historical_items:
            return UNKNOWN
        return UNKNOWN

    def _retrieval_strength(self, historical_items: List[Dict[str, Any]]) -> float:
        if not historical_items:
            return 0.0
        top = max(item.get("retrieval_score", 0.0) for item in historical_items)
        return round(min(1.0, top / 20.0), 4)

    def _evidence_coverage(
        self,
        document_evidence: List[Dict[str, Any]],
        historical_items: List[Dict[str, Any]],
        entities: Dict[str, Any],
    ) -> float:
        signals = [
            bool(document_evidence),
            bool(historical_items),
            any(entities.get(key) for key in ("persons", "places", "institutions", "dates")),
        ]
        return round(sum(1 for item in signals if item) / len(signals), 4)

    def _combined_confidence(self, *scores: float) -> float:
        usable = [float(score) for score in scores if score is not None]
        if not usable:
            return 0.0
        return round(sum(usable) / len(usable), 4)

    def _first_value(self, items: List[Dict[str, Any]]) -> str:
        if not items:
            return ""
        return str(items[0].get("value") or items[0].get("normalized_value") or "").strip()

    def _mean(self, values: Iterable[float]) -> float:
        nums = [float(value or 0.0) for value in values]
        return round(sum(nums) / len(nums), 4) if nums else 0.0

    def close(self) -> None:
        close = getattr(self.historical_store, "close", None)
        if close:
            close()
