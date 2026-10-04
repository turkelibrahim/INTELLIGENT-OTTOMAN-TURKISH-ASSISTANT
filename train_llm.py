import torch
import os
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# Yol ayarları
DATASET_PATH = os.path.join("datasets", "osmanli_egitim_verisi_mega.jsonl")
MODEL_OUTPUT_DIR = os.path.join("models", "osmanli_tarihcisi_lora")
CHECKPOINT_DIR = os.path.join("models", "checkpoints")

# 1. QLoRA ve 4-bit Quantizasyon Ayarları
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
)

model_id = "NousResearch/Meta-Llama-3-8B"

print("Model yükleniyor...")
tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token

# 0. GPU'ya (RTX 4050) zorlama ayarı (6GB VRAM kurtarıcısı)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map={"": 0} 
)
model = prepare_model_for_kbit_training(model)

# 2. LoRA Konfigürasyonu
peft_config = LoraConfig(
    r=8, 
    lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], 
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, peft_config)

# 3. Veri Setini Yükle ve Manuel Tokenize Et (En Sağlam Yöntem)
alpaca_prompt = """Aşağıdaki talimatı yerine getiren bir cevap yaz.

### Talimat:
{}

### Girdi (Belge):
{}

### Cevap (Tarihsel Analiz):
{}"""

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for instruction, input, output in zip(instructions, inputs, outputs):
        text = alpaca_prompt.format(instruction, input, output) + tokenizer.eos_token
        texts.append(text)
    return { "text" : texts }

print(f"Veri seti yükleniyor: {DATASET_PATH}")
dataset = load_dataset("json", data_files={"train": DATASET_PATH}, split="train")

# Metinleri oluştur
dataset = dataset.map(formatting_prompts_func, batched = True)

# Metinleri doğrudan sayılara çevir (256 kelime sınırı ile VRAM'i koruyoruz)
print("Veri seti bilgisayarın anlayacağı formata (tokenlara) çevriliyor...")
def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, max_length=256)
    
tokenized_dataset = dataset.map(tokenize_function, batched=True)

# 4. Eğitimi Başlat (Klasik ve Asla Çökmeyen Trainer Modeli)
training_args = TrainingArguments(
    output_dir=CHECKPOINT_DIR, 
    per_device_train_batch_size=1,        
    gradient_accumulation_steps=4,        
    warmup_steps=5,
    max_steps=40,                         
    learning_rate=2e-4,
    fp16=not torch.cuda.is_bf16_supported(),
    bf16=torch.cuda.is_bf16_supported(),
    logging_steps=1,
    optim="paged_adamw_8bit", 
    weight_decay=0.01,
    lr_scheduler_type="linear",
    seed=3407,
    gradient_checkpointing=True,
)

# Verileri eğitime hazırlayan toplayıcı
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)

print("Eğitim Başlıyor... Görev Yöneticisinden GPU Kullanımını İzleyebilirsiniz!")
trainer.train()

# 5. Eğitilmiş Modeli 'models' Klasörüne Kaydet
print(f"Eğitim bitti, LoRA ağırlıkları '{MODEL_OUTPUT_DIR}' konumuna kaydediliyor...")
trainer.model.save_pretrained(MODEL_OUTPUT_DIR)
tokenizer.save_pretrained(MODEL_OUTPUT_DIR)
print("İşlem başarıyla tamamlandı!")