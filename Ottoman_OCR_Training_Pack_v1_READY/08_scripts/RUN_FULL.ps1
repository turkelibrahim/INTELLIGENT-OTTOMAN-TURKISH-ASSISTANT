$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
& "$PSScriptRoot\RUN_CORE.ps1"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
& $Python "$PSScriptRoot\02_download_full.py" --extract
& $Python "$PSScriptRoot\06_index_full_makhzan.py"
& $Python "$PSScriptRoot\09_validate_pack.py" --full
& $Python "$PSScriptRoot\10_hash_pack.py"
Write-Host "FULL_DATA_PACK_READY"
