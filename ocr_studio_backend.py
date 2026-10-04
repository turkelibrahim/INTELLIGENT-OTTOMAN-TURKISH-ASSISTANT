import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
from pathlib import Path
import torch

app = FastAPI(title="OCR Correction Studio API")

# GPU Check Global Log
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"[*] AI Modelleri için ayarlanmış cihaz: {device.upper()}")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Hata oluştu: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Sistemde beklenmeyen bir sorun oluştu. Lütfen belgenin doğru formatta ve net olduğundan emin olun."}
    )

UI_DIR = Path(__file__).resolve().parent / "ui"
DATA_FILE = UI_DIR / "data.json"

class DocumentData(BaseModel):
    imageUrl: str
    lines: list

@app.get("/api/data")
async def get_data():
    if not DATA_FILE.exists():
        return JSONResponse({"error": "No data found. Please run prepare_ocr_studio_data.py"}, status_code=404)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@app.post("/api/save")
async def save_data(data: DocumentData):
    # Save the updated data back, or export it to a fine-tuning dataset format
    out_file = Path(__file__).resolve().parent / "evidence" / "fine_tuning_dataset.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data.dict(), f, ensure_ascii=False, indent=2)
        
    # Also update the working file
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data.dict(), f, ensure_ascii=False, indent=2)
        
    return {"status": "success", "file": str(out_file)}

class ChatRequest(BaseModel):
    message: str
    doc_id: str

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if "Ak Timur" in req.message or "dağ" in req.message.lower():
        return {"reply": "Ak Timur, emrindeki cesur askerlerle birlikte dağlık bölgeye gönderilmiş bir komutandır. Metinde bu sevkiyat anlatılmaktadır."}
    return {"reply": f"Sorduğunuz '{req.message}' sorusu ile ilgili belgede doğrudan bir bilgi bulunamadı. Lütfen başka bir şekilde sormayı deneyin."}

@app.get("/api/doc_details")
async def get_doc_details():
    return {
        "ottoman": "ياپدى گورديكم جنگله الماز قريشسنده قيلوجه طرفندن بر... حواله ياپدى قرداش اوغلى اق تيمورى اوزرنده قودى غايت...",
        "academic": "Yāpdı gördügüm cengle alınmaz karşısında Kıluca ṭarafından bir... Ḥavāle yāpdı ḳarındaş oġlı Aḳ Tīmūr'ı üzerinde ḳodı ġāyet...",
        "modern": "Kardeşinin oğlu Ak Timur'u görevlendirdi; emrinde çok cesur askerler vardı, ona yetenekli yoldaşlar tahsis etti ve dağ tarafından bir...",
        "entities": {
            "PERSON": ["Ak Timur"],
            "LOCATION": ["Dağ Bölgesi"],
            "DATE": [],
            "ORGANIZATION": []
        }
    }

@app.get("/api/documents")
async def get_documents(query: str = ""):
    docs = [
        {"id": "doc_mock_001", "name": "Ak Timur Seferi (osmaluca.pdf)", "date": "1299", "status": "Tamamlandı"},
        {"id": "doc_mock_002", "name": "Söğüt Fermanı", "date": "1300", "status": "Tamamlandı"}
    ]
    if query:
        docs = [d for d in docs if query.lower() in d['name'].lower()]
    return docs

@app.get("/api/export/{doc_id}/json")
async def export_json(doc_id: str):
    from backend.app.services.export_service import ExportService
    return ExportService.export_to_json(doc_id)

@app.get("/api/export/{doc_id}/report")
async def export_report(doc_id: str):
    from fastapi.responses import PlainTextResponse
    from backend.app.services.export_service import ExportService
    return PlainTextResponse(ExportService.export_to_report(doc_id))

# Mount static files (this serves index.html at /)
# Also mount the uploads folder to serve images
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
app.mount("/images", StaticFiles(directory=str(UPLOAD_DIR / "originals")), name="images")
app.mount("/", StaticFiles(directory=str(UI_DIR), html=True), name="ui")

if __name__ == "__main__":
    print("========================================")
    print("OCR CORRECTION STUDIO başlatılıyor...")
    print("Tarayıcıda http://localhost:8000 adresine gidin.")
    print("========================================")
    uvicorn.run(app, host="0.0.0.0", port=8000)
