@echo off
chcp 65001 >nul
echo ============================================
echo    VTT @SAINT4AI - Build Script
echo ============================================
echo.

cd /d "%~dp0"

echo [1/4] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Creating icon...
python create_icon.py
if %errorlevel% neq 0 (
    echo WARNING: Could not create icon, continuing...
)

echo.
echo [3/4] Building EXE with PyInstaller...
python build.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to build EXE
    pause
    exit /b 1
)

echo.
echo [4/4] Creating installer...
echo.
echo To create installer, you need Inno Setup installed.
echo Download from: https://jrsoftware.org/isdl.php
echo.
echo After installing, run:
echo   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
echo.
echo Or open installer.iss in Inno Setup Compiler and click Build.
echo.

echo ============================================
echo    BUILD COMPLETE!
echo ============================================
echo.
echo EXE location: dist\VTT_SAINT4AI.exe
echo.
echo You can now:
echo   1. Run the EXE directly from dist folder
echo   2. Create installer using Inno Setup
echo.
pause
