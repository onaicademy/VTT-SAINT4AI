# VTT v2.3 - Сборка для macOS

## ВАЖНО: Актуальный код на GitHub!

Последняя версия **VTT v2.3** с новой системой горячих клавиш уже на GitHub!

### Что нового в v2.3:
- Новый UI захвата клавиш: Изменить → зажать клавиши → Сохранить
- Поддержка любых комбинаций (Ctrl+Shift+Alt+Win+любая клавиша)
- Поддержка только модификаторов (Ctrl+Shift)
- Улучшенный скролл тачпада для виджета
- Аналитика Supabase

## Шаг 1: Клонировать АКТУАЛЬНУЮ версию

```bash
cd ~/Desktop
git clone https://github.com/onaicademy/VTT-SAINT4AI.git
cd VTT-SAINT4AI

# Убедись что последняя версия:
git pull origin main
```

## Шаг 2: Создать ветку для macOS

```bash
git checkout -b macos
```

## Шаг 3: Промпт для Claude Code

Скопируй этот промпт и вставь в Claude Code на Mac:

---

```
Привет! Мне нужно адаптировать VTT v2.3 (Voice-to-Text) приложение для macOS и собрать DMG установщик.

Я уже на ветке `macos` - все изменения делай здесь и потом запушь в эту ветку.

Текущий код в voice_to_text.py написан для Windows. Нужно:

1. **Адаптировать код под macOS:**
   - Заменить `keyboard` библиотеку на `pynput` (keyboard не работает на Mac без sudo)
   - Убрать `winreg` (Windows-only) - заменить автозапуск на LaunchAgents для Mac
   - Проверить `pyautogui` - может потребоваться разрешение Accessibility
   - Убрать `ctypes.windll` вызовы - это Windows API

2. **ВАЖНО - Новая система горячих клавиш в v2.3:**
   - В Windows используется `keyboard.hook()` для захвата клавиш
   - На Mac нужно использовать `pynput.keyboard.Listener`
   - Логика: start_hotkey_capture() → пользователь зажимает клавиши → save_hotkey_capture()
   - Методы: start_hotkey_capture, save_hotkey_capture, cancel_hotkey_capture, _update_hotkey_display
   - Адаптировать под pynput сохраняя UX

3. **Создать macOS версию файла** - можно назвать `voice_to_text_mac.py`

4. **Создать иконку для Mac:**
   - Конвертировать icon.ico в icon.icns (формат macOS)
   - Или создать новую иконку

5. **Собрать .app и DMG:**
   ```bash
   pip3 install -r requirements.txt
   pip3 install pyinstaller pynput

   pyinstaller --onefile --windowed --name "VTT" --icon icon.icns voice_to_text_mac.py

   # Создать DMG
   hdiutil create -volname "VTT @SAINT4AI" -srcfolder dist/VTT.app -ov -format UDZO VTT_v2.3_Mac.dmg
   ```

6. **Важные отличия macOS:**
   - Горячие клавиши: вместо Win использовать Cmd
   - Нужно запросить разрешение на микрофон и Accessibility в System Preferences
   - Floating widget может работать иначе (проверить attributes)

После завершения:
- Закоммить все изменения
- Запушить в ветку macos: `git push -u origin macos`

7. **ВАЖНО - Аналитика:**
   - Файл `analytics.py` уже настроен с Supabase
   - НЕ МЕНЯТЬ URL и ключи в analytics.py - они уже правильные
   - Supabase URL: https://qiyekjrpcewewxumhifc.supabase.co
   - База уже создана и работает

Начни с чтения текущего voice_to_text.py и адаптируй под macOS.
```

---

## Шаг 4: Установить зависимости на Mac

```bash
# Установить Python если нет
brew install python3

# Установить зависимости
pip3 install customtkinter pillow sounddevice numpy scipy groq pyperclip pyautogui python-dotenv pyinstaller pynput requests
```

## Шаг 5: После сборки

DMG файл будет в текущей папке. Можно:
1. Загрузить на GitHub Releases
2. Протестировать установку (перетащить в Applications)

## Важно для macOS

При первом запуске macOS попросит разрешения:
- **Микрофон** - для записи голоса
- **Accessibility** - для горячих клавиш и автовставки
- **Input Monitoring** - для pynput

Пользователь должен дать эти разрешения в:
`System Preferences → Security & Privacy → Privacy`

---

## Файлы в репозитории

```
VTT-SAINT4AI/
├── voice_to_text.py      # Windows версия v2.3
├── voice_to_text_mac.py  # macOS версия (создать)
├── build_both.py         # Windows билд скрипт (две версии)
├── build_mac.py          # macOS билд скрипт (создать)
├── analytics.py          # Supabase аналитика
├── requirements.txt      # Зависимости
├── icon.ico              # Windows иконка
├── icon.icns             # macOS иконка (создать)
└── terms.json            # Словарь терминов
```
