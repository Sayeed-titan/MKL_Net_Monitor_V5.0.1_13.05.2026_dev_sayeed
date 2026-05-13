# Net Monitor v5

A lightweight always-on-top Windows desktop widget that shows live internet speed and alerts you instantly when your connection drops — with voice announcements, sound tones, offline duration tracking, **system tray support**, and **persistent window positioning**.

Built for team environments where staying aware of network status matters.

![Widget Preview](https://img.shields.io/badge/platform-Windows-blue) ![Python](https://img.shields.io/badge/python-3.10%2B-green) ![License](https://img.shields.io/badge/license-MIT-orange)

---

## What it does

```
● UP: 1.2 KB/s    DN: 4.5 KB/s  ◀
```

- **Live speed** — upload and download updated every second
- **Status circle** — Green (fast) / Yellow (slow) / Red (offline)
- **Voice alert** — says *"Internet disconnected"* and *"Connection restored"* out loud
- **Sound tones** — distinct tones for disconnect and reconnect
- **Offline timer** — reconnect notification shows how long you were down
  - e.g. *"Back online — was down 4 min 32 sec"*
- **False alarm protection** — pings both Google DNS and Cloudflare DNS, only alerts after 2 consecutive failures (10 seconds)
- **Auto-starts** with Windows — no manual launch needed
- **Always visible** — stays on top even when switching between windows/tabs
- **Position memory** — remembers exactly where you placed it and restores on restart
- **System tray** — minimize to tray and restore from tray icon
- **Fixed size** — no accidental resizing, clean appearance

---

## Widget controls

| Action | How |
|--------|-----|
| Move | Click and drag the bar |
| Mini mode | Click `◀` to shrink to just the circle `●` |
| Restore | Click `▶` to go back to full bar |
| Hide to tray | Right-click → Hide |
| Restore from tray | Click tray icon → Show |
| Quit | Right-click widget → Quit, or tray menu → Quit |

---

## Status circle colours

| Colour | Meaning |
|--------|---------|
| 🟢 Green | Download speed ≥ 1 Mbps |
| 🟡 Yellow | Connected but slow (< 1 Mbps) |
| 🔴 Red | Internet offline |

---

## Requirements

- Windows 10 or Windows 11
- Python 3.10+ (installer handles this automatically)
- `psutil` — network speed monitoring
- `plyer` — Windows toast notifications
- `pystray` — system tray icon
- `pillow` — image generation for tray icon

> **tkinter** (UI) and **winsound** (tones) are built into Python — no extra install needed.

---

## Quick install (for teammates)

1. Download or clone this repository
2. Double-click **`INSTALL.bat`**
3. Click **Run** on the Windows security prompt (one-time only)
4. Done — widget appears bottom-right of screen

The installer will:
- Find or download Python automatically
- Install required packages (psutil, plyer, pystray, pillow)
- Copy the app to a permanent location
- Add Net Monitor to Windows startup
- Launch the widget immediately

---

## Folder structure

```
MKL_Net_Monitor/
├── INSTALL.bat                 # Double-click to install
├── UNINSTALL.bat              # Remove Net Monitor completely
├── INSTALL_UNINSTALL.txt      # Step-by-step guides
├── HOW_IT_WORKS.txt           # User guide
├── README.md                  # This file
└── app/                        # ← Application folder
    ├── net_monitor.py         # Main application
    ├── setup.ps1              # Installer script
    └── net_monitor_config.json # Position & settings (auto-created)
```

---

## Uninstall

Double-click `UNINSTALL.bat` and type `YES` when prompted.

This removes:
- The app files from `%LOCALAPPDATA%\NetMonitor\`
- The Windows startup shortcut

Python and pip packages are **not** removed.

---

## New in v5

✨ **Always visible** — Window stays on top when switching between applications. The disconnect/reconnect alerts won't be hidden.

✨ **Persistent position** — Moves the widget somewhere? Restart your PC and it'll be right back there. Position is saved automatically as you drag.

✨ **System tray integration** — Right-click the tray icon to show, hide, or quit. Useful if you want to keep the monitor running but get it out of sight temporarily.

✨ **Fixed size** — No accidental resizing. The widget is clean and predictable.

✨ **Mini mode toggle** — Click the arrow to shrink to just the status circle, perfect for minimal UI.

---

## Manual run (for developers)

```bash
cd app
pip install psutil plyer pystray pillow
python net_monitor.py
```

---

## How disconnect detection works

Every 2 seconds the app pings two servers:

| Server | Address |
|--------|---------|
| Google DNS | `8.8.8.8:53` |
| Cloudflare DNS | `1.1.1.1:53` |

A disconnect alert only fires if **both servers fail consecutively** (≈2 seconds). This eliminates false alerts from brief packet loss or a single slow ping response.

On reconnect, **either** server responding is enough to confirm the connection is back.

---

## Speed thresholds

| Threshold | Value |
|-----------|-------|
| Green (fast) | Download ≥ 1 Mbps |
| Yellow (slow) | Download < 1 Mbps but online |
| Red (offline) | No response from both ping servers |

Thresholds can be changed in `app/net_monitor.py`:

```python
SPEED_GREEN  = 1_000_000   # 1 Mbps
SPEED_YELLOW =   100_000   # 100 KB/s
```

---

## Customisation

Open `app/net_monitor.py` in any text editor.

**Change ping interval:**
```python
CHECK_INTERVAL = 2      # seconds between checks
```

**Change fail threshold:**
```python
FAIL_THRESHOLD = 1      # consecutive failures before alert
```

**Change alert tones:**
```python
TONE_DISCONNECT = [(600, 180), (400, 250), (250, 400)]   # (frequency_hz, duration_ms)
TONE_RECONNECT  = [(350, 120), (550, 120), (850, 300)]
```

**Change widget colours:**
```python
C_GREEN  = "#00e676"
C_YELLOW = "#ffca28"
C_RED    = "#ff4757"
```

**Change transparency:**
```python
# In config file (app/net_monitor_config.json) or default in code:
"transparency": 0.95   # 0.0 = invisible, 1.0 = opaque
```

---

## Configuration file

Position and settings are saved in `app/net_monitor_config.json`:

```json
{
  "window_x": 1200,
  "window_y": 650,
  "mini_mode": false,
  "transparency": 0.95
}
```

- **window_x, window_y** — saved automatically when you move the widget
- **mini_mode** — toggled by clicking the arrow button
- **transparency** — window opacity (0-1)

To reset to defaults, just delete this file. It will be recreated on launch.

---

## Contributing

Pull requests are welcome. Some ideas for future improvements:

- [ ] Settings panel (thresholds, colours, ping servers)
- [ ] Connection history log
- [ ] Network adapter selector
- [ ] Ping latency display
- [ ] Daily/weekly speed summary
- [ ] Network stats export (CSV/JSON)

To contribute:

```bash
git clone https://github.com/your-username/net-monitor.git
cd net-monitor/app
pip install psutil plyer pystray pillow
python net_monitor.py
```

---

## Developed by

**Sayeed** — MKL Team  
Build: 13.05.2026

---

## License

MIT License — free to use, modify and distribute.