import os
import zipfile

dataset_py_icerik = """import pandas as pd
from torch.utils.data import Dataset
from PIL import Image
import os

class OttomanDataset(Dataset):
    def __init__(self, csv_file, root_dir, processor, max_target_length=128):
        self.df = pd.read_csv(csv_file)
        self.root_dir = root_dir
        self.processor = processor
        self.max_target_length = max_target_length

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        file_name = self.df['file_name'][idx]
        text = self.df['text'][idx]
        
        image_path = os.path.join(self.root_dir, file_name)
        image = Image.open(image_path).convert("RGB")
        
        pixel_values = self.processor(image, return_tensors="pt").pixel_values.squeeze()
        
        labels = self.processor.tokenizer(
            text,
            padding="max_length",
            max_length=self.max_target_length,
            truncation=True
        ).input_ids
        
        labels = [label if label != self.processor.tokenizer.pad_token_id else -100 for label in labels]
        return {"pixel_values": pixel_values, "labels": labels}
"""

train_py_icerik = """from transformers import TrOCRProcessor, VisionEncoderDecoderModel, Seq2SeqTrainer, Seq2SeqTrainingArguments, default_data_collator
from dataset import OttomanDataset
from torch.utils.data import random_split
import torch

processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

model.config.decoder_start_token_id = processor.tokenizer.cls_token_id
model.config.pad_token_id = processor.tokenizer.pad_token_id
model.config.vocab_size = model.config.decoder.vocab_size

dataset = OttomanDataset(csv_file="data/train.csv", root_dir="data/images", processor=processor)

train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

training_args = Seq2SeqTrainingArguments(
    predict_with_generate=True,
    evaluation_strategy="epoch",
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    fp16=torch.cuda.is_available(),
    output_dir="./ottoman-ocr-model",
    logging_steps=10,
    save_strategy="epoch",
    num_train_epochs=5,
)

trainer = Seq2SeqTrainer(
    model=model,
    tokenizer=processor.feature_extractor,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    data_collator=default_data_collator,
)

trainer.train()
trainer.save_model("./ottoman-ocr-model-final")
processor.save_pretrained("./ottoman-ocr-model-final")
"""

req_icerik = "torch\ntransformers\npillow\npandas\nscikit-learn\naccelerate\nevaluate\njiwer\n"

train_csv_icerik = "file_name,text\nsayfa1_satir1.jpg,محمود پاشا\nsayfa1_satir2.jpg,عثمانلى دورت\n"

# 1. Klasörleri oluştur
os.makedirs("osmanlica_egitim/data/images", exist_ok=True)

# 2. Dosyaları yaz
with open("osmanlica_egitim/dataset.py", "w", encoding="utf-8") as f: f.write(dataset_py_icerik)
with open("osmanlica_egitim/train.py", "w", encoding="utf-8") as f: f.write(train_py_icerik)
with open("osmanlica_egitim/requirements.txt", "w", encoding="utf-8") as f: f.write(req_icerik)
with open("osmanlica_egitim/data/train.csv", "w", encoding="utf-8") as f: f.write(train_csv_icerik)
with open("osmanlica_egitim/data/val.csv", "w", encoding="utf-8") as f: f.write(train_csv_icerik) # Şimdilik train kopyası

# Görüntü dosyası için boş txt dosyalarını jpg uzantısıyla placeholder olarak ekle
with open("osmanlica_egitim/data/images/sayfa1_satir1.jpg", "w") as f: f.write("")
with open("osmanlica_egitim/data/images/sayfa1_satir2.jpg", "w") as f: f.write("")

# 3. Zip dosyası oluştur
with zipfile.ZipFile("osmanlica_egitim.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk("osmanlica_egitim"):
        for file in files:
            file_path = os.path.join(root, file)
            zipf.write(file_path, os.path.relpath(file_path, "."))

print("Başarılı! 'osmanlica_egitim' klasörü ve 'osmanlica_egitim.zip' dosyası bulunduğunuz dizine oluşturuldu.")