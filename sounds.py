"""
Premium sounds for VTT @SAINT4AI
iPhone-style notification sounds using winsound
"""
import winsound
import threading
import time


def play_start_sound():
    """Premium sound for recording start - ascending tone like iPhone."""
    def play():
        # Ascending tones - like iPhone activation
        frequencies = [523, 659, 784]  # C5, E5, G5 (major chord ascending)
        for freq in frequencies:
            winsound.Beep(freq, 80)
            time.sleep(0.02)
    threading.Thread(target=play, daemon=True).start()


def play_stop_sound():
    """Premium sound for recording stop - descending tone."""
    def play():
        # Descending tones - indicates stop
        frequencies = [784, 659, 523]  # G5, E5, C5 (descending)
        for freq in frequencies:
            winsound.Beep(freq, 80)
            time.sleep(0.02)
    threading.Thread(target=play, daemon=True).start()


def play_success_sound():
    """Premium sound for success - pleasant chime."""
    def play():
        # Success chime - like iPhone success
        winsound.Beep(880, 100)  # A5
        time.sleep(0.05)
        winsound.Beep(1109, 150)  # C#6
    threading.Thread(target=play, daemon=True).start()


def play_error_sound():
    """Sound for error."""
    def play():
        winsound.Beep(300, 200)
        time.sleep(0.1)
        winsound.Beep(300, 200)
    threading.Thread(target=play, daemon=True).start()


if __name__ == "__main__":
    print("Testing sounds...")
    print("Start sound:")
    play_start_sound()
    time.sleep(1)

    print("Stop sound:")
    play_stop_sound()
    time.sleep(1)

    print("Success sound:")
    play_success_sound()
    time.sleep(1)

    print("Error sound:")
    play_error_sound()
