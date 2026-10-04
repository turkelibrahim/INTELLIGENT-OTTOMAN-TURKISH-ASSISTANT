from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional import guard
    Image = None  # type: ignore[assignment]


REQUIRED_METADATA_FIELDS = [
    "page_id",
    "source_document",
    "title",
    "approximate_year",
    "page_number",
    "print_or_handwriting",
    "typography",
    "image_quality",
    "degradation_type",
    "dpi",
    "rights_or_ownership",
    "annotator",
    "reviewer",
    "notes",
]

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".pdf"}
ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
DIACRITIC_RE = re.compile(r"[\u064b-\u065f\u0670]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


@dataclass
class ValidationIssue:
    code: str
    message: str
    path: str | None = None


@dataclass
class ValidationResult:
    status: str
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    info: list[ValidationIssue] = field(default_factory=list)
    manifest: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "errors": [issue.__dict__ for issue in self.errors],
            "warnings": [issue.__dict__ for issue in self.warnings],
            "info": [issue.__dict__ for issue in self.info],
            "manifest": self.manifest,
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_metadata(metadata_path: Path, result: ValidationResult) -> tuple[list[dict[str, str]], list[str]]:
    if not metadata_path.exists():
        result.errors.append(ValidationIssue("METADATA_MISSING", "metadata.csv is required", str(metadata_path)))
        return [], []

    try:
        with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames or []
            rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]
    except UnicodeDecodeError:
        result.errors.append(ValidationIssue("METADATA_ENCODING", "metadata.csv must be UTF-8", str(metadata_path)))
        return [], []

    missing = [field for field in REQUIRED_METADATA_FIELDS if field not in fields]
    if missing:
        result.errors.append(
            ValidationIssue("METADATA_FIELDS", f"metadata.csv missing fields: {', '.join(missing)}", str(metadata_path))
        )
    return rows, fields


def image_dimensions(path: Path) -> tuple[int | None, int | None, int | None]:
    if Image is None or path.suffix.lower() == ".pdf":
        return None, None, None
    with Image.open(path) as image:
        dpi_tuple = image.info.get("dpi") or (None, None)
        dpi = int(dpi_tuple[0]) if dpi_tuple and dpi_tuple[0] else None
        return image.width, image.height, dpi


def validate_sidecar(sidecar_path: Path, image_width: int | None, image_height: int | None, result: ValidationResult) -> None:
    if not sidecar_path.exists():
        result.info.append(ValidationIssue("LINE_SIDECAR_ABSENT", "Optional line sidecar is absent", str(sidecar_path)))
        return
    try:
        payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except Exception as exc:
        result.errors.append(ValidationIssue("LINE_SIDECAR_INVALID", f"Line sidecar is invalid JSON: {exc}", str(sidecar_path)))
        return

    lines = payload.get("lines", payload if isinstance(payload, list) else [])
    if not isinstance(lines, list):
        result.errors.append(ValidationIssue("LINE_SIDECAR_SCHEMA", "Line sidecar must contain a lines list", str(sidecar_path)))
        return

    orders: list[int] = []
    for index, line in enumerate(lines):
        if not isinstance(line, dict):
            result.errors.append(ValidationIssue("LINE_SCHEMA", f"Line {index} is not an object", str(sidecar_path)))
            continue
        order = line.get("reading_order")
        if not isinstance(order, int):
            result.errors.append(ValidationIssue("READING_ORDER_INVALID", f"Line {index} reading_order must be int", str(sidecar_path)))
        else:
            orders.append(order)
        bbox = line.get("bounding_box")
        if not (isinstance(bbox, list) and len(bbox) == 4 and all(isinstance(value, (int, float)) for value in bbox)):
            result.errors.append(ValidationIssue("BBOX_INVALID", f"Line {index} bounding_box must be [x,y,w,h]", str(sidecar_path)))
            continue
        x, y, width, height = bbox
        if width <= 0 or height <= 0:
            result.errors.append(ValidationIssue("BBOX_SIZE_INVALID", f"Line {index} bbox size must be positive", str(sidecar_path)))
        if image_width and image_height and (x < 0 or y < 0 or x + width > image_width or y + height > image_height):
            result.errors.append(ValidationIssue("BBOX_OUT_OF_BOUNDS", f"Line {index} bbox exceeds image bounds", str(sidecar_path)))
    if len(set(orders)) != len(orders):
        result.errors.append(ValidationIssue("READING_ORDER_DUPLICATE", "reading_order values must be unique", str(sidecar_path)))


def validate_dataset(input_root: Path) -> ValidationResult:
    result = ValidationResult(status="UNKNOWN")
    images_dir = input_root / "images"
    transcriptions_dir = input_root / "transcriptions"
    metadata_path = input_root / "metadata.csv"
    images_dir.mkdir(parents=True, exist_ok=True)
    transcriptions_dir.mkdir(parents=True, exist_ok=True)

    rows, fields = read_metadata(metadata_path, result)
    metadata_by_page = {row.get("page_id", ""): row for row in rows if row.get("page_id")}
    human_review_blockers: list[str] = []

    images = sorted(path for path in images_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
    transcriptions = sorted(path for path in transcriptions_dir.iterdir() if path.is_file() and path.name.endswith(".gt.txt"))
    image_stems = {path.stem for path in images}
    transcription_stems = {path.name.removesuffix(".gt.txt") for path in transcriptions}

    if not images and not transcriptions:
        result.status = "BLOCKED_USER_DATA_REQUIRED"
        result.info.append(ValidationIssue("NO_REAL_DATA", "No real images or human-verified transcriptions are present"))
    else:
        for missing in sorted(image_stems - transcription_stems):
            result.errors.append(ValidationIssue("TRANSCRIPTION_MISSING", "Matching .gt.txt file is missing", missing))
        for missing in sorted(transcription_stems - image_stems):
            result.errors.append(ValidationIssue("IMAGE_MISSING", "Matching image file is missing", missing))

    for stem in sorted((image_stems | transcription_stems) - set(metadata_by_page)):
        result.errors.append(ValidationIssue("METADATA_ROW_MISSING", "metadata.csv row is missing for page_id", stem))
    for page_id in sorted(set(metadata_by_page) - (image_stems | transcription_stems)):
        result.warnings.append(ValidationIssue("METADATA_WITHOUT_FILE", "metadata.csv row has no matching file pair", page_id))

    image_hashes: dict[str, str] = {}
    split_by_hash: dict[str, set[str]] = {}
    page_entries: list[dict[str, Any]] = []
    for image_path in images:
        page_id = image_path.stem
        digest = sha256_file(image_path)
        if digest in image_hashes:
            result.errors.append(
                ValidationIssue("DUPLICATE_IMAGE", f"Duplicate image content also used by {image_hashes[digest]}", str(image_path))
            )
        image_hashes[digest] = page_id

        width: int | None = None
        height: int | None = None
        embedded_dpi: int | None = None
        try:
            width, height, embedded_dpi = image_dimensions(image_path)
        except Exception as exc:
            result.errors.append(ValidationIssue("IMAGE_READ_FAILED", f"Cannot read image dimensions: {exc}", str(image_path)))

        metadata = metadata_by_page.get(page_id, {})
        declared_dpi = int(metadata.get("dpi") or 0) if (metadata.get("dpi") or "").isdigit() else None
        effective_dpi = declared_dpi or embedded_dpi
        if width and height and (width < 1000 or height < 1000):
            result.warnings.append(ValidationIssue("LOW_RESOLUTION_DIMENSIONS", "Image is below 1000 px on at least one side", str(image_path)))
        if effective_dpi and effective_dpi < 300:
            result.warnings.append(ValidationIssue("LOW_DPI", "DPI is below 300", str(image_path)))

        for required in ("rights_or_ownership", "annotator", "reviewer"):
            if not metadata.get(required):
                result.errors.append(ValidationIssue("METADATA_VALUE_MISSING", f"{required} is required", page_id))
        human_verified = (metadata.get("human_verified") or "").strip().lower()
        annotation_status = (metadata.get("annotation_status") or "").strip().upper()
        reviewer = (metadata.get("reviewer") or "").strip().upper()
        if human_verified in {"false", "0", "no"} or annotation_status in {"ASSISTED_ANNOTATION_DRAFT", "PENDING_HUMAN_REVIEW"}:
            human_review_blockers.append(page_id)
        if reviewer == "PENDING_HUMAN_REVIEW":
            human_review_blockers.append(page_id)
        split = metadata.get("split", "") if "split" in fields else ""
        if split:
            split_by_hash.setdefault(digest, set()).add(split)
        validate_sidecar(transcriptions_dir / f"{page_id}.lines.json", width, height, result)
        page_entries.append(
            {
                "page_id": page_id,
                "image_path": str(image_path),
                "transcription_path": str(transcriptions_dir / f"{page_id}.gt.txt"),
                "sha256": digest,
                "width": width,
                "height": height,
                "dpi": effective_dpi,
                "split": split or None,
            }
        )

    for digest, splits in split_by_hash.items():
        if len(splits) > 1:
            result.errors.append(ValidationIssue("SPLIT_LEAKAGE", f"Image hash appears in multiple splits: {sorted(splits)}", digest))

    total_chars = 0
    total_lines = 0
    for transcription_path in transcriptions:
        try:
            text = transcription_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            result.errors.append(ValidationIssue("TRANSCRIPTION_ENCODING", "Transcription must be UTF-8", str(transcription_path)))
            continue
        if not text.strip():
            result.errors.append(ValidationIssue("TRANSCRIPTION_EMPTY", "Transcription is empty", str(transcription_path)))
        if CONTROL_RE.search(text):
            result.errors.append(ValidationIssue("CONTROL_CHARACTERS", "Transcription contains disallowed control characters", str(transcription_path)))
        if unicodedata.normalize("NFC", text) != text:
            result.warnings.append(ValidationIssue("NOT_NFC", "Transcription is not NFC-normalized", str(transcription_path)))
        if "\u0640" in text:
            result.info.append(ValidationIssue("TATWEEL_PRESENT", "Tatweel is present and will be tracked", str(transcription_path)))
        if DIACRITIC_RE.search(text):
            result.info.append(ValidationIssue("DIACRITICS_PRESENT", "Arabic diacritics are present and will be tracked", str(transcription_path)))
        if not ARABIC_RE.search(text):
            result.warnings.append(ValidationIssue("RTL_SCRIPT_ABSENT", "No Arabic-script characters found", str(transcription_path)))
        lines = [line for line in text.splitlines() if line.strip()]
        total_lines += len(lines)
        total_chars += len(text)

    if result.status != "BLOCKED_USER_DATA_REQUIRED":
        if result.errors:
            result.status = "FAIL"
        elif human_review_blockers:
            result.status = "BLOCKED_HUMAN_REVIEW_REQUIRED"
            result.warnings.append(
                ValidationIssue(
                    "HUMAN_REVIEW_REQUIRED",
                    f"Pages are not locked human-verified ground truth: {', '.join(sorted(set(human_review_blockers)))}",
                )
            )
        else:
            result.status = "PASS"

    result.manifest = {
        "input_root": str(input_root),
        "metadata_fields": fields,
        "page_count": len(images),
        "transcription_count": len(transcriptions),
        "verified_line_count": total_lines,
        "character_count": total_chars,
        "dataset_level": dataset_level(len(images), total_lines, len({row.get("source_document", "") for row in rows if row.get("source_document")})),
        "human_review_blockers": sorted(set(human_review_blockers)),
        "pages": page_entries,
    }
    return result


def dataset_level(page_count: int, line_count: int, source_count: int) -> str:
    if page_count >= 20 and line_count >= 300 and source_count >= 3:
        return "FINAL_ACADEMIC_READY_CANDIDATE"
    if page_count >= 3 and line_count >= 50:
        return "PILOT_EVALUATION_ONLY"
    if page_count == 0 and line_count == 0:
        return "NO_DATA"
    return "INSUFFICIENT_FOR_EVALUATION"


def write_evidence(evidence_root: Path, validation: ValidationResult) -> None:
    evidence_root.mkdir(parents=True, exist_ok=True)
    status = validation.status
    payload = validation.to_dict()
    (evidence_root / "input_validation.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (evidence_root / "dataset_manifest.json").write_text(
        json.dumps({"status": status, **validation.manifest}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (evidence_root / "split_manifest.json").write_text(
        json.dumps({"status": status, "splits": {}, "reason": "No split created without locked real data"}, indent=2),
        encoding="utf-8",
    )
    (evidence_root / "annotation_audit.json").write_text(
        json.dumps({"status": status, "locked_pages": [], "assisted_annotation_excluded": True}, indent=2),
        encoding="utf-8",
    )
    (evidence_root / "locked_ground_truth_export.json").write_text(
        json.dumps({"status": status, "pages": [], "reason": "No locked ground truth export without user data"}, indent=2),
        encoding="utf-8",
    )
    blocked_json = {"status": status, "metrics": None, "reason": "Real locked ground truth data is required"}
    for name in [
        "baseline_raw_results.json",
        "aggregate_metrics.json",
        "confidence_intervals.json",
        "line_detection_metrics.json",
        "performance_results.json",
    ]:
        (evidence_root / name).write_text(json.dumps(blocked_json, indent=2), encoding="utf-8")
    for name, header in [
        ("preprocessing_ablation.csv", "status,profile,cer,wer,line_precision,line_recall,reason\n"),
        ("page_metrics.csv", "status,page_id,cer,wer,line_precision,line_recall,reason\n"),
    ]:
        (evidence_root / name).write_text(
            header + f"{status},,,,,Real locked ground truth data is required\n",
            encoding="utf-8",
        )
    (evidence_root / "dataset_provenance.md").write_text(
        "# Dataset Provenance\n\n"
        f"Status: {status}\n\n"
        "No original user-owned/permitted Ottoman Turkish pages are present yet. "
        "Each future page must include rights/ownership, annotator, reviewer, and source document metadata.\n",
        encoding="utf-8",
    )
    (evidence_root / "error_analysis.md").write_text(
        "# Error Analysis\n\nStatus: BLOCKED_USER_DATA_REQUIRED\n\nNo OCR error analysis was produced because no locked real ground truth data exists.\n",
        encoding="utf-8",
    )
    (evidence_root / "warning_audit.md").write_text(
        "# Warning Audit\n\nStatus: PENDING_COMMAND_RUNS\n\nBackend/frontend warning commands have not been recorded yet in this file.\n",
        encoding="utf-8",
    )
    (evidence_root / "browser_e2e.txt").write_text("PENDING_BROWSER_E2E\n", encoding="utf-8")
    (evidence_root / "backend_tests.txt").write_text("PENDING_BACKEND_TESTS\n", encoding="utf-8")
    (evidence_root / "frontend_tests.txt").write_text("PENDING_FRONTEND_TESTS\n", encoding="utf-8")
    (evidence_root / "FINAL_OCR_QUALITY_REPORT.md").write_text(
        "# Final OCR Quality Report\n\n"
        f"Status: {status}\n\n"
        "CER, WER, preprocessing ablation, confidence intervals, and line detection metrics are not reported. "
        "The gate is blocked until original locked ground truth data is supplied and validated.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate real Ottoman OCR ground truth input data.")
    parser.add_argument("--input-root", default="evidence/ocr_quality_real/input")
    parser.add_argument("--evidence-root", default="evidence/ocr_quality_real")
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()

    validation = validate_dataset(Path(args.input_root))
    if args.write_evidence:
        write_evidence(Path(args.evidence_root), validation)
    print(json.dumps(validation.to_dict(), ensure_ascii=False, indent=2))
    return 1 if validation.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
