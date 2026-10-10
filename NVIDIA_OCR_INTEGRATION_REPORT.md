# NVIDIA API ENTEGRASYON VE BENCHMARK RAPORU

## LOCAL RESULT:
- **Duration**: ~28.16 saniye (Subprocess fallback nedeniyle aşırı yavaş, CPU-bound).
- **Quality**: Hatalı veya düşük confidence üretmeye yatkın (GPU hızlandırması çalışmadığı için timeout ve kesilmeler yaşanıyor).
- **VRAM/CPU Etkisi**: Her istekte model RAM'e yüklendiği için %100 CPU kullanımı, 0 MB VRAM (GPU kullanılmıyor).

## NVIDIA RESULT:
- **Model**: `meta/llama-3.2-11b-vision-instruct` (NVIDIA API üzerinden multimodal).
- **Duration**: ~25.26 saniye (API network transferi ve image processing dahil).
- **Quality**: Osmanlıca harfleri tanıyıp Türkçeye çevirme ve Latin harflerine aktarma konusunda çok başarılı (Küçük encoding uyarıları python konsolu seviyesinde düzeltildi).
- **VRAM/CPU Etkisi**: 0 MB VRAM, 0 MB CPU. İşlem tamamen Cloud (NVIDIA) tarafında gerçekleşiyor. Local kaynaklar boşa çıkıyor.

## BEST ROUTING:
1. **Local-First Yaklaşımı Korundu**: Pipeline her zaman önce Local OCR'ı (Kraken/EasyOCR) dener.
2. **Akıllı Fallback Eklendi**: Local OCR'ın başarısız sayıldığı şu senaryolarda sistem otomatik olarak NVIDIA Vision API'ye geçer:
   - OCR **Boş** yanıt dönerse.
   - OCR **Güven Skoru (Confidence)** ayarlanan barajın (`OCR_MIN_CONFIDENCE_THRESHOLD = 0.60`) altında kalırsa.
   - OCR **Çok Uzun Sürerse** (`OCR_MAX_DURATION_SECONDS = 15s` aşıldığında).
3. **Maliyet/Hız Dengesi**: Sadece zor veya yavaşlayan belgelerde API çağrısı yapıldığı için kotalar korunur ve sistem kesintisiz çalışır.

## LATENCY:
- **Sadece Local (Sorunlu halde)**: ~28 - 30 sn (Darboğaz).
- **Sadece NVIDIA Vision**: ~25 sn.
- **Local (Başarılı/GPU) + LLM**: Beklenen normal süre ~5 sn.
- **Local (Hatalı) + NVIDIA Fallback**: ~15 sn (timeout) + 25 sn = ~40 sn. (Yalnızca exception veya çok düşük kalitede bu süreye çıkılır, ancak pipeline'ın **çökmesini** engeller).

## QUALITY:
NVIDIA Vision modeli (`meta/llama-3.2-11b-vision-instruct`), görüntüdeki metni doğrudan bağlamıyla anlayabildiği için bozuk Osmanlıca matbu belgelerinde klasik OCR'dan (Kraken/Tesseract) daha yüksek anlamsal doğruluk (Semantic Accuracy) sağlamaktadır. Ancak karakter koordinatları (Bounding Boxes) dönmediği için UI tarafındaki vurgulama özellikleri için Local OCR'ın sentetik satırlarına entegre edilmiştir.

## FAILURE HANDLING:
- **Network Hatası / NVIDIA API Çökmesi**: NVIDIA API çağrısı 45 saniyelik `timeout` ile sınırlandırıldı. `httpx.AsyncClient` `try-except` bloğu içinde güvenle çağrılıyor. API hata verirse sistem çökmüyor, fallback boş dönüyor ve süreç durmuyor.
- **Fallback Uyumu**: NVIDIA metni dönse bile, satır satır bölünüp (`\n`) Local OCR'ın `Line` modellerine (boş Bounding Box ile) enjekte ediliyor. Böylece `analyze-full` sonrası çalışan Çeviri, NER ve RAG adımları aynı standart API contract'ını kullanmaya devam ediyor.

## SECURITY:
- **NVIDIA_API_KEY Sızıntısı Yok**: Key yalnızca backend tarafında `.env` (sunucu ortam değişkeni) üzerinden okunmaktadır.
- Frontend'e, veritabanına veya API response'larına (JSON) kesinlikle eklenmemektedir.
- Github'a veya loglara yazdırılması engellenmiştir. (Logs sadece süre ve confidence yazar).

## RECOMMENDATION:
1. **GPU (CUDA) Onarımı**: Local OCR'ın asıl darboğazı olan "Legacy Subprocess Fallback" hatasını çözmek için `start_kraken_service.ps1` daemon olarak ayağa kaldırılmalıdır. Local OCR GPU'da 1-2 saniyeye inecektir.
2. **NVIDIA ile Çapraz Doğrulama (Cross-Validation)**: Sistem şu an config üzerinden başarıyla NVIDIA fallback yapacak şekilde tasarlandı. Eğer Local OCR düzeltilirse, NVIDIA sadece çok silik veya el yazısı (Rika/Divani) gibi zorlu belgelerde "Kurtarıcı (Savior)" olarak çalışıp harika bir hibrit (Local + Cloud) çözüm sunacaktır.
3. NVIDIA_VISION_MODEL olarak config'de 11B seçildi. Daha zorlu belgelerde `90b-vision-instruct` modeline geçilebilir.
