# Otonom Ajan Otopilot Paketi

Bu paket mevcut `AGENTS.md`, Obsidian Wiki ve 01–20 uçuş promptlarının üzerine kurulur.

## Kurulum

ZIP'i proje köküne çıkart. Klasör adı:

`OTONOM_AJAN_OTOPILOT_PAKETI`

PowerShell'i proje kökünde aç:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\OTONOM_AJAN_OTOPILOT_PAKETI\INSTALL_AUTONOMOUS_AGENT.ps1
```

Sonra proje kökündeki `START_AUTONOMOUS_AGENT.txt` içeriğini kodlama ajanına yalnız bir kez ver.

## Davranış

- Aktif görevi Wiki'den bulur.
- İlgili aşama promptunu kendisi açar.
- Görevi uygular.
- Test eder.
- Bağımsız doğrular.
- PASS ise sıradaki göreve geçer.
- Yeni ajan oturumunda kaldığı yerden devam eder.
- Release ve yayın sonrası smoke tamamlanana kadar çalışır.

## Gerçek Teknik Sınır

Bir ajan oturumu platform tarafından kapatılırsa ajan fiziksel olarak kendi kendine yeni sohbet veya yeni süreç başlatamaz. Yeni ajan oturumu açıldığında `START_AUTONOMOUS_AGENT.txt` tekrar verilir veya `PROMPTS/98_AUTONOMOUS_WATCHDOG.md` çalıştırılır. Ajan kalıcı durum dosyasından tam kaldığı yerden devam eder.
