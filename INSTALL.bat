@echo off
title Net Monitor - Installer
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "setup.ps1"
if %errorlevel% neq 0 (
    echo.
    echo   Something went wrong. Read the red message above.
    pause
)
