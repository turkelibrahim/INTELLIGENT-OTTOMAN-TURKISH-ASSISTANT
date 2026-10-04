"""Q8 LLM Post-Correction for Ottoman OCR (V_MAX)."""

import sys
import json
import time
from pathlib import Path
import sqlite3
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.hybrid_recognition_q6 import summarize

Q8_DIR = Path(__file__).resolve().parents[1] / "evidence" / "llm_correction_q8"
Q8_DIR.mkdir(parents=True, exist_ok=True)
TRACE_FILE = Path(__file__).resolve().parents[1] / "evidence" / "real_ocr_quality" / "boundary_decision_trace.jsonl"

def load_ground_truth():
    conn = sqlite3.connect(Path(__file__).resolve().parents[1] / "backend" / "ottoman_assistant.db")
    conn.row_factory = sqlite3.Row
    pages = {}
    for row in conn.execute("select * from ground_truth_pages where dataset_id=2 and id in (1, 2, 3) order by id"):
        page_id = row["id"]
        lines = [
            dict(line)
            for line in conn.execute(
                "select * from ground_truth_lines where page_id=? order by reading_order",
                (page_id,),
            )
        ]
        pages[page_id] = [line["text_content"] for line in lines]
    return pages

def load_ocr_results():
    page_predictions = {1: [], 2: [], 3: []}
    with open(TRACE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            page_id = data["page_id"]
            if page_id in page_predictions:
                page_predictions[page_id].append(data["text"])
    return page_predictions

def apply_llm_correction(text_line, model, tokenizer):
    if len(text_line.strip()) == 0:
        return ""
    
    system_prompt = (
        "Sen bir Osmanlıca metin düzeltme asistanısın. "
        "Sana OCR'dan çıkmış gürültülü metinler verilecek. "
        "GÖREVİN: Sadece yanlış okunmuş harfleri bağlama göre düzeltmek. "
        "KURAL 1: Asla metnin anlamını değiştirme. "
        "KURAL 2: Asla yeni kelime ekleme veya var olan kelimeyi silme. "
        "KURAL 3: Girdi kaç kelimeyse çıktı da aynı kelime sayısında olmalıdır.\n"
        f"Girdi: {text_line}\nÇıktı:"
    )
    
    try:
        inputs = tokenizer(system_prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=128, temperature=0.1, num_beams=3, early_stopping=True)
        corrected = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        
        # Fallback if hallucinated completely empty
        if len(corrected) < 2:
            corrected = text_line
            
        return corrected
    except Exception:
        return text_line

def save_corrected_results(results_list, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for item in results_list:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def main():
    print("Loading mt5-small directly...")
    try:
        tokenizer = AutoTokenizer.from_pretrained("google/mt5-small")
        model = AutoModelForSeq2SeqLM.from_pretrained("google/mt5-small")
    except Exception as e:
        print(f"Could not load model: {e}")
        sys.exit(1)
        
    print("Loading OCR Predictions from Trace...")
    page_predictions = load_ocr_results()
    gt_pages = load_ground_truth()
    
    gt_all = []
    pred_all = []
    corrected_results = []
    
    print("Starting LLM Post-Correction...")
    start_t = time.perf_counter()
    
    for page_id in [1, 2, 3]:
        if page_id not in gt_pages or page_id not in page_predictions:
            continue
            
        print(f"Processing Page {page_id}...")
        gt_texts = gt_pages[page_id]
        raw_preds = page_predictions[page_id]
        
        for i, text in enumerate(raw_preds):
            gt_text = gt_texts[i] if i < len(gt_texts) else ""
            corrected = apply_llm_correction(text, model, tokenizer)
            
            gt_all.append(gt_text)
            pred_all.append(corrected)
            
            corrected_results.append({
                "page_id": page_id,
                "line_index": i,
                "raw_ocr": text,
                "llm_corrected": corrected,
                "ground_truth": gt_text
            })

    save_corrected_results(corrected_results, Q8_DIR / "llm_predictions.jsonl")

    import statistics
    summary = summarize(gt_all, pred_all)
    
    final_metrics = {
        **summary,
        "time_ms": (time.perf_counter() - start_t) * 1000,
    }
    
    with open(Q8_DIR / "q8_llm_correction_metrics_vmax.json", "w", encoding="utf-8") as f:
        json.dump(final_metrics, f, indent=2)
        
    print(f"LLM Correction completed! Normalized WER: {final_metrics['normalized_wer']}")

if __name__ == "__main__":
    main()
