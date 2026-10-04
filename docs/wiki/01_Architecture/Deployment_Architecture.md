---
type: module
status: partial
last_verified: 2026-07-28
owners: []
source_paths:
  - frontend/package.json
  - backend/requirements.txt
  - backend/app/main.py
tags: [deployment, ops]
---

# Deployment Architecture

**Ozet:** Yerel gelistirme mimarisi FastAPI backend ve Next.js frontend olarak belgelenmistir. Production hosting, process manager, reverse proxy, secret management ve database stratejisi DOĞRULANMADI. Riskler [[Risks]] ve gorevler [[Task_Queue]] icindedir.

**Kutuphaneler:** uvicorn, Next.js, npm, SQLite.

**Baglantilar:** [[Architecture_Map]], [[FastAPI_API]], [[Document_Workspace]]

## Sorumluluklar
- Calistirma, ortam degiskenleri, CORS, API URL ve veri depolama kararlarini tasimak.

## Girdiler
- `backend/requirements.txt`, `frontend/package.json`, `.env`.

## Ciktilar
- Yerel servisler; production DOĞRULANMADI.

## Bagimliliklar
- Python venv, Node/npm, SQLite, Poppler gereksinimi.

## Veri Akisi
- Frontend sabit API URL ile backend'e gider.

## Hata Durumlari
- Sabit `127.0.0.1` API URL network cihazlarda hata uretebilir.

## Guvenlik ve Gizlilik
- `.env` icinde hassas anahtar riski var.

## Testler ve Kabul Kriterleri
- Henuz deployment testi yok.

## Kod Kanitlari
- `frontend/package.json` -> `dev`, `build`, `start`, `lint`
- `backend/app/main.py` -> CORS, `/uploads`

## Bilinen Eksikler
- Production deployment tanimi yok.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
