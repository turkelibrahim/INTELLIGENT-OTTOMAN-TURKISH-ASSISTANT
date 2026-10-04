---
type: decision
status: proposed
last_verified: 2026-07-28
owners: []
source_paths:
  - frontend/package.json
  - frontend/src/app
  - docs/wiki/05_UI/Streamlit_UI.md
tags: [adr, frontend, nextjs, streamlit]
---

# ADR-001 - Next.js Frontend

**Durum:** proposed

**Ozet:** Mevcut calisan frontend Next.js App Router tabanlidir; kodbase icinde Streamlit uygulamasi bulunamadi. Streamlit teknoloji adi tek basina fonksiyonel UI gereksinimi sayilmamalidir; gerekli kullanici davranislari Next.js ile karsilanabiliyorsa teknoloji degisikligi karar olarak kaydedilmelidir.

**Kutuphaneler:** Next.js, React, TypeScript.

**Baglantilar:** [[Document_Workspace]], [[Streamlit_UI]], [[Architecture_Map]], [[Decisions]]

## Baglam
- `frontend/package.json` Next.js/React uygulamasini dogrular.
- `frontend/src/app` login, dashboard, upload ve belge detay ekranlarini icerir.
- `docs/wiki/05_UI/Streamlit_UI.md` Streamlit kodu bulunmadigini kaydeder.

## Degerlendirilen Secenekler
- Streamlit UI eklemek.
- Mevcut Next.js UI ile fonksiyonel gereksinimleri tamamlamak.
- Iki UI teknolojisini birlikte surdurmek.

## Karar
Proposed: MVP icin mevcut Next.js UI surdurulsun; Streamlit yalniz SRS tarafindan kesin teknoloji zorunlulugu olarak onaylanirsa yeniden degerlendirilsin.

## Gerekce
- Mevcut kod ve build kaniti Next.js tarafindadir.
- Streamlit kodu yoktur.
- Fonksiyonel gereksinimler teknoloji adindan ayrilmalidir.

## Sonuclar
- UI gereksinimleri `Document_Workspace` uzerinden izlenecek.
- Streamlit yoklugu otomatik fonksiyonel eksik sayilmayacak.
- Kullanici veya SRS acik teknoloji zorunlulugu isterse karar tekrar acilacak.

## Riskler
- SRS Streamlit'i teslim zorunlulugu olarak yaziyorsa bu ADR kabul edilmeden yeterli olmaz.
- Next.js API URL ve font/lint uyarilari ayri gorevlerle ele alinmalidir.

## Geri Donus Kosullari
- SRS tam metni Streamlit'i MUST teslim teknolojisi olarak dogrularsa.
- Kullanici akademik teslim icin Streamlit'i zorunlu kilar.

## Kanitlar
- `frontend/package.json` -> Next.js dependency ve scripts.
- `frontend/src/app/**` -> Next.js ekranlari.
- `evidence/recover_baseline/frontend_build.txt` -> build PASS.
