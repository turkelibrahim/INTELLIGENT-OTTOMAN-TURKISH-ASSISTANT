param(
    [string]$Distro = "Ubuntu-24.04",
    [string]$PythonPath = "/home/black_man/venvs/ottoman_kraken/bin/python",
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8765,
    [int]$Concurrency = 1
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LogDir = Join-Path $ProjectRoot "runtime\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogPath = Join-Path $LogDir "kraken_service.log"
$Url = "http://127.0.0.1:$Port"

try {
    $ready = Invoke-RestMethod -Uri "$Url/health/ready" -TimeoutSec 2
    if ($ready.model_loaded -eq $true) {
        Write-Host "ALREADY_RUNNING"
        $ready | ConvertTo-Json -Depth 5
        exit 0
    }
}
catch {
    # Not running; continue startup.
}

$ModelPath = Join-Path $ProjectRoot "models\recognition\ottoman_recognition_final_v1.mlmodel"
$ServiceScript = Join-Path $ProjectRoot "backend\scripts\kraken_wsl_service.py"
$WslModelPath = (& wsl.exe -d $Distro -- wslpath -a "$ModelPath").Trim()
$WslServiceScript = (& wsl.exe -d $Distro -- wslpath -a "$ServiceScript").Trim()
$StdoutPath = Join-Path $LogDir "kraken_service.stdout.log"
$StderrPath = Join-Path $LogDir "kraken_service.stderr.log"
$BridgeRuntimeDir = "C:/ottoman_ocr_runtime"
New-Item -ItemType Directory -Force -Path $BridgeRuntimeDir | Out-Null
$WinLaunchScript = Join-Path $BridgeRuntimeDir "start_kraken_service.sh"
$WslLaunchScript = "/mnt/c/ottoman_ocr_runtime/start_kraken_service.sh"
$WslLogPath = (& wsl.exe -d $Distro -- wslpath -a "$StderrPath").Trim()
$LaunchContent = @"
#!/usr/bin/env bash
cd /tmp
exec "$PythonPath" "$WslServiceScript" --host "0.0.0.0" --port "$Port" --model-path "$WslModelPath" --concurrency "$Concurrency" >> "$WslLogPath" 2>&1
"@
$LaunchContent = $LaunchContent.Replace("`r`n", "`n").TrimStart() + "`n"
[System.IO.File]::WriteAllText($WinLaunchScript, $LaunchContent, [System.Text.UTF8Encoding]::new($false))
Start-Process `
    -FilePath "wsl.exe" `
    -ArgumentList @("-d", $Distro, "--", "/bin/bash", $WslLaunchScript) `
    -WindowStyle Hidden | Out-Null

$deadline = (Get-Date).AddSeconds(180)
do {
    Start-Sleep -Seconds 2
    try {
        $ready = Invoke-RestMethod -Uri "$Url/health/ready" -TimeoutSec 5
        if ($ready.model_loaded -eq $true) {
            "Kraken service READY $(Get-Date -Format o)" | Out-File -FilePath $LogPath -Append -Encoding utf8
            Get-Content -LiteralPath $StderrPath -ErrorAction SilentlyContinue | Out-File -FilePath $LogPath -Append -Encoding utf8
            $ready | ConvertTo-Json -Depth 5
            exit 0
        }
    }
    catch {
        "Waiting for Kraken service: $($_.Exception.Message)" | Out-File -FilePath $LogPath -Append -Encoding utf8
    }
} while ((Get-Date) -lt $deadline)

Write-Error "Kraken service did not become READY before timeout. See $LogPath"
exit 1
