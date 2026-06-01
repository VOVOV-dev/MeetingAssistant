param(
    [switch]$OneFile,
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'

$ReleaseDir = $PSScriptRoot
$RootDir = (Resolve-Path (Join-Path $ReleaseDir '..')).Path
$BuildDir = Join-Path $ReleaseDir 'build'
$DistDir = Join-Path $ReleaseDir 'dist'
$SpecDir = Join-Path $ReleaseDir 'spec'

if ($Clean) {
    foreach ($path in @($BuildDir, $DistDir, $SpecDir)) {
        if (Test-Path $path) {
            Remove-Item $path -Recurse -Force
        }
    }
}

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host 'PyInstaller not found, installing...'
    python -m pip install --upgrade pyinstaller
}

$baseArgs = @(
    (Join-Path $RootDir 'main.py'),
    '--name', 'MeetingAssistant',
    '--noconfirm',
    '--clean',
    '--windowed',
    '--distpath', $DistDir,
    '--workpath', $BuildDir,
    '--specpath', $SpecDir
)

if ($OneFile) {
    $baseArgs += '--onefile'
} else {
    $baseArgs += '--onedir'
}

$baseArgs += @(
    '--collect-all', 'PyQt6',
    '--collect-all', 'markdown',
    '--collect-all', 'moviepy',
    '--collect-all', 'openai',
    '--collect-all', 'dashscope'
)

python -m PyInstaller @baseArgs

if (Test-Path (Join-Path $RootDir '.env.example')) {
    $TargetDir = if ($OneFile) { $DistDir } else { Join-Path $DistDir 'MeetingAssistant' }
    if (Test-Path $TargetDir) {
        Copy-Item (Join-Path $RootDir '.env.example') (Join-Path $TargetDir '.env.example') -Force
    }
}

Write-Host ''
Write-Host 'Build complete.'
Write-Host ('Output path: {0}' -f $DistDir)
