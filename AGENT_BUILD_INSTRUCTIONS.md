# VTT Build Instructions for Agent

## Quick Start

```bash
cd C:\VoiceToText
git pull origin main
python build_both.py
```

## What Gets Built

| File | Description |
|------|-------------|
| `VTT.exe` | Production version for users |
| `VTT_Admin.exe` | Admin version with Supabase dashboard button |

## Current Version: 2.2

### Features
- Groq Whisper transcription
- LLaMA 3.1 70B AI Brain for text correction
- Resizable floating widget
- User counter in footer
- Admin dashboard (Admin version only)

## Build Requirements

- Python 3.11+
- PyInstaller
- All dependencies from requirements.txt

## Build Process

The `build_both.py` script automatically:
1. Removes admin.key
2. Builds VTT.exe (production)
3. Creates admin.key
4. Builds VTT_Admin.exe
5. Copies both EXEs to root folder

## Repository

- URL: https://github.com/onaicademy/VTT-SAINT4AI
- Branch: main

## After Build

EXE files are in the root folder:
- `C:\VoiceToText\VTT.exe`
- `C:\VoiceToText\VTT_Admin.exe`

## Distribution

VTT.exe - distribute to users
VTT_Admin.exe - keep for yourself (admin only)

## Analytics

All analytics go to Supabase:
- Project: qiyekjrpcewewxumhifc
- Dashboard: https://supabase.com/dashboard/project/qiyekjrpcewewxumhifc/editor

## macOS Build

See `BUILD_MACOS.md` for macOS agent instructions.
