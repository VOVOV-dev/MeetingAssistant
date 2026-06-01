param(
    [switch]$OneFile
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host 'PyInstaller not found, installing...'
    python -m pip install --upgrade pyinstaller
}

$baseArgs = @(
    'main.py',
    '--name', 'MeetingAssistant',
    '--noconfirm',
    '--clean',
    '--windowed'
)

if ($OneFile) {
    $baseArgs += '--onefile'
} else {
    $baseArgs += '--onedir'
}

# Collect Qt and app dependencies so the packaged app can run on machines without Python.
$baseArgs += @(
    '--collect-all', 'PyQt6',
    '--collect-all', 'markdown',
    '--collect-all', 'moviepy',
    '--collect-all', 'openai',
    '--collect-all', 'dashscope'
)

# Ensure imageio and its ffmpeg plugin metadata and data are included
$baseArgs += @(
    '--collect-data', 'imageio',
    '--collect-data', 'imageio',
    '--collect-data', 'imageio_ffmpeg',
    '--copy-metadata', 'imageio',
    '--copy-metadata', 'imageio-ffmpeg'
)

python -m PyInstaller @baseArgs
