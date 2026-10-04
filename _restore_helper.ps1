# Reads full transcript and extracts file contents from VIEW_FILE steps
$transcriptPath = "C:\Users\ibrah\.gemini\antigravity-ide\brain\332de882-18b6-41d5-abab-1248ab0bb3b7\.system_generated\logs\transcript_full.jsonl"
$lines = Get-Content $transcriptPath

$targetSteps = @(8, 9, 10, 11)  # Steps for the bat files that were viewed before deletion

foreach ($i in $targetSteps) {
    $json = $lines[$i] | ConvertFrom-Json
    $content = $json.content
    # Extract file path
    if ($content -match 'File Path: `file:///(.+?)`') {
        $filePath = [System.Uri]::UnescapeDataString($matches[1])
        Write-Output "=========================================="
        Write-Output "STEP $i - FILE: $filePath"
        Write-Output "=========================================="
        Write-Output $content
        Write-Output ""
    }
}
