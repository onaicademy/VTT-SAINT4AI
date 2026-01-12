# Интеграция CGEventTap на Voice-to-Text

## Шаг 1: Данные установки ПОБ

```bash
pip install pyobjc-framework-Cocoa
```

## Шаг 2: Регистрация права

1. **System Settings > Privacy & Security > Accessibility**
   - Открыть "Accessibility"
   - Клик на добавление `+`
   - Пойти в `/Applications/Utilities`
   - Выбери `Terminal.app`
   - Клик на и прикрепи

2. **System Settings > Privacy & Security > Input Monitoring**
   - Вызначай Terminal если уже там
   - Откнить `–` нопку
   - Дода Terminal заново

3. **Ребут Terminal**
   ```bash
   exit  # закрыть Terminal
   # Открыть заново
   ```

## Шаг 3: Редактировать `setup_hotkey()`

Текуший код:
```python
def setup_hotkey(self):
    """Setup global hotkey using pynput."""
    if self.hotkey_listener:
        self.hotkey_listener.stop()
        self.hotkey_listener = None

    self.hotkey_keys = self._parse_hotkey(self.settings["hotkey"])
    self.current_keys = set()

    def on_press(key):
        self.current_keys.add(key)
        if self.hotkey_keys and self.hotkey_keys.issubset(self.current_keys):
            self.after(0, self.toggle_recording)

    def on_release(key):
        self.current_keys.discard(key)

    try:
        self.hotkey_listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
        self.hotkey_listener.start()
        self.record_btn.hint.configure(text=f"or {self._format_hotkey_display(self.settings['hotkey'])}")
    except Exception as e:
        print(f"[ERROR] Hotkey: {e}")
```

Заменить на:
```python
def setup_hotkey(self):
    """Глобальные горячие клавиши используя CGEventTap.
    
    Это решение делает возможным перехват глобальных
    поправка клавиш (гкк Space, F1) БЕЗ модификаторов
    на macOS 15 Tahoe.
    """
    try:
        from macos_keyboard import KeyboardListener
    except ImportError:
        print("❌ [HOTKEY] macos_keyboard не найден. Параллель к войне по fallback на pynput")
        self._setup_hotkey_fallback()
        return
    
    # Останови старый слушатель pynput
    if hasattr(self, 'hotkey_listener') and self.hotkey_listener:
        try:
            self.hotkey_listener.stop()
        except:
            pass
    
    print("⚠️ [HOTKEY] Initializing CGEventTap-based listener...")
    
    # Получи keycode из настроек
    hotkey_str = self.settings.get("hotkey", "space").lower()
    
    try:
        # Пытаясь получить keycode
        if hotkey_str.isdigit():
            target_keycode = int(hotkey_str)
        else:
            target_keycode = KeyboardListener.get_keycode(hotkey_str)
            if target_keycode is None:
                print(f"⚠️  Читать [{hotkey_str}] - Непонятная клавиша, Space (49)")
                target_keycode = 49  # Space
        
        # Создай триггерную функцию
        def on_hotkey():
            try:
                self.toggle_recording()
            except Exception as e:
                print(f"❌ [HOTKEY] Ошибка в callback: {e}")
        
        # Создай и запусти Listener
        # allow_modifiers=False = триггер только если НЕТ модификаторов
        self.kb_listener = KeyboardListener(
            target_keycode=target_keycode,
            callback=on_hotkey,
            allow_modifiers=False
        )
        self.kb_listener.start()
        
        # Обнови UI дорог
        display_text = f"or {hotkey_str.upper()}"
        if hasattr(self, 'record_btn'):
            self.record_btn.hint.configure(text=display_text)
        
        print(f"✓ [HOTKEY] CGEventTap установлен он с keycode {target_keycode}")
        
    except Exception as e:
        print(f"❌ [HOTKEY] Ошибка: {e}")
        print("⚠️  Фольбаск на pynput...")
        self._setup_hotkey_fallback()

def _setup_hotkey_fallback(self):
    """Фольбаск: используй pynput для горячих клавиш с модификаторами."""
    if self.hotkey_listener:
        self.hotkey_listener.stop()
        self.hotkey_listener = None

    self.hotkey_keys = self._parse_hotkey(self.settings["hotkey"])
    self.current_keys = set()

    def on_press(key):
        self.current_keys.add(key)
        if self.hotkey_keys and self.hotkey_keys.issubset(self.current_keys):
            self.after(0, self.toggle_recording)

    def on_release(key):
        self.current_keys.discard(key)

    try:
        self.hotkey_listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
        self.hotkey_listener.start()
        self.record_btn.hint.configure(text=f"or {self._format_hotkey_display(self.settings['hotkey'])}")
        print(f"✓ [HOTKEY] pynput инициализирован (limit: модификаторы нужны)")
    except Exception as e:
        print(f"[ERROR] Hotkey fallback: {e}")
```

## Шаг 4: Настройка остановки

Замени `on_close()` с желательным ними:

```python
def on_close(self):
    self.is_recording = False
    
    # Останови CGEventTap listener
    if hasattr(self, 'kb_listener'):
        try:
            self.kb_listener.stop()
        except:
            pass
    
    # Останови pynput fallback listener
    if self.hotkey_listener:
        try:
            self.hotkey_listener.stop()
        except:
            pass
    
    # ... (rest of close logic)
```

## Шаг 5: Тестировать

```bash
# Права Terminal чек
# System Settings > Privacy & Security > Accessibility и Input Monitoring

# Протестирую Space
python voice_to_text_mac.py

# Должна выводить строки вроде:
# 🎧 [HOTKEY] Keyboard Tap запущен.
#    Слушаем keycode: 49
#    Allow modifiers: False

# Нажми Space - должна занать запись
# Нажми Space + Cmd - НЕ должна занать
```

## Настойка варианты

### Опция 1: Открыть Space (классик)
```python
self.kb_listener = KeyboardListener(
    target_keycode=49,  # Space
    callback=on_hotkey,
    allow_modifiers=False
)
self.kb_listener.start()
```

### Опция 2: Открыть F1 (рекомендуется)
```python
self.kb_listener = KeyboardListener(
    target_keycode=122,  # F1
    callback=on_hotkey,
    allow_modifiers=False
)
self.kb_listener.start()
```

### Опция 3: Модификатор ОПТИОНАЛНЫЙ
```python
# При allow_modifiers=True, триггер только когда модификатор подаво
 self.kb_listener = KeyboardListener(
    target_keycode=49,
    callback=on_hotkey,
    allow_modifiers=True  # Надо Cmd или Shift
)
self.kb_listener.start()
```

## Очека файла задиректорие

```
VTT-SAINT4AI/
├─ macos_keyboard.py          ← НОВЫЙ CGEventTap listener
├─ HOTKEY_SOLUTION.md         ← НОВОЕ документация
├─ INTEGRATION_GUIDE.md        ← НОВЫЕ читаюгие
├─ voice_to_text_mac.py        ← ОБНОВЛЕННЫЕ setup_hotkey()
└─ ...
```

## Ожидаемые выводы

При успешном запуске:
```
🎧 [HOTKEY] Keyboard Tap запущен.
   Слушаем keycode: 49
   Allow modifiers: False
```

При нехватке прав:
```
❌ [HOTKEY] Ошибка: Не удалось создать EventTap.
Проверь права в System Settings -> Privacy & Security:
  1. Accessibility (Универсальный доступ)
  2. Input Monitoring (Мониторинг ввода)
Добавь туда Terminal или VTT.app
```

## Основые органов

| Клавиша | Keycode |
|-----------|--------|
| Space | 49 |
| F1 | 122 |
| F2 | 120 |
| F3 | 99 |
| F4 | 118 |
| F5 | 96 |

[See more](./HOTKEY_SOLUTION.md#%D0%BA%D0%BE%D0%B4%D1%8B-%D0%BA%D0%BB%D0%B0%D0%B2%D0%B8%D1%88-macos)

## Дополнительная информация

[HOTKEY_SOLUTION.md](./HOTKEY_SOLUTION.md) - Модуль на бсегда работают диагностики
