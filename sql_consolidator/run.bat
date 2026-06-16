@echo off
title SQL Query Consolidation Tool
color 0A

echo ============================================================
echo   SQL QUERY CONSOLIDATION ^& DEDUPLICATION TOOL
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt -q
if not exist "logs" mkdir logs
if not exist "output" mkdir output

:MENU
echo.
echo   1. Run CLI Tool
echo   2. Launch Streamlit GUI
echo   3. Run with Sample Input
echo   4. Run Unit Tests
echo   5. Exit
echo.
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto CLI
if "%choice%"=="2" goto GUI
if "%choice%"=="3" goto SAMPLE
if "%choice%"=="4" goto TEST
if "%choice%"=="5" goto EXIT
goto MENU

:CLI
set /p idir="Input directory: "
set /p odir="Output directory (default ./output): "
if "%odir%"=="" set odir=./output
python main.py -i "%idir%" -o "%odir%" --verbose
pause
goto MENU

:GUI
echo Opening http://localhost:8501
streamlit run ui/streamlit_app.py --server.port 8501
goto MENU

:SAMPLE
python main.py -i "./sample_input" -o "./output/sample_run" --verbose
echo Done! Check ./output/sample_run/
pause
goto MENU

:TEST
pytest tests/ -v --tb=short
pause
goto MENU

:EXIT
deactivate
exit /b 0
