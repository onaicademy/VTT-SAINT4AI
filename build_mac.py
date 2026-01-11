"""
Build script for VTT @SAINT4AI - macOS
Creates standalone .app and DMG using PyInstaller
"""
import os
import subprocess
import shutil

APP_NAME = "VTT"
APP_VERSION = "2.1"
MAIN_SCRIPT = "voice_to_text_mac.py"
ICON_FILE = "icon.icns"
DMG_NAME = f"VTT_v{APP_VERSION}_Mac.dmg"


def build():
    print("=" * 50)
    print("Building VTT @SAINT4AI for macOS...")
    print("=" * 50)

    # Clean previous builds
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            print(f"Cleaning {folder}...")
            shutil.rmtree(folder)

    # Remove old spec file
    if os.path.exists(f"{APP_NAME}.spec"):
        os.remove(f"{APP_NAME}.spec")

    # PyInstaller command for macOS
    cmd = [
        'pyinstaller',
        '--name', APP_NAME,
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
        '--hidden-import', 'pynput',
        '--hidden-import', 'pynput.keyboard',
        '--hidden-import', 'pynput.keyboard._darwin',
        '--hidden-import', 'pynput._util',
        '--hidden-import', 'pynput._util.darwin',
        '--hidden-import', 'pyperclip',
        '--hidden-import', 'pyautogui',
        '--hidden-import', 'groq',
        '--hidden-import', 'requests',
        '--hidden-import', 'tkinter',
        '--hidden-import', 'tkinter.ttk',
        '--collect-all', 'customtkinter',
        '--collect-all', 'pynput',
        '--collect-submodules', 'pynput',
        '--add-data', 'terms.json:.',
        '--add-data', 'analytics.py:.',
        '--osx-bundle-identifier', 'com.saint4ai.vtt',
    ]

    if os.path.exists(ICON_FILE):
        cmd.extend(['--icon', ICON_FILE])
        print(f"Using icon: {ICON_FILE}")

    cmd.append(MAIN_SCRIPT)

    print("\nRunning PyInstaller...")
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)) or '.')

    if result.returncode == 0:
        app_path = os.path.join('dist', f'{APP_NAME}.app')
        if os.path.exists(app_path):
            print("\n" + "=" * 50)
            print("APP BUILD SUCCESSFUL!")
            print(f"App: {os.path.abspath(app_path)}")

            # Sign the app (ad-hoc signature for local use)
            print("\nSigning app...")
            sign_result = subprocess.run(['codesign', '--force', '--deep', '--sign', '-', app_path])
            if sign_result.returncode == 0:
                print("App signed successfully!")
            else:
                print("Warning: Signing failed, app may not run properly")

            # Create DMG
            print("\nCreating DMG installer...")
            create_dmg(app_path)
        else:
            print("App bundle not found!")
    else:
        print("Build failed!")

    return result.returncode


def create_dmg(app_path):
    """Create DMG from .app bundle."""
    dmg_path = DMG_NAME

    # Remove existing DMG
    if os.path.exists(dmg_path):
        os.remove(dmg_path)

    # Create DMG using hdiutil
    cmd = [
        'hdiutil', 'create',
        '-volname', 'VTT @SAINT4AI',
        '-srcfolder', app_path,
        '-ov',
        '-format', 'UDZO',
        dmg_path
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0 and os.path.exists(dmg_path):
        size_mb = os.path.getsize(dmg_path) / (1024 * 1024)
        print(f"\nDMG CREATED SUCCESSFULLY!")
        print(f"DMG: {os.path.abspath(dmg_path)}")
        print(f"Size: {size_mb:.1f} MB")
    else:
        print("DMG creation failed!")


if __name__ == "__main__":
    build()
