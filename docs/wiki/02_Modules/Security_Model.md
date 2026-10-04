---
type: module
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - backend/app/core/security.py
  - backend/app/api/routes/auth.py
  - backend/app/models/user.py
  - frontend/src/lib/api.ts
test_paths:
  - backend/tests/test_auth_security.py
tags: [security, auth]
---

# Security Model

**Ozet:** Sistem JWT tabanli auth, bcrypt/passlib parola hashleme ve route-level current_user dependency kullanir. TASK-011 ile register/login/me/logout, gecersiz token, belge IDOR ve kullaniciya gore belge liste izolasyonu testlendi. Frontend token'i localStorage'da saklar. Secret ve CORS riskleri [[Risks]] icindedir.

**Kutuphaneler:** python-jose, passlib, bcrypt, FastAPI OAuth2PasswordBearer.

**Baglantilar:** [[FastAPI_API]], [[Document_Workspace]], [[Risks]]

## Sorumluluklar
- Kullanici kaydi/girisi, token uretimi, token dogrulama, rol kontrolleri.

## Girdiler
- Email/parola, JWT bearer token.

## Ciktilar
- Access token, `UserResponse`, current_user.

## Bagimliliklar
- `settings.SECRET_KEY`, `User`, DB session.

## Veri Akisi
- Login/register -> token -> frontend localStorage -> Authorization header.

## Hata Durumlari
- Gecersiz token 401; inactive kullanici 403.

## Guvenlik ve Gizlilik
- `.env` secret riski var; localStorage XSS'e duyarlidir.

## Testler ve Kabul Kriterleri
- `backend/tests/test_auth_security.py` auth flow, generic login error, expired/missing token, belge IDOR ve belge liste scoping testlerini icerir.
- Kanit: `evidence/environment_gate/backend_pytest_task011_full.txt` -> 14 passed.

## Kod Kanitlari
- `backend/app/core/security.py` -> `create_access_token`, `get_current_user`
- `backend/app/api/routes/auth.py` -> `register`, `login`
- `backend/app/api/routes/documents.py` -> `_get_user_document` sahip/admin izolasyonu.

## Bilinen Eksikler
- Refresh token, revoke list ve rate limit yok.
- Production CORS ve secret rotasyonu TASK-026 kapsaminda kalir.

## Degisiklik Gecmisi
- 2026-07-28: BOOTSTRAP sirasinda olusturuldu.
- 2026-07-28: TASK-011 sirasinda auth ve belge izolasyonu test kanitlari eklendi.
