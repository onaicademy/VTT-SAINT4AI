"""
Voice-to-Text Pro - Production Windows Application
Голосовой ввод текста через Groq Whisper API
"""
import os
import sys
import json
import time
import threading
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

# Default settings
DEFAULT_SETTINGS = {
    "api_key": "",
    "hotkey": "F9",
    "microphone": "",
    "language": "ru",
    "auto_paste": True,
    "show_notifications": True,
    "theme": "dark"
}


class VoiceToTextApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("500x650")
        self.minsize(450, 600)

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # State
        self.is_recording = False
        self.audio_data = []
        self.recording_thread = None
        self.level_thread = None
        self.groq_client = None
        self.current_hotkey = None
        self.waiting_for_hotkey = False
        self.mic_stream = None

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
        """Load settings from file."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    # Merge with defaults
                    settings = DEFAULT_SETTINGS.copy()
                    settings.update(saved)
                    return settings
        except Exception:
            pass
        return DEFAULT_SETTINGS.copy()

    def save_settings(self):
        """Save settings to file."""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def create_ui(self):
        """Create the main UI."""
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Title
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 15))

        title_label = ctk.CTkLabel(
            title_frame,
            text="🎙️ VTT @SAINT4AI",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack()

        subtitle = ctk.CTkLabel(
            title_frame,
            text="Voice-to-Text • AI Транскрибация",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle.pack()

        # === API Key Section ===
        self.create_section_label("🔑 API Ключ Groq")

        api_frame = ctk.CTkFrame(self.main_frame)
        api_frame.pack(fill="x", pady=(0, 15))

        self.api_entry = ctk.CTkEntry(
            api_frame,
            placeholder_text="Введите ваш Groq API ключ...",
            show="•",
            height=40
        )
        self.api_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        if self.settings["api_key"]:
            self.api_entry.insert(0, self.settings["api_key"])

        self.api_btn = ctk.CTkButton(
            api_frame,
            text="💾",
            width=40,
            height=40,
            command=self.save_api_key
        )
        self.api_btn.pack(side="right", padx=(0, 10), pady=10)

        self.api_status = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.api_status.pack(anchor="w", padx=10)

        # === Microphone Section ===
        self.create_section_label("🎤 Микрофон")

        mic_frame = ctk.CTkFrame(self.main_frame)
        mic_frame.pack(fill="x", pady=(0, 10))

        self.mic_combo = ctk.CTkComboBox(
            mic_frame,
            values=["Загрузка..."],
            height=35,
            command=self.on_mic_change
        )
        self.mic_combo.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)

        refresh_btn = ctk.CTkButton(
            mic_frame,
            text="🔄",
            width=40,
            height=35,
            command=self.refresh_microphones
        )
        refresh_btn.pack(side="right", padx=(0, 10), pady=10)

        # Voice level meter
        level_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        level_frame.pack(fill="x", padx=10, pady=(0, 15))

        ctk.CTkLabel(level_frame, text="Уровень:", font=ctk.CTkFont(size=11)).pack(side="left")

        self.level_bar = ctk.CTkProgressBar(level_frame, height=15)
        self.level_bar.pack(side="left", fill="x", expand=True, padx=(10, 10))
        self.level_bar.set(0)

        self.test_mic_btn = ctk.CTkButton(
            level_frame,
            text="Тест",
            width=60,
            height=28,
            command=self.toggle_mic_test
        )
        self.test_mic_btn.pack(side="right")
        self.mic_testing = False

        # === Hotkey Section ===
        self.create_section_label("⌨️ Горячая клавиша")

        hotkey_frame = ctk.CTkFrame(self.main_frame)
        hotkey_frame.pack(fill="x", pady=(0, 15))

        self.hotkey_display = ctk.CTkEntry(
            hotkey_frame,
            height=40,
            justify="center",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.hotkey_display.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        self.hotkey_display.insert(0, self.settings["hotkey"])
        self.hotkey_display.configure(state="disabled")

        self.set_hotkey_btn = ctk.CTkButton(
            hotkey_frame,
            text="Изменить",
            width=80,
            height=40,
            command=self.start_hotkey_capture
        )
        self.set_hotkey_btn.pack(side="right", padx=(0, 10), pady=10)

        hotkey_hint = ctk.CTkLabel(
            self.main_frame,
            text="💡 Нажмите 'Изменить' и затем нужную клавишу или комбинацию",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        hotkey_hint.pack(anchor="w", padx=10)

        # === Options Section ===
        self.create_section_label("⚙️ Настройки")

        options_frame = ctk.CTkFrame(self.main_frame)
        options_frame.pack(fill="x", pady=(0, 15))

        self.auto_paste_var = ctk.BooleanVar(value=self.settings["auto_paste"])
        auto_paste_check = ctk.CTkCheckBox(
            options_frame,
            text="Автоматически вставлять текст (Ctrl+V)",
            variable=self.auto_paste_var,
            command=self.on_settings_change
        )
        auto_paste_check.pack(anchor="w", padx=15, pady=(10, 5))

        self.notify_var = ctk.BooleanVar(value=self.settings["show_notifications"])
        notify_check = ctk.CTkCheckBox(
            options_frame,
            text="Звуковые уведомления",
            variable=self.notify_var,
            command=self.on_settings_change
        )
        notify_check.pack(anchor="w", padx=15, pady=(5, 10))

        # === Record Button ===
        self.record_btn = ctk.CTkButton(
            self.main_frame,
            text="🎤 Начать запись",
            height=60,
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self.toggle_recording,
            fg_color="#2d5a27",
            hover_color="#3d7a37"
        )
        self.record_btn.pack(fill="x", pady=15, padx=10)

        # Status
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="Готов к работе",
            font=ctk.CTkFont(size=13)
        )
        self.status_label.pack(pady=(0, 10))

        # === Help Section ===
        self.create_section_label("📖 Как пользоваться")

        help_frame = ctk.CTkFrame(self.main_frame)
        help_frame.pack(fill="x", pady=(0, 10))

        help_text = """
1️⃣  Введите API ключ Groq (получить: console.groq.com)
2️⃣  Выберите микрофон и проверьте его кнопкой "Тест"
3️⃣  Настройте горячую клавишу (по умолчанию F9)
4️⃣  Нажмите горячую клавишу → говорите → нажмите снова
5️⃣  Текст автоматически вставится в активное поле!
        """

        help_label = ctk.CTkLabel(
            help_frame,
            text=help_text.strip(),
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        help_label.pack(padx=15, pady=10, anchor="w")

    def create_section_label(self, text):
        """Create a section label."""
        label = ctk.CTkLabel(
            self.main_frame,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        label.pack(fill="x", padx=5, pady=(10, 5))

    def refresh_microphones(self):
        """Refresh list of available microphones."""
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
                # Select saved or first
                if self.settings["microphone"] in mics:
                    self.mic_combo.set(self.settings["microphone"])
                else:
                    self.mic_combo.set(mics[0])
                    self.settings["microphone"] = mics[0]
            else:
                self.mic_combo.configure(values=["Микрофоны не найдены"])
                self.mic_combo.set("Микрофоны не найдены")
        except Exception as e:
            self.mic_combo.configure(values=[f"Ошибка: {e}"])

    def on_mic_change(self, choice):
        """Handle microphone selection change."""
        self.settings["microphone"] = choice
        self.save_settings()

    def toggle_mic_test(self):
        """Toggle microphone test mode."""
        if not self.mic_testing:
            self.mic_testing = True
            self.test_mic_btn.configure(text="Стоп", fg_color="#8B0000")
            self.start_level_monitor()
        else:
            self.mic_testing = False
            self.test_mic_btn.configure(text="Тест", fg_color=("#3B8ED0", "#1F6AA5"))
            self.stop_level_monitor()

    def start_level_monitor(self):
        """Start monitoring microphone level."""
        def monitor():
            try:
                mic_name = self.mic_combo.get()
                device_id = self.mic_devices.get(mic_name)

                def audio_callback(indata, frames, time_info, status):
                    if self.mic_testing:
                        level = np.abs(indata).mean()
                        # Normalize to 0-1 range
                        normalized = min(1.0, level / 0.1)
                        self.after(0, lambda: self.level_bar.set(normalized))

                self.mic_stream = sd.InputStream(
                    device=device_id,
                    channels=1,
                    samplerate=16000,
                    callback=audio_callback
                )
                self.mic_stream.start()

                while self.mic_testing:
                    time.sleep(0.05)

                self.mic_stream.stop()
                self.mic_stream.close()
                self.after(0, lambda: self.level_bar.set(0))

            except Exception as e:
                self.after(0, lambda: self.set_status(f"Ошибка микрофона: {e}"))
                self.mic_testing = False

        self.level_thread = threading.Thread(target=monitor, daemon=True)
        self.level_thread.start()

    def stop_level_monitor(self):
        """Stop monitoring microphone level."""
        self.mic_testing = False
        if self.mic_stream:
            try:
                self.mic_stream.stop()
                self.mic_stream.close()
            except:
                pass
        self.level_bar.set(0)

    def save_api_key(self):
        """Save API key and test connection."""
        api_key = self.api_entry.get().strip()
        if not api_key:
            self.api_status.configure(text="❌ Введите API ключ", text_color="red")
            return

        self.settings["api_key"] = api_key
        self.save_settings()

        # Test connection
        try:
            self.groq_client = Groq(api_key=api_key)
            self.api_status.configure(text="✅ API ключ сохранён и проверен", text_color="green")
        except Exception as e:
            self.api_status.configure(text=f"⚠️ Сохранено, но ошибка: {e}", text_color="orange")

    def check_api_key(self):
        """Check if API key is configured."""
        if self.settings["api_key"]:
            try:
                self.groq_client = Groq(api_key=self.settings["api_key"])
                self.api_status.configure(text="✅ API подключен", text_color="green")
            except Exception as e:
                self.api_status.configure(text=f"❌ Ошибка API: {e}", text_color="red")
        else:
            self.api_status.configure(text="⚠️ Введите API ключ", text_color="orange")

    def start_hotkey_capture(self):
        """Start capturing new hotkey."""
        self.waiting_for_hotkey = True
        self.set_hotkey_btn.configure(text="Жду...", fg_color="#8B4513")
        self.hotkey_display.configure(state="normal")
        self.hotkey_display.delete(0, "end")
        self.hotkey_display.insert(0, "Нажмите клавишу...")
        self.hotkey_display.configure(state="disabled")

        # Remove old hotkey temporarily
        if self.current_hotkey:
            try:
                keyboard.remove_hotkey(self.current_hotkey)
            except:
                pass

        def capture():
            event = keyboard.read_event(suppress=True)
            if event.event_type == keyboard.KEY_DOWN:
                # Build hotkey string
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
                    if modifiers:
                        hotkey = '+'.join(modifiers + [key])
                    else:
                        hotkey = key

                    self.after(0, lambda: self.set_new_hotkey(hotkey))

        threading.Thread(target=capture, daemon=True).start()

    def set_new_hotkey(self, hotkey):
        """Set the new hotkey."""
        self.waiting_for_hotkey = False
        self.settings["hotkey"] = hotkey
        self.save_settings()

        self.hotkey_display.configure(state="normal")
        self.hotkey_display.delete(0, "end")
        self.hotkey_display.insert(0, hotkey.upper())
        self.hotkey_display.configure(state="disabled")

        self.set_hotkey_btn.configure(text="Изменить", fg_color=("#3B8ED0", "#1F6AA5"))

        self.setup_hotkey()
        self.set_status(f"Горячая клавиша: {hotkey.upper()}")

    def setup_hotkey(self):
        """Setup the global hotkey."""
        if self.current_hotkey:
            try:
                keyboard.remove_hotkey(self.current_hotkey)
            except:
                pass

        try:
            self.current_hotkey = keyboard.add_hotkey(
                self.settings["hotkey"],
                self.toggle_recording,
                suppress=True
            )
        except Exception as e:
            self.set_status(f"Ошибка горячей клавиши: {e}")

    def on_settings_change(self):
        """Handle settings checkbox changes."""
        self.settings["auto_paste"] = self.auto_paste_var.get()
        self.settings["show_notifications"] = self.notify_var.get()
        self.save_settings()

    def toggle_recording(self):
        """Toggle recording state."""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start recording audio."""
        if not self.groq_client:
            self.set_status("❌ Сначала настройте API ключ!")
            return

        self.is_recording = True
        self.audio_data = []

        self.record_btn.configure(
            text="⏹️ Остановить запись",
            fg_color="#8B0000",
            hover_color="#A52A2A"
        )
        self.set_status("🎤 Запись... Говорите!")

        if self.settings["show_notifications"]:
            self.play_beep(800, 150)

        def record():
            try:
                mic_name = self.mic_combo.get()
                device_id = self.mic_devices.get(mic_name)

                def callback(indata, frames, time_info, status):
                    if self.is_recording:
                        self.audio_data.append(indata.copy())
                        # Update level bar
                        level = np.abs(indata).mean()
                        normalized = min(1.0, level / 0.1)
                        self.after(0, lambda: self.level_bar.set(normalized))

                with sd.InputStream(
                    device=device_id,
                    samplerate=16000,
                    channels=1,
                    dtype='int16',
                    callback=callback
                ):
                    while self.is_recording:
                        time.sleep(0.05)

                self.after(0, lambda: self.level_bar.set(0))

            except Exception as e:
                self.after(0, lambda: self.set_status(f"Ошибка записи: {e}"))
                self.is_recording = False

        self.recording_thread = threading.Thread(target=record, daemon=True)
        self.recording_thread.start()

    def stop_recording(self):
        """Stop recording and transcribe."""
        self.is_recording = False

        if self.settings["show_notifications"]:
            self.play_beep(400, 150)

        self.record_btn.configure(
            text="🎤 Начать запись",
            fg_color="#2d5a27",
            hover_color="#3d7a37"
        )

        if not self.audio_data:
            self.set_status("❌ Нет аудио данных")
            return

        self.set_status("⏳ Транскрибирую...")

        # Process in background
        def process():
            try:
                # Combine audio
                audio = np.concatenate(self.audio_data, axis=0)

                # Save temp file
                temp_file = "temp_recording.wav"
                write_wav(temp_file, 16000, audio)

                # Transcribe
                with open(temp_file, "rb") as f:
                    result = self.groq_client.audio.transcriptions.create(
                        file=(temp_file, f.read()),
                        model="whisper-large-v3",
                        language=self.settings["language"],
                        response_format="text",
                        prompt="Расставь пунктуацию правильно."
                    )

                # Clean up
                try:
                    os.remove(temp_file)
                except:
                    pass

                text = result.strip() if isinstance(result, str) else str(result).strip()

                if text:
                    self.after(0, lambda: self.handle_transcription(text))
                else:
                    self.after(0, lambda: self.set_status("❌ Пустой результат"))

            except Exception as e:
                self.after(0, lambda: self.set_status(f"❌ Ошибка: {e}"))

        threading.Thread(target=process, daemon=True).start()

    def handle_transcription(self, text):
        """Handle successful transcription."""
        # Copy to clipboard
        pyperclip.copy(text)

        # Show result
        display_text = text[:50] + "..." if len(text) > 50 else text
        self.set_status(f"✅ {display_text}")

        # Auto paste if enabled
        if self.settings["auto_paste"]:
            time.sleep(0.15)
            try:
                pyautogui.hotkey('ctrl', 'v')
            except:
                pass

        if self.settings["show_notifications"]:
            self.play_beep(600, 100)

    def set_status(self, text):
        """Update status label."""
        self.status_label.configure(text=text)

    def play_beep(self, freq, duration):
        """Play a beep sound."""
        try:
            threading.Thread(
                target=lambda: winsound.Beep(freq, duration),
                daemon=True
            ).start()
        except:
            pass

    def on_close(self):
        """Handle window close."""
        self.stop_level_monitor()
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
