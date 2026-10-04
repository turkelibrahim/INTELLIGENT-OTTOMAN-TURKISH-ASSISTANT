---
type: questions
status: verified
last_verified: 2026-07-28
owners: []
source_paths: []
tags: [questions, bootstrap]
---

# Open Questions

**Ozet:** Bu sayfa BOOTSTRAP sirasinda kanitlanamayan veya kullanici karari gerektiren konulari tutar. Kodda bulunmayan ozellikler uygulanmis kabul edilmez. Cevaplanan maddeler [[Decisions]] veya ilgili modul sayfasina tasinmalidir.

**Kutuphaneler:** Yok.

**Baglantilar:** [[Current_State]], [[Task_Queue]], [[Risks]]

## Karar Gerektirenler
- Git Windows PATH'e eklenecek mi, yoksa repo durumu baska aracla mi dogrulanacak?
- `.env` icindeki LLM API anahtari rotate edilecek mi ve gizli yonetim stratejisi ne olacak?
- Frontend API base URL ortam degiskenine alinacak mi?
- Production CORS politikasi hangi originlerle sinirlanacak?
- SQLite kalici hedef mi, yoksa PostgreSQL gecisi planlaniyor mu?
- Eski/yanlis hafiza klasorleri (`OBSIDIAN_MIMARI_BEYIN_PAKETI/`, `osmanlıca/`) ne zaman arsivlenecek veya temizlenecek?

## Teknik Belirsizlikler
- SRS PDF icerigi bu oturumda parse edilmedi; SRS gereksinimleri DOCUMENTED olarak bile tam haritalanmis degil.
- Poppler kurulu mu? PDF sayfalama gercek PDF ile dogrulanmadi.
- OCR icin gercek Ottoman fine-tuned model var mi? Mevcut `microsoft/trocr-base-printed` genel modeldir.
- RAG chat servisi hangi vektor store ve LLM saglayici ile tamamlanacak?
- ProcessingJob modeli arka plan kuyrugu ile mi, senkron route akislariyla mi kullanilacak?
- Kullanici rolleri `expert/admin` UI veya admin API ile yonetilecek mi?
- Pytest backend venv'e eklenecek mi ve ilk integration test kapsami auth/upload/preprocessing olarak mi baslayacak?
- TASK-008 icin SRS text extraction tamamlandi; `pypdf` backend venv'e kuruldu. Bu dependency requirements'a eklenecek mi, yoksa yalniz evidence tooling olarak mi kalacak?
- Next.js frontend ADR-001 kabul edilecek mi, yoksa SRS Streamlit'i teknoloji zorunlulugu olarak mi dayatiyor?
