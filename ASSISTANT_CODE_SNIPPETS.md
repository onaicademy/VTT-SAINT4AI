# Кодовые сниппеты для ассистента

Готовые компоненты для устранения разницы Windows vs macOS.

---

## 1. ПОНОВ HOTKEY ГОТОВО (✅)

### Файл: `macos_keyboard.py`

При передаче `allow_modifiers=True`:

```python
# Command+Shift+Space триггерит запись
listener = KeyboardListener(
    target_keycode=49,  # Space
    callback=self.toggle_recording,
    allow_modifiers=True  # Ожидаем модификатор
)
```

---

## 2. ДИНАМИЧЕСКОЕ ИЗМЕНЕНИЕ HOTKEY

### Файл: `voice_to_text_mac.py`

#### Шаг 1: Вставить в __init__

```python
self.kb_listener = None  # для CGEventTap listener
```

#### Шаг 2: Метод для остановки

```python
def stop_hotkey_listener(self):
    """Stop CGEventTap listener."""
    if hasattr(self, 'kb_listener') and self.kb_listener:
        try:
            self.kb_listener.stop()
            self.kb_listener = None
        except Exception as e:
            print(f"[WARNING] Failed to stop listener: {e}")
```

#### Шаг 3: Обновленный setup_hotkey()

```python
def setup_hotkey(self):
    """Глобальные горячие клавиши используя CGEventTap.
    
    Поддерживает динамическое изменение hotkey из UI.
    """
    try:
        from macos_keyboard import KeyboardListener
    except ImportError:
        print("❌ [HOTKEY] macos_keyboard module not found")
        self._setup_hotkey_fallback()
        return
    
    # Останови старый
    self.stop_hotkey_listener()
    
    # Получи hotkey строку из настроек (e.g. "49" или "space")
    hotkey_str = self.settings.get("hotkey", "49").lower().strip()
    
    try:
        # Пытаясь получить keycode
        if hotkey_str.isdigit():
            target_keycode = int(hotkey_str)
        else:
            target_keycode = KeyboardListener.get_keycode(hotkey_str)
            if target_keycode is None:
                print(f"[WARNING] Unknown hotkey [{hotkey_str}], using Space (49)")
                target_keycode = 49
        
        # Коллбек
        def on_hotkey():
            try:
                self.toggle_recording()
            except Exception as e:
                print(f"[ERROR] Hotkey callback: {e}")
        
        # Крейт listener
        # allow_modifiers=True для Cmd+Shift+Space
        # allow_modifiers=False для просто Space
        self.kb_listener = KeyboardListener(
            target_keycode=target_keycode,
            callback=on_hotkey,
            allow_modifiers=True  # Ожидай модификатор (алт опция)
        )
        self.kb_listener.start()
        print(f"[HOTKEY] Listener started for keycode {target_keycode}")
        
        # Обнови UI
        if hasattr(self, 'record_btn'):
            self.record_btn.hint.configure(text=f"or {hotkey_str.upper()}")
    
    except Exception as e:
        print(f"[ERROR] Hotkey setup: {e}")
        self._setup_hotkey_fallback()
```

#### Шаг 4: Новый метод change_hotkey() для UI

```python
def change_hotkey(self):
    """Позволить пользователю выбрать клавишу."""
    self.hotkey_label.configure(
        text="Press key...",
        text_color=COLORS["warning"]
    )
    print("[HOTKEY] Waiting for key press (5 seconds)...")
    # В будущем: перехватить нажатие одной клавиши
    # TODO: Настроить кей капчер через CGEventTap
```

#### Шаг 5: Обнови on_close()

```python
def on_close(self):
    self.is_recording = False
    self.stop_hotkey_listener()  # НОВОЕ
    if self.hotkey_listener:  # Остарое
        try:
            self.hotkey_listener.stop()
        except:
            pass
    # ... rest
```

---

## 3. АВТОВСТАВКА (ГОТОВО)

### Файл: `voice_to_text_mac.py`

```python
def auto_paste_text(self, text):
    """Вставить текст в активное поле."""
    if not self.settings.get("auto_paste"):
        return
    
    def do_paste():
        try:
            # Срости пользователю пероключиться
            time.sleep(0.3)
            
            # Метод 1: pyautogui
            try:
                import pyautogui
                pyperclip.copy(text)
                pyautogui.hotkey('command', 'v')
                print("[INFO] Auto-paste via pyautogui")
            except Exception as e:
                print(f"[WARNING] pyautogui failed: {e}")
                # Метод 2: AppleScript fallback
                self._paste_via_applescript(text)
        except Exception as e:
            print(f"[ERROR] Auto-paste: {e}")
    
    threading.Thread(target=do_paste, daemon=True).start()

def _paste_via_applescript(self, text):
    """Вставить через AppleScript."""
    import subprocess
    try:
        pyperclip.copy(text)
        script = 'tell application "System Events" to keystroke "v" using command down'
        subprocess.run(['osascript', '-e', script], check=True)
    except Exception as e:
        print(f"[ERROR] AppleScript paste: {e}")
```

---

## 4. ЗВУКОВЫЕ ОПОВЕЩЕНИЯ

### Файл: `voice_to_text_mac.py`

```python
def play_sound(self, type_):
    """Воспроизвести звук."""
    if not self.settings["sounds"]:
        return
    
    import subprocess
    sounds = {
        "start": "/System/Library/Sounds/Glass.aiff",
        "stop": "/System/Library/Sounds/Morse.aiff",
        "success": "/System/Library/Sounds/Ping.aiff"
    }
    
    sound_file = sounds.get(type_)
    if not sound_file:
        return
    
    def play():
        try:
            subprocess.run(['afplay', sound_file], check=True)
        except Exception as e:
            print(f"[WARNING] Failed to play sound: {e}")
    
    threading.Thread(target=play, daemon=True).start()
```

Оставься: афплея уже работает

---

## 5. ИСТОРИЯ ЗАПИСЕЙ

### Файл: `voice_to_text_mac.py`

Код ало есть в `voice_to_text_app_production.py` - скопировать:

- `load_history()`
- `save_history()`
- `add_to_history(text)`
- `HistoryWindow` класс (для UI)

Короткий основной код:

```python
def load_history(self):
    try:
        if os.path.exists("history.json"):
            with open("history.json", 'r', encoding='utf-8') as f:
                self.history = json.load(f)
    except:
        self.history = []

def add_to_history(self, text):
    self.history.insert(0, {
        "text": text,
        "timestamp": datetime.now().isoformat()
    })
    self.save_history()
```

---

## 6. AI BRAIN (LLaMA)

### Файл: `voice_to_text_mac.py`

Код ало есть - скопировать точно из Windows версии:

- `process_with_ai_brain(text)`
- `apply_terms_dict(text)`
- `load_terms_dict()`

```python
def process_with_ai_brain(self, text):
    """Улучшить текст через LLaMA."""
    if not self.settings.get("ai_brain_enabled") or not self.groq_client:
        return text
    
    try:
        prompt = f"""Исправь текст:
- Грамматика
- Пунктуация
- Верни ТОЛЬКО текст

{text}"""
        
        response = self.groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return text
```

---

## 7. ТЕСТ МИКРОФОНА

### Файл: `voice_to_text_mac.py`

Код уже видео в Windows версии - скопировать `test_mic()` метод

---

## 8. ПЛАВАЮЩИЙ ВИДЖЕТ

### Файл: `voice_to_text_mac.py`

`FloatingWidget` класс в жі уже реализован - полное речение!

---

## 9. МУЛЬТИЯЗЫЧНОСТЬ (RU/KK)

### Файл: `voice_to_text_mac.py`

Добавить казахские переводы в TEXTS dict:

```python
TEXTS = {
    "ru": {
        "subtitle": "by @SAINT4AI",
        "api_key": "API КЛЮЧ GROQ",
        # ... остальные
    },
    "kk": {
        "subtitle": "@SAINT4AI жасаған",
        "api_key": "GROQ API КІЛТІ",
        # ... казахские переводы
    }
}

def toggle_language(self):
    current = self.settings.get("ui_lang", "ru")
    self.settings["ui_lang"] = "kk" if current == "ru" else "ru"
    self.save_settings()
    # Rebuild UI
    for w in self.winfo_children():
        w.destroy()
    self.create_ui()
```

---

## 10. АВТОЗАПУСК НА macOS

### Файл: `voice_to_text_mac.py`

```python
def set_autostart(self, enable):
    """Настроить автозапуск через LaunchAgents."""
    try:
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.saint4ai.vtt.plist")
        
        if enable:
            exe_path = self.get_exe_path()
            plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.saint4ai.vtt</string>
    <key>ProgramArguments</key>
    <array>
        <string>open</string>
        <string>-a</string>
        <string>{exe_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>'''
            os.makedirs(os.path.dirname(plist_path), exist_ok=True)
            with open(plist_path, 'w') as f:
                f.write(plist)
            print(f"[INFO] Autostart enabled")
        else:
            if os.path.exists(plist_path):
                os.remove(plist_path)
                print(f"[INFO] Autostart disabled")
    except Exception as e:
        print(f"[ERROR] Autostart: {e}")

def check_autostart(self):
    plist_path = os.path.expanduser("~/Library/LaunchAgents/com.saint4ai.vtt.plist")
    return os.path.exists(plist_path)
```

---

## ОРГАНИЗАЦИЯ КОДА

### Когда вставляють этот код:

```
VoiceToTextApp.__init__():
    - self.kb_listener = None
    - self.history = []
    - self.groq_client = None

VoiceToTextApp._finish_loading():
    - self.load_history()  # НОВОЕ
    - self.load_terms_dict()  # НОВОЕ

VoiceToTextApp.create_ui():
    - добавить toggle_language() кнопку
    - добавить history раздел
    - добавить AI Brain раздел
    - добавить autostart чекбокс

VoiceToTextApp.handle_result():
    - self.add_to_history(text)  # НОВОЕ
    - self.process_with_ai_brain()  # НОВОЕ
    - self.auto_paste_text()  # ОБНОВЛЕННОЕ
    - self.play_sound("success")  # НОВОЕ

VoiceToTextApp.on_close():
    - self.stop_hotkey_listener()  # НОВОЕ
```

---

## ТЕСТИРОВАНИЕ

```bash
# Повторные права
# System Settings > Privacy & Security > Accessibility - Terminal
# System Settings > Privacy & Security > Input Monitoring - Terminal

# По на Cmd+Shift+Space должна запустить запись
# По на Space и Shift+Space - НЕ должна (ПОТОму что allow_modifiers=True)
```

---

## ОТ АССИСТЕНТУ: Оставься убедиться

1. НЕ использовать `keyboard.add_hotkey()` - вы увидите `ModuleNotFoundError` на macOS
2. НЕ делать `import Quartz` в `voice_to_text_mac.py` глобально - это в `macos_keyboard.py`
3. Усе аптекэ довольно быть thread-safe
4. Напишите тэсты для `auto_paste_text()` - это сложный тюн
