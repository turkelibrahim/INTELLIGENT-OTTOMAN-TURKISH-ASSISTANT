param(
    [string]$Url = "http://127.0.0.1:8765"
)

$ErrorActionPreference = "Stop"

try {
    $live = Invoke-RestMethod -Uri "$Url/health/live" -TimeoutSec 2
    $ready = Invoke-RestMethod -Uri "$Url/health/ready" -TimeoutSec 5
    [PSCustomObject]@{
        status = "READY"
        live = $live.status
        model_loaded = $ready.model_loaded
        model_load_count = $ready.model_load_count
        request_count = $ready.request_count
        device = $ready.device
        cuda_available = $ready.cuda_available
        model_path = $ready.model_path
    } | ConvertTo-Json -Depth 4
    exit 0
}
catch {
    [PSCustomObject]@{
        status = "UNAVAILABLE"
        error = $_.Exception.Message
    } | ConvertTo-Json -Depth 4
    exit 1
}
