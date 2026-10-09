[CmdletBinding()]
param(
    [ValidateSet('Install', 'Uninstall', 'Status', 'Prepare')][string]$Action = 'Status',
    [ValidatePattern('^[a-p]{32}$')][string]$ExtensionId,
    [string]$PythonPath
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$localDir = Join-Path $projectRoot '.local'
$manifestPath = Join-Path $localDir 'host-manifest.json'
$keyPath = 'HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.sgokb.web_page_capture'
if ($Action -eq 'Status') {
    $registered = Test-Path -LiteralPath $keyPath
    [pscustomobject]@{ Registered = $registered; ManifestExists = (Test-Path -LiteralPath $manifestPath); LauncherExists = (Test-Path -LiteralPath (Join-Path $localDir 'host.exe')) }
    if ($registered) { (Get-Item -LiteralPath $keyPath).GetValue('') }
    return
}
if ($Action -eq 'Uninstall') {
    if (Test-Path -LiteralPath $keyPath) {
        if ((Get-Item -LiteralPath $keyPath).GetValue('') -ne $manifestPath) { throw '別の登録先を参照しています。削除しません。' }
        Remove-Item -LiteralPath $keyPath
    }
    Write-Output '登録を解除しました。Captureと.localのファイルは保持します。'
    return
}
if (-not $ExtensionId) { throw 'chrome://extensions のExtension IDを -ExtensionId に指定してください。' }
if (-not $PythonPath) { $PythonPath = (& python -c 'import sys; print(sys.executable)'); if ($LASTEXITCODE -ne 0) { throw 'Pythonが見つかりません。' } }
$PythonPath = (Resolve-Path -LiteralPath $PythonPath).Path
& $PythonPath -I -c 'import sys; assert sys.version_info >= (3, 10)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.10以降が必要です。' }
if ($Action -eq 'Install' -and (Test-Path -LiteralPath $keyPath) -and (Get-Item -LiteralPath $keyPath).GetValue('') -ne $manifestPath) { throw '既存の別Host登録は上書きしません。' }
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) { throw 'Windows .NET Framework C# compilerが必要です。' }
New-Item -ItemType Directory -Path $localDir -Force | Out-Null
$hostPath = Join-Path $PSScriptRoot 'host.py'
$source = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'Launcher.cs')).Replace('__PYTHON__', $PythonPath.Replace('"', '""')).Replace('__HOST__', $hostPath.Replace('"', '""'))
$sourcePath = Join-Path $localDir 'Launcher.cs'
[IO.File]::WriteAllText($sourcePath, $source, (New-Object Text.UTF8Encoding($false)))
$exePath = Join-Path $localDir 'host.exe'
& $compiler /nologo /target:exe "/out:$exePath" $sourcePath
if ($LASTEXITCODE -ne 0) { throw 'Native Host launcherのコンパイルに失敗しました。' }
$manifest = @{name = 'com.sgokb.web_page_capture'; description = 'Web Page Capture storage bridge'; path = $exePath; type = 'stdio'; allowed_origins = @("chrome-extension://$ExtensionId/")}
[IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json), (New-Object Text.UTF8Encoding($false)))
if ($Action -eq 'Install') {
    New-Item -Path $keyPath -Force | Out-Null
    Set-Item -LiteralPath $keyPath -Value $manifestPath
    Write-Output '現在ユーザーのChrome Native Hostを登録しました。'
} else { Write-Output 'Hostを準備しました。Registryは変更していません。' }
