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
    # Prefer project virtualenv python if available
    $VenvPython = Join-Path $RootDir '.venv\Scripts\python.exe'
    if (Test-Path $VenvPython) {
        & $VenvPython -m pip install --upgrade pyinstaller
    } else {
        python -m pip install --upgrade pyinstaller
    }
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
    '--collect-all', 'PyQt6-WebEngine',
    '--collect-all', 'PyQt6-WebEngine-Qt6',
    '--collect-all', 'markdown',
    '--collect-all', 'moviepy',
    '--collect-all', 'openai',
    '--collect-all', 'dashscope'
)

# Ensure imageio and its ffmpeg plugin are collected; avoid copy-metadata which can fail
$baseArgs += @(
    '--collect-all', 'imageio',
    '--collect-all', 'imageio_ffmpeg'
)

# Use project's virtualenv python if available so local deps (PyQt6) are visible
$VenvPython = Join-Path $RootDir '.venv\Scripts\python.exe'
if (Test-Path $VenvPython) {
    & $VenvPython -m PyInstaller @baseArgs
} else {
    python -m PyInstaller @baseArgs
}

if (Test-Path (Join-Path $RootDir '.env.example')) {
    $TargetDir = if ($OneFile) { $DistDir } else { Join-Path $DistDir 'MeetingAssistant' }
    if (Test-Path $TargetDir) {
        Copy-Item (Join-Path $RootDir '.env.example') (Join-Path $TargetDir '.env.example') -Force
    }
}

# If project venv contains PyQt6 Qt6 runtime, copy it into the dist so Qt DLLs/plugins are available
$VenvQt = Join-Path $RootDir '.venv\Lib\site-packages\PyQt6\Qt6'
if (Test-Path $VenvQt) {
    $TargetDir = if ($OneFile) { $DistDir } else { Join-Path $DistDir 'MeetingAssistant' }
    if (Test-Path $TargetDir) {
        Write-Host "Copying Qt6 runtime from $VenvQt to $TargetDir\Qt6"
        $dest = Join-Path $TargetDir 'Qt6'
        if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
        Copy-Item $VenvQt $dest -Recurse -Force
        # Also copy Qt binaries into target root for easier DLL resolution
        $binSrc = Join-Path $VenvQt 'bin'
        if (Test-Path $binSrc) {
            Get-ChildItem $binSrc -Filter *.dll -File | ForEach-Object { Copy-Item $_.FullName -Destination $TargetDir -Force }
            # copy Qt WebEngine process exe
            $webProc = Join-Path $binSrc 'QtWebEngineProcess.exe'
            if (Test-Path $webProc) { Copy-Item $webProc -Destination $TargetDir -Force }
        }
    }
}

Write-Host ''
Write-Host 'Build complete.'
Write-Host ('Output path: {0}' -f $DistDir)
