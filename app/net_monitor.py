"""
Net Monitor v5 — Single line floating widget with system tray
● UP: x KB/s    DN: x KB/s
Developed for: Global Mediklaud (BD) Ltd. Team
Developed By: sayeed.ttian (Github)
Voice + tone alerts, dual-ping, offline timer, system tray, persistent position
"""

__author__  = "Kazi Abu Sayeed"
__version__ = "5.0.1"
__date__    = "13.05.2026"

import tkinter as tk
import psutil
import time
import threading
import socket
import subprocess
import sys
import json
import os
from pathlib import Path
from ctypes import windll, Structure, c_int, c_void_p, POINTER

try:
    import winsound
    WINSOUND = True
except ImportError:
    WINSOUND = False

try:
    from plyer import notification
    PLYER = True
except ImportError:
    PLYER = False

try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY = True
except ImportError:
    PYSTRAY = False

# ── Config ─────────────────────────────────────────────────────────────────────
CHECK_INTERVAL = 2      # seconds between internet checks
FAIL_THRESHOLD = 1      # consecutive all-fail rounds before disconnect alert
PING_TIMEOUT   = 2
UPDATE_MS      = 1000

PING_SERVERS = [
    ("8.8.8.8", 53),   # Google DNS
    ("1.1.1.1", 53),   # Cloudflare DNS
]

SPEED_GREEN  = 1_000_000   # >= 1 Mbps  → green
SPEED_YELLOW =   100_000   # >= 100 KB/s → yellow   (below = yellow too, red = offline)

TONE_DISCONNECT = [(600, 180), (400, 250), (250, 400)]
TONE_RECONNECT  = [(350, 120), (550, 120), (850, 300)]

C_BG      = "#0f0f1a"
C_SURFACE = "#16162a"
C_BORDER  = "#2a2a50"
C_UP      = "#4e9af1"
C_DN      = "#00d4aa"
C_MUTED   = "#55557a"
C_GREEN   = "#00e676"
C_YELLOW  = "#ffca28"
C_RED     = "#ff4757"
C_TEXT    = "#c8c8e0"

CONFIG_FILE = Path(__file__).parent / "net_monitor_config.json"

# Windows API structures
class POINT(Structure):
    _fields_ = [("x", c_int), ("y", c_int)]

class RECT(Structure):
    _fields_ = [("left", c_int), ("top", c_int), ("right", c_int), ("bottom", c_int)]

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
HWND_TOPMOST = c_void_p(-1)

# ── Config Management ──────────────────────────────────────────────────────────
def load_config():
    """Load window position and settings from config file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "window_x": None,
        "window_y": None,
        "mini_mode": False,
        "transparency": 0.95
    }

def save_config(config):
    """Save window position and settings to config file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        pass

# ── Utilities ─────────────────────────────────────────────────────────────────
def fmt(bps):
    if bps < 1024:
        return f"{bps:.0f} B/s"
    elif bps < 1_048_576:
        return f"{bps/1024:.1f} KB/s"
    else:
        return f"{bps/1_048_576:.1f} MB/s"


def check_internet():
    """True if at least one server responds — only False when ALL fail."""
    for host, port in PING_SERVERS:
        try:
            socket.create_connection((host, port), timeout=PING_TIMEOUT)
            return True
        except OSError:
            pass
    return False


def play_tone(tones):
    if not WINSOUND:
        return
    def _play():
        for freq, dur in tones:
            try:
                winsound.Beep(freq, dur)
            except Exception:
                pass
    threading.Thread(target=_play, daemon=True).start()


def speak(text):
    """Windows built-in TTS — no extra packages needed."""
    def _go():
        try:
            cmd = (
                f'Add-Type -AssemblyName System.Speech; '
                f'$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                f'$s.Volume = 100; $s.Speak("{text}")'
            )
            subprocess.Popen(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception:
            pass
    threading.Thread(target=_go, daemon=True).start()


def push_notify(title, msg):
    if not PLYER:
        return
    try:
        notification.notify(title=title, message=msg,
                            app_name="Net Monitor", timeout=8)
    except Exception:
        pass

def create_tray_icon():
    """Create a system tray icon."""
    if not PYSTRAY:
        return None
    try:
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, 56, 56], fill='#4e9af1', outline='#0f0f1a', width=2)
        return image
    except Exception:
        return None

# ── Main App ──────────────────────────────────────────────────────────────────
class NetMonitor:

    def __init__(self):
        self.dl_bps        = 0.0
        self.ul_bps        = 0.0
        self.online        = True
        self.was_connected = True
        self.fail_count    = 0
        self.offline_since = None
        self.running       = True
        self.mini_mode     = False
        self._prev         = psutil.net_io_counters()
        self._prev_t       = time.time()
        self._full_w       = 260
        self._h            = 26
        self._config       = load_config()
        self._tray_icon    = None

        self._build_window()
        self._build_ui()
        self._setup_tray()

        threading.Thread(target=self._bg_loop, daemon=True).start()
        self._tick()

        try:
            self.root.mainloop()
        finally:
            self._cleanup()

    # ── Window ────────────────────────────────────────────────────────────────
    def _build_window(self):
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        try:
            root.attributes("-alpha", self._config.get("transparency", 0.95))
        except Exception:
            pass
        root.configure(bg=C_BG)

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()

        # Load saved position or use default
        x = self._config.get("window_x")
        y = self._config.get("window_y")
        if x is None or y is None:
            x = sw - self._full_w - 20
            y = sh - self._h - 60

        root.geometry(f"{self._full_w}x{self._h}+{x}+{y}")

        self._menu = tk.Menu(root, tearoff=0, bg="#1a1a30", fg="white",
                             activebackground="#2a2a50", activeforeground="white",
                             font=("Segoe UI", 9))
        self._menu.add_command(label="  Net Monitor v5", state="disabled")
        self._menu.add_separator()
        self._menu.add_command(label="  Hide", command=self._hide_window)
        self._menu.add_separator()
        self._menu.add_command(label="  Quit", command=self._quit)

        root.bind("<Button-3>", self._show_menu)
        root.protocol("WM_DELETE_WINDOW", self._quit)

        self.root = root

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Thin border
        outer = tk.Frame(self.root, bg=C_BORDER, padx=1, pady=1)
        outer.pack(fill="both", expand=True)

        # Surface
        self._surface = tk.Frame(outer, bg=C_SURFACE)
        self._surface.pack(fill="both", expand=True)

        # Single row
        row = tk.Frame(self._surface, bg=C_SURFACE)
        row.pack(fill="both", expand=True, padx=5, pady=0)
        self._row = row

        # Drag bindings on all containers
        for w in (outer, self._surface, row):
            w.bind("<Button-1>",  self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)
            w.bind("<Button-3>",  self._show_menu)

        # ● Status circle
        self._cv = tk.Canvas(row, width=14, height=14,
                             bg=C_SURFACE, highlightthickness=0)
        self._cv.pack(side="left", padx=(0, 4))
        self._circle = self._cv.create_oval(2, 2, 12, 12,
                                            fill=C_GREEN, outline="")
        self._cv.bind("<Button-1>",  self._drag_start)
        self._cv.bind("<B1-Motion>", self._drag_move)

        # Speed frame (hidden in mini mode)
        self._spd = tk.Frame(row, bg=C_SURFACE)
        self._spd.pack(side="left", fill="x", expand=True)

        tk.Label(self._spd, text="UP:", bg=C_SURFACE, fg=C_UP,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        self._up = tk.Label(self._spd, text="0 B/s", bg=C_SURFACE, fg=C_UP,
                            font=("Consolas", 9, "bold"), width=9, anchor="w")
        self._up.pack(side="left")

        tk.Label(self._spd, text="DN:", bg=C_SURFACE, fg=C_DN,
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(6, 0))
        self._dn = tk.Label(self._spd, text="0 B/s", bg=C_SURFACE, fg=C_DN,
                            font=("Consolas", 9, "bold"), width=9, anchor="w")
        self._dn.pack(side="left")

        # ◀ Toggle button
        self._tbtn = tk.Label(row, text="◀", bg=C_SURFACE, fg=C_MUTED,
                              font=("Segoe UI", 7), cursor="hand2")
        self._tbtn.pack(side="right", padx=(2, 0))
        self._tbtn.bind("<Button-1>", lambda e: self._toggle_mini())

    # ── Mini toggle ───────────────────────────────────────────────────────────
    def _toggle_mini(self):
        self.mini_mode = not self.mini_mode
        if self.mini_mode:
            self._spd.pack_forget()
            self._tbtn.config(text="▶")
            self.root.geometry(f"26x{self._h}")
        else:
            self._spd.pack(side="left", fill="x", expand=True)
            self._tbtn.config(text="◀")
            self.root.geometry(f"{self._full_w}x{self._h}")
        self._config["mini_mode"] = self.mini_mode
        save_config(self._config)

    # ── Drag ──────────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._ox, self._oy = e.x, e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._ox
        y = self.root.winfo_y() + e.y - self._oy
        self.root.geometry(f"+{x}+{y}")

        self._config["window_x"] = x
        self._config["window_y"] = y

    def _show_menu(self, e):
        self._menu.post(e.x_root, e.y_root)

    # ── System Tray ───────────────────────────────────────────────────────────
    def _setup_tray(self):
        """Setup system tray icon with menu."""
        if not PYSTRAY:
            return

        try:
            icon_image = create_tray_icon()
            if icon_image is None:
                return

            menu = pystray.Menu(
                pystray.MenuItem("Show", lambda: self._show_window()),
                pystray.MenuItem("Hide", lambda: self._hide_window()),
                pystray.MenuItem("Quit", lambda: self._quit())
            )

            self._tray_icon = pystray.Icon(
                "NetMonitor",
                icon_image,
                "Net Monitor v5",
                menu
            )

            threading.Thread(target=self._tray_icon.run, daemon=True).start()
        except Exception as e:
            pass

    def _show_window(self):
        """Show the window and bring it to foreground."""
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.focus()
        self._keep_window_visible()

    def _hide_window(self):
        """Hide window to system tray."""
        self.root.withdraw()

    def _keep_window_visible(self):
        """Use Windows API to keep window always visible."""
        try:
            hwnd = self.root.winfo_id()
            windll.user32.SetWindowPos(
                c_void_p(hwnd),
                HWND_TOPMOST,
                0, 0, 0, 0,
                SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
            )
        except Exception:
            pass

    # ── Background monitor thread ─────────────────────────────────────────────
    def _bg_loop(self):
        tick = 0
        while self.running:
            time.sleep(1)
            tick += 1

            # Speed measurement
            now  = time.time()
            curr = psutil.net_io_counters()
            dt   = max(now - self._prev_t, 0.001)
            self.dl_bps  = (curr.bytes_recv - self._prev.bytes_recv) / dt
            self.ul_bps  = (curr.bytes_sent - self._prev.bytes_sent) / dt
            self._prev   = curr
            self._prev_t = now

            # Internet check every CHECK_INTERVAL seconds
            if tick % CHECK_INTERVAL == 0:
                up = check_internet()

                if up:
                    self.fail_count = 0
                    if not self.was_connected:
                        # ── RECONNECTED ─────────────────────────────────────
                        self.was_connected = True
                        self.online        = True
                        if self.offline_since:
                            secs  = int(time.time() - self.offline_since)
                            mins  = secs // 60
                            secs  = secs % 60
                            msg   = f"Back online — was down {mins} min {secs} sec"
                        else:
                            msg = "Back online"
                        self.offline_since = None
                        play_tone(TONE_RECONNECT)
                        threading.Timer(0.9, lambda: speak("Medi Cloud Connection Reconnected")).start()
                        push_notify("✅ Internet Reconnected", msg)
                else:
                    self.fail_count += 1
                    if self.fail_count >= FAIL_THRESHOLD and self.was_connected:
                        # ── DISCONNECTED ────────────────────────────────────
                        self.was_connected = False
                        self.online        = False
                        self.offline_since = time.time()
                        play_tone(TONE_DISCONNECT)
                        threading.Timer(0.9, lambda: speak("Medi Cloud Connection disconnected")).start()
                        push_notify("❌ Internet Disconnected",
                                    "Connection lost. Monitoring for reconnect...")

    # ── UI refresh (main thread) ──────────────────────────────────────────────
    def _circle_color(self):
        if not self.online:
            return C_RED
        if self.dl_bps >= SPEED_GREEN:
            return C_GREEN
        return C_YELLOW   # connected but slow

    def _tick(self):
        self._cv.itemconfig(self._circle, fill=self._circle_color())
        if self.online:
            self._up.config(text=fmt(self.ul_bps), fg=C_UP)
            self._dn.config(text=fmt(self.dl_bps), fg=C_DN)
        else:
            self._up.config(text="OFFLINE", fg=C_RED)
            self._dn.config(text="OFFLINE", fg=C_RED)

        if self.root.state() == 'normal':
            self._keep_window_visible()

        self.root.after(UPDATE_MS, self._tick)

    def _cleanup(self):
        """Cleanup before exit."""
        self.running = False
        try:
            self._config["window_x"] = self.root.winfo_x()
            self._config["window_y"] = self.root.winfo_y()
            self._config["mini_mode"] = self.mini_mode
            save_config(self._config)
        except Exception:
            pass

        if self._tray_icon:
            try:
                self._tray_icon.stop()
            except Exception:
                pass

    def _quit(self):
        self.running = False
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)


if __name__ == "__main__":
    NetMonitor()
