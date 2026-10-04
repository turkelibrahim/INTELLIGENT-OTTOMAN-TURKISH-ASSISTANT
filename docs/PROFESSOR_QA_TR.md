# Profesör Soru-Cevap Hazırlığı

## OCR ve Model

**Soru:** OCR motoru nedir?

**Yanıt:** Üretim hattında OCR motoru Kraken olarak doğrulanır. Final gate kanıtında `ocr_engine=kraken` ve `fallback_used=false` döndü.

**Soru:** EasyOCR veya mock fallback var mı?

**Yanıt:** Final demo akışında EasyOCR fallback kullanılmadı. Eski engine kayıtları kodda bulunabilir, ancak bu gate gerçek endpoint sonucunda Kraken çalışmasını ve fallback olmamasını doğrular.

**Soru:** Model dosyasının değişmediğini nasıl biliyoruz?

**Yanıt:** `pre_demo_check.ps1`, `models/recognition/ottoman_recognition_final_v1.mlmodel` dosyasının SHA-256 değerini beklenen değerle karşılaştırır.

## RAG ve Kanıt

**Soru:** Tarihsel analiz nereden geliyor?

**Yanıt:** Qdrant tabanlı yerel tarihsel corpus kullanılır. Pre-demo kontrolde corpus erişimi ve kayıt sayısı doğrulanır; browser E2E sonucunda doğrulanmış harici kaynak sayısı kaydedilir.

**Soru:** Sistem kesin tarihsel hüküm veriyor mu?

**Yanıt:** Hayır. Belge kanıtı, doğrulanmış harici kaynak ve model çıkarımı ekranda ayrı etiketlenir. Belirsiz alanlar açıkça gösterilir.

## Güvenlik

**Soru:** Dosya yükleme güvenli mi?

**Yanıt:** Dosya uzantısı, boyut limiti ve yetkili endpoint kontrolleri korunur. Final security audit UI’da yerel dosya yolu, secret, traceback veya model yolu sızıntısı olmadığını doğrular.

**Soru:** Debug açık mı?

**Yanıt:** Release varsayılanı `DEBUG=False` olarak sertleştirildi. Demo launcher ayrıca `DEBUG=production` env değeriyle backend’i başlatır.

## Demo ve Operasyon

**Soru:** Demo günü nasıl başlatılır?

**Yanıt:** `scripts/pre_demo_check.ps1` ile sağlık kontrolü yapılır, ardından `scripts/start_demo.ps1` çalıştırılır. Gerekirse `scripts/stop_demo.ps1` yalnız kayıtlı demo PID’lerini kapatır.

**Soru:** İnternet gerekirse ne olur?

**Yanıt:** Final demo yerel Ollama modeli ve yerel Qdrant corpus ile çalışacak şekilde hazırlanmıştır. Dış API anahtarı gerektirmeyen yol tercih edilir.

**Soru:** En büyük kalan risk nedir?

**Yanıt:** Frontend production modda React hydration uyarıları yakalandı; E2E fonksiyonel olarak geçti, ancak görsel/SSR stabilitesi için ayrıca temizlenmesi önerilir.
