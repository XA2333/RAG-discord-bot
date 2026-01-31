@echo off
echo ====================================
echo   RAG Discord Bot Launcher
echo ====================================
echo.

:: Set PYTHONPATH to ensure imports work
set PYTHONPATH=%~dp0

:: Use the system Python or Miniconda Python
:: Adjust this path if your Python is elsewhere
set PYTHON_EXE=python

:: Check if Python is available
%PYTHON_EXE% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python or update PYTHON_EXE path.
    pause
    exit /b 1
)

echo [1/2] Running Healthcheck...
%PYTHON_EXE% healthcheck.py
if errorlevel 1 (
    echo [WARNING] Healthcheck reported issues. Continuing anyway...
)

echo.
echo [2/2] Starting Discord Bot...
%PYTHON_EXE% main_bot.py

pause
