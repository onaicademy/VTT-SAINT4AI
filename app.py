"""
Voice-to-Text: F9 для записи -> Groq Whisper -> автовставка
"""
import os
import sys
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
import config

is_recording = False
audio_data = []
recording_thread = None
client = None


def beep(freq=800, dur=150):
    try:
        winsound.Beep(freq, dur)
    except:
        pass


def start_recording():
    global is_recording, audio_data
    audio_data = []
    is_recording = True
    print("\n🎤 Запись... (F9 - стоп)")
    beep(800, 150)

    def callback(indata, frames, time_info, status):
        if is_recording:
            audio_data.append(indata.copy())

    with sd.InputStream(samplerate=config.SAMPLE_RATE, channels=config.CHANNELS,
                        dtype=config.DTYPE, callback=callback):
        while is_recording:
            time.sleep(0.1)


def stop_recording():
    global is_recording
    is_recording = False
    beep(400, 150)
    print("⏹️ Транскрибирую...")

    if not audio_data:
        return None

    audio = np.concatenate(audio_data, axis=0)
    write_wav(config.TEMP_AUDIO_FILE, config.SAMPLE_RATE, audio)
    return config.TEMP_AUDIO_FILE


def transcribe(audio_file):
    if not os.path.exists(audio_file):
        return ""
    try:
        with open(audio_file, "rb") as f:
            result = client.audio.transcriptions.create(
                file=(audio_file, f.read()),
                model=config.WHISPER_MODEL,
                language=config.LANGUAGE,
                response_format="text",
                prompt=config.TRANSCRIPTION_PROMPT
            )
        os.remove(audio_file)
        return result.strip() if isinstance(result, str) else str(result).strip()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return ""


def paste(text):
    if not text:
        return
    pyperclip.copy(text)
    print(f"📋 {text[:60]}..." if len(text) > 60 else f"📋 {text}")
    time.sleep(0.15)
    try:
        pyautogui.hotkey('ctrl', 'v')
        print("✅ Вставлено!")
    except:
        print("⚠️ Текст в буфере")


def on_f9():
    global is_recording, recording_thread
    if not is_recording:
        recording_thread = threading.Thread(target=start_recording, daemon=True)
        recording_thread.start()
    else:
        audio_file = stop_recording()
        if audio_file:
            if recording_thread:
                recording_thread.join(timeout=1)
            text = transcribe(audio_file)
            if text:
                paste(text)


def main():
    global client
    print("=" * 40)
    print("🎙️ Voice-to-Text (Groq Whisper)")
    print("=" * 40)

    if not config.GROQ_API_KEY:
        print("❌ GROQ_API_KEY не найден в .env!")
        sys.exit(1)

    client = Groq(api_key=config.GROQ_API_KEY)
    print("✅ Groq подключен")

    keyboard.add_hotkey(config.HOTKEY, on_f9, suppress=True)
    print(f"✅ Клавиша: {config.HOTKEY}")
    print("\n📌 F9 = старт/стоп записи")
    print("🔄 Ожидание... (Ctrl+C выход)\n")

    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("\n👋 Выход")


if __name__ == "__main__":
    main()
