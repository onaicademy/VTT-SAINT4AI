# Альтернативные решения - для продвинутых разработчиков

⎠️ **ТБК**: Эти опции не тоборы если QuickMacHotKey работает.

---

## Предпосылки

Если ты хочешь что-то я что-то строго задомать исключительно используя Cocoa/Quartz фреймворки, вот твои панасен.

```bash
pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz
```

---

## Опция 1: NSEvent Global Monitor (Cocoa) ✅

То - нативные Cocoa орудия, работают надежно.

### Почему это лучше

- Партные Cocoa API
- Не требует threading гравиток
- Работает на нормальных маками и Apple Silicon

### Реализация

```python
from Cocoa import NSEvent, NSEventMaskKeyDown, NSEventMaskFlagsChanged
from Cocoa import NSApplication
from Foundation import NSObject, NSMutableArray
import threading
import time

class CocoaHotkeys(NSObject):
    """Глобальные hotkeys через NSEvent"""
    
    def __init__(self, on_f9_callback):
        self.on_f9_callback = on_f9_callback
        self.listening = False
    
    def start(self):
        """Start listening in background thread"""
        if self.listening:
            return
        
        self.listening = True
        listener_thread = threading.Thread(
            target=self._listen_cocoa,
            daemon=True
        )
        listener_thread.start()
    
    def _listen_cocoa(self):
        """Настраиваем глобальные мониторы для Cocoa"""
        try:
            # Настраиваем мониторы без NSApplication
            
            # Опция 1: Прямое слежение клавиатуры (экспериментально)
            import AppKit
            
            def hotkey_handler(event):
                # F9 = keyCode 101
                if event.keyCode() == 101:
                    self.on_f9_callback()
                return event
            
            # Центральный event monitor
            NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                NSEventMaskKeyDown,
                hotkey_handler
            )
            
            print("✅ Cocoa hotkey listener started")
            
            # Keep the listener running
            while self.listening:
                time.sleep(0.1)
        
        except Exception as e:
            print(f"❌ Cocoa listener error: {e}")
            self.listening = False


# Пример использования
def on_f9():
    print("🔔 F9 pressed via NSEvent!")

hotkeys = CocoaHotkeys(on_f9)
hotkeys.start()

# Дадо слушают hotkeys
print("\nListening for F9... (Press Ctrl+C to stop)")
try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    hotkeys.listening = False
    print("\nHotkey listener stopped")
```

### Она не работает сразу?

```python
# Нужно скопировать расгрузить ан пылесома
# Нисок биет категорически по старимм макос

# Поэтому QuickMacHotKey лучше ✅
```

---

## Опция 2: CGEventTap (Low-level Quartz) - для экспертов

Это даёт полный контроль над всеми системными ностами. Но сложнее.

### На что наобладать

```python
from Quartz import (
    CGEventTapCreate,
    CGEventTapEnable,
    CFRunLoopGetCurrent,
    CFRunLoopAddSource,
    CFMachPortCreateRunLoopSource,
    kCGEventTapOptionDefault,
    kCGHeadInsertEventTap,
    CGEventMaskBit,
    kCGKeyDown,
    CGEventGetIntegerValueField,
    kCGKeyboardEventKeycode,
    CGEventSetIntegerValueField,
    kCGEventSourceStateHIDSystemState,
)
from Foundation import NSRunLoop
import threading

class QuartzEventTap:
    """Low-level CGEventTap for complete control"""
    
    def __init__(self, on_f9_callback):
        self.on_f9_callback = on_f9_callback
        self.tap = None
        self.listening = False
    
    def start(self):
        """Start the event tap"""
        if self.listening:
            return
        
        self.listening = True
        listener_thread = threading.Thread(
            target=self._setup_tap,
            daemon=True
        )
        listener_thread.start()
    
    def _event_tap_callback(self, proxy, event_type, event, refcon):
        """Обработчик всех клавиатурных событий"""
        try:
            # Получаем код клавиши
            keyCode = CGEventGetIntegerValueField(
                event,
                kCGKeyboardEventKeycode
            )
            
            # Проверяем F9 (101)
            if keyCode == 101:
                self.on_f9_callback()
                # Оптионально: блокируем евент от системы
                # return None  # возвращаем None чтобы блокировать
            
            return event  # На деле пропускаем событие
        
        except Exception as e:
            print(f"❌ Event tap callback error: {e}")
            return event
    
    def _setup_tap(self):
        """Устанавливаем тап и запускаем event loop"""
        try:
            # Нужно что-то валдно именовать
            refcon = {'callback': self.on_f9_callback}
            
            # Создаем event tap
            self.tap = CGEventTapCreate(
                kCGHIDEventTap,  # kCGHIDEventTap – средние уровневые
                kCGHeadInsertEventTap,  # Основные тапы регистрируются в головке
                kCGEventTapOptionDefault,  # Дефаолтные опции
                CGEventMaskBit(kCGKeyDown),  # Отслеживаем только клавиатурные события
                self._event_tap_callback,  # Калбэк
                refcon  # Кустомные данные
            )
            
            if not self.tap:
                print("❌ Failed to create event tap (permission denied?)")
                self.listening = False
                return
            
            # Собираем run loop source
            source = CFMachPortCreateRunLoopSource(
                None,  # аллокатор
                self.tap,
                0  # ордер
            )
            
            # Добавляем source в current run loop
            CFRunLoopAddSource(
                CFRunLoopGetCurrent(),
                source,
                None  # режим
            )
            
            # Отключаем тап
            CGEventTapEnable(self.tap, True)
            
            print("✅ Quartz event tap started")
            
            # Основные run loop
            from Foundation import NSRunLoop, NSDefaultRunLoopMode
            runloop = NSRunLoop.currentRunLoop()
            while self.listening:
                runloop.runUntilDate_(
                    NSRunLoop.currentRunLoop().fireDate()
                )
        
        except Exception as e:
            print(f"❌ Event tap setup error: {e}")
            self.listening = False
```

### Негативы

```
❌ Соквнэснюя сложность
❌ Нужно глубокое понимание Quartz
❌ Нужно больше пермиссий
❌ Медленнее чем QuickMacHotKey
```

---

## Опция 3: IOKit Low-level (но НЕ рекомендуется)

Даже ниже Quartz. Целево для кевянора жения на уровне контролыера устройства.

**Не рекомендуем** – Основные cases не требуют этого.

---

## Комвасадия решений

| Техника | Уровень | Используется | Сложность | Рекомендация |
|---|---|---|---|---|
| **QuickMacHotKey** | Мыдный | Carbon/Quartz (штукатура системи) | 3/10 | ✅ 100% выбор |
| **NSEvent Monitor** | Cocoa | Нативные Cocoa APIs | 4/10 | ✅ Кандидат |
| **CGEventTap** | Low-level Quartz | Операционная система | 8/10 | ✅ Экспертов |
| **IOKit** | Одва в драйвере | Промея рв устройств | 10/10 | ❌ Не требуется |

---

## Настройка для разных скенариев

### У меня очень частые понатий F9 не должни быть видными

```python
# Блокируем событие от гстемы CGEventTap или imo Cocoa

class SecretHotkey:
    def _event_tap_callback(self, proxy, event_type, event, refcon):
        keyCode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
        
        if keyCode == 101:  # F9
            self.on_f9_callback()
            return None  # блокируем все событие - система не полусіост F9
        
        return event  # Пропускаем другие
```

### Мне нужны несколько hotkeys

```python
hotkey_configs = {
    101: self.on_f9,       # F9
    109: self.on_f10,      # F10
    103: self.on_f11,      # F11
    111: self.on_f12,      # F12
}

def _event_tap_callback(self, proxy, event_type, event, refcon):
    keyCode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
    
    if keyCode in self.hotkey_configs:
        self.hotkey_configs[keyCode]()
    
    return event
```

### Мне нужны модификаторы (COMMAND+OPTION+K)

```python
from Cocoa import NSEventModifierFlags

COMMAND = 0x00100100  # kEventModifierFlagCommand
OPTION = 0x00080100   # kEventModifierFlagOption

def _event_tap_callback(self, proxy, event_type, event, refcon):
    keyCode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
    flags = CGEventGetIntegerValueField(event, kCGKeyboardEventKeyboardType)  # Get flags
    
    # K = keyCode 40
    if keyCode == 40 and (flags & (COMMAND | OPTION)):
        self.on_hotkey()
    
    return event
```

---

## Дебуггинг

### Полуия не срабатывают

```python
# Добавь гыссо в callback
def _event_tap_callback(self, proxy, event_type, event, refcon):
    keyCode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
    print(f"🕐 Got key: {keyCode}")
    
    if keyCode == 101:
        print("🔔 Matched F9!")
        self.on_f9_callback()
    
    return event
```

### lldb дебуггинг

```bash
lldb ./dist/VTT.app/Contents/MacOS/VTT

# В lldb:
(lldb) breakpoint set -n _event_tap_callback
(lldb) run
# Нажми F9
(lldb) po keyCode  # Покажет keyCode
```

---

## Тестирование

```python
import time
from your_module import CocoaHotkeys  # или QuartzEventTap

test_results = []

def on_f9_test():
    test_results.append(time.time())
    print(f"🔔 F9 detected at {test_results[-1]}")

hotkeys = CocoaHotkeys(on_f9_test)
hotkeys.start()

print("Press F9 three times with 1 second delays...")
time.sleep(5)  # дай тест рун

hotkeys.listening = False

print(f"\nDetected {len(test_results)} F9 presses")
if len(test_results) >= 3:
    print("✅ Test PASSED")
else:
    print("❌ Test FAILED")
```

---

## Нериски и голоса

| Проблема | НЕРИск | Что сделать |
|---|---|---|
| Нет получанных ностаний | Пермиссия | Нобедитесь через System Preferences > Accessibility |
| Event tap не полусястся | Не зарегистрирован | Проверь CGEventTapCreate ретурй |
| Cocoa понтроли сразу выходят | Event loop ОНА твердая | Нужно держать event loop в живые |
| Постоянные краши | Thread любой | Добавь try-except и растарт |

---

## Продвинутые типы

### Swift на macOS

Если ты хотел бы написать на Swift, используй `LocalEventMonitor` для hotkeys.

### Rust + tauri
За если переписывают на Rust, `tauri-hotkey` антиошідует.

---

## Итого

1. Первое пробую: **QuickMacHotKey** ✅
2. Если проблемы: **NSEvent Monitor** ✅
3. Нужна отличная точность: **CGEventTap** 🔬
4. Ничто другое не работает: Перепиши на Swift/Rust

---

✅ **Удачи твоему проекту!**
