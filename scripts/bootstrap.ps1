Write-Output "Bootstrapping environment..."
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Push-Location $backend

# Create virtual environment
python -m venv venv

# Upgrade pip to secure version immediately (SECURITY REQUIREMENT)
& venv\Scripts\python.exe -m pip install --upgrade pip==26.2

# Install backend requirements
& venv\Scripts\python.exe -m pip install -r requirements.txt
& venv\Scripts\python.exe -m pip install -r requirements-ocr.txt

Pop-Location

# Frontend setup
Push-Location $frontend
npm.cmd install
Pop-Location

Write-Output "Environment successfully bootstrapped."
