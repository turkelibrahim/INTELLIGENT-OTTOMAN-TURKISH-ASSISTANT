# Demo ve Release Hazırlığı

## Startup Commands
**Backend & Worker:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
python worker.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Dependencies:**
- PostgreSQL, Redis, Qdrant (Docker veya Local)
- Ollama (qwen model yüklü olmalı)

## Demo Checklist
- [ ] Sistem healthcheck kontrol edildi (`python backend/scripts/healthcheck.py`).
- [ ] Login yapıldı.
- [ ] `silah-atmama-ilani_ahmed-vefik-pasa.jpg` belge upload edildi.
- [ ] Preprocessing ve OCR aşamaları progress bar üzerinden takip edildi.
- [ ] Original Image ve OCR bounding box'lar UI'da görüntülendi.
- [ ] Latin Transliteration ve Modern Türkçe sekmeleri açılıp veriler doğrulandı.
- [ ] OCR Review panelinde bir satır düzenlendi, kaydedildi ve UI/DB'de güncellendi.
- [ ] Downstream (Transliteration/Modernization) RAG/Vector store verileri doğrulandı.
- [ ] Belge arşive kaydedildi, dashboard'dan geri dönüldü ve persist olduğu gösterildi.

## Performance Numbers (Local RTX 4050 / 16GB)
- Q5_READTEXT_CONFIG EasyOCR batch_size=16
- Dummy image (no-text): ~2.39s
- Tam sayfa Osmanlıca (Kraken + HF NER): ~10-15s

## Known Limitations
- HF NER modeli (`savasy/bert-base-turkish-ner-cased`) ilk yüklemede internet bağımlılığı içeriyor (HF Cache yoksa indirir).
- Tam sayfa çevirilerde Ollama-qwen modeli local GPU'ya göre yavaş yanıt verebilir.
- Playwright E2E browser testleri yerel ortamda X11/ekran bağımlılığı isteyebilir.

## Test Report
- **E2E Quality Gates:** PASS (`test_full_e2e_flow.py`, `run_e2e_acceptance.py` başarılı).
- **False Pass Audit:** PASS (Sahte confidence, mocked pipeline, yutulan loglar temizlendi).
- **GPU Optimization:** PASS (Pipeline ve engine caching ile bellek korundu).

## Recovery & Rollback Notes
- Eğer local worker kitlenirse: `kill` komutuyla `worker.py` durdurulup yeniden başlatılabilir. Pipeline cache'i otomatik rebuild edilir.
- Veritabanı state corruption olursa: SQLite/Postgres `alembic downgrade` veya DB backup restore.
- Model cache bozulursa: `C:\Users\ibrah\.cache\huggingface` silinebilir.
