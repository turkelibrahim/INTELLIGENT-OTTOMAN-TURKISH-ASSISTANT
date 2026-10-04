from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.processing_outputs import ModelRegistryEntry


@dataclass(frozen=True)
class ConfidenceAssessment:
    score: float
    label: str
    policy_version: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelDescriptor:
    name: str
    model_type: str
    version: str
    source: str
    license: Optional[str]
    config: Dict[str, Any]


class ConfidenceManager:
    POLICY_VERSION = "confidence-policy-v1"

    def assess(self, score: Optional[float], *, fallback: bool = False) -> ConfidenceAssessment:
        normalized = self._normalize(score)
        if fallback:
            return ConfidenceAssessment(
                score=normalized,
                label="fallback",
                policy_version=self.POLICY_VERSION,
                explanation="Fallback output; confidence is not a correctness guarantee.",
            )
        if normalized >= 0.85:
            label = "high"
        elif normalized >= 0.65:
            label = "medium"
        elif normalized > 0:
            label = "low"
        else:
            label = "unknown"
        return ConfidenceAssessment(
            score=normalized,
            label=label,
            policy_version=self.POLICY_VERSION,
            explanation="Confidence score is normalized to [0, 1] and must be shown as uncertainty, not truth.",
        )

    def _normalize(self, score: Optional[float]) -> float:
        if score is None:
            return 0.0
        return round(max(0.0, min(float(score), 1.0)), 4)


class ModelRegistryService:
    REGISTRY_VERSION = "model-registry-service-v1"

    def ensure_entry(self, db: Session, descriptor: ModelDescriptor) -> ModelRegistryEntry:
        existing = (
            db.query(ModelRegistryEntry)
            .filter(
                ModelRegistryEntry.name == descriptor.name,
                ModelRegistryEntry.model_type == descriptor.model_type,
                ModelRegistryEntry.version == descriptor.version,
            )
            .first()
        )
        if existing:
            return existing

        entry = ModelRegistryEntry(
            name=descriptor.name,
            model_type=descriptor.model_type,
            version=descriptor.version,
            source=descriptor.source,
            license=descriptor.license,
            config=descriptor.config,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def descriptor_for_operation(self, operation: str, metadata: Dict[str, Any]) -> ModelDescriptor:
        if operation == "ocr":
            return ModelDescriptor(
                name=str(metadata.get("model_name", "microsoft/trocr-base-printed")),
                model_type="ocr",
                version=str(metadata.get("model_version", "unversioned")),
                source="huggingface-or-local-fallback",
                license=None,
                config={
                    "device": metadata.get("device"),
                    "fallback": metadata.get("fallback"),
                    "fallback_reason": metadata.get("fallback_reason"),
                    "registry_version": self.REGISTRY_VERSION,
                },
            )
        if operation == "transliteration":
            return ModelDescriptor(
                name=str(metadata.get("method_version", "rule-based-ottoman-latin-v1")),
                model_type="transliteration",
                version=str(metadata.get("method_version", "rule-based-ottoman-latin-v1")),
                source="local-rule-based",
                license="project",
                config={"operation": operation, "registry_version": self.REGISTRY_VERSION},
            )
        if operation == "modernization":
            return ModelDescriptor(
                name=str(metadata.get("provider", "local-rule-based-fallback")),
                model_type="modernization",
                version=str(metadata.get("prompt_version", "rule-based-modernization-v1")),
                source="local-rule-based",
                license="project",
                config={
                    "mode": metadata.get("mode"),
                    "prompt_version": metadata.get("prompt_version"),
                    "registry_version": self.REGISTRY_VERSION,
                },
            )
        if operation == "ner":
            return ModelDescriptor(
                name=str(metadata.get("method_version", "rule-based-ner-date-glossary-v1")),
                model_type="ner",
                version=str(metadata.get("method_version", "rule-based-ner-date-glossary-v1")),
                source="local-rule-based",
                license="project",
                config={"operation": operation, "registry_version": self.REGISTRY_VERSION},
            )
        raise ValueError(f"Unsupported operation for model registry: {operation}")


def build_operation_metadata(
    operation: str,
    *,
    confidence_score: Optional[float],
    model_metadata: Dict[str, Any],
    fallback: bool = False,
) -> Dict[str, Any]:
    confidence = ConfidenceManager().assess(confidence_score, fallback=fallback)
    descriptor = ModelRegistryService().descriptor_for_operation(operation, model_metadata)
    return {
        "operation": operation,
        "confidence": confidence.to_dict(),
        "model": asdict(descriptor),
    }
