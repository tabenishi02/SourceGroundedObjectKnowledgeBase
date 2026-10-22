param(
    [string]$RunId = "",
    [string]$QdrantExe = ".local\qdrant-1.19.2\qdrant.exe",
    [int]$PointCount = 256,
    [int]$RepeatIndexed = 5
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

if ([string]::IsNullOrWhiteSpace($RunId)) {
    $stamp = Get-Date -Format "yyyyMMddTHHmmsszzz"
    $RunId = $stamp.Replace(":", "")
}

$RunRoot = Join-Path $RepoRoot ".local\n05d01\$RunId"
if (Test-Path -LiteralPath $RunRoot) {
    throw "Run root already exists: $RunRoot"
}
New-Item -ItemType Directory -Path $RunRoot -Force | Out-Null

$meta = [ordered]@{
    run_id = $RunId
    started_at = (Get-Date).ToString("o")
    git_head = (git rev-parse HEAD).Trim()
    origin_main = (git rev-parse origin/main).Trim()
    branch = (git branch --show-current).Trim()
    git_status = @((git status --porcelain))
    qdrant_exe = $QdrantExe
}
$meta | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $RunRoot "run-meta.json") -Encoding utf8

$python = (Get-Command python).Source
$tool = Join-Path $RepoRoot "benchmark\tools\n05d01_qdrant_storage_diagnosis.py"

# Probe the currently running Reference Workstation server without restarting it.
& $python $tool `
    --url "http://localhost:6333" `
    --http-port 6333 `
    --grpc-port 6334 `
    --point-count $PointCount `
    --repeat-indexed $RepeatIndexed `
    --storage-path (Join-Path $RepoRoot ".local\n04p06\qdrant") `
    --output (Join-Path $RunRoot "current-server.json") `
    *> (Join-Path $RunRoot "current-server.log")
$currentExit = $LASTEXITCODE

# Start a second native Qdrant instance with explicit absolute paths.
$qdrantPath = (Resolve-Path (Join-Path $RepoRoot $QdrantExe)).Path
$isolatedRoot = Join-Path $RunRoot "isolated-qdrant"
$storage = Join-Path $isolatedRoot "storage"
$snapshots = Join-Path $isolatedRoot "snapshots"
$temp = Join-Path $isolatedRoot "temp"
$config = Join-Path $isolatedRoot "config.yaml"
New-Item -ItemType Directory -Path $storage,$snapshots,$temp -Force | Out-Null

function As-QdrantPath([string]$Path) {
    return $Path.Replace("\", "/")
}

$configText = @"
log_level: INFO
storage:
  storage_path: "$(As-QdrantPath $storage)"
  snapshots_path: "$(As-QdrantPath $snapshots)"
  temp_path: "$(As-QdrantPath $temp)"
service:
  host: 127.0.0.1
  http_port: 6433
  grpc_port: 6434
telemetry_disabled: true
"@
$configText | Set-Content -LiteralPath $config -Encoding utf8

$stdout = Join-Path $RunRoot "isolated-qdrant.stdout.log"
$stderr = Join-Path $RunRoot "isolated-qdrant.stderr.log"
$env:RUST_BACKTRACE = "1"
$process = Start-Process `
    -FilePath $qdrantPath `
    -ArgumentList @("--config-path", $config) `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -PassThru

$isolatedReady = $false
try {
    for ($i = 0; $i -lt 60; $i++) {
        if ($process.HasExited) {
            break
        }
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:6433/" -TimeoutSec 2
            if ($null -ne $response) {
                $isolatedReady = $true
                break
            }
        } catch {
        }
        Start-Sleep -Milliseconds 500
    }

    if (-not $isolatedReady) {
        throw "Isolated Qdrant did not become ready; inspect isolated-qdrant logs."
    }

    & $python $tool `
        --url "http://localhost:6433" `
        --http-port 6433 `
        --grpc-port 6434 `
        --point-count $PointCount `
        --repeat-indexed $RepeatIndexed `
        --storage-path $storage `
        --output (Join-Path $RunRoot "isolated-server.json") `
        *> (Join-Path $RunRoot "isolated-server.log")
    $isolatedExit = $LASTEXITCODE
} finally {
    if ($null -ne $process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        Wait-Process -Id $process.Id -ErrorAction SilentlyContinue
    }
}

$summary = [ordered]@{
    schema_version = "sgokb.n05d01.runner-summary.v1"
    run_id = $RunId
    current_server_exit = $currentExit
    isolated_server_exit = $isolatedExit
    isolated_server_ready = $isolatedReady
    completed_at = (Get-Date).ToString("o")
    note = "Diagnostic exits are evidence signals, not N-05 performance PASS/FAIL."
}
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $RunRoot "summary.json") -Encoding utf8

Write-Output "N05D-01 evidence: $RunRoot"
Write-Output "Current server diagnostic exit: $currentExit"
Write-Output "Isolated server diagnostic exit: $isolatedExit"
