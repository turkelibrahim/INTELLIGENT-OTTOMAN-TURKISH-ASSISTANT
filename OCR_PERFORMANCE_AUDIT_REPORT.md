# OCR PERFORMANCE AUDIT REPORT

## 1. Mevcut `analyze-full` Akışı (DocumentAnalysisPipeline)
Pipeline, `worker.py` içindeki `process_full_document_analysis_job` üzerinden tetiklenmektedir ve `DocumentAnalysisPipeline.analyze_document()` sınıfını çağırır.
Akış sırası:
1. `_process_page` (Image Load -> Preprocessor -> OCR Inference)
2. `_transliterate` (TransliterationEngine - LLM API Call)
3. `_modernize` (Translator - LLM API Call)
4. `_line_transformations` (Metinlerin hizalanması ve satır içi Entity Extraction - NER LLM API Call)
5. `visual_extractor.extract` (Görsel varlık analizi)
6. `_document_claims` & `_retrieval_query` (RAG için metin hazırlığı)
7. `_retrieve_verified_historical_evidence` (Qdrant BM25 + Dense Retrieval)
8. `intelligence.enrich_entities` (DocIntelligenceEngine - Tarihsel Analiz LLM API Call)
9. (Optional) `smart_router.selective_document_verification` (Cloud/Lokal Güvenlik Kontrolü)

## 2. Aşamaların Ölçüm Sonuçları (RTX 4050 - 6GB VRAM)
Bir adet test görseli (`175_230f03eb.jpg`) ile izole pipeline üzerinde yapılan benchmark (LLM hariç tam donanım analizi) sonucu:

| Aşama | Süre (ms) | VRAM Kullanımı (MB) |
|---|---:|---:|
| Image Loading | 8.40 ms | 0.00 MB |
| Preprocessing | 302.35 ms | 0.00 MB |
| OCR Engine Load | 4958.58 ms (4.95 sn) | 0.00 MB |
| **OCR Inference** | **28167.97 ms (28.16 sn)** | **0.00 MB (CPU'ya düşüyor)** |
| Transliteration Engine Load | 1353.72 ms | 0.00 MB |
| LLM Inferences (Transliteration, vb.) | ~ 8000 - 16000 ms (Tahmini Toplam) | Ollama VRAM kullanır (~3.5 GB) |
| RAG (Qdrant & Embeddings) Load | ~ 800 ms | 0.00 MB |

*Not: LLM (Ollama) modellerinin kendi bellek yönetimi dışsal (external process) olduğundan backend script'in VRAM footprint'i 0 MB görünmektedir.*

## 3. Özel Kontroller ve Soruların Cevapları

- **OCR modeli her request'te tekrar yükleniyor mu?**
  **HAYIR.** `ocr_factory.py` içindeki `_ENGINE_CACHE` global değişkeni sayesinde ilk çağrıda yüklenir, sonraki `DocumentAnalysisPipeline` yaratımlarında cache'den okunur (Engine load süresi yansıtılmaz). ANCAK, aşağıda belirtilen fallback hatasından dolayı model her işlemde alt-süreçte (subprocess) tekrar yükleniyor!
- **Ollama modeli her request'te tekrar çağrılıyor mu?**
  **EVET.** `OllamaProvider` REST API üzerinden Ollama sunucusuna HTTP çağrıları yapar. VRAM'e yeniden model yüklenmez ancak network/API gecikmesi eklenir (Stateless çağrılar).
- **Embedding modeli gereksiz yere tekrar başlatılıyor mu?**
  **HAYIR.** `HistoricalQdrantStore` singleton kalıbı (`__new__` ile `_STORE_CACHE`) kullanır. Modeller (BGE/BM25) sadece bir kez RAM'e yüklenir.
- **Aynı görüntü birden fazla preprocess ediliyor mu?**
  **HAYIR.** Sayfa başına tam 1 kez işlenir.
- **Aynı OCR birden fazla çalıştırılıyor mu?**
  **HAYIR.** Sayfa başına 1 kez çalıştırılır.
- **Aynı belge tekrar analiz ediliyor mu?**
  **HAYIR.** Veritabanı durum (`status`) yönetimi ve `worker.py` üzerindeki kilitler bunu engelliyor.
- **RAG gereksiz şekilde her sayfada çalışıyor mu?**
  **HAYIR.** Sayfalar döngüde (`_process_page`) işlendikten sonra, tüm doküman metni birleştirilerek RAG sadece DOKÜMAN BAŞINA 1 kez çağrılır.
- **Tüm pipeline synchronous mı?**
  **Kısmen.** `analyze_document` metodu ve OCR işlemleri `async` (Ollama çağrıları vb.), ancak `ImagePreprocessor` gibi CPU-bound kısımlar event-loop'u bloke eden synchronous yapıdadır.
- **Tek backend worker request boyunca bloklanıyor mu?**
  **Kısmen.** Asenkron yazılmış olsa da, arka planda çalışan ve CPU sömüren OCR fallback süreci veya senkron preprocess adımları (OpenCV) concurrency'yi ciddi şekilde yavaşlatır.
- **Büyük image'lar gereksiz şekilde RAM/VRAM'de kopyalanıyor mu?**
  Preprocess işleminde standart numpy array kopyaları oluşuyor, 6 GB kısıtı için kritik bir RAM dar boğazı değil (VRAM'e geçmediği için).

## 4. Bottlenecks (Darboğazlar)

### BOTTLENECK #1
**OCR Inference (28.16 saniye / Sayfa)**
- Pipeline'ın uzak ara en yavaş adımı. Bunun sebebi kod içindeki fallback mekanizmasıdır.
- Loglarda karşılaşılan hata: `PERSISTENT_OCR_SERVICE_UNAVAILABLE USING_LEGACY_SUBPROCESS_FALLBACK`
- GPU kullanımı yok (Pytorch CPU fallback: `'pin_memory' argument is set as true but no accelerator is found`).

### BOTTLENECK #2
**LLM API Çağrı Sayısı (Network & Sequential Execution)**
- Bir belge için en az 4 ayrı ağır LLM çağrısı yapılıyor: Transliterasyon, Çeviri, NER, Tarihsel Analiz. Bu işlemler ardışık (sequential) olduğu için birinin bitmesi diğerini bekliyor ve toplam süreye (approx. 10-15s) ekleniyor.

### BOTTLENECK #3
**Preprocess ve Senkron Kod Blokları**
- 302ms süren `ImagePreprocessor.process` asyncio thread-pool dışında (doğrudan async metot içinde senkron olarak) çalıştırıldığı için yüksek hacimde event loop'u bloke etme potansiyeline sahip.

## 5. Kritik Problem Raporu (Kök Neden)

**ROOT CAUSE:** 
Kraken tabanlı OCR modeli (PyTorch) yerel GPU (CUDA) ortamında veya kalıcı bir servis (Persistent Service port: 8765) olarak çalışmıyor. Kod, bu servise ulaşamadığı için "Legacy Subprocess Fallback" moduna geçiyor. 

**EVIDENCE:** 
```text
C:\projeler\INTELLIGENT OTTOMAN TURKISH ASSISTANT\backend\venv\Lib\site-packages\torch\utils\data\dataloader.py:759: UserWarning: 'pin_memory' argument is set as true but no accelerator is found, then device pinned memory won't be used.

PERSISTENT_OCR_SERVICE_UNAVAILABLE USING_LEGACY_SUBPROCESS_FALLBACK: HTTPConnectionPool(host='127.0.0.1', port=8765): Max retries exceeded with url: /health/ready (Caused by ConnectTimeoutError(<HTTPConnection(host='127.0.0.1', port=8765) at 0x1eda04bb390>, 'Connection to 127.0.0.1 timed out. (connect timeout=2)'))
```
Proje kök dizininde bulunan `start_kraken_service.ps1` dosyasının çalıştırılmamış olması (veya hata vermesi), OCR motorunu her seferinde diskten modeli yükleyen çok yavaş bir "CPU Subprocess" moduna sokuyor.

**ESTIMATED IMPACT:** 
1 saniye civarında sürmesi gereken OCR işlemi, 28 saniyeye uzayarak %2700 oranında performans kaybı (ve CPU tarafında %100 yük) yaratıyor. GPU'nun (RTX 4050) tamamen boşa çıkmasına neden oluyor.

**RECOMMENDED FIX:** 
1. `start_kraken_service.ps1` başlatılmalı ve persistent OCR servisinin 8765 portunda sağlıklı yanıt verdiğinden emin olunmalıdır (`check_kraken_service.ps1`).
2. WSL/PyTorch ortamında CUDA desteğinin (`no accelerator is found` hatası) aktif olup olmadığı kontrol edilmeli.

## 6. Soruya Kesin Cevap

**Soru:** *"OCR'ın yavaş olmasının gerçek nedeni OCR inference mı, yoksa OCR'dan sonra çalışan diğer AI/RAG adımları mı?"*

**Kesin Cevap:** **Yavaşlığın gerçek ve asıl nedeni KESİNLİKLE OCR Inference'dır.** 
Benchmark sonucunda tek bir sayfa için sırf OCR adımı CPU'da **28 saniye** sürmüştür. Diğer AI/RAG adımları API çağrısı ve LLM inferenceları gerektirdiği için 10-15 saniye ek süre yaratsa da, OCR'ın bu derece (normalden 25x yavaş) uzun sürmesi sistemin kilitlenmesine sebep olmaktadır. Sorun model ağırlığında değil, Persistent Service kapalı olduğu için OCR'ın **subprocess içinde CPU ile çalıştırılmaya (fallback)** zorlanmasıdır.
