@echo off
setlocal enabledelayedexpansion
set "ROOT=%~dp0"
set "DIST=%ROOT%dist"
set "EXE=%DIST%\MeetingAssistant\MeetingAssistant.exe"
set "SINGLE=%DIST%\MeetingAssistant.exe"
set "ENV=%ROOT%.env"

if exist "%EXE%" goto launch
if exist "%SINGLE%" goto launch_single

echo Release build not found. Please run build.ps1 first.
pause
exit /b 1

:launch
if not exist "%ENV%" (
    echo Missing .env configuration.
    echo Copy .env.example to .env in the release folder and fill in your API keys.
    pause
    exit /b 1
)
copy /Y "%ENV%" "%DIST%\MeetingAssistant\.env" >nul
start "" "%EXE%"
exit /b 0

:launch_single
if not exist "%ENV%" (
    echo Missing .env configuration.
    echo Copy .env.example to .env in the release folder and fill in your API keys.
    pause
    exit /b 1
)
copy /Y "%ENV%" "%DIST%\.env" >nul
start "" "%SINGLE%"
exit /b 0
