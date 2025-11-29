# Investment Platform

A Python project for investment management.

## Project Structure

```
.
├── src/
│   └── investment_platform/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   └── test_example.py
├── docs/
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Setup

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd investment-platform
   ```

2. Create and set up the virtual environment:
   
   **Option A: Use the automated setup script (Recommended)**
   - On Windows (PowerShell):
     ```powershell
     .\setup_venv.ps1
     ```
   - On Windows (Command Prompt):
     ```cmd
     setup_venv.bat
     ```
   
   **Option B: Manual setup**
   ```bash
   python -m venv .venv
   ```
   
   Then activate the virtual environment:
   - On Windows (PowerShell):
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - On Windows (Command Prompt):
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

   Or install in editable mode with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Usage

Run the main application:
```bash
python -m investment_platform.main
```

## Development

### Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=investment_platform --cov-report=html
```

### Code Formatting

Format code with black:
```bash
black src/ tests/
```

### Linting

Check code style with flake8:
```bash
flake8 src/ tests/
```

Type checking with mypy:
```bash
mypy src/
```

## License

MIT

