# Otonom Osmanlıca Belge Asistanı
**Kullanım Kılavuzu**

Bu kılavuz, sistemi kişisel bilgisayarınızda nasıl başlatacağınızı ve temel özelliklerini nasıl kullanacağınızı açıklar.

## 1. Sistem Gereksinimleri
- **İşletim Sistemi:** Windows 10/11
- **Programlama Dili:** Python 3.10 veya daha yenisi
- **Donanım (Önerilen):** Nvidia RTX GPU (Örn: RTX 4050 ve üzeri). Yapay Zeka modellerinin (LLM, RAG, OCR) hızlı çalışması için ekran kartınızın belleği (VRAM) kullanılacaktır.

## 2. Kurulum ve Başlatma
1. Proje klasörünü bilgisayarınıza indirin (Örn: Masaüstü).
2. Klasör içerisindeki `start_assistant.bat` dosyasına çift tıklayın.
3. Bu script otomatik olarak gerekli Python paketlerini kuracak (veya varsa kontrol edecek) ve arka planda **FastAPI** sunucusunu başlatacaktır.
4. Başlatma tamamlandığında (yaklaşık 3-5 saniye) varsayılan tarayıcınız otomatik açılarak sizi `Dashboard` ekranına yönlendirecektir.

## 3. Temel Özellikler (Modüller)

### 3.1. Belge Yükleme (Dashboard)
Dashboard ana ekranında ortada bulunan kutucuğa bir PDF belgesi veya görüntü dosyası (JPG, PNG) sürükleyip bırakabilirsiniz. Bu işlem otomatik olarak "Metin Tanıma (OCR)" ve "Belge Zekası" adımlarını başlatır.

### 3.2. RAG Destekli Akıllı Arama
Sisteme yüklediğiniz yüzlerce belge arasında **anlamsal (semantic)** aramalar yapabilirsiniz. Örneğin; *"Dağlık bölgeye gönderilen askerler"* gibi doğal dilde yazılmış bir kelime öbeği, belgede "dağ" veya "asker" geçmese bile size en alakalı belgeyi getirecektir.

### 3.3. Otonom Asistan ile Sohbet (Chat UI)
Geçmiş belgelerinizden birine tıklayarak Chat ekranına geçebilirsiniz:
- Sol tarafta orijinal Osmanlıca, İslâm Ansiklopedisi (İA) formatında transkripsiyon ve günümüz Türkçesi listelenir.
- Ayrıca belgedeki Kişi, Yer, Tarih ve Kurumlar (NER) otomatik tespit edilip size sunulur.
- Sağ taraftaki "Sohbet" alanından asistana belge hakkında doğrudan soru sorabilirsiniz. (Örn: *Bu ferman kime yazılmış?*)

### 3.4. Dışa Aktarma (Export)
Tez, makale veya arşiv çalışmaları için belgelerinizi iki formatta indirebilirsiniz:
- **JSON Formatı (`</>` ikonu):** Tüm OCR ve çeviri verisini makinece okunabilir şekilde dışa aktarır.
- **Rapor Formatı (Belge ikonu):** Belgenin Türkçe çevirisini, özetini ve tespit edilen varlıkları, temiz bir Metin/Markdown formatında bilgisayarınıza indirir.

## 4. Olası Hata Çözümleri
- **Sunucu Açılmıyor:** CMD (Komut İstemi) penceresinde `error` içeren bir yazı görürseniz, muhtemelen Python PATH ayarlarına eklenmemiştir. Python'u kurarken "Add Python to PATH" kutucuğunun işaretli olduğundan emin olun.
- **Yapay Zeka Hata Veriyor:** Cihazınızda yeterli boş RAM/VRAM kalmamış olabilir. Tarayıcınızda veya arka planda çalışan ağır uygulamaları kapatıp tekrar deneyin.
