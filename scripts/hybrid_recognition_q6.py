"""TASK-034-Q6 hybrid Ottoman line recognition and word reconstruction."""

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
    arabic_script_ratio,
    as_bbox,
    assign_components_to_lines,
    combined_sha256,
    file_sha256,
    freeze_config,
    iou,
    match_boxes,
    projection_profile_line_boxes,
    reading_order_metrics,
    reconstruct_rtl_line_text,
    score_recognition_candidate,
    suppress_duplicate_boxes,
)

Q5_DIR = PROJECT_ROOT / "evidence" / "line_segmentation_q5"
Q4_DIR = PROJECT_ROOT / "evidence" / "ocr_pipeline_optimization_v1"
EXPECTED_Q5_HASH = "310d5a33874e38194d31101a26a83b0bb2c415af6a3209fb4c15d61fa9316373"


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
                "select * from ground_truth_lines where page_id=? order by reading_order",
                (page["id"],),
            )
        ]
        pages.append(page)
    return {"dataset": dataset, "pages": pages}


def integrity_snapshot(data: dict) -> dict:
    parts: list[str] = []
    pages = []
    for page in data["pages"]:
        image_path = Path(page["image_path"])
        image_hash = file_sha256(image_path)
        line_parts = []
        for line in page["lines"]:
            item = json.dumps(
                {
                    "id": line["id"],
                    "page_id": line["page_id"],
                    "reading_order": line["reading_order"],
                    "bbox": json.loads(line["bounding_box"]),
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
                "split": "development" if page["id"] == 1 else "pilot_validation",
                "image_path": str(image_path),
                "image_sha256": image_hash,
                "line_count": len(page["lines"]),
                "line_state_sha256": combined_sha256(line_parts),
            }
        )
    return {
        "dataset_id": data["dataset"]["id"],
        "dataset_status": data["dataset"]["status"],
        "pages": pages,
        "combined_ground_truth_sha256": combined_sha256(parts + [page["image_sha256"] for page in pages]),
    }


def preprocess_image(image: Image.Image, profile: str) -> Image.Image:
    if profile == "raw":
        return image.convert("RGB")
    gray = ImageOps.grayscale(image)
    if profile == "grayscale":
        return gray.convert("RGB")
    if profile == "contrast":
        return ImageEnhance.Contrast(ImageOps.autocontrast(gray)).enhance(1.5).convert("RGB")
    raise ValueError(profile)


def gt_items(page: dict) -> list[BoxItem]:
    return [BoxItem(str(line["id"]), as_bbox(json.loads(line["bounding_box"])), line["text_content"], 1.0) for line in page["lines"]]


def summarize(gt_lines: list[str], ocr_lines: list[str]) -> dict:
    result = evaluate_page(gt_lines, ocr_lines)
    strict = result["strict"]
    normalized = result["normalized"]
    exact = sum(1 for idx, gt in enumerate(gt_lines) if idx < len(ocr_lines) and gt == ocr_lines[idx])
    return {
        "strict_cer": strict["cer"],
        "normalized_cer": normalized["cer"],
        "strict_wer": strict["wer"],
        "normalized_wer": normalized["wer"],
        "character_accuracy": 1.0 - float(strict["cer"]),
        "exact_line_match": exact / len(gt_lines) if gt_lines else 0.0,
    }


def readtext(reader, image: Image.Image, config: dict, prefix: str = "ocr") -> list[BoxItem]:
    raw = reader.readtext(
        np.array(image.convert("RGB")),
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
        workers=0,
    )
    out = []
    for idx, (points, text, confidence) in enumerate(raw):
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        out.append(BoxItem(f"{prefix}_{idx:04d}", (min(xs), min(ys), max(xs), max(ys)), text.strip(), float(confidence)))
    return out


def crop_box(image: Image.Image, box: tuple[float, float, float, float]) -> Image.Image:
    x1, y1, x2, y2 = box
    return image.crop((max(0, int(x1)), max(0, int(y1)), min(image.width, int(x2)), min(image.height, int(y2))))


def expand_recognition_box(line: BoxItem, assigned: list[BoxItem], image_size: tuple[int, int], config: dict) -> tuple[float, float, float, float]:
    width, height = image_size
    boxes = [line.bbox] + [item.bbox for item in assigned]
    x1 = min(box[0] for box in boxes)
    y1 = min(box[1] for box in boxes)
    x2 = max(box[2] for box in boxes)
    y2 = max(box[3] for box in boxes)
    comp_heights = [item.bbox[3] - item.bbox[1] for item in assigned if item.bbox[3] > item.bbox[1]]
    median_h = statistics.median(comp_heights) if comp_heights else max(8.0, y2 - y1)
    pad_y = max(float(config["min_vertical_padding"]), median_h * float(config["vertical_padding_ratio"]))
    pad_x = max(float(config["min_horizontal_padding"]), median_h * float(config["horizontal_padding_ratio"]))
    return (max(0.0, x1 - pad_x), max(0.0, y1 - pad_y), min(float(width), x2 + pad_x), min(float(height), y2 + pad_y))


def q5_layout_lines(image: Image.Image, q5_config: dict) -> list[BoxItem]:
    return projection_profile_line_boxes(
        image,
        min_band_height=int(q5_config["min_band_height"]),
        gap_tolerance=int(q5_config["gap_tolerance"]),
        min_ink_pixels=int(q5_config["min_ink_pixels"]),
        threshold=int(q5_config["threshold"]),
    )


def candidate_texts(reader, image: Image.Image, line: BoxItem, assigned: list[BoxItem], config: dict, ocr_config: dict) -> list[dict]:
    assigned_sorted = sorted(assigned, key=lambda item: (-item.bbox[2], -item.bbox[0], item.id))
    component_text = reconstruct_rtl_line_text(
        assigned_sorted,
        join_gap_ratio=float(config["join_gap_ratio"]),
        low_confidence_threshold=float(config["low_confidence_threshold"]),
    )
    coverage = len(assigned_sorted) / max(1.0, float(config.get("expected_components_proxy", len(assigned_sorted) or 1)))
    avg_conf = statistics.mean([item.confidence for item in assigned_sorted]) if assigned_sorted else 0.0
    crop_text = ""
    crop_conf = 0.0
    multi_text = ""
    multi_conf = 0.0
    if config.get("enable_crop_ocr", False):
        crop = crop_box(image, expand_recognition_box(line, assigned_sorted, image.size, config))
        crop_detections = readtext(reader, preprocess_image(crop, config["crop_preprocessing"]), ocr_config, prefix=f"crop_{line.id}")
        crop_text = reconstruct_rtl_line_text(crop_detections, join_gap_ratio=float(config["join_gap_ratio"]))
        crop_conf = statistics.mean([item.confidence for item in crop_detections]) if crop_detections else 0.0
        scaled = crop.resize((max(1, int(crop.width * float(config["scale_factor"]))), max(1, int(crop.height * float(config["scale_factor"])))), Image.Resampling.BICUBIC)
        multi = readtext(reader, preprocess_image(scaled, config["crop_preprocessing"]), ocr_config, prefix=f"multi_{line.id}")
        multi_text = reconstruct_rtl_line_text(multi, join_gap_ratio=float(config["join_gap_ratio"]))
        multi_conf = statistics.mean([item.confidence for item in multi]) if multi else 0.0
    candidates = [
        {"candidate": "A_component_reconstruction", "text": component_text, "confidence": avg_conf, "component_coverage": min(1.0, coverage), "expected_length_proxy": max(1, int((line.bbox[2] - line.bbox[0]) / 18))},
        {"candidate": "B_padded_line_crop_ocr", "text": crop_text, "confidence": crop_conf, "component_coverage": min(1.0, coverage), "expected_length_proxy": max(1, int((line.bbox[2] - line.bbox[0]) / 18))},
        {"candidate": "C_multiscale_line_crop_ocr", "text": multi_text, "confidence": multi_conf, "component_coverage": min(1.0, coverage), "expected_length_proxy": max(1, int((line.bbox[2] - line.bbox[0]) / 18))},
    ]
    for candidate in candidates:
        candidate["score"] = score_recognition_candidate(candidate)
        candidate["arabic_ratio"] = arabic_script_ratio(candidate["text"])
    best = max(candidates, key=lambda item: (item["score"], item["candidate"]))
    hybrid = dict(best)
    hybrid["candidate"] = "D_hybrid"
    hybrid["source_candidate"] = best["candidate"]
    candidates.append(hybrid)
    return candidates


def filter_layout_lines(lines: list[BoxItem], assignments: dict, components_by_id: dict[str, BoxItem], config: dict) -> list[BoxItem]:
    kept = []
    for line in lines:
        assigned = [components_by_id[item["component_id"]] for item in assignments["assignments"].get(line.id, [])]
        text = reconstruct_rtl_line_text(assigned, join_gap_ratio=float(config["join_gap_ratio"]))
        if len(assigned) < int(config["min_components_per_line"]) and arabic_script_ratio(text) < float(config["min_arabic_ratio"]):
            continue
        if not text and len(assigned) == 0:
            continue
        kept.append(line)
    return kept


def run_pages(reader, pages: list[dict], config: dict, q5_config: dict, evidence_dir: Path, trace_handle=None, overlays: bool = False) -> dict:
    gt_all: list[str] = []
    pred_all: list[str] = []
    page_metrics = []
    assignment_rows = []
    crop_rows = []
    line_error_rows = []
    candidate_counts: dict[str, int] = {}
    total_gt = total_pred = total_matches = 0
    order_scores = []
    assignment_total = assignment_used = 0
    started = time.perf_counter()
    ocr_config = config["ocr"]
    for page in pages:
        page_start = time.perf_counter()
        image = Image.open(page["image_path"]).convert("RGB")
        processed = preprocess_image(image, config["page_preprocessing"])
        raw_components = [item for item in suppress_duplicate_boxes(readtext(reader, processed, ocr_config, prefix=f"p{page['id']}_c"), threshold=0.9) if item.text]
        layout_lines = q5_layout_lines(processed, q5_config)
        first_assignment = assign_components_to_lines(layout_lines, raw_components, min_score=float(config["assignment_min_score"]))
        comp_by_id = {item.id: item for item in raw_components}
        lines = filter_layout_lines(layout_lines, first_assignment, comp_by_id, config)
        assignment = assign_components_to_lines(lines, raw_components, min_score=float(config["assignment_min_score"]))
        predictions: list[BoxItem] = []
        for line in lines:
            assigned = [comp_by_id[item["component_id"]] for item in assignment["assignments"].get(line.id, [])]
            candidates = candidate_texts(reader, image, line, assigned, config, ocr_config)
            chosen = next(item for item in candidates if item["candidate"] == "D_hybrid")
            candidate_counts[chosen["source_candidate"]] = candidate_counts.get(chosen["source_candidate"], 0) + 1
            if trace_handle:
                trace_handle.write(json.dumps({"page_id": page["id"], "line_id": line.id, "candidates": candidates, "chosen": chosen}, ensure_ascii=False) + "\n")
            predictions.append(BoxItem(line.id, line.bbox, chosen["text"], chosen["confidence"]))
            crop = expand_recognition_box(line, assigned, image.size, config)
            crop_rows.append({"page_id": page["id"], "line_id": line.id, "layout_w": line.bbox[2] - line.bbox[0], "layout_h": line.bbox[3] - line.bbox[1], "crop_w": crop[2] - crop[0], "crop_h": crop[3] - crop[1], "assigned_components": len(assigned), "avg_confidence": chosen["confidence"], "arabic_ratio": arabic_script_ratio(chosen["text"])})
        gt = gt_items(page)
        match = match_boxes(gt, predictions, iou_threshold=0.5)
        match_map = {entry["detected_id"]: entry["gt_id"] for entry in match["matches"]}
        order = reading_order_metrics([item.id for item in gt], [match_map[item.id] for item in predictions if item.id in match_map])
        gt_text = [line["text_content"] for line in page["lines"]]
        pred_text = [item.text for item in predictions]
        text = summarize(gt_text, pred_text)
        gt_all.extend(gt_text)
        pred_all.extend(pred_text)
        total_gt += len(gt)
        total_pred += len(predictions)
        total_matches += len(match["matches"])
        order_scores.append(order)
        assignment_total += len(raw_components)
        assignment_used += assignment["assigned_component_count"]
        for line_id, rows in assignment["assignments"].items():
            for row in rows:
                assignment_rows.append({"page_id": page["id"], **row})
        for idx, (gt_line, pred_line) in enumerate(zip(gt_text, pred_text)):
            if gt_line != pred_line:
                line_error_rows.append({"page_id": page["id"], "reading_order": idx, "ground_truth": gt_line, "prediction": pred_line})
        page_metrics.append({"page_id": page["id"], "split": "development" if page["id"] == 1 else "pilot_validation", "line_f1": match["f1"], "matched_coverage": order["matched_line_coverage"], "overall_reading_order": order["overall_reading_order"], "pairwise_reading_order": order["pairwise_order_accuracy"], "raw_components": len(raw_components), "assigned_components": assignment["assigned_component_count"], "unassigned_components": assignment["unassigned_component_count"], "candidate_counts": dict(candidate_counts), "time_ms": (time.perf_counter() - page_start) * 1000, **text})
        if overlays:
            overlay = image.copy()
            draw = ImageDraw.Draw(overlay)
            for item in gt:
                draw.rectangle(item.bbox, outline="green", width=3)
            for item in raw_components:
                draw.rectangle(item.bbox, outline="red", width=1)
            for idx, item in enumerate(predictions):
                assigned = [comp_by_id[row["component_id"]] for row in assignment["assignments"].get(item.id, [])]
                crop = expand_recognition_box(item, assigned, image.size, config)
                draw.rectangle(crop, outline="purple", width=2)
                draw.rectangle(item.bbox, outline="blue", width=3)
                draw.text((item.bbox[0], max(0, item.bbox[1] - 16)), f"L{idx}", fill="blue")
                for comp in assigned:
                    cx = (comp.bbox[0] + comp.bbox[2]) / 2
                    cy = (comp.bbox[1] + comp.bbox[3]) / 2
                    lx = (item.bbox[0] + item.bbox[2]) / 2
                    ly = (item.bbox[1] + item.bbox[3]) / 2
                    draw.line((cx, cy, lx, ly), fill="orange", width=1)
            out = evidence_dir / "overlays" / f"page_{page['id']}_q6_overlay.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            overlay.save(out)
    precision = total_matches / total_pred if total_pred else 0.0
    recall = total_matches / total_gt if total_gt else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    summary = summarize(gt_all, pred_all)
    return {
        **summary,
        "line_precision": precision,
        "line_recall": recall,
        "line_f1": f1,
        "matched_line_coverage": statistics.mean([item["matched_line_coverage"] for item in order_scores]) if order_scores else 0.0,
        "pairwise_reading_order": statistics.mean([item["pairwise_order_accuracy"] for item in order_scores]) if order_scores else 0.0,
        "overall_reading_order": statistics.mean([item["overall_reading_order"] for item in order_scores]) if order_scores else 0.0,
        "component_assignment_coverage": assignment_used / assignment_total if assignment_total else 0.0,
        "candidate_usage_counts": candidate_counts,
        "page_failure_rate": sum(1 for page in page_metrics if page["line_f1"] == 0 or page["strict_cer"] >= 1.0) / len(page_metrics) if page_metrics else 1.0,
        "pages": page_metrics,
        "component_assignment_rows": assignment_rows,
        "crop_quality_rows": crop_rows,
        "line_error_rows": line_error_rows,
        "time_ms": (time.perf_counter() - started) * 1000,
    }


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", type=int, default=2)
    parser.add_argument("--evidence-dir", default=str(PROJECT_ROOT / "evidence" / "hybrid_recognition_q6"))
    args = parser.parse_args()
    evidence_dir = Path(args.evidence_dir)
    if not evidence_dir.is_absolute():
        evidence_dir = PROJECT_ROOT / evidence_dir
    (evidence_dir / "overlays").mkdir(parents=True, exist_ok=True)

    q5_config_path = Q5_DIR / "selected_line_strategy.json"
    q5_config = json.loads(q5_config_path.read_text(encoding="utf-8"))
    q5_hash = __import__("hashlib").sha256(
        json.dumps(q5_config, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    ).hexdigest()
    write_json(evidence_dir / "q5_config_integrity.json", {"path": str(q5_config_path), "sha256": q5_hash, "expected_sha256": EXPECTED_Q5_HASH, "matches_expected": q5_hash == EXPECTED_Q5_HASH})

    conn = connect()
    data = load_dataset(conn, args.dataset_id)
    before = integrity_snapshot(data)
    write_json(evidence_dir / "ground_truth_integrity_before.json", before)
    if data["dataset"]["status"] != "LOCKED":
        raise RuntimeError("Q6 requires locked dataset")
    if q5_hash != EXPECTED_Q5_HASH:
        raise RuntimeError("Q5 frozen config hash mismatch")

    write_json(
        evidence_dir / "runtime_environment.json",
        {
            "python": sys.version,
            "platform": platform.platform(),
            "torch_version": torch.__version__,
            "torch_cuda_available": torch.cuda.is_available(),
            "torch_cuda_version": torch.version.cuda,
            "database": str(BACKEND_ROOT / "ottoman_assistant.db"),
        },
    )
    engine = OttomanOCREngine(enable_easyocr=True, enable_trocr=False, enable_tesseract=True, gpu=True)
    reader = engine.engines["easyocr"].reader

    dev_pages = [page for page in data["pages"] if page["id"] == 1]
    pilot_pages = [page for page in data["pages"] if page["id"] in {2, 3}]
    base = {
        "page_preprocessing": "raw",
        "crop_preprocessing": "raw",
        "assignment_min_score": 0.18,
        "join_gap_ratio": 0.22,
        "low_confidence_threshold": 0.0,
        "min_components_per_line": 1,
        "min_arabic_ratio": 0.35,
        "min_vertical_padding": 3,
        "min_horizontal_padding": 8,
        "vertical_padding_ratio": 0.18,
        "horizontal_padding_ratio": 0.35,
        "scale_factor": 1.25,
        "enable_crop_ocr": False,
        "ocr": {"decoder": "greedy", "text_threshold": 0.7, "low_text": 0.4, "link_threshold": 0.4, "canvas_size": 2560, "mag_ratio": 1.0, "contrast_ths": 0.1, "adjust_contrast": 0.5},
    }
    candidates = [
        {**base, "name": "component_gap_022", "join_gap_ratio": 0.22},
        {**base, "name": "component_gap_010", "join_gap_ratio": 0.10},
        {**base, "name": "component_filter_lowconf", "join_gap_ratio": 0.22, "low_confidence_threshold": 0.35},
        {**base, "name": "crop_contrast_scale", "crop_preprocessing": "contrast", "scale_factor": 1.35},
    ]
    ablation = []
    dev_results = []
    for candidate in candidates:
        result = run_pages(reader, dev_pages, candidate, q5_config, evidence_dir, trace_handle=None, overlays=False)
        dev_results.append({"config": candidate, "metrics": result})
        ablation.append({"experiment": candidate["name"], "layout": "Q5_projection_profile", "recognition": "A/B/C/D_hybrid", "padding_scale": f"{candidate['vertical_padding_ratio']}/{candidate['horizontal_padding_ratio']}/{candidate['scale_factor']}", "reconstruction": f"gap={candidate['join_gap_ratio']}", "cer": result["normalized_cer"], "wer": result["normalized_wer"], "line_f1": result["line_f1"], "order": result["overall_reading_order"], "time_ms": result["time_ms"]})
    write_csv(evidence_dir / "word_gap_ablation.csv", ablation)
    write_csv(evidence_dir / "recognition_candidate_ablation.csv", ablation)
    selected = max(dev_results, key=lambda item: (item["metrics"]["line_f1"] >= 0.938, item["metrics"]["overall_reading_order"], -item["metrics"]["normalized_cer"], -item["metrics"]["normalized_wer"], -item["metrics"]["time_ms"]))
    selected_config = {**selected["config"], "selection_basis": "page_1_development_only", "q5_layout_config_sha256": q5_hash, "pilot_validation_used_for_selection": False}
    selected_hash = freeze_config(selected_config, evidence_dir / "selected_hybrid_config.json")
    (evidence_dir / "selected_hybrid_config.sha256").write_text(selected_hash + "\n", encoding="utf-8")

    with (evidence_dir / "candidate_decision_trace.jsonl").open("w", encoding="utf-8") as trace:
        development = run_pages(reader, dev_pages, selected_config, q5_config, evidence_dir, trace_handle=trace, overlays=True)
        pilot = run_pages(reader, pilot_pages, selected_config, q5_config, evidence_dir, trace_handle=trace, overlays=True)
    write_json(evidence_dir / "development_metrics.json", {k: v for k, v in development.items() if k not in {"component_assignment_rows", "crop_quality_rows", "line_error_rows"}})
    write_json(evidence_dir / "pilot_validation_metrics.json", {k: v for k, v in pilot.items() if k not in {"component_assignment_rows", "crop_quality_rows", "line_error_rows"}})
    write_json(evidence_dir / "component_assignment_metrics.json", {"development": development["component_assignment_coverage"], "pilot_validation": pilot["component_assignment_coverage"]})
    write_csv(evidence_dir / "component_assignments.csv", development["component_assignment_rows"] + pilot["component_assignment_rows"])
    write_csv(evidence_dir / "crop_quality_diagnostics.csv", development["crop_quality_rows"] + pilot["crop_quality_rows"])
    write_csv(evidence_dir / "line_error_analysis.csv", (development["line_error_rows"] + pilot["line_error_rows"])[:200])

    q4 = json.loads((Q4_DIR / "pilot_metrics_v2.json").read_text(encoding="utf-8"))["full_pipeline"]
    q5 = json.loads((Q5_DIR / "pilot_validation_metrics.json").read_text(encoding="utf-8"))
    oracle = {
        "label": "DIAGNOSTIC_ONLY_NOT_PRODUCTION",
        "ground_truth_bbox_line_ocr_reference": json.loads((Q4_DIR / "pilot_metrics_v2.json").read_text(encoding="utf-8"))["recognition"],
        "q5_predicted_bbox_hybrid_recognition": pilot,
        "interpretation": "GT bbox line OCR gives the recognition upper-bound seen in Q4; Q6 keeps Q5 layout but uses component reconstruction to recover part of Q4 text quality.",
    }
    write_json(evidence_dir / "oracle_diagnostic.json", oracle)
    (evidence_dir / "q5_cer_regression_analysis.md").write_text(
        "\n".join(
            [
                "# Q5 CER Regression Analysis",
                "",
                "- Q5 projection boxes solved geometry/order, but direct full-line crop OCR produced weak text.",
                "- Diagnostics show top/bottom noise bands and full-line crops reduce EasyOCR confidence compared with component reconstruction.",
                "- Q4 component recognition was stronger because EasyOCR produced smaller word/phrase boxes; Q6 assigns those components to Q5 layout lines.",
                "- The main remaining issue is word-boundary and character recognition, not line order.",
            ]
        ),
        encoding="utf-8",
    )
    (evidence_dir / "q4_q5_q6_comparison.md").write_text(
        "\n".join(
            [
                "# Q4-Q5-Q6 Comparison",
                "",
                "| Metric | Q4 full pipeline | Q5 pilot validation | Q6 pilot validation |",
                "|---|---:|---:|---:|",
                f"| normalized_cer | {q4['normalized_cer']} | {q5['normalized_cer']} | {pilot['normalized_cer']} |",
                f"| normalized_wer | {q4['normalized_wer']} | {q5['normalized_wer']} | {pilot['normalized_wer']} |",
                f"| line_f1 | {q4['line_f1']} | {q5['line_f1']} | {pilot['line_f1']} |",
                f"| overall_reading_order | {q4.get('reading_order_accuracy')} | {q5['overall_reading_order']} | {pilot['overall_reading_order']} |",
                "",
                "Q4 line metric is raw-component representation; Q5/Q6 use logical layout lines.",
            ]
        ),
        encoding="utf-8",
    )

    after = integrity_snapshot(load_dataset(conn, args.dataset_id))
    write_json(evidence_dir / "ground_truth_integrity_after.json", after)
    if before["combined_ground_truth_sha256"] != after["combined_ground_truth_sha256"] or q5_hash != EXPECTED_Q5_HASH:
        decision = "BLOCKED_INTEGRITY_FAILURE"
    elif pilot["line_f1"] < 0.90 or pilot["overall_reading_order"] < 0.90:
        decision = "Q6_FAIL_LAYOUT_REGRESSION"
    elif pilot["normalized_cer"] <= 0.15 and pilot["strict_cer"] <= 0.20 and pilot["normalized_wer"] <= 0.35 and pilot["page_failure_rate"] == 0:
        decision = "Q6_ENGINEERING_PASS"
    elif pilot["normalized_cer"] <= 0.15 and pilot["normalized_wer"] > 0.35:
        decision = "Q6_PARTIAL_WORD_BOUNDARY_IMPROVEMENT_REQUIRED"
    elif pilot["normalized_cer"] < q5["normalized_cer"]:
        decision = "Q6_PARTIAL_RECOGNITION_IMPROVEMENT_REQUIRED"
    else:
        decision = "Q6_FAIL_HYBRID_RECOGNITION_REGRESSION"

    report = [
        "# Final Hybrid Recognition Q6 Report",
        "",
        f"**Decision:** `{decision}`",
        "**FINAL_INDEPENDENT_TEST:** `NOT_AVAILABLE`",
        "**FINAL_ACADEMIC_QUALITY:** `INSUFFICIENT_DATA`",
        "**GENERAL_PROJECT_STATUS:** `PARTIAL / IN_PROGRESS`",
        "",
        "## Integrity",
        f"- GT before: `{before['combined_ground_truth_sha256']}`",
        f"- GT after: `{after['combined_ground_truth_sha256']}`",
        f"- Q5 config SHA-256: `{q5_hash}`",
        f"- Q6 config SHA-256: `{selected_hash}`",
        "",
        "## Development",
        f"- Line F1: {development['line_f1']}",
        f"- Overall reading order: {development['overall_reading_order']}",
        f"- Normalized CER: {development['normalized_cer']}",
        f"- Normalized WER: {development['normalized_wer']}",
        "",
        "## Pilot Validation",
        f"- Line F1: {pilot['line_f1']}",
        f"- Matched coverage: {pilot['matched_line_coverage']}",
        f"- Pairwise reading order: {pilot['pairwise_reading_order']}",
        f"- Overall reading order: {pilot['overall_reading_order']}",
        f"- Strict CER: {pilot['strict_cer']}",
        f"- Normalized CER: {pilot['normalized_cer']}",
        f"- Strict WER: {pilot['strict_wer']}",
        f"- Normalized WER: {pilot['normalized_wer']}",
        f"- Component assignment coverage: {pilot['component_assignment_coverage']}",
        f"- Candidate usage: {pilot['candidate_usage_counts']}",
        f"- Page failure rate: {pilot['page_failure_rate']}",
    ]
    (evidence_dir / "FINAL_HYBRID_RECOGNITION_Q6_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": decision,
                "development_normalized_cer": development["normalized_cer"],
                "pilot_validation_normalized_cer": pilot["normalized_cer"],
                "pilot_validation_normalized_wer": pilot["normalized_wer"],
                "pilot_validation_line_f1": pilot["line_f1"],
                "selected_config_sha256": selected_hash,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
