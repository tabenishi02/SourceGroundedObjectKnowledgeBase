[CmdletBinding()]
param(
    [string]$TaskName = "Qdrant",

    [string]$TaskPath = "\SGOKB\",

    [string]$ReadyUrl = "http://127.0.0.1:6333/readyz",

    [ValidateRange(1, 3600)]
    [int]$ReadyTimeoutSeconds = 120,

    [string]$ExpectedQdrantExe = ""
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

if ($task.Triggers.Count -lt 1) {
    throw "Scheduled task has no trigger: $normalizedTaskPath$TaskName"
}
$logonTrigger = $task.Triggers | Where-Object { $_.CimClass.CimClassName -eq "MSFT_TaskLogonTrigger" }
if ($null -eq $logonTrigger) {
    throw "Scheduled task does not contain an AtLogOn trigger: $normalizedTaskPath$TaskName"
}
if ($task.Actions.Count -ne 1) {
    throw "Scheduled task must have exactly one direct Qdrant action. Found $($task.Actions.Count)."
}
if ($task.Settings.MultipleInstances -ne "IgnoreNew") {
    throw "Scheduled task MultipleInstances must be IgnoreNew. Found $($task.Settings.MultipleInstances)."
}
if ($task.Settings.RestartCount -lt 1) {
    throw "Scheduled task must enable restart-on-failure."
}
$restartInterval = [string]$task.Settings.RestartInterval
if ([string]::IsNullOrWhiteSpace($restartInterval)) {
    throw "Scheduled task must configure a restart interval."
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
    schema_version = "sgokb.qdrant-windows-autostart-check/1.0"
    task_path = "$normalizedTaskPath$TaskName"
    task_state = [string]$task.State
    executable = [string]$action.Execute
    arguments = [string]$action.Arguments
    working_directory = [string]$action.WorkingDirectory
    restart_count = [int]$task.Settings.RestartCount
    restart_interval = $restartInterval
    last_run_time = $taskInfo.LastRunTime.ToString("o")
    last_task_result = [int64]$taskInfo.LastTaskResult
    ready_url = $ReadyUrl
    ready_status = [int]$response.StatusCode
}

$result | ConvertTo-Json -Depth 4
