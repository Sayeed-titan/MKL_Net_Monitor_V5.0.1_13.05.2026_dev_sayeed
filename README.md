# Net Monitor v3

A lightweight always-on-top Windows desktop widget that shows live internet speed and alerts you instantly when your connection drops — with voice announcements, sound tones, and offline duration tracking.

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

---

## Widget controls

| Action | How |
|--------|-----|
| Move | Click and drag the bar |
| Resize | Drag the `⠿` grip at the bottom-right corner |
| Mini mode | Click `◀` to shrink to just the circle `●` |
| Restore | Click `▶` to go back to full bar |
| Quit | Right-click → Quit |

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

> **tkinter** (UI) and **winsound** (tones) are built into Python — no extra install needed.

---

## Quick install (for teammates)

1. Download or clone this repository
2. Put all files in one folder
3. Double-click **`START.bat`**
4. Click **Run** on the Windows security prompt (one-time only)
5. Done — widget appears bottom-right of screen

The installer will:
- Find or download Python automatically
- Install required packages
- Copy the app to a permanent location
- Add Net Monitor to Windows startup
- Launch the widget immediately

---

## Files

```
├── START.bat               # Double-click to install
├── setup.ps1               # Installer script (runs automatically)
├── net_monitor.py          # Main application
├── UNINSTALL.bat           # Removes Net Monitor completely
├── HOW_IT_WORKS.txt        # User guide
└── INSTALL_UNINSTALL.txt   # Step-by-step install and uninstall guide
```

---

## Uninstall

Double-click `UNINSTALL.bat` and type `YES` when prompted.

This removes:
- The app files from `%LOCALAPPDATA%\NetMonitor\`
- The Windows startup shortcut

Python and pip packages are **not** removed.

---

## Manual run (for developers)

```bash
pip install psutil plyer
python net_monitor.py
```

---

## How disconnect detection works

Every 5 seconds the app pings two servers:

| Server | Address |
|--------|---------|
| Google DNS | `8.8.8.8:53` |
| Cloudflare DNS | `1.1.1.1:53` |

A disconnect alert only fires if **both servers fail two times in a row** (10 seconds total). This eliminates false alerts from brief packet loss or a single slow ping response.

On reconnect, **either** server responding is enough to confirm the connection is back.

---

## Speed thresholds

| Threshold | Value |
|-----------|-------|
| Green (fast) | Download ≥ 1 Mbps |
| Yellow (slow) | Download < 1 Mbps but online |
| Red (offline) | No response from both ping servers |

Thresholds can be changed in `net_monitor.py`:

```python
SPEED_GREEN  = 1_000_000   # 1 Mbps
SPEED_YELLOW =   100_000   # 100 KB/s
```

---

## Customisation

Open `net_monitor.py` in any text editor.

**Change ping interval:**
```python
CHECK_INTERVAL = 5      # seconds between checks
```

**Change fail threshold:**
```python
FAIL_THRESHOLD = 2      # consecutive failures before alert
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

**Change default position:**
```python
x = sw - self._full_w - 20   # pixels from right edge
y = sh - self._h - 60        # pixels from bottom edge
```

---

## Contributing

Pull requests are welcome. Some ideas for future improvements:

- [ ] Settings panel (thresholds, colours, ping servers)
- [ ] Connection history log
- [ ] Network adapter selector
- [ ] macOS / Linux support
- [ ] Ping latency display
- [ ] Daily/weekly speed summary

To contribute:

```bash
git clone https://github.com/your-username/net-monitor.git
cd net-monitor
pip install psutil plyer
python net_monitor.py
```

---

## Developed by

**Sayeed** — MKL Team  
Build: 13.05.2026

---

## License

MIT License — free to use, modify and distribute.