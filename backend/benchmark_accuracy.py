import os
import re
import cv2
import time
import asyncio
import numpy as np
import sys
import jiwer

# Add backend to path
sys.path.insert(0, os.path.abspath('.'))

from app.services.document_processing.ocr_engine import KrakenWSLEngine, EasyOCREngine, OCRLineResult

def calculate_metrics(reference, hypothesis):
    if not reference or reference == "[Buraya yazın]":
        return None
    
    # Calculate CER and WER using jiwer
    try:
        cer = jiwer.cer(reference, hypothesis)
        wer = jiwer.wer(reference, hypothesis)
        
        char_out = jiwer.process_characters(reference, hypothesis)
        
        char_acc = max(0.0, 1.0 - cer)
        line_acc = 1.0 if reference.strip() == hypothesis.strip() else 0.0
        
        return {
            "cer": cer,
            "wer": wer,
            "char_acc": char_acc,
            "line_acc": line_acc,
            "insertions": char_out.insertions,
            "deletions": char_out.deletions,
            "substitutions": char_out.substitutions
        }
    except ValueError:
        return {"cer": 1.0, "wer": 1.0, "char_acc": 0.0, "line_acc": 0.0, "insertions": 0, "deletions": 0, "substitutions": 0}

async def main():
    gt_file = "C:\\Users\\black man\\.gemini\\antigravity-ide\\brain\\e21073d1-8097-46df-86b9-7d5c6a2dffa3\\ground_truth_proposal.md"
    
    if not os.path.exists(gt_file):
        print("Ground truth dosyası bulunamadı.")
        return
        
    with open(gt_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Regex to find crop path and transcription
    pattern = r"!\[.*?\]\((.*?)\)\n\*\*Transkripsiyon:\*\* `(.*?)`"
    matches = re.findall(pattern, content)
    
    if not matches:
        print("Geçerli formatta satır bulunamadı.")
        return
        
    print("Loading Engines...")
    kraken = KrakenWSLEngine(
        model_path="C:\\projeler\\INTELLIGENT OTTOMAN TURKISH ASSISTANT\\models\\recognition\\ottoman_recognition_final_v1.mlmodel",
        model_sha256="f5abbba1976e9782ddf5d7185d911722c74558e12b57a12566c96e22a3e3b963",
        distro="Ubuntu-24.04",
        python_path="/home/black_man/venvs/ottoman_kraken/bin/python"
    )
    easyocr_engine = EasyOCREngine(languages=['ar'], gpu=False)
    
    print("\n--- BENCHMARK BAŞLIYOR ---")
    valid_lines = 0
    
    for img_path, gt_text in matches:
        if gt_text == "[Buraya yazın]":
            continue
            
        valid_lines += 1
        print(f"\nDosya: {os.path.basename(img_path)}")
        print(f"Ground Truth: {gt_text}")
        
        # Windows path fix for reading cv2 from full path
        image = cv2.imread(img_path)
        if image is None:
            print("Resim okunamadı!")
            continue
            
        # 1. EasyOCR
        t0 = time.perf_counter()
        results = easyocr_engine.reader.readtext(image, detail=1, paragraph=False)
        easy_time = time.perf_counter() - t0
        
        easy_text = " ".join([r[1] for r in results]) if results else ""
        easy_conf = np.mean([r[2] for r in results]) if results else 0.0
        
        # 2. Kraken
        # We need to pass the whole image as a single line to Kraken
        h, w = image.shape[:2]
        line = OCRLineResult(
            text="", confidence=1.0, bbox=(0, 0, w, h), line_index=0,
            engine_name="kraken", engine_version="", device="", processing_time_ms=0.0
        )
        
        t0 = time.perf_counter()
        kraken_res, _ = await kraken.extract_batch(image, [line])
        kraken_time = time.perf_counter() - t0
        
        kraken_text = kraken_res[0].text if kraken_res else ""
        kraken_conf = kraken_res[0].confidence if kraken_res else 0.0
        
        # Evaluate
        easy_metrics = calculate_metrics(gt_text, easy_text)
        kraken_metrics = calculate_metrics(gt_text, kraken_text)
        
        print(f"  EasyOCR | CER: {easy_metrics['cer']:.2f} | WER: {easy_metrics['wer']:.2f} | Char Acc: {easy_metrics['char_acc']:.2f} | Line Acc: {easy_metrics['line_acc']:.2f} | Ins: {easy_metrics['insertions']} | Del: {easy_metrics['deletions']} | Sub: {easy_metrics['substitutions']} | Conf: {easy_conf:.2f} | Time: {easy_time:.2f}s | Pred: {easy_text}")
        print(f"  Kraken  | CER: {kraken_metrics['cer']:.2f} | WER: {kraken_metrics['wer']:.2f} | Char Acc: {kraken_metrics['char_acc']:.2f} | Line Acc: {kraken_metrics['line_acc']:.2f} | Ins: {kraken_metrics['insertions']} | Del: {kraken_metrics['deletions']} | Sub: {kraken_metrics['substitutions']} | Conf: {kraken_conf:.2f} | Time: {kraken_time:.2f}s | Pred: {kraken_text}")
        
    if valid_lines == 0:
        print("\nUYARI: Bütün transkripsiyonlar '[Buraya yazın]' olarak bırakılmış. Benchmark çalıştırılmadı.")
        print("Lütfen ground_truth_proposal.md dosyasını doldurun ve tekrar çalıştırın.")

if __name__ == "__main__":
    asyncio.run(main())
