@echo off
echo ====================================
echo   RAG Bot Dashboard Launcher
echo ====================================
echo.

:: Set PYTHONPATH to ensure imports work
set PYTHONPATH=%~dp0

:: Use the system Python or Miniconda Python
set PYTHON_EXE=python

:: Check if Python is available
%PYTHON_EXE% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python or update PYTHON_EXE path.
    pause
    exit /b 1
)

echo Starting Dashboard Server...
echo Open http://localhost:5000 in your browser
echo.

%PYTHON_EXE% backend/monitor_server.py

pause
