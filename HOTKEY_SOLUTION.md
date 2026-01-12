# Глобальные Hotkey на macOS 15+ Tahoe

## Проблема

Это решение направлено на исправление проблемы с перехватом глобальных горячих клавиш (КОП) без модификаторов на macOS 15 Tahoe с архитектурой M3.

### Осы кости

- **НСН Проблема**: `NSEvent.addGlobalMonitor...` работает только с модификаторами (Cmd+Space удачно, один Space - нет)
- **Почему**: Apple интенционально блокирует такие события для предотвращения кейлоггинга (кража паролей, записи передач)
- **Отказался**: CGEventTap (не обязательно рекомендуется использовать), Carbon регистрация горячих клавиш (deprecated)

## Решение: CGEventTap

### Почему CGEventTap работает

1. **Нижний уровень**: Он работает с сырым потоком событий ниже, чем NSEvent
2. **Не требует root**: Нужны только Accessibility и Input Monitoring права
3. **Обходит ограничения NSEvent**: Не блокирует одиночные клавиши
4. **Используется Whisper Flow/Super Whisper**: Проверенный выход

### Как использовать

```python
from macos_keyboard import KeyboardListener

def on_hotkey_pressed():
    print("🎧 Hotkey triggered!")
    # запусти запись аудио
    
keycodes = {
    'space': 49,
    'f1': 122,
    'f2': 120,
    'f3': 99,
    # ...
}

# Получи keycode для Space (49)
target_keycode = KeyboardListener.get_keycode('space')

# Создай и запусти слушатель в отдельном потоке
listener = KeyboardListener(
    target_keycode=target_keycode,
    callback=on_hotkey_pressed,
    allow_modifiers=False  # игнорируй Space + Cmd итд
)
listener.start()

# Латер, чтобы остановить
listener.stop()
```

## Коды клавиш macOS

### Функциональные
| Клавиша | Keycode |
|-----------|--------|
| F1 | 122 |
| F2 | 120 |
| F3 | 99 |
| F4 | 118 |
| F5 | 96 |
| F6 | 97 |
| F7 | 98 |
| F8 | 100 |
| F9 | 101 |
| F10 | 109 |
| F11 | 103 |
| F12 | 111 |
| F13 | 105 |
| F14 | 107 |
| F15 | 113 |

### Специальные
| Клавиша | Keycode |
|-----------|--------|
| Space | 49 |
| Return | 36 |
| Tab | 48 |
| CapsLock | 57 |
| Escape | 53 |
| Delete | 51 |

### Навигация
| Клавиша | Keycode |
|-----------|--------|
| Up | 126 |
| Down | 125 |
| Left | 123 |
| Right | 124 |

Найти все keycode: `KeyboardListener.KEYCODES`

## Права НА macOS 15

### 🔐 Критически важно!

**System Settings > Privacy & Security > Accessibility**
1. Нажми `+` для добавления приложения
2. Выбери Terminal или VTT.app (если ассемблированное)

**System Settings > Privacy & Security > Input Monitoring**
1. Если там уже Terminal - удали (кнопка `-`)
2. Повторно добавь Terminal

### Очень важно
- После чистки прав - **перезагружи** Terminal/VTT
- Если после добавления прав они не работают:
  - Перебуть Mac
  - Удали из списка и добавь заново

## Таблица диагностики

| Все работает? | Ожидаемый вывод |
|-----------|------------------|
| Нет прав | `❌ [HOTKEY] Ошибка: Не удалось создать EventTap...` |
| Есть права | `🎧 [HOTKEY] Keyboard Tap запущен...` |
| Провал | `[ERROR] PyObjC не установлен` |

## Настройка для VTT

```python
# в voice_to_text_mac.py, замени setup_hotkey():

from macos_keyboard import KeyboardListener

def setup_hotkey(self):
    """Setup global hotkey using CGEventTap (works without modifiers)."""
    print("⚠️ Setting up Global CGEventTap Hotkey...")
    
    # Прекрати старый слушатель pynput
    if self.hotkey_listener:
        try:
            self.hotkey_listener.stop()
        except:
            pass
        self.hotkey_listener = None
    
    # Получи код клавиши из настроек
    # Экспектируются данные либо в виде имени ('space', 'f1')
    # либо в виде keycode прямо
    hotkey_str = self.settings.get("hotkey", "space").lower()
    
    # Пытаясь получить keycode
    try:
        if hotkey_str.isdigit():
            target_keycode = int(hotkey_str)
        else:
            target_keycode = KeyboardListener.get_keycode(hotkey_str)
            if target_keycode is None:
                print(f"⚠️  [{hotkey_str}] - неизвестная клавиша, использую Space (49)")
                target_keycode = 49  # Space
        
        # Создай callback
        def on_hotkey():
            self.toggle_recording()
        
        # Без модификаторов (Space, F1 и т.д.)
        self.kb_listener = KeyboardListener(
            target_keycode=target_keycode,
            callback=on_hotkey,
            allow_modifiers=False
        )
        self.kb_listener.start()
        
        # Упдейт условия в UI
        self.record_btn.hint.configure(text=f"or {hotkey_str.upper()}")
        
    except Exception as e:
        print(f"[ERROR] Hotkey setup failed: {e}")
```

## Варианты

### Опция 1: Только один Space
```python
listener = KeyboardListener(49, on_hotkey, allow_modifiers=False)
listener.start()
```
**Поведение**: Space триггерит запись, но Cmd+Space игнорируется

### Опция 2: F1 с режимом "долгое нажатие"
```python
# для диктовки, которая повторно записывает материал
# это требует много дополнительных механизмов
```

## Тестирование

```bash
# Проверь что PyObjC установлен
cd ~/vtt-saint4ai
python -c "import Quartz; print('OK')"

# Настрой права
# System Settings > Privacy & Security > Accessibility
# System Settings > Privacy & Security > Input Monitoring
# Добавь Terminal в оба места

# Дан простой тест
# test_hotkey.py
from macos_keyboard import KeyboardListener

def on_space():
    print("🔥 SPACE понят!")

listener = KeyboardListener(49, on_space)  # 49 = Space
listener.start()

print("🎧 Listening for SPACE key...")
print("❌ CTRL+C to stop")

try:
    while True:
        import time
        time.sleep(1)
except KeyboardInterrupt:
    listener.stop()
    print("

Stopped.")
```

## Ожидаемые выводы

### Успех
```
🎧 [HOTKEY] Keyboard Tap запущен.
   Слушаем keycode: 49
   Allow modifiers: False
```

### Нет прав
```
❌ [HOTKEY] Ошибка: Не удалось создать EventTap.
Проверь права в System Settings -> Privacy & Security:
  1. Accessibility (Универсальный доступ)
  2. Input Monitoring (Мониторинг ввода)
Добавь туда Terminal или VTT.app
```

### Нет PyObjC
```
[ERROR] PyObjC не установлен. Установи: pip install pyobjc-framework-Cocoa
```

## Понятие квалификатора `allow_modifiers`

```python
# Space игнорирует Cmd, Ctrl, Alt, Shift
listener = KeyboardListener(49, callback, allow_modifiers=False)
# При нажатии Cmd+Space - огород не триггерится
# При нажатии только Space - триггерится (🔥)

# Space триггерит только если прижат модификатор
listener = KeyboardListener(49, callback, allow_modifiers=True)
# При нажатии Space - он не триггерится
# При нажатии Cmd+Space - триггерится (🔥)
```

## УКОНОМНО! Space и UX

### Проблема
- Если Space - поомитое hotkey, то пользователь не сможет печатать пробелы

### Решение
```python
# В _event_callback, если Space:
# return event     <- По тропинки, Space напечатается в других окнах
# return None      <- Space поглощен (VTT регистрирует, но пробел не напечатается)
```

### Рекомендация
- Лучших результатов дасти F1, F2 или F3
- не Space для мосного hotkey
- И либо Option+Space, так как так трогает живые коды

## Референции

- Whisper Flow - коммерческие товары, тоже использует CGEventTap
- Super Whisper - открытого источника
- [Core Graphics EventTap](https://developer.apple.com/documentation/coregraphics/core_graphics_event_tap_services)
- [macOS 15 Security Changes](https://developer.apple.com/documentation/security)

## Частые проблемы

### “Нет конмуникации”
- Выли Terminal из Accessibility и Input Monitoring
- Перебуть
- Новые автоадорос Terminal

### “Энтрин много таймавтов”
- Если EventTap был активн только меньше 100мс, то macOS автоматически отключает его
- Модуль автоматически переактивирует читать сообщение ошибки ✅

### “Копия Space не работаюкт, сидят Cmd+Space”
- Замените hotkey с F1, F2 или F3
- Или используйте Option+Space для модификатора
