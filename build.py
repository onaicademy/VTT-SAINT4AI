"""
Build script for VTT @SAINT4AI
Creates standalone EXE using PyInstaller
"""
import os
import subprocess
import shutil

APP_NAME = "VTT_SAINT4AI"
MAIN_SCRIPT = "voice_to_text.py"
ICON_FILE = "icon.ico"

def build():
    print("=" * 50)
    print("Building VTT @SAINT4AI...")
    print("=" * 50)

    # Clean previous builds
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            print(f"Cleaning {folder}...")
            shutil.rmtree(folder)

    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--name', APP_NAME,
        '--onefile',
        '--windowed',
        '--noconfirm',
        '--clean',
        '--hidden-import', 'customtkinter',
        '--hidden-import', 'PIL',
        '--hidden-import', 'PIL._tkinter_finder',
        '--hidden-import', 'sounddevice',
        '--hidden-import', 'numpy',
        '--hidden-import', 'scipy',
        '--hidden-import', 'scipy.io.wavfile',
        '--hidden-import', 'keyboard',
        '--hidden-import', 'pyperclip',
        '--hidden-import', 'pyautogui',
        '--hidden-import', 'groq',
        '--hidden-import', 'dotenv',
        '--collect-all', 'customtkinter',
    ]

    if os.path.exists(ICON_FILE):
        cmd.extend(['--icon', ICON_FILE])
        # Also add icon as data file for window icon at runtime
        cmd.extend(['--add-data', f'{ICON_FILE};.'])
        print(f"Using icon: {ICON_FILE} (embedded + data)")
    else:
        print("No icon file found, using default")

    cmd.append(MAIN_SCRIPT)

    print("\nRunning PyInstaller...")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

    if result.returncode == 0:
        exe_path = os.path.join('dist', f'{APP_NAME}.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print("\n" + "=" * 50)
            print(f"BUILD SUCCESSFUL!")
            print(f"EXE: {os.path.abspath(exe_path)}")
            print(f"Size: {size_mb:.1f} MB")
            print("=" * 50)
        else:
            print("EXE not found after build")
    else:
        print("Build failed!")

    return result.returncode


if __name__ == "__main__":
    build()
