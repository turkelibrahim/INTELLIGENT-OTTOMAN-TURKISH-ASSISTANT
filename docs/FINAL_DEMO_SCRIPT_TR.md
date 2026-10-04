# Final Demo Akış Metni

## Açılış

Bu proje, Osmanlı Türkçesi belgeler için uçtan uca çalışan bir analiz asistanıdır. Demo boyunca tek bir gerçek belge üzerinden yükleme, görüntü hazırlama, Kraken OCR, Latin transliterasyon, günümüz Türkçesi aktarımı ve doğrulanmış tarihsel RAG kanıtlarını göstereceğim.

## Demo Öncesi Kontrol

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\pre_demo_check.ps1
```

Beklenen sonuç `PRE_DEMO_HEALTH_GATE: PASS` olmalıdır. Bu kontrol Ollama modellerini, Kraken model SHA değerini, Qdrant corpus erişimini, Python bağımlılıklarını ve frontend build durumunu doğrular.

## Sistemi Başlatma

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\start_demo.ps1
```

Başarılı durumda:

- Frontend: `http://127.0.0.1:3000/login`
- Backend dokümantasyonu: `http://127.0.0.1:8000/docs`
- API: `http://127.0.0.1:8000/api/v1`

## Canlı Gösterim Sırası

1. Login veya kayıt ekranından giriş yapılır.
2. Ana dashboard açılır ve Osmanlıca belge seçilir.
3. `Analiz Et` ile gerçek `POST /api/v1/document/analyze-full` endpointi çağrılır.
4. Sonuçta OCR motoru `kraken`, fallback `false`, OCR satırları, Latin okunuş, günümüz Türkçesi ve tarihsel kanıtlar gösterilir.
5. Görüntü İşleme Laboratuvarı açılır; orijinal belge, OCR-safe çıktı ve üretilmeyen ara aşamalar açıkça ayrılır.
6. Tarihsel Analiz ekranında belge kanıtı, doğrulanmış harici kaynaklar, model çıkarımları ve belirsizlikler birlikte gösterilir.
7. `Yeni Analiz` ile oturum bağlamının sıfırlandığı gösterilir.
8. Mobil genişlikte responsive görünüm kısaca gösterilir.

## Vurgulanacak Noktalar

- OCR motoru Kraken olarak sabittir.
- EasyOCR fallback kullanılmaz.
- RAG kanıtları Qdrant corpus içinden gelir.
- Görsel restorasyon OCR girdisi değildir; OCR-safe çıktı ayrı işaretlenir.
- Belirsizlikler saklanmaz, kullanıcıya görünür.
- Windows üzerindeki Türkçe karakterli proje yolunda çalışır.

## Kapanış

Bu demo bir mock ekran değildir. Backend, frontend, Kraken OCR, Ollama ve Qdrant aynı anda gerçek veriyle çalıştırılmıştır. Kanıt dosyaları `evidence/final_release_gate/` altında saklanır.
