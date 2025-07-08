@echo off
echo.
echo ========================================
echo   LinkedIn Easy Apply Bot - Web UI
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo [INFO] Python found
echo [INFO] Starting LinkedIn Easy Apply Bot Web UI...
echo.

REM Try to install dependencies if they don't exist
echo [INFO] Checking dependencies...
python -c "import flask, psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing missing dependencies...
    pip install flask psutil
)

REM Start the web UI
echo [INFO] Launching web interface...
echo [INFO] The web UI will open at: http://localhost:5000
echo.
echo [TIP] Keep this window open while using the bot
echo [TIP] Press Ctrl+C to stop the web UI
echo.

python web_ui.py

echo.
echo [INFO] Web UI has been stopped
pause