# INSTALL_AUTONOMOUS_AGENT.ps1
$ErrorActionPreference = "Stop"

$root = (Get-Location).Path
$source = Join-Path $root "OTONOM_AJAN_OTOPILOT_PAKETI"

if (-not (Test-Path $source)) {
    Write-Host "HATA: OTONOM_AJAN_OTOPILOT_PAKETI proje kokunde bulunamadi." -ForegroundColor Red
    exit 1
}

$requiredRoot = @("AGENTS.md", "docs\wiki\Index.md", "PROMPTS")
foreach ($item in $requiredRoot) {
    if (-not (Test-Path (Join-Path $root $item))) {
        Write-Host "HATA: Proje kokunde eksik: $item" -ForegroundColor Red
        exit 1
    }
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $root "backup_autonomous_$timestamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null

$targetPrompt = Join-Path $root "PROMPTS\00_AUTONOMOUS_MASTER_ORCHESTRATOR.md"
$targetWatchdog = Join-Path $root "PROMPTS\98_AUTONOMOUS_WATCHDOG.md"
$targetState = Join-Path $root "docs\wiki\00_System\Autonomous_Run_State.md"

foreach ($target in @($targetPrompt, $targetWatchdog, $targetState)) {
    if (Test-Path $target) {
        Copy-Item $target $backup -Force
    }
}

Copy-Item (Join-Path $source "PROMPTS\00_AUTONOMOUS_MASTER_ORCHESTRATOR.md") $targetPrompt -Force
Copy-Item (Join-Path $source "PROMPTS\98_AUTONOMOUS_WATCHDOG.md") $targetWatchdog -Force
Copy-Item (Join-Path $source "docs\wiki\00_System\Autonomous_Run_State.md") $targetState -Force
Copy-Item (Join-Path $source "START_AUTONOMOUS_AGENT.txt") (Join-Path $root "START_AUTONOMOUS_AGENT.txt") -Force

Write-Host "PASS: Otonom ajan dosyalari yerlestirildi." -ForegroundColor Green
Write-Host "Ana prompt: $targetPrompt"
Write-Host "Durum dosyasi: $targetState"
Write-Host "Baslangic metni: $(Join-Path $root 'START_AUTONOMOUS_AGENT.txt')"
Write-Host "Yedek: $backup"
