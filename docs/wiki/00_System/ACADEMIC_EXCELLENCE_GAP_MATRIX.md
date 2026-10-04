---
type: matrix
status: planned
last_verified: 2026-08-02
owners: []
source_paths: []
tags: [academic, gap-matrix, planning]
---

# Academic Excellence Gap Matrix

## 1. OCR Düzeltme Stüdyosu
- **MEVCUT**: Basit OCR sonuç ekranı (metin/NER görünümü) mevcut. Yalnızca satır seviyesinde metin güncellemesi ve audit log var (TASK-018). RTL testleri (TASK-016) backend'de var.
- **EKSİK**: Görsel/metin senkronizasyonu, düşük güvenli bölgelerin renk/ikon gösterimi, CER/WER hesaplaması (önce/sonra), sürüm geçmişli geri alma, karakter/kelime seçimi, UI üzerinden RTL okuma sırası ve sütun düzeltmesi.
- **UYGULANACAK**:
  - Gelişmiş OCR editör bileşeni (bounding box çizimi, görsel senkronizasyonu).
  - Güven skoruna göre renk kodlaması.
  - Revizyon geçmişi ve CER/WER hesaplama motorunun UI ile entegrasyonu.
- **TEST**: React Testing Library ile görsel editör testleri, backend'de CER/WER delta doğrulama testleri.
- **KANIT**: E2E test ile bir metnin düzeltilmesi, revizyon logu ve CER/WER değişim raporu.

## 2. Özgün Değerlendirme Veri Seti
- **MEVCUT**: Temel mock ve basit resim/PDF'ler kullanılıyor. Açık bir "Ground Truth" veri seti paketi yok.
- **EKSİK**: Gerçek Osmanlıca sayfalardan ground truth veri seti. ALTO/PageXML uyumu. Train/val/test ayrımı, veri kartı, lisans beyanı.
- **UYGULANACAK**:
  - `data/ground_truth/` klasörünün oluşturulması.
  - PageXML/ALTO formatında dışa/içe aktarma fonksiyonları.
  - Veri setine SHA-256 manifesti ve veri kartı oluşturulması.
- **TEST**: Veri setinin yapısal bütünlük testleri, format ayrıştırma testleri.
- **KANIT**: SHA-256 hash raporu, Veri Kartı belgesi (Data Card).

## 3. OCR Deney ve Hata Analizi
- **MEVCUT**: EasyOCR CPU (TASK-034) üzerinden sadece temel metin çıkarımı yapılıyor. Görüntü ön işleme (TASK-015) var ama pipeline karşılaştırması yapılmadı.
- **EKSİK**: CLAHE, Deskew, Gürültü azaltma ve Binarizasyon ile baseline karşılaştırma testleri. Hata analiz raporu (en az 5 gerçek başarısız örnek analizi).
- **UYGULANACAK**:
  - Farklı pipeline konfigürasyonlarını (ön işlemesiz, CLAHE'li, vb.) çalıştıracak `experiment_runner.py` scripti.
  - Sonuçları tablo ve grafik (matplotlib/seaborn) ile raporlama.
- **TEST**: Deney scriptinin deterministik çalışması, rapor üretme doğrulama testleri.
- **KANIT**: Çıktı olarak alınacak PDF/Markdown CER/WER performans grafikleri ve log raporları.

## 4. Transliterasyon ve Modern Türkçe
- **MEVCUT**: Kural tabanlı transliterasyon API (TASK-019), sadık/sadeleştirilmiş/özet modları (TASK-020). Helsinki-NLP kullanımına dair bir engel belirtildi ama mevcut durum kodda RAG veya mock şeklinde olabilir.
- **EKSİK**: Kelime/satır hizalaması, alternatif güven seviyesi, özel testler (özel ad, sayı, tarih, noktalama), gerçek LLM modeli/lisans ve sürüm checksum'u, uzman doğruluk metriği (Rubrik).
- **UYGULANACAK**:
  - Kelime ve satır hizalama logiğinin eklenmesi.
  - Belirsiz okumalar için confidence/alternatives API yapısı.
  - ModelChecksum ve Lisans kayıt sisteminin entegre edilmesi.
- **TEST**: Özel ad, rakam ve tarih koruma testleri.
- **KANIT**: Alignment (Hizalama) doğrulama test raporları ve Model Lisans Kaydı.

## 5. Güvenilir Özet, NER ve RAG
- **MEVCUT**: NER placeholder/kural tabanlı, RAG için FAISS entegre edildi (TASK-021, TASK-023). Indexing çalışıyor, prompt injection koruması var.
- **EKSİK**: Özet cümlelerinin spesifik kaynak satırlara bağlanması, hallucination (hayalî bilgi) önleme testleri (belgede yoksa cevap üretmeme), NER mikro F1 raporu.
- **UYGULANACAK**:
  - RAG promptlarının strict "kaynak göster" yapısına geçirilmesi.
  - NER için değerlendirme scriptinin (F1-score) gerçek veri setinde çalıştırılması.
- **TEST**: Hallucination testleri (kasıtlı olarak yanlış bilgi sorarak reddedilmesini sağlama). İki kullanıcıyla FAISS izolasyonunun reverifikasyonu.
- **KANIT**: RAG citation (alıntı) kanıt raporu, NER Micro-F1 raporu, izolasyon logu.

## 6. Son Kullanıcı Deneyimi
- **MEVCUT**: NextJS (TASK-031) temel ekranlar yapıldı. Token tabanlı görsel gösterme (UI-FIX-20260802) halledildi.
- **EKSİK**: Tam kapsamlı gerçek RTL/Bidi davranışları (özellikle karma Osmanlıca ve Latin/Modern Türkçe yan yana gelince). Kapsamlı UI hata (empty, loading, low confidence) durumları, erişilebilirlik.
- **UYGULANACAK**:
  - CSS RTL yapılandırmaları (`dir="rtl"` ve `dir="ltr"` alanlarının izolasyonu).
  - Skeleton loading, empty states tasarım bileşenleri eklentisi.
  - Klavye erişilebilirliği (Focus outline).
- **TEST**: a11y (erişilebilirlik) testleri, RTL layout testleri (Cypress/Playwright).
- **KANIT**: UI test geçiş kanıtları, Lighthouse/a11y raporu.

## 7. Akademik Teslim Paketi
- **MEVCUT**: Temel wiki yapılandırması ve dokümantasyonlar mevcut.
- **EKSİK**: Akademik yayın standartlarında yayın/sunum paketi, veri kartları, jüri soruları, makale formatında metodoloji ve sonuçlar.
- **UYGULANACAK**:
  - `docs/academic/` veya `docs/wiki/12_Operations/Academic/` dizini oluşturulması.
  - İlgili tüm rapor, rubrik, metrik, veri kartı ve sunum senaryolarının Markdown/PDF olarak yazılması.
- **TEST**: Tüm belgelerin mevcut sistem kodlarıyla tutarlı olduğunun (`LINT`) teyit edilmesi.
- **KANIT**: Hazırlanacak `ACADEMIC_PACKAGE_INDEX.md` ve tüm belgelerin derlenmiş hali.
