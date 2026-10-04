---
type: module
status: verified
last_verified: 2026-08-09
owners:
  - Codex
source_paths:
  - frontend/src/components/auth/AuthShell.tsx
  - frontend/src/app/login/page.tsx
  - frontend/src/app/register/page.tsx
  - frontend/src/app/globals.css
  - frontend/src/lib/api.ts
test_paths:
  - frontend/package.json
  - evidence/auth_ui_implementation/lint_result.txt
  - evidence/auth_ui_implementation/build_result.txt
  - evidence/auth_ui_implementation/route_status.json
tags: [ui, auth, login, register, premium-dark]
---

# Auth UI

**Özet:** Login ve register ekranları premium koyu tema, altın vurgu ve Osmanlıca belge analizi görsel diliyle uygulanmıştır. Ekranlar gerçek `authApi` entegrasyonunu kullanır ve `/login` ile `/register` route'larında çalışır.

**Kütüphaneler:** Next.js, React, TypeScript, Tailwind CSS global styles.

**Bağlantılar:** [[Document_Workspace]], [[Security_Model]], [[FastAPI_API]], [[Index]]

## Sorumluluklar
- Kullanıcı giriş ve kayıt formlarını göstermek.
- Loading, disabled, error ve success durumlarını yönetmek.
- Auth token saklama davranışını remember-me seçimine göre uygulamak.
- Ürün kimliğini premium dark/gold tasarım sistemiyle sunmak.

## Girdiler
- Login: e-posta, şifre, beni hatırla.
- Register: ad soyad, e-posta, şifre, şifre tekrar, kurum/üniversite, koşul onayı.

## Çıktılar
- Başarılı auth sonrası `/dashboard` yönlendirmesi.
- Başarısız auth için kullanıcı dostu hata mesajı.

## Bağımlılıklar
- `frontend/src/lib/api.ts` → `authApi.login`, `authApi.register`, `setToken`.
- Backend auth endpoints: `/api/v1/auth/login`, `/api/v1/auth/register`.

## Veri Akışı
1. Kullanıcı formu doldurur.
2. Client form validasyonunu çalıştırır.
3. `authApi` backend'e istek gönderir.
4. Token `localStorage` veya `sessionStorage` içine yazılır.
5. Kullanıcı dashboard'a yönlendirilir.

## Hata Durumları
- Eksik alan.
- Şifrelerin eşleşmemesi.
- Kullanım koşullarının kabul edilmemesi.
- Backend 401/409/422 hataları.
- Backend bağlantı hatası.

## Güvenlik ve Gizlilik
- Token remember-me kapalıyken session storage içinde tutulur.
- Evidence dosyalarına token veya parola kaydedilmedi.

## Testler ve Kabul Kriterleri
- `npm.cmd run lint` PASS.
- `npm.cmd run build` PASS.
- `/login` HTTP 200.
- `/register` HTTP 200.
- Playwright screenshot kanıtı üretildi.

## Kod Kanıtları
- `frontend/src/components/auth/AuthShell.tsx` → `AuthShell`
- `frontend/src/app/login/page.tsx` → `LoginPage`
- `frontend/src/app/register/page.tsx` → `RegisterPage`
- `frontend/src/lib/api.ts` → `setToken`, `getToken`, `removeToken`
- `frontend/src/app/globals.css` → `.auth-page`, `.auth-card`, `.auth-visual-card`

## Bilinen Eksikler
- Sosyal giriş butonları görsel olarak hazır, provider entegrasyonu yok.

## Değişiklik Geçmişi
- 2026-08-09: Premium login/register UI uygulandı ve lint/build/route/screenshot kanıtları üretildi.
