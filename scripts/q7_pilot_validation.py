"""Pilot validation for Q7 Word Boundary configuration."""

import sys
import json
import csv
import time
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.evaluation.ocr_pipeline_optimization import (
    reading_order_metrics, 
    match_boxes,
    BoxItem,
    arabic_script_ratio,
    suppress_duplicate_boxes
)
from scripts.hybrid_recognition_q6 import summarize, gt_items, preprocess_image, q5_layout_lines, filter_layout_lines, assign_components_to_lines
from app.services.document_processing.word_boundary import reconstruct_rtl_line_text_v2
from app.services.document_processing.ocr_engine import OttomanOCREngine

Q7_DIR = Path(__file__).resolve().parents[1] / "evidence" / "word_boundary_q7"
Q6_DIR = Path(__file__).resolve().parents[1] / "evidence" / "hybrid_recognition_q6"

def load_data():
    conn = sqlite3.connect(Path(__file__).resolve().parents[1] / "backend" / "ottoman_assistant.db")
    conn.row_factory = sqlite3.Row
    pages = []
    for row in conn.execute("select * from ground_truth_pages where dataset_id=2 and id in (2, 3) order by id"):
        page = dict(row)
        page["lines"] = [
            dict(line)
            for line in conn.execute(
                "select * from ground_truth_lines where page_id=? order by reading_order",
                (page["id"],),
            )
        ]
        pages.append(page)
    return pages

def main():
    print("Starting Q7 Pilot Validation...")
    pages = load_data()
    
    q5_config = json.loads((Q7_DIR.parent / "line_segmentation_q5" / "selected_line_strategy.json").read_text(encoding="utf-8"))
    q6_config = json.loads((Q6_DIR / "selected_hybrid_config.json").read_text(encoding="utf-8"))
    q7_config = {
        "name": f"Strategy F - Always Space",
        "strategy": "hybrid",
        "gap_weight": 0.0,
        "joining_penalty": 0.0,
        "punctuation_bonus": 0.0,
        "digit_bonus": 0.0,
        "boundary_score_threshold": -1.0, 
        "low_confidence_threshold": 0.0,
        "enable_internal_split": False
    }
    engine = OttomanOCREngine(enable_easyocr=True, enable_trocr=False, enable_tesseract=True, gpu=True)
    reader = engine.engines["easyocr"].reader
    
    gt_all = []
    pred_all = []
    total_gt = total_pred = total_matches = 0
    order_scores = []
    page_metrics = []
    
    start_t = time.perf_counter()
    
    import torch
    from PIL import Image
    from scripts.hybrid_recognition_q6 import readtext
    
    trace_handle = open(Q7_DIR / "boundary_decision_trace.jsonl", "w", encoding="utf-8")
    
    for page in pages:
        page_start = time.perf_counter()
        image = Image.open(page["image_path"]).convert("RGB")
        processed = preprocess_image(image, q6_config["page_preprocessing"])
        
        raw_components = readtext(reader, processed, q6_config["ocr"], prefix="c")
        raw_components = [item for item in suppress_duplicate_boxes(raw_components, threshold=0.9) if item.text]
        
        layout_lines = q5_layout_lines(processed, q5_config)
        first_assignment = assign_components_to_lines(layout_lines, raw_components, min_score=float(q6_config["assignment_min_score"]))
        comp_by_id = {item.id: item for item in raw_components}
        
        lines = filter_layout_lines(layout_lines, first_assignment, comp_by_id, q6_config)
        assignment = assign_components_to_lines(lines, raw_components, min_score=float(q6_config["assignment_min_score"]))
        
        gt = gt_items(page)
        gt_texts = [line["text_content"] for line in page["lines"]]
        
        predictions = []
        assigned_ids = set()
        for line in lines:
            assigned = [comp_by_id[item["component_id"]] for item in assignment["assignments"].get(line.id, [])]
            for comp in assigned:
                assigned_ids.add(comp.id)
            text = reconstruct_rtl_line_text_v2(assigned, q7_config)
            predictions.append(BoxItem(line.id, line.bbox, text, 1.0))
            
            trace_handle.write(json.dumps({
                "page_id": page["id"],
                "line_id": line.id,
                "assigned_components_count": len(assigned),
                "text": text
            }, ensure_ascii=False) + "\n")
            
        leftovers = [comp for comp in raw_components if comp.id not in assigned_ids]
        if leftovers:
            from app.services.evaluation.ocr_pipeline_optimization import logical_line_items
            extra_lines = logical_line_items(leftovers, id_prefix="extra")
            # For extra lines, we must also apply the word_boundary reconstruction (always space)
            # Actually, extra_lines already has the joined text, but it's joined by default spaces.
            # Strategy F always uses space anyway. So extra_lines is perfect.
            for idx, extra in enumerate(extra_lines):
                # We need to split the extra line back into its components to apply reconstruct_rtl_line_text_v2?
                # For Strategy F it's the same, but let's just use extra.text
                predictions.append(BoxItem(f"extra_{idx}", extra.bbox, extra.text, 1.0))
                
        match = match_boxes(gt, predictions, iou_threshold=0.5)
        match_map = {entry["detected_id"]: entry["gt_id"] for entry in match["matches"]}
        order = reading_order_metrics([item.id for item in gt], [match_map[item.id] for item in predictions if item.id in match_map])
        
        predictions.sort(key=lambda item: (item.bbox[1], -item.bbox[2], item.id))
        pred_texts = [item.text for item in predictions]
        summary = summarize(gt_texts, pred_texts)
        
        precision = len(match["matches"]) / len(predictions) if predictions else 0.0
        recall = len(match["matches"]) / len(gt) if gt else 0.0
        boundary_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        
        gt_all.extend(gt_texts)
        pred_all.extend(pred_texts)
        total_gt += len(gt)
        total_pred += len(predictions)
        total_matches += len(match["matches"])
        order_scores.append(order)
        
        page_metrics.append({
            "page_id": page["id"],
            "split": "pilot_validation",
            "boundary_p": precision,
            "boundary_r": recall,
            "boundary_f1": boundary_f1,
            "line_f1": match["f1"],
            "matched_coverage": order["matched_line_coverage"],
            "pairwise_reading_order": order["pairwise_order_accuracy"],
            "overall_reading_order": order["overall_reading_order"],
            **summary,
            "time_ms": (time.perf_counter() - page_start) * 1000
        })
        
        # Optionally generate overlays
        import PIL.ImageDraw as ImageDraw
        overlay = image.copy()
        draw = ImageDraw.Draw(overlay)
        for item in gt:
            draw.rectangle(item.bbox, outline="green", width=3)
        for item in raw_components:
            draw.rectangle(item.bbox, outline="red", width=1)
        for item in predictions:
            draw.rectangle(item.bbox, outline="blue", width=3)
        
        overlay_dir = Q7_DIR / "overlays"
        overlay_dir.mkdir(parents=True, exist_ok=True)
        overlay.save(overlay_dir / f"page_{page['id']}_q7_overlay.png")
        
    trace_handle.close()
    
    precision = total_matches / total_pred if total_pred else 0.0
    recall = total_matches / total_gt if total_gt else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    
    import statistics
    summary = summarize(gt_all, pred_all)
    
    final_metrics = {
        **summary,
        "boundary_precision": precision,
        "boundary_recall": recall,
        "boundary_f1": f1,
        "line_precision": precision,
        "line_recall": recall,
        "line_f1": f1,
        "matched_line_coverage": statistics.mean([item["matched_line_coverage"] for item in order_scores]) if order_scores else 0.0,
        "pairwise_reading_order": statistics.mean([item["pairwise_order_accuracy"] for item in order_scores]) if order_scores else 0.0,
        "overall_reading_order": statistics.mean([item["overall_reading_order"] for item in order_scores]) if order_scores else 0.0,
        "page_failure_rate": sum(1 for page in page_metrics if page["line_f1"] == 0 or page["strict_cer"] >= 1.0) / len(page_metrics) if page_metrics else 1.0,
        "pages": page_metrics,
        "time_ms": (time.perf_counter() - start_t) * 1000,
    }
    
    with open(Q7_DIR / "pilot_validation_metrics.json", "w", encoding="utf-8") as f:
        json.dump(final_metrics, f, indent=2)
        
    print(f"Pilot validation completed! Normalized WER: {final_metrics['normalized_wer']}")
    
if __name__ == "__main__":
    main()
