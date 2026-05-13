# Net Monitor v5 - Installer
# Run via INSTALL.bat

$Host.UI.RawUI.WindowTitle = "Net Monitor v5 Setup"
$ErrorActionPreference = "Continue"

Get-ChildItem -Path $PSScriptRoot -ErrorAction SilentlyContinue | ForEach-Object {
    Unblock-File -Path $_.FullName -ErrorAction SilentlyContinue
}

cls
Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host "      Net Monitor v5  |  Auto Installer      " -ForegroundColor Cyan
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""

$sourceScript = Join-Path $PSScriptRoot "net_monitor.py"
if (-not (Test-Path $sourceScript)) {
    Write-Host "  ERROR: net_monitor.py not found." -ForegroundColor Red
    Write-Host "  File should be in: $PSScriptRoot" -ForegroundColor Red
    Write-Host ""
    Read-Host "  Press Enter to exit"
    exit 1
}

# --- 1. Find or install Python ---
Write-Host "  [1/5]  Locating Python..." -ForegroundColor Yellow

$pythonExe = $null

try {
    $p = Get-Command python -ErrorAction SilentlyContinue
    if ($p) { $pythonExe = $p.Source }
} catch {}

if (-not $pythonExe) {
    $searchPaths = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python"),
        "C:\Python312",
        "C:\Python311",
        "C:\Python310",
        "C:\Program Files\Python312",
        "C:\Program Files\Python311"
    )
    foreach ($base in $searchPaths) {
        if (Test-Path $base) {
            $found = Get-ChildItem -Path $base -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) { $pythonExe = $found.FullName; break }
        }
    }
}

if (-not $pythonExe) {
    Write-Host "         Not found. Downloading Python 3.12..." -ForegroundColor Yellow
    $installer = Join-Path $env:TEMP "python_installer.exe"
    try {
        Invoke-WebRequest "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe" -OutFile $installer -UseBasicParsing
    } catch {
        Write-Host ""
        Write-Host "  ERROR: Download failed. Check internet and try again." -ForegroundColor Red
        Read-Host "  Press Enter to exit"
        exit 1
    }
    Write-Host "         Installing silently - please wait..." -ForegroundColor Yellow
    Start-Process $installer -ArgumentList "/quiet","InstallAllUsers=0","PrependPath=1","Include_test=0" -Wait
    Remove-Item $installer -Force -ErrorAction SilentlyContinue

    $found = Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA "Programs\Python") -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $pythonExe = $found.FullName }
}

if (-not $pythonExe) {
    Write-Host ""
    Write-Host "  ERROR: Python not found after install." -ForegroundColor Red
    Write-Host "  Install manually from python.org then re-run." -ForegroundColor Red
    Read-Host "  Press Enter to exit"
    exit 1
}

Write-Host "         OK: $pythonExe" -ForegroundColor Green
$pythonDir  = Split-Path $pythonExe
$pythonwExe = Join-Path $pythonDir "pythonw.exe"
if (-not (Test-Path $pythonwExe)) { $pythonwExe = $pythonExe }

# --- 2. Copy script ---
Write-Host ""
Write-Host "  [2/5]  Copying files..." -ForegroundColor Yellow

$dest   = Join-Path $env:LOCALAPPDATA "NetMonitor"
$script = Join-Path $dest "net_monitor.py"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -Path $sourceScript -Destination $script -Force
Write-Host "         Saved to: $dest" -ForegroundColor Green

# --- 3. Install packages ---
Write-Host ""
Write-Host "  [3/5]  Installing packages..." -ForegroundColor Yellow
& $pythonExe -m pip install psutil plyer pystray pillow --quiet --no-warn-script-location 2>&1 | Out-Null
Write-Host "         psutil, plyer, pystray, pillow installed." -ForegroundColor Green

# --- 4. Copy config if needed ---
Write-Host ""
Write-Host "  [4/5]  Setting up configuration..." -ForegroundColor Yellow
$configFile = Join-Path $dest "net_monitor_config.json"
if (-not (Test-Path $configFile)) {
    $defaultConfig = @{
        window_x = $null
        window_y = $null
        mini_mode = $false
        transparency = 0.95
    }
    $defaultConfig | ConvertTo-Json | Set-Content -Path $configFile -Encoding UTF8 -Force
    Write-Host "         Config file created." -ForegroundColor Green
} else {
    Write-Host "         Config file exists (preserved)." -ForegroundColor Green
}

# --- 5. Startup shortcut ---
Write-Host ""
Write-Host "  [5/5]  Adding to Windows startup..." -ForegroundColor Yellow

$startupDir = [Environment]::GetFolderPath("Startup")
$lnkPath    = Join-Path $startupDir "NetMonitor.lnk"

try {
    $wsh = New-Object -ComObject WScript.Shell
    $lnk = $wsh.CreateShortcut($lnkPath)
    $lnk.TargetPath       = $pythonwExe
    $lnk.Arguments        = "`"$script`""
    $lnk.WorkingDirectory = $dest
    $lnk.WindowStyle      = 7
    $lnk.Description      = "Net Monitor v5"
    $lnk.Save()
    Write-Host "         Startup shortcut created." -ForegroundColor Green
} catch {
    Write-Host "         Could not create startup shortcut (non-critical)." -ForegroundColor Yellow
}

# --- Launch ---
Write-Host ""
Write-Host "  Launching Net Monitor..." -ForegroundColor Cyan
Start-Process $pythonwExe -ArgumentList "`"$script`""
Start-Sleep -Seconds 3

$running = Get-Process pythonw -ErrorAction SilentlyContinue
if (-not $running) {
    Write-Host ""
    Write-Host "  Widget did not start - opening with console to show error..." -ForegroundColor Yellow
    Start-Process $pythonExe -ArgumentList "`"$script`""
    Start-Sleep -Seconds 4
}

Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "     All done! Net Monitor v5 installed" -ForegroundColor Green
Write-Host ""
Write-Host "     Features:" -ForegroundColor Cyan
Write-Host "     • Always visible - stays on top when switching tabs" -ForegroundColor White
Write-Host "     • Fixed size - no resize grip" -ForegroundColor White
Write-Host "     • Position saved - returns to exact spot on restart" -ForegroundColor White
Write-Host "     • System tray - access from tray icon" -ForegroundColor White
Write-Host "     • Mini mode - click arrow to hide/show speeds" -ForegroundColor White
Write-Host ""
Write-Host "     Controls:" -ForegroundColor Cyan
Write-Host "     • Drag:     Move the widget around" -ForegroundColor White
Write-Host "     • Arrow:    Toggle between full/mini view" -ForegroundColor White
Write-Host "     • Tray:     Right-click tray icon for menu" -ForegroundColor White
Write-Host "     • Right:    Right-click widget for quick exit" -ForegroundColor White
Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "  Press Enter to close this window"
