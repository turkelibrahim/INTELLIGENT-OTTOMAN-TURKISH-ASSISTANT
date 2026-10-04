param(
  [string]$EvidencePath = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RuntimeDir = Join-Path $ProjectRoot "runtime\demo"
$LogDir = Join-Path $RuntimeDir "logs"
$EvidenceDir = if ($EvidencePath) { $EvidencePath } else { Join-Path $ProjectRoot "evidence\final_release_gate" }
$BackendPid = Join-Path $RuntimeDir "backend.pid"
$FrontendPid = Join-Path $RuntimeDir "frontend.pid"

New-Item -ItemType Directory -Force -Path $RuntimeDir, $LogDir, $EvidenceDir | Out-Null

function Stop-DemoPid([string]$PidPath, [string]$Name) {
  $result = [ordered]@{ name = $Name; pid_file = $PidPath; stopped = $false; stopped_pids = @(); note = "" }
  if (-not (Test-Path -LiteralPath $PidPath)) {
    $result.note = "pid file not found"
    Write-Host "${Name}: PID file not found."
    return $result
  }
  $pidValue = (Get-Content -LiteralPath $PidPath -ErrorAction SilentlyContinue | Select-Object -First 1)
  if (-not $pidValue) {
    $result.note = "pid file empty"
    Remove-Item -LiteralPath $PidPath -Force -ErrorAction SilentlyContinue
    return $result
  }
  $result.pid = $pidValue
  try {
    $proc = Get-Process -Id ([int]$pidValue) -ErrorAction Stop
    $children = @()
    $queue = @([int]$pidValue)
    while ($queue.Count -gt 0) {
      $parent = $queue[0]
      if ($queue.Count -eq 1) {
        $queue = @()
      } else {
        $queue = $queue[1..($queue.Count - 1)]
      }
      $found = Get-CimInstance Win32_Process -Filter "ParentProcessId=$parent" -ErrorAction SilentlyContinue
      foreach ($child in $found) {
        $children += [int]$child.ProcessId
        $queue += [int]$child.ProcessId
      }
    }
    foreach ($childPid in ($children | Sort-Object -Descending -Unique)) {
      try {
        Stop-Process -Id $childPid -Force -ErrorAction Stop
        $result.stopped_pids += "$childPid"
      } catch {
        $result.stopped_pids += "${childPid}:not-running"
      }
    }
    Stop-Process -Id $proc.Id -Force -ErrorAction Stop
    $result.stopped_pids += "$($proc.Id)"
    $result.stopped = $true
    $result.note = "stopped PID $pidValue ($($proc.ProcessName)) and recorded descendants"
    Write-Host "${Name}: stopped PID $pidValue"
  } catch {
    $result.note = "process was not running: $($_.Exception.Message)"
    Write-Host "${Name}: process was not running."
  }
  Remove-Item -LiteralPath $PidPath -Force -ErrorAction SilentlyContinue
  return $result
}

$summary = [ordered]@{
  timestamp = (Get-Date).ToString("o")
  stopped = @(
    (Stop-DemoPid $FrontendPid "frontend"),
    (Stop-DemoPid $BackendPid "backend")
  )
}

$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $EvidenceDir "stop_demo_state.json") -Encoding UTF8
Write-Host "DEMO STOP: DONE"
