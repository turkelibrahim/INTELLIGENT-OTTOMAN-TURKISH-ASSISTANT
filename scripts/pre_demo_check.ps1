param(
  [switch]$AllowFrontendBuild,
  [string]$EvidencePath = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$EvidenceDir = if ($EvidencePath) { $EvidencePath } else { Join-Path $ProjectRoot "evidence\final_release_gate" }
$KrakenModel = Join-Path $ProjectRoot "models\recognition\ottoman_recognition_final_v1.mlmodel"
$ExpectedKrakenSha = "f5abbba1976e9782ddf5d7185d911722c74558e12b57a12566c96e22a3e3b963"
$QdrantPath = if ($env:HISTORICAL_QDRANT_PATH) { $env:HISTORICAL_QDRANT_PATH } else { "C:\ottoman_ai_data\qdrant" }
$RequiredOllamaModels = @("qwen3.5:4b", "qwen3-embedding:0.6b")

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

$checks = [ordered]@{
  timestamp = (Get-Date).ToString("o")
  project_root = $ProjectRoot
  ollama = [ordered]@{}
  backend = [ordered]@{}
  frontend = [ordered]@{}
  storage = [ordered]@{}
  status = "FAIL"
  errors = @()
}

function Add-Error([string]$Message) {
  $script:checks.errors += $Message
  Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Add-Ok([string]$Message) {
  Write-Host "[OK] $Message" -ForegroundColor Green
}

function Test-WritableDirectory([string]$Path) {
  New-Item -ItemType Directory -Force -Path $Path | Out-Null
  $probe = Join-Path $Path (".demo_write_probe_{0}.tmp" -f ([guid]::NewGuid().ToString("N")))
  Set-Content -LiteralPath $probe -Value "ok" -Encoding ASCII
  Remove-Item -LiteralPath $probe -Force
  return $true
}

try {
  $ollama = Get-Command ollama.exe -ErrorAction SilentlyContinue
  if (-not $ollama) { Add-Error "ollama.exe not found in PATH." } else {
    $checks.ollama.executable = $ollama.Source
    $tagsRaw = & ollama.exe list 2>&1
    if ($LASTEXITCODE -ne 0) {
      Add-Error "Ollama is not reachable: $tagsRaw"
    } else {
      $checks.ollama.reachable = $true
      $checks.ollama.list_output = ($tagsRaw -join "`n")
      foreach ($model in $RequiredOllamaModels) {
        $present = ($tagsRaw | Select-String -SimpleMatch $model -Quiet)
        $checks.ollama[$model] = $present
        if ($present) { Add-Ok "Ollama model available: $model" } else { Add-Error "Missing Ollama model: $model" }
      }
    }
  }
} catch {
  Add-Error "Ollama check failed: $($_.Exception.Message)"
}

try {
  $python = Join-Path $BackendDir "venv\Scripts\python.exe"
  if (-not (Test-Path -LiteralPath $python)) { Add-Error "Backend venv python missing: $python" } else {
    $checks.backend.python = $python
    $pyVersion = & $python --version 2>&1
    $checks.backend.python_version = ($pyVersion -join " ")
    Add-Ok "Backend Python available: $($checks.backend.python_version)"
    $moduleScript = @'
import importlib, json, sys
mods = ["fastapi", "uvicorn", "sqlalchemy", "cv2", "qdrant_client", "faiss", "numpy", "PIL", "requests"]
result = {}
for mod in mods:
    try:
        importlib.import_module(mod)
        result[mod] = True
    except Exception as exc:
        result[mod] = f"{type(exc).__name__}: {exc}"
print(json.dumps(result, ensure_ascii=False))
'@
    $moduleJson = $moduleScript | & $python -
    $moduleResult = $moduleJson | ConvertFrom-Json
    $checks.backend.modules = $moduleResult
    foreach ($prop in $moduleResult.PSObject.Properties) {
      if ($prop.Value -eq $true) { Add-Ok "Python module import OK: $($prop.Name)" } else { Add-Error "Python module import failed: $($prop.Name) -> $($prop.Value)" }
    }
  }

  if (-not (Test-Path -LiteralPath $KrakenModel)) {
    Add-Error "Kraken model missing: $KrakenModel"
  } else {
    $sha = (Get-FileHash -Algorithm SHA256 -LiteralPath $KrakenModel).Hash.ToLowerInvariant()
    $checks.backend.kraken_model = [ordered]@{ path = $KrakenModel; sha256 = $sha; expected_sha256 = $ExpectedKrakenSha; ok = ($sha -eq $ExpectedKrakenSha) }
    if ($sha -eq $ExpectedKrakenSha) { Add-Ok "Kraken model SHA verified." } else { Add-Error "Kraken model SHA mismatch: $sha" }
  }

  if (-not (Test-Path -LiteralPath $QdrantPath)) {
    Add-Error "Historical Qdrant path missing: $QdrantPath"
  } else {
    $checks.backend.qdrant_path = $QdrantPath
    Add-Ok "Historical Qdrant path exists."
    if (Test-Path -LiteralPath $python) {
      $qdrantScript = @'
import json
from app.services.historical_rag import HistoricalQdrantStore
store = HistoricalQdrantStore()
try:
    count = store.count()
    results = store.search("Osmanlı", limit=3, verified_only=True)
    print(json.dumps({
        "count": count,
        "verified_search_count": len(results),
        "all_verified": all(item.get("verified") is True for item in results),
    }, ensure_ascii=False))
finally:
    pass
'@
      Push-Location $BackendDir
      try {
        $env:PYTHONPATH = "."
        $qdrantJson = $qdrantScript | & $python -
      } finally {
        Pop-Location
      }
      $qdrant = $qdrantJson | ConvertFrom-Json
      $checks.backend.qdrant = $qdrant
      if ($qdrant.count -gt 0 -and $qdrant.all_verified) { Add-Ok "Historical Qdrant corpus accessible: $($qdrant.count) points." } else { Add-Error "Historical Qdrant corpus check failed." }
    }
  }
} catch {
  Add-Error "Backend check failed: $($_.Exception.Message)"
}

try {
  $node = Get-Command node.exe -ErrorAction SilentlyContinue
  $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
  if (-not $node) { Add-Error "node.exe not found in PATH." } else {
    $checks.frontend.node = (& node.exe --version)
    Add-Ok "Node available: $($checks.frontend.node)"
  }
  if (-not $npm) { Add-Error "npm.cmd not found in PATH." } else {
    Push-Location $FrontendDir
    try {
      $checks.frontend.npm = (& npm.cmd --version)
    } finally {
      Pop-Location
    }
    Add-Ok "npm available: $($checks.frontend.npm)"
  }
  if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "node_modules"))) {
    Add-Error "frontend node_modules missing. Run npm install before demo."
  } else {
    Add-Ok "frontend node_modules exists."
  }
  $nextBuild = Join-Path $FrontendDir ".next"
  if (Test-Path -LiteralPath $nextBuild) {
    $checks.frontend.next_build_exists = $true
    Add-Ok "frontend .next build exists."
  } elseif ($AllowFrontendBuild) {
    Push-Location $FrontendDir
    try {
      $env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000/api/v1"
      & npm.cmd run build
      if ($LASTEXITCODE -ne 0) { Add-Error "frontend build command failed." } else { Add-Ok "frontend build command passed." }
    } finally {
      Pop-Location
    }
  } else {
    Add-Error "frontend .next build missing. Run pre_demo_check.ps1 -AllowFrontendBuild or npm.cmd run build."
  }
} catch {
  Add-Error "Frontend check failed: $($_.Exception.Message)"
}

try {
  $uploadDir = Join-Path $BackendDir "uploads"
  $evidenceDirWritable = $EvidenceDir
  $checks.storage.upload_writable = Test-WritableDirectory $uploadDir
  $checks.storage.evidence_writable = Test-WritableDirectory $evidenceDirWritable
  Add-Ok "upload and evidence directories writable."
} catch {
  Add-Error "Storage writable check failed: $($_.Exception.Message)"
}

if ($checks.errors.Count -eq 0) {
  $checks.status = "PASS"
  Write-Host "PRE_DEMO_HEALTH_GATE: PASS" -ForegroundColor Green
} else {
  $checks.status = "FAIL"
  Write-Host "PRE_DEMO_HEALTH_GATE: FAIL" -ForegroundColor Red
}

$checks | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $EvidenceDir "pre_demo_health.json") -Encoding UTF8
if ($checks.status -ne "PASS") { exit 1 }
