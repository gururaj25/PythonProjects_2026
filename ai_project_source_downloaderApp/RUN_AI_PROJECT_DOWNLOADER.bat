@echo off
title AI Project Source Downloader Launcher
color 0A

echo ==========================================
echo AI Project Source Downloader
echo One Click Startup Script
echo ==========================================

cd /d "%~dp0"

echo.
echo [1/6] Checking Python...
python --version >nul 2>&1

IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not added to PATH.
    echo Please install Python 3.11+
    pause
    exit /b
)

echo.
echo [2/6] Creating virtual environment...

IF NOT EXIST venv (
    python -m venv venv
)

call venv\Scripts\activate

echo.
echo [3/6] Installing backend dependencies...
pip install -r requirements.txt

echo.
echo [4/6] Installing frontend dependencies...

IF EXIST frontend (
    cd frontend

    where npm >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo Node.js/npm not installed.
        echo Install Node.js from https://nodejs.org
        pause
        exit /b
    )

    IF NOT EXIST node_modules (
        call npm install
    )

    start cmd /k "npm run dev"

    cd ..
)

echo.
echo [5/6] Starting FastAPI backend...
start cmd /k "call venv\Scripts\activate && uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo [6/6] Opening application...

timeout /t 5 >nul

start http://localhost:5173
start http://localhost:8000/docs

echo.
echo ==========================================
echo Application Started Successfully
echo ==========================================
echo Frontend : http://localhost:5173
echo Backend  : http://localhost:8000
echo API Docs : http://localhost:8000/docs
echo ==========================================

pause