$ErrorActionPreference = 'Stop'

$ReleaseDir = $PSScriptRoot
$DistDir = Join-Path $ReleaseDir 'dist'
$ExePath = Join-Path $DistDir 'MeetingAssistant\MeetingAssistant.exe'
$SingleExePath = Join-Path $DistDir 'MeetingAssistant.exe'
$RootEnvPath = Join-Path $ReleaseDir '.env'

if (-not (Test-Path $ExePath) -and -not (Test-Path $SingleExePath)) {
    Write-Host 'Release build not found. Run .\build.ps1 first.'
    exit 1
}

if (-not (Test-Path $RootEnvPath)) {
    Write-Host 'Missing .env configuration.'
    Write-Host 'Copy .env.example to .env in the release folder and fill in your API keys.'
    exit 1
}

$Target = if (Test-Path $ExePath) { $ExePath } else { $SingleExePath }
$TargetDir = Split-Path $Target -Parent
Copy-Item $RootEnvPath (Join-Path $TargetDir '.env') -Force
Start-Process -FilePath $Target
