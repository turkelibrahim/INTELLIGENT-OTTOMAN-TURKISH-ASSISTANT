import time
from typing import Dict, Any, Optional
from app.core.config import settings
from .confidence import calculate_risk, calculate_confidence, determine_route
from .cache import cache_store
from .nvidia_client import verify_task

class OttomanSmartAIRouter:
    def __init__(self):
        self.primary_model = settings.NVIDIA_PRIMARY_MODEL
        self.secondary_model = settings.NVIDIA_SECONDARY_MODEL
        self.local_model = "qwen3.5:4b"

    def calculate_system_confidence(
        self,
        local_result: Dict[str, Any],
        rag_context: Optional[Dict[str, Any]] = None
    ) -> float:
        # Extract signals safely, defaulting to 0.5 (medium risk) if missing
        ocr_uncertainty = 1.0 - local_result.get("ocr_confidence", 0.5)
        # Placeholder risk extractions
        character_anomaly = 0.1
        language_uncertainty = 0.1
        local_model_disagreement = 0.0
        rag_disagreement = 0.2 if not rag_context else 0.0
        translation_uncertainty = 0.1
        metadata_uncertainty = 0.1
        
        risk = calculate_risk(
            ocr_uncertainty,
            character_anomaly,
            language_uncertainty,
            local_model_disagreement,
            rag_disagreement,
            translation_uncertainty,
            metadata_uncertainty
        )
        return calculate_confidence(risk)

    async def verify_with_cloud(
        self,
        task: str,
        prompt: str,
        image_url: Optional[str] = None,
        image_region_hash: str = "full",
        prompt_version: str = "v1"
    ) -> Dict[str, Any]:
        """Runs cloud verification with Cache, Fallback and Escalation"""
        
        model_to_use = settings.NVIDIA_VISION_MODEL if image_url else self.primary_model
        
        # 1. Check Cache for Model
        cache_hit_primary = cache_store.get(
            image_region_hash, prompt, task, prompt_version, model_to_use
        )
        if cache_hit_primary:
            cache_hit_primary["cache_hit"] = True
            return cache_hit_primary

        start_time = time.time()
        try:
            primary_result = await verify_task(
                task=task,
                prompt=prompt,
                image_url=image_url,
                model=model_to_use
            )
            primary_result["cache_hit"] = False
            primary_result["model_used"] = model_to_use
            primary_result["latency_ms"] = int((time.time() - start_time) * 1000)
            
            # Cache the successful primary result
            cache_store.set(
                primary_result, image_region_hash, prompt, task, prompt_version, model_to_use
            )
            
            # Check if Second Opinion (GLM) is needed
            # Only escalate if primary model is explicitly uncertain or failed
            if primary_result.get("decision") == "uncertain" or primary_result.get("confidence", 1.0) < 0.5:
                # Need GLM escalation
                cache_hit_secondary = cache_store.get(
                    image_region_hash, prompt, task, prompt_version, self.secondary_model
                )
                if cache_hit_secondary:
                    cache_hit_secondary["cache_hit"] = True
                    cache_hit_secondary["second_opinion"] = True
                    return cache_hit_secondary
                
                start_time_sec = time.time()
                try:
                    secondary_result = await verify_task(
                        task=task,
                        prompt=prompt,
                        image_url=image_url,
                        model=self.secondary_model
                    )
                    secondary_result["cache_hit"] = False
                    secondary_result["second_opinion"] = True
                    secondary_result["model_used"] = self.secondary_model
                    secondary_result["latency_ms"] = int((time.time() - start_time_sec) * 1000)
                    
                    cache_store.set(
                        secondary_result, image_region_hash, prompt, task, prompt_version, self.secondary_model
                    )
                    return secondary_result
                except Exception as e:
                    # GLM Failed, fallback to primary result despite uncertainty
                    primary_result["second_opinion_failed"] = True
                    return primary_result

            return primary_result
            
        except Exception as e:
            # Complete failure of cloud path -> Local Fallback
            return {
                "error": str(e),
                "verification_status": "local_fallback",
                "cache_hit": False,
                "latency_ms": int((time.time() - start_time) * 1000)
            }

    async def selective_document_verification(
        self,
        local_result: Dict[str, Any],
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parses the full document local_result, bundles suspicious lines,
        sends to NVIDIA if needed, and patches the final result.
        """
        sys_conf = self.calculate_system_confidence(local_result)
        route = determine_route(sys_conf)
        
        final_response = dict(local_result)
        final_response["ai_route"] = {
            "primary": "local",
            "verification": None,
            "second_opinion": None
        }
        final_response["verification_status"] = "local"
        final_response["system_confidence"] = sys_conf
        final_response["models_used"] = [self.local_model]
        
        if not settings.NVIDIA_ENABLED or route == "local_only":
            return final_response
            
        # Selective bundling: Find lines with low confidence
        transliteration = local_result.get("transliteration", {})
        modern = local_result.get("modern_turkish", {})
        
        # Combine lines info
        t_lines = transliteration.get("lines", [])
        m_lines = modern.get("lines", [])
        
        suspicious_lines = []
        for i, t_line in enumerate(t_lines):
            t_conf = t_line.get("confidence", 1.0)
            m_conf = m_lines[i].get("confidence", 1.0) if i < len(m_lines) else 1.0
            
            if t_conf < 0.70 or m_conf < 0.70:
                suspicious_lines.append({
                    "id": i,
                    "ocr": t_line.get("ocr_text", ""),
                    "latin": t_line.get("latin_text", ""),
                    "modern": m_lines[i].get("modern_text", "") if i < len(m_lines) else ""
                })
                
        if not suspicious_lines:
            # Maybe the page overall confidence is low but individual lines were scored high?
            if sys_conf < 0.5:
                # Force top 3 lines
                suspicious_lines = [{"id": i, "ocr": l.get("ocr_text",""), "latin": l.get("latin_text",""), "modern": ""} for i, l in enumerate(t_lines[:3])]
            else:
                return final_response
                
        prompt_lines = "\n".join([f"ID[{s['id']}]: OCR: {s['ocr']} | LATIN: {s['latin']} | MODERN: {s['modern']}" for s in suspicious_lines])
        prompt = f"Please verify and correct the following suspicious lines. Output a JSON dictionary mapping ID to corrected {{'ocr': '...', 'latin': '...', 'modern': '...'}}.\n\n{prompt_lines}"
        
        final_response["ai_route"]["verification"] = "nvidia"
        
        # Generate hash based on suspicious lines text
        image_region_hash = cache_store._generate_key("selective", prompt, "SELECTIVE_VERIFY", "v1", self.primary_model)
        
        cloud_result = await self.verify_with_cloud(
            task="SELECTIVE_VERIFY",
            prompt=prompt,
            image_url=image_url,
            image_region_hash=image_region_hash,
            prompt_version="v1"
        )
        
        if cloud_result.get("verification_status") == "local_fallback" or cloud_result.get("error"):
            final_response["verification_status"] = "local_fallback"
            return final_response
            
        final_response["cache_hit"] = cloud_result.get("cache_hit", False)
        final_response["models_used"].append(cloud_result.get("model_used", self.primary_model))
        if cloud_result.get("second_opinion"):
            final_response["ai_route"]["second_opinion"] = True
            
        # Patch the results if corrections are provided
        corrections = cloud_result.get("corrections") or cloud_result
        patched = False
        if isinstance(corrections, dict):
            for i_str, corr in corrections.items():
                if not i_str.isdigit() and "id" not in str(i_str).lower():
                    continue
                try:
                    idx = int(''.join(filter(str.isdigit, i_str)))
                    if idx < len(t_lines):
                        if isinstance(corr, dict):
                            if corr.get("ocr"): t_lines[idx]["ocr_text"] = corr["ocr"]
                            if corr.get("latin"): t_lines[idx]["latin_text"] = corr["latin"]
                            if corr.get("modern") and idx < len(m_lines): m_lines[idx]["modern_text"] = corr["modern"]
                            patched = True
                except Exception:
                    pass
        
        if patched:
            final_response["verification_status"] = "verified"
            # We could optionally reconstruct full document text from lines here, but keeping it simple.
        else:
            final_response["verification_status"] = "uncertain"
            
        return final_response

smart_router = OttomanSmartAIRouter()
