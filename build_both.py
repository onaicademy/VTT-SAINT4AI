"""
Build script for VTT @SAINT4AI - Both versions
Creates:
- VTT.exe (production)
- VTT_Admin.exe (with admin dashboard)
"""
import os
import subprocess
import shutil

MAIN_SCRIPT = "voice_to_text.py"
ICON_FILE = "icon.ico"
ADMIN_KEY_FILE = "admin.key"

def build_exe(name, with_admin=False):
    print("\n" + "=" * 50)
    print(f"Building {name}...")
    print("=" * 50)

    # Clean previous builds (handle locked files gracefully)
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
            except PermissionError:
                # Try to remove files individually
                for root, dirs, files in os.walk(folder, topdown=False):
                    for f in files:
                        try:
                            os.remove(os.path.join(root, f))
                        except:
                            pass
                    for d in dirs:
                        try:
                            os.rmdir(os.path.join(root, d))
                        except:
                            pass
                try:
                    os.rmdir(folder)
                except:
                    print(f"Warning: Could not fully clean {folder}, continuing anyway...")

    # Handle admin.key
    if with_admin:
        # Create admin.key for admin build
        with open(ADMIN_KEY_FILE, 'w') as f:
            f.write("admin")
        print("Created admin.key for admin build")
    else:
        # Remove admin.key for production build
        if os.path.exists(ADMIN_KEY_FILE):
            os.remove(ADMIN_KEY_FILE)
        print("Removed admin.key for production build")

    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--name', name,
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
        '--hidden-import', 'requests',
        '--collect-all', 'customtkinter',
    ]

    if os.path.exists(ICON_FILE):
        cmd.extend(['--icon', ICON_FILE])
        cmd.extend(['--add-data', f'{ICON_FILE};.'])

    # Add admin.key to admin build
    if with_admin and os.path.exists(ADMIN_KEY_FILE):
        cmd.extend(['--add-data', f'{ADMIN_KEY_FILE};.'])

    cmd.append(MAIN_SCRIPT)

    print(f"Running: {' '.join(cmd[:10])}...")
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)) or '.')

    if result.returncode == 0:
        exe_path = os.path.join('dist', f'{name}.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"SUCCESS: {name}.exe ({size_mb:.1f} MB)")
            return exe_path

    print(f"FAILED: {name}")
    return None


def main():
    print("=" * 60)
    print("VTT @SAINT4AI - Building Both Versions")
    print("=" * 60)

    results = {}

    # Build production version (without admin)
    prod_exe = build_exe("VTT", with_admin=False)
    if prod_exe:
        # Move to final location
        final_prod = "VTT.exe"
        if os.path.exists(final_prod):
            os.remove(final_prod)
        shutil.copy(prod_exe, final_prod)
        results["VTT.exe"] = final_prod
        print(f"Copied to: {final_prod}")

    # Build admin version (with admin.key)
    admin_exe = build_exe("VTT_Admin", with_admin=True)
    if admin_exe:
        # Move to final location
        final_admin = "VTT_Admin.exe"
        if os.path.exists(final_admin):
            os.remove(final_admin)
        shutil.copy(admin_exe, final_admin)
        results["VTT_Admin.exe"] = final_admin
        print(f"Copied to: {final_admin}")

    # Cleanup
    if os.path.exists(ADMIN_KEY_FILE):
        os.remove(ADMIN_KEY_FILE)

    print("\n" + "=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)
    for name, path in results.items():
        if os.path.exists(path):
            size = os.path.getsize(path) / (1024 * 1024)
            print(f"  {name}: {size:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
