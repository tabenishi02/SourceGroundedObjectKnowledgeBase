[CmdletBinding()]
param(
    [string]$TaskName = "Qdrant",

    [string]$TaskPath = "\SGOKB\",

    [string]$ReadyUrl = "http://127.0.0.1:6333/readyz",

    [ValidateRange(1, 3600)]
    [int]$ReadyTimeoutSeconds = 120,

    [string]$ExpectedQdrantExe = "",

    [ValidateRange(60, 2678400)]
    [int]$ExpectedRecoveryIntervalSeconds = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-NormalizedTaskPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    $normalized = $Path.Trim()
    if (-not $normalized.StartsWith("\")) {
        $normalized = "\$normalized"
    }
    if (-not $normalized.EndsWith("\")) {
        $normalized = "$normalized\"
    }
    return $normalized
}

function Wait-QdrantReady {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $lastError = $null
    do {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                return $response
            }
            $lastError = "HTTP $($response.StatusCode)"
        }
        catch {
            $lastError = $_.Exception.Message
        }
        Start-Sleep -Seconds 2
    } while ([DateTime]::UtcNow -lt $deadline)

    throw "Qdrant did not become ready at '$Url' within $TimeoutSeconds seconds. Last error: $lastError"
}

Import-Module ScheduledTasks -ErrorAction Stop
$normalizedTaskPath = Get-NormalizedTaskPath -Path $TaskPath
$task = Get-ScheduledTask -TaskName $TaskName -TaskPath $normalizedTaskPath
$taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName -TaskPath $normalizedTaskPath

if ($task.Triggers.Count -ne 2) {
    throw "Scheduled task must contain exactly two triggers (AtLogOn + repeating recovery pulse). Found $($task.Triggers.Count)."
}
$logonTriggers = @($task.Triggers | Where-Object { $_.CimClass.CimClassName -eq "MSFT_TaskLogonTrigger" })
if ($logonTriggers.Count -ne 1) {
    throw "Scheduled task must contain exactly one AtLogOn trigger: $normalizedTaskPath$TaskName"
}
$recoveryTriggers = @($task.Triggers | Where-Object { $_.CimClass.CimClassName -eq "MSFT_TaskTimeTrigger" })
if ($recoveryTriggers.Count -ne 1) {
    throw "Scheduled task must contain exactly one repeating time trigger for crash recovery."
}
$recoveryTrigger = $recoveryTriggers[0]
$recoveryInterval = [string]$recoveryTrigger.Repetition.Interval
if ([string]::IsNullOrWhiteSpace($recoveryInterval)) {
    throw "Crash-recovery time trigger must configure a repetition interval."
}
$recoveryIntervalSeconds = [int][Math]::Round([Xml.XmlConvert]::ToTimeSpan($recoveryInterval).TotalSeconds)
if ($recoveryIntervalSeconds -ne $ExpectedRecoveryIntervalSeconds) {
    throw "Crash-recovery interval mismatch. Expected ${ExpectedRecoveryIntervalSeconds}s; found ${recoveryIntervalSeconds}s ($recoveryInterval)."
}
$recoveryDuration = [string]$recoveryTrigger.Repetition.Duration
if (-not [string]::IsNullOrWhiteSpace($recoveryDuration)) {
    throw "Crash-recovery repetition must be indefinite (no repetition duration). Found '$recoveryDuration'."
}

if ([string]$task.Principal.LogonType -ne "Interactive") {
    throw "Scheduled task principal must use Interactive logon. Found $($task.Principal.LogonType)."
}
if ($task.Actions.Count -ne 1) {
    throw "Scheduled task must have exactly one direct Qdrant action. Found $($task.Actions.Count)."
}
if ($task.Settings.MultipleInstances -ne "IgnoreNew") {
    throw "Scheduled task MultipleInstances must be IgnoreNew. Found $($task.Settings.MultipleInstances)."
}
if ($task.Settings.RestartCount -lt 1) {
    throw "Scheduled task must retain restart-on-failure as a start-failure fallback."
}
$restartInterval = [string]$task.Settings.RestartInterval
if ([string]::IsNullOrWhiteSpace($restartInterval)) {
    throw "Scheduled task must configure a restart-on-failure fallback interval."
}

$action = $task.Actions[0]
if (-not [string]::IsNullOrWhiteSpace($ExpectedQdrantExe)) {
    $expected = (Resolve-Path -LiteralPath $ExpectedQdrantExe).Path
    $actual = [IO.Path]::GetFullPath($action.Execute)
    if (-not [string]::Equals($expected, $actual, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Scheduled task executable mismatch. Expected '$expected'; found '$actual'."
    }
}

$response = Wait-QdrantReady -Url $ReadyUrl -TimeoutSeconds $ReadyTimeoutSeconds

$result = [ordered]@{
    schema_version = "sgokb.qdrant-windows-autostart-check/1.1"
    task_path = "$normalizedTaskPath$TaskName"
    task_state = [string]$task.State
    principal_logon_type = [string]$task.Principal.LogonType
    executable = [string]$action.Execute
    arguments = [string]$action.Arguments
    working_directory = [string]$action.WorkingDirectory
    trigger_count = [int]$task.Triggers.Count
    recovery_interval = $recoveryInterval
    recovery_interval_seconds = $recoveryIntervalSeconds
    recovery_start_boundary = [string]$recoveryTrigger.StartBoundary
    restart_count = [int]$task.Settings.RestartCount
    restart_interval = $restartInterval
    last_run_time = $taskInfo.LastRunTime.ToString("o")
    last_task_result = [int64]$taskInfo.LastTaskResult
    ready_url = $ReadyUrl
    ready_status = [int]$response.StatusCode
}

$result | ConvertTo-Json -Depth 4
