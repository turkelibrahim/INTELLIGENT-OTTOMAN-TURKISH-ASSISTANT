---
type: decision
status: accepted
last_verified: 2026-07-28
owners:
  - codex
source_paths:
  - PROMPTS/03_ENVIRONMENT_GATE.md
  - evidence/environment_gate/doctor_full.txt
  - evidence/environment_gate/wsl_status.txt
tags: [adr, environment, windows, wsl]
---

# ADR-002 - Windows Native Development Gate

**Durum:** accepted

**Ozet:** TASK-009 icin kanonik yerel gelistirme ortami Windows uzerindeki `backend/venv` ve `frontend` npm ortamidir. WSL komutlari bu oturumda zaman asimina ugradi; SRS'te WSL Ubuntu Kraken icin onerilen uyumluluk katmani olarak gecmektedir. Bu nedenle WSL, genel dev/test gate icin zorunlu degil; OCR/Kraken gate icin TASK-017 kapsaminda yeniden dogrulanacak.

**Kutuphaneler:** Python 3.11.9, pytest, coverage, pypdf, Node.js, npm.

**Baglantilar:** [[Deployment_Architecture]], [[Test_Strategy]], [[OCR_Service]], [[Task_Queue]]

## Baglam
- `evidence/environment_gate/doctor_full.txt` backend pytest, core imports, frontend lint/build kontrollerinin PASS oldugunu gosterir.
- `evidence/environment_gate/wsl_status.txt` ve `wsl_version.txt` komutlari timeout verdi.
- SRS yazilim bagimliliklari bolumunde WSL2 Ubuntu `SHOULD`, Kraken/OCR ise `MUST` olarak gecmektedir.

## Karar
Windows-native ortam TASK-009 icin kabul edilir. WSL/Kraken dogrulamasi TASK-017 OCR adapter ve model dependency gate icinde release blocker olarak ele alinacaktir.

## Sonuclar
- TASK-009, WSL timeout riskini acik kayitla PASS olabilir.
- OCR/Kraken uygulamasina gecilmeden WSL veya esdeger calisma yolu dogrulanmalidir.

## Kanitlar
- `evidence/environment_gate/doctor_full.txt`
- `evidence/environment_gate/wsl_status.txt`
- `evidence/requirements_traceability/srs_extracted_text.txt`
