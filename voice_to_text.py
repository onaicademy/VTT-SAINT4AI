"""
VTT @SAINT4AI - Voice-to-Text Pro
Premium voice input with Groq Whisper API
"""
import os
import sys
import json
import time
import threading
import math
import winsound
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as write_wav
import keyboard
import pyperclip
import pyautogui
from groq import Groq
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import io
import base64

# App info
APP_NAME = "VTT @SAINT4AI"
APP_VERSION = "1.0.0"
CONFIG_FILE = "settings.json"

# Colors
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_card": "#16213e",
    "accent": "#0f3460",
    "primary": "#e94560",
    "primary_hover": "#ff6b6b",
    "success": "#00d26a",
    "warning": "#ffc107",
    "text": "#ffffff",
    "text_dim": "#8892b0",
    "recording": "#ff4757",
    "recording_glow": "#ff6b81"
}

DEFAULT_SETTINGS = {
    "api_key": "",
    "hotkey": "F9",
    "microphone": "",
    "language": "ru",
    "auto_paste": True,
    "copy_to_clipboard": True,
    "sound_notifications": True,
    "theme": "dark"
}


class Tooltip:
    """Premium tooltip with animation."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = ctk.CTkToplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        self.tooltip.attributes("-topmost", True)

        frame = ctk.CTkFrame(self.tooltip, fg_color=COLORS["bg_card"], corner_radius=8)
        frame.pack(padx=2, pady=2)

        label = ctk.CTkLabel(
            frame,
            text=self.text,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"],
            wraplength=250,
            justify="left"
        )
        label.pack(padx=10, pady=8)

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class HelpButton(ctk.CTkButton):
    """Small help button with tooltip."""
    def __init__(self, master, tooltip_text, **kwargs):
        super().__init__(
            master,
            text="?",
            width=24,
            height=24,
            corner_radius=12,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["primary"],
            **kwargs
        )
        Tooltip(self, tooltip_text)


class AnimatedRecordButton(ctk.CTkFrame):
    """Premium animated recording button with pulsing effect."""
    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.command = command
        self.is_recording = False
        self.animation_running = False
        self.pulse_phase = 0
        self.wave_data = []

        # Main container
        self.canvas_size = 180
        self.canvas = ctk.CTkCanvas(
            self,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=COLORS["bg_dark"],
            highlightthickness=0
        )
        self.canvas.pack(pady=10)

        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="Nажмите для записи",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_dim"]
        )
        self.status_label.pack(pady=(5, 0))

        # Hotkey hint
        self.hotkey_label = ctk.CTkLabel(
            self,
            text="или используйте горячую клавишу",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"]
        )
        self.hotkey_label.pack()

        self.canvas.bind("<Button-1>", self.on_click)
        self.draw_idle_state()

    def draw_idle_state(self):
        """Draw the idle microphone button."""
        self.canvas.delete("all")
        cx, cy = self.canvas_size // 2, self.canvas_size // 2

        # Outer glow ring
        for i in range(3):
            alpha = 0.1 - i * 0.03
            size = 70 + i * 10
            self.canvas.create_oval(
                cx - size, cy - size, cx + size, cy + size,
                fill="", outline=COLORS["primary"], width=2
            )

        # Main circle
        self.canvas.create_oval(
            cx - 50, cy - 50, cx + 50, cy + 50,
            fill=COLORS["primary"], outline=""
        )

        # Microphone icon (simplified)
        self.canvas.create_oval(cx - 12, cy - 25, cx + 12, cy + 5, fill="white", outline="")
        self.canvas.create_arc(cx - 20, cy - 15, cx + 20, cy + 20, start=0, extent=-180,
                               fill="", outline="white", width=3, style="arc")
        self.canvas.create_line(cx, cy + 20, cx, cy + 35, fill="white", width=3)
        self.canvas.create_line(cx - 15, cy + 35, cx + 15, cy + 35, fill="white", width=3)

    def draw_recording_state(self):
        """Draw animated recording state with sound waves."""
        self.canvas.delete("all")
        cx, cy = self.canvas_size // 2, self.canvas_size // 2

        # Animated pulse rings
        for i in range(4):
            phase = (self.pulse_phase + i * 0.5) % 2
            size = 50 + phase * 40
            alpha = max(0, 1 - phase / 2)
            color = self._interpolate_color(COLORS["recording"], COLORS["bg_dark"], 1 - alpha)
            self.canvas.create_oval(
                cx - size, cy - size, cx + size, cy + size,
                fill="", outline=color, width=2
            )

        # Sound wave visualization
        if self.wave_data:
            wave_count = 12
            for i in range(wave_count):
                angle = (i / wave_count) * 2 * math.pi
                base_len = 55
                wave_len = base_len + (self.wave_data[i % len(self.wave_data)] * 25 if self.wave_data else 0)

                x1 = cx + math.cos(angle) * 45
                y1 = cy + math.sin(angle) * 45
                x2 = cx + math.cos(angle) * wave_len
                y2 = cy + math.sin(angle) * wave_len

                self.canvas.create_line(x1, y1, x2, y2, fill=COLORS["recording_glow"], width=3)

        # Main recording circle
        self.canvas.create_oval(
            cx - 40, cy - 40, cx + 40, cy + 40,
            fill=COLORS["recording"], outline=""
        )

        # Stop icon (square)
        self.canvas.create_rectangle(
            cx - 12, cy - 12, cx + 12, cy + 12,
            fill="white", outline=""
        )

    def _interpolate_color(self, color1, color2, t):
        """Interpolate between two hex colors."""
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def start_animation(self):
        """Start recording animation."""
        self.is_recording = True
        self.animation_running = True
        self.status_label.configure(text="Запись... Говорите!", text_color=COLORS["recording"])
        self.hotkey_label.configure(text="нажмите снова для остановки")
        self._animate()

    def stop_animation(self):
        """Stop recording animation."""
        self.is_recording = False
        self.animation_running = False
        self.status_label.configure(text="Обработка...", text_color=COLORS["warning"])
        self.draw_idle_state()

    def reset(self):
        """Reset to idle state."""
        self.status_label.configure(text="Нажмите для записи", text_color=COLORS["text_dim"])
        self.hotkey_label.configure(text="или используйте горячую клавишу")
        self.draw_idle_state()

    def set_success(self, text):
        """Show success state."""
        self.status_label.configure(text=text, text_color=COLORS["success"])

    def _animate(self):
        """Animation loop."""
        if not self.animation_running:
            return

        self.pulse_phase = (self.pulse_phase + 0.08) % 2
        self.draw_recording_state()
        self.after(30, self._animate)

    def update_wave(self, level):
        """Update wave visualization with audio level."""
        self.wave_data = [level * (0.5 + 0.5 * math.sin(i * 0.5 + self.pulse_phase * 3)) for i in range(12)]

    def on_click(self, event):
        """Handle button click."""
        if self.command:
            self.command()


class VoiceToTextApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title(f"{APP_NAME}")
        self.geometry("520x780")
        self.minsize(480, 700)
        self.configure(fg_color=COLORS["bg_dark"])

        # Set theme
        ctk.set_appearance_mode("dark")

        # State
        self.is_recording = False
        self.audio_data = []
        self.recording_thread = None
        self.groq_client = None
        self.current_hotkey = None
        self.waiting_for_hotkey = False
        self.mic_stream = None
        self.mic_testing = False

        # Load settings
        self.settings = self.load_settings()

        # Create UI
        self.create_ui()

        # Initialize
        self.refresh_microphones()
        self.setup_hotkey()
        self.check_api_key()

        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_settings(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    settings = DEFAULT_SETTINGS.copy()
                    settings.update(saved)
                    return settings
        except Exception:
            pass
        return DEFAULT_SETTINGS.copy()

    def save_settings(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def create_ui(self):
        """Create premium UI."""
        # Scrollable main frame
        self.main_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg_dark"],
            scrollbar_button_color=COLORS["accent"]
        )
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # === HEADER ===
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title = ctk.CTkLabel(
            header_frame,
            text="VTT @SAINT4AI",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text"]
        )
        title.pack()

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Голосовой ввод текста с AI",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"]
        )
        subtitle.pack()

        # === RECORD BUTTON ===
        self.record_button = AnimatedRecordButton(
            self.main_frame,
            command=self.toggle_recording
        )
        self.record_button.pack(pady=10)

        # === API KEY SECTION ===
        self.create_section("API Ключ Groq", "api")

        api_card = self.create_card()

        api_header = ctk.CTkFrame(api_card, fg_color="transparent")
        api_header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            api_header,
            text="Введите ваш API ключ:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"]
        ).pack(side="left")

        HelpButton(
            api_header,
            "API ключ нужен для работы с Groq Whisper.\n\n"
            "Как получить:\n"
            "1. Зайдите на console.groq.com\n"
            "2. Зарегистрируйтесь или войдите\n"
            "3. Перейдите в раздел API Keys\n"
            "4. Создайте новый ключ и скопируйте его"
        ).pack(side="right")

        api_input_frame = ctk.CTkFrame(api_card, fg_color="transparent")
        api_input_frame.pack(fill="x")

        self.api_entry = ctk.CTkEntry(
            api_input_frame,
            placeholder_text="gsk_xxxxxxxxxxxxxxxxxxxxx",
            show="*",
            height=45,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["accent"],
            border_color=COLORS["accent"]
        )
        self.api_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        if self.settings["api_key"]:
            self.api_entry.insert(0, self.settings["api_key"])

        self.api_btn = ctk.CTkButton(
            api_input_frame,
            text="Сохранить",
            width=100,
            height=45,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self.save_api_key
        )
        self.api_btn.pack(side="right")

        self.api_status = ctk.CTkLabel(
            api_card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"]
        )
        self.api_status.pack(anchor="w", pady=(10, 0))

        # === MICROPHONE SECTION ===
        self.create_section("Микрофон", "mic")

        mic_card = self.create_card()

        mic_header = ctk.CTkFrame(mic_card, fg_color="transparent")
        mic_header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            mic_header,
            text="Выберите устройство записи:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"]
        ).pack(side="left")

        HelpButton(
            mic_header,
            "Выберите микрофон, который будет использоваться для записи голоса.\n\n"
            "Нажмите 'Тест' чтобы проверить работу микрофона - "
            "полоска уровня должна двигаться когда вы говорите."
        ).pack(side="right")

        mic_select_frame = ctk.CTkFrame(mic_card, fg_color="transparent")
        mic_select_frame.pack(fill="x")

        self.mic_combo = ctk.CTkComboBox(
            mic_select_frame,
            values=["Загрузка..."],
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["accent"],
            border_color=COLORS["accent"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            command=self.on_mic_change
        )
        self.mic_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.test_btn = ctk.CTkButton(
            mic_select_frame,
            text="Тест",
            width=80,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["accent"],
            hover_color=COLORS["primary"],
            command=self.toggle_mic_test
        )
        self.test_btn.pack(side="right")

        # Level meter
        level_frame = ctk.CTkFrame(mic_card, fg_color="transparent")
        level_frame.pack(fill="x", pady=(15, 0))

        ctk.CTkLabel(
            level_frame,
            text="Уровень сигнала:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"]
        ).pack(side="left")

        self.level_bar = ctk.CTkProgressBar(
            level_frame,
            height=12,
            corner_radius=6,
            fg_color=COLORS["accent"],
            progress_color=COLORS["success"]
        )
        self.level_bar.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.level_bar.set(0)

        # === HOTKEY SECTION ===
        self.create_section("Горячая клавиша", "hotkey")

        hotkey_card = self.create_card()

        hotkey_header = ctk.CTkFrame(hotkey_card, fg_color="transparent")
        hotkey_header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            hotkey_header,
            text="Клавиша для активации записи:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"]
        ).pack(side="left")

        HelpButton(
            hotkey_header,
            "Эта клавиша включает и выключает запись голоса.\n\n"
            "Как изменить:\n"
            "1. Нажмите кнопку 'Изменить'\n"
            "2. Нажмите нужную клавишу или комбинацию\n"
            "   (например: F9, Ctrl+Shift+Space)\n"
            "3. Клавиша автоматически сохранится"
        ).pack(side="right")

        hotkey_frame = ctk.CTkFrame(hotkey_card, fg_color="transparent")
        hotkey_frame.pack(fill="x")

        self.hotkey_display = ctk.CTkEntry(
            hotkey_frame,
            height=45,
            justify="center",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLORS["accent"],
            border_color=COLORS["accent"],
            state="disabled"
        )
        self.hotkey_display.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.hotkey_display.configure(state="normal")
        self.hotkey_display.insert(0, self.settings["hotkey"].upper())
        self.hotkey_display.configure(state="disabled")

        self.hotkey_btn = ctk.CTkButton(
            hotkey_frame,
            text="Изменить",
            width=100,
            height=45,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["accent"],
            hover_color=COLORS["primary"],
            command=self.start_hotkey_capture
        )
        self.hotkey_btn.pack(side="right")

        # === SETTINGS SECTION ===
        self.create_section("Настройки", "settings")

        settings_card = self.create_card()

        # Auto-paste
        self.create_setting_row(
            settings_card,
            "Автоматическая вставка",
            "auto_paste",
            "После транскрибации текст автоматически\n"
            "вставляется в активное поле ввода (Ctrl+V).\n\n"
            "Полезно для быстрого ввода в чаты,\n"
            "документы и любые текстовые поля."
        )

        # Copy to clipboard
        self.create_setting_row(
            settings_card,
            "Копировать в буфер обмена",
            "copy_to_clipboard",
            "Текст копируется в буфер обмена.\n\n"
            "Вы сможете вставить его позже\n"
            "нажав Ctrl+V в любом приложении."
        )

        # Sound notifications
        self.create_setting_row(
            settings_card,
            "Звуковые уведомления",
            "sound_notifications",
            "Короткие звуковые сигналы:\n"
            "- Высокий тон = запись началась\n"
            "- Низкий тон = запись остановлена\n"
            "- Средний тон = текст готов"
        )

        # === HOW TO USE ===
        self.create_section("Как пользоваться", "help")

        help_card = self.create_card()

        steps = [
            ("1", "Введите API ключ Groq и нажмите 'Сохранить'"),
            ("2", "Выберите микрофон и проверьте его кнопкой 'Тест'"),
            ("3", "Кликните на большую кнопку или нажмите горячую клавишу"),
            ("4", "Говорите - ваш голос записывается"),
            ("5", "Нажмите снова - текст появится в активном поле!")
        ]

        for num, text in steps:
            step_frame = ctk.CTkFrame(help_card, fg_color="transparent")
            step_frame.pack(fill="x", pady=5)

            ctk.CTkLabel(
                step_frame,
                text=num,
                width=30,
                height=30,
                corner_radius=15,
                fg_color=COLORS["primary"],
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="white"
            ).pack(side="left", padx=(0, 12))

            ctk.CTkLabel(
                step_frame,
                text=text,
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text"],
                anchor="w"
            ).pack(side="left", fill="x")

    def create_section(self, title, icon):
        """Create section header."""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.pack(fill="x", pady=(20, 8))

        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text"]
        ).pack(side="left")

    def create_card(self):
        """Create a card container."""
        card = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=12
        )
        card.pack(fill="x", pady=(0, 5))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=18)

        return inner

    def create_setting_row(self, parent, label, setting_key, tooltip_text):
        """Create a setting row with checkbox and help."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=8)

        var = ctk.BooleanVar(value=self.settings.get(setting_key, True))
        setattr(self, f"{setting_key}_var", var)

        checkbox = ctk.CTkCheckBox(
            row,
            text=label,
            variable=var,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            border_color=COLORS["accent"],
            command=lambda: self.on_setting_change(setting_key, var.get())
        )
        checkbox.pack(side="left")

        HelpButton(row, tooltip_text).pack(side="right")

    def on_setting_change(self, key, value):
        """Handle setting change."""
        self.settings[key] = value
        self.save_settings()

    def refresh_microphones(self):
        try:
            devices = sd.query_devices()
            mics = []
            self.mic_devices = {}

            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    name = dev['name']
                    mics.append(name)
                    self.mic_devices[name] = i

            if mics:
                self.mic_combo.configure(values=mics)
                if self.settings["microphone"] in mics:
                    self.mic_combo.set(self.settings["microphone"])
                else:
                    self.mic_combo.set(mics[0])
                    self.settings["microphone"] = mics[0]
            else:
                self.mic_combo.configure(values=["Микрофоны не найдены"])
        except Exception as e:
            self.mic_combo.configure(values=[f"Ошибка: {e}"])

    def on_mic_change(self, choice):
        self.settings["microphone"] = choice
        self.save_settings()

    def toggle_mic_test(self):
        if not self.mic_testing:
            self.mic_testing = True
            self.test_btn.configure(text="Стоп", fg_color=COLORS["recording"])
            self.start_level_monitor()
        else:
            self.mic_testing = False
            self.test_btn.configure(text="Тест", fg_color=COLORS["accent"])
            self.level_bar.set(0)

    def start_level_monitor(self):
        def monitor():
            try:
                mic_name = self.mic_combo.get()
                device_id = self.mic_devices.get(mic_name)

                def callback(indata, frames, time_info, status):
                    if self.mic_testing:
                        level = np.abs(indata).mean()
                        normalized = min(1.0, level / 0.05)
                        self.after(0, lambda: self.level_bar.set(normalized))

                self.mic_stream = sd.InputStream(
                    device=device_id, channels=1, samplerate=16000, callback=callback
                )
                self.mic_stream.start()

                while self.mic_testing:
                    time.sleep(0.05)

                self.mic_stream.stop()
                self.mic_stream.close()
            except Exception as e:
                self.after(0, lambda: self.api_status.configure(text=f"Ошибка: {e}"))
                self.mic_testing = False

        threading.Thread(target=monitor, daemon=True).start()

    def save_api_key(self):
        api_key = self.api_entry.get().strip()
        if not api_key:
            self.api_status.configure(text="Введите API ключ", text_color=COLORS["warning"])
            return

        self.settings["api_key"] = api_key
        self.save_settings()

        try:
            self.groq_client = Groq(api_key=api_key)
            self.api_status.configure(text="API ключ сохранён и работает!", text_color=COLORS["success"])
        except Exception as e:
            self.api_status.configure(text=f"Ошибка: {e}", text_color=COLORS["recording"])

    def check_api_key(self):
        if self.settings["api_key"]:
            try:
                self.groq_client = Groq(api_key=self.settings["api_key"])
                self.api_status.configure(text="API подключён", text_color=COLORS["success"])
            except Exception as e:
                self.api_status.configure(text=f"Ошибка: {e}", text_color=COLORS["recording"])
        else:
            self.api_status.configure(text="Введите API ключ для начала работы", text_color=COLORS["warning"])

    def start_hotkey_capture(self):
        self.waiting_for_hotkey = True
        self.hotkey_btn.configure(text="Жду...", fg_color=COLORS["warning"])
        self.hotkey_display.configure(state="normal")
        self.hotkey_display.delete(0, "end")
        self.hotkey_display.insert(0, "Нажмите клавишу...")
        self.hotkey_display.configure(state="disabled")

        if self.current_hotkey:
            try:
                keyboard.remove_hotkey(self.current_hotkey)
            except:
                pass

        def capture():
            event = keyboard.read_event(suppress=True)
            if event.event_type == keyboard.KEY_DOWN:
                modifiers = []
                if keyboard.is_pressed('ctrl'):
                    modifiers.append('ctrl')
                if keyboard.is_pressed('shift'):
                    modifiers.append('shift')
                if keyboard.is_pressed('alt'):
                    modifiers.append('alt')

                key = event.name
                if key not in ['ctrl', 'shift', 'alt', 'left ctrl', 'right ctrl',
                               'left shift', 'right shift', 'left alt', 'right alt']:
                    hotkey = '+'.join(modifiers + [key]) if modifiers else key
                    self.after(0, lambda: self.set_new_hotkey(hotkey))

        threading.Thread(target=capture, daemon=True).start()

    def set_new_hotkey(self, hotkey):
        self.waiting_for_hotkey = False
        self.settings["hotkey"] = hotkey
        self.save_settings()

        self.hotkey_display.configure(state="normal")
        self.hotkey_display.delete(0, "end")
        self.hotkey_display.insert(0, hotkey.upper())
        self.hotkey_display.configure(state="disabled")

        self.hotkey_btn.configure(text="Изменить", fg_color=COLORS["accent"])
        self.setup_hotkey()

    def setup_hotkey(self):
        if self.current_hotkey:
            try:
                keyboard.remove_hotkey(self.current_hotkey)
            except:
                pass

        try:
            self.current_hotkey = keyboard.add_hotkey(
                self.settings["hotkey"], self.toggle_recording, suppress=True
            )
            self.record_button.hotkey_label.configure(
                text=f"или нажмите {self.settings['hotkey'].upper()}"
            )
        except Exception as e:
            print(f"Hotkey error: {e}")

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def play_start_sound(self):
        """Premium start sound - ascending chord."""
        def play():
            for freq in [523, 659, 784]:  # C5, E5, G5
                winsound.Beep(freq, 80)
                time.sleep(0.02)
        threading.Thread(target=play, daemon=True).start()

    def play_stop_sound(self):
        """Premium stop sound - descending chord."""
        def play():
            for freq in [784, 659, 523]:  # G5, E5, C5
                winsound.Beep(freq, 80)
                time.sleep(0.02)
        threading.Thread(target=play, daemon=True).start()

    def play_success_sound(self):
        """Premium success chime."""
        def play():
            winsound.Beep(880, 100)
            time.sleep(0.05)
            winsound.Beep(1109, 150)
        threading.Thread(target=play, daemon=True).start()

    def start_recording(self):
        print("[DEBUG] start_recording called")

        if not self.groq_client:
            print("[DEBUG] No groq_client!")
            self.record_button.status_label.configure(
                text="Сначала введите API ключ!", text_color=COLORS["warning"]
            )
            return

        self.is_recording = True
        self.audio_data = []
        self.record_button.start_animation()

        if self.settings.get("sound_notifications", True):
            self.play_start_sound()

        def record():
            try:
                mic_name = self.mic_combo.get()
                device_id = self.mic_devices.get(mic_name)

                print(f"[DEBUG] Recording with mic: {mic_name}, device_id: {device_id}")
                print(f"[DEBUG] Available devices: {self.mic_devices}")

                if device_id is None:
                    # Try default device
                    print("[DEBUG] device_id is None, using default")
                    device_id = sd.default.device[0]
                    print(f"[DEBUG] Default device: {device_id}")

                def callback(indata, frames, time_info, status):
                    if status:
                        print(f"[DEBUG] Audio status: {status}")
                    if self.is_recording:
                        self.audio_data.append(indata.copy())
                        level = np.abs(indata).mean()
                        normalized = min(1.0, level / 0.02)  # More sensitive
                        self.after(0, lambda l=normalized: self.level_bar.set(l))
                        self.after(0, lambda l=normalized: self.record_button.update_wave(l))

                print("[DEBUG] Opening InputStream...")
                with sd.InputStream(device=device_id, samplerate=16000, channels=1,
                                    dtype='int16', callback=callback):
                    print("[DEBUG] Recording started!")
                    while self.is_recording:
                        time.sleep(0.05)

                print(f"[DEBUG] Recording stopped, got {len(self.audio_data)} chunks")
                self.after(0, lambda: self.level_bar.set(0))
            except Exception as e:
                print(f"[ERROR] Recording error: {e}")
                import traceback
                traceback.print_exc()
                self.after(0, lambda: self.record_button.set_success(f"Ошибка: {e}"))
                self.is_recording = False

        self.recording_thread = threading.Thread(target=record, daemon=True)
        self.recording_thread.start()

    def stop_recording(self):
        print("[DEBUG] stop_recording called")
        self.is_recording = False
        self.record_button.stop_animation()

        if self.settings.get("sound_notifications", True):
            self.play_stop_sound()

        if not self.audio_data:
            print("[DEBUG] No audio data!")
            self.record_button.reset()
            return

        print(f"[DEBUG] Processing {len(self.audio_data)} audio chunks...")

        def process():
            try:
                audio = np.concatenate(self.audio_data, axis=0)
                print(f"[DEBUG] Audio shape: {audio.shape}, duration: {len(audio)/16000:.1f}s")

                temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_recording.wav")
                write_wav(temp_file, 16000, audio)
                print(f"[DEBUG] Saved to: {temp_file}")

                print("[DEBUG] Sending to Groq API...")
                with open(temp_file, "rb") as f:
                    result = self.groq_client.audio.transcriptions.create(
                        file=(temp_file, f.read()),
                        model="whisper-large-v3",
                        language=self.settings["language"],
                        response_format="text",
                        prompt="Расставь пунктуацию правильно."
                    )

                print(f"[DEBUG] API response: {result}")

                try:
                    os.remove(temp_file)
                except:
                    pass

                text = result.strip() if isinstance(result, str) else str(result).strip()

                if text:
                    print(f"[DEBUG] Got text: {text}")
                    self.after(0, lambda: self.handle_result(text))
                else:
                    print("[DEBUG] Empty result")
                    self.after(0, lambda: self.record_button.set_success("Пустой результат"))
                    self.after(2000, self.record_button.reset)
            except Exception as e:
                print(f"[ERROR] Processing error: {e}")
                import traceback
                traceback.print_exc()
                self.after(0, lambda: self.record_button.set_success(f"Ошибка: {e}"))
                self.after(3000, self.record_button.reset)

        threading.Thread(target=process, daemon=True).start()

    def handle_result(self, text):
        print(f"[DEBUG] handle_result: {text}")

        if self.settings.get("copy_to_clipboard", True):
            pyperclip.copy(text)
            print("[DEBUG] Copied to clipboard")

        display = text[:40] + "..." if len(text) > 40 else text
        self.record_button.set_success(f"Готово: {display}")

        if self.settings.get("auto_paste", True):
            time.sleep(0.15)
            try:
                pyautogui.hotkey('ctrl', 'v')
                print("[DEBUG] Auto-pasted")
            except Exception as e:
                print(f"[DEBUG] Auto-paste failed: {e}")

        if self.settings.get("sound_notifications", True):
            self.play_success_sound()

        self.after(3000, self.record_button.reset)

    def on_close(self):
        self.mic_testing = False
        self.is_recording = False
        if self.current_hotkey:
            try:
                keyboard.remove_hotkey(self.current_hotkey)
            except:
                pass
        self.destroy()


def main():
    app = VoiceToTextApp()
    app.mainloop()


if __name__ == "__main__":
    main()
