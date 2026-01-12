"""macOS Global Keyboard Listener using CGEventTap.

Это решение использует CGEventTap вместо NSEvent для перехвата
глобальных горячих клавиш БЕЗ модификаторов (Space, F1, и т.д.).

Почему CGEventTap работает:
- Работает на уровне ниже, чем NSEvent
- Не требует root, только Accessibility Permission
- Может ловить ВСЕ клавиши, включая обычные
- Используется Whisper Flow и Super Whisper
"""

import threading
import time
try:
    import Quartz
    from Foundation import NSObject
except ImportError:
    print("[ERROR] PyObjC не установлен. Установи: pip install pyobjc-framework-Cocoa")
    Quartz = None


class KeyboardListener(threading.Thread):
    """Слушатель клавиш на уровне системы используя CGEventTap."""

    # Стандартные коды клавиш на macOS
    KEYCODES = {
        'space': 49,
        'f1': 122,
        'f2': 120,
        'f3': 99,
        'f4': 118,
        'f5': 96,
        'f6': 97,
        'f7': 98,
        'f8': 100,
        'f9': 101,
        'f10': 109,
        'f11': 103,
        'f12': 111,
        'f13': 105,
        'f14': 107,
        'f15': 113,
        'return': 36,
        'tab': 48,
        'capslock': 57,
        'escape': 53,
        'delete': 51,
        'backspace': 51,
        'up': 126,
        'down': 125,
        'left': 123,
        'right': 124,
        'a': 0,
        'b': 11,
        'c': 8,
        'd': 2,
        'e': 14,
        'f': 3,
        'g': 5,
        'h': 4,
        'i': 34,
        'j': 38,
        'k': 40,
        'l': 37,
        'm': 46,
        'n': 45,
        'o': 31,
        'p': 35,
        'q': 12,
        'r': 15,
        's': 1,
        't': 17,
        'u': 32,
        'v': 9,
        'w': 13,
        'x': 7,
        'y': 16,
        'z': 6,
    }

    def __init__(self, target_keycode, callback, allow_modifiers=False):
        """Инициализируй слушатель.

        Args:
            target_keycode (int): Код клавиши для перехвата (49 для Space)
            callback (callable): Функция для вызова при нажатии
            allow_modifiers (bool): Если False, игнорировать если нажаты модификаторы
        """
        super().__init__()
        self.target_keycode = target_keycode
        self.callback = callback
        self.allow_modifiers = allow_modifiers
        self.daemon = True
        self.tap = None
        self.run_loop_source = None
        self.running = False

        if not Quartz:
            raise RuntimeError("PyObjC не установлен")

    @classmethod
    def get_keycode(cls, key_name):
        """Получи код клавиши по имени.

        Args:
            key_name (str): Имя клавиши ('space', 'f1', и т.д.)

        Returns:
            int: Код клавиши или None
        """
        return cls.KEYCODES.get(key_name.lower())

    def run(self):
        """Запусти слушатель в отдельном потоке."""
        self.running = True

        # Маска событий: только KeyDown
        mask = (1 << Quartz.kCGEventKeyDown)

        # Создай Event Tap
        # kCGSessionEventTap = перехват на уровне сессии пользователя
        # kCGHeadInsertEventTap = вставка в начало цепи обработки событий
        self.tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            0,
            mask,
            self._event_callback,
            None
        )

        if not self.tap:
            print(
                "❌ [HOTKEY] Ошибка: Не удалось создать EventTap.\n"
                "Проверь права в System Settings -> Privacy & Security:\n"
                "  1. Accessibility (Универсальный доступ)\n"
                "  2. Input Monitoring (Мониторинг ввода)\n"
                "Добавь туда Terminal или VTT.app"
            )
            return

        # Создай RunLoop Source
        self.run_loop_source = Quartz.CFMachPortCreateRunLoopSource(
            None, self.tap, 0
        )

        # Добавь в RunLoop текущего потока
        Quartz.CFRunLoopAddSource(
            Quartz.CFRunLoopGetCurrent(),
            self.run_loop_source,
            Quartz.kCFRunLoopCommonModes
        )

        # Включи Tap
        Quartz.CGEventTapEnable(self.tap, True)

        print(
            f"🎧 [HOTKEY] Keyboard Tap запущен.\n"
            f"   Слушаем keycode: {self.target_keycode}\n"
            f"   Allow modifiers: {self.allow_modifiers}"
        )

        # Запусти RunLoop (это блокирует текущий поток)
        try:
            Quartz.CFRunLoopRun()
        except KeyboardInterrupt:
            self.stop()

    def _event_callback(self, proxy, type_, event, refcon):
        """Callback для обработки событий клавиатуры."""
        # Если Tap был отключен по timeout - переактивируй
        if type_ == Quartz.kCGEventTapDisabledByTimeout:
            print("⚠️  [HOTKEY] EventTap отключен по timeout, переактивируем...")
            Quartz.CGEventTapEnable(self.tap, True)
            return event

        # Пропусти если не KeyDown
        if type_ != Quartz.kCGEventKeyDown:
            return event

        try:
            # Получи код клавиши
            keycode = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGKeyboardEventKeycode
            )

            # Проверь если это наша клавиша
            if keycode == self.target_keycode:
                # Получи флаги модификаторов
                flags = Quartz.CGEventGetFlags(event)

                # Проверь какие модификаторы нажаты
                has_command = bool(flags & Quartz.kCGEventFlagMaskCommand)
                has_control = bool(flags & Quartz.kCGEventFlagMaskControl)
                has_alternate = bool(flags & Quartz.kCGEventFlagMaskAlternate)
                has_shift = bool(flags & Quartz.kCGEventFlagMaskShift)

                # Проверь условие запуска
                has_modifiers = has_command or has_control or has_alternate or has_shift

                # Если allow_modifiers=False и есть модификаторы - пропусти
                if not self.allow_modifiers and has_modifiers:
                    return event

                # Если allow_modifiers=True и нет модификаторов - пропусти
                if self.allow_modifiers and not has_modifiers:
                    return event

                # 🔥 ТРИГГЕР! Вызови callback
                try:
                    self.callback()
                except Exception as e:
                    print(f"❌ [HOTKEY] Ошибка в callback: {e}")

                # Важно: возвращаем event для того, чтобы событие продолжило
                # нормальную обработку. Если вернуть None, событие будет
                # поглощено и, например, Space не напечатается в других окнах.
                return event

        except Exception as e:
            print(f"❌ [HOTKEY] Ошибка в обработке события: {e}")

        return event

    def stop(self):
        """Остановка слушателя."""
        self.running = False
        try:
            if self.run_loop_source:
                Quartz.CFRunLoopRemoveSource(
                    Quartz.CFRunLoopGetCurrent(),
                    self.run_loop_source,
                    Quartz.kCFRunLoopCommonModes
                )
            if self.tap:
                Quartz.CGEventTapEnable(self.tap, False)
            Quartz.CFRunLoopStop(Quartz.CFRunLoopGetCurrent())
            print("✓ [HOTKEY] Keyboard Tap остановлен")
        except Exception as e:
            print(f"⚠️  [HOTKEY] Ошибка при остановке: {e}")
