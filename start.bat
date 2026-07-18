@echo off
title Cognitive Automator
color 0A

echo =========================================
echo Starting Cognitive Automator...
echo =========================================

:: Check if virtual environment exists
if not exist venv (
    echo [INFO] Virtual environment not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Ensure Python is installed and in your PATH.
        pause
        exit /b 1
    )
)

:: Activate the virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies (updates them if pyproject.toml changed)
echo [INFO] Installing/Updating dependencies...
pip install -e .

:: Start the application
echo [INFO] Launching the application...
python -m cognitive_automator

:: Keep the window open if the app crashes
if errorlevel 1 (
    echo [ERROR] Application exited with an error.
    pause
)
