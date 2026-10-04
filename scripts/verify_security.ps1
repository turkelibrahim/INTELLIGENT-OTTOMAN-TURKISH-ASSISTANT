Write-Output "Starting Security Verification"
$ErrorActionPreference = "Continue"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

$failed = 0
function Assert-Pass {
    param([string]$Name, [int]$ExitCode)
    if ($ExitCode -ne 0) {
        Write-Output "FAIL: $Name"
        $script:failed += 1
    } else {
        Write-Output "PASS: $Name"
    }
}

# 1. Pip 26.2 bootstrap
Write-Output "--- 1. Clean Environment Bootstrap ---"
Push-Location $root
if (Test-Path "C:\temp\cenv") { Remove-Item -Recurse -Force "C:\temp\cenv" }
python -m venv C:\temp\cenv
& C:\temp\cenv\Scripts\python.exe -m pip install --upgrade pip==26.2
Assert-Pass "Pip 26.2 upgrade" $LASTEXITCODE

# 2. Kanonik requirements kurulumu
& C:\temp\cenv\Scripts\python.exe -m pip install -r backend\requirements.txt --ignore-installed setuptools --quiet
& C:\temp\cenv\Scripts\python.exe -m pip install -r backend\requirements-ocr.txt --ignore-installed setuptools --quiet
Assert-Pass "Kanonik requirements kurulumu" $LASTEXITCODE

# 3. pip check
Write-Output "--- 3. pip check ---"
& C:\temp\cenv\Scripts\python.exe -m pip check
Assert-Pass "pip check" $LASTEXITCODE

# 4. Tam pip-audit
Write-Output "--- 4. pip-audit ---"
& C:\temp\cenv\Scripts\python.exe -m pip install pip-audit
$env:PYTHONUTF8=1
& C:\temp\cenv\Scripts\python.exe -m pip_audit
Assert-Pass "pip-audit" $LASTEXITCODE

# 5. Backend testlerinin tamami
Write-Output "--- 5. Backend Tests ---"
Push-Location $backend
$env:PYTHONPATH="."
& C:\temp\cenv\Scripts\python.exe -m pytest tests -q
Assert-Pass "Backend tests" $LASTEXITCODE
Pop-Location

# 6. Doctor gate
Write-Output "--- 6. Doctor Gate ---"
powershell -ExecutionPolicy Bypass -File scripts\bootstrap.ps1
Assert-Pass "Bootstrap main venv" $LASTEXITCODE

powershell -ExecutionPolicy Bypass -File scripts\doctor.ps1
Assert-Pass "Doctor gate" $LASTEXITCODE

# 11. Frontend lint/build
Write-Output "--- 11. Frontend Lint/Build ---"
Push-Location $frontend
npm.cmd run lint
Assert-Pass "Frontend lint" $LASTEXITCODE
npm.cmd run build
Assert-Pass "Frontend build" $LASTEXITCODE
Pop-Location

# 12. npm audit
Write-Output "--- 12. npm audit ---"
Push-Location $frontend
npm.cmd audit --audit-level=high
Assert-Pass "npm audit" $LASTEXITCODE
Pop-Location

# Live Server Smoke Tests
Write-Output "--- Live Server Smoke Tests ---"
Push-Location $backend
$proc = Start-Process -NoNewWindow -FilePath "C:\temp\cenv\Scripts\python.exe" -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8002" -PassThru
Start-Sleep -Seconds 7

try {
    $response = Invoke-RestMethod http://127.0.0.1:8002/health
    if ($response.status -eq "healthy") {
        Assert-Pass "Canli /health" 0
    } else {
        Assert-Pass "Canli /health" 1
    }
} catch {
    Assert-Pass "Canli /health" 1
}

try {
    $body = @{
        email = "test_smoke@example.com"
        password = "testpassword123"
        username = "test_smoke"
    } | ConvertTo-Json
    Invoke-RestMethod -Uri http://127.0.0.1:8002/api/v1/auth/register -Method Post -Body $body -ContentType "application/json" -ErrorAction SilentlyContinue | Out-Null
    
    $loginBody = "username=test_smoke@example.com&password=testpassword123"
    $loginResponse = Invoke-RestMethod -Uri http://127.0.0.1:8002/api/v1/auth/login -Method Post -Body $loginBody -ContentType "application/x-www-form-urlencoded"
    if ($loginResponse.access_token) {
        Assert-Pass "Canli kayit/giris" 0
    } else {
        Assert-Pass "Canli kayit/giris" 1
    }
} catch {
    Assert-Pass "Canli kayit/giris" 1
}

Stop-Process -Id $proc.Id -Force
Pop-Location

# 15. Gercek OCR smoke
Write-Output "--- 15. Gercek OCR smoke ---"
Push-Location $root
& C:\temp\cenv\Scripts\python.exe backend\scripts\test_real_ocr.py
Assert-Pass "Gercek OCR smoke" $LASTEXITCODE
Pop-Location

if ($failed -gt 0) {
    Write-Output "VERIFICATION FAILED: $failed checks failed."
    exit 1
}
Write-Output "VERIFICATION PASSED."
exit 0
