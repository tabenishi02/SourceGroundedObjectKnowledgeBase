[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$QdrantExe,

    [string]$QdrantArguments = "",

    [string]$WorkingDirectory = "",

    [string]$TaskName = "Qdrant",

    [string]$TaskPath = "\SGOKB\",

    [ValidateRange(1, 255)]
    [int]$RestartCount = 10,

    [ValidateRange(60, 2678400)]
    [int]$RestartIntervalSeconds = 60,

    [switch]$StartNow,

    [ValidateRange(1, 3600)]
    [int]$ReadyTimeoutSeconds = 120,

    [string]$ReadyUrl = "http://127.0.0.1:6333/readyz"
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

function Ensure-ScheduledTaskFolder {
    param([Parameter(Mandatory = $true)][string]$Path)

    if ($Path -eq "\") {
        return
    }

    $service = New-Object -ComObject "Schedule.Service"
    $service.Connect()
    $currentFolder = $service.GetFolder("\")
    $currentPath = ""

    foreach ($segment in $Path.Trim("\").Split("\")) {
        if ([string]::IsNullOrWhiteSpace($segment)) {
            continue
        }

        $currentPath = "$currentPath\$segment"
        try {
            $currentFolder = $service.GetFolder($currentPath)
        }
        catch {
            $currentFolder = $currentFolder.CreateFolder($segment)
        }
    }
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
                return
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

$resolvedExe = (Resolve-Path -LiteralPath $QdrantExe).Path
if (-not (Test-Path -LiteralPath $resolvedExe -PathType Leaf)) {
    throw "Qdrant executable is not a file: $resolvedExe"
}
if ([IO.Path]::GetExtension($resolvedExe) -ine ".exe") {
    throw "Qdrant executable must be a Windows .exe file: $resolvedExe"
}

if ([string]::IsNullOrWhiteSpace($WorkingDirectory)) {
    $resolvedWorkingDirectory = Split-Path -Parent $resolvedExe
}
else {
    $resolvedWorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory).Path
}
if (-not (Test-Path -LiteralPath $resolvedWorkingDirectory -PathType Container)) {
    throw "Working directory does not exist: $resolvedWorkingDirectory"
}

$normalizedTaskPath = Get-NormalizedTaskPath -Path $TaskPath
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

Import-Module ScheduledTasks -ErrorAction Stop

$actionParameters = @{
    Execute = $resolvedExe
    WorkingDirectory = $resolvedWorkingDirectory
}
if (-not [string]::IsNullOrWhiteSpace($QdrantArguments)) {
    $actionParameters.Argument = $QdrantArguments
}
$action = New-ScheduledTaskAction @actionParameters
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
$principal = New-ScheduledTaskPrincipal `
    -UserId $currentUser `
    -LogonType Interactive `
    -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
    -RestartCount $RestartCount `
    -RestartInterval (New-TimeSpan -Seconds $RestartIntervalSeconds) `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

$task = New-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "SGOKB native Windows Qdrant runtime. Lifecycle owner: Windows Task Scheduler."

$target = "$normalizedTaskPath$TaskName"
if ($PSCmdlet.ShouldProcess($target, "Register native Qdrant auto-start task")) {
    Ensure-ScheduledTaskFolder -Path $normalizedTaskPath

    Register-ScheduledTask `
        -TaskName $TaskName `
        -TaskPath $normalizedTaskPath `
        -InputObject $task `
        -Force | Out-Null

    $registered = Get-ScheduledTask -TaskName $TaskName -TaskPath $normalizedTaskPath
    Write-Host "Registered $target for user $currentUser"
    Write-Host "Executable: $resolvedExe"
    Write-Host "Working directory: $resolvedWorkingDirectory"
    Write-Host "Restart policy: $RestartCount attempt(s), interval ${RestartIntervalSeconds}s"

    if ($StartNow) {
        if ($registered.State -ne "Running") {
            Start-ScheduledTask -TaskName $TaskName -TaskPath $normalizedTaskPath
        }
        Wait-QdrantReady -Url $ReadyUrl -TimeoutSeconds $ReadyTimeoutSeconds
        Write-Host "Qdrant ready: $ReadyUrl"
    }
}
