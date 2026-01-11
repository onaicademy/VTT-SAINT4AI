"""
VTT by @SAINT4AI
Premium Voice-to-Text with Groq Whisper
"""
import os
import sys
import json
import time
import threading
import math
import ctypes
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as write_wav
import keyboard
import pyperclip
import pyautogui
from groq import Groq
import customtkinter as ctk
from datetime import datetime

# App info
APP_NAME = "VTT"
APP_VERSION = "1.1"
CONFIG_FILE = "settings.json"
HISTORY_FILE = "history.json"
MAX_HISTORY = 50

# Premium Color Scheme
COLORS = {
    "bg": "#0a0a0a",
    "bg_secondary": "#111111",
    "bg_card": "#161616",
    "bg_hover": "#1f1f1f",
    "accent": "#6366f1",
    "accent_glow": "#818cf8",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "text": "#ffffff",
    "text_secondary": "#a1a1aa",
    "text_muted": "#52525b",
    "border": "#262626",
    "metallic": "#71717a",
    "recording": "#ef4444",
    "recording_glow": "#fca5a5",
    "widget_bg": "#1a1a1a"
}

DEFAULT_SETTINGS = {
    "api_key": "",
    "hotkey": "F9",
    "microphone": "",
    "language": "ru",
    "auto_paste": True,
    "copy_clipboard": True,
    "sounds": True
}


class PremiumSounds:
    """Premium iPhone-style sounds using sine waves."""

    @staticmethod
    def generate_tone(freq, duration, volume=0.3, fade=True):
        """Generate a smooth sine wave tone."""
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone = np.sin(2 * np.pi * freq * t) * volume

        if fade:
            # Smooth fade in/out
            fade_len = int(len(tone) * 0.15)
            fade_in = np.linspace(0, 1, fade_len)
            fade_out = np.linspace(1, 0, fade_len)
            tone[:fade_len] *= fade_in
            tone[-fade_len:] *= fade_out

        return tone.astype(np.float32)

    @staticmethod
    def play_start():
        """Play elegant start recording sound."""
        def play():
            try:
                # Rising chime - C5 -> E5 -> G5
                tones = []
                for freq in [523, 659, 784]:
                    tones.append(PremiumSounds.generate_tone(freq, 0.08, 0.25))
                    tones.append(np.zeros(int(44100 * 0.02), dtype=np.float32))

                audio = np.concatenate(tones)
                sd.play(audio, 44100, blocking=True)
            except:
                pass
        threading.Thread(target=play, daemon=True).start()

    @staticmethod
    def play_stop():
        """Play elegant stop recording sound."""
        def play():
            try:
                # Falling tone - G5 -> E5
                tones = []
                for freq in [784, 659]:
                    tones.append(PremiumSounds.generate_tone(freq, 0.06, 0.2))
                    tones.append(np.zeros(int(44100 * 0.015), dtype=np.float32))

                audio = np.concatenate(tones)
                sd.play(audio, 44100, blocking=True)
            except:
                pass
        threading.Thread(target=play, daemon=True).start()

    @staticmethod
    def play_success():
        """Play success completion sound."""
        def play():
            try:
                # Happy ascending - like iPhone payment success
                tones = []
                for freq in [880, 1047, 1319]:
                    tones.append(PremiumSounds.generate_tone(freq, 0.07, 0.2))
                    tones.append(np.zeros(int(44100 * 0.02), dtype=np.float32))

                audio = np.concatenate(tones)
                sd.play(audio, 44100, blocking=True)
            except:
                pass
        threading.Thread(target=play, daemon=True).start()


class PremiumRecordButton(ctk.CTkFrame):
    """Premium animated recording button with smooth transitions."""

    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.command = command
        self.is_recording = False
        self.animation_running = False
        self.pulse_phase = 0.0
        self.audio_level = 0.0
        self.target_level = 0.0
        self.glow_intensity = 0.0

        # Canvas for smooth animations
        self.size = 110
        self.canvas = ctk.CTkCanvas(
            self, width=self.size, height=self.size,
            bg=COLORS["bg"], highlightthickness=0
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", lambda e: command() if command else None)
        self.canvas.bind("<Enter>", self._on_hover)
        self.canvas.bind("<Leave>", self._on_leave)
        self.hover = False

        # Status text
        self.status = ctk.CTkLabel(
            self, text="Нажми для записи",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_muted"]
        )
        self.status.pack(pady=(10, 0))

        # Hotkey hint
        self.hint = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_muted"]
        )
        self.hint.pack(pady=(2, 0))

        self.draw_idle()

    def _on_hover(self, e):
        self.hover = True
        if not self.is_recording:
            self.draw_idle()

    def _on_leave(self, e):
        self.hover = False
        if not self.is_recording:
            self.draw_idle()

    def draw_idle(self):
        """Draw elegant idle state."""
        self.canvas.delete("all")
        cx, cy = self.size // 2, self.size // 2
        r = 42

        # Outer glow rings
        for i in range(3):
            alpha = 0.15 - i * 0.04
            color = self._alpha_color(COLORS["accent"], alpha) if self.hover else COLORS["border"]
            self.canvas.create_oval(
                cx - r - 4 - i*4, cy - r - 4 - i*4,
                cx + r + 4 + i*4, cy + r + 4 + i*4,
                fill="", outline=color, width=1
            )

        # Main circle
        fill = COLORS["bg_hover"] if self.hover else COLORS["bg_card"]
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=fill, outline=COLORS["border"], width=2
        )

        # Mic icon - premium design
        self._draw_premium_mic(cx, cy, COLORS["text_secondary"] if not self.hover else COLORS["accent"])

    def draw_recording(self):
        """Draw recording state with smooth animations - contained within bounds."""
        self.canvas.delete("all")
        cx, cy = self.size // 2, self.size // 2
        r = 40  # Slightly smaller main circle

        # Animated pulse rings - contained within canvas
        for i in range(2):  # Only 2 rings
            phase = (self.pulse_phase + i * 0.4) % 1.0
            # Ease out quad
            eased = 1 - (1 - phase) ** 2
            ring_r = r + 2 + eased * 10  # Max expansion: 40+2+10=52, within 55
            alpha = (1 - phase) * 0.5
            color = self._alpha_color(COLORS["recording"], alpha)
            self.canvas.create_oval(
                cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r,
                fill="", outline=color, width=2
            )

        # Audio level ring - subtle glow inside
        if self.audio_level > 0.05:
            level_r = r + 1 + self.audio_level * 8  # Max: 40+1+8=49
            self.canvas.create_oval(
                cx - level_r, cy - level_r, cx + level_r, cy + level_r,
                fill="", outline=COLORS["recording_glow"], width=1
            )

        # Main circle
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=COLORS["recording"], outline=""
        )

        # Stop icon - smaller square
        sq = 11
        self.canvas.create_rectangle(
            cx - sq, cy - sq, cx + sq, cy + sq,
            fill=COLORS["text"], outline=""
        )

    def _draw_premium_mic(self, cx, cy, color):
        """Draw premium microphone icon."""
        # Mic body - capsule shape
        self.canvas.create_oval(cx-8, cy-18, cx+8, cy+2, fill=color, outline="")

        # Mic stand arc - smooth curve
        self.canvas.create_arc(
            cx-14, cy-10, cx+14, cy+14,
            start=0, extent=-180, style="arc",
            outline=color, width=2
        )

        # Stand - centered
        self.canvas.create_line(cx, cy+14, cx, cy+22, fill=color, width=2)
        self.canvas.create_line(cx-10, cy+22, cx+10, cy+22, fill=color, width=2)

    def _alpha_color(self, hex_color, alpha):
        """Create color with alpha blending against bg."""
        r1, g1, b1 = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        bg = COLORS["bg"]
        r2, g2, b2 = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
        r = int(r1 * alpha + r2 * (1 - alpha))
        g = int(g1 * alpha + g2 * (1 - alpha))
        b = int(b1 * alpha + b2 * (1 - alpha))
        return f"#{r:02x}{g:02x}{b:02x}"

    def start_recording(self):
        self.is_recording = True
        self.animation_running = True
        self.status.configure(text="Запись...", text_color=COLORS["recording"])
        self._animate()

    def stop_recording(self):
        self.is_recording = False
        self.animation_running = False
        self.audio_level = 0
        self.status.configure(text="Обработка...", text_color=COLORS["warning"])

    def reset(self):
        self.status.configure(text="Нажми для записи", text_color=COLORS["text_muted"])
        self.draw_idle()

    def set_success(self, text):
        self.status.configure(text=text, text_color=COLORS["success"])
        self.draw_idle()

    def set_error(self, text):
        self.status.configure(text=text, text_color=COLORS["error"])
        self.draw_idle()

    def update_level(self, level):
        self.target_level = min(1.0, level)

    def _animate(self):
        if not self.animation_running:
            return

        # Smooth phase increment
        self.pulse_phase = (self.pulse_phase + 0.025) % 1.0

        # Smooth audio level interpolation
        self.audio_level += (self.target_level - self.audio_level) * 0.3

        self.draw_recording()
        self.after(20, self._animate)


class FloatingWidget(ctk.CTkToplevel):
    """Floating draggable widget when app is minimized."""

    def __init__(self, master, toggle_callback, **kwargs):
        super().__init__(master, **kwargs)

        self.toggle_callback = toggle_callback
        self.is_recording = False

        # Window setup - no decorations, always on top
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.95)
        self.configure(fg_color=COLORS["widget_bg"])

        # Size
        self.size = 60
        self.geometry(f"{self.size}x{self.size}+100+100")

        # Canvas
        self.canvas = ctk.CTkCanvas(
            self, width=self.size, height=self.size,
            bg=COLORS["widget_bg"], highlightthickness=0
        )
        self.canvas.pack()

        # Drag functionality
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)

        self._drag_data = {"x": 0, "y": 0}
        self.pulse_phase = 0
        self.animation_running = False

        self.draw_idle()
        self.withdraw()  # Start hidden

    def _on_click(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        # Single click toggles recording
        self.toggle_callback()

    def _on_drag(self, event):
        x = self.winfo_x() + event.x - self._drag_data["x"]
        y = self.winfo_y() + event.y - self._drag_data["y"]
        self.geometry(f"+{x}+{y}")

    def _on_double_click(self, event):
        # Double click restores main window
        self.master.deiconify()
        self.master.lift()
        self.withdraw()

    def draw_idle(self):
        self.canvas.delete("all")
        cx, cy = self.size // 2, self.size // 2
        r = 24

        # Circle background
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=COLORS["bg_card"], outline=COLORS["accent"], width=2
        )

        # Mic icon
        self.canvas.create_oval(cx-5, cy-12, cx+5, cy+1, fill=COLORS["accent"], outline="")
        self.canvas.create_arc(cx-9, cy-6, cx+9, cy+8, start=0, extent=-180, style="arc", outline=COLORS["accent"], width=2)
        self.canvas.create_line(cx, cy+8, cx, cy+14, fill=COLORS["accent"], width=2)

    def draw_recording(self):
        self.canvas.delete("all")
        cx, cy = self.size // 2, self.size // 2
        r = 24

        # Pulse ring
        phase = self.pulse_phase
        ring_r = r + 3 + phase * 8
        alpha = 1 - phase
        self.canvas.create_oval(
            cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r,
            fill="", outline=COLORS["recording"], width=2
        )

        # Main circle
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=COLORS["recording"], outline=""
        )

        # Stop icon
        sq = 8
        self.canvas.create_rectangle(cx - sq, cy - sq, cx + sq, cy + sq, fill=COLORS["text"], outline="")

    def start_recording(self):
        self.is_recording = True
        self.animation_running = True
        self._animate_widget()

    def stop_recording(self):
        self.is_recording = False
        self.animation_running = False
        self.draw_idle()

    def _animate_widget(self):
        if not self.animation_running:
            return
        self.pulse_phase = (self.pulse_phase + 0.05) % 1.0
        self.draw_recording()
        self.after(30, self._animate_widget)

    def show(self):
        self.deiconify()
        self.lift()

    def hide(self):
        self.withdraw()


class VoiceToTextApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VTT")
        self.geometry("360x620")
        self.minsize(340, 550)
        self.configure(fg_color=COLORS["bg"])

        ctk.set_appearance_mode("dark")

        # State
        self.is_recording = False
        self.audio_data = []
        self.groq_client = None
        self.current_hotkey = None
        self.mic_devices = {}
        self.history = []
        self.last_focused_window = None

        self.settings = self.load_settings()
        self.load_history()
        self.create_ui()
        self.refresh_mics()
        self.setup_hotkey()
        self.check_api()

        # Floating widget
        self.floating_widget = FloatingWidget(self, self.toggle_recording)

        # Window events
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Unmap>", self._on_minimize)
        self.bind("<Map>", self._on_restore)

    def _on_minimize(self, event):
        if self.state() == 'iconic':
            self.floating_widget.show()

    def _on_restore(self, event):
        self.floating_widget.hide()

    def load_settings(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    s = DEFAULT_SETTINGS.copy()
                    s.update(json.load(f))
                    return s
        except:
            pass
        return DEFAULT_SETTINGS.copy()

    def save_settings(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except:
            pass

    def load_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except:
            self.history = []

    def save_history(self):
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except:
            pass

    def add_to_history(self, text):
        """Add transcription to history with auto-cleanup."""
        entry = {
            "text": text,
            "timestamp": datetime.now().isoformat(),
        }
        self.history.insert(0, entry)

        # Auto cleanup at 50 records
        if len(self.history) > MAX_HISTORY:
            self.history = self.history[:MAX_HISTORY]
            print(f"[DEBUG] История очищена до {MAX_HISTORY} записей")

        self.save_history()

    def create_ui(self):
        # Main container
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=16, pady=16)

        # Header
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            header, text="VTT",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="center")

        ctk.CTkLabel(
            header, text="by @SAINT4AI",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["metallic"]
        ).pack(anchor="center")

        # Record button
        self.record_btn = PremiumRecordButton(main, command=self.toggle_recording)
        self.record_btn.pack(pady=12)

        # Scrollable settings
        settings_frame = ctk.CTkScrollableFrame(
            main, fg_color="transparent",
            scrollbar_button_color=COLORS["border"]
        )
        settings_frame.pack(fill="both", expand=True)

        # API Key
        self._section(settings_frame, "API КЛЮЧ")
        api_frame = self._card(settings_frame)

        api_row = ctk.CTkFrame(api_frame, fg_color="transparent")
        api_row.pack(fill="x", pady=(0, 4))

        self.api_entry = ctk.CTkEntry(
            api_row, placeholder_text="gsk_...",
            height=32, font=ctk.CTkFont(size=12),
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border"],
            text_color=COLORS["text"]
        )
        self.api_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            api_row, text="Вставить", width=70, height=32,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_glow"],
            command=self.paste_api_key
        ).pack(side="right")

        if self.settings["api_key"]:
            self.api_entry.insert(0, self.settings["api_key"])

        self.api_status = ctk.CTkLabel(
            api_frame, text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        )
        self.api_status.pack(anchor="w")

        self.api_entry.bind("<Return>", lambda e: self.save_api())
        self.api_entry.bind("<FocusOut>", lambda e: self.save_api())

        # Microphone
        self._section(settings_frame, "МИКРОФОН")
        mic_frame = self._card(settings_frame)

        self.mic_combo = ctk.CTkComboBox(
            mic_frame, values=["Загрузка..."],
            height=32, font=ctk.CTkFont(size=11),
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border"],
            button_color=COLORS["border"],
            dropdown_fg_color=COLORS["bg_card"],
            command=self.on_mic_change
        )
        self.mic_combo.pack(fill="x", pady=(0, 6))

        level_row = ctk.CTkFrame(mic_frame, fg_color="transparent")
        level_row.pack(fill="x")

        ctk.CTkLabel(
            level_row, text="Уровень",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        self.level_bar = ctk.CTkProgressBar(
            level_row, height=4,
            fg_color=COLORS["bg_secondary"],
            progress_color=COLORS["accent"]
        )
        self.level_bar.pack(side="left", fill="x", expand=True, padx=(8, 8))
        self.level_bar.set(0)

        # Test button for mic level
        self.test_btn = ctk.CTkButton(
            level_row, text="Тест", width=50, height=22,
            font=ctk.CTkFont(size=10),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["bg_hover"],
            border_width=1, border_color=COLORS["border"],
            command=self.test_mic
        )
        self.test_btn.pack(side="right")
        self.mic_testing = False

        # Hotkey
        self._section(settings_frame, "ГОРЯЧАЯ КЛАВИША")
        hk_frame = self._card(settings_frame)

        hk_row = ctk.CTkFrame(hk_frame, fg_color="transparent")
        hk_row.pack(fill="x")

        self.hotkey_label = ctk.CTkLabel(
            hk_row, text=self.settings["hotkey"].upper(),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["accent"]
        )
        self.hotkey_label.pack(side="left")

        ctk.CTkButton(
            hk_row, text="Изменить", width=70, height=28,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["bg_hover"],
            border_width=1, border_color=COLORS["border"],
            command=self.change_hotkey
        ).pack(side="right")

        # Options
        self._section(settings_frame, "НАСТРОЙКИ")
        opt_frame = self._card(settings_frame)

        self.auto_paste_var = ctk.BooleanVar(value=self.settings["auto_paste"])
        ctk.CTkCheckBox(
            opt_frame, text="Автовставка текста",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_glow"],
            border_color=COLORS["border"],
            variable=self.auto_paste_var,
            command=lambda: self._save_opt("auto_paste", self.auto_paste_var.get())
        ).pack(anchor="w", pady=2)

        self.clipboard_var = ctk.BooleanVar(value=self.settings["copy_clipboard"])
        ctk.CTkCheckBox(
            opt_frame, text="Копировать в буфер",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_glow"],
            border_color=COLORS["border"],
            variable=self.clipboard_var,
            command=lambda: self._save_opt("copy_clipboard", self.clipboard_var.get())
        ).pack(anchor="w", pady=2)

        self.sounds_var = ctk.BooleanVar(value=self.settings["sounds"])
        ctk.CTkCheckBox(
            opt_frame, text="Звуковые оповещения",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_glow"],
            border_color=COLORS["border"],
            variable=self.sounds_var,
            command=lambda: self._save_opt("sounds", self.sounds_var.get())
        ).pack(anchor="w", pady=2)

        # History section - with updatable title
        self.history_title = ctk.CTkLabel(
            settings_frame, text=f"ИСТОРИЯ ({len(self.history)}/{MAX_HISTORY})",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text_muted"]
        )
        self.history_title.pack(anchor="w", pady=(12, 4))
        hist_frame = self._card(settings_frame)

        hist_row = ctk.CTkFrame(hist_frame, fg_color="transparent")
        hist_row.pack(fill="x")

        self.history_label = ctk.CTkLabel(
            hist_row,
            text=self._get_last_history() if self.history else "Пока нет записей",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            wraplength=220,
            anchor="w",
            justify="left"
        )
        self.history_label.pack(side="left", fill="x", expand=True)

        # Copy last button
        self.copy_hist_btn = ctk.CTkButton(
            hist_row, text="Копировать", width=80, height=26,
            font=ctk.CTkFont(size=10),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["bg_hover"],
            border_width=1, border_color=COLORS["border"],
            command=self.copy_last_history
        )
        if self.history:
            self.copy_hist_btn.pack(side="right", padx=(8, 0))

        # Footer
        ctk.CTkLabel(
            main, text=f"v{APP_VERSION} - Groq Whisper",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        ).pack(pady=(12, 0))

    def _get_last_history(self):
        if not self.history:
            return ""
        last = self.history[0]
        text = last["text"][:50] + "..." if len(last["text"]) > 50 else last["text"]
        return f'"{text}"'

    def copy_last_history(self):
        """Copy last history item to clipboard."""
        if self.history:
            text = self.history[0]["text"]
            pyperclip.copy(text)
            # Visual feedback
            original = self.copy_hist_btn.cget("text")
            self.copy_hist_btn.configure(text="Готово!", fg_color=COLORS["success"])
            self.after(1000, lambda: self.copy_hist_btn.configure(text=original, fg_color=COLORS["bg_secondary"]))

    def _section(self, parent, title):
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(12, 4))

    def _card(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_card"],
            corner_radius=8, border_width=1,
            border_color=COLORS["border"]
        )
        card.pack(fill="x")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        return inner

    def _save_opt(self, key, val):
        self.settings[key] = val
        self.save_settings()

    def refresh_mics(self):
        try:
            devices = sd.query_devices()
            self.mic_devices = {}
            mics = []
            seen = set()

            exclude = ["переназначение", "первичный драйвер", "стерео микшер",
                      "stereo mix", "loopback", "virtual", "лин. вход", "line in"]

            for i, d in enumerate(devices):
                if d['max_input_channels'] > 0:
                    name = d['name']
                    name_lower = name.lower()

                    if any(ex in name_lower for ex in exclude):
                        continue

                    if "микрофон" in name_lower or "microphone" in name_lower or "mic" in name_lower:
                        short = name.split("(")[1].split(")")[0] if "(" in name else name
                        if short not in seen:
                            seen.add(short)
                            mics.append(name)
                            self.mic_devices[name] = i

            if mics:
                self.mic_combo.configure(values=mics)
                sel = self.settings["microphone"] if self.settings["microphone"] in mics else mics[0]
                self.mic_combo.set(sel)
                self.settings["microphone"] = sel
            else:
                self.mic_combo.configure(values=["Не найден"])
                self.mic_combo.set("Не найден")
        except Exception as e:
            print(f"[ERROR] Mics: {e}")

    def on_mic_change(self, val):
        self.settings["microphone"] = val
        self.save_settings()

    def test_mic(self):
        """Test microphone level without recording."""
        if self.mic_testing:
            # Stop testing
            self.mic_testing = False
            self.test_btn.configure(text="Тест", fg_color=COLORS["bg_secondary"])
            self.level_bar.set(0)
            return

        # Start testing
        self.mic_testing = True
        self.test_btn.configure(text="Стоп", fg_color=COLORS["recording"])

        def monitor():
            try:
                mic = self.mic_combo.get()
                dev = self.mic_devices.get(mic) or sd.default.device[0]

                def cb(indata, frames, t, status):
                    if self.mic_testing:
                        raw_level = np.abs(indata.astype(np.float32)).mean()
                        lvl = min(1.0, raw_level / 3000)
                        self.after(0, lambda l=lvl: self.level_bar.set(l))

                with sd.InputStream(device=dev, samplerate=16000, channels=1, dtype='int16', callback=cb):
                    while self.mic_testing:
                        time.sleep(0.03)

                self.after(0, lambda: self.level_bar.set(0))
            except Exception as e:
                print(f"[ERROR] Test mic: {e}")
                self.after(0, lambda: self.test_btn.configure(text="Тест", fg_color=COLORS["bg_secondary"]))
                self.mic_testing = False

        threading.Thread(target=monitor, daemon=True).start()

    def paste_api_key(self):
        try:
            key = pyperclip.paste() or self.clipboard_get()
            if key and key.strip():
                self.api_entry.delete(0, "end")
                self.api_entry.insert(0, key.strip())
                self.save_api()
        except Exception as e:
            print(f"[ERROR] Paste: {e}")

    def save_api(self):
        key = self.api_entry.get().strip()
        if key:
            self.settings["api_key"] = key
            self.save_settings()
            self.check_api()

    def check_api(self):
        key = self.settings.get("api_key", "")
        if not key:
            self.api_status.configure(text="Введите ключ", text_color=COLORS["text_muted"])
            self.groq_client = None
            return

        if not key.startswith("gsk_") or len(key) < 20:
            self.api_status.configure(text="Неверный формат", text_color=COLORS["error"])
            self.groq_client = None
            return

        try:
            self.groq_client = Groq(api_key=key)
            self.api_status.configure(text="Готов", text_color=COLORS["success"])
        except Exception as e:
            self.api_status.configure(text="Ошибка", text_color=COLORS["error"])
            self.groq_client = None

    def change_hotkey(self):
        self.hotkey_label.configure(text="...", text_color=COLORS["warning"])
        if self.current_hotkey:
            try: keyboard.remove_hotkey(self.current_hotkey)
            except: pass

        def capture():
            e = keyboard.read_event(suppress=True)
            if e.event_type == keyboard.KEY_DOWN:
                mods = []
                if keyboard.is_pressed('ctrl'): mods.append('ctrl')
                if keyboard.is_pressed('shift'): mods.append('shift')
                if keyboard.is_pressed('alt'): mods.append('alt')
                key = e.name
                if key not in ['ctrl','shift','alt','left ctrl','right ctrl','left shift','right shift','left alt','right alt']:
                    hk = '+'.join(mods + [key]) if mods else key
                    self.after(0, lambda: self._set_hotkey(hk))

        threading.Thread(target=capture, daemon=True).start()

    def _set_hotkey(self, hk):
        self.settings["hotkey"] = hk
        self.save_settings()
        self.hotkey_label.configure(text=hk.upper(), text_color=COLORS["accent"])
        self.setup_hotkey()

    def setup_hotkey(self):
        if self.current_hotkey:
            try: keyboard.remove_hotkey(self.current_hotkey)
            except: pass
        try:
            self.current_hotkey = keyboard.add_hotkey(
                self.settings["hotkey"], self.toggle_recording, suppress=True
            )
            self.record_btn.hint.configure(text=f"или {self.settings['hotkey'].upper()}")
        except Exception as e:
            print(f"[ERROR] Hotkey: {e}")

    def play_sound(self, type_):
        if not self.settings["sounds"]:
            return
        if type_ == "start":
            PremiumSounds.play_start()
        elif type_ == "stop":
            PremiumSounds.play_stop()
        elif type_ == "success":
            PremiumSounds.play_success()

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        if not self.groq_client:
            self.record_btn.set_error("Добавь API ключ")
            return

        # Save current focused window for auto-paste
        try:
            self.last_focused_window = ctypes.windll.user32.GetForegroundWindow()
        except:
            pass

        self.is_recording = True
        self.audio_data = []
        self.record_btn.start_recording()
        self.floating_widget.start_recording()
        self.play_sound("start")

        def record():
            try:
                mic = self.mic_combo.get()
                dev = self.mic_devices.get(mic) or sd.default.device[0]

                # Auto-stop settings
                silence_threshold = 200  # Raw level below this = silence
                silence_timeout = 20  # Seconds of silence before auto-stop
                max_duration = 60  # Max recording time in seconds

                start_time = time.time()
                last_sound_time = start_time

                def cb(indata, frames, t, status):
                    nonlocal last_sound_time
                    if self.is_recording:
                        self.audio_data.append(indata.copy())
                        raw_level = np.abs(indata.astype(np.float32)).mean()
                        lvl = min(1.0, raw_level / 3000)
                        self.after(0, lambda l=lvl: self.level_bar.set(l))
                        self.after(0, lambda l=lvl: self.record_btn.update_level(l))

                        # Update last sound time if signal detected
                        if raw_level > silence_threshold:
                            last_sound_time = time.time()

                with sd.InputStream(device=dev, samplerate=16000, channels=1, dtype='int16', callback=cb):
                    while self.is_recording:
                        time.sleep(0.1)
                        elapsed = time.time() - start_time
                        silence_duration = time.time() - last_sound_time

                        # Auto-stop after max duration
                        if elapsed > max_duration:
                            print(f"[DEBUG] Auto-stop: max duration {max_duration}s")
                            self.after(0, self.stop_recording)
                            break

                        # Auto-stop after silence timeout (but only after some audio was recorded)
                        if silence_duration > silence_timeout and len(self.audio_data) > 50:
                            print(f"[DEBUG] Auto-stop: {silence_timeout}s silence")
                            self.after(0, self.stop_recording)
                            break

                self.after(0, lambda: self.level_bar.set(0))
            except Exception as e:
                print(f"[ERROR] Record: {e}")
                self.after(0, lambda: self.record_btn.set_error("Ошибка записи"))
                self.is_recording = False

        threading.Thread(target=record, daemon=True).start()

    def stop_recording(self):
        self.is_recording = False
        self.record_btn.stop_recording()
        self.floating_widget.stop_recording()
        self.play_sound("stop")

        if not self.audio_data:
            self.record_btn.reset()
            return

        def process():
            try:
                audio = np.concatenate(self.audio_data, axis=0)
                tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rec.wav")
                write_wav(tmp, 16000, audio)

                with open(tmp, "rb") as f:
                    result = self.groq_client.audio.transcriptions.create(
                        file=(tmp, f.read()),
                        model="whisper-large-v3",
                        language=self.settings["language"],
                        response_format="text"
                    )

                try: os.remove(tmp)
                except: pass

                text = result.strip() if isinstance(result, str) else str(result).strip()

                if text:
                    self.after(0, lambda: self.handle_result(text))
                else:
                    self.after(0, lambda: self.record_btn.set_error("Речь не распознана"))
                    self.after(2000, self.record_btn.reset)
            except Exception as e:
                print(f"[ERROR] Process: {e}")
                err = "Неверный ключ" if "auth" in str(e).lower() else "Ошибка API"
                self.after(0, lambda: self.record_btn.set_error(err))
                self.after(3000, self.record_btn.reset)

        threading.Thread(target=process, daemon=True).start()

    def handle_result(self, text):
        # Add to history
        self.add_to_history(text)
        self.history_label.configure(text=self._get_last_history())

        # Update history counter
        self.history_title.configure(text=f"ИСТОРИЯ ({len(self.history)}/{MAX_HISTORY})")

        # Show copy button if first entry
        try:
            self.copy_hist_btn.pack(side="right", padx=(8, 0))
        except:
            pass

        # Copy to clipboard
        if self.settings["copy_clipboard"]:
            pyperclip.copy(text)

        # Show result
        short = (text[:35] + "...") if len(text) > 35 else text
        self.record_btn.set_success(short)

        # Auto-paste to last focused window using keyboard module
        if self.settings["auto_paste"] and self.last_focused_window:
            def do_paste():
                try:
                    time.sleep(0.2)
                    ctypes.windll.user32.SetForegroundWindow(self.last_focused_window)
                    time.sleep(0.15)
                    keyboard.send('ctrl+v')
                except Exception as e:
                    print(f"[ERROR] Auto-paste: {e}")
            threading.Thread(target=do_paste, daemon=True).start()

        self.play_sound("success")
        self.after(3000, self.record_btn.reset)

    def on_close(self):
        self.is_recording = False
        if self.current_hotkey:
            try: keyboard.remove_hotkey(self.current_hotkey)
            except: pass
        self.floating_widget.destroy()
        self.destroy()


if __name__ == "__main__":
    print("=" * 50)
    print("VTT @SAINT4AI - Voice to Text v1.1")
    print("=" * 50)
    app = VoiceToTextApp()
    app.mainloop()
