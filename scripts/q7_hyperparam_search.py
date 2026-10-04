import sys
import json
import csv
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.evaluation.ocr_pipeline_optimization import match_boxes, BoxItem
from scripts.hybrid_recognition_q6 import summarize
from app.services.document_processing.word_boundary import reconstruct_rtl_line_text_v2

Q7_DIR = Path(__file__).resolve().parents[1] / "evidence" / "word_boundary_q7"
Q6_DIR = Path(__file__).resolve().parents[1] / "evidence" / "hybrid_recognition_q6"

def load_data():
    conn = sqlite3.connect(Path(__file__).resolve().parents[1] / "backend" / "ottoman_assistant.db")
    conn.row_factory = sqlite3.Row
    pages = []
    for row in conn.execute("select * from ground_truth_pages where dataset_id=2 and id=1 order by id"):
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

import torch
from PIL import Image
from scripts.hybrid_recognition_q6 import readtext, preprocess_image, q5_layout_lines, filter_layout_lines, assign_components_to_lines
from app.services.document_processing.ocr_engine import OttomanOCREngine
from scripts.hybrid_recognition_q6 import gt_items

def main():
    pages = load_data()
    dev_page = pages[0]
    
    q5_config = json.loads((Q7_DIR.parent / "line_segmentation_q5" / "selected_line_strategy.json").read_text(encoding="utf-8"))
    q6_config = json.loads((Q6_DIR / "selected_hybrid_config.json").read_text(encoding="utf-8"))
    
    engine = OttomanOCREngine(enable_easyocr=True, enable_trocr=False, enable_tesseract=True, gpu=True)
    reader = engine.engines["easyocr"].reader
    
    image = Image.open(dev_page["image_path"]).convert("RGB")
    processed = preprocess_image(image, q6_config["page_preprocessing"])
    
    raw_components = readtext(reader, processed, q6_config["ocr"], prefix="c")
    from app.services.evaluation.ocr_pipeline_optimization import suppress_duplicate_boxes
    raw_components = [item for item in suppress_duplicate_boxes(raw_components, threshold=0.9) if item.text]
    
    layout_lines = q5_layout_lines(processed, q5_config)
    first_assignment = assign_components_to_lines(layout_lines, raw_components, min_score=float(q6_config["assignment_min_score"]))
    comp_by_id = {item.id: item for item in raw_components}
    
    lines = filter_layout_lines(layout_lines, first_assignment, comp_by_id, q6_config)
    assignment = assign_components_to_lines(lines, raw_components, min_score=float(q6_config["assignment_min_score"]))
    
    # Pre-compute leftovers
    assigned_ids = {item["component_id"] for r in assignment["assignments"].values() for item in r}
    leftovers = [comp for comp in raw_components if comp.id not in assigned_ids]
    extra_lines = []
    if leftovers:
        from app.services.evaluation.ocr_pipeline_optimization import logical_line_items
        extra_lines = logical_line_items(leftovers, id_prefix="extra")
    
    gt = gt_items(dev_page)
    gt_texts = [line["text_content"] for line in dev_page["lines"]]
    
    best_wer = 1.0
    best_cand = None
    
    import itertools
    gap_weights = [1.0, 1.2, 1.5]
    join_penalties = [0.1, 0.2]
    punct_bonuses = [0.1, 0.2]
    digit_bonuses = [0.1, 0.2]
    thresholds = [0.05, 0.1, 0.15]
    
    print("Starting grid search with leftovers...")
    for gw, jp, pb, db, th in itertools.product(gap_weights, join_penalties, punct_bonuses, digit_bonuses, thresholds):
        cand = {
            "name": f"Strategy E - gw{gw}_jp{jp}_pb{pb}_db{db}_th{th}",
            "strategy": "hybrid",
            "gap_weight": gw,
            "joining_penalty": jp,
            "punctuation_bonus": pb,
            "digit_bonus": db,
            "boundary_score_threshold": th,
            "low_confidence_threshold": 0.0,
            "enable_internal_split": False
        }
        predictions = []
        for line in lines:
            assigned = [comp_by_id[item["component_id"]] for item in assignment["assignments"].get(line.id, [])]
            text = reconstruct_rtl_line_text_v2(assigned, cand)
            predictions.append(BoxItem(line.id, line.bbox, text, 1.0))
            
        for idx, extra in enumerate(extra_lines):
            predictions.append(BoxItem(f"extra_{idx}", extra.bbox, extra.text, 1.0))
            
        predictions.sort(key=lambda item: (item.bbox[1], -item.bbox[2], item.id))
        pred_texts = [item.text for item in predictions]
        summary = summarize(gt_texts, pred_texts)
        wer = summary["normalized_wer"]
        
        if wer < best_wer:
            best_wer = wer
            best_cand = cand
            print(f"New best WER: {wer} with {cand['name']}")
            
    # Also evaluate Strategy F
    cand_f = {
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
    predictions = []
    for line in lines:
        assigned = [comp_by_id[item["component_id"]] for item in assignment["assignments"].get(line.id, [])]
        text = reconstruct_rtl_line_text_v2(assigned, cand_f)
        predictions.append(BoxItem(line.id, line.bbox, text, 1.0))
    for idx, extra in enumerate(extra_lines):
        predictions.append(BoxItem(f"extra_{idx}", extra.bbox, extra.text, 1.0))
    predictions.sort(key=lambda item: (item.bbox[1], -item.bbox[2], item.id))
    pred_texts = [item.text for item in predictions]
    wer_f = summarize(gt_texts, pred_texts)["normalized_wer"]
    print(f"Strategy F WER: {wer_f}")
    
    if wer_f < best_wer:
        best_wer = wer_f
        best_cand = cand_f
        
    print(f"\nGrid search done. Best WER: {best_wer} using {best_cand['name']}")
    
    candidates = [
        {"name": "Strategy A - Q6 baseline", "strategy": "Q6_baseline", "join_gap_ratio": 0.22, "low_confidence_threshold": 0.0},
        best_cand
    ]
    
    with open(Q7_DIR / "candidates_to_evaluate.json", "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2)

if __name__ == "__main__":
    main()
