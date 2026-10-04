import sys
import json
import csv
from pathlib import Path
import sqlite3
import difflib

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.evaluation.metrics import normalize_ottoman_text

Q7_DIR = Path(__file__).resolve().parents[1] / "evidence" / "word_boundary_q7"
Q7_DIR.mkdir(parents=True, exist_ok=True)

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(Path(__file__).resolve().parents[1] / "backend" / "ottoman_assistant.db")
    conn.row_factory = sqlite3.Row
    return conn

def load_dataset(conn: sqlite3.Connection, dataset_id: int) -> dict:
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
    return {"pages": pages}

def classify_errors(gt: str, hyp: str):
    # Normalized for evaluation
    gt_norm = normalize_ottoman_text(gt)
    hyp_norm = normalize_ottoman_text(hyp)
    
    # Strip spaces to compare character sequences
    gt_nospace = gt_norm.replace(" ", "")
    hyp_nospace = hyp_norm.replace(" ", "")
    
    classes = set()
    
    # Check simple space count diff
    gt_spaces = gt_norm.count(" ")
    hyp_spaces = hyp_norm.count(" ")
    
    # If the characters match exactly, then all errors are just spacing errors
    if gt_nospace == hyp_nospace:
        if hyp_spaces > gt_spaces:
            classes.add("OVER_SPLIT")
        if hyp_spaces < gt_spaces:
            classes.add("OVER_MERGE")
        # Check specific boundaries (basic heuristics)
        for char in gt_norm:
            if char.isdigit(): classes.add("DIGIT_BOUNDARY")
            if char in ".,!?;:'\"()[]{}؟،؛": classes.add("PUNCTUATION_BOUNDARY")
    else:
        # There is a recognition error
        classes.add("RECOGNITION_ERROR_NOT_BOUNDARY")
        if hyp_spaces > gt_spaces: classes.add("OVER_SPLIT")
        if hyp_spaces < gt_spaces: classes.add("OVER_MERGE")
        
        # Determine if it's omission or duplication
        if len(hyp_nospace) < len(gt_nospace) - 5:
            classes.add("COMPONENT_OMISSION")
        if len(hyp_nospace) > len(gt_nospace) + 5:
            classes.add("COMPONENT_DUPLICATION")
            
    # Compute boundary precision/recall/F1 based on char index
    # Map each char to its original index in spaced string
    def get_space_indices(text):
        indices = set()
        char_idx = 0
        for i, char in enumerate(text):
            if char == " ":
                indices.add(char_idx)
            else:
                char_idx += 1
        return indices
        
    gt_spaces_idx = get_space_indices(gt_norm)
    hyp_spaces_idx = get_space_indices(hyp_norm)
    
    # Only valid if gt_nospace == hyp_nospace, otherwise it's just an approximation
    tp = len(gt_spaces_idx.intersection(hyp_spaces_idx))
    fp = len(hyp_spaces_idx - gt_spaces_idx)
    fn = len(gt_spaces_idx - hyp_spaces_idx)
    
    return list(classes), tp, fp, fn, len(gt_norm.split()), len(hyp_norm.split())

def main():
    conn = connect()
    data = load_dataset(conn, 2)
    
    # Read Q6 predictions from oracle diagnostic or candidate trace
    q6_trace_path = Path(__file__).resolve().parents[1] / "evidence" / "hybrid_recognition_q6" / "candidate_decision_trace.jsonl"
    
    predictions = {}
    with open(q6_trace_path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            predictions[(obj["page_id"], obj["line_id"])] = obj["chosen"]["text"]
            
    word_count_analysis = []
    error_analysis = []
    
    for page in data["pages"]:
        split = "development" if page["id"] == 1 else "pilot_validation"
        for i, line in enumerate(page["lines"]):
            gt = line["text_content"]
            # Try to get prediction. Wait, candidate_decision_trace uses line_id like `projection_0000`
            # For simplicity, we just assume they are matched by order since Q6 has 1.0 overall reading order
            # Actually, let's look at `line_error_analysis.csv` from Q6! That's much safer!
            pass
            
    # Read line_error_analysis.csv from Q6
    q6_error_path = Path(__file__).resolve().parents[1] / "evidence" / "hybrid_recognition_q6" / "line_error_analysis.csv"
    
    with open(q6_error_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            page_id = int(row["page_id"])
            gt = row["ground_truth"]
            hyp = row["prediction"]
            split = "development" if page_id == 1 else "pilot_validation"
            
            classes, tp, fp, fn, gt_words, hyp_words = classify_errors(gt, hyp)
            
            word_count_analysis.append({
                "page_id": page_id,
                "split": split,
                "reading_order": row["reading_order"],
                "gt_words": gt_words,
                "hyp_words": hyp_words,
                "ratio": hyp_words / gt_words if gt_words > 0 else 0
            })
            
            error_analysis.append({
                "page_id": page_id,
                "split": split,
                "reading_order": row["reading_order"],
                "ground_truth": gt,
                "prediction": hyp,
                "error_classes": "|".join(classes),
                "tp": tp,
                "fp": fp,
                "fn": fn
            })
            
    # Write CSVs
    with open(Q7_DIR / "word_count_analysis.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["page_id", "split", "reading_order", "gt_words", "hyp_words", "ratio"])
        writer.writeheader()
        writer.writerows(word_count_analysis)
        
    with open(Q7_DIR / "boundary_error_analysis.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["page_id", "split", "reading_order", "ground_truth", "prediction", "error_classes", "tp", "fp", "fn"])
        writer.writeheader()
        writer.writerows(error_analysis)
        
    print("Boundary error analysis completed.")

if __name__ == "__main__":
    main()
