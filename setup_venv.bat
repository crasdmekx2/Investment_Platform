@echo off
REM Batch script to set up virtual environment for Investment Platform
REM Make sure Python 3.8+ is installed and in your PATH

echo Setting up virtual environment...

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+ and add it to your PATH.
    echo Download Python from: https://www.python.org/downloads/
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment in .venv...
python -m venv .venv

if %errorlevel% equ 0 (
    echo Virtual environment created successfully!
    
    REM Activate virtual environment
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    
    REM Upgrade pip
    echo Upgrading pip...
    python -m pip install --upgrade pip
    
    REM Install requirements if they exist
    if exist requirements.txt (
        echo Installing requirements...
        python -m pip install -r requirements.txt
    )
    
    if exist requirements-dev.txt (
        echo Installing development requirements...
        python -m pip install -r requirements-dev.txt
    )
    
    echo.
    echo Setup complete! Virtual environment is activated.
    echo To activate it in the future, run: .venv\Scripts\activate.bat
) else (
    echo Failed to create virtual environment.
    exit /b 1
)


