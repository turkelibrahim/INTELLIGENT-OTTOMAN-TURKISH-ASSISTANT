import torch
import warnings
from fastapi import FastAPI, File, UploadFile
import io
from PIL import Image
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

warnings.filterwarnings("ignore")

app = FastAPI(title="Osmanlı Tarihçisi Analiz API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Yapay Zeka API Sunucusu Başlatılıyor...")
model_id = "NousResearch/Meta-Llama-3-8B"
adapter_path = "models/osmanli_tarihcisi_lora"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
)

tokenizer = AutoTokenizer.from_pretrained(model_id)
base_model = AutoModelForCausalLM.from_pretrained(
    model_id, quantization_config=bnb_config, device_map={"": 0}
)
model = PeftModel.from_pretrained(base_model, adapter_path)
print("Model başarıyla yüklendi! API İstek dinlemeye hazır.")

# KULLANICIDAN GELECEK VERİ: Artık soru değil, OCR'dan çıkan tam metin gelecek
class BelgeIstegi(BaseModel):
    belge_metni: str

# --- OCR MODELİ UÇ NOKTASI ---
@app.post("/api/ocr")
async def belge_ocr(dosya: UploadFile = File(...)):
    print(f"OCR İçin Dosya Alındı: {dosya.filename}")
    
    # 1. Gelen Resmi Oku
    resim_bytes = await dosya.read()
    image = Image.open(io.BytesIO(resim_bytes)).convert("RGB")
    
    # 2. OCR Modelinden Geçir (Kendi modelinin kodunu buraya ekleyeceksin)
    # Örnek:
    # pixel_values = ocr_processor(image, return_tensors="pt").pixel_values.to("cuda")
    # generated_ids = ocr_model.generate(pixel_values)
    # ocr_metni = ocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    # Şimdilik test amaçlı sahte metin döndürüyoruz:
    ocr_metni = "Bu metin Python API'sindeki OCR Endpoint'inden gelmektedir!"
    
    return {"ocr_metni": ocr_metni}

# YENİ UÇ NOKTA: /api/belge-analiz
@app.post("/api/belge-analiz")
async def belge_analiz(istek: BelgeIstegi):
    
    # YAPAY ZEKAYA YENİ TALİMAT: Belgeyi oku ve analiz et
    talimat = "Aşağıdaki Osmanlıca belgenin güncel Türkçe çevirisini incele. Bu belgenin tarihsel bağlamını, dönemini ve içindeki önemli kişi, kurum veya olayları tespit ederek özet bir tarihsel analiz raporu oluştur."
    girdi = f"Belge Çevirisi:\n{istek.belge_metni}"
    
    alpaca_prompt = f"""Aşağıdaki talimatı yerine getiren bir cevap yaz.

### Talimat:
{talimat}

### Girdi (Belge):
{girdi}

### Cevap (Tarihsel Analiz):
"""
    
    inputs = tokenizer(alpaca_prompt, return_tensors="pt").to("cuda")
    
    outputs = model.generate(
        **inputs, 
        max_new_tokens=300,      # Rapor olacağı için kelime limitini 300'e çıkardık
        temperature=0.6,         # Analiz yapacağı için halüsinasyonu engellemek adına yaratıcılığı biraz kıstık
        top_p=0.9,
        repetition_penalty=1.1,
        pad_token_id=tokenizer.eos_token_id
    )
    
    cevap_tamami = tokenizer.decode(outputs[0], skip_special_tokens=True)
    temiz_cevap = cevap_tamami.split("### Cevap (Tarihsel Analiz):")[1].strip()
    
    return {"analiz_raporu": temiz_cevap}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)