# PowerShell script to set up virtual environment for Investment Platform
# Make sure Python 3.8+ is installed and in your PATH

Write-Host "Setting up virtual environment..." -ForegroundColor Green

# Check if Python is available
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} else {
    Write-Host "ERROR: Python not found. Please install Python 3.8+ and add it to your PATH." -ForegroundColor Red
    Write-Host "Download Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment in .venv..." -ForegroundColor Cyan
& $pythonCmd -m venv .venv

if ($LASTEXITCODE -eq 0) {
    Write-Host "Virtual environment created successfully!" -ForegroundColor Green
    
    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & .\.venv\Scripts\Activate.ps1
    
    # Upgrade pip
    Write-Host "Upgrading pip..." -ForegroundColor Cyan
    python -m pip install --upgrade pip
    
    # Install requirements if they exist
    if (Test-Path "requirements.txt") {
        Write-Host "Installing requirements..." -ForegroundColor Cyan
        python -m pip install -r requirements.txt
    }
    
    if (Test-Path "requirements-dev.txt") {
        Write-Host "Installing development requirements..." -ForegroundColor Cyan
        python -m pip install -r requirements-dev.txt
    }
    
    Write-Host "`nSetup complete! Virtual environment is activated." -ForegroundColor Green
    Write-Host "To activate it in the future, run: .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
} else {
    Write-Host "Failed to create virtual environment." -ForegroundColor Red
    exit 1
}


