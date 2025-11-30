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

## Database Setup

### Prerequisites

- Docker and Docker Compose installed
- PostgreSQL with TimescaleDB extension (via Docker)

### Initial Setup

1. Start the database container:
   ```bash
   docker-compose up -d
   ```
   
   Or use the setup script:
   - On Windows (PowerShell):
     ```powershell
     .\setup_database.ps1
     ```
   - On Linux/macOS:
     ```bash
     ./setup_database.sh
     ```

2. Execute the database schema:
   ```bash
   python scripts/execute_schema.py
   ```

   This will create all tables, indexes, hypertables, functions, triggers, and policies.

### Database Connection

The database uses the following default connection parameters:
- Host: `localhost`
- Port: `5432`
- Database: `investment_platform`
- User: `postgres`
- Password: `postgres`

You can override these using environment variables:
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

### Testing Database Connectivity

Test database connectivity:
```bash
python test_connection.py
```

## Development

### Running Tests

Run all tests:
```bash
pytest
```

Run database tests only:
```bash
pytest tests/test_schema_verification.py
pytest tests/test_data_integrity.py
pytest tests/test_functions_triggers.py
pytest tests/test_timescaledb_features.py
pytest tests/test_index_performance.py
pytest tests/test_sample_data.py
pytest tests/test_data_quality.py
```

Run tests with coverage:
```bash
pytest --cov=investment_platform --cov-report=html
```

### Database Testing

The test suite includes comprehensive database tests:

1. **Schema Verification** (`test_schema_verification.py`): Verifies all database objects are created correctly
2. **Data Integrity** (`test_data_integrity.py`): Tests constraints, foreign keys, and data validation
3. **Functions & Triggers** (`test_functions_triggers.py`): Tests all database functions and triggers
4. **TimescaleDB Features** (`test_timescaledb_features.py`): Verifies TimescaleDB-specific features
5. **Index Performance** (`test_index_performance.py`): Verifies indexes and query performance
6. **Sample Data** (`test_sample_data.py`): Integration tests with sample data
7. **Data Quality** (`test_data_quality.py`): Data quality validation tests

**Test Execution Order:**
1. Ensure database is running: `docker-compose up -d`
2. Execute schema: `python scripts/execute_schema.py`
3. Run schema verification: `pytest tests/test_schema_verification.py -v`
4. Run remaining tests: `pytest tests/ -v`

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

