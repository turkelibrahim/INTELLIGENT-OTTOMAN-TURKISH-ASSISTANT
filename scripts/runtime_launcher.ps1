param(
  [ValidateSet("Start", "Stop", "Restart", "Status", "Health", "Backend", "Frontend", "Setup")]
  [string]$Action = "Status"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$RuntimeDir = Join-Path $ProjectRoot "runtime"
$LogDir = Join-Path $RuntimeDir "logs"
$BackendPid = Join-Path $RuntimeDir "backend.pid"
$WorkerPid = Join-Path $RuntimeDir "worker.pid"
$FrontendPid = Join-Path $RuntimeDir "frontend.pid"
$BackendUrl = "http://127.0.0.1:8000"
$FrontendUrl = "http://127.0.0.1:3000"
$ApiUrl = "$BackendUrl/api/v1"
$ModelPath = Join-Path $ProjectRoot "models\recognition\ottoman_recognition_final_v1.mlmodel"
$ExpectedModelSha = "f5abbba1976e9782ddf5d7185d911722c74558e12b57a12566c96e22a3e3b963"
$LoraModelPath = Join-Path $ProjectRoot "models\osmanli_tarihcisi_lora"
$WslDistro = "Ubuntu-24.04"
$KrakenPython = "/home/black_man/venvs/ottoman_kraken/bin/python"

# Force Python to use UTF-8 encoding for stdout/stderr to prevent easyocr charmap errors
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

New-Item -ItemType Directory -Force $RuntimeDir, $LogDir | Out-Null

function Write-Log([string]$Message) {
  $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
  Add-Content -LiteralPath (Join-Path $LogDir "launcher.log") -Value $line -Encoding UTF8
  Write-Host $Message
}

function Test-Http([string]$Url, [int]$TimeoutSec = 3) {
  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
    return [int]$response.StatusCode
  } catch {
    return 0
  }
}

function Test-PidAlive([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $false }
  $pidValue = (Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue | Select-Object -First 1)
  if (-not $pidValue) { return $false }
  try {
    $proc = Get-Process -Id ([int]$pidValue) -ErrorAction Stop
    return ($null -ne $proc)
  } catch {
    return $false
  }
}

function Stop-PidFile([string]$Path, [string]$Name) {
  if (-not (Test-Path -LiteralPath $Path)) {
    Write-Log "$Name PID not found."
    return
  }
  $pidValue = (Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue | Select-Object -First 1)
  if ($pidValue) {
    try {
      $proc = Get-Process -Id ([int]$pidValue) -ErrorAction Stop
      Write-Log "Stopping $Name PID $pidValue..."
      & taskkill.exe /PID $proc.Id /T /F | Out-Null
    } catch {
      Write-Log "$Name PID $pidValue is not running."
    }
  }
  Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
}

function Assert-File([string]$Path, [string]$Message) {
  if (-not (Test-Path -LiteralPath $Path)) {
    throw $Message
  }
}

function Get-ModelSha {
  Assert-File $ModelPath "Kraken model file not found: $ModelPath"
  return (Get-FileHash -Algorithm SHA256 -LiteralPath $ModelPath).Hash.ToLowerInvariant()
}

function Test-Model {
  $sha = Get-ModelSha
  if ($sha -ne $ExpectedModelSha) {
    throw "Kraken model SHA mismatch. Expected $ExpectedModelSha, got $sha"
  }
  return $true
}

function Test-WslKraken {
  $wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
  if (-not $wsl) { throw "wsl.exe not found." }
  & wsl.exe -d $WslDistro -- true 2>$null
  if ($LASTEXITCODE -ne 0) { throw "WSL distro '$WslDistro' not found or not runnable." }
  $version = & wsl.exe -d $WslDistro -- $KrakenPython --version 2>&1
  if ($LASTEXITCODE -ne 0) { throw "Kraken Python not runnable: $version" }
  $import = & wsl.exe -d $WslDistro -- $KrakenPython -c "import kraken; print(getattr(kraken, '__version__', 'unknown'))" 2>&1
  if ($LASTEXITCODE -ne 0) { throw "Kraken import failed: $import" }
  return $true
}

function Test-Database {
  Assert-File (Join-Path $BackendDir "ottoman_assistant.db") "Database file not found."
  Push-Location $BackendDir
  try {
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $alembicLog = Join-Path $LogDir ("alembic_current_{0}_{1}.log" -f $PID, (Get-Date -Format "yyyyMMdd_HHmmssfff"))
    & ".\venv\Scripts\python.exe" -m alembic current > $alembicLog 2>&1
    $ErrorActionPreference = $oldPreference
    if ($LASTEXITCODE -ne 0) { throw "Alembic current failed. See $alembicLog" }
  } finally {
    if ($oldPreference) { $ErrorActionPreference = $oldPreference }
    Pop-Location
  }
  return $true
}

function Get-PortOwner([int]$Port) {
  $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $conn) { return $null }
  try {
    return Get-Process -Id $conn.OwningProcess -ErrorAction Stop
  } catch {
    return [pscustomobject]@{ Id = $conn.OwningProcess; ProcessName = "unknown" }
  }
}

function Start-DetachedCommand([string]$Command, [string]$WorkingDirectory) {
  $args = @{
    CommandLine = $Command
    CurrentDirectory = $WorkingDirectory
  }
  $result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments $args
  if ($result.ReturnValue -ne 0) {
    throw "Could not create process. WMI return value: $($result.ReturnValue)"
  }
  return [int]$result.ProcessId
}

function Assert-Prerequisites {
  Assert-File (Join-Path $BackendDir "venv\Scripts\python.exe") "Backend venv not found: backend\venv"
  Assert-File (Join-Path $FrontendDir "package.json") "Frontend package.json not found."
  Assert-File (Join-Path $FrontendDir "node_modules") "frontend\node_modules not found. Run FIRST_RUN_SETUP.bat if this is a new machine."
  $node = Get-Command node.exe -ErrorAction SilentlyContinue
  if (-not $node) { throw "node.exe not found in PATH." }
  $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
  if (-not $npm) { throw "npm.cmd not found in PATH." }
  Test-Model | Out-Null
  Test-WslKraken | Out-Null
  Test-Database | Out-Null
}

function Start-Backend {
  $health = Test-Http "$BackendUrl/health"
  if ($health -eq 200) {
    $owner = Get-PortOwner 8000
    if ($owner) { Set-Content -LiteralPath $BackendPid -Value $owner.Id -Encoding ASCII }
    Write-Log "Backend already ONLINE on $BackendUrl"
    return
  }
  $owner = Get-PortOwner 8000
  if ($owner) { throw "Port 8000 is occupied by PID $($owner.Id) ($($owner.ProcessName)), but backend health is not OK. Not killing foreign process." }
  if (Test-PidAlive $BackendPid) {
    Write-Log "Backend PID exists but health is not ready; continuing to poll."
  } else {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $out = Join-Path $LogDir "backend_$stamp.log"
    $err = Join-Path $LogDir "backend_error_$stamp.log"
    Write-Log "Starting backend..."
    $python = Join-Path $BackendDir "venv\Scripts\python.exe"
    $command = 'cmd.exe /d /c ""{0}" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 1>>"{1}" 2>>"{2}""' -f $python, $out, $err
    $createdPid = Start-DetachedCommand $command $BackendDir
    Set-Content -LiteralPath $BackendPid -Value $createdPid -Encoding ASCII
    Set-Content -LiteralPath (Join-Path $LogDir "backend_latest.log.path") -Value $out -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $LogDir "backend_error_latest.log.path") -Value $err -Encoding UTF8
  }
  for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    if ((Test-Http "$BackendUrl/health") -eq 200) {
      $owner = Get-PortOwner 8000
      if ($owner) { Set-Content -LiteralPath $BackendPid -Value $owner.Id -Encoding ASCII }
      Write-Log "Backend ONLINE."
      return
    }
  }
  throw "Backend could not start. See runtime\logs\backend_error_*.log"
}

function Start-Worker {
  if (Test-PidAlive $WorkerPid) {
    Write-Log "Worker already running."
    return
  }
  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $out = Join-Path $LogDir "worker_$stamp.log"
  $err = Join-Path $LogDir "worker_error_$stamp.log"
  Write-Log "Starting OCR worker..."
  $python = Join-Path $BackendDir "venv\Scripts\python.exe"
  $command = 'cmd.exe /d /c ""{0}" worker.py 1>>"{1}" 2>>"{2}""' -f $python, $out, $err
  $createdPid = Start-DetachedCommand $command $BackendDir
  Set-Content -LiteralPath $WorkerPid -Value $createdPid -Encoding ASCII
  Set-Content -LiteralPath (Join-Path $LogDir "worker_latest.log.path") -Value $out -Encoding UTF8
  Set-Content -LiteralPath (Join-Path $LogDir "worker_error_latest.log.path") -Value $err -Encoding UTF8
}

function Start-Frontend {
  $status = Test-Http "$FrontendUrl/login"
  if ($status -eq 200) {
    $owner = Get-PortOwner 3000
    if ($owner) { Set-Content -LiteralPath $FrontendPid -Value $owner.Id -Encoding ASCII }
    Write-Log "Frontend already ONLINE on $FrontendUrl"
    return
  }
  $owner = Get-PortOwner 3000
  if ($owner) { throw "Port 3000 is occupied by PID $($owner.Id) ($($owner.ProcessName)), but frontend is not OK. Not killing foreign process." }
  if (-not (Test-PidAlive $FrontendPid)) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $out = Join-Path $LogDir "frontend_$stamp.log"
    $err = Join-Path $LogDir "frontend_error_$stamp.log"
    Write-Log "Starting frontend..."
    $command = 'cmd.exe /d /c "set NEXT_PUBLIC_API_URL={0}&& npm.cmd run start -- -H 127.0.0.1 -p 3000 1>>"{1}" 2>>"{2}""' -f $ApiUrl, $out, $err
    $createdPid = Start-DetachedCommand $command $FrontendDir
    Set-Content -LiteralPath $FrontendPid -Value $createdPid -Encoding ASCII
    Set-Content -LiteralPath (Join-Path $LogDir "frontend_latest.log.path") -Value $out -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $LogDir "frontend_error_latest.log.path") -Value $err -Encoding UTF8
  }
  for ($i = 0; $i -lt 80; $i++) {
    Start-Sleep -Milliseconds 500
    if ((Test-Http "$FrontendUrl/login") -eq 200) {
      $owner = Get-PortOwner 3000
      if ($owner) { Set-Content -LiteralPath $FrontendPid -Value $owner.Id -Encoding ASCII }
      Write-Log "Frontend ONLINE."
      return
    }
  }
  throw "Frontend could not start. See runtime\logs\frontend_error_*.log"
}

function Show-Status {
  $backend = if ((Test-Http "$BackendUrl/health") -eq 200) { "ONLINE" } else { "OFFLINE" }
  $frontend = if ((Test-Http "$FrontendUrl/login") -eq 200) { "ONLINE" } else { "OFFLINE" }
  $db = if (Test-Path -LiteralPath (Join-Path $BackendDir "ottoman_assistant.db")) { "READY" } else { "MISSING" }
  $modelSha = if (Test-Path -LiteralPath $ModelPath) { Get-ModelSha } else { "MISSING" }
  $model = if ($modelSha -eq $ExpectedModelSha) { "VERIFIED" } else { "INVALID" }
  $wsl = "UNKNOWN"
  $kraken = "UNKNOWN"
  $cuda = "UNKNOWN"
  try {
    Test-WslKraken | Out-Null
    $wsl = "ONLINE"
    $kraken = "READY"
    $cudaOut = & wsl.exe -d $WslDistro -- $KrakenPython -c "import torch; print(torch.cuda.is_available())" 2>$null
    $cuda = ($cudaOut | Select-Object -First 1)
  } catch {
    $wsl = "CHECK_FAILED"
    $kraken = "CHECK_FAILED"
  }
  Write-Host ""
  Write-Host "Backend ........ $backend"
  Write-Host "Frontend ....... $frontend"
  Write-Host "Database ....... $db"
  Write-Host "WSL Ubuntu ..... $wsl"
  Write-Host "Kraken ......... $kraken"
  Write-Host "CUDA ........... $cuda"
  Write-Host "Model .......... $model"
  Write-Host "Model SHA ...... $modelSha"
  
  $loraStatus = if (Test-Path -LiteralPath $LoraModelPath) { "READY" } else { "MISSING (Will fallback/error)" }
  Write-Host "LoRA Model ..... $loraStatus"
  
  $port8000 = Get-PortOwner 8000
  $port3000 = Get-PortOwner 3000
  Write-Host "Port 8000 ...... $(if ($port8000) { "PID $($port8000.Id) $($port8000.ProcessName)" } else { "FREE" })"
  Write-Host "Port 3000 ...... $(if ($port3000) { "PID $($port3000.Id) $($port3000.ProcessName)" } else { "FREE" })"
}

function Start-App {
  Assert-Prerequisites
  Start-Backend
  Start-Worker
  Start-Frontend
  Write-Host ""
  Write-Host "==============================================="
  Write-Host "INTELLIGENT OTTOMAN TURKISH ASSISTANT"
  Write-Host "SYSTEM READY"
  Write-Host "==============================================="
  Write-Host "Backend : ONLINE"
  Write-Host "Frontend: ONLINE"
  Write-Host "Database: READY"
  Write-Host "Kraken  : READY"
  Write-Host "Model   : VERIFIED"
  $lora = if (Test-Path -LiteralPath $LoraModelPath) { "READY" } else { "MISSING" }
  Write-Host "LoRA    : $lora"
  Write-Host "==============================================="
  if ($env:RUNTIME_LAUNCHER_NO_PAUSE -ne "1") {
    Start-Process -FilePath "explorer.exe" -ArgumentList "$FrontendUrl/login"
  }
}

function Stop-App {
  Stop-PidFile $FrontendPid "Frontend"
  Stop-PidFile $WorkerPid "Worker"
  Stop-PidFile $BackendPid "Backend"
}

function Run-Health {
  Assert-Prerequisites
  Show-Status
}

function Run-Setup {
  New-Item -ItemType Directory -Force $RuntimeDir, $LogDir, (Join-Path $BackendDir "uploads") | Out-Null
  Assert-File (Join-Path $BackendDir "venv\Scripts\python.exe") "backend\venv missing. Create the backend virtual environment first."
  Assert-File (Join-Path $FrontendDir "package.json") "frontend\package.json missing."
  if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "node_modules"))) {
    Push-Location $FrontendDir
    try { npm.cmd install } finally { Pop-Location }
  }
  Write-Host "FIRST RUN SETUP READY"
}

try {
  switch ($Action) {
    "Start" { Start-App }
    "Stop" { Stop-App }
    "Restart" { Stop-App; Start-Sleep -Seconds 2; Start-App }
    "Status" { Show-Status }
    "Health" { Run-Health }
    "Backend" { Assert-Prerequisites; Start-Backend }
    "Frontend" { Start-Frontend }
    "Setup" { Run-Setup }
  }
} catch {
  Write-Host ""
  Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
  Add-Content -LiteralPath (Join-Path $LogDir "launcher.log") -Value ("{0} ERROR {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $_.Exception.Message) -Encoding UTF8
  exit 1
}
