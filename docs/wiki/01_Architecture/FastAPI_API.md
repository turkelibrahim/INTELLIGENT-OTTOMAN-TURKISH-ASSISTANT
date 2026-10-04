---
type: module
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/main.py
  - backend/app/api/router.py
test_paths:
  - backend/test_import.py
tags: [backend, api]
---

# FastAPI API

**Ozet:** Backend FastAPI uygulamasi auth, document, page ve preprocessing routerlarini yayinlar. `/health` ve `/` endpointleri `backend/app/main.py` icinde tanimlidir. Ayrintili kanitlar [[Source_Map]] icindedir.

**Kutuphaneler:** FastAPI, CORSMiddleware, StaticFiles, uvicorn.

**Baglantilar:** [[Architecture_Map]], [[Security_Model]], [[Document_Ingestion]], [[Image_Preprocessing]]

## Sorumluluklar
- API uygulamasini kurmak, CORS eklemek, upload dosyalarini static sunmak, routerlari baglamak.

## Girdiler
- HTTP istekleri ve `settings`.

## Ciktilar
- JSON API yanitlari ve static upload dosyalari.

## Bagimliliklar
- `app.core.config.settings`, `app.db.database.init_db`, `app.api.router.api_router`.

## Veri Akisi
- Frontend [[Document_Workspace]] -> `frontend/src/lib/api.ts` -> FastAPI route -> servis/model katmani.

## Hata Durumlari
- CORS tum originlere acik; production riski [[Risks]] icinde.

## Guvenlik ve Gizlilik
- Route bazinda `get_current_user` dependency kullanilir; ana uygulamada CORS gevsek.

## Testler ve Kabul Kriterleri
- `backend/test_import.py` import smoke dosyasi var; kapsamli test yok.

## Kod Kanitlari
- `backend/app/main.py` -> `app`, `lifespan`, `health_check`
- `backend/app/api/router.py` -> `api_router.include_router`

## Bilinen Eksikler
- Production CORS ve deployment ayarlari DOĞRULANMADI.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
