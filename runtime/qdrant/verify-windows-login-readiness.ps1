[CmdletBinding()]
param(
    [ValidateRange(10, 900)]
    [int]$TimeoutSeconds = 180,

    [ValidateRange(1, 30)]
    [int]$PollIntervalSeconds = 2
)

$ErrorActionPreference = "Stop"

$ComposePath = Join-Path $PSScriptRoot "compose.yaml"
$ProjectName = "sgokb-qdrant"
$ServiceName = "qdrant"
$ReadyUri = "http://127.0.0.1:6333/readyz"
$Deadline = (Get-Date).AddSeconds($TimeoutSeconds)

function Invoke-DockerText {
    param([Parameter(Mandatory)][string[]]$Arguments)

    $output = & docker @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "docker $($Arguments -join ' ') failed: $($output -join [Environment]::NewLine)"
    }
    return (($output | Out-String).Trim())
}

function Wait-DockerEngine {
    while ((Get-Date) -lt $Deadline) {
        try {
            $version = Invoke-DockerText -Arguments @("info", "--format", "{{.ServerVersion}}")
            if (-not [string]::IsNullOrWhiteSpace($version)) {
                return $version
            }
        }
        catch {
            Start-Sleep -Seconds $PollIntervalSeconds
        }
    }

    throw "Docker Engine did not become ready within $TimeoutSeconds seconds. Confirm Docker Desktop Settings > General > 'Start Docker Desktop when you sign in to your computer' is enabled and inspect Docker Desktop diagnostics."
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "docker CLI was not found. Install the supported Docker Desktop prerequisite before running this observer."
}

if (-not (Test-Path -LiteralPath $ComposePath)) {
    throw "Repository-owned Compose definition was not found: $ComposePath"
}

$DockerServerVersion = Wait-DockerEngine

$ContainerId = Invoke-DockerText -Arguments @(
    "compose", "-f", $ComposePath, "-p", $ProjectName, "ps", "-a", "-q", $ServiceName
)
if ([string]::IsNullOrWhiteSpace($ContainerId)) {
    throw "The persisted SGOKB Qdrant container does not exist. Perform the one-time P-RUNTIME-02 initialization with 'docker compose up -d --wait --wait-timeout 120'. This probe intentionally does not create or start runtime state."
}

$RestartPolicy = Invoke-DockerText -Arguments @(
    "inspect", "--format", "{{.HostConfig.RestartPolicy.Name}}", $ContainerId
)
if ($RestartPolicy -ne "unless-stopped") {
    throw "Unexpected Qdrant restart policy '$RestartPolicy'; expected 'unless-stopped' from the repository-owned Compose contract."
}

$LastState = "unknown"
$LastHealth = "unknown"
$LastReadyError = $null

while ((Get-Date) -lt $Deadline) {
    try {
        $LastState = Invoke-DockerText -Arguments @(
            "inspect", "--format", "{{.State.Status}}", $ContainerId
        )
        $LastHealth = Invoke-DockerText -Arguments @(
            "inspect", "--format", "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}", $ContainerId
        )

        $response = Invoke-WebRequest -Uri $ReadyUri -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -eq 200) {
            [pscustomobject]@{
                schema = "sgokb.windows-login-readiness/1.0"
                ready = $true
                docker_server_version = $DockerServerVersion
                compose_project = $ProjectName
                service = $ServiceName
                container_id = $ContainerId
                restart_policy = $RestartPolicy
                container_state = $LastState
                container_health = $LastHealth
                readiness_uri = $ReadyUri
                readiness_status = $response.StatusCode
                observed_at = (Get-Date).ToUniversalTime().ToString("o")
                lifecycle_owner = "external"
            } | ConvertTo-Json -Depth 3
            exit 0
        }
    }
    catch {
        $LastReadyError = $_.Exception.Message
    }

    Start-Sleep -Seconds $PollIntervalSeconds
}

throw "Qdrant did not reach $ReadyUri within $TimeoutSeconds seconds after Docker Engine became available. Last container state='$LastState', health='$LastHealth', readiness error='$LastReadyError'. Inspect 'docker compose ps -a' and 'docker compose logs --tail 200 qdrant'. If the service was intentionally stopped, 'unless-stopped' requires an explicit operator start; that state is not an auto-start failure."
