---
type: risk_register
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/.env
  - backend/app/services/document_processing/pipeline.py
  - backend/app/main.py
  - frontend/src/lib/api.ts
tags: [risks, security, quality]
---

# Risks

**Ozet:** En kritik risk `.env` icinde hassas API anahtari bulunmasidir; deger kaydedilmemistir. Ikinci ana risk, AI/ML pipeline iddialari ile entegre API/UI arasinda bosluk olmasidir. TASK-009/TASK-010 ile pytest, doctor ve DB migration gate PASS oldu; pipeline ve security riskleri devam eder.

**Kutuphaneler:** FastAPI, Next.js, passlib, bcrypt, pdf2image, transformers.

**Baglantilar:** [[Current_State]], [[Task_Queue]], [[Open_Questions]], [[Security_Model]]

## P0
- `.env` icinde hassas LLM API anahtari bulundu. Deger wikiye kopyalanmadi. Kanit: `backend/.env` -> `LLM_API_KEY` satiri var. Aksiyon: anahtari rotate et, `.env.example` olustur, gizli bilgiyi repo disi yonet.
- AI/ML pipeline runtime smoke BROKEN. Kanit: `evidence/recover_baseline/backend_pipeline_smoke_utf8.txt` -> `AttributeError: 'ImagePreprocessor' object has no attribute 'process'`.
- SRS metni artik cikarildi; ancak 115 MUST gereksinimden 0'i release seviyesinde VERIFIED. Kanit: `evidence/requirements_traceability/matrix_summary_autonomous.txt`.

## P1
- Test kapsami halen dar; pytest artik kurulu ve backend smoke/migration testleri PASS. Auth, upload, AI pipeline ve e2e testleri eksik.
- Yeni TASK-010 tablolarinin runtime route/service entegrasyonu henuz yok; migration/model kapisi PASS olsa da OCR/text/entity/chat/citation/export akislari sonraki gorevlere bagli.
- TASK-011 sonrasinda npm high audit bulgulari override ile giderildi; lockfile PASS. Bu override'lar frontend dependency upgrade'lerinde yeniden dogrulanmali.
- Upload route integration, PDF fixture, thumbnail ve preprocessing endpoint testleri henuz eksik; TASK-012 kapsamina tasindi.
- `backend/app/main.py` CORS ayarini `allow_origins=["*"]` ile aciyor; `settings.CORS_ORIGINS` tanimli ama kullanilmiyor. Bu production icin risklidir.
- `frontend/src/lib/api.ts` API adresini `http://127.0.0.1:8000/api/v1` olarak sabitliyor; network IP veya deployment ortaminda baglanti hatasi uretebilir.
- `DocumentProcessingPipeline.process_document` `ImagePreprocessor.process` cagiriyor; `ImagePreprocessor` icinde bu sembol yok. Kanit: `pipeline.py` ve `preprocessor.py`.
- TrOCR tokenizer yuklemesi `sentencepiece or tiktoken` bagimliligi istiyor; OCR engine fallback'a dusuyor. Kanit: `evidence/recover_baseline/backend_pipeline_smoke_utf8.txt`.
- Test kapsami yok veya bulunamadi; sadece `backend/test_import.py` smoke import dosyasi var. `pytest` kurulu degil. Kanit: `evidence/recover_baseline/backend_pytest.txt`.
- Git durumu alinamadi; `git` PATH uzerinde yok. Kanit: `evidence/recover_baseline/git_status.txt`.
- Image preprocessing tek basina VERIFIED degildir; endpoint test yok ve pipeline uyumsuzlugu var. Kanit: [[Image_Preprocessing]].
- WSL komutlari TASK-009 sirasinda timeout verdi; Windows-native dev gate PASS, WSL/Kraken uyumlulugu TASK-017 icin release blocker olarak kalir. Kanit: `evidence/environment_gate/wsl_status.txt`, [[ADR-002_Windows_Native_Dev_Gate]].

## P2
- Root altinda eski/yanlis hafiza kopyalari halen duruyor: `OBSIDIAN_MIMARI_BEYIN_PAKETI/`, `osmanlıca/`. Baglayici kaynak degil, silinmedi.
- OCR/Translator/NER kodlari mock/placeholder sonuclar dondurebiliyor; uygulanmis AI sonucu gibi sunulmamali.
- PDF sayfalama `pdf2image` ve Poppler'a bagli; Poppler kurulumu DOĞRULANMADI.
- UI ve kod yorumlarinda karakter encoding bozulmalari var; Turkce metin kalitesi ve kullanici guveni etkilenir.
- `backend/ottoman_assistant.db` ve `backend/uploads` proje icinde bulunuyor; kullanici verisi ve dosya artefaktlarinin versiyonlama/backup politikasi DOĞRULANMADI.
