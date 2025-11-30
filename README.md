# Investment Platform

A Python project for investment management.

## Project Structure

```
.
├── frontend/              # React + TypeScript front-end application
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
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
python tests/test_connection.py
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

## Front-End Setup

### Prerequisites

- Node.js 18+ and npm (or yarn/pnpm)

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create environment file:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and configure:
   - `VITE_API_BASE_URL`: Backend API base URL (default: `http://localhost:8000/api`)
   - `VITE_WS_URL`: WebSocket URL for real-time data (default: `ws://localhost:8000/ws`)

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

### Building for Production

Build the application:
```bash
npm run build
```

The production build will be in the `frontend/dist/` directory.

Preview the production build:
```bash
npm run preview
```

### Front-End Development Tools

**Linting:**
```bash
npm run lint
```

**Formatting:**
```bash
npm run format
npm run format:check
```

**Testing:**
```bash
npm run test
npm run test:ui
npm run test:coverage
```

### Front-End Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Zustand** - State management
- **Axios** - HTTP client
- **Vitest** - Testing framework
- **React Testing Library** - Component testing

## License

MIT

