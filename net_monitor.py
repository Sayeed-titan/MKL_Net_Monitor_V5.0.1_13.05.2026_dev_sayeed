"""
Net Monitor v3 — Single line floating widget
● UP: x KB/s    DN: x KB/s
Developed for: Global Mediklaud (BD) Ltd. Team
Developed By: sayeed.ttian (Github)
Voice + tone alerts, dual-ping, offline timer
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

        self._build_window()
        self._build_ui()
        threading.Thread(target=self._bg_loop, daemon=True).start()
        self._tick()
        self.root.mainloop()

    # ── Window ────────────────────────────────────────────────────────────────
    def _build_window(self):
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        try:
            root.attributes("-alpha", 0.95)
        except Exception:
            pass
        root.configure(bg=C_BG)

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x  = sw - self._full_w - 20
        y  = sh - self._h - 60
        root.geometry(f"{self._full_w}x{self._h}+{x}+{y}")

        self._menu = tk.Menu(root, tearoff=0, bg="#1a1a30", fg="white",
                             activebackground="#2a2a50", activeforeground="white",
                             font=("Segoe UI", 9))
        self._menu.add_command(label="  Net Monitor v3", state="disabled")
        self._menu.add_separator()
        self._menu.add_command(label="  Quit", command=self._quit)

        root.bind("<Button-3>", self._show_menu)
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

        # ⠿ Resize grip (bottom-right corner)
        self._grip = tk.Label(self.root, text="⠿", bg=C_BG, fg=C_MUTED,
                              font=("Segoe UI", 7), cursor="sizing")
        self._grip.place(relx=1.0, rely=1.0, anchor="se")
        self._grip.bind("<Button-1>",  self._resize_start)
        self._grip.bind("<B1-Motion>", self._resize_drag)

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

    # ── Drag ──────────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._ox, self._oy = e.x, e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._ox
        y = self.root.winfo_y() + e.y - self._oy
        self.root.geometry(f"+{x}+{y}")

    # ── Resize ────────────────────────────────────────────────────────────────
    def _resize_start(self, e):
        self._rx = e.x_root
        self._ry = e.y_root
        self._rw = self.root.winfo_width()
        self._rh = self.root.winfo_height()

    def _resize_drag(self, e):
        nw = max(100, self._rw + (e.x_root - self._rx))
        nh = max(20,  self._rh + (e.y_root - self._ry))
        self.root.geometry(f"{nw}x{nh}")

    def _show_menu(self, e):
        self._menu.post(e.x_root, e.y_root)

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
                        threading.Timer(0.9, lambda: speak("Medi Cloud Connecttion Reconnected")).start()
                        push_notify("✅ Internet Reconnected", msg)
                else:
                    self.fail_count += 1
                    if self.fail_count >= FAIL_THRESHOLD and self.was_connected:
                        # ── DISCONNECTED ────────────────────────────────────
                        self.was_connected = False
                        self.online        = False
                        self.offline_since = time.time()
                        play_tone(TONE_DISCONNECT)
                        threading.Timer(0.9, lambda: speak("Medi Cloud Connecttion disconnected")).start()
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
        self.root.after(UPDATE_MS, self._tick)

    def _quit(self):
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    NetMonitor()
