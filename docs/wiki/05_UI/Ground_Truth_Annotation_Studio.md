---
type: module
status: verified
last_verified: 2026-08-02
owners: [Antigravity]
source_paths: [frontend/src/app/dashboard/annotation-studio/page.tsx, backend/app/api/routes/ground_truth.py]
test_paths: []
tags: [ui, ground-truth, ocr-evaluation]
---

# Ground Truth Annotation Studio

**Özet:** Osmanlıca belgeler için model kalitesini ölçmek amacıyla, insanın gözden geçirdiği kesin doğru transkripsiyonların (Ground Truth) veri tabanına işlenmesini ve kilitlenmesini sağlayan arayüz.

**Kütüphaneler:** React, Next.js, FastAPI, SQLAlchemy.

**Bağlantılar:** [[OCR_Evaluation_Methodology]], [[Index]]

## Sorumluluklar
- Osmanlıca sayfa görüntülerinin yüklenmesi ve gösterilmesi.
- Satır bazlı poligonal veya dikdörtgen (bounding box) alan seçimleri.
- RTL (Sağdan Sola) okuma sırasına göre transkripsiyon girişi.
- OCR modelleriyle tarafsız kıyaslama yapabilmek için Ground Truth metinlerinin OCR çıktısı görülmeden girilmesini sağlama (yanlılığı engelleme).

## Girdiler
- `Dataset`: Koleksiyon tanımı.
- `GroundTruthPage`: Belge ve sayfa bilgisi, görsel hash'i.
- `GroundTruthLine`: Satır koordinatları ve insan tarafından girilen RTL metin.

## Çıktılar
- `LOCKED` (Kilitli) statüsündeki satırlar, `metrics.py` (Jiwer) tarafından OCR tahmini ile karşılaştırılarak katı (strict) ve normalize (normalized) CER/WER skorları üretir.

## Bağımlılıklar
- `app.models.ground_truth` (SQLAlchemy modelleri).
- `app.api.routes.ground_truth` (FastAPI Endpoints).

## Veri Akışı
1. Kullanıcı görüntüyü görür, satırları böler, Osmanlıca (Arapça) metni bağımsız yazar.
2. Satırlar `DRAFT` olarak veritabanına kaydedilir.
3. Review sonrasında kullanıcı satırları `LOCKED` durumuna getirir.
4. Yalnızca `LOCKED` satırlar final OCR Engine (EasyOCR) testine sokulur.

## Hata Durumları
- Kilitli sayfalara izinsiz/yetkisiz ekleme yapılamaz. API katmanında reddedilir.
- Eksik veya hatalı bounding box koordinatları kabul edilmez.

## Güvenlik ve Gizlilik
- Kullanıcı izole çalışır (kendi eklediği dataset'lere müdahale edebilir).
- Kilitlenmiş ground truth'lar veri seti sürümü değiştirilmedikçe düzenlenemez.

## Testler ve Kabul Kriterleri
- Kilitli verinin yeni sürüm açılmadan değiştirilememesi API tarafından doğrulanır.

## Kod Kanıtları
- `frontend/src/app/dashboard/annotation-studio/page.tsx`
- `backend/app/api/routes/ground_truth.py`

## Bilinen Eksikler
- Yok.

## Değişiklik Geçmişi
- 2026-08-02: Studio arayüzü ve API eklendi.

## TASK-034-Q3 Human Review Gate
- 2026-08-02: API-backed insan review workflow, audit trail, dataset-level ready/lock ve `pilot_ocr_evaluation` worker auto-trigger entegre edildi.
- Pilot draft bos dataset durumunda kullanici hesabina otomatik hazirlanir; kaynak 3 sayfa/73 satirdir.
- Reviewer kimligi backend authentication baglamindan gelir; kullanici payload'i ile sahte reviewer reddedilir.
- Tum 73 satir text+bbox review edilmeden dataset lock olmaz; durum `WAITING_FOR_HUMAN_CONTENT_REVIEW`.
- Kanitlar: `evidence/human_review_gate/FINAL_HUMAN_REVIEW_GATE_REPORT.md`, `review_api_tests.txt`, `frontend_build.txt`, `live_smoke.txt`.
