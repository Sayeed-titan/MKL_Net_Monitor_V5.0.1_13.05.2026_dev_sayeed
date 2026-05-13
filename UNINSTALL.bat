@echo off
title Net Monitor - Uninstaller
cls
echo.
echo   ============================================
echo        Net Monitor  ^|  Uninstaller
echo   ============================================
echo.
echo   This will stop Net Monitor and remove all files.
echo.
set /p CONFIRM=   Type Y to confirm uninstall: 
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo   Cancelled.
    pause
    exit /b
)

echo.
echo   Stopping Net Monitor...
powershell -NoProfile -Command ^
    "Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like '*net_monitor*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
echo   Done.

echo.
echo   Removing startup shortcut...
set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\NetMonitor.lnk"
if exist "%LNK%" (
    del /Q "%LNK%"
    echo   Done.
) else (
    echo   Not found (already removed).
)

echo.
echo   Removing app files...
set "DEST=%LOCALAPPDATA%\NetMonitor"
if exist "%DEST%" (
    rmdir /S /Q "%DEST%"
    echo   Done.
) else (
    echo   Not found (already removed).
)

echo.
echo   ============================================
echo      Net Monitor has been uninstalled.
echo      Python and pip packages are kept.
echo   ============================================
echo.
pause
