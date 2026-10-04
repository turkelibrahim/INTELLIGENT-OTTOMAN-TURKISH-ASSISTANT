"""
Ottoman Turkish Handwritten TrOCR Fine-Tuning Script
----------------------------------------------------
This script fine-tunes the Microsoft TrOCR model on your custom handwritten 
Ottoman Turkish dataset. It uses HuggingFace Transformers and requires a GPU.

Usage:
1. Prepare your dataset in a CSV file (e.g., `dataset.csv`) with two columns:
   - `file_name`: Path to the cropped line image (e.g., "images/line_001.png")
   - `text`: The correct Ottoman text for that line.
2. Run this script:
   `python scripts/train_handwritten_trocr.py --csv_path dataset.csv`

Requirements:
- pip install transformers datasets evaluate accelerate torch torchvision pillow
"""

import argparse
import os
import torch
import pandas as pd
from PIL import Image
from transformers import (
    TrOCRProcessor,
    VisionEncoderDecoderModel,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    default_data_collator,
)
from datasets import Dataset

def load_dataset_from_csv(csv_path: str):
    df = pd.read_csv(csv_path)
    if "file_name" not in df.columns or "text" not in df.columns:
        raise ValueError("CSV must contain 'file_name' and 'text' columns")
    
    # Ensure paths are absolute or relative to the csv directory
    csv_dir = os.path.dirname(os.path.abspath(csv_path))
    def fix_path(path):
        if not os.path.isabs(path):
            return os.path.join(csv_dir, path)
        return path
    
    df["file_name"] = df["file_name"].apply(fix_path)
    return Dataset.from_pandas(df)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv_path", type=str, required=True, help="Path to training dataset CSV")
    parser.add_argument("--base_model", type=str, default="microsoft/trocr-base-printed", help="Base model to fine-tune")
    parser.add_argument("--output_dir", type=str, default="models/trocr-ottoman-handwritten", help="Output directory")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Training batch size")
    args = parser.parse_args()

    print(f"Loading base model: {args.base_model}")
    processor = TrOCRProcessor.from_pretrained(args.base_model)
    model = VisionEncoderDecoderModel.from_pretrained(args.base_model)
    
    # Configure model for text generation
    model.config.decoder_start_token_id = processor.tokenizer.cls_token_id
    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.config.vocab_size = model.config.decoder.vocab_size
    model.config.eos_token_id = processor.tokenizer.sep_token_id
    model.config.max_length = 64
    model.config.early_stopping = True
    model.config.no_repeat_ngram_size = 3
    model.config.length_penalty = 2.0
    model.config.num_beams = 4

    print(f"Loading dataset from: {args.csv_path}")
    dataset = load_dataset_from_csv(args.csv_path)
    
    # Split into train and eval (90% / 10%)
    dataset = dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = dataset["train"]
    eval_dataset = dataset["test"]

    def preprocess_function(examples):
        images = []
        for file_path in examples["file_name"]:
            try:
                image = Image.open(file_path).convert("RGB")
                images.append(image)
            except Exception as e:
                print(f"Error loading image {file_path}: {e}")
                # Provide a dummy white image if missing to prevent crash
                images.append(Image.new("RGB", (300, 100), (255, 255, 255)))

        pixel_values = processor(images, return_tensors="pt").pixel_values
        labels = processor.tokenizer(
            examples["text"], padding="max_length", max_length=64, truncation=True
        ).input_ids

        # Replace padding token id's of the labels by -100 so it's ignored by the loss
        labels = [[-100 if token == processor.tokenizer.pad_token_id else token for token in label] for label in labels]

        return {"pixel_values": pixel_values, "labels": labels}

    print("Preprocessing datasets...")
    train_dataset = train_dataset.map(preprocess_function, batched=True, remove_columns=["file_name", "text"])
    eval_dataset = eval_dataset.map(preprocess_function, batched=True, remove_columns=["file_name", "text"])

    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        predict_with_generate=True,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=10,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        fp16=torch.cuda.is_available(),
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="loss"
    )

    trainer = Seq2SeqTrainer(
        model=model,
        tokenizer=processor.feature_extractor,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=default_data_collator,
    )

    print("Starting training...")
    trainer.train()

    print(f"Saving fine-tuned model to {args.output_dir}...")
    trainer.save_model(args.output_dir)
    processor.save_pretrained(args.output_dir)
    print("Training complete! You can now load this model in OttomanOCREngine by passing trocr_model=args.output_dir")

if __name__ == "__main__":
    main()
