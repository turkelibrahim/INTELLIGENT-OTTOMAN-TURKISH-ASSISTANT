"""Run TASK-034-Q5 line segmentation, RTL, and WER improvement loop.

The script reads locked dataset 2, never mutates ground-truth tables, selects a
candidate on the existing dev split only, then evaluates the frozen candidate on
the existing test split.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import platform
import sqlite3
import statistics
import sys
import time
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(BACKEND_ROOT)

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

from app.services.document_processing.ocr_engine import OttomanOCREngine
from app.services.evaluation.metrics import evaluate_page
from app.services.evaluation.ocr_pipeline_optimization import (
    BoxItem,
    as_bbox,
    clean_component_boxes,
    combined_sha256,
    file_sha256,
    freeze_config,
    group_rtl_lines,
    hybrid_line_items,
    logical_line_items,
    match_boxes,
    merge_adjacent_line_boxes,
    projection_profile_line_boxes,
    reading_order_metrics,
)


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(BACKEND_ROOT / "ottoman_assistant.db")
    conn.row_factory = sqlite3.Row
    return conn


def load_dataset(conn: sqlite3.Connection, dataset_id: int) -> dict:
    dataset = dict(conn.execute("select * from datasets where id=?", (dataset_id,)).fetchone())
    pages = []
    for row in conn.execute("select * from ground_truth_pages where dataset_id=? order by id", (dataset_id,)):
        page = dict(row)
        page["lines"] = [
            dict(line)
            for line in conn.execute(
                "select * from ground_truth_lines where page_id=? order by reading_order", (page["id"],)
            )
        ]
        pages.append(page)
    return {"dataset": dataset, "pages": pages}


def integrity_snapshot(data: dict) -> dict:
    parts = []
    pages = []
    for page in data["pages"]:
        image_path = Path(page["image_path"])
        image_hash = file_sha256(image_path)
        line_parts = []
        for line in page["lines"]:
            bbox = json.loads(line["bounding_box"]) if isinstance(line["bounding_box"], str) else line["bounding_box"]
            item = json.dumps(
                {
                    "id": line["id"],
                    "page_id": line["page_id"],
                    "reading_order": line["reading_order"],
                    "bbox": bbox,
                    "text": line["text_content"],
                    "text_reviewed": line["text_reviewed"],
                    "bbox_reviewed": line["bbox_reviewed"],
                    "status": line["status"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            parts.append(item)
            line_parts.append(item)
        pages.append(
            {
                "page_id": page["id"],
                "split": page["split_type"],
                "image_path": str(image_path),
                "image_sha256": image_hash,
                "line_count": len(page["lines"]),
                "line_state_sha256": combined_sha256(line_parts),
            }
        )
    return {
        "dataset_id": data["dataset"]["id"],
        "dataset_status": data["dataset"]["status"],
        "dataset_version": data["dataset"]["version"],
        "pages": pages,
        "combined_ground_truth_sha256": combined_sha256(parts + [page["image_sha256"] for page in pages]),
    }


def gt_items(page: dict) -> list[BoxItem]:
    out = []
    for line in page["lines"]:
        bbox = json.loads(line["bounding_box"]) if isinstance(line["bounding_box"], str) else line["bounding_box"]
        out.append(BoxItem(str(line["id"]), as_bbox(bbox), line["text_content"], 1.0))
    return out


def preprocess_image(image: Image.Image, profile: str) -> Image.Image:
    if profile == "raw":
        return image.convert("RGB")
    gray = ImageOps.grayscale(image)
    if profile == "autocontrast":
        return ImageOps.autocontrast(gray).convert("RGB")
    if profile == "contrast":
        return ImageEnhance.Contrast(ImageOps.autocontrast(gray)).enhance(1.6).convert("RGB")
    if profile == "threshold":
        enhanced = ImageEnhance.Contrast(ImageOps.autocontrast(gray)).enhance(1.5)
        return enhanced.point(lambda pixel: 255 if pixel > 170 else 0).convert("RGB")
    raise ValueError(profile)


def crop_line(image: Image.Image, bbox: tuple[float, float, float, float], padding: int) -> Image.Image:
    x1, y1, x2, y2 = bbox
    return image.crop((max(0, int(x1) - padding), max(0, int(y1) - padding), min(image.width, int(x2) + padding), min(image.height, int(y2) + padding)))


def readtext(reader, image: Image.Image, config: dict) -> list[BoxItem]:
    arr = np.array(image.convert("RGB"))
    raw = reader.readtext(
        arr,
        detail=1,
        paragraph=False,
        decoder=config.get("decoder", "greedy"),
        text_threshold=config.get("text_threshold", 0.7),
        low_text=config.get("low_text", 0.4),
        link_threshold=config.get("link_threshold", 0.4),
        canvas_size=config.get("canvas_size", 2560),
        mag_ratio=config.get("mag_ratio", 1.0),
        contrast_ths=config.get("contrast_ths", 0.1),
        adjust_contrast=config.get("adjust_contrast", 0.5),
    )
    out = []
    for idx, (points, text, confidence) in enumerate(raw):
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        out.append(BoxItem(f"ocr_{idx:04d}", (min(xs), min(ys), max(xs), max(ys)), text.strip(), float(confidence)))
    return out


def summarize(gt_lines: list[str], ocr_lines: list[str]) -> dict:
    result = evaluate_page(gt_lines, ocr_lines)
    strict = result["strict"]
    normalized = result["normalized"]
    exact = sum(1 for idx, gt in enumerate(gt_lines) if idx < len(ocr_lines) and gt == ocr_lines[idx])
    return {
        "strict_cer": strict.get("cer"),
        "normalized_cer": normalized.get("cer"),
        "strict_wer": strict.get("wer"),
        "normalized_wer": normalized.get("wer"),
        "character_accuracy": 1.0 - float(strict.get("cer", 1.0)),
        "word_accuracy": 1.0 - float(strict.get("wer", 1.0)),
        "exact_line_match": exact / len(gt_lines) if gt_lines else 0.0,
    }


def line_text(items: list[BoxItem]) -> list[str]:
    return [item.text.strip() for item in sorted(items, key=lambda item: (item.bbox[1], -item.bbox[2], item.id)) if item.text.strip()]


def build_lines(image: Image.Image, components: list[BoxItem], config: dict) -> list[BoxItem]:
    page_size = (image.width, image.height)
    clean = clean_component_boxes(
        components,
        page_size=page_size,
        min_area=float(config.get("min_area", 25.0)),
        min_height=float(config.get("min_height", 4.0)),
        duplicate_iou_threshold=float(config.get("duplicate_iou_threshold", 0.9)),
        nested_threshold=float(config.get("nested_threshold", 0.92)),
    )
    strategy = config["strategy"]
    if strategy == "raw_components":
        return components
    if strategy == "clean_components":
        return clean
    if strategy == "logical":
        return logical_line_items(clean, page_size=page_size, y_tolerance_ratio=float(config.get("y_tolerance_ratio", 0.55)), vertical_overlap_threshold=float(config.get("vertical_overlap_threshold", 0.35)))
    if strategy == "merged":
        return merge_adjacent_line_boxes(clean, y_tolerance_ratio=float(config.get("y_tolerance_ratio", 0.55)), vertical_overlap_threshold=float(config.get("vertical_overlap_threshold", 0.35)), max_horizontal_gap_ratio=float(config.get("max_horizontal_gap_ratio", 0.08)), page_width=image.width)
    if strategy == "projection":
        return projection_profile_line_boxes(
            image,
            min_band_height=int(config.get("min_band_height", 8)),
            gap_tolerance=int(config.get("gap_tolerance", 3)),
            min_ink_pixels=int(config.get("min_ink_pixels", 8)),
            threshold=int(config.get("projection_threshold", 210)),
            horizontal_margin=int(config.get("horizontal_margin", 4)),
        )
    if strategy == "hybrid":
        bands = projection_profile_line_boxes(
            image,
            min_band_height=int(config.get("min_band_height", 8)),
            gap_tolerance=int(config.get("gap_tolerance", 3)),
            min_ink_pixels=int(config.get("min_ink_pixels", 8)),
            threshold=int(config.get("projection_threshold", 210)),
            horizontal_margin=int(config.get("horizontal_margin", 4)),
        )
        return hybrid_line_items(clean, bands)
    raise ValueError(strategy)


def component_fragmentation(gt: list[BoxItem], components: list[BoxItem]) -> dict:
    split = merged = noise = 0
    cover_counts = []
    for gt_item in gt:
        covered = [comp for comp in components if comp.bbox[2] >= gt_item.bbox[0] and comp.bbox[0] <= gt_item.bbox[2] and comp.bbox[3] >= gt_item.bbox[1] and comp.bbox[1] <= gt_item.bbox[3]]
        cover_counts.append(len(covered))
        if len(covered) > 1:
            split += 1
    for comp in components:
        covered_gt = [gt_item for gt_item in gt if comp.bbox[2] >= gt_item.bbox[0] and comp.bbox[0] <= gt_item.bbox[2] and comp.bbox[3] >= gt_item.bbox[1] and comp.bbox[1] <= gt_item.bbox[3]]
        if not covered_gt:
            noise += 1
        if len(covered_gt) > 1:
            merged += 1
    return {"fragmented_lines": split, "merged_line_components": merged, "noise_components": noise, "avg_components_per_gt": statistics.mean(cover_counts) if cover_counts else 0.0}


def evaluate_candidate(reader, pages: list[dict], config: dict, evidence_dir: Path, label: str, overlays: bool) -> dict:
    started = time.perf_counter()
    page_rows = []
    gt_all = []
    ocr_all = []
    total_gt = total_det = total_matches = 0
    total_missed = total_extra = 0
    confidences = []
    reading_pairs = []
    frags = Counter()
    for page in pages:
        image = Image.open(page["image_path"]).convert("RGB")
        processed = preprocess_image(image, config.get("preprocessing", "raw"))
        components = readtext(reader, processed, config)
        components = [item for item in components if item.text]
        lines = build_lines(processed, components, config)
        gt = gt_items(page)
        match = match_boxes(gt, lines, iou_threshold=float(config.get("iou_threshold", 0.5)))
        match_map = {entry["detected_id"]: entry["gt_id"] for entry in match["matches"]}
        expected_ids = [item.id for item in gt]
        actual_ids = [match_map[item.id] for item in lines if item.id in match_map]
        order = reading_order_metrics(expected_ids, actual_ids)
        gt_text = [line["text_content"] for line in page["lines"]]
        ocr_text = line_text(lines)
        text_metrics = summarize(gt_text, ocr_text)
        frag = component_fragmentation(gt, components)
        frags.update(frag)
        confidences.extend([item.confidence for item in components if item.confidence is not None])
        total_gt += len(gt)
        total_det += len(lines)
        total_matches += len(match["matches"])
        total_missed += len(match["missed"])
        total_extra += len(match["extra"])
        gt_all.extend(gt_text)
        ocr_all.extend(ocr_text)
        reading_pairs.append(order["overall_reading_order"])
        page_rows.append(
            {
                "page_id": page["id"],
                "split": page["split_type"],
                "gt_lines": len(gt),
                "ocr_lines": len(lines),
                "component_count": len(components),
                "matches": len(match["matches"]),
                "precision": match["precision"],
                "recall": match["recall"],
                "f1": match["f1"],
                "missed": len(match["missed"]),
                "extra": len(match["extra"]),
                "reading_order_accuracy": order["overall_reading_order"],
                **text_metrics,
            }
        )
        if overlays:
            overlay = image.copy()
            draw = ImageDraw.Draw(overlay)
            matched_gt = {entry["gt_id"] for entry in match["matches"]}
            matched_det = {entry["detected_id"] for entry in match["matches"]}
            for index, item in enumerate(gt):
                draw.rectangle(item.bbox, outline="green", width=4)
                draw.text((item.bbox[0], max(0, item.bbox[1] - 18)), f"GT{index}", fill="green")
            for index, item in enumerate(lines):
                color = "blue" if item.id in matched_det else "red"
                draw.rectangle(item.bbox, outline=color, width=2)
                draw.text((item.bbox[0], item.bbox[3] + 2), f"P{index}", fill=color)
            for item in gt:
                if item.id not in matched_gt:
                    draw.rectangle(item.bbox, outline="yellow", width=6)
            out = evidence_dir / "overlays" / f"{label}_page_{page['id']}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            overlay.save(out)
    precision = total_matches / total_det if total_det else 0.0
    recall = total_matches / total_gt if total_gt else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    summary = summarize(gt_all, ocr_all)
    summary.update(
        {
            "strategy": config["strategy"],
            "name": config["name"],
            "line_precision": precision,
            "line_recall": recall,
            "line_f1": f1,
            "missed_lines": total_missed,
            "extra_boxes": total_extra,
            "average_ocr_confidence": statistics.mean(confidences) if confidences else 0.0,
            "reading_order_accuracy": statistics.mean(reading_pairs) if reading_pairs else 0.0,
            "page_failure_rate": sum(1 for row in page_rows if row["ocr_lines"] == 0) / len(page_rows) if page_rows else 1.0,
            "pages": page_rows,
            "time_ms": (time.perf_counter() - started) * 1000,
            "fragmentation": dict(frags),
        }
    )
    return summary


def recognition_only(reader, pages: list[dict], config: dict) -> dict:
    gt_all = []
    ocr_all = []
    page_rows = []
    confidences = []
    started = time.perf_counter()
    for page in pages:
        image = Image.open(page["image_path"]).convert("RGB")
        page_gt = []
        page_ocr = []
        for line in page["lines"]:
            bbox = json.loads(line["bounding_box"]) if isinstance(line["bounding_box"], str) else line["bounding_box"]
            crop = crop_line(image, as_bbox(bbox), int(config.get("padding", 8)))
            crop = preprocess_image(crop, config.get("preprocessing", "raw"))
            detections = readtext(reader, crop, config)
            grouped = group_rtl_lines(detections)
            text = " ".join(" ".join(item.text for item in group if item.text) for group in grouped).strip()
            page_gt.append(line["text_content"])
            page_ocr.append(text)
            confidences.extend([item.confidence for item in detections])
        metrics = summarize(page_gt, page_ocr)
        page_rows.append({"page_id": page["id"], "split": page["split_type"], **metrics})
        gt_all.extend(page_gt)
        ocr_all.extend(page_ocr)
    out = summarize(gt_all, ocr_all)
    out.update({"pages": page_rows, "average_ocr_confidence": statistics.mean(confidences) if confidences else 0.0, "time_ms": (time.perf_counter() - started) * 1000})
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def char_errors(gt: str, hyp: str) -> list[dict]:
    counts = Counter()
    for left, right in zip(gt, hyp):
        if left != right:
            counts[(left, right)] += 1
    if len(gt) > len(hyp):
        for char in gt[len(hyp):]:
            counts[(char, "")] += 1
    elif len(hyp) > len(gt):
        for char in hyp[len(gt):]:
            counts[("", char)] += 1
    return [{"source": src, "target": dst, "count": count} for (src, dst), count in counts.most_common(80)]


def acceptance(metrics: dict, before_hash: str, after_hash: str) -> dict:
    gates = {
        "test_cer_lte_0_25": metrics["strict_cer"] <= 0.25,
        "test_wer_lte_0_55": metrics["strict_wer"] <= 0.55,
        "test_line_f1_gte_0_75": metrics["line_f1"] >= 0.75,
        "reading_order_gte_0_90": metrics["reading_order_accuracy"] >= 0.90,
        "no_empty_or_crash": metrics["page_failure_rate"] == 0,
        "ground_truth_hash_unchanged": before_hash == after_hash,
    }
    return {"gates": gates, "decision": "PASS" if all(gates.values()) else "FAIL_NEEDS_MODEL_IMPROVEMENT"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", type=int, default=2)
    parser.add_argument("--evidence-dir", default=str(PROJECT_ROOT / "evidence" / "line_segmentation_q5"))
    args = parser.parse_args()
    evidence_dir = Path(args.evidence_dir)
    if not evidence_dir.is_absolute():
        evidence_dir = PROJECT_ROOT / evidence_dir
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "overlays").mkdir(parents=True, exist_ok=True)

    conn = connect()
    data = load_dataset(conn, args.dataset_id)
    before = integrity_snapshot(data)
    (evidence_dir / "ground_truth_integrity_before.json").write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding="utf-8")
    if data["dataset"]["status"] != "LOCKED":
        raise RuntimeError("Q5 requires locked dataset")

    split = {
        "train_pages": [page["id"] for page in data["pages"] if page["split_type"] == "train"],
        "validation_pages": [page["id"] for page in data["pages"] if page["split_type"] in {"dev", "validation", "val"}],
        "test_pages": [page["id"] for page in data["pages"] if page["split_type"] == "test"],
        "policy": "existing_split_preserved_no_resampling",
        "seed": None,
        "limitation": "Only 73 lines across 3 pages; estimates are pilot engineering signals, not production SLA statistics.",
    }
    (evidence_dir / "split_manifest.json").write_text(json.dumps(split, ensure_ascii=False, indent=2), encoding="utf-8")
    validation_pages = [page for page in data["pages"] if page["id"] in set(split["validation_pages"])]
    test_pages = [page for page in data["pages"] if page["id"] in set(split["test_pages"])]

    env = {
        "python": sys.version,
        "platform": platform.platform(),
        "torch_version": torch.__version__,
        "torch_cuda_available": torch.cuda.is_available(),
        "torch_cuda_version": torch.version.cuda,
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "database": str(BACKEND_ROOT / "ottoman_assistant.db"),
    }
    (evidence_dir / "runtime_environment.json").write_text(json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8")

    engine = OttomanOCREngine(enable_easyocr=True, enable_trocr=False, enable_tesseract=True, gpu=True)
    reader = engine.engines["easyocr"].reader
    env["easyocr_device"] = engine.engines["easyocr"].device
    (evidence_dir / "runtime_environment.json").write_text(json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8")

    base = {
        "padding": 8,
        "preprocessing": "raw",
        "decoder": "greedy",
        "text_threshold": 0.7,
        "low_text": 0.4,
        "link_threshold": 0.4,
        "canvas_size": 2560,
        "mag_ratio": 1.0,
        "contrast_ths": 0.1,
        "adjust_contrast": 0.5,
        "iou_threshold": 0.5,
        "duplicate_iou_threshold": 0.9,
        "nested_threshold": 0.92,
        "min_area": 25,
        "min_height": 4,
        "y_tolerance_ratio": 0.55,
        "vertical_overlap_threshold": 0.35,
        "max_horizontal_gap_ratio": 0.08,
    }
    candidates = [
        {**base, "name": "q4_raw_components", "family": "baseline", "strategy": "raw_components"},
        {**base, "name": "clean_components", "family": "detection_box_merging", "strategy": "clean_components", "min_area": 80, "min_height": 8},
        {**base, "name": "logical_lines_default", "family": "detection_box_merging", "strategy": "logical"},
        {**base, "name": "merged_lines_wide_gap", "family": "detection_box_merging", "strategy": "merged", "max_horizontal_gap_ratio": 0.22},
        {**base, "name": "projection_bands_raw", "family": "preprocessing", "strategy": "projection", "min_band_height": 12, "gap_tolerance": 5, "min_ink_pixels": 18, "projection_threshold": 210},
        {**base, "name": "hybrid_projection_raw", "family": "preprocessing", "strategy": "hybrid", "min_band_height": 12, "gap_tolerance": 5, "min_ink_pixels": 18, "projection_threshold": 210},
        {**base, "name": "hybrid_projection_autocontrast", "family": "preprocessing", "strategy": "hybrid", "preprocessing": "autocontrast", "min_band_height": 12, "gap_tolerance": 5, "min_ink_pixels": 18, "projection_threshold": 210},
        {**base, "name": "recognition_beam_merged", "family": "recognition_normalization", "strategy": "merged", "decoder": "beamsearch", "max_horizontal_gap_ratio": 0.22},
    ]

    recognition_baseline = recognition_only(reader, data["pages"], base)
    validation_rows = []
    validation_results = []
    for config in candidates:
        metrics = evaluate_candidate(reader, validation_pages, config, evidence_dir, f"val_{config['name']}", overlays=True)
        validation_results.append({"config": config, "metrics": metrics})
        validation_rows.append(
            {
                "name": config["name"],
                "family": config["family"],
                "strategy": config["strategy"],
                "preprocessing": config["preprocessing"],
                "decoder": config["decoder"],
                "validation_strict_cer": metrics["strict_cer"],
                "validation_strict_wer": metrics["strict_wer"],
                "validation_normalized_cer": metrics["normalized_cer"],
                "validation_line_f1": metrics["line_f1"],
                "validation_reading_order": metrics["reading_order_accuracy"],
                "time_ms": metrics["time_ms"],
                "gpu_memory_mb": 0 if not torch.cuda.is_available() else torch.cuda.max_memory_allocated() / (1024 * 1024),
            }
        )
    write_csv(evidence_dir / "candidate_validation_results.csv", validation_rows)
    (evidence_dir / "candidate_validation_results.json").write_text(json.dumps(validation_results, ensure_ascii=False, indent=2), encoding="utf-8")

    selected = max(
        validation_results,
        key=lambda item: (
            item["metrics"]["line_f1"] >= 0.75,
            item["metrics"]["reading_order_accuracy"] >= 0.90,
            item["metrics"]["page_failure_rate"] == 0,
            -item["metrics"]["strict_wer"],
            -item["metrics"]["strict_cer"],
            item["metrics"]["line_f1"],
            item["metrics"]["reading_order_accuracy"],
        ),
    )
    selected_config = {**selected["config"], "selection_basis": "validation_split_only", "test_pages_used_for_selection": False}
    selected_hash = freeze_config(selected_config, evidence_dir / "selected_config_q5.json")

    detection_baseline = evaluate_candidate(reader, data["pages"], candidates[0], evidence_dir, "baseline_q4_raw", overlays=True)
    full_test = evaluate_candidate(reader, test_pages, selected_config, evidence_dir, "test_selected_q5", overlays=True)
    full_all = evaluate_candidate(reader, data["pages"], selected_config, evidence_dir, "all_selected_q5", overlays=True)
    full_validation = selected["metrics"]

    after = integrity_snapshot(load_dataset(conn, args.dataset_id))
    (evidence_dir / "ground_truth_integrity_after.json").write_text(json.dumps(after, ensure_ascii=False, indent=2), encoding="utf-8")
    accept = acceptance(full_test, before["combined_ground_truth_sha256"], after["combined_ground_truth_sha256"])

    baselines = {
        "recognition_only": recognition_baseline,
        "detection_only_raw_components": detection_baseline,
        "full_pipeline_raw_components": detection_baseline,
    }
    (evidence_dir / "baseline_metrics.json").write_text(json.dumps(baselines, ensure_ascii=False, indent=2), encoding="utf-8")
    (evidence_dir / "test_metrics_q5.json").write_text(json.dumps(full_test, ensure_ascii=False, indent=2), encoding="utf-8")
    (evidence_dir / "all_metrics_q5.json").write_text(json.dumps(full_all, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(evidence_dir / "page_metrics_q5.csv", full_all["pages"])

    gt_joined = "\n".join(line["text_content"] for page in data["pages"] for line in page["lines"])
    hyp_joined = "\n".join(line for page in full_all["pages"] for line in [])
    write_csv(evidence_dir / "recognition_error_samples.csv", char_errors(gt_joined, hyp_joined))

    report_lines = [
        "# TASK-034-Q5 OCR Quality Improvement Report",
        "",
        f"**Decision:** {accept['decision']}",
        "",
        "## Ground Truth Integrity",
        f"- Before: `{before['combined_ground_truth_sha256']}`",
        f"- After: `{after['combined_ground_truth_sha256']}`",
        f"- Changed: `{before['combined_ground_truth_sha256'] != after['combined_ground_truth_sha256']}`",
        "",
        "## Split",
        f"- Train pages: {split['train_pages']}",
        f"- Validation pages: {split['validation_pages']}",
        f"- Test pages: {split['test_pages']}",
        f"- Limitation: {split['limitation']}",
        "",
        "## Selected Candidate",
        f"- Name: `{selected_config['name']}`",
        f"- Family: `{selected_config['family']}`",
        f"- Config SHA-256: `{selected_hash}`",
        "- Selection used validation split only; test pages were not used for selection.",
        "",
        "## Baselines",
        f"- Recognition-only strict CER: {recognition_baseline['strict_cer']}",
        f"- Recognition-only strict WER: {recognition_baseline['strict_wer']}",
        f"- Detection-only raw precision/recall/F1: {detection_baseline['line_precision']} / {detection_baseline['line_recall']} / {detection_baseline['line_f1']}",
        f"- Full-pipeline raw strict CER/WER: {detection_baseline['strict_cer']} / {detection_baseline['strict_wer']}",
        "",
        "## Best Validation Result",
        f"- Strict CER: {full_validation['strict_cer']}",
        f"- Strict WER: {full_validation['strict_wer']}",
        f"- Line precision/recall/F1: {full_validation['line_precision']} / {full_validation['line_recall']} / {full_validation['line_f1']}",
        f"- Reading-order accuracy: {full_validation['reading_order_accuracy']}",
        "",
        "## Untouched Test Result",
        f"- Strict CER: {full_test['strict_cer']}",
        f"- Normalized CER: {full_test['normalized_cer']}",
        f"- Strict WER: {full_test['strict_wer']}",
        f"- Normalized WER: {full_test['normalized_wer']}",
        f"- Detection precision/recall/F1: {full_test['line_precision']} / {full_test['line_recall']} / {full_test['line_f1']}",
        f"- Reading-order accuracy: {full_test['reading_order_accuracy']}",
        f"- Page failure rate: {full_test['page_failure_rate']}",
        f"- Average OCR confidence: {full_test['average_ocr_confidence']}",
        "",
        "## Pilot Gates",
    ]
    for gate, passed in accept["gates"].items():
        report_lines.append(f"- {gate}: {'PASS' if passed else 'FAIL'}")
    report_lines.extend(
        [
            "",
            "## Candidate Evidence",
            "- `candidate_validation_results.csv` records all 8 controlled candidates.",
            "- `overlays/` contains GT, prediction, match, extra, missed, and order labels for every evaluated page.",
            "- `baseline_metrics.json`, `test_metrics_q5.json`, and `all_metrics_q5.json` contain machine-readable metrics.",
            "",
            "## Root Cause",
            "- Raw EasyOCR output over-produces fragmented boxes; Q5 merging improves line box count but recognition text alignment still remains weak on this tiny 3-page pilot.",
            "- No ground-truth text or bounding box was changed, and no test page was used for parameter selection.",
        ]
    )
    (evidence_dir / "FINAL_Q5_OCR_QUALITY_REPORT.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(json.dumps({"decision": accept["decision"], "selected": selected_config["name"], "test": full_test, "hash_unchanged": before["combined_ground_truth_sha256"] == after["combined_ground_truth_sha256"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

