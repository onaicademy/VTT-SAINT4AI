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
import webbrowser
import winreg
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as write_wav
import keyboard
import pyperclip
import pyautogui
from groq import Groq
import customtkinter as ctk
from datetime import datetime

# Analytics (optional)
try:
    from analytics import get_analytics, track
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    def track(*args, **kwargs): pass
    def get_analytics(*args, **kwargs): return None

# App info
APP_NAME = "VTT"
APP_VERSION = "2.2"
CONFIG_FILE = "settings.json"
HISTORY_FILE = "history.json"
TERMS_FILE = "terms.json"
ADMIN_MODE_FILE = "admin.key"  # If this file exists, admin mode is enabled

# Check if admin mode
ADMIN_MODE = os.path.exists(ADMIN_MODE_FILE) or "--admin" in sys.argv

# Pixel Gun Style Colors
COLORS = {
    "bg": "#0d0015",
    "bg_secondary": "#1a0a2e",
    "bg_card": "#2a1045",
    "bg_hover": "#3d1a5c",
    "accent": "#ff6b35",
    "accent_glow": "#ff9f1c",
    "success": "#39ff14",
    "warning": "#ffdd00",
    "error": "#ff0080",
    "text": "#ffffff",
    "text_secondary": "#00d4ff",
    "text_muted": "#8b5cf6",
    "border": "#ff6b35",
    "metallic": "#00d4ff",
    "metallic_silver": "#e8e8e8",  # Shiny silver for Build text
    "recording": "#ff0080",
    "recording_glow": "#ff69b4",
    "widget_bg": "#1a0a2e"
}

# Translations
TEXTS = {
    "ru": {
        "subtitle": "by @SAINT4AI",
        "api_key": "API КЛЮЧ GROQ",
        "api_key_desc": "Бесплатный ключ для распознавания речи. Получи на console.groq.com",
        "paste": "Вставить",
        "connected": "Подключено",
        "not_connected": "Не подключено",
        "mic": "МИКРОФОН",
        "mic_desc": "Выбери микрофон и проверь уровень звука кнопкой Тест",
        "level": "Уровень",
        "test": "Тест",
        "stop": "Стоп",
        "hotkey": "ГОРЯЧАЯ КЛАВИША",
        "hotkey_desc": "Нажми эту клавишу в любом приложении для записи голоса",
        "change": "Изменить",
        "options": "НАСТРОЙКИ",
        "auto_paste": "Автовставка текста",
        "auto_paste_desc": "Автоматически вставлять текст в активное поле после записи",
        "copy_clip": "Копировать в буфер",
        "copy_clip_desc": "Копировать распознанный текст в буфер обмена",
        "sounds": "Звуковые оповещения",
        "sounds_desc": "Воспроизводить звуки при начале и окончании записи",
        "autostart": "Запуск с Windows",
        "autostart_desc": "Автоматически запускать VTT при включении компьютера",
        "history": "ИСТОРИЯ",
        "history_desc": "Все твои транскрибации сохраняются здесь",
        "no_history": "Пока нет записей",
        "copy": "Копировать",
        "done": "Готово!",
        "loading": "Загрузка...",
        "init_app": "Инициализация приложения...",
        "load_settings": "Загрузка настроек...",
        "init_audio": "Инициализация аудио...",
        "connect_api": "Подключение к API...",
        "ready": "Готов к работе!",
        "view_all": "Смотреть всё",
        "close": "Закрыть",
        "clear_all": "Очистить всё",
        "history_title": "История транскрибаций",
        "copied": "Скопировано!",
        "deleted": "Удалено",
        # AI Brain
        "ai_brain": "AI-МОЗГ (LLaMA)",
        "ai_brain_desc": "Улучшает текст с помощью нейросети LLaMA 3.1",
        "ai_brain_enable": "Включить AI-мозг",
        "ai_brain_warn": "⚠️ Расход API увеличится в 1.5 раза",
        "ai_brain_benefits": "✓ Исправляет ошибки транскрипции\n✓ Добавляет пунктуацию\n✓ Распознаёт IT-термины\n✓ Улучшает грамматику",
        "ai_brain_context": "Запоминать контекст",
        "ai_processing": "AI улучшает...",
    },
    "kk": {
        "subtitle": "@SAINT4AI жасаған",
        "api_key": "GROQ API КІЛТІ",
        "api_key_desc": "Тегін сөйлеуді тану кілті. console.groq.com сайтынан алыңыз",
        "paste": "Қою",
        "connected": "Қосылды",
        "not_connected": "Қосылмаған",
        "mic": "МИКРОФОН",
        "mic_desc": "Микрофонды таңдап, Тест түймесімен дыбыс деңгейін тексеріңіз",
        "level": "Деңгей",
        "test": "Тест",
        "stop": "Тоқта",
        "hotkey": "ЖЫЛДАМ ПЕРНЕ",
        "hotkey_desc": "Дауыс жазу үшін кез келген қолданбада осы пернені басыңыз",
        "change": "Өзгерту",
        "options": "БАПТАУЛАР",
        "auto_paste": "Автоматты қою",
        "auto_paste_desc": "Жазудан кейін мәтінді белсенді өріске автоматты қою",
        "copy_clip": "Буферге көшіру",
        "copy_clip_desc": "Танылған мәтінді алмасу буферіне көшіру",
        "sounds": "Дыбыстық хабарламалар",
        "sounds_desc": "Жазу басталғанда және аяқталғанда дыбыс ойнату",
        "autostart": "Windows-пен қосу",
        "autostart_desc": "Компьютер қосылғанда VTT автоматты түрде іске қосылады",
        "history": "ТАРИХ",
        "history_desc": "Барлық транскрипцияларыңыз осында сақталады",
        "no_history": "Әзірге жазбалар жоқ",
        "copy": "Көшіру",
        "done": "Дайын!",
        "loading": "Жүктелуде...",
        "init_app": "Қолданба іске қосылуда...",
        "load_settings": "Баптаулар жүктелуде...",
        "init_audio": "Аудио инициализациясы...",
        "connect_api": "API-ге қосылу...",
        "ready": "Жұмысқа дайын!",
        "view_all": "Барлығын көру",
        "close": "Жабу",
        "clear_all": "Барлығын тазалау",
        "history_title": "Транскрипция тарихы",
        "copied": "Көшірілді!",
        "deleted": "Жойылды",
        # AI Brain
        "ai_brain": "AI-МИ (LLaMA)",
        "ai_brain_desc": "LLaMA 3.1 нейрожелісі арқылы мәтінді жақсартады",
        "ai_brain_enable": "AI-миды қосу",
        "ai_brain_warn": "⚠️ API шығыны 1.5 есе артады",
        "ai_brain_benefits": "✓ Транскрипция қателерін түзетеді\n✓ Тыныс белгілерін қосады\n✓ IT терминдерді танады\n✓ Грамматиканы жақсартады",
        "ai_brain_context": "Контекстті есте сақтау",
        "ai_processing": "AI жақсартуда...",
    }
}

DEFAULT_SETTINGS = {
    "api_key": "",
    "hotkey": "F9",
    "microphone": "",
    "language": "ru",
    "ui_lang": "ru",
    "auto_paste": True,
    "copy_clipboard": True,
    "sounds": True,
    "autostart": False,
    # AI Brain (uses same Groq API key)
    "ai_brain_enabled": False,
    "ai_brain_context": True
}


class AnimatedBackground(ctk.CTkCanvas):
    """Pixel Gun style animated background with particles flying to sun."""

    def __init__(self, master, **kwargs):
        super().__init__(master, highlightthickness=0, **kwargs)
        self.configure(bg=COLORS["bg"])

        self.particles = []
        self.sun_x = 0
        self.sun_y = 0
        self.animation_running = True

        # Create initial particles
        self.after(100, self._init_particles)
        self.after(150, self._animate)

    def _init_particles(self):
        """Create particles that will fly towards the sun."""
        w = self.winfo_width() or 360
        h = self.winfo_height() or 620

        self.sun_x = w // 2
        self.sun_y = 60  # Sun at top center

        # Create 15 particles
        import random
        for _ in range(15):
            self.particles.append({
                "x": random.randint(0, w),
                "y": random.randint(h // 2, h),
                "speed": random.uniform(0.3, 1.0),
                "size": random.randint(1, 3),
                "alpha": random.uniform(0.3, 0.8)
            })

    def _animate(self):
        if not self.animation_running:
            return

        self.delete("all")
        w = self.winfo_width() or 360
        h = self.winfo_height() or 620
        self.sun_x = w // 2
        self.sun_y = 60

        # Draw subtle gradient rays from sun
        for i in range(8):
            angle = (i / 8) * 3.14159 * 2 + (time.time() * 0.1)
            length = 300
            x2 = self.sun_x + math.cos(angle) * length
            y2 = self.sun_y + math.sin(angle) * length
            # Faded ray color
            self.create_line(
                self.sun_x, self.sun_y, x2, y2,
                fill="#1a0a2e", width=20
            )

        # Draw sun glow
        for r in range(40, 10, -5):
            alpha = (40 - r) / 30
            color = self._blend_color(COLORS["bg"], COLORS["accent_glow"], alpha * 0.3)
            self.create_oval(
                self.sun_x - r, self.sun_y - r,
                self.sun_x + r, self.sun_y + r,
                fill=color, outline=""
            )

        # Sun core
        self.create_oval(
            self.sun_x - 8, self.sun_y - 8,
            self.sun_x + 8, self.sun_y + 8,
            fill=COLORS["accent"], outline=""
        )

        # Update and draw particles
        import random
        for p in self.particles:
            # Move towards sun
            dx = self.sun_x - p["x"]
            dy = self.sun_y - p["y"]
            dist = max(1, (dx**2 + dy**2) ** 0.5)

            p["x"] += (dx / dist) * p["speed"] * 2
            p["y"] += (dy / dist) * p["speed"] * 2

            # Reset if reached sun
            if dist < 20:
                p["x"] = random.randint(0, w)
                p["y"] = random.randint(h // 2, h)
                p["speed"] = random.uniform(0.3, 1.0)

            # Draw particle with trail
            color = self._blend_color(COLORS["bg"], COLORS["metallic"], p["alpha"])
            s = p["size"]
            self.create_oval(
                p["x"] - s, p["y"] - s,
                p["x"] + s, p["y"] + s,
                fill=color, outline=""
            )

        self.after(50, self._animate)

    def _blend_color(self, c1, c2, alpha):
        """Blend two hex colors."""
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        r = int(r1 * (1 - alpha) + r2 * alpha)
        g = int(g1 * (1 - alpha) + g2 * alpha)
        b = int(b1 * (1 - alpha) + b2 * alpha)
        return f"#{r:02x}{g:02x}{b:02x}"

    def stop(self):
        self.animation_running = False


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
    """Premium animated recording button with integrated background animation."""

    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.command = command
        self.is_recording = False
        self.animation_running = False
        self.pulse_phase = 0.0
        self.audio_level = 0.0
        self.target_level = 0.0
        self.glow_intensity = 0.0
        self.bg_phase = 0.0  # For background animation

        # Canvas - with integrated animation (smaller size)
        self.size = 85
        self.canvas = ctk.CTkCanvas(
            self, width=self.size, height=self.size,
            highlightthickness=0, bg=COLORS["bg"]
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", lambda e: command() if command else None)
        self.canvas.bind("<Enter>", self._on_hover)
        self.canvas.bind("<Leave>", self._on_leave)
        self.hover = False

        # Start background animation for this button
        self._animate_bg()

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

        # Timer display (hidden by default)
        self.timer_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLORS["recording"]
        )
        self.max_duration = 300  # seconds
        self.current_time = 0

        self.draw_idle()

    def _on_hover(self, e):
        self.hover = True
        if not self.is_recording:
            self.draw_idle()

    def _on_leave(self, e):
        self.hover = False
        if not self.is_recording:
            self.draw_idle()

    def _animate_bg(self):
        """Animate background particles on button canvas."""
        if not self.is_recording:
            self.bg_phase = (self.bg_phase + 0.02) % 1.0
            # Redraw with animated background
            self._draw_with_bg()
        self.after(50, self._animate_bg)

    def _draw_with_bg(self):
        """Draw button with animated background effects."""
        self.canvas.delete("all")
        cx, cy = self.size // 2, self.size // 2

        # Draw animated rays from center (like sun rays)
        import math
        for i in range(6):
            angle = (i / 6) * math.pi * 2 + (self.bg_phase * math.pi * 2)
            # Inner point
            x1 = cx + math.cos(angle) * 35
            y1 = cy + math.sin(angle) * 35
            # Outer point
            x2 = cx + math.cos(angle) * 52
            y2 = cy + math.sin(angle) * 52
            # Faint ray
            self.canvas.create_line(x1, y1, x2, y2, fill="#1a0a2e", width=8)

        # Draw small particles moving outward
        for i in range(4):
            angle = (i / 4) * math.pi * 2 + (self.bg_phase * math.pi * 4)
            dist = 30 + (self.bg_phase * 25) % 25
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            self.canvas.create_oval(px-2, py-2, px+2, py+2, fill="#00d4ff", outline="")

        # Now draw the actual button on top
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

        # Main circle with semi-transparent effect
        fill = COLORS["bg_hover"] if self.hover else COLORS["bg_card"]
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=fill, outline=COLORS["border"], width=2
        )

        # Mic icon
        self._draw_premium_mic(cx, cy, COLORS["text_secondary"] if not self.hover else COLORS["accent"])

    def draw_idle(self):
        """Draw elegant idle state (called by _draw_with_bg now)."""
        # This is now handled by _draw_with_bg for animated version
        pass

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
        self.current_time = 0
        self.status.configure(text="Запись...", text_color=COLORS["recording"])
        self.timer_label.configure(text=f"0 сек / {self.max_duration}")
        self.timer_label.pack(pady=(2, 0))
        self._animate()

    def stop_recording(self):
        self.is_recording = False
        self.animation_running = False
        self.audio_level = 0
        self.timer_label.pack_forget()  # Hide timer
        self.status.configure(text="Обработка...", text_color=COLORS["warning"])

    def update_timer(self, seconds):
        """Update the recording timer display."""
        self.current_time = seconds
        self.timer_label.configure(text=f"{int(seconds)} сек / {self.max_duration}")

    def reset(self):
        self.timer_label.pack_forget()  # Hide timer
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
    """Floating draggable widget when app is minimized. Resizable with mouse wheel."""

    # Size limits
    MIN_SIZE = 28   # Tiny icon like Windows tray
    MAX_SIZE = 120  # Large comfortable size
    DEFAULT_SIZE = 70

    def __init__(self, master, toggle_callback, **kwargs):
        super().__init__(master, **kwargs)

        self.toggle_callback = toggle_callback
        self.is_recording = False

        # Window setup - no decorations, always on top
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.95)
        self.configure(fg_color=COLORS["widget_bg"])

        # Size - resizable
        self.size = self.DEFAULT_SIZE
        self.geometry(f"{self.size}x{self.size}+100+100")

        # Canvas
        self.canvas = ctk.CTkCanvas(
            self, width=self.size, height=self.size,
            bg=COLORS["widget_bg"], highlightthickness=0
        )
        self.canvas.pack()

        # Drag state - separate drag from click
        self._drag_data = {"x": 0, "y": 0, "dragging": False, "moved": False}
        self.pulse_phase = 0
        self.animation_running = False

        # Bind events
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        # Mouse wheel for resizing
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<MouseWheel>", self._on_mousewheel)

        self.draw_idle()
        self.withdraw()  # Start hidden

    def _on_mousewheel(self, event):
        """Resize widget with mouse wheel."""
        # event.delta > 0 = scroll up = increase size
        # event.delta < 0 = scroll down = decrease size
        step = 8
        if event.delta > 0:
            new_size = min(self.MAX_SIZE, self.size + step)
        else:
            new_size = max(self.MIN_SIZE, self.size - step)

        if new_size != self.size:
            self._resize(new_size)

    def _resize(self, new_size):
        """Resize the widget to new size."""
        self.size = new_size
        # Keep center position
        x = self.winfo_x() + (self.canvas.winfo_width() - new_size) // 2
        y = self.winfo_y() + (self.canvas.winfo_height() - new_size) // 2
        # Update canvas and window
        self.canvas.configure(width=new_size, height=new_size)
        self.geometry(f"{new_size}x{new_size}+{x}+{y}")
        # Redraw
        if self.is_recording:
            self.draw_recording()
        else:
            self.draw_idle()

    def _is_in_center(self, x, y):
        """Check if click is in the center button area."""
        cx, cy = self.size // 2, self.size // 2
        # Click radius scales with size
        click_radius = max(10, self.size * 0.3)
        dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        return dist <= click_radius

    def _on_press(self, event):
        """Handle mouse press - prepare for drag or click."""
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self._drag_data["moved"] = False
        # Check if in drag zone (outer ring) or button zone (center)
        self._drag_data["in_center"] = self._is_in_center(event.x, event.y)

    def _on_drag(self, event):
        """Handle dragging - move window, don't trigger recording."""
        dx = abs(event.x - self._drag_data["x"])
        dy = abs(event.y - self._drag_data["y"])

        # Only start dragging if moved more than 5 pixels
        if dx > 5 or dy > 5:
            self._drag_data["moved"] = True

        if self._drag_data["moved"]:
            # Calculate new position
            x = self.winfo_x() + event.x - self._drag_data["x"]
            y = self.winfo_y() + event.y - self._drag_data["y"]

            # Clamp to screen bounds
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = max(0, min(x, screen_w - self.size))
            y = max(0, min(y, screen_h - self.size))

            self.geometry(f"+{x}+{y}")

    def _on_release(self, event):
        """Handle mouse release - toggle recording only if didn't drag."""
        if not self._drag_data["moved"] and self._drag_data["in_center"]:
            # Click in center without dragging - toggle recording
            self.toggle_callback()
        self._drag_data["moved"] = False

    def _on_double_click(self, event):
        # Double click restores main window
        self.master.deiconify()
        self.master.lift()
        self.withdraw()

    def draw_idle(self):
        self.canvas.delete("all")
        cx, cy = self.size // 2, self.size // 2
        # Scale factor based on size (1.0 at default 70px)
        scale = self.size / self.DEFAULT_SIZE
        r = int(22 * scale)  # Center button radius scales

        # Outer drag ring (only if big enough)
        if self.size >= 50:
            outer_r = int(32 * scale)
            self.canvas.create_oval(
                cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                fill="", outline=COLORS["text_muted"], width=1, dash=(3, 3)
            )

        # Main circle button
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=COLORS["bg_card"], outline=COLORS["accent"], width=max(1, int(2 * scale))
        )

        # Mic icon (scaled)
        if self.size >= 40:
            # Full mic icon
            mic_w = int(5 * scale)
            mic_h = int(6 * scale)
            self.canvas.create_oval(cx-mic_w, cy-int(10*scale), cx+mic_w, cy+int(2*scale), fill=COLORS["accent"], outline="")
            arc_w = int(9 * scale)
            self.canvas.create_arc(cx-arc_w, cy-int(4*scale), cx+arc_w, cy+int(8*scale), start=0, extent=-180, style="arc", outline=COLORS["accent"], width=max(1, int(2*scale)))
            self.canvas.create_line(cx, cy+int(8*scale), cx, cy+int(13*scale), fill=COLORS["accent"], width=max(1, int(2*scale)))
        else:
            # Tiny dot for very small sizes
            dot_r = max(2, int(4 * scale))
            self.canvas.create_oval(cx-dot_r, cy-dot_r, cx+dot_r, cy+dot_r, fill=COLORS["accent"], outline="")

    def draw_recording(self):
        self.canvas.delete("all")
        cx, cy = self.size // 2, self.size // 2
        # Scale factor
        scale = self.size / self.DEFAULT_SIZE
        r = int(22 * scale)

        # Outer drag ring (only if big enough)
        if self.size >= 50:
            outer_r = int(32 * scale)
            self.canvas.create_oval(
                cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                fill="", outline=COLORS["text_muted"], width=1, dash=(3, 3)
            )

        # Pulse ring
        phase = self.pulse_phase
        ring_r = r + int(2 * scale) + phase * int(6 * scale)
        self.canvas.create_oval(
            cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r,
            fill="", outline=COLORS["recording"], width=max(1, int(2 * scale))
        )

        # Main circle
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=COLORS["recording"], outline=""
        )

        # Stop icon (scaled)
        sq = max(3, int(7 * scale))
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


class SplashScreen(ctk.CTkToplevel):
    """Loading splash screen with animated logs."""

    def __init__(self, master, lang="ru"):
        super().__init__(master)
        self.lang = lang
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=COLORS["bg"])

        # Center on screen
        w, h = 320, 280
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Content
        ctk.CTkLabel(
            self, text="VTT",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(pady=(40, 5))

        ctk.CTkLabel(
            self, text="@SAINT4AI",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["metallic"]
        ).pack()

        # Progress bar
        self.progress = ctk.CTkProgressBar(
            self, width=200, height=8,
            fg_color=COLORS["bg_secondary"],
            progress_color=COLORS["accent"]
        )
        self.progress.pack(pady=30)
        self.progress.set(0)

        # Status label
        self.status = ctk.CTkLabel(
            self, text=self._t("loading"),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        )
        self.status.pack()

        # Log area
        self.log_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_secondary"],
            justify="left"
        )
        self.log_label.pack(pady=(20, 10))

        self.logs = []

    def _t(self, key):
        return TEXTS.get(self.lang, TEXTS["ru"]).get(key, key)

    def update_progress(self, value, status_key, log_text=None):
        self.progress.set(value)
        self.status.configure(text=self._t(status_key))
        if log_text:
            self.logs.append(f"> {log_text}")
            if len(self.logs) > 4:
                self.logs = self.logs[-4:]
            self.log_label.configure(text="\n".join(self.logs))
        self.update()


class HistoryWindow(ctk.CTkToplevel):
    """Full history popup window with scroll and copy functionality."""

    def __init__(self, master, history, lang="ru", on_update=None):
        super().__init__(master)
        self.history = history
        self.lang = lang
        self.on_update = on_update  # Callback to update main window

        self.title(self._t("history_title"))
        self.geometry("420x500")
        self.configure(fg_color=COLORS["bg"])
        self.attributes("-topmost", True)

        # Center on screen
        self.update_idletasks()
        w, h = 420, 500
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            header, text=self._t("history_title"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(side="left")

        ctk.CTkButton(
            header, text=self._t("close"), width=70, height=28,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["bg_hover"],
            border_width=1, border_color=COLORS["border"],
            command=self.destroy
        ).pack(side="right")

        # Scrollable history list
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"]
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=16, pady=8)

        # Populate history items
        self._populate_history()

        # Footer with clear all button
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(8, 16))

        self.status_label = ctk.CTkLabel(
            footer, text=f"{len(self.history)} items",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        )
        self.status_label.pack(side="left")

        ctk.CTkButton(
            footer, text=self._t("clear_all"), width=100, height=28,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["error"],
            hover_color="#ff3399",
            command=self._clear_all
        ).pack(side="right")

    def _t(self, key):
        return TEXTS.get(self.lang, TEXTS["ru"]).get(key, key)

    def _populate_history(self):
        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.history:
            ctk.CTkLabel(
                self.scroll_frame, text=self._t("no_history"),
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_muted"]
            ).pack(pady=20)
            return

        for i, entry in enumerate(self.history):
            self._create_history_item(i, entry)

    def _create_history_item(self, index, entry):
        """Create a single history item card."""
        card = ctk.CTkFrame(
            self.scroll_frame, fg_color=COLORS["bg_card"],
            corner_radius=8, border_width=1,
            border_color=COLORS["border"]
        )
        card.pack(fill="x", pady=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)

        # Timestamp
        timestamp = entry.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%d.%m %H:%M")
            except:
                time_str = ""
        else:
            time_str = ""

        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(
            top_row, text=time_str,
            font=ctk.CTkFont(size=9),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        btn_frame.pack(side="right")

        copy_btn = ctk.CTkButton(
            btn_frame, text=self._t("copy"), width=60, height=22,
            font=ctk.CTkFont(size=9),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_glow"],
            command=lambda t=entry["text"], b=None: self._copy_item(t, copy_btn)
        )
        copy_btn.pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            btn_frame, text="✕", width=22, height=22,
            font=ctk.CTkFont(size=10),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["error"],
            command=lambda idx=index: self._delete_item(idx)
        ).pack(side="left")

        # Text content
        text = entry.get("text", "")
        ctk.CTkLabel(
            inner, text=text,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text"],
            wraplength=360,
            anchor="w",
            justify="left"
        ).pack(fill="x", pady=(6, 0))

    def _copy_item(self, text, btn):
        """Copy text to clipboard."""
        pyperclip.copy(text)
        original = btn.cget("text")
        btn.configure(text=self._t("copied"), fg_color=COLORS["success"])
        self.after(1000, lambda: btn.configure(text=original, fg_color=COLORS["accent"]))

    def _delete_item(self, index):
        """Delete a history item."""
        if 0 <= index < len(self.history):
            self.history.pop(index)
            self._populate_history()
            self.status_label.configure(text=f"{len(self.history)} items")
            if self.on_update:
                self.on_update()

    def _clear_all(self):
        """Clear all history."""
        self.history.clear()
        self._populate_history()
        self.status_label.configure(text="0 items")
        if self.on_update:
            self.on_update()


class VoiceToTextApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Load settings first for language
        self.settings = self._load_settings_quick()

        self.title("VTT")
        self.geometry("360x620")
        self.minsize(340, 550)
        self.configure(fg_color=COLORS["bg"])
        self._set_icon()

        ctk.set_appearance_mode("dark")

        # State
        self.is_recording = False
        self.audio_data = []
        self.groq_client = None
        self.current_hotkey = None
        self.mic_devices = {}
        self.history = []
        self.last_focused_window = None

        # Show splash screen and start loading
        self.withdraw()  # Hide main window
        self.splash = SplashScreen(self, self.settings.get("ui_lang", "ru"))
        self.after(100, self._loading_step1)

    def _loading_step1(self):
        self.splash.update_progress(0.2, "init_app", "Starting VTT...")
        self.after(200, self._loading_step2)

    def _loading_step2(self):
        self.splash.update_progress(0.4, "load_settings", "Loading settings.json")
        self.settings = self.load_settings()
        self.after(200, self._loading_step3)

    def _loading_step3(self):
        self.splash.update_progress(0.6, "init_audio", "Initializing sounddevice")
        self.load_history()
        self.after(200, self._loading_step4)

    def _loading_step4(self):
        self.splash.update_progress(0.8, "connect_api", "Checking Groq API")
        self.after(200, self._loading_step5)

    def _loading_step5(self):
        self.splash.update_progress(1.0, "ready", "All systems ready!")
        self.after(300, self._finish_loading)

    def _finish_loading(self):
        self.splash.destroy()

        # Initialize analytics
        if ANALYTICS_AVAILABLE:
            self.analytics = get_analytics(APP_VERSION)
            self.analytics.track_session()
        else:
            self.analytics = None
        self.deiconify()  # Show main window

        self.create_ui()
        self.refresh_mics()
        self.setup_hotkey()
        self.check_api()

        # Window events
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Unmap>", self._on_minimize)
        self.bind("<Map>", self._on_restore)

    def _on_minimize(self, event):
        if self.state() == 'iconic':
            self.floating_widget.show()

    def _on_restore(self, event):
        self.floating_widget.hide()

    def _load_settings_quick(self):
        """Quick settings load for splash screen language."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return DEFAULT_SETTINGS.copy()

    def _set_icon(self):
        """Set window icon."""
        try:
            icon_paths = []

            # When running as PyInstaller EXE
            if getattr(sys, 'frozen', False):
                # 1. PyInstaller temp folder (--add-data)
                if hasattr(sys, '_MEIPASS'):
                    icon_paths.append(os.path.join(sys._MEIPASS, "icon.ico"))
                # 2. Same directory as EXE
                icon_paths.append(os.path.join(os.path.dirname(sys.executable), "icon.ico"))
            else:
                # Running as script
                icon_paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico"))

            # Also try current directory
            icon_paths.append("icon.ico")

            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    self.iconbitmap(icon_path)
                    print(f"[DEBUG] Icon loaded: {icon_path}")
                    return
            print("[DEBUG] No icon found in paths:", icon_paths)
        except Exception as e:
            print(f"[DEBUG] Icon error: {e}")

    def t(self, key):
        """Get translation."""
        lang = self.settings.get("ui_lang", "ru")
        return TEXTS.get(lang, TEXTS["ru"]).get(key, key)

    def toggle_language(self):
        """Switch between RU and KZ."""
        current = self.settings.get("ui_lang", "ru")
        self.settings["ui_lang"] = "kk" if current == "ru" else "ru"
        self.save_settings()
        # Rebuild UI
        for w in self.winfo_children():
            w.destroy()
        self.create_ui()
        self.refresh_mics()
        self.check_api()

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

    def get_exe_path(self):
        """Get the path to the executable."""
        if getattr(sys, 'frozen', False):
            # Running as compiled EXE
            return sys.executable
        else:
            # Running as script
            return os.path.abspath(__file__)

    def set_autostart(self, enable):
        """Enable or disable autostart with Windows."""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)

            if enable:
                exe_path = self.get_exe_path()
                winreg.SetValueEx(key, "VTT_SAINT4AI", 0, winreg.REG_SZ, f'"{exe_path}"')
                print(f"[DEBUG] Autostart enabled: {exe_path}")
            else:
                try:
                    winreg.DeleteValue(key, "VTT_SAINT4AI")
                    print("[DEBUG] Autostart disabled")
                except FileNotFoundError:
                    pass  # Key doesn't exist, that's OK

            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"[ERROR] Autostart: {e}")
            return False

    def check_autostart(self):
        """Check if autostart is currently enabled."""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "VTT_SAINT4AI")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except:
            return False

    def toggle_autostart(self):
        """Toggle autostart setting."""
        enable = self.autostart_var.get()
        success = self.set_autostart(enable)
        if success:
            self.settings["autostart"] = enable
            self.save_settings()
        else:
            # Revert checkbox if failed
            self.autostart_var.set(not enable)

    def add_to_history(self, text):
        """Add transcription to history."""
        entry = {
            "text": text,
            "timestamp": datetime.now().isoformat(),
        }
        self.history.insert(0, entry)
        self.save_history()

    def load_terms_dict(self):
        """Load terms dictionary from file."""
        try:
            if os.path.exists(TERMS_FILE):
                with open(TERMS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Flatten all categories into one dict
                    terms = {}
                    for category, items in data.items():
                        if isinstance(items, dict) and category != "_comment":
                            terms.update(items)
                    return terms
        except Exception as e:
            print(f"[ERROR] Load terms: {e}")
        return {}

    def apply_terms_dict(self, text):
        """Apply terms dictionary to text (replace misheard words)."""
        terms = self.load_terms_dict()
        result = text.lower()
        for wrong, correct in terms.items():
            if wrong in result:
                result = result.replace(wrong, correct)
        # Restore original case for first letter if was capitalized
        if text and text[0].isupper():
            result = result[0].upper() + result[1:] if len(result) > 1 else result.upper()
        return result

    def process_with_ai_brain(self, text):
        """Enhance text using AI Brain (Groq LLaMA) with smart dictionary."""
        if not self.settings.get("ai_brain_enabled") or not self.groq_client:
            return text

        try:
            # First pass: apply local terms dictionary
            text = self.apply_terms_dict(text)

            # Load terms for context hint (just category names, not all terms)
            terms = self.load_terms_dict()
            terms_hint = ", ".join(list(terms.values())[:20])  # Top 20 terms as hint

            # Compact prompt - minimal tokens
            prompt = f"""Исправь текст голосовой транскрипции:
- Грамматика и пунктуация
- Это может быть про: {terms_hint}
- Верни ТОЛЬКО исправленный текст

{text}"""

            response = self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.2
            )

            improved = response.choices[0].message.content.strip()
            return improved if improved else text

        except Exception as e:
            print(f"[ERROR] AI Brain: {e}")
            return text

    def create_ui(self):
        # Floating widget (recreate if needed)
        if not hasattr(self, 'floating_widget') or not self.floating_widget.winfo_exists():
            self.floating_widget = FloatingWidget(self, self.toggle_recording)

        # Animated background
        if not hasattr(self, 'bg_canvas') or not self.bg_canvas.winfo_exists():
            self.bg_canvas = AnimatedBackground(self)
            self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Main container (on top of background) - wider settings area
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=6, pady=4)
        main.lift()  # Ensure it's above background

        # Header with language button
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", pady=(0, 2))

        # Language switch button (top right)
        lang_btn = ctk.CTkButton(
            header,
            text="KZ" if self.settings.get("ui_lang") == "ru" else "RU",
            width=40, height=24,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_hover"],
            border_width=1, border_color=COLORS["accent"],
            command=self.toggle_language
        )
        lang_btn.place(relx=1.0, x=-5, y=0, anchor="ne")

        ctk.CTkLabel(
            header, text="VTT",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="center")

        ctk.CTkLabel(
            header, text=self.t("subtitle"),
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["metallic"]
        ).pack(anchor="center")

        # Record button (compact)
        self.record_btn = PremiumRecordButton(main, command=self.toggle_recording)
        self.record_btn.pack(pady=4)

        # Scrollable settings
        settings_frame = ctk.CTkScrollableFrame(
            main, fg_color="transparent",
            scrollbar_button_color=COLORS["border"]
        )
        settings_frame.pack(fill="both", expand=True)

        # === HISTORY SECTION (FIRST!) ===
        self._section(settings_frame, f"{self.t('history')} ({len(self.history)})", self.t("history_desc"))
        hist_frame = self._card(settings_frame)

        # History label - show 2 lines of text
        self.history_label = ctk.CTkLabel(
            hist_frame,
            text=self._get_last_history() if self.history else self.t("no_history"),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            wraplength=280,  # Wider for 2 lines
            anchor="w",
            justify="left"
        )
        self.history_label.pack(fill="x", pady=(0, 6))

        # History buttons row
        hist_btn_row = ctk.CTkFrame(hist_frame, fg_color="transparent")
        hist_btn_row.pack(fill="x")

        ctk.CTkButton(
            hist_btn_row, text=self.t("view_all"), width=100, height=26,
            font=ctk.CTkFont(size=10),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_glow"],
            command=self.open_history_window
        ).pack(side="left", padx=(0, 8))

        self.copy_hist_btn = ctk.CTkButton(
            hist_btn_row, text=self.t("copy"), width=80, height=26,
            font=ctk.CTkFont(size=10),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["bg_hover"],
            border_width=1, border_color=COLORS["border"],
            command=self.copy_last_history
        )
        if self.history:
            self.copy_hist_btn.pack(side="left")

        # Store reference for updating title
        self.history_title = None  # Will be the section label

        # API Key
        self._section(settings_frame, self.t("api_key"), self.t("api_key_desc"))
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
            api_row, text=self.t("paste"), width=70, height=32,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_glow"],
            command=self.paste_api_key
        ).pack(side="right")

        if self.settings["api_key"]:
            self.api_entry.insert(0, self.settings["api_key"])

        # Status and help row
        status_row = ctk.CTkFrame(api_frame, fg_color="transparent")
        status_row.pack(fill="x")

        self.api_status = ctk.CTkLabel(
            status_row, text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        )
        self.api_status.pack(side="left")

        # "How to get?" button
        self.api_help_btn = ctk.CTkButton(
            status_row, text="▶ Как получить?", width=100, height=20,
            font=ctk.CTkFont(size=9),
            fg_color="transparent",
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["metallic"],
            command=self.toggle_api_help
        )
        self.api_help_btn.pack(side="right")

        # Expandable instructions (hidden by default)
        self.api_help_frame = ctk.CTkFrame(api_frame, fg_color=COLORS["bg_secondary"], corner_radius=8)
        self.api_help_text = ctk.CTkLabel(
            self.api_help_frame,
            text="""📋 Как получить API ключ Groq (бесплатно):

1️⃣ Открой console.groq.com
2️⃣ Нажми "Sign Up" → создай аккаунт (Google/GitHub)
3️⃣ В меню слева выбери "API Keys"
4️⃣ Нажми "Create API Key"
5️⃣ Скопируй ключ (начинается с gsk_)
6️⃣ Вставь его сюда ↑

💡 Ключ бесплатный, лимит ~14,400 запросов/день""",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text"],
            justify="left",
            anchor="w"
        )
        self.api_help_text.pack(padx=10, pady=8)
        self.api_help_visible = False

        self.api_entry.bind("<Return>", lambda e: self.save_api())
        self.api_entry.bind("<FocusOut>", lambda e: self.save_api())

        # Microphone
        self._section(settings_frame, self.t("mic"), self.t("mic_desc"))
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
            level_row, text=self.t("level"),
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
            level_row, text=self.t("test"), width=50, height=22,
            font=ctk.CTkFont(size=10),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["bg_hover"],
            border_width=1, border_color=COLORS["border"],
            command=self.test_mic
        )
        self.test_btn.pack(side="right")
        self.mic_testing = False

        # Hotkey
        self._section(settings_frame, self.t("hotkey"), self.t("hotkey_desc"))
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
            hk_row, text=self.t("change"), width=70, height=28,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["bg_hover"],
            border_width=1, border_color=COLORS["border"],
            command=self.change_hotkey
        ).pack(side="right")

        # Options
        self._section(settings_frame, self.t("options"))
        opt_frame = self._card(settings_frame)

        self.auto_paste_var = ctk.BooleanVar(value=self.settings["auto_paste"])
        ctk.CTkCheckBox(
            opt_frame, text=self.t("auto_paste"),
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
            opt_frame, text=self.t("copy_clip"),
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
            opt_frame, text=self.t("sounds"),
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_glow"],
            border_color=COLORS["border"],
            variable=self.sounds_var,
            command=lambda: self._save_opt("sounds", self.sounds_var.get())
        ).pack(anchor="w", pady=2)

        # Autostart checkbox - check actual registry state
        actual_autostart = self.check_autostart()
        self.settings["autostart"] = actual_autostart
        self.autostart_var = ctk.BooleanVar(value=actual_autostart)
        ctk.CTkCheckBox(
            opt_frame, text=self.t("autostart"),
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_glow"],
            border_color=COLORS["border"],
            variable=self.autostart_var,
            command=self.toggle_autostart
        ).pack(anchor="w", pady=2)

        # AI Brain section - with description
        self._section(settings_frame, self.t("ai_brain"), self.t("ai_brain_desc"))
        ai_frame = self._card(settings_frame)

        # AI Brain enable checkbox
        self.ai_brain_var = ctk.BooleanVar(value=self.settings.get("ai_brain_enabled", False))
        ctk.CTkCheckBox(
            ai_frame, text=self.t("ai_brain_enable"),
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"],
            fg_color=COLORS["success"],
            hover_color="#50ff50",
            border_color=COLORS["border"],
            variable=self.ai_brain_var,
            command=self.toggle_ai_brain
        ).pack(anchor="w", pady=2)

        # Benefits description (shown when enabled)
        self.ai_benefits_label = ctk.CTkLabel(
            ai_frame, text=self.t("ai_brain_benefits"),
            font=ctk.CTkFont(size=9),
            text_color=COLORS["success"],
            anchor="w",
            justify="left"
        )

        # Warning about API usage
        self.ai_warn_label = ctk.CTkLabel(
            ai_frame, text=self.t("ai_brain_warn"),
            font=ctk.CTkFont(size=9),
            text_color=COLORS["warning"],
            anchor="w"
        )

        # Show benefits and warning if enabled
        if self.settings.get("ai_brain_enabled"):
            self.ai_benefits_label.pack(anchor="w", padx=(24, 0), pady=(4, 0))
            self.ai_warn_label.pack(anchor="w", padx=(24, 0), pady=(2, 0))

        # AI Brain context checkbox
        self.ai_context_var = ctk.BooleanVar(value=self.settings.get("ai_brain_context", True))
        ctk.CTkCheckBox(
            ai_frame, text=self.t("ai_brain_context"),
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"],
            fg_color=COLORS["success"],
            hover_color="#50ff50",
            border_color=COLORS["border"],
            variable=self.ai_context_var,
            command=lambda: self._save_opt("ai_brain_context", self.ai_context_var.get())
        ).pack(anchor="w", pady=2)

        # Button to view/edit terms dictionary
        ctk.CTkButton(
            ai_frame, text="📖 Открыть словарь терминов",
            width=180, height=26,
            font=ctk.CTkFont(size=10),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["bg_hover"],
            border_width=1, border_color=COLORS["metallic"],
            text_color=COLORS["metallic"],
            command=self.open_terms_file
        ).pack(anchor="w", pady=(8, 2))

        # Footer with clickable links - compact
        footer = ctk.CTkFrame(main, fg_color="transparent")
        footer.pack(pady=(4, 0), fill="x")

        # Row 1: Instagram
        row1 = ctk.CTkFrame(footer, fg_color="transparent")
        row1.pack(anchor="center")

        ctk.CTkLabel(
            row1, text="Instagram: ",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        ig_link = ctk.CTkLabel(
            row1, text="@SAINT4AI",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["recording"],
            cursor="hand2"
        )
        ig_link.pack(side="left")
        ig_link.bind("<Button-1>", lambda e: webbrowser.open("https://www.instagram.com/saint4ai/"))
        ig_link.bind("<Enter>", lambda e: ig_link.configure(text_color=COLORS["accent"]))
        ig_link.bind("<Leave>", lambda e: ig_link.configure(text_color=COLORS["recording"]))

        # Row 2: Telegram chanel
        row2 = ctk.CTkFrame(footer, fg_color="transparent")
        row2.pack(anchor="center")

        ctk.CTkLabel(
            row2, text="Telegram chanel: ",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        ).pack(side="left")

        tg_link = ctk.CTkLabel(
            row2, text="VIBE-OPUS@saint4ai",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["metallic"],
            cursor="hand2"
        )
        tg_link.pack(side="left")
        tg_link.bind("<Button-1>", lambda e: webbrowser.open("https://t.me/+0alb9_Y1yv9mMDVi"))
        tg_link.bind("<Enter>", lambda e: tg_link.configure(text_color=COLORS["accent"]))
        tg_link.bind("<Leave>", lambda e: tg_link.configure(text_color=COLORS["metallic"]))

        # Row 3: Build number - metallic shine
        build_label = ctk.CTkLabel(
            footer, text="✦ Build 02-777-kz ✦",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=COLORS["metallic_silver"]
        )
        build_label.pack(anchor="center", pady=(2, 0))

        # Row 4: Users count (public metric)
        self.users_count_label = ctk.CTkLabel(
            footer, text="👥 ... пользователей",
            font=ctk.CTkFont(size=9),
            text_color=COLORS["text_muted"]
        )
        self.users_count_label.pack(anchor="center", pady=(2, 0))
        self._fetch_users_count()

        # Admin mode: Show dashboard button
        if ADMIN_MODE:
            admin_btn = ctk.CTkButton(
                footer, text="📊 Админ-панель",
                width=120, height=24,
                font=ctk.CTkFont(size=9),
                fg_color=COLORS["recording"],
                hover_color=COLORS["recording_glow"],
                command=self._open_admin_dashboard
            )
            admin_btn.pack(anchor="center", pady=(6, 0))

    def _fetch_users_count(self):
        """Fetch total users count from Supabase RPC (async)."""
        def fetch():
            try:
                import requests
                url = "https://qiyekjrpcewewxumhifc.supabase.co/rest/v1/rpc/count_unique_users"
                headers = {
                    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFpeWVranJwY2V3ZXd4dW1oaWZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgxNjY4OTYsImV4cCI6MjA4Mzc0Mjg5Nn0.a9E7f2Uox9fDxxty-m2eTfPuiT7iNoSWQwmHl6gk9jE",
                    "Content-Type": "application/json"
                }
                resp = requests.post(url, headers=headers, json={}, timeout=5)
                count = resp.json()
                if isinstance(count, int) and count > 0:
                    self.after(0, lambda: self.users_count_label.configure(
                        text=f"👥 {count:,} пользователей".replace(",", " ")
                    ))
            except:
                pass
        threading.Thread(target=fetch, daemon=True).start()

    def _open_admin_dashboard(self):
        """Open Supabase dashboard directly."""
        # Direct link to Supabase Table Editor
        webbrowser.open("https://supabase.com/dashboard/project/qiyekjrpcewewxumhifc/editor")

    def _get_last_history(self):
        """Get last history entry, show up to 100 chars (2 lines)."""
        if not self.history:
            return ""
        last = self.history[0]
        text = last["text"][:100] + "..." if len(last["text"]) > 100 else last["text"]
        return f'"{text}"'

    def copy_last_history(self):
        """Copy last history item to clipboard."""
        if self.history:
            text = self.history[0]["text"]
            pyperclip.copy(text)
            # Visual feedback
            original = self.copy_hist_btn.cget("text")
            self.copy_hist_btn.configure(text=self.t("done"), fg_color=COLORS["success"])
            self.after(1000, lambda: self.copy_hist_btn.configure(text=original, fg_color=COLORS["bg_secondary"]))

    def open_history_window(self):
        """Open the full history popup window."""
        HistoryWindow(self, self.history, self.settings.get("ui_lang", "ru"), self.update_history_display)

    def update_history_display(self):
        """Update history display after changes in popup."""
        self.save_history()
        self.history_label.configure(
            text=self._get_last_history() if self.history else self.t("no_history")
        )

    def _section(self, parent, title, desc=None):
        # Title - always left aligned
        title_label = ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text_muted"],
            anchor="w",
            justify="left"
        )
        title_label.pack(anchor="w", fill="x", pady=(12, 2))

        if desc:
            # Description - left aligned with proper wrapping
            desc_label = ctk.CTkLabel(
                parent, text=desc,
                font=ctk.CTkFont(size=9),
                text_color=COLORS["text_secondary"],
                wraplength=290,
                anchor="w",
                justify="left"
            )
            desc_label.pack(anchor="w", fill="x", pady=(0, 4))

    def _card(self, parent):
        """Create a Liquid Glass style card."""
        # Outer glow frame (glass effect)
        outer = ctk.CTkFrame(
            parent, fg_color="transparent",
            corner_radius=12
        )
        outer.pack(fill="x", pady=2)

        # Main card with gradient-like border
        card = ctk.CTkFrame(
            outer,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["metallic"]  # Cyan glow border
        )
        card.pack(fill="x", padx=1, pady=1)

        # Inner content frame
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
            self.test_btn.configure(text=self.t("test"), fg_color=COLORS["bg_secondary"])
            self.level_bar.set(0)
            return

        # Start testing
        self.mic_testing = True
        self.test_btn.configure(text=self.t("stop"), fg_color=COLORS["recording"])

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
                test_text = self.t("test")
                self.after(0, lambda: self.test_btn.configure(text=test_text, fg_color=COLORS["bg_secondary"]))
                self.mic_testing = False

        threading.Thread(target=monitor, daemon=True).start()

    def toggle_api_help(self):
        """Toggle API help instructions visibility."""
        if self.api_help_visible:
            self.api_help_frame.pack_forget()
            self.api_help_btn.configure(text="▶ Как получить?")
        else:
            self.api_help_frame.pack(fill="x", pady=(6, 0))
            self.api_help_btn.configure(text="▼ Скрыть")
        self.api_help_visible = not self.api_help_visible

    def open_terms_file(self):
        """Open terms dictionary file in default editor."""
        import subprocess
        terms_path = os.path.abspath(TERMS_FILE)
        if os.path.exists(terms_path):
            subprocess.Popen(['notepad', terms_path])
        else:
            # Create default terms file if doesn't exist
            self.create_default_terms()
            subprocess.Popen(['notepad', terms_path])

    def create_default_terms(self):
        """Create default terms dictionary file."""
        default_terms = {
            "_comment": "Словарь терминов для AI-мозга. Добавляй свои термины!",
            "programming": {"мейк": "make", "гитхаб": "GitHub", "реакт": "React"},
            "tools": {"вскод": "VS Code", "постман": "Postman"}
        }
        with open(TERMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_terms, f, indent=2, ensure_ascii=False)

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

    def toggle_ai_brain(self):
        """Toggle AI Brain feature."""
        enabled = self.ai_brain_var.get()
        self.settings["ai_brain_enabled"] = enabled
        self.save_settings()

        # Track AI brain toggle
        track("ai_brain_toggle", {"enabled": enabled})

        # Show/hide benefits and warning labels
        if enabled:
            self.ai_benefits_label.pack(anchor="w", padx=(24, 0), pady=(4, 0))
            self.ai_warn_label.pack(anchor="w", padx=(24, 0), pady=(2, 0))
        else:
            self.ai_benefits_label.pack_forget()
            self.ai_warn_label.pack_forget()

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

        # Track recording start
        track("recording_start")

        def record():
            try:
                mic = self.mic_combo.get()
                dev = self.mic_devices.get(mic) or sd.default.device[0]

                # Auto-stop settings
                silence_threshold = 200  # Raw level below this = silence
                silence_timeout = 20  # Seconds of silence before auto-stop
                max_duration = 300  # Max recording time in seconds

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

                        # Update timer display
                        self.after(0, lambda e=elapsed: self.record_btn.update_timer(e))

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

                # Track error
                if ANALYTICS_AVAILABLE and hasattr(self, 'analytics') and self.analytics:
                    self.analytics.track_error("transcription_error", str(e))

        threading.Thread(target=process, daemon=True).start()

    def handle_result(self, text):
        ai_used = False
        # Process with AI Brain if enabled (uses Groq LLaMA)
        if self.settings.get("ai_brain_enabled") and self.groq_client:
            self.record_btn.status.configure(text=self.t("ai_processing"), text_color=COLORS["metallic"])
            improved = self.process_with_ai_brain(text)
            if improved and improved != text:
                text = improved
                ai_used = True
                print(f"[DEBUG] AI Brain improved text")

        # Track successful recording
        if ANALYTICS_AVAILABLE and self.analytics:
            self.analytics.track_recording(
                duration_seconds=self.record_btn.current_time,
                text_length=len(text),
                ai_brain_used=ai_used
            )

        # Add to history
        self.add_to_history(text)
        self.history_label.configure(text=self._get_last_history())

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
        # Stop background animation
        if hasattr(self, 'bg_canvas'):
            self.bg_canvas.stop()
        self.floating_widget.destroy()
        self.destroy()


if __name__ == "__main__":
    print("=" * 50)
    print(f"VTT @SAINT4AI - Voice to Text v{APP_VERSION}")
    print("=" * 50)
    app = VoiceToTextApp()
    app.mainloop()
