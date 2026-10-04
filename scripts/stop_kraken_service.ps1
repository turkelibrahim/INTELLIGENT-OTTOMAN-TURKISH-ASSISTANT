param(
    [string]$Url = "http://127.0.0.1:8765"
)

$ErrorActionPreference = "Continue"

try {
    Invoke-RestMethod -Method Post -Uri "$Url/shutdown" -TimeoutSec 3 | Out-Null
    Start-Sleep -Seconds 2
    Write-Host "STOP_REQUESTED"
    exit 0
}
catch {
    Write-Host "STOP_SKIPPED_OR_ALREADY_STOPPED: $($_.Exception.Message)"
    exit 0
}
