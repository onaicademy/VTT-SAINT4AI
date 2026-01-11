"""Test microphone directly"""
import sounddevice as sd
import numpy as np
import time

print("=" * 50)
print("ТЕСТ МИКРОФОНА")
print("=" * 50)

# List all devices
print("\nВсе аудио устройства:")
devices = sd.query_devices()
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        print(f"  [{i}] {d['name']} (in={d['max_input_channels']}, out={d['max_output_channels']})")

print(f"\nУстройство по умолчанию: {sd.default.device}")

# Test each input device
input_devices = []
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        name = d['name'].lower()
        if 'mic' in name or 'microphone' in name:
            input_devices.append((i, d['name']))

print(f"\nНайдено микрофонов: {len(input_devices)}")

for dev_id, dev_name in input_devices:
    print(f"\n--- Тест: {dev_name} (ID: {dev_id}) ---")
    try:
        # Record 2 seconds
        print("Запись 2 секунды... ГОВОРИ!")
        recording = sd.rec(int(2 * 16000), samplerate=16000, channels=1, dtype='int16', device=dev_id)
        sd.wait()

        # Check signal level
        level = np.abs(recording).mean()
        max_level = np.abs(recording).max()

        print(f"  Средний уровень: {level:.2f}")
        print(f"  Максимальный: {max_level}")

        if max_level > 100:
            print("  [OK] Сигнал обнаружен!")
        else:
            print("  [!] Сигнал очень слабый или нет")

    except Exception as e:
        print(f"  [ОШИБКА] {e}")

print("\n" + "=" * 50)
print("Тест завершен")
