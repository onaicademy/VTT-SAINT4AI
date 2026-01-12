# 🎤 Voice to Text for macOS - Fix: Trackpad Scroll

## 🐛 Проблема: Trackpad Scroll не работает

**Симптомы:**
- ✅ Scroll мышкой = работает
- ❌ Scroll тачпадом = не работает

**Причина:** CustomTkinter on macOS не обрабатывает trackpad события корректно.

---

## ✅ Решение (3 варианта)

### Вариант 1: Простой класс (РЕКОМЕНДУЕТСЯ)

```python
import customtkinter as ctk

class ScrollableTextbox(ctk.CTkTextbox):
    """CTkTextbox с поддержкой trackpad scroll на macOS"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Обработка всех scroll событий
        self.bind('<MouseWheel>', self._on_scroll)
        self.bind('<Button-4>', self._on_scroll)  # trackpad up
        self.bind('<Button-5>', self._on_scroll)  # trackpad down
    
    def _on_scroll(self, event):
        """Единый обработчик для mouse wheel и trackpad"""
        # Trackpad: event.num = 4 (up) или 5 (down)
        if hasattr(event, 'num') and event.num in (4, 5):
            direction = -3 if event.num == 4 else 3  # trackpad = больше
        # Mouse wheel: event.delta > 0 (up) или < 0 (down)
        elif hasattr(event, 'delta'):
            direction = -1 if event.delta > 0 else 1
        else:
            return
        
        self.yview_scroll(direction, 'units')
        return 'break'  # Остановить propagation
```

**Использование в приложении:**
```python
# Вместо:
self.text_output = ctk.CTkTextbox(self, height=250)

# Используйте:
self.text_output = ScrollableTextbox(self, height=250)
```

---

### Вариант 2: Функция для любого виджета

```python
def enable_trackpad_scroll(widget):
    """Добавить trackpad scroll к любому CTkTextbox"""
    def on_scroll(event):
        if hasattr(event, 'num') and event.num in (4, 5):
            distance = -3 if event.num == 4 else 3
        elif hasattr(event, 'delta'):
            distance = -1 if event.delta > 0 else 1
        else:
            return
        
        widget.yview_scroll(distance, 'units')
        return 'break'
    
    widget.bind('<MouseWheel>', on_scroll)
    widget.bind('<Button-4>', on_scroll)
    widget.bind('<Button-5>', on_scroll)

# В вашем App.__init__:
enable_trackpad_scroll(self.text_output)
enable_trackpad_scroll(self.info_text)
```

---

### Вариант 3: Обновить текущий код минимально

В `voice_to_text_app.py` найди строку:

```python
self.text_output = ctk.CTkTextbox(self, height=250, font=("Courier", 11))
self.text_output.pack(...)
```

И добавь после:

```python
# Fix trackpad scroll для macOS
def on_scroll(event):
    if hasattr(event, 'num') and event.num in (4, 5):
        self.text_output.yview_scroll(-3 if event.num == 4 else 3, 'units')
    elif hasattr(event, 'delta'):
        self.text_output.yview_scroll(-1 if event.delta > 0 else 1, 'units')
    return 'break'

self.text_output.bind('<MouseWheel>', on_scroll)
self.text_output.bind('<Button-4>', on_scroll)
self.text_output.bind('<Button-5>', on_scroll)
```

---

## 🧪 Тестирование

```python
# Добавь логирование для дебага:
def on_scroll(event):
    print(f"Event num: {getattr(event, 'num', 'N/A')}")
    print(f"Event delta: {getattr(event, 'delta', 'N/A')}")
    print(f"Event keysym: {event.keysym}")
    # ... rest of code
```

Покрути тачпадом, посмотри какие события приходят. Это поможет понять конкретно на твой маке.

---

## 📊 Event Values Reference

| Источник | event.num | event.delta | Комента |
|----------|-----------|-------------|---------|
| Mouse wheel up | — | > 0 | Windows/Linux mouse |
| Mouse wheel down | — | < 0 | Windows/Linux mouse |
| Trackpad up | 4 | — | macOS trackpad |
| Trackpad down | 5 | — | macOS trackpad |

---

## 💡 Почему это работает

- **Mouse wheel** отправляет `<MouseWheel>` с `event.delta`
- **Trackpad macOS** отправляет `<Button-4>` (up) и `<Button-5>` (down) с `event.num`
- Default CustomTkinter слушает только `<MouseWheel>`, поэтому trackpad не ловится

Добавляя оба события — ловим и mouse, и trackpad. ✅

---

## 🎯 TL;DR

Скопируй и вставь класс `ScrollableTextbox` в начало файла, замени `ctk.CTkTextbox` на `ScrollableTextbox` — готово!

```python
class ScrollableTextbox(ctk.CTkTextbox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for event in ['<MouseWheel>', '<Button-4>', '<Button-5>']:
            self.bind(event, self._scroll)
    
    def _scroll(self, event):
        if hasattr(event, 'num') and event.num in (4, 5):
            dist = -3 if event.num == 4 else 3
        else:
            dist = -1 if getattr(event, 'delta', -1) > 0 else 1
        self.yview_scroll(dist, 'units')
        return 'break'
```

Один класс, все решено. 🎉
