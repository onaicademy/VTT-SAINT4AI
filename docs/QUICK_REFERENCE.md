# QuickMacHotKey - Быстрая реализация (30 минут)

⚠️ **TL;DR**: Это гайд для тех, кто хочет сразу стартовать

---

## Шаг 1: Установка (2 минуты)

```bash
pip install quickmachotkey pyobjc-framework-Cocoa
```

---

## Шаг 2: Хандлер Hotkey (скопируй это в твой проект) (5 минут)

**созди `app/hotkeys.py`:**

```python
import quickmachotkey
import threading
from typing import Callable, Optional

class MacHotkeys:
    """Глобальные hotkeys для macOS"""
    
    def __init__(self, on_f9: Callable):
        self.on_f9 = on_f9
        self.listening = False
    
    def start(self):
        """Запусти hotkey listener в отдельном потоке"""
        if self.listening:
            return
        
        self.listening = True
        listener_thread = threading.Thread(
            target=self._listen,
            daemon=True,
            name="HotkeysListener"
        )
        listener_thread.start()
    
    def stop(self):
        """Останови listener"""
        self.listening = False
    
    def _listen(self):
        """Внутренний listener loop"""
        try:
            # F9 = keycode 101
            quickmachotkey.register_hotkey(
                keycode=101,
                on_press=self._handle_f9
            )
            quickmachotkey.listen()
        except Exception as e:
            print(f"❌ Hotkey listener error: {e}")
            self.listening = False
    
    def _handle_f9(self):
        """Обработчик F9"""
        try:
            self.on_f9()
        except Exception as e:
            print(f"❌ Error in F9 handler: {e}")
```

---

## Шаг 3: Интеграция в ваш майн апп (5 минут)

**замени старые hotkeys на новые:**

```python
# было
from pynput import keyboard

def on_hotkey():
    toggle_recording()

listener = keyboard.GlobalHotKeys({'<F9>': on_hotkey})
listener.start()

# стало
from app.hotkeys import MacHotkeys

hotkeys = MacHotkeys(on_f9=toggle_recording)
hotkeys.start()
```

---

## Шаг 4: Обнови requirements.txt (2 минуты)

**добавь:**
```
quickmachotkey>=1.0.2
pyobjc-framework-Cocoa>=10.1
```

**удали:**
```
pynput  # ручно его выбери и делетни из всюду
```

---

## Шаг 5: Тестирование (3 минуты)

**созди `test_hotkeys_local.py`:**

```python
#!/usr/bin/env python3
import quickmachotkey
import time

print("🔠 Registering F9 hotkey...")

def on_f9_pressed():
    print("✅ F9 PRESSED!")

quickmachotkey.register_hotkey(
    keycode=101,  # F9
    on_press=on_f9_pressed
)

print("\n🔛 Listening... Press F9 multiple times (Ctrl+C to exit)\n")

try:
    quickmachotkey.listen()
except KeyboardInterrupt:
    print("\n✋ Test completed!")
```

**запусти:**
```bash
python test_hotkeys_local.py
# Нажми F9 несколько раз
# Ндолжны видеть "✅ F9 PRESSED!"
# Нажми Ctrl+C чтобы выйти
```

---

## Шаг 6: PyInstaller спец (5 минут)

**останови старые процессы:**
```bash
killall VTT VTT.exe 2>/dev/null; true
```

**созди `build_macos.py`:**

```python
#!/usr/bin/env python3
import PyInstaller.__main__
import sys
import os
from pathlib import Path

project_dir = Path(__file__).parent

PyInstaller.__main__.run([
    'main.py',
    '--name=VTT',
    '--windowed',
    '--onefile',
    f'--icon={project_dir}/assets/icon.icns',
    '--target-arch=arm64',  # Apple Silicon
    '--add-data=app:app',
    '--add-data=config:config',
    '--hidden-import=quickmachotkey',
    '--hidden-import=Cocoa',
    '--hidden-import=objc',
    '--osx-bundle-identifier=com.onai.vtt',
])

print("\n✅ Build complete! App at: dist/VTT.app")
```

**запусти:**
```bash
python build_macos.py
```

---

## Шаг 7: Тестирование в .app (3 минуты)

```bash
# Где поживает апп
./dist/VTT.app/Contents/MacOS/VTT

# Нажми F9 и проверь что нет краша
```

---

## Шаг 8: Системные разрешения (2 минуты) - импортантно

⚠️ **Без этого работать не будет!**

1. Открой: **System Preferences → Security & Privacy → Accessibility**
2. Нажми Ключом для редактирования
3. Нажми `+`
4. Навигируй к `dist/VTT.app`
5. Открой

**или скриптом:**
```bash
open /System/Library/PreferencePanes/Security.prefpane
```

---

## Шаг 9: Code Signing (2 минуты)

```bash
codesign -s - dist/VTT.app --deep
```

---

## Шаг 10: Понытие (1 минута)

Тото! Повторно работайте локально, а не правильно. Нажмите F9 и целебность!

---

## Нюансы кода

### 1. Коды клавиш

```python
# Другие клавиши если F9 конфликтует
# https://eastmanreference.com/complete-list-of-applescript-key-codes

F1 = 122
F2 = 120
F3 = 99
F4 = 118
F5 = 96
F6 = 97
F7 = 98
F8 = 100
F9 = 101
F10 = 109
F11 = 103
F12 = 111
```

### 2. Модификаторы

```python
from Cocoa import NSEventModifierFlags

SHIFT = NSEventModifierFlags.NSEventModifierFlagShift
CONTROL = NSEventModifierFlags.NSEventModifierFlagControl
OPTION = NSEventModifierFlags.NSEventModifierFlagOption
COMMAND = NSEventModifierFlags.NSEventModifierFlagCommand

# Пример: COMMAND+OPTION+K
quickmachotkey.register_hotkey(
    keycode=40,  # K
    modifiers=COMMAND | OPTION,
    on_press=on_hotkey
)
```

### 3. Одновременные hotkeys

```python
class DualStateHotkey:
    def __init__(self):
        self.recording = False
    
    def toggle(self):
        self.recording = not self.recording
        if self.recording:
            print("🔴 Recording...")
        else:
            print("⏹️ Recording stopped")

hotkey = DualStateHotkey()
hotkeys = MacHotkeys(on_f9=hotkey.toggle)
hotkeys.start()
```

---

## Начальник 100% частые дотрагования

### Данные при запуске: "Permission denied"

**Решение:**
```bash
# Дай на права в Accessibility (выше)
open /System/Library/PreferencePanes/Security.prefpane
```

### Ничего не случается когда я нажимаю F9

**Проверка:**
```python
# С тестовым скриптом выше (тест_hotkeys_local.py)
quickmachotkey.register_hotkey(101, lambda: print("✅ GOT IT!"))
```

### Апп крашится в начале и выходит

**Проблема:** quickmachotkey требует Cocoa, которые не установлены

**Ответ:**
```bash
pip install pyobjc-framework-Cocoa
```

### Апп при зарыстовке не равботает

**Проблема:** PyInstaller не выйти все зависимости

**Проверъте:**
```bash
# Думка hidden imports
pyinstaller --collect-all=quickmachotkey main.py

# Отдадбир в spec
'--hidden-import=quickmachotkey',
'--hidden-import=Cocoa',
'--hidden-import=objc',
```

---

## Взровняние драма

Если НЕ работает, вот что открыть:

1. **Console logs**:
   ```bash
   log show --level debug --predicate 'process == "VTT"' --last 10m
   ```

2. **Дебаггер**:
   ```bash
   lldb ./dist/VTT.app/Contents/MacOS/VTT
   (lldb) run
   # Нажми F9
   ```

3. **Повторные запуски**:
   ```bash
   killall VTT
   ./dist/VTT.app/Contents/MacOS/VTT
   ```

---

## Чек-лист установки

- [ ] Установил `quickmachotkey` и `pyobjc-framework-Cocoa`
- [ ] Тестировал с test_hotkeys_local.py
- [ ] Скотіуровал жою pynput из майна
- [ ] Обновил requirements.txt
- [ ] Составил новый spec для PyInstaller
- [ ] Собрал апп
- [ ] Дал разрешение в Accessibility
- [ ] Подписал app
- [ ] Потестировал на F9 аез краша ✅

---

## Отправка в release

```bash
# Собери в dist/
zipn dist/VTT.app VTT-macos.zip

# Она GitHub Releases
# Открыть новые Release
# Мозжет хзд та VTT-macos.zip
```

---

## Ресурсы

- [QuickMacHotKey Documentation](https://pypi.org/project/quickmachotkey/)
- [Key codes reference](https://eastmanreference.com/complete-list-of-applescript-key-codes)
- [macOS Security & Privacy](https://support.apple.com/en-us/guide/mac-help/allowapp-mchlp1434/mac)

---

🌟 **Отлично! Естественно готово на мачОС!**
