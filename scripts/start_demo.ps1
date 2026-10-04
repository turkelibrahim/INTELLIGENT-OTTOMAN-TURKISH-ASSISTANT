param(
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 3000,
  [switch]$SkipFrontendBuild,
  [string]$EvidencePath = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$RuntimeDir = Join-Path $ProjectRoot "runtime\demo"
$LogDir = Join-Path $RuntimeDir "logs"
$EvidenceDir = if ($EvidencePath) { $EvidencePath } else { Join-Path $ProjectRoot "evidence\final_release_gate" }
$BackendPid = Join-Path $RuntimeDir "backend.pid"
$FrontendPid = Join-Path $RuntimeDir "frontend.pid"
$BackendUrl = "http://127.0.0.1:$BackendPort"
$FrontendUrl = "http://127.0.0.1:$FrontendPort"
$ApiUrl = "$BackendUrl/api/v1"

New-Item -ItemType Directory -Force -Path $RuntimeDir, $LogDir, $EvidenceDir | Out-Null

function Write-DemoLog([string]$Message) {
  $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
  Add-Content -LiteralPath (Join-Path $LogDir "demo_launcher.log") -Value $line -Encoding UTF8
  Write-Host $Message
}

function Get-PortOwner([int]$Port) {
  $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $conn) { return $null }
  try { return Get-Process -Id $conn.OwningProcess -ErrorAction Stop } catch { return [pscustomobject]@{ Id = $conn.OwningProcess; ProcessName = "unknown" } }
}

function Test-Http([string]$Url, [int]$TimeoutSec = 3) {
  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
    return [int]$response.StatusCode
  } catch {
    return 0
  }
}

function Wait-HttpOk([string]$Url, [int]$Seconds, [string]$Name) {
  for ($i = 0; $i -lt ($Seconds * 2); $i++) {
    Start-Sleep -Milliseconds 500
    $status = Test-Http $Url 3
    if ($status -ge 200 -and $status -lt 500) {
      Write-DemoLog "$Name ready: $Url (HTTP $status)"
      return $true
    }
  }
  throw "$Name did not become ready at $Url"
}

function Start-Backend {
  $docsUrl = "$BackendUrl/docs"
  if ((Test-Http $docsUrl 3) -eq 200) {
    $owner = Get-PortOwner $BackendPort
    if ($owner) { Set-Content -LiteralPath $BackendPid -Value $owner.Id -Encoding ASCII }
    Write-DemoLog "Backend already online at $BackendUrl"
    return
  }
  $owner = Get-PortOwner $BackendPort
  if ($owner) {
    throw "Backend port $BackendPort is occupied by PID $($owner.Id) ($($owner.ProcessName)); not killing foreign process."
  }
  $python = Join-Path $BackendDir "venv\Scripts\python.exe"
  if (-not (Test-Path -LiteralPath $python)) { throw "Backend venv python missing: $python" }
  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $out = Join-Path $LogDir "backend_$stamp.log"
  $err = Join-Path $LogDir "backend_error_$stamp.log"
  $env:PYTHONPATH = $BackendDir
  $env:DEBUG = "production"
  $env:LLM_PROVIDER = "ollama"
  $env:LLM_MODEL = "qwen3.5:4b"
  $env:LLM_BASE_URL = "http://127.0.0.1:11434"
  $env:OLLAMA_MODEL = "qwen3.5:4b"
  $env:OLLAMA_EMBEDDING_MODEL = "qwen3-embedding:0.6b"
  $env:CORS_ORIGINS = "[`"http://localhost:$FrontendPort`",`"http://127.0.0.1:$FrontendPort`"]"
  Write-DemoLog "Starting backend on $BackendUrl"
  $cmd = "set PYTHONPATH=$BackendDir&& set DEBUG=production&& set LLM_PROVIDER=ollama&& set LLM_MODEL=qwen3.5:4b&& set LLM_BASE_URL=http://127.0.0.1:11434&& set OLLAMA_MODEL=qwen3.5:4b&& set OLLAMA_EMBEDDING_MODEL=qwen3-embedding:0.6b&& set CORS_ORIGINS=[`"http://localhost:$FrontendPort`",`"http://127.0.0.1:$FrontendPort`"]&& `"$python`" -m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort > `"$out`" 2> `"$err`""
  $proc = Start-Process -FilePath "cmd.exe" -ArgumentList @("/d", "/c", $cmd) -WorkingDirectory $BackendDir -WindowStyle Hidden -PassThru
  Set-Content -LiteralPath $BackendPid -Value $proc.Id -Encoding ASCII
  Set-Content -LiteralPath (Join-Path $LogDir "backend_latest.log.path") -Value $out -Encoding UTF8
  Set-Content -LiteralPath (Join-Path $LogDir "backend_error_latest.log.path") -Value $err -Encoding UTF8
  Wait-HttpOk "$BackendUrl/docs" 90 "Backend" | Out-Null
}

function Start-Frontend {
  $loginUrl = "$FrontendUrl/login"
  if ((Test-Http $loginUrl 3) -eq 200) {
    $owner = Get-PortOwner $FrontendPort
    if ($owner) { Set-Content -LiteralPath $FrontendPid -Value $owner.Id -Encoding ASCII }
    Write-DemoLog "Frontend already online at $FrontendUrl"
    return
  }
  $owner = Get-PortOwner $FrontendPort
  if ($owner) {
    throw "Frontend port $FrontendPort is occupied by PID $($owner.Id) ($($owner.ProcessName)); not killing foreign process."
  }
  if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "node_modules"))) {
    throw "frontend node_modules missing. Run npm install before demo."
  }
  Push-Location $FrontendDir
  try {
    $env:NEXT_PUBLIC_API_URL = $ApiUrl
    if (-not $SkipFrontendBuild) {
      Write-DemoLog "Building frontend with NEXT_PUBLIC_API_URL=$ApiUrl"
      & npm.cmd run build
      if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
    } elseif (-not (Test-Path -LiteralPath (Join-Path $FrontendDir ".next"))) {
      throw "Frontend .next build missing and -SkipFrontendBuild was supplied."
    }
  } finally {
    Pop-Location
  }
  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $out = Join-Path $LogDir "frontend_$stamp.log"
  $err = Join-Path $LogDir "frontend_error_$stamp.log"
  Write-DemoLog "Starting frontend on $FrontendUrl"
  $cmd = "set NEXT_PUBLIC_API_URL=$ApiUrl&& npm.cmd run start -- -H 127.0.0.1 -p $FrontendPort > `"$out`" 2> `"$err`""
  $proc = Start-Process -FilePath "cmd.exe" -ArgumentList @("/d", "/c", $cmd) -WorkingDirectory $FrontendDir -WindowStyle Hidden -PassThru
  Set-Content -LiteralPath $FrontendPid -Value $proc.Id -Encoding ASCII
  Set-Content -LiteralPath (Join-Path $LogDir "frontend_latest.log.path") -Value $out -Encoding UTF8
  Set-Content -LiteralPath (Join-Path $LogDir "frontend_error_latest.log.path") -Value $err -Encoding UTF8
  Wait-HttpOk "$FrontendUrl/login" 90 "Frontend" | Out-Null
}

try {
  $start = Get-Date
  Write-DemoLog "Running pre-demo health check"
  & (Join-Path $PSScriptRoot "pre_demo_check.ps1") -EvidencePath $EvidenceDir
  if ($LASTEXITCODE -ne 0) { throw "Pre-demo health check failed." }
  Start-Backend
  Start-Frontend
  $elapsed = [math]::Round(((Get-Date) - $start).TotalSeconds, 2)
  $summary = [ordered]@{
    status = "PASS"
    timestamp = (Get-Date).ToString("o")
    backend_url = $BackendUrl
    frontend_url = $FrontendUrl
    api_url = $ApiUrl
    elapsed_seconds = $elapsed
    backend_pid = if (Test-Path $BackendPid) { (Get-Content -Raw -LiteralPath $BackendPid).Trim() } else { $null }
    frontend_pid = if (Test-Path $FrontendPid) { (Get-Content -Raw -LiteralPath $FrontendPid).Trim() } else { $null }
  }
  $summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $EvidenceDir "startup_state.json") -Encoding UTF8
  Write-Host ""
  Write-Host "DEMO STARTUP: PASS" -ForegroundColor Green
  Write-Host "Frontend URL: $FrontendUrl/login"
  Write-Host "Backend URL : $BackendUrl/docs"
  Write-Host "API URL     : $ApiUrl"
  exit 0
} catch {
  Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
  Add-Content -LiteralPath (Join-Path $LogDir "demo_launcher.log") -Value ("{0} ERROR {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $_.Exception.Message) -Encoding UTF8
  exit 1
}
