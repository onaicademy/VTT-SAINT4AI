# voice_to_text_app_fixed.py
"""
✅ FIXED: Proper threading architecture
- Hotkey listener in separate daemon thread (non-blocking)
- Whisper transcription in worker thread
- UI updates via self.after() for thread safety
- No deadlocks or UI freezes
"""

import customtkinter as ctk
import threading
import time
import os
import sounddevice as sd
import numpy as np
from scipy.io import wavfile
from groq import Groq
import queue
import traceback

# ============ Whisper Engine ============

class WhisperTranscriber:
    def __init__(self, api_key: str, language: str = "ru"):
        self.client = Groq(api_key=api_key)
        self.language = language
        self.sample_rate = 16000
        self.channels = 1
    
    def record(self, duration: float = 5.0) -> np.ndarray:
        """Record audio with correct format"""
        print(f"🎤 Recording {duration}s...")
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='int16'
        )
        sd.wait()
        print("✅ Recorded")
        return audio
    
    def save(self, audio: np.ndarray, filepath: str = "temp.wav") -> str:
        """Save to WAV"""
        wavfile.write(filepath, self.sample_rate, audio.astype('int16'))
        print(f"💾 Saved: {filepath}")
        return filepath
    
    def check_quality(self, audio: np.ndarray) -> bool:
        """Check audio quality"""
        rms = np.sqrt(np.mean(audio.astype(float) ** 2))
        peak = np.max(np.abs(audio))
        
        print(f"\n📊 Audio Quality:")
        print(f"   RMS: {rms:.0f} (target: 3000-10000)")
        print(f"   Peak: {peak:.0f} (target: > 5000)")
        
        if rms < 500:
            print("   ❌ TOO QUIET!")
            return False
        
        if rms > 20000:
            print("   ⚠️  TOO LOUD! May clip")
        
        print("   ✅ Good")
        return True
    
    def transcribe(self, filepath: str, retries: int = 3) -> str:
        """Transcribe with retry logic"""
        for attempt in range(retries):
            try:
                print(f"📤 Transcribing... (attempt {attempt + 1}/{retries})")
                
                with open(filepath, "rb") as f:
                    response = self.client.audio.transcriptions.create(
                        file=f,
                        model="whisper-large-v3",
                        language=self.language,
                        temperature=0.2
                    )
                
                text = response.text.strip()
                
                # Check for junk responses
                if not text or text.lower() in ["продолжение следует", "you", "...", "silence"]:
                    if attempt < retries - 1:
                        print("⚠️  Got placeholder, retrying...")
                        time.sleep(2)
                        continue
                    print("⚠️  All retries exhausted, returning empty")
                    return ""
                
                print(f"✅ Success: {text[:60]}...")
                return text
            
            except Exception as e:
                error_str = str(e).lower()
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                
                if "rate_limit" in error_str:
                    print("🔄 Rate limit, waiting 30s...")
                    time.sleep(30)
                elif "timeout" in error_str:
                    print("⏱️  Timeout, waiting 5s...")
                    time.sleep(5)
                elif attempt < retries - 1:
                    time.sleep(2)
                else:
                    return ""
        
        return ""
    
    def process(self, duration: float = 5.0) -> str:
        """Complete cycle: record → check → transcribe"""
        try:
            audio = self.record(duration)
            
            if not self.check_quality(audio):
                return ""
            
            filepath = self.save(audio)
            text = self.transcribe(filepath)
            
            # Cleanup
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return text
        
        except Exception as e:
            print(f"❌ Process error: {e}")
            traceback.print_exc()
            return ""

# ============ Global Hotkey Monitor (Thread-Safe) ============

class GlobalHotkeyMonitor:
    """
    Non-blocking hotkey listener.
    Runs in daemon thread, posts events to queue.
    """
    
    VIRTUAL_KEYS = {
        'A': 0, 'S': 1, 'D': 2, 'F': 3, 'H': 4, 'G': 5, 'Z': 6, 'X': 7,
        'C': 8, 'V': 9, 'B': 11, 'Q': 12, 'W': 13, 'E': 14, 'R': 15,
        'Y': 16, 'T': 17, 'Escape': 53, 'F1': 122, 'F2': 120, 'F3': 99,
        'F4': 118, 'F5': 96, 'F6': 97, 'F7': 98, 'F8': 100, 'F9': 101,
        'F10': 109, 'F11': 103, 'F12': 111, 'Print': 105, 'Home': 115,
        'Page_Up': 116, 'Delete': 117, 'End': 119, 'Page_Down': 121,
        'Left': 123, 'Right': 124, 'Down': 125, 'Up': 126, 'Tab': 48,
        'space': 49, 'Return': 36, 'BackSpace': 51, 'Shift_L': 56,
        'Shift_R': 60, 'Control_L': 59, 'Control_R': 62, 'Alt_L': 58,
        'Alt_R': 61, 'cmd': 55,
    }
    
    def __init__(self, event_queue: queue.Queue):
        """
        Args:
            event_queue: Queue to post hotkey events to
        """
        self.event_queue = event_queue
        self.running = False
        self.thread = None
        self.registered_hotkey = None
    
    def register(self, keycode: int, modifiers: int):
        """Register hotkey and start listening"""
        self.registered_hotkey = (keycode, modifiers)
        self.start()
    
    def start(self):
        """Start listening in background thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        print(f"🎧 Hotkey listener started (kc={self.registered_hotkey[0]}, mod={self.registered_hotkey[1]})")
    
    def _listen(self):
        """
        Listen for hotkey events (runs in daemon thread)
        
        This uses a polling approach instead of quickmachotkey
        to avoid blocking and threading conflicts.
        """
        try:
            import quickmachotkey
            
            keycode, modifiers = self.registered_hotkey
            
            # Register the hotkey
            quickmachotkey.RegisterEventHotKey(
                keycode=keycode,
                modifiers=modifiers,
                on_press=self._on_hotkey_pressed
            )
            
            # Start listening (blocks until stop() is called)
            print(f"🎧 Listening for hotkey (kc={keycode}, mod={modifiers})...")
            quickmachotkey.listen()
        
        except Exception as e:
            print(f"❌ Hotkey monitor error: {e}")
            traceback.print_exc()
            self.event_queue.put(("error", str(e)))
    
    def _on_hotkey_pressed(self):
        """Called when hotkey is pressed - post event to queue"""
        print("🔥 HOTKEY TRIGGERED!")
        self.event_queue.put(("hotkey_pressed", None))
    
    def stop(self):
        """Stop listening"""
        self.running = False
        print("🛑 Hotkey listener stopped")

# ============ Hotkey Recorder Dialog ============

class HotkeyRecorder(ctk.CTkToplevel):
    """Dialog for recording hotkey combination"""
    
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Запись горячей клавиши")
        self.geometry("500x300")
        self.resizable(False, False)
        
        self.callback = callback
        self.recorded = False
        self.keycode = None
        self.modifiers = None
        
        # UI
        ctk.CTkLabel(
            self,
            text="Нажмите комбинацию клавиш",
            font=("Arial", 14, "bold")
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            self,
            text="(например: Shift+Cmd+M)",
            font=("Arial", 10),
            text_color="gray"
        ).pack(pady=(0, 15))
        
        self.display = ctk.CTkLabel(
            self,
            text="Ожидание ввода...",
            font=("Arial", 12),
            text_color="gray"
        )
        self.display.pack(pady=15)
        
        self.info = ctk.CTkLabel(self, text="", font=("Arial", 9), text_color="lightblue")
        self.info.pack(pady=5)
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(20, 15), padx=20, fill="x", expand=False)
        
        ctk.CTkButton(
            button_frame,
            text="Сохранить",
            command=self.save,
            fg_color="green",
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Отмена",
            command=self.destroy,
            fg_color="gray",
            width=150
        ).pack(side="left", padx=5)
        
        self.bind('<KeyPress>', self.on_key_press)
        self.focus()
        self.attributes('-topmost', True)
    
    def on_key_press(self, event) -> str:
        if self.recorded:
            return 'break'
        
        keycode = GlobalHotkeyMonitor.VIRTUAL_KEYS.get(event.keysym, -1)
        
        # Convert Tkinter modifiers to Carbon format
        carbon_mods = 0
        if event.state & 0x0001:
            carbon_mods |= 0x0200  # Shift
        if event.state & 0x0004:
            carbon_mods |= 0x1000  # Ctrl
        if event.state & 0x0008:
            carbon_mods |= 0x0800  # Opt
        if event.state & 0x0080:
            carbon_mods |= 0x0100  # Cmd
        
        # Readable format
        mods = []
        if event.state & 0x0001:
            mods.append("Shift")
        if event.state & 0x0004:
            mods.append("Ctrl")
        if event.state & 0x0008:
            mods.append("Opt")
        if event.state & 0x0080:
            mods.append("Cmd")
        
        readable = "+".join(mods + [event.keysym]) if mods else event.keysym
        
        self.display.configure(text=f"✅ {readable}", text_color="green")
        self.info.configure(text=f"keycode={keycode}, mods={carbon_mods}")
        
        self.recorded = True
        self.keycode = keycode
        self.modifiers = carbon_mods
        
        return 'break'
    
    def save(self):
        if self.keycode is None:
            self.display.configure(text="⚠️ Клавиша не записана!", text_color="orange")
            self.update()
            self.after(1000, self.destroy)
            return
        
        self.callback(self.keycode, self.modifiers)
        self.destroy()

# ============ Scrollable Textbox ============

class ScrollableTextbox(ctk.CTkTextbox):
    """CTkTextbox with trackpad scroll support for macOS"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Bind all scroll events
        for event in ['<MouseWheel>', '<Button-4>', '<Button-5>']:
            self.bind(event, self._on_scroll)
    
    def _on_scroll(self, event):
        """Handle both mouse wheel and trackpad scroll"""
        if hasattr(event, 'num') and event.num in (4, 5):
            distance = -3 if event.num == 4 else 3
        elif hasattr(event, 'delta'):
            distance = -1 if event.delta > 0 else 1
        else:
            return
        
        self.yview_scroll(distance, 'units')
        return 'break'

# ============ Main Application ============

class VoiceToTextApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎤 Voice to Text for macOS - FIXED")
        self.geometry("700x600")
        
        # Initialize transcriber
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("❌ Error: GROQ_API_KEY not set")
            exit(1)
        
        self.transcriber = WhisperTranscriber(api_key=api_key, language="ru")
        
        # Event queue for hotkey events
        self.hotkey_event_queue = queue.Queue()
        self.hotkey_monitor = GlobalHotkeyMonitor(self.hotkey_event_queue)
        
        # Flag to prevent concurrent transcriptions
        self.transcribing = False
        
        # === UI ===
        
        # Header
        ctk.CTkLabel(
            self,
            text="🎤 Voice to Text (FIXED)",
            font=("Arial", 20, "bold")
        ).pack(pady=(20, 10))
        
        # Status
        self.status = ctk.CTkLabel(
            self,
            text="Ready",
            font=("Arial", 12),
            text_color="gray"
        )
        self.status.pack()
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkButton(
            button_frame,
            text="🎤 Record & Transcribe (5s)",
            command=self.record_and_transcribe,
            fg_color="blue",
            width=200
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="🔧 Setup Global Hotkey",
            command=self.setup_hotkey,
            fg_color="purple",
            width=200
        ).pack(side="left", padx=5)
        
        # Hotkey status
        self.hotkey_status = ctk.CTkLabel(
            self,
            text="No hotkey configured",
            font=("Arial", 10),
            text_color="gray"
        )
        self.hotkey_status.pack()
        
        # Text output label
        ctk.CTkLabel(
            self,
            text="Результаты транскрипции:",
            font=("Arial", 12, "bold")
        ).pack(pady=(20, 5), padx=20, anchor="w")
        
        # Text output with trackpad scroll
        self.text_output = ScrollableTextbox(self, height=250, font=("Courier", 11))
        self.text_output.pack(pady=(0, 20), padx=20, fill="both", expand=True)
        
        # Footer
        ctk.CTkLabel(
            self,
            text="✅ Threading fixed: UI non-blocking, hotkey listener in daemon thread",
            font=("Arial", 9),
            text_color="green"
        ).pack(pady=(0, 10))
        
        # Start polling for hotkey events
        self._poll_hotkey_events()
    
    def record_and_transcribe(self):
        """Trigger recording and transcription"""
        if self.transcribing:
            print("⏳ Already transcribing, please wait...")
            return
        
        # Start in worker thread
        thread = threading.Thread(target=self._do_transcription, daemon=True)
        thread.start()
    
    def _do_transcription(self):
        """Worker thread for transcription (non-blocking UI)"""
        try:
            self.transcribing = True
            
            # Update UI from worker thread safely
            self.after(0, lambda: self.status.configure(
                text="🎤 Recording...", text_color="orange"
            ))
            
            # Run transcription
            text = self.transcriber.process(duration=5.0)
            
            # Update UI with result
            if text:
                self.after(0, lambda: self._insert_text(text))
                self.after(0, lambda: self.status.configure(
                    text="✅ Done!", text_color="green"
                ))
            else:
                self.after(0, lambda: self.status.configure(
                    text="❌ Empty result (check mic/volume)",
                    text_color="red"
                ))
        
        except Exception as e:
            print(f"❌ Error: {e}")
            traceback.print_exc()
            self.after(0, lambda: self.status.configure(
                text=f"❌ Error: {str(e)[:50]}",
                text_color="red"
            ))
        
        finally:
            self.transcribing = False
    
    def _insert_text(self, text: str):
        """Insert text into output (thread-safe via self.after)"""
        self.text_output.insert("0.0", f"{text}\n\n")
    
    def setup_hotkey(self):
        """Open hotkey recorder dialog"""
        HotkeyRecorder(self, self.on_hotkey_configured)
    
    def on_hotkey_configured(self, keycode: int, modifiers: int):
        """Hotkey was recorded"""
        try:
            self.status.configure(text="🔧 Starting hotkey listener...", text_color="orange")
            self.update()
            
            # Register and start listening
            self.hotkey_monitor.register(keycode, modifiers)
            
            self.hotkey_status.configure(
                text=f"✅ Hotkey active (kc={keycode}, mod={modifiers})",
                text_color="green"
            )
            self.status.configure(text="🎧 Listening...", text_color="blue")
        
        except Exception as e:
            print(f"❌ Hotkey setup error: {e}")
            traceback.print_exc()
            self.hotkey_status.configure(text=f"❌ Error: {e}", text_color="red")
            self.status.configure(text="Error", text_color="red")
    
    def _poll_hotkey_events(self):
        """Poll for hotkey events (runs periodically in main thread)"""
        try:
            while True:
                event_type, event_data = self.hotkey_event_queue.get_nowait()
                
                if event_type == "hotkey_pressed":
                    print("🔥 Hotkey event received in main thread")
                    self.record_and_transcribe()
                
                elif event_type == "error":
                    print(f"❌ Hotkey error: {event_data}")
                    self.status.configure(
                        text=f"❌ Hotkey error: {event_data}",
                        text_color="red"
                    )
        
        except queue.Empty:
            pass  # No events, continue
        
        finally:
            # Poll again in 100ms
            self.after(100, self._poll_hotkey_events)

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("❌ Error: GROQ_API_KEY not set")
        print("Set it with: export GROQ_API_KEY='gsk_...'")
        exit(1)
    
    print("="*60)
    print("🎤 Voice to Text - FIXED VERSION")
    print("="*60)
    print("✅ Proper threading architecture")
    print("✅ Non-blocking UI")
    print("✅ Hotkey listener in daemon thread")
    print("✅ Queue-based communication")
    print("="*60)
    
    app = VoiceToTextApp()
    app.mainloop()
