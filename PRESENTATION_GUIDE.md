# 🎯 Teknik Mülakat ve Sunum Rehberi (45 Dakika)

Bu doküman, "Intelligent Ottoman Turkish Assistant" projesini teknik bir jüriye, yatırımcılara veya CTO/Mimar seviyesindeki yöneticilere sunarken kullanacağınız **45 dakikalık** ideal sunum akışını içermektedir.

---

## ⏱️ Sunum Zaman Çizelgesi (Timeline)

- **[00:00 - 10:00]** Bölüm 1: Vizyon, Problem Tanımı ve Değer Önerisi (10 Dk)
- **[10:00 - 25:00]** Bölüm 2: Derin Mimari, Yapay Zeka ve RAG Sistemi (15 Dk)
- **[25:00 - 35:00]** Bölüm 3: Canlı Demo (Live Showcase) (10 Dk)
- **[35:00 - 45:00]** Bölüm 4: Soru - Cevap (Q&A) (10 Dk)

---

## 🎤 Bölüm 1: Vizyon, Problem Tanımı ve Değer Önerisi (10 Dk)

**Temel Mesaj:** *Osmanlı arşivlerinde yatan milyonlarca sayfalık miras, dil bariyeri ve eski yazı (matbu/rika vb.) nedeniyle araştırmacılara kapalı. Bu proje, tarihi dijitalleştiren otonom bir fabrikadır.*

- **Problem:** Mevcut OCR sistemlerinin Osmanlıcaya uygun olmaması; çevirilerin bağlamdan kopuk (halüsinasyonlu) olması.
- **Çözümümüz:**
  - Görsel iyileştirme (Pre-processing) + Kraken OCR kombinasyonu.
  - LLM'lerin (Ollama) metin çevirisinde "Strict JSON Formatting" (Sıkı Format) ile sınırlandırılması.
  - Varlıkların (Kişi, Yer, Tarih) RAG (Qdrant) ile doğrulanması.
- **Vurgulanacak Yetkinlik:** *Sadece bir web sitesi değil, arka planda asenkron çalışan (worker.py) ölçeklenebilir bir mikroservis yapısı kurduğunuzu hissettirin.*

---

## 🧠 Bölüm 2: Derin Mimari ve Yapay Zeka (15 Dk)

**Temel Mesaj:** *Sistem hem kod kalitesi (Clean Code) hem de donanım optimizasyonu (Local LLM, Concurrency) açısından Enterprise (Kurumsal) standartlardadır.*

1. **Frontend Mimarisi (Next.js & React 19):**
   - Jürinin dikkatini UI'a çekin. UI'ın donmamasını sağlayan **Custom Hooks (`useDocumentAnalysis.ts` vs)** mantığından bahsedin. "Spagetti koddan kaçınmak için mantık ile UI'ı birbirinden kopardık" deyin.
2. **Backend & Concurrency (FastAPI & SQLite WAL):**
   - "Database is locked" hatalarını önlemek için SQLite'ı nasıl WAL (Write-Ahead Logging) modunda yapılandırdığınızı anlatın. Worker'ların nasıl kalpten (heartbeat) API ile senkronize olduğunu vurgulayın.
3. **AI Pipeline & RAG Guardrails (En Önemli Kısım):**
   - Prompt Engineering yaklaşımınızı gösterin: *LLM'e sadece "çevir" demiyoruz. "Kesinlikle kaynak metin dışına çıkma, tarihsel uydurma yapma" şeklinde kısıtlayıcı Prompt ve Pydantic benzeri output parser'lar (JSON şemaları) ile çalışıyoruz.*
   - Qdrant Vector DB entegrasyonuyla skor eşiklerinin (threshold) nasıl filtrelendiğini ve BM25 + Domain Boost algoritmalarını açıklayın.

---

## 💻 Bölüm 3: Canlı Demo (Live Showcase) (10 Dk)

**Temel Mesaj:** *Kurduğumuz sistem teoride değil, pratikte de anlık ve hatasız çalışıyor.*

1. **Start-up:** `docker-compose up -d --build` komutunu gösterin. Sistemin Docker üzerinden nasıl izole ve hızlı kalktığını belirtin. (Multi-stage build ile imaj boyutlarını nasıl kıstığınıza değinin).
2. **İşlem Aşaması:** Dashboard ekranını açın. Bir dosya yükleyip analiz sürecindeki (Worker'ın arka planda işlediği) "Loading/Processing" akıcılığını (state management) jüriye izletin.
3. **Büyük Final (PDF Export):** Analiz bitince **"PDF İndir"** butonuna basın. İnen raporu açın. 
   - **Vurgu Noktası:** *Burada jüriye dönüp, "PDF üzerinde Osmanlıca metnin (Arap alfabesinin) soldan sağa ters çıkmasını veya harflerin kopuk olmasını engellemek için arka planda ReportLab, arabic-reshaper ve python-bidi (RTL) kullandık" diyerek ufak detaylara (Edge Cases) ne kadar hakim olduğunuzu gösterin.*

---

## ❓ Bölüm 4: Beklenen Soru - Cevap (Q&A) Hazırlığı (10 Dk)

Jüriden gelebilecek muhtemel zorlayıcı sorular ve "kurtarıcı" yanıtlarınız:

- **Soru 1:** *Neden cloud bir LLM (Örn: OpenAI) yerine Local LLM (Ollama) tercih ettin?*
  - **Cevap:** Gizlilik (tarihi arşiv verileri dışarı çıkmamalı), maliyet optimizasyonu ve otonomi için.
- **Soru 2:** *Frontend'de neden bu kadar fazla Custom Hook yazdın?*
  - **Cevap:** Separation of Concerns (Sorumlulukların Ayrılığı) prensibi için. `DashboardPage.tsx` içerisinde state'ler şiştiğinde React Hooks Kurallarını (Rules of Hooks) ihlal ediyordu. Mimaride UI'ı sadece render alanına indirgeyerek performansı (re-render) optimize ettim.
- **Soru 3:** *İleride sistemi büyütmek istesek SQLite yetersiz kalmaz mı?*
  - **Cevap:** Kesinlikle. Ancak FastAPI ve SQLAlchemy ORM kullandığım için, PostgreSQL'e geçiş yapmak sadece ortam değişkenindeki (`DATABASE_URL`) tek bir satırı değiştirmek kadar kolay. Mimari tamamen decoupled (bağımsız) tasarlandı.

---
> **Sunum Öncesi Altın Tavsiye:** Teknik derinliği anlatırken, karşı tarafın kodunuzu değil, *problem çözme vizyonunuzu* satın aldığını unutmayın. Hata çıktığında paniklemek yerine, yazdığınız "Fallback (Geri Dönüş)" senaryolarından (LLM çökerse kural tabanlı algoritmaların nasıl devreye girdiğinden) bahsederek durumu bir avantaja çevirin. Başarılar!
