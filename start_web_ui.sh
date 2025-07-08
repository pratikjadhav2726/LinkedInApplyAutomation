#!/bin/bash

echo
echo "========================================"
echo "  LinkedIn Easy Apply Bot - Web UI"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[ERROR] Python is not installed"
    echo "Please install Python 3.9+ from https://python.org"
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "[INFO] Python found: $PYTHON_CMD"
echo "[INFO] Starting LinkedIn Easy Apply Bot Web UI..."
echo

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "[INFO] Virtual environment detected: $VIRTUAL_ENV"
fi

# Try UV first, then pip
echo "[INFO] Checking dependencies..."
if command -v uv &> /dev/null; then
    echo "[INFO] UV found, using UV for dependency management..."
    uv sync
else
    echo "[INFO] UV not found, checking for Flask and psutil..."
    $PYTHON_CMD -c "import flask, psutil" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "[INFO] Installing missing dependencies with pip..."
        $PYTHON_CMD -m pip install flask psutil
    fi
fi

# Make sure we have the output directory
mkdir -p output

# Start the web UI
echo
echo "[INFO] Launching web interface..."
echo "[INFO] The web UI will open at: http://localhost:5000"
echo
echo "[TIP] Keep this terminal open while using the bot"
echo "[TIP] Press Ctrl+C to stop the web UI"
echo

$PYTHON_CMD web_ui.py

echo
echo "[INFO] Web UI has been stopped"