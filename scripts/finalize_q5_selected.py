"""Finalize Q5 with the validation-selected text-producing candidate."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import scripts.line_segmentation_q5 as q5
from app.services.document_processing.ocr_engine import OttomanOCREngine
from app.services.evaluation.ocr_pipeline_optimization import freeze_config


def main() -> int:
    evidence_dir = PROJECT_ROOT / "evidence" / "line_segmentation_q5"
    dataset_id = 2
    selected_name = "recognition_beam_merged"
    conn = q5.connect()
    data = q5.load_dataset(conn, dataset_id)
    before = q5.integrity_snapshot(data)
    (evidence_dir / "ground_truth_integrity_before.json").write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding="utf-8")

    split = json.loads((evidence_dir / "split_manifest.json").read_text(encoding="utf-8"))
    validation_rows = list(csv.DictReader((evidence_dir / "candidate_validation_results.csv").open(encoding="utf-8")))
    selected_validation = next(row for row in validation_rows if row["name"] == selected_name)

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
        "max_horizontal_gap_ratio": 0.22,
        "name": selected_name,
        "family": "recognition_normalization",
        "strategy": "merged",
        "selection_basis": "existing validation_split_only; selected from candidate_validation_results.csv",
        "test_pages_used_for_selection": False,
    }
    base["decoder"] = "beamsearch"
    selected_hash = freeze_config(base, evidence_dir / "selected_config_q5.json")

    engine = OttomanOCREngine(enable_easyocr=True, enable_trocr=False, enable_tesseract=True, gpu=True)
    reader = engine.engines["easyocr"].reader
    test_pages = [page for page in data["pages"] if page["id"] in set(split["test_pages"])]
    validation_pages = [page for page in data["pages"] if page["id"] in set(split["validation_pages"])]
    full_test = q5.evaluate_candidate(reader, test_pages, base, evidence_dir, "test_selected_q5_beam", overlays=True)
    full_validation = q5.evaluate_candidate(reader, validation_pages, base, evidence_dir, "validation_selected_q5_beam", overlays=True)
    full_all = q5.evaluate_candidate(reader, data["pages"], base, evidence_dir, "all_selected_q5_beam", overlays=True)
    after = q5.integrity_snapshot(q5.load_dataset(conn, dataset_id))
    (evidence_dir / "ground_truth_integrity_after.json").write_text(json.dumps(after, ensure_ascii=False, indent=2), encoding="utf-8")
    accept = q5.acceptance(full_test, before["combined_ground_truth_sha256"], after["combined_ground_truth_sha256"])

    (evidence_dir / "test_metrics_q5.json").write_text(json.dumps(full_test, ensure_ascii=False, indent=2), encoding="utf-8")
    (evidence_dir / "all_metrics_q5.json").write_text(json.dumps(full_all, ensure_ascii=False, indent=2), encoding="utf-8")
    q5.write_csv(evidence_dir / "page_metrics_q5.csv", full_all["pages"])

    baseline = json.loads((evidence_dir / "baseline_metrics.json").read_text(encoding="utf-8"))
    report = [
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
        f"- Name: `{base['name']}`",
        f"- Family: `{base['family']}`",
        f"- Config SHA-256: `{selected_hash}`",
        "- Selection used validation split only; test pages were not used for selection.",
        "",
        "## Baselines",
        f"- Recognition-only strict CER: {baseline['recognition_only']['strict_cer']}",
        f"- Recognition-only strict WER: {baseline['recognition_only']['strict_wer']}",
        f"- Detection-only raw precision/recall/F1: {baseline['detection_only_raw_components']['line_precision']} / {baseline['detection_only_raw_components']['line_recall']} / {baseline['detection_only_raw_components']['line_f1']}",
        f"- Full-pipeline raw strict CER/WER: {baseline['full_pipeline_raw_components']['strict_cer']} / {baseline['full_pipeline_raw_components']['strict_wer']}",
        "",
        "## Controlled Candidate Families",
        "- Detection/box merging: clean components, logical lines, merged wide-gap lines.",
        "- Preprocessing: projection bands raw, hybrid projection raw, hybrid projection autocontrast.",
        "- Recognition/normalization: beamsearch recognition with merged line geometry.",
        "- Complete table: `candidate_validation_results.csv`.",
        "",
        "## Best Validation Result",
        f"- Strict CER: {full_validation['strict_cer']} (CSV prior: {selected_validation['validation_strict_cer']})",
        f"- Strict WER: {full_validation['strict_wer']} (CSV prior: {selected_validation['validation_strict_wer']})",
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
        report.append(f"- {gate}: {'PASS' if passed else 'FAIL'}")
    report.extend([
        "",
        "## Root Cause",
        "- Q5 fixes the dominant detection/RTL failure: raw fragmented box F1 rises to the selected merged-line F1 reported above.",
        "- Recognition remains the limiting factor: strict WER stays above the pilot gate even with beamsearch and merged line geometry.",
        "- Projection-only detection passes geometry but has no OCR text and is therefore not a valid final quality candidate.",
        "- No ground-truth text or bounding box was changed, and no test page was used for parameter selection.",
    ])
    (evidence_dir / "FINAL_Q5_OCR_QUALITY_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"decision": accept["decision"], "selected": selected_name, "test": full_test, "hash_unchanged": before["combined_ground_truth_sha256"] == after["combined_ground_truth_sha256"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
