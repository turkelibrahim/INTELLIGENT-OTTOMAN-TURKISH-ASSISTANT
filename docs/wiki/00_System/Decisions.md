---
type: decisions
status: verified
last_verified: 2026-07-28
owners: []
source_paths:
  - AGENTS.md
  - PROMPTS/01_RECOVER_BASELINE.md
tags: [decisions, recover, baseline]
---

# Decisions

**Ozet:** Kok `AGENTS.md` tek baglayici anayasa, `PROMPTS/` tek prompt koku, `docs/wiki/` tek wiki koku olarak kullanilir. TASK-009 icin Windows-native gate ADR kabul edildi; TASK-010 icin Alembic initial migration MVP migration stratejisi kabul edildi.

**Kutuphaneler:** Yok.

**Baglantilar:** [[Index]], [[Current_State]], [[Risks]]

## Kayitli Kararlar
- 2026-07-28: Kullanici talimati nedeniyle ilk islem sadece BOOTSTRAP, INGEST ve HANDOFF kapsaminda tutuldu.
- 2026-07-28: Kaynak kod, konfig, bagimlilik, veritabani ve kullanici verisi degistirilmedi.
- 2026-07-28: Hassas `.env` degeri wikiye veya rapora kopyalanmadi.
- 2026-07-28: RECOVER sirasinda tek baglayici anayasa olarak kok `AGENTS.md` dogrulandi.
- 2026-07-28: Tek prompt koku olarak `PROMPTS/`, tek wiki koku olarak `docs/wiki/` dogrulandi.
- 2026-07-28: Eski kopyalar `frontend/AGENTS.md`, `OBSIDIAN_MIMARI_BEYIN_PAKETI/AGENTS.md`, `OBSIDIAN_MIMARI_BEYIN_PAKETI/docs/wiki/` ve diger eski hafiza klasorleri baglayici kaynak olarak kullanilmadi ve silinmedi.
- 2026-07-28: BASELINE-001 sonrasi gelistirme promptuna gecilmeden once `PROMPTS/02_REQUIREMENTS_TRACEABILITY.md` calistirilacak.
- 2026-07-28: TASK-008 sirasinda SRS PDF tam metni cikarilamadigi icin gelistirme promptlarina gecilmeyecek.
- 2026-07-28: Next.js frontend icin [[ADR-001_NextJS_Frontend]] proposed olarak kaydedildi; Streamlit teknoloji adi fonksiyonel gereksinimden ayrildi.
- 2026-07-28: TASK-009 icin [[ADR-002_Windows_Native_Dev_Gate]] kabul edildi; WSL timeout riski OCR/Kraken gate'e tasindi.
- 2026-07-28: TASK-010 icin SQLite MVP uzerinde Alembic initial migration ve gecici test DB rollback gate'i kabul edildi; production DB upgrade kullanici verisi yedegi olmadan kosulmayacak.

## ADR Durumu
- [[ADR-001_NextJS_Frontend]]: proposed.
- [[ADR-002_Windows_Native_Dev_Gate]]: accepted.
