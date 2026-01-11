# VTT - Сборка для macOS

## ВАЖНО: Актуальный код на GitHub!

Последняя версия VTT v2.1 с аналитикой уже на GitHub. Просто клонируй и собирай!

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
Привет! Мне нужно адаптировать VTT (Voice-to-Text) приложение для macOS и собрать DMG установщик.

Я уже на ветке `macos` - все изменения делай здесь и потом запушь в эту ветку.

Текущий код в voice_to_text.py написан для Windows. Нужно:

1. **Адаптировать код под macOS:**
   - Заменить `keyboard` библиотеку на `pynput` (keyboard не работает на Mac без sudo)
   - Убрать `winreg` (Windows-only) - заменить автозапуск на LaunchAgents для Mac
   - Проверить `pyautogui` - может потребоваться разрешение Accessibility
   - Убрать `ctypes.windll` вызовы - это Windows API

2. **Создать macOS версию файла** - можно назвать `voice_to_text_mac.py`

3. **Создать иконку для Mac:**
   - Конвертировать icon.ico в icon.icns (формат macOS)
   - Или создать новую иконку

4. **Собрать .app и DMG:**
   ```bash
   pip3 install -r requirements.txt
   pip3 install pyinstaller pynput

   pyinstaller --onefile --windowed --name "VTT" --icon icon.icns voice_to_text_mac.py

   # Создать DMG
   hdiutil create -volname "VTT @SAINT4AI" -srcfolder dist/VTT.app -ov -format UDZO VTT_v2.0_Mac.dmg
   ```

5. **Важные отличия macOS:**
   - Горячие клавиши: вместо F9 лучше использовать Cmd+Shift+R или подобное
   - Нужно запросить разрешение на микрофон и Accessibility в System Preferences
   - Floating widget может работать иначе (проверить attributes)

После завершения:
- Закоммить все изменения
- Запушить в ветку macos: `git push -u origin macos`

6. **ВАЖНО - Аналитика:**
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
pip3 install customtkinter pillow sounddevice numpy scipy groq pyperclip pyautogui python-dotenv pyinstaller pynput
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
├── voice_to_text.py      # Windows версия
├── voice_to_text_mac.py  # macOS версия (создать)
├── build.py              # Windows билд скрипт
├── build_mac.py          # macOS билд скрипт (создать)
├── requirements.txt      # Зависимости
├── icon.ico              # Windows иконка
├── icon.icns             # macOS иконка (создать)
└── terms.json            # Словарь терминов
```
