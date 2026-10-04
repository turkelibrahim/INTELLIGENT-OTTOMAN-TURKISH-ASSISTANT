import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
import warnings
warnings.filterwarnings("ignore") # Gereksiz kırmızı uyarıları gizle

model_id = "NousResearch/Meta-Llama-3-8B"
adapter_path = "models/osmanli_tarihcisi_lora" # Eğittiğimiz beynin yolu

print("1. Ana model yükleniyor (Bu işlem VRAM'e sığması için yine 4-bit yapılıyor)...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
)

tokenizer = AutoTokenizer.from_pretrained(model_id)
base_model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    quantization_config=bnb_config, 
    device_map={"": 0}
)

print("2. Senin eğittiğin Osmanlı Tarihçisi beyni (LoRA) ana modele entegre ediliyor...")
model = PeftModel.from_pretrained(base_model, adapter_path)

# Test Sorumuz
soru = "Tanzimat Fermanı"
talimat = f"Aşağıdaki belgede/konuda geçen '{soru}' hakkında detaylı bir tarihsel analiz yap."
girdi = f"Konu/Belge: {soru}"

# Modelin eğitimde gördüğü şablonun aynısı
alpaca_prompt = f"""Aşağıdaki talimatı yerine getiren bir cevap yaz.

### Talimat:
{talimat}

### Girdi (Belge):
{girdi}

### Cevap (Tarihsel Analiz):
"""

print("\n3. Yapay zeka düşünüyor...\n" + "="*50)

inputs = tokenizer(alpaca_prompt, return_tensors="pt").to("cuda")

# Modeli konuşturuyoruz
outputs = model.generate(
    **inputs, 
    max_new_tokens=250,      # Maksimum üreteceği kelime sayısı
    temperature=0.7,         # Yaratıcılık oranı (Tarih için dengeli)
    top_p=0.9,
    repetition_penalty=1.1,  # Kendini tekrar etmesini engeller
    pad_token_id=tokenizer.eos_token_id
)

# Çıktıyı Türkçeye çevirip formatlıyoruz
cevap_tamami = tokenizer.decode(outputs[0], skip_special_tokens=True)
temiz_cevap = cevap_tamami.split("### Cevap (Tarihsel Analiz):")[1].strip()

print(f"SENİN SORUN:\n{talimat}\n")
print(f"OSMANLI TARİHÇİSİ (YAPAY ZEKA) CEVABI:\n{temiz_cevap}")
print("="*50)