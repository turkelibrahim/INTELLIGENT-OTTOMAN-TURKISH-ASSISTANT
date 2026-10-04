---
type: module
status: documented
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/models/processing_job.py
tags: [jobs, processing]
---

# Processing Job State Machine

**Ozet:** `ProcessingJob` modeli pending/running/completed/failed/cancelled durumlarini ve job_type alanini tanimlar. Route veya servis akislarinda aktif kullanimi BOOTSTRAP sirasinda bulunamadi. Bu nedenle documented olarak isaretlidir.

**Kutuphaneler:** SQLAlchemy.

**Baglantilar:** [[Database_Model]], [[Image_Preprocessing]], [[OCR_Service]]

## Sorumluluklar
- Islem gorevlerinin durum, model, parametre, sonuc ve sure bilgilerini tutmak.

## Girdiler
- document_id, page_id, user_id, job_type.

## Ciktilar
- `processing_jobs` DB satiri.

## Bagimliliklar
- Document/Page/User foreign keyleri.

## Veri Akisi
- DOĞRULANMADI; mevcut route entegrasyonu bulunamadi.

## Hata Durumlari
- Model var ama state transition guard yok.

## Guvenlik ve Gizlilik
- Kullanici ve belge referansi tutar.

## Testler ve Kabul Kriterleri
- Test bulunamadi.

## Kod Kanitlari
- `backend/app/models/processing_job.py` -> `ProcessingJob`

## Bilinen Eksikler
- Queue/worker/route entegrasyonu yok.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
