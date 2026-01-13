# macOS Hotkey Crash Fix - Полное руководство

## Проблема

**EXC_BREAKPOINT (SIGTRAP)** крах при нажатии F9 на macOS 15.x (Sequoia) с Apple Silicon.

### Корневая причина

pynput вызывает `TSMGetInputSourceProperty` из фонового потока, но macOS требует этого только из главного потока. Результат: мгновенный крах приложения.

```
Thread 0 Crashed:: Dispatch queue: com.apple.main-thread
0   com.apple.HIToolbox            0x7fff2b5c4594 TSMGetInputSourceProperty + 56
1   pynput._util.darwin.PyObjCKeyboardListener  0x104c8a3a4 func + 120
```

---

## Решение: QuickMacHotKey (рекомендуется)

### Почему это работает

- Использует те же стабильные API, что и профессиональные macOS приложения
- Полностью избегает threading проблем
- Работает идеально с PyInstaller
- Минимальные изменения кода

### Установка

```bash
# 1. Установи зависимости
pip install quickmachotkey pyobjc-framework-Cocoa

# 2. Обнови requirements.txt
quickmachotkey>=1.0.2
pyobjc-framework-Cocoa>=10.1
```

### Замена кода

#### Было (pynput):
```python
from pynput import keyboard

def on_hotkey():
    print("F9 pressed!")

listener = keyboard.GlobalHotKeys({
    '<F9>': on_hotkey
})
listener.start()
```

#### Стало (QuickMacHotKey):
```python
import quickmachotkey

def on_hotkey():
    print("F9 pressed!")

# Регистрируем F9 (код 101 для F9)
quickmachotkey.register_hotkey(
    keycode=101,
    on_press=on_hotkey
)
quickmachotkey.listen()
```

### Полная интеграция в VTT

```python
import quickmachotkey
import threading
from app.recorder import AudioRecorder

class VTTHotkeys:
    def __init__(self, recorder: AudioRecorder):
        self.recorder = recorder
        self.recording = False
    
    def toggle_recording(self):
        """F9 - Toggle recording"""
        if not self.recording:
            self.recorder.start()
            self.recording = True
            print("🔴 Recording started...")
        else:
            self.recorder.stop()
            self.recording = False
            print("⏹️ Recording stopped...")
    
    def start_listening(self):
        """Запуск в отдельном потоке"""
        hotkey_thread = threading.Thread(
            target=self._listen,
            daemon=True
        )
        hotkey_thread.start()
    
    def _listen(self):
        """Слушаем глобальные hotkeys"""
        try:
            # F9 = keycode 101
            quickmachotkey.register_hotkey(
                keycode=101,
                on_press=self.toggle_recording
            )
            quickmachotkey.listen()
        except Exception as e:
            print(f"❌ Hotkey listener error: {e}")

# Использование:
# recorder = AudioRecorder()
# hotkeys = VTTHotkeys(recorder)
# hotkeys.start_listening()
```

### Коды клавиш macOS

```python
# Основные клавиши для переопределения
F9 = 101
F10 = 109
F11 = 103
F12 = 111

# Модификаторы
SHIFT = 0x00020100
CONTROL = 0x00040100
OPTION = 0x00080100
COMMAND = 0x00100100

# Комбинация: COMMAND + OPTION + K
quickmachotkey.register_hotkey(
    keycode=40,  # K
    modifiers=COMMAND | OPTION,
    on_press=on_hotkey
)
```

### PyInstaller конфигурация

```spec
# vtt.spec
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        # Для QuickMacHotKey
        (
            '/opt/homebrew/lib/libquickmachotkey.dylib',
            '.'
        ),
    ],
    datas=[
        ('app', 'app'),
        ('config', 'config'),
    ],
    hiddenimports=[
        'quickmachotkey',
        'Cocoa',
        'objc',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VTT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',  # Для Apple Silicon
    codesign_identity='ad-hoc',  # Signing
)

app = BUNDLE(
    exe,
    name='VTT.app',
    icon='assets/icon.icns',
    bundle_identifier='com.onai.vtt',
    info_plist={
        'NSMicrophoneUsageDescription': 'VTT needs microphone access',
        'NSLocalNetworkUsageDescription': 'VTT needs local network access',
    },
)
```

### Команды сборки

```bash
# 1. Создай spec файл
pyinstaller --onefile --windowed --name VTT --icon assets/icon.icns main.py

# 2. Модифицируй vtt.spec (см. выше)

# 3. Собери
pyinstaller vtt.spec

# 4. Подпиши (опционально, но рекомендуется)
codesign -s - dist/VTT.app --deep

# 5. Тестируй
./dist/VTT.app/Contents/MacOS/VTT
```

---

## Альтернативные решения

### 1. NSEvent Global Monitor (Native Cocoa)

Если QuickMacHotKey недостаточно стабилен, используй напрямую Cocoa:

```python
from Cocoa import NSEvent, NSEventMaskKeyDown, NSApplication
import threading

class CocoaHotkeys:
    def __init__(self, recorder):
        self.recorder = recorder
        self.recording = False
    
    def monitor_keyboard(self):
        """Использует NSEvent напрямую"""
        def _listen():
            app = NSApplication.sharedApplication()
            
            def hotkey_handler(event):
                if event.keyCode() == 101:  # F9
                    self.toggle_recording()
                return event
            
            # Устанавливаем глобальный монитор
            NSEvent.addGlobalMonitorForEventsMatchingMask_handler(
                NSEventMaskKeyDown,
                hotkey_handler
            )
            
            # Запускаем event loop
            app.run()
        
        thread = threading.Thread(target=_listen, daemon=True)
        thread.start()
    
    def toggle_recording(self):
        if not self.recording:
            self.recorder.start()
            self.recording = True
        else:
            self.recorder.stop()
            self.recording = False
```

### 2. CGEventTap (Low-level)

Для максимального контроля (но сложнее в настройке):

```python
from Quartz import CGEventTapCreate, CGEventTapEnable, CFRunLoopGetCurrent
from Quartz import kCGEventTapOptionDefault, kCGHeadInsertEventTap
from Quartz import CGEventMaskBit, kCGKeyDown, CFMachPortSetInvalidationCallBack

def event_tap_callback(proxy, type_, event, refcon):
    """Обработчик всех событий клавиатуры"""
    keyCode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
    
    if keyCode == 101:  # F9
        refcon['callback']()
        # Возвращаем None чтобы предотвратить распространение события
        return None
    
    return event

def setup_event_tap(callback):
    """Создает глобальный CGEventTap"""
    refcon = {'callback': callback}
    
    tap = CGEventTapCreate(
        kCGHIDEventTap,
        kCGHeadInsertEventTap,
        kCGEventTapOptionDefault,
        CGEventMaskBit(kCGKeyDown),
        event_tap_callback,
        refcon
    )
    
    if not tap:
        print("❌ Failed to create event tap")
        return
    
    source = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)
    CFRunLoopAddSource(CFRunLoopGetCurrent(), source, kCFRunLoopCommonModes)
    CGEventTapEnable(tap, True)
    
    return tap
```

---

## Проверка и тестирование

### 1. Локальный тест

```python
# test_hotkeys.py
import quickmachotkey
import time

def on_f9():
    print("✅ F9 pressed!")

print("Registering F9 hotkey...")
quickmachotkey.register_hotkey(
    keycode=101,
    on_press=on_f9
)

print("Listening for F9... (Press F9 to test)")
try:
    quickmachotkey.listen()
except KeyboardInterrupt:
    print("\nTest completed!")
```

Запуск:
```bash
python test_hotkeys.py
# Нажми F9 несколько раз
```

### 2. Интеграционный тест

```python
# test_integration.py
from app.vtt_hotkeys import VTTHotkeys
from app.recorder import AudioRecorder
import time

recorder = AudioRecorder()
hotkeys = VTTHotkeys(recorder)
hotkeys.start_listening()

print("VTT hotkey system started!")
print("Press F9 to toggle recording (press Ctrl+C to exit)")

try:
    time.sleep(60)  # Слушаем 60 секунд
except KeyboardInterrupt:
    print("\nTest completed!")
```

### 3. Проверка в Xcode

Если все еще падает:

```bash
# Запусти с отладкой
lldb ./dist/VTT.app/Contents/MacOS/VTT

# В lldb консоли:
(lldb) run
# Нажми F9
# lldb покажет exactную строку краша
```

---

## Известные проблемы и решения

### Проблема 1: "Permission denied" при запуске

**Причина:** macOS требует разрешение на захват клавиатуры

**Решение:**
```bash
# Дай разрешение в System Preferences → Security & Privacy → Accessibility
# Добавь VTT.app в список

# Или программно:
codesign --force --deep --sign - dist/VTT.app
```

### Проблема 2: Hotkey работает только в первый раз

**Причина:** Event loop не перезапускается

**Решение:**
```python
# Добавь обработку исключений
def _listen(self):
    while True:
        try:
            quickmachotkey.register_hotkey(101, self.toggle_recording)
            quickmachotkey.listen()
        except Exception as e:
            print(f"Hotkey error: {e}")
            time.sleep(1)  # Retry after 1 second
```

### Проблема 3: F9 перехватывает браузер/приложение

**Причина:** F9 - системная клавиша в некоторых приложениях

**Решение:** Используй другую комбинацию:
```python
# Вместо F9, используй COMMAND+OPTION+K
quickmachotkey.register_hotkey(
    keycode=40,  # K
    modifiers=quickmachotkey.MOD_CMD | quickmachotkey.MOD_OPT,
    on_press=self.toggle_recording
)
```

---

## Финальная чек-лист

- [ ] Установил `quickmachotkey` и `pyobjc-framework-Cocoa`
- [ ] Заменил pynput на QuickMacHotKey в коде
- [ ] Обновил `requirements.txt`
- [ ] Протестировал локально: `python test_hotkeys.py`
- [ ] Создал новый `vtt.spec` с правильной конфигурацией
- [ ] Собрал с PyInstaller: `pyinstaller vtt.spec`
- [ ] Дал разрешение в System Preferences → Accessibility
- [ ] Подписал app: `codesign -s - dist/VTT.app --deep`
- [ ] Протестировал в .app: `./dist/VTT.app/Contents/MacOS/VTT`
- [ ] Нажал F9 и проверил что работает без краша ✅

---

## Поддержка и дальнейшие вопросы

Если что-то не работает:

1. Проверь версию macOS: `sw_vers`
2. Проверь архитектуру: `uname -m` (должно быть `arm64`)
3. Смотри логи: `log show --level debug`
4. Используй lldb для отладки

Успехи! 🚀
