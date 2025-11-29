# Installing Python for Investment Platform

Python is not currently installed on your system. Here are several ways to install it:

## Option 1: Windows Store (Easiest)

1. Open the Microsoft Store
2. Search for "Python 3.12" or "Python 3.11"
3. Click "Install"
4. After installation, restart your terminal/PowerShell
5. Run `.\setup_venv.ps1` to set up the virtual environment

## Option 2: Official Python Website (Recommended)

1. Visit: https://www.python.org/downloads/
2. Download the latest Python 3.x installer (3.8 or higher)
3. **IMPORTANT**: During installation, check the box "Add Python to PATH"
4. Complete the installation
5. Restart your terminal/PowerShell
6. Run `.\setup_venv.ps1` to set up the virtual environment

## Option 3: Using winget (Windows Package Manager)

If you have Windows 10/11 with winget installed:

```powershell
winget install Python.Python.3.12
```

Then restart your terminal and run `.\setup_venv.ps1`

## Verify Installation

After installing, verify Python is available:

```powershell
python --version
```

You should see something like: `Python 3.12.x`

## Next Steps

Once Python is installed, run:

```powershell
.\setup_venv.ps1
```

This will automatically:
- Create a virtual environment in `.venv`
- Activate it
- Upgrade pip
- Install all project dependencies


