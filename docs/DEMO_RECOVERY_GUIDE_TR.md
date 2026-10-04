# Demo Kurtarma Rehberi

## Hızlı Sağlık Kontrolü

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\pre_demo_check.ps1
```

Başarılı çıktı: `PRE_DEMO_HEALTH_GATE: PASS`.

## Demo Başlatma

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\start_demo.ps1
```

## Demo Durdurma

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\stop_demo.ps1
```

Bu script yalnız `runtime/demo/*.pid` içinde kayıtlı demo süreçlerini ve onların alt süreçlerini kapatır.

## Yaygın Sorunlar

### Port 8000 veya 3000 Dolu

Önce:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\stop_demo.ps1
```

Sonra tekrar başlatın. Portu yabancı bir süreç kullanıyorsa script bunu öldürmez; ilgili uygulamayı elle kapatın veya farklı portlarla başlatın.

### Ollama Modeli Yok

```powershell
ollama list
```

Gerekli modeller:

- `qwen3.5:4b`
- `qwen3-embedding:0.6b`

### Kraken Hatası

`scripts/pre_demo_check.ps1` Kraken model dosyasını ve SHA değerini doğrular. Model yoksa veya SHA tutmuyorsa demo başlatılmamalıdır.

### Frontend Build Hatası

```powershell
cd frontend
npm.cmd run build
```

PowerShell execution policy nedeniyle `npm` aliası sorun çıkarırsa `npm.cmd` kullanın.

### Backend Test veya Import Hatası

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_unknown_document_pipeline.py tests/test_ocr_engine.py tests/test_kraken_integration.py -q
```

### Qdrant Corpus Kilidi

Qdrant path varsayılan olarak `C:\ottoman_ai_data\qdrant` altındadır. Başka bir süreç aynı storage’ı kilitlediyse onu kapatıp tekrar deneyin.

### Analiz Uzun Sürüyor

Kraken OCR ve yerel LLM çağrıları donanıma göre yavaşlayabilir. Final E2E ölçümünde tam analiz yaklaşık 59 saniye sürdü.
