import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WHISPER_MODEL = "whisper-large-v3"
LANGUAGE = "ru"
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
HOTKEY = "F9"
TEMP_AUDIO_FILE = "temp_recording.wav"
TRANSCRIPTION_PROMPT = "Расставь пунктуацию правильно."
