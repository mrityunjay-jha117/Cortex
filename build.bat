@echo off
REM ============================================================
REM  build.bat — One-click build script for Cognitive Automator
REM
REM  Requirements:
REM    - Python 3.11+ in PATH
REM    - pip install pyinstaller
REM    - UPX in PATH (optional, for compression)
REM    - Inno Setup 6 (optional, for installer)
REM
REM  Usage: build.bat [--skip-installer]
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   Cognitive Automator — Build Script
echo ============================================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH. Install Python 3.11+.
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] Python %PY_VER%

REM --- Check PyInstaller ---
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller pyinstaller-hooks-contrib
)
echo [OK] PyInstaller ready

REM --- Install dependencies ---
echo.
echo [STEP 1] Installing dependencies...
pip install -e ".[build]" --quiet
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    exit /b 1
)
echo [OK] Dependencies installed

REM --- Clean previous build ---
echo.
echo [STEP 2] Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist
echo [OK] Clean done

REM --- Generate placeholder icon if missing ---
if not exist cognitive_automator\assets\icon.ico (
    echo [INFO] No icon.ico found — generating placeholder...
    python scripts\generate_icon.py
)

REM --- Run PyInstaller ---
echo.
echo [STEP 3] Running PyInstaller (onefile mode)...
python -m PyInstaller CognitiveAutomator.spec --noconfirm --log-level WARN
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)
echo [OK] EXE built: dist\CognitiveAutomator.exe

REM --- Report EXE size ---
for %%f in (dist\CognitiveAutomator.exe) do (
    set /a SIZE_MB=%%~zf / 1048576
    echo [INFO] EXE size: !SIZE_MB! MB
)

REM --- Inno Setup installer (optional) ---
if "%1"=="--skip-installer" goto :done

set ISCC_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist %ISCC_PATH% (
    echo.
    echo [STEP 4] Building installer with Inno Setup...
    if not exist Output mkdir Output
    %ISCC_PATH% CognitiveAutomator_Setup.iss /Q
    if errorlevel 1 (
        echo [WARN] Inno Setup failed — EXE is still available in dist\
    ) else (
        echo [OK] Installer built: Output\CognitiveAutomator-Setup-1.0.0.exe
    )
) else (
    echo [SKIP] Inno Setup not found at %ISCC_PATH% — skipping installer.
    echo        Install Inno Setup 6 from https://jrsoftware.org/isinfo.php
    echo        Then re-run: build.bat
)

:done
echo.
echo ============================================================
echo   Build complete!
echo   EXE:       dist\CognitiveAutomator.exe
if exist Output\CognitiveAutomator-Setup-1.0.0.exe (
    echo   Installer: Output\CognitiveAutomator-Setup-1.0.0.exe
)
echo ============================================================
echo.
