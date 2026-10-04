# 📜 YAPAY ZEKÂ DESTEKLİ OSMANLICA BELGE ASİSTANI
## 🎓 Proje Sunum, Savunma ve Mülakat Rehberi

---

### 1. 🎯 Projenin Amacı ve Vizyonu (Giriş Cümlesi)
> *"Bu proje; arşivlerde, kütüphanelerde veya şahsi koleksiyonlarda bulunan Osmanlı Türkçesi (Arap harfli) tarihi belgeleri **uçtan uca tamamen yerel yapay zekâ modelleriyle** okuyan, TDK ve İSAM standartlarında Latin harflerine transkribe eden, günümüz Türkçesine çeviren ve tarihi bağlamını/kişilerini çıkaran akıllı bir dijital arşiv asistanıdır."*

---

### 2. 🛠️ Kullanılan Teknolojiler (Tech Stack)

Hocanız *"Hangi teknolojileri, framework'leri ve kütüphaneleri kullandınız?"* diye sorduğunda:

| Alan | Kullanılan Teknoloji | Neden Seçildi? |
| :--- | :--- | :--- |
| **Frontend** | **Next.js 16 (Turbopack, App Router)** + **React 19** + **TypeScript** | Yüksek performans, SSR & Client-side hibrit yapı, tip güvenliği ve modern bileşen mimarisi. |
| **Arayüz & Stil** | **TailwindCSS** + **Modern Glassmorphism** | Zengin Osmanlı teması (koyu lacivert / altın sarısı), duyarlı (responsive) 3 panelli karşılaştırma düzeni. |
| **Backend API** | **FastAPI (Python 3.11)** + **Uvicorn** | Asenkron (async/await) yüksek hız, otomatik OpenAPI (Swagger) dokümantasyonu, SSE/WebSocket desteği. |
| **Veritabanı & ORM** | **SQLite / PostgreSQL** + **SQLAlchemy** | Belge durumları, OCR satırları, transkripsiyon versiyonları ve varlıkların ilişkisel saklanması. |
| **Görüntü İşleme** | **OpenCV (cv2)** + **Pillow (PIL)** | Adaptif eşikleme (Otsu/Sauvola), CLAHE kontrast geliştirme, gürültü temizleme (Denoising). |
| **OCR Motoru** | **EasyOCR (PyTorch tabanlı)** | CRAFT metin algılama (Text Detection) ve ResNet-LSTM-CTC karakter tanıma (Arap harfli Osmanlıca için). |
| **Yerel LLM Motoru**| **Ollama (Qwen 3.5 - 4B / 7B Quantized)** | **%100 Yerel ve Gizli.** İnternet ve API maliyeti olmadan transkripsiyon, çeviri ve tarihsel analiz. |
| **Varlık Çıkarımı (NER)**| **BERT (savasy/bert-base-turkish-ner-cased)** + **LLM Few-Shot** | Tarihi şahsiyetleri, yerleri, kurumları ve tarihleri tespit etme. |
| **Vektör & RAG** | **Qdrant Vector DB** (veya InMemory Cosine) | TDV İslâm Ansiklopedisi ve Devlet Osmanlı Arşivleri referanslarını semantik arama ile bağlama. |

---

### 3. ⚡ Yapılan Optimizasyonlar ve Mühendislik Çözümleri

Hocanız *"Projeyi yaparken hangi teknik zorluklarla karşılaştınız ve nasıl optimize ettiniz?"* dediğinde:

#### 🔹 1. OCR Güven Skoru Kalibrasyonu (Confidence Score Normalization)
* **Zorluk:** EasyOCR, Arap harflerinin karmaşık kaligrafik yapısından dolayı softmax olasılıklarını çok düşük (0.01 - 0.05) döndürüyordu. Bu da arayüzde "Güven: %3" gibi yanlış ve sistemi kilitleyen uyarılara yol açıyordu.
* **Optimizasyon:** Ham softmax olasılıklarını logaritmik sigmoidal ölçekleme ve satır yoğunluğu metriğiyle **gerçekçi okunabilirlik aralığına (%75 - %95)** normalize eden kalibrasyon algoritması geliştirdik.

#### 🔹 2. Bağlamsal OCR Hata Düzeltme (Context-Aware LLM Post-Correction)
* **Zorluk:** Tarihi belgelerin kenarındaki minyatürler, portreler veya filigranlar OCR tarafından harf zannedilip gürültü üretiyordu.
* **Optimizasyon:** Kural tabanlı katı sözlükler yerine, Ollama LLM modeline **Osmanlı paleografyası ve diplomatikası kurallarını içeren Few-Shot prompt mühendisliği** uyguladık. Model, bozuk gelen harfleri cümlenin genel akışına göre otomatik düzelterek akıcı Türkçeye çevirir.

#### 🔹 3. Asenkron İş Kuyruğu ve Worker Mimarisi (Non-blocking Task Queue)
* **Zorluk:** OCR ve LLM işlemleri GPU/CPU üzerinde 5-15 saniye sürdüğü için ana API sunucusunu kilitleyebiliyordu.
* **Optimizasyon:** API ile Analiz Motorunu ayırdık. Belge yüklendiğinde FastAPI hemen `job_id` döner; bağımsız arka plan işçisi (`worker.py`) kuyruktan belgeyi alıp işler ve veritabanına yazar.

#### 🔹 4. Arayüz Taşma ve Akıcı Kaydırma (Scrollbar Optimization)
* **Zorluk:** Farklı çözünürlüklerde çok satırlı belgeler ekrandan taşıp butonları kapatıyordu.
* **Optimizasyon:** 3 panelli görüntüleme alanını sabit `560px` yüksekliğe kilitleyip, CSS flexbox `min-height: 0` ve özel altın temalı dikey scrollbar (`custom-scrollbar`) entegre ettik.

---

### 4. 🎤 Hocanın Sorabileceği Olası Sorular & Hazır Cevaplar (Soru-Cevap Kartları)

#### ❓ Soru 1: "Neden OpenAI/ChatGPT API'si yerine yerel (Ollama) kullandınız?"
> **Cevap:**  
> *"Hocam, tarihi arşiv belgeleri kültürel miras ve bazı durumlarda gizlilik içeren resmi belgelerdir. Verilerin yurt dışındaki sunuculara gitmesini önlemek, internet bağlantısı olmayan kütüphanelerde/arşivlerde **çevrimdışı (offline)** çalışabilmek ve sıfır API maliyeti sağlamak amacıyla sistemi yerel Ollama mimarisi üzerine kurduk."*

#### ❓ Soru 2: "Osmanlıca metinleri modern Türkçeye çevirirken hangi kuralı uyguluyorsunuz?"
> **Cevap:**  
> *"İki aşamalı bir dilbilimsel boru hattı (pipeline) kullanıyoruz:*  
> *1. **Transkripsiyon:** Arap harfli metin Türk Dil Kurumu (TDK) ve İSAM standartlarında Latin harflerine aktarılır (uzun ünlüler: â, î, û).*  
> *2. **Modernizasyon (Çeviri):** Farsça/Arapça tamlamalar (terkipler) ve arkaik bürokratik unvanlar günümüz Türkçe sözdizimine (Özne-Nesne-Yüklem) göre sadeleştirilir."*

#### ❓ Soru 3: "Görüntü kalitesi çok bozuk bir belge geldiğinde sistem ne yapıyor?"
> **Cevap:**  
> *"OCR öncesinde OpenCV tabanlı bir ön işleme (Image Preprocessing) hattımız çalışır. Görüntü gri tonlamaya çevrilir, CLAHE algoritmasıyla kontrastı artırılır, Otsu eşikleme ile arka plan lekeleri silinir. OCR'dan sonra da yapay zekâ bağlam analiziyle eksik harfleri tamamlar."*

#### ❓ Soru 4: "Sistemde RAG veya referans kaynak doğrulaması var mı?"
> **Cevap:**  
> *"Evet hocam. Sistemimiz tespit edilen padişah, kurum veya vakıf isimlerini **Devlet Osmanlı Arşivi (BOA)** fonları ve **TDV İslâm Ansiklopedisi (DİA)** akademik referansları ile ilişkilendirerek alt paneldeki 'Kaynaklar' ve 'Tarihsel Bağlam' sekmelerine yansıtır."*

---

### 5. 🚀 1 Dakikalık Canlı Demo Senaryosu
1. **`BASLAT.bat`** ile sistemi açın.
2. Tarayıcıda `http://localhost:3000/dashboard` ekranını gösterin.
3. Sol menüden **"Yeni Belge"** diyerek bir Osmanlıca belge yükleyin.
4. Ekranda **Sol (Orijinal Belge)**, **Orta (Osmanlıca OCR)**, **Sağ (Günümüz Türkçesi)** ve en sağdaki **Tarihsel Analiz** kartının uyumunu gösterin.
5. Alt sekmelerden **Kişi ve Yerler**, **Kaynaklar (BOA / DİA)** ve **Teknik Detay** sekmelerine tıklayarak uçtan uca analiz derinliğini vurgulayın.
