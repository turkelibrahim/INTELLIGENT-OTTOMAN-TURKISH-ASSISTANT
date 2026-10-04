$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[1/3] Python sanal ortam olusturuluyor..."
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { & py -3 -m venv .venv } else { & python -m venv .venv }
}
$Python = Join-Path $Root ".venv\Scripts\python.exe"
Write-Host "[2/3] pip guncelleniyor..."
& $Python -m pip install --upgrade pip
Write-Host "[3/3] Gereksinimler kuruluyor..."
& $Python -m pip install -r (Join-Path $Root "00_README\requirements.txt")
Write-Host "INSTALL_OK"
