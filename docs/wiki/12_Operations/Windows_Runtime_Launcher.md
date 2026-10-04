---
type: module
status: verified
last_verified: 2026-08-09
owners:
  - Codex
source_paths:
  - START_APP.bat
  - STOP_APP.bat
  - RESTART_APP.bat
  - STATUS_APP.bat
  - HEALTH_CHECK.bat
  - START_BACKEND.bat
  - START_FRONTEND.bat
  - FIRST_RUN_SETUP.bat
  - scripts/runtime_launcher.ps1
  - HOW_TO_RUN.md
test_paths:
  - evidence/runtime_launcher/start_test.txt
  - evidence/runtime_launcher/stop_test.txt
  - evidence/runtime_launcher/restart_test.txt
  - evidence/runtime_launcher/double_start_test.txt
  - evidence/runtime_launcher/health_check_bat.txt
tags: [operations, windows, launcher, runtime, wsl, kraken]
---

# Windows Runtime Launcher

**Özet:** Windows üzerinde çift tıklamayla backend, worker ve frontend servislerini başlatan launcher sistemi uygulanmıştır. Launcher PID dosyalarıyla yalnız kendi processlerini durdurur, WSL Ubuntu'yu terminate etmez ve Kraken model SHA kontrolünü startup health gate olarak kullanır.

**Kütüphaneler:** Windows Batch, PowerShell, FastAPI, Uvicorn, Next.js, WSL, Kraken.

**Bağlantılar:** [[Deployment_Architecture]], [[FastAPI_API]], [[Document_Workspace]], [[OCR_Service]], [[Index]]

## Sorumluluklar
- `START_APP.bat` ile uygulama runtime'ını başlatmak.
- `STOP_APP.bat` ile yalnız launcher PID'lerini durdurmak.
- `STATUS_APP.bat` ve `HEALTH_CHECK.bat` ile read-only tanılama sağlamak.
- Backend, worker ve frontend runtime config uyumunu korumak.

## Girdiler
- `backend\venv`
- `frontend\package.json`
- `frontend\node_modules`
- `backend\ottoman_assistant.db`
- `models\recognition\ottoman_recognition_final_v1.mlmodel`
- WSL Ubuntu ve Kraken Python path.

## Çıktılar
- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:3000`
- Browser: `http://127.0.0.1:3000/login`
- Runtime logs: `runtime\logs\`

## Bağımlılıklar
- Node.js/npm.cmd.
- Python 3.11 backend venv.
- WSL Ubuntu.
- `/home/ibrah/venvs/ottoman_kraken/bin/python`.
- SQLite database.

## Veri Akışı
1. Launcher prerequisites ve model SHA kontrolü yapar.
2. Backend health hazır olana kadar poll eder.
3. Worker process başlatılır.
4. Frontend `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1` ile başlatılır.
5. Login route hazır olunca browser açılır.

## Hata Durumları
- Port 8000 veya 3000 yanlış process tarafından dinleniyorsa launcher o processi öldürmez ve açık hata verir.
- Model SHA uyuşmazsa startup durur.
- Backend/frontend hazır olmazsa ilgili runtime log dosyasına yönlendirir.

## Güvenlik ve Gizlilik
- Token, parola veya secret evidence/wiki içine yazılmadı.
- STOP scriptleri `taskkill /F /IM python.exe` veya `node.exe` kullanmaz.
- WSL distro varsayılan olarak terminate edilmez.

## Testler ve Kabul Kriterleri
- `START_APP.bat` PASS.
- `STOP_APP.bat` PASS.
- `RESTART_APP.bat` PASS.
- Double-start duplicate process oluşturmadı.
- Backend health, frontend login/register, auth, upload ve Kraken OCR smoke PASS.

## Kod Kanıtları
- `scripts/runtime_launcher.ps1` → `Start-App`, `Stop-App`, `Show-Status`, `Run-Health`
- `START_APP.bat` → kullanıcı launcher'ı.
- `STOP_APP.bat` → güvenli durdurma.
- `evidence/runtime_launcher/kraken_runtime_metadata.json` → `actual_engine=kraken`, `fallback_used=false`.

## Bilinen Eksikler
- Launcher production process manager değildir; yerel Windows geliştirme/kullanıcı başlatma akışı içindir.

## Değişiklik Geçmişi
- 2026-08-09: Runtime launcher sistemi uygulandı ve `WINDOWS_ONE_CLICK_RUNTIME_PASS` kanıtlandı.
