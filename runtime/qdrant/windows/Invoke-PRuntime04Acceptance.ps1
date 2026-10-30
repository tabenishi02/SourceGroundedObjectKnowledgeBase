[CmdletBinding()]
param(
    [ValidateSet("Observe", "PrepareReboot", "VerifyAfterLogin", "ExerciseUnexpectedStop")]
    [string]$Mode = "Observe",

    [ValidateRange(10, 900)]
    [int]$TimeoutSeconds = 180,

    [ValidateRange(1, 30)]
    [int]$PollSeconds = 2,

    [string]$ReceiptPath = (Join-Path $env:TEMP "sgokb-p-runtime-04-pre-reboot.json"),

    [string]$ReadyUri = "http://127.0.0.1:6333/readyz",

    [switch]$AsJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = [System.IO.Path]::GetFullPath((Join-Path $ScriptRoot "..\compose.yaml"))

function Invoke-DockerCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [switch]$AllowFailure
    )

    $output = & docker @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $text = ($output | ForEach-Object { [string]$_ }) -join "`n"
    if (($exitCode -ne 0) -and -not $AllowFailure) {
        throw "docker $($Arguments -join ' ') failed with exit code $exitCode: $text"
    }
    return [pscustomobject]@{
        ExitCode = $exitCode
        Output = $text.Trim()
    }
}

function Assert-WindowsReferenceEnvironment {
    if ($env:OS -ne "Windows_NT") {
        throw "P-RUNTIME-04 acceptance requires the supported Windows reference environment."
    }
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker CLI was not found. Install Docker Desktop before running P-RUNTIME-04 acceptance."
    }
    if (-not (Test-Path -LiteralPath $ComposeFile)) {
        throw "Compose file not found: $ComposeFile"
    }
}

function Get-BootTimeUtc {
    $os = Get-CimInstance Win32_OperatingSystem
    return ([DateTime]$os.LastBootUpTime).ToUniversalTime()
}

function Get-DockerDesktopStatus {
    $result = Invoke-DockerCommand -Arguments @("desktop", "status") -AllowFailure
    return [pscustomobject]@{
        available = ($result.ExitCode -eq 0)
        text = $result.Output
    }
}

function Wait-DockerEngine {
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        $probe = Invoke-DockerCommand -Arguments @("version", "--format", "{{.Server.Version}}") -AllowFailure
        if (($probe.ExitCode -eq 0) -and -not [string]::IsNullOrWhiteSpace($probe.Output)) {
            return $probe.Output.Trim()
        }
        Start-Sleep -Seconds $PollSeconds
    } while ([DateTime]::UtcNow -lt $deadline)

    $desktop = Get-DockerDesktopStatus
    throw "Docker Engine did not become ready within $TimeoutSeconds seconds. Docker Desktop status: $($desktop.text)"
}

function Get-QdrantContainerId {
    $probe = Invoke-DockerCommand -Arguments @("compose", "-f", $ComposeFile, "ps", "-q", "qdrant") -AllowFailure
    if ($probe.ExitCode -ne 0) {
        return ""
    }
    return $probe.Output.Trim()
}

function Get-QdrantContainerInfo {
    param([Parameter(Mandatory = $true)][string]$ContainerId)

    $inspect = Invoke-DockerCommand -Arguments @("inspect", $ContainerId)
    $record = ($inspect.Output | ConvertFrom-Json)[0]
    $health = $null
    if (($null -ne $record.State) -and ($record.State.PSObject.Properties.Name -contains "Health")) {
        if ($null -ne $record.State.Health) {
            $health = [string]$record.State.Health.Status
        }
    }
    $mountNames = @()
    foreach ($mount in @($record.Mounts)) {
        if ($mount.Type -eq "volume") {
            $mountNames += [string]$mount.Name
        }
    }
    return [pscustomobject]@{
        container_id = [string]$record.Id
        image = [string]$record.Config.Image
        status = [string]$record.State.Status
        health = $health
        started_at = [string]$record.State.StartedAt
        restart_count = [int]$record.RestartCount
        restart_policy = [string]$record.HostConfig.RestartPolicy.Name
        volume_names = @($mountNames)
    }
}

function Test-QdrantReady {
    try {
        $response = Invoke-WebRequest -Uri $ReadyUri -UseBasicParsing -TimeoutSec 5
        return ($response.StatusCode -eq 200)
    }
    catch {
        return $false
    }
}

function Wait-QdrantReady {
    $engineVersion = Wait-DockerEngine
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        $containerId = Get-QdrantContainerId
        if (-not [string]::IsNullOrWhiteSpace($containerId)) {
            $info = Get-QdrantContainerInfo -ContainerId $containerId
            if (($info.status -eq "running") -and (Test-QdrantReady)) {
                if ($info.restart_policy -ne "unless-stopped") {
                    throw "Qdrant restart policy is '$($info.restart_policy)', expected 'unless-stopped'."
                }
                if ($info.image -ne "qdrant/qdrant:v1.20.0") {
                    throw "Qdrant image is '$($info.image)', expected 'qdrant/qdrant:v1.20.0'."
                }
                if ($info.volume_names -notcontains "sgokb_qdrant_storage") {
                    throw "Qdrant container is not using the accepted named volume sgokb_qdrant_storage."
                }
                return [pscustomobject]@{
                    engine_version = $engineVersion
                    container = $info
                    ready_uri = $ReadyUri
                    ready = $true
                }
            }
        }
        Start-Sleep -Seconds $PollSeconds
    } while ([DateTime]::UtcNow -lt $deadline)

    $containerId = Get-QdrantContainerId
    throw "Qdrant did not become ready within $TimeoutSeconds seconds. Container id: '$containerId'."
}

function New-Observation {
    param([string]$ObservationMode)

    $runtime = Wait-QdrantReady
    $desktop = Get-DockerDesktopStatus
    $appData = [Environment]::GetFolderPath([Environment+SpecialFolder]::ApplicationData)
    $settingsPath = Join-Path $appData "Docker\settings-store.json"
    return [pscustomobject]@{
        schema_version = "sgokb.p-runtime-04-acceptance/1.0"
        mode = $ObservationMode
        observed_at_utc = [DateTime]::UtcNow.ToString("o")
        boot_time_utc = (Get-BootTimeUtc).ToString("o")
        compose_file = $ComposeFile
        docker_desktop = $desktop
        docker_desktop_settings_path = $settingsPath
        docker_desktop_settings_present = (Test-Path -LiteralPath $settingsPath)
        runtime = $runtime
        observer_only = $true
        lifecycle_start_command_issued = $false
    }
}

function Invoke-PrepareReboot {
    $observation = New-Observation -ObservationMode "PrepareReboot"
    $receiptDirectory = Split-Path -Parent $ReceiptPath
    if (-not [string]::IsNullOrWhiteSpace($receiptDirectory)) {
        New-Item -ItemType Directory -Force -Path $receiptDirectory | Out-Null
    }
    $observation | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ReceiptPath -Encoding UTF8
    return [pscustomobject]@{
        result = "prepared"
        receipt_path = $ReceiptPath
        pre_reboot = $observation
        instruction = "Reboot Windows normally. After sign-in, do not manually start Docker Desktop or Qdrant; run this script with -Mode VerifyAfterLogin."
    }
}

function Invoke-VerifyAfterLogin {
    if (-not (Test-Path -LiteralPath $ReceiptPath)) {
        throw "Pre-reboot receipt not found: $ReceiptPath. Run -Mode PrepareReboot before rebooting."
    }
    $before = Get-Content -LiteralPath $ReceiptPath -Raw | ConvertFrom-Json
    $currentBoot = Get-BootTimeUtc
    $previousBoot = [DateTime]::Parse([string]$before.boot_time_utc).ToUniversalTime()
    if ($currentBoot -le $previousBoot) {
        throw "A newer Windows boot was not observed. PrepareReboot boot=$($previousBoot.ToString('o')); current boot=$($currentBoot.ToString('o'))."
    }
    $observation = New-Observation -ObservationMode "VerifyAfterLogin"
    return [pscustomobject]@{
        result = "post_login_ready"
        reboot_observed = $true
        previous_boot_time_utc = $previousBoot.ToString("o")
        current_boot_time_utc = $currentBoot.ToString("o")
        manual_runtime_start_command_required = $false
        post_login = $observation
    }
}

function Invoke-UnexpectedStopExercise {
    $before = New-Observation -ObservationMode "UnexpectedStopBefore"
    $containerId = [string]$before.runtime.container.container_id
    $startedAt = [DateTime]::Parse([string]$before.runtime.container.started_at).ToUniversalTime()
    $ageSeconds = ([DateTime]::UtcNow - $startedAt).TotalSeconds
    if ($ageSeconds -lt 10) {
        Start-Sleep -Seconds ([int][Math]::Ceiling(10 - $ageSeconds))
    }

    $kill = Invoke-DockerCommand -Arguments @("kill", $containerId)
    $after = New-Observation -ObservationMode "UnexpectedStopAfter"
    if ([string]$after.runtime.container.container_id -ne $containerId) {
        throw "Unexpected-stop recovery changed the Qdrant container identity."
    }
    if ([int]$after.runtime.container.restart_count -le [int]$before.runtime.container.restart_count) {
        throw "Qdrant restart count did not increase after docker kill."
    }
    return [pscustomobject]@{
        result = "unexpected_stop_recovered"
        explicit_test_action = "docker kill"
        kill_output = $kill.Output
        start_command_issued_after_kill = $false
        before = $before
        after = $after
    }
}

Assert-WindowsReferenceEnvironment

switch ($Mode) {
    "Observe" { $result = New-Observation -ObservationMode "Observe" }
    "PrepareReboot" { $result = Invoke-PrepareReboot }
    "VerifyAfterLogin" { $result = Invoke-VerifyAfterLogin }
    "ExerciseUnexpectedStop" { $result = Invoke-UnexpectedStopExercise }
    default { throw "Unsupported mode: $Mode" }
}

if ($AsJson) {
    $result | ConvertTo-Json -Depth 12
}
else {
    $result
}
