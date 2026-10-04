param(
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvPython = Join-Path $backend "venv\Scripts\python.exe"

Write-Output "DOCTOR_ROOT=$root"
Write-Output "DATE_UTC=$((Get-Date).ToUniversalTime().ToString('s'))Z"

$failed = 0

function Run-Step {
    param(
        [string]$Name,
        [scriptblock]$Script
    )
    Write-Output "--- $Name ---"
    try {
        & $Script
        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
            Write-Output "RESULT=$Name FAIL exit=$LASTEXITCODE"
            $script:failed += 1
            return
        }
        Write-Output "RESULT=$Name PASS"
    } catch {
        Write-Output "RESULT=$Name FAIL $($_.Exception.Message)"
        $script:failed += 1
    }
}

Run-Step "python-version" { & $venvPython --version }
Run-Step "backend-import" { Push-Location $backend; & $venvPython test_import.py; Pop-Location }
Run-Step "backend-pytest" {
    Push-Location $backend
    & $venvPython -m pytest tests --ignore=tests/e2e/test_ground_truth_browser.py
    Pop-Location
}
Run-Step "backend-core-imports" {
    Push-Location $backend
    $code = "import cv2; from PIL import Image; import torch; import sqlalchemy; from app.main import app; from app.db.database import Base; print('fastapi_app', bool(app)); print('sqlalchemy_metadata_tables', len(Base.metadata.tables)); print('opencv', cv2.__version__); print('pillow', Image.__version__); print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"
    & $venvPython -c $code
    Pop-Location
}
Run-Step "node-version" { node --version; npm.cmd --version }
Run-Step "frontend-lint" { Push-Location $frontend; npm.cmd run lint; Pop-Location }
if (-not $SkipFrontendBuild) {
    Run-Step "frontend-build" { Push-Location $frontend; npm.cmd run build; Pop-Location }
}

Write-Output "DOCTOR_FAILED=$failed"
if ($failed -gt 0) {
    exit 1
}
exit 0
