@echo off
setlocal

if not exist .venv\Scripts\python.exe (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Ensure Python is installed.
        exit /b 1
    )
    echo Installing dependencies...
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies.
        exit /b 1
    )
)

.\.venv\Scripts\python.exe -m src.cli.main %*
