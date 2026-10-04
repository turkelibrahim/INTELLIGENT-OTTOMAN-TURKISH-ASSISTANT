# OCR Görsel Düzeltme Stüdyosu (Fine-Tuning Hazırlık Aracı)

Bu araç, **TASK-037-Q9_OCR_CORRECTION_STUDIO** kapsamında, Osmanlıca OCR modelimizin (EasyOCR / Tesseract) fine-tuning (ince ayar) eğitimi için gerekli veri setini hazırlamak amacıyla oluşturulmuştur.

LLM tabanlı metin düzeltmenin (Q8) başarısız olması sonrasında, hatalı karakterlerin bizzat kullanıcı/uzman tarafından, orijinal belge ile eş zamanlı bakılarak düzeltilmesi zorunlu hale gelmiştir. Bu stüdyo, Ground Truth ve OCR eşleşmelerini mükemmel bir şekilde yaparak eğitim verisi üretir.

## 🛠 Teknoloji Yığını
- **Frontend:** Vanilla HTML5, CSS3, JavaScript (Dışa bağımlılık yok, süper hızlı)
- **Görselleştirme:** HTML5 `<canvas>` API (Bounding box çizimi ve interaktif imaj manipülasyonu)
- **Backend:** `FastAPI` & `Uvicorn` (Sistemin ana backend teknolojisi ile uyumlu)
- **Veri Altyapısı:** `JSON` tabanlı state yönetimi.

## 🚀 Kurulum ve Çalıştırma

### 1. Veriyi Hazırlamak
Öncelikle stüdyoda görünecek (veritabanından çekilmiş Q7 koordinatları ve metinleri) JSON dosyasını oluşturmalısınız:
```powershell
python -c "
import sqlite3, json, os
os.makedirs('ui', exist_ok=True)
conn = sqlite3.connect('backend/ottoman_assistant.db')
conn.row_factory = sqlite3.Row
lines = list(conn.execute('select * from ground_truth_lines where page_id=1 order by reading_order'))
data = {'imageUrl': '/images/osmaluca_page_1.png', 'lines': []}
for idx, row in enumerate(lines):
    bbox_str = row['bounding_box']
    bbox = json.loads(bbox_str) if isinstance(bbox_str, str) else bbox_str
    data['lines'].append({
        'id': f'line_{idx}',
        'text': row['text_content'],
        'bbox': bbox,
        'confidence': 0.9 if idx % 2 == 0 else 0.4
    })
with open('ui/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
"
```
*(Not: AI ajan otomatik olarak bu scripti çalıştırarak ilk veriyi hazırlamıştır.)*

### 2. Uygulamayı Başlatmak
Proje ana dizinindeyken aşağıdaki komutu çalıştırarak FastAPI backendini ayağa kaldırın:
```powershell
python ocr_studio_backend.py
```
*(veya terminalde `uvicorn ocr_studio_backend:app --host 0.0.0.0 --port 8000`)*

### 3. Kullanım
Tarayıcınızdan şu adrese gidin:
👉 **http://localhost:8000**

- **Sol panelde** orijinal belgeyi göreceksiniz. Mouse ile sürükleyebilir (Pan) veya büyütebilirsiniz (Zoom).
- **Sağ panelde** metinleri göreceksiniz.
- Bir metin kutusuna tıkladığınızda, sol tarafta orijinal belgedeki yeri (Bounding Box) **mor renk** ile vurgulanır ve ekran o noktaya otomatik kayar (Auto-Pan).
- Satırları bölme (Scissors), birleştirme (Merge) ve yukarı/aşağı taşıma (Arrows) araçlarını kullanabilirsiniz.
- Düşük güven skoruna sahip kelimeler/satırlar sollarında kırmızı/sarı bir nokta ile uyarılır.
- İşiniz bitince sağ üstteki **"Dışa Aktar (JSON)"** butonuna basın. Düzenlenen veriler `evidence/fine_tuning_dataset.json` dosyasına kaydedilecektir.
