# Development Standards

## Introduction & Purpose

This document establishes the development standards for the Investment Platform Python backend development. All backend implementations must adhere to these standards to ensure consistent, maintainable, and high-quality code. These standards are based on Python best practices, industry standards, and the specific requirements of financial data processing applications.

**Purpose:**
- Ensure consistent code quality across all backend features
- Maintain maintainable and testable codebase
- Guide developers in implementing robust, production-ready code
- Establish clear patterns for error handling, logging, and data processing
- Provide actionable checklists and implementation guidelines

**Who Should Use This Document:**
- Backend engineers implementing Python features
- Data engineers working with data collection and processing
- QA engineers writing and reviewing tests
- Code reviewers ensuring standards compliance
- DevOps engineers deploying and monitoring applications

**Reference Documents:**
- [Python Developer Role](../roles/python-developer.md)
- [Data Engineer Role](../roles/data-engineer.md)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [PEP 484 Type Hints](https://peps.python.org/pep-0484/)

---

## 1. Code Style & Formatting

### 1.1 Code Formatter: Black

**MANDATORY:** All code MUST be formatted using Black with the project's configuration.

**Configuration (from `pyproject.toml`):**
- Line length: 100 characters
- Target Python versions: 3.8, 3.9, 3.10, 3.11, 3.12

**Usage:**
```bash
# Format all files
black .

# Check formatting without making changes
black --check .

# Format specific file
black src/investment_platform/ingestion/ingestion_engine.py
```

**Implementation:**
```python
# ✅ Good: Properly formatted with Black
def collect_historical_data(
    self,
    symbol: str,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    **kwargs: Any,
) -> Union[pd.DataFrame, Dict[str, Any]]:
    """Collect historical data for an asset."""
    pass

# ❌ Bad: Inconsistent formatting
def collect_historical_data(self,symbol:str,start_date:Union[str,datetime],end_date:Union[str,datetime],**kwargs:Any)->Union[pd.DataFrame,Dict[str,Any]]:
    """Collect historical data for an asset."""
    pass
```

**Checklist:**
- [ ] All code formatted with Black before commit
- [ ] Line length does not exceed 100 characters
- [ ] Consistent indentation (4 spaces, no tabs)
- [ ] Proper spacing around operators and after commas
- [ ] Black configuration matches `pyproject.toml`

### 1.2 Linting: Flake8

**MANDATORY:** All code MUST pass Flake8 linting checks.

**Configuration (from `pyproject.toml`):**
- Max line length: 100
- Extended ignore: E203, E266, E501, W503 (compatible with Black)

**Usage:**
```bash
# Run flake8
flake8 src/ tests/

# Run with specific configuration
flake8 --config=pyproject.toml src/
```

**Common Issues to Avoid:**
- Unused imports
- Undefined variables
- Syntax errors
- Style violations

**Checklist:**
- [ ] All code passes Flake8 checks
- [ ] No unused imports or variables
- [ ] No undefined names
- [ ] Follows PEP 8 style guidelines

### 1.3 Type Checking: mypy

**MANDATORY:** All code MUST include type hints and pass mypy type checking.

**Configuration (from `pyproject.toml`):**
- Python version: 3.8
- Warn return any: true
- Warn unused configs: true
- Disallow untyped defs: false (gradual typing)
- Ignore missing imports: true (for third-party libraries)

**Type Hint Requirements:**
- All function parameters must have type hints
- All function return values must have type hints
- Class attributes should have type hints where possible
- Use `Optional[T]` for nullable types
- Use `Union[T, U]` for multiple possible types
- Use `Dict[str, Any]` for flexible dictionaries
- Use `List[T]` for lists

**Implementation:**
```python
# ✅ Good: Complete type hints
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import pandas as pd

def ingest(
    self,
    symbol: str,
    asset_type: str,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    collector_kwargs: Optional[Dict[str, Any]] = None,
    asset_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Ingest data for a single asset.
    
    Returns:
        Dictionary with ingestion results containing:
        - asset_id: Optional[int]
        - records_collected: int
        - records_loaded: int
        - status: str
        - error_message: Optional[str]
    """
    result: Dict[str, Any] = {
        "asset_id": None,
        "records_collected": 0,
        "records_loaded": 0,
        "status": "failed",
        "error_message": None,
    }
    return result

# ❌ Bad: Missing type hints
def ingest(self, symbol, asset_type, start_date, end_date, collector_kwargs=None):
    result = {}
    return result
```

**Type Hint Patterns:**
```python
# Optional parameters
def process_data(data: pd.DataFrame, validate: Optional[bool] = None) -> bool:
    pass

# Union types
def get_value(key: str) -> Union[str, int, float, None]:
    pass

# Generic collections
def process_items(items: List[Dict[str, Any]]) -> List[str]:
    pass

# Class attributes
class DataCollector:
    logger: logging.Logger
    output_format: str = "dataframe"
    
    def __init__(self, output_format: str = "dataframe") -> None:
        self.output_format = output_format
```

**Checklist:**
- [ ] All functions have complete type hints
- [ ] All return types are specified
- [ ] Optional parameters use `Optional[T]`
- [ ] Union types used where appropriate
- [ ] mypy passes without errors
- [ ] Type hints are accurate and helpful

---

## 2. Documentation Standards

### 2.1 Docstrings

**MANDATORY:** All public classes, methods, and functions MUST have docstrings.

**Format:** Google-style docstrings (preferred) or NumPy-style.

**Required Sections:**
- Brief description (one line)
- Detailed description (if needed)
- Args: Parameter descriptions with types
- Returns: Return value description with type
- Raises: Exceptions that may be raised (if any)

**Implementation:**
```python
# ✅ Good: Complete Google-style docstring
def collect_historical_data(
    self,
    symbol: str,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    **kwargs: Any,
) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Collect historical data for an asset.
    
    This method fetches historical market data for the specified asset
    within the given date range. Data is returned in the format specified
    by the output_format parameter.
    
    Args:
        symbol: Asset symbol (e.g., 'AAPL', 'BTC-USD', 'EURUSD')
        start_date: Start date for data collection (ISO format string or datetime)
        end_date: End date for data collection (ISO format string or datetime)
        **kwargs: Additional parameters specific to the collector type
        
    Returns:
        Historical data in the specified output format:
        - DataFrame if output_format='dataframe'
        - Dict if output_format='dict'
        - List[Dict] if output_format='list'
        
    Raises:
        APIError: If data collection fails due to API issues
        ValidationError: If input parameters are invalid
        RateLimitError: If API rate limit is exceeded
    """
    pass

# ❌ Bad: Missing or incomplete docstring
def collect_historical_data(self, symbol, start_date, end_date):
    """Collect data."""
    pass
```

**Class Docstrings:**
```python
# ✅ Good: Class with comprehensive docstring
class IngestionEngine:
    """
    Main ingestion engine that orchestrates data collection and loading.
    
    The IngestionEngine coordinates the entire data ingestion pipeline:
    1. Asset registration/retrieval
    2. Data collection via collectors
    3. Schema mapping to database format
    4. Data loading into PostgreSQL
    
    Attributes:
        incremental: Whether to use incremental mode (only fetch missing data)
        on_conflict: How to handle conflicts ('do_nothing', 'update', 'skip')
        asset_manager: AssetManager instance for asset operations
        schema_mapper: SchemaMapper instance for data transformation
        data_loader: DataLoader instance for database operations
    """
    pass
```

**Checklist:**
- [ ] All public classes have docstrings
- [ ] All public methods have docstrings
- [ ] All public functions have docstrings
- [ ] Args section includes all parameters with types
- [ ] Returns section describes return value and type
- [ ] Raises section lists all possible exceptions
- [ ] Docstrings are clear and concise
- [ ] Examples included for complex functions

### 2.2 Inline Comments

**Guidelines:**
- Use comments to explain "why", not "what"
- Code should be self-documenting through clear naming
- Add comments for complex logic or non-obvious decisions
- Keep comments up-to-date with code changes

**Implementation:**
```python
# ✅ Good: Comments explain why, not what
# Use coordinator for intelligent batching to avoid rate limits
if coordinator.enabled:
    data = coordinator.submit_request(...)
else:
    # Direct collection (backward compatibility)
    data = collector.collect_historical_data(...)

# Convert volume to numeric first (handles string decimals like '954.43296228')
# Then convert to int64 for BIGINT database column
volume_series = pd.to_numeric(data["volume"], errors='coerce').fillna(0)
result["volume"] = volume_series.astype("int64")

# ❌ Bad: Comments that just repeat the code
# Get the symbol
symbol = self._get_symbol(name)

# Increment the counter
counter += 1
```

**Checklist:**
- [ ] Comments explain "why", not "what"
- [ ] Complex logic has explanatory comments
- [ ] Non-obvious decisions are documented
- [ ] Comments are kept up-to-date
- [ ] No commented-out code in production

---

## 3. Error Handling

### 3.1 Exception Hierarchy

**MANDATORY:** Use custom exception classes for different error types.

**Custom Exception Classes:**
```python
# Base exception for data collection
class DataCollectionError(Exception):
    """Base exception for data collection errors."""
    pass

# Specific exception types
class APIError(DataCollectionError):
    """Raised when API calls fail."""
    pass

class ValidationError(DataCollectionError):
    """Raised when input validation fails."""
    pass

class RateLimitError(DataCollectionError):
    """Raised when API rate limit is exceeded."""
    pass
```

**Implementation:**
```python
# ✅ Good: Specific exception types
def collect_historical_data(self, symbol: str, ...) -> pd.DataFrame:
    try:
        # Validate input
        if not symbol:
            raise ValidationError("Symbol cannot be empty")
        
        # Make API call
        data = self._fetch_data(symbol)
        
        if data.empty:
            raise APIError(f"No data returned for {symbol}")
        
        return data
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            raise RateLimitError(f"Rate limit exceeded for {symbol}") from e
        raise APIError(f"API error for {symbol}: {e}") from e
    except Exception as e:
        self._handle_error(e, f"collect_historical_data for {symbol}")
        raise

# ❌ Bad: Generic exceptions
def collect_historical_data(self, symbol: str, ...):
    if not symbol:
        raise Exception("Symbol cannot be empty")
    # ...
```

**Checklist:**
- [ ] Custom exception classes used appropriately
- [ ] Exceptions preserve original exception with `from e`
- [ ] Error messages are clear and actionable
- [ ] Exceptions are logged before raising
- [ ] Exception types match error categories

### 3.2 Error Handling Patterns

**Try-Except Blocks:**
- Always catch specific exceptions when possible
- Use `except Exception` only as a last resort
- Always log exceptions with context
- Re-raise exceptions with additional context when appropriate

**Implementation:**
```python
# ✅ Good: Comprehensive error handling
def ingest(self, symbol: str, ...) -> Dict[str, Any]:
    start_time = time.time()
    result = {
        "status": "failed",
        "error_message": None,
        "execution_time_ms": 0,
    }
    
    try:
        # Main logic
        asset_id = self._get_asset_info(symbol, asset_type)
        data = self._collect_data(symbol, start_date, end_date)
        records_loaded = self._load_data(data, asset_id)
        
        result["status"] = "success"
        result["records_loaded"] = records_loaded
        
    except ValidationError as e:
        # Validation errors are permanent - don't retry
        result["error_message"] = f"Validation error: {e}"
        self.logger.error(f"Validation error for {symbol}: {e}")
        
    except RateLimitError as e:
        # Rate limit errors are transient - can retry
        result["error_message"] = f"Rate limit exceeded: {e}"
        self.logger.warning(f"Rate limit for {symbol}: {e}")
        
    except APIError as e:
        # API errors may be transient or permanent
        result["error_message"] = f"API error: {e}"
        self.logger.error(f"API error for {symbol}: {e}", exc_info=True)
        
    except Exception as e:
        # Catch-all for unexpected errors
        result["error_message"] = f"Unexpected error: {e}"
        self.logger.error(
            f"Unexpected error for {symbol}: {e}",
            exc_info=True
        )
        
    finally:
        result["execution_time_ms"] = int((time.time() - start_time) * 1000)
    
    return result
```

**Error Classification:**
```python
# Classify errors for retry logic
def classify_error(error: Exception, error_message: Optional[str] = None) -> Tuple[str, str]:
    """
    Classify an error into a category and provide recovery suggestions.
    
    Returns:
        Tuple of (error_category, recovery_suggestion)
        error_category: 'transient', 'permanent', or 'system'
    """
    error_str = error_message or str(error).lower()
    
    # Transient errors (retryable)
    transient_indicators = ['rate limit', 'timeout', 'connection', 'network']
    if any(indicator in error_str for indicator in transient_indicators):
        return ('transient', 'Error is transient, will retry automatically')
    
    # Permanent errors (not retryable)
    permanent_indicators = ['validation', 'invalid', 'not found', 'unauthorized']
    if any(indicator in error_str for indicator in permanent_indicators):
        return ('permanent', 'Error is permanent, check configuration')
    
    # Default: treat as transient (safer to retry)
    return ('transient', 'Unknown error, will retry automatically')
```

**Checklist:**
- [ ] Specific exceptions caught when possible
- [ ] Exceptions logged with context (`exc_info=True` for unexpected errors)
- [ ] Error messages are clear and actionable
- [ ] Exceptions preserve original with `from e`
- [ ] Error classification used for retry logic
- [ ] Finally blocks used for cleanup

---

## 4. Logging Standards

### 4.1 Logger Setup

**MANDATORY:** All modules MUST use the standard logging module with proper logger names.

**Implementation:**
```python
# ✅ Good: Module-level logger
import logging

logger = logging.getLogger(__name__)

class IngestionEngine:
    def __init__(self):
        # Use module logger, not create new one
        self.logger = logger
        
    def ingest(self, symbol: str, ...):
        self.logger.info(f"Starting ingestion for {symbol}")
        # ...
```

**Logger Configuration:**
- Use `logging.getLogger(__name__)` for module-level loggers
- Use descriptive log messages with context
- Include relevant data in log messages
- Use appropriate log levels

**Checklist:**
- [ ] Module-level logger created with `__name__`
- [ ] Logger used consistently throughout module
- [ ] Log messages include relevant context
- [ ] Appropriate log levels used

### 4.2 Log Levels

**Log Level Guidelines:**
- **DEBUG**: Detailed information for debugging (development only)
- **INFO**: General informational messages (start/end of operations, status updates)
- **WARNING**: Warning messages (non-critical issues, recoverable errors)
- **ERROR**: Error messages (exceptions, failures that need attention)
- **CRITICAL**: Critical errors (system failures, data corruption)

**Implementation:**
```python
# ✅ Good: Appropriate log levels
logger.debug(f"Processing {len(data)} records")  # Detailed debugging
logger.info(f"Starting ingestion for {symbol}")  # Operation start
logger.info(f"Successfully collected {len(data)} records")  # Success message
logger.warning(f"No data found for {symbol}, skipping")  # Recoverable issue
logger.error(f"Failed to ingest {symbol}: {e}", exc_info=True)  # Error with traceback
logger.critical(f"Database connection lost, aborting")  # Critical failure

# ❌ Bad: Wrong log levels
logger.error(f"Starting ingestion for {symbol}")  # Should be INFO
logger.info(f"Failed to connect to database: {e}")  # Should be ERROR
```

**Log Message Format:**
```python
# ✅ Good: Clear, contextual log messages
logger.info(
    f"Starting ingestion for {symbol} ({asset_type}) "
    f"from {start_date} to {end_date}"
)

logger.info(
    f"Completed ingestion for {symbol}: "
    f"{total_loaded} records loaded, status={result['status']}"
)

logger.error(
    f"Failed to ingest data for {symbol}: {e}",
    exc_info=True  # Include traceback for errors
)

# ❌ Bad: Vague or missing context
logger.info("Starting")
logger.error("Error occurred")
```

**Checklist:**
- [ ] DEBUG used only for detailed debugging information
- [ ] INFO used for operation status and success messages
- [ ] WARNING used for recoverable issues
- [ ] ERROR used for exceptions and failures
- [ ] CRITICAL used only for system-critical failures
- [ ] Log messages include relevant context (symbol, asset_type, etc.)
- [ ] `exc_info=True` used for error logging

### 4.3 Structured Logging

**Best Practices:**
- Include relevant context in log messages
- Use consistent message formats
- Log at appropriate points (start, end, errors)
- Include performance metrics when relevant

**Implementation:**
```python
# ✅ Good: Structured logging with context
start_time = time.time()
logger.info(f"Starting ingestion for {symbol} ({asset_type})")

try:
    # ... processing ...
    execution_time_ms = int((time.time() - start_time) * 1000)
    logger.info(
        f"Completed ingestion for {symbol}: "
        f"{records_loaded} records loaded in {execution_time_ms}ms"
    )
except Exception as e:
    execution_time_ms = int((time.time() - start_time) * 1000)
    logger.error(
        f"Failed to ingest {symbol} after {execution_time_ms}ms: {e}",
        exc_info=True
    )
```

**Checklist:**
- [ ] Log messages include relevant context
- [ ] Consistent message format across modules
- [ ] Performance metrics logged when relevant
- [ ] Start and end of operations logged
- [ ] Errors logged with full context

---

## 5. Testing Standards

### 5.1 Test Framework: pytest

**MANDATORY:** All code MUST have comprehensive test coverage using pytest.

**Test File Naming:**
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

**Test Structure:**
```python
# ✅ Good: Well-structured test
import pytest
from investment_platform.ingestion.ingestion_engine import IngestionEngine

class TestIngestionEngine:
    """Test suite for IngestionEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create IngestionEngine instance for testing."""
        return IngestionEngine(incremental=False)
    
    def test_ingest_success(self, engine):
        """Test successful data ingestion."""
        result = engine.ingest(
            symbol="AAPL",
            asset_type="stock",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        
        assert result["status"] == "success"
        assert result["records_loaded"] > 0
        assert result["asset_id"] is not None
    
    def test_ingest_invalid_symbol(self, engine):
        """Test ingestion with invalid symbol."""
        result = engine.ingest(
            symbol="INVALID",
            asset_type="stock",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        
        assert result["status"] == "failed"
        assert result["error_message"] is not None
```

**Checklist:**
- [ ] All test files follow naming convention (`test_*.py`)
- [ ] Test functions use descriptive names (`test_*`)
- [ ] Tests are organized into test classes when appropriate
- [ ] Fixtures used for common setup/teardown
- [ ] Tests are independent and can run in any order
- [ ] Test coverage is comprehensive (aim for >80%)

### 5.2 Test Coverage

**Coverage Requirements:**
- Aim for >80% code coverage
- Critical paths must have 100% coverage
- Error handling paths must be tested
- Edge cases must be tested

**Running Tests:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/investment_platform --cov-report=html

# Run specific test file
pytest tests/test_ingestion_engine.py

# Run specific test
pytest tests/test_ingestion_engine.py::TestIngestionEngine::test_ingest_success
```

**Test Categories:**
- **Unit Tests**: Test individual functions/methods in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows

**Implementation:**
```python
# Unit test example
def test_schema_mapper_map_to_market_data():
    """Test mapping to market_data format."""
    mapper = SchemaMapper()
    data = pd.DataFrame({
        'open': [100.0],
        'high': [105.0],
        'low': [99.0],
        'close': [103.0],
        'volume': [1000000],
    }, index=[pd.Timestamp('2024-01-01')])
    
    result = mapper.map_to_market_data(data, asset_id=1)
    
    assert 'time' in result.columns
    assert 'asset_id' in result.columns
    assert result['asset_id'].iloc[0] == 1
    assert len(result) == 1

# Integration test example
def test_ingestion_engine_end_to_end(db_connection):
    """Test complete ingestion workflow."""
    engine = IngestionEngine()
    result = engine.ingest(
        symbol="AAPL",
        asset_type="stock",
        start_date="2024-01-01",
        end_date="2024-01-31",
    )
    
    assert result["status"] == "success"
    
    # Verify data in database
    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM market_data WHERE asset_id = %s",
            (result["asset_id"],)
        )
        count = cursor.fetchone()[0]
        assert count > 0
```

**Checklist:**
- [ ] Unit tests for all public methods
- [ ] Integration tests for component interactions
- [ ] Error cases tested
- [ ] Edge cases tested
- [ ] Test coverage >80%
- [ ] Critical paths have 100% coverage

### 5.3 Test Fixtures

**Common Fixtures:**
- Database connections
- Test data
- Mock objects
- Configuration

**Implementation:**
```python
# ✅ Good: Reusable fixtures
import pytest
from investment_platform.ingestion.db_connection import get_db_connection

@pytest.fixture
def db_connection():
    """Provide database connection for testing."""
    conn = get_db_connection()
    yield conn
    conn.close()

@pytest.fixture
def sample_market_data():
    """Provide sample market data DataFrame."""
    return pd.DataFrame({
        'open': [100.0, 101.0],
        'high': [105.0, 106.0],
        'low': [99.0, 100.0],
        'close': [103.0, 104.0],
        'volume': [1000000, 1100000],
    }, index=[
        pd.Timestamp('2024-01-01'),
        pd.Timestamp('2024-01-02'),
    ])

@pytest.fixture
def mock_collector(monkeypatch):
    """Mock data collector for testing."""
    def mock_collect(symbol, start_date, end_date):
        return pd.DataFrame({
            'open': [100.0],
            'high': [105.0],
            'low': [99.0],
            'close': [103.0],
        }, index=[pd.Timestamp('2024-01-01')])
    
    monkeypatch.setattr(
        'investment_platform.collectors.StockCollector.collect_historical_data',
        mock_collect
    )
```

**Checklist:**
- [ ] Fixtures used for common setup/teardown
- [ ] Database fixtures properly clean up after tests
- [ ] Mock fixtures used for external dependencies
- [ ] Fixtures are reusable across test files
- [ ] Fixtures are properly scoped (function, class, module)

---

## 6. Database Patterns

### 6.1 Connection Management

**MANDATORY:** All database operations MUST use connection context managers.

**Implementation:**
```python
# ✅ Good: Context manager for connections
from investment_platform.ingestion.db_connection import get_db_connection

def load_data(self, data: pd.DataFrame, asset_type: str) -> int:
    """Load data into database."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO market_data (time, asset_id, open, high, low, close) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (time, asset_id, open, high, low, close)
            )
            conn.commit()
            return cursor.rowcount

# ❌ Bad: Manual connection management
def load_data(self, data: pd.DataFrame, asset_type: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(...)
    conn.commit()
    cursor.close()
    conn.close()  # Easy to forget!
```

**Transaction Management:**
```python
# ✅ Good: Explicit transaction management
with get_db_connection() as conn:
    try:
        with conn.cursor() as cursor:
            # Multiple operations
            cursor.execute("INSERT INTO ...")
            cursor.execute("UPDATE ...")
            conn.commit()  # Commit only if all succeed
    except Exception as e:
        conn.rollback()  # Rollback on error
        raise
```

**Checklist:**
- [ ] Context managers used for all database connections
- [ ] Transactions properly committed or rolled back
- [ ] Connections properly closed (automatic with context managers)
- [ ] Error handling includes rollback on failure

### 6.2 SQL Best Practices

**Parameterized Queries:**
- Always use parameterized queries to prevent SQL injection
- Never use string formatting for SQL queries
- Use `%s` placeholders for PostgreSQL

**Implementation:**
```python
# ✅ Good: Parameterized query
cursor.execute(
    "SELECT * FROM market_data WHERE asset_id = %s AND time >= %s",
    (asset_id, start_date)
)

# ❌ Bad: String formatting (SQL injection risk)
cursor.execute(
    f"SELECT * FROM market_data WHERE asset_id = {asset_id}"
)
```

**Bulk Operations:**
```python
# ✅ Good: Bulk insert using executemany or COPY
# Option 1: executemany for small batches
cursor.executemany(
    "INSERT INTO market_data (time, asset_id, open, high, low, close) "
    "VALUES (%s, %s, %s, %s, %s, %s)",
    [(row['time'], asset_id, row['open'], row['high'], row['low'], row['close'])
     for _, row in data.iterrows()]
)

# Option 2: COPY for large datasets (preferred for performance)
from io import StringIO
output = StringIO()
data.to_csv(output, sep='\t', header=False, index=False)
output.seek(0)
cursor.copy_from(output, 'market_data', columns=['time', 'asset_id', 'open', 'high', 'low', 'close'])
```

**Checklist:**
- [ ] All queries use parameterized placeholders
- [ ] No string formatting in SQL queries
- [ ] Bulk operations use executemany or COPY
- [ ] Queries are optimized (indexes used where appropriate)
- [ ] Connection pooling used for high-throughput scenarios

### 6.3 Data Validation

**Pre-Insert Validation:**
- Validate data types before insertion
- Check for required fields
- Validate data ranges where applicable
- Handle NULL values appropriately

**Implementation:**
```python
# ✅ Good: Data validation before insertion
def load_data(self, data: pd.DataFrame, asset_type: str) -> int:
    """Load data with validation."""
    # Validate required columns
    required_cols = ['time', 'asset_id', 'open', 'high', 'low', 'close']
    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        raise ValidationError(f"Missing required columns: {missing_cols}")
    
    # Validate data types
    if not pd.api.types.is_datetime64_any_dtype(data['time']):
        raise ValidationError("'time' column must be datetime type")
    
    # Validate data ranges
    if (data['high'] < data['low']).any():
        raise ValidationError("High values cannot be less than low values")
    
    # Handle NULLs
    data = data.dropna(subset=required_cols)
    
    # Proceed with insertion
    # ...
```

**Checklist:**
- [ ] Required columns validated before insertion
- [ ] Data types validated
- [ ] Data ranges validated where applicable
- [ ] NULL values handled appropriately
- [ ] Validation errors provide clear messages

---

## 7. Project Structure

### 7.1 Directory Layout

**Standard Structure:**
```
investment-platform/
├── src/
│   └── investment_platform/
│       ├── __init__.py
│       ├── collectors/          # Data collectors
│       ├── ingestion/           # Ingestion pipeline
│       └── api/                 # API endpoints (if applicable)
├── tests/                       # Test files
├── docs/                        # Documentation
├── scripts/                     # Utility scripts
├── requirements.txt             # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml               # Project configuration
└── README.md                    # Project documentation
```

**Module Organization:**
- One class per file (when possible)
- Related classes in same module
- Clear separation of concerns
- Logical grouping by functionality

**Checklist:**
- [ ] Follows standard project structure
- [ ] Modules organized by functionality
- [ ] Clear separation of concerns
- [ ] Easy to navigate and understand

### 7.2 Import Organization

**Import Order:**
1. Standard library imports
2. Third-party imports
3. Local application imports

**Implementation:**
```python
# ✅ Good: Organized imports
# Standard library
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Union

# Third-party
import pandas as pd

# Local application
from investment_platform.collectors import StockCollector
from investment_platform.ingestion.schema_mapper import SchemaMapper
from investment_platform.ingestion.data_loader import DataLoader

# ❌ Bad: Unorganized imports
import pandas as pd
import logging
from investment_platform.collectors import StockCollector
import time
from datetime import datetime
```

**Import Best Practices:**
- Use absolute imports (preferred)
- Avoid circular imports
- Import only what you need
- Group imports logically

**Checklist:**
- [ ] Imports organized (stdlib, third-party, local)
- [ ] Absolute imports used
- [ ] No circular imports
- [ ] Only necessary imports included

---

## 8. Dependency Management

### 8.1 Requirements Files

**File Structure:**
- `requirements.txt`: Production dependencies with versions
- `requirements-dev.txt`: Development dependencies
- `pyproject.toml`: Project metadata and tool configuration

**Version Pinning:**
- Pin major and minor versions (e.g., `pandas>=2.0.0,<3.0.0`)
- Use `>=` for minimum versions
- Update dependencies regularly for security patches

**Implementation:**
```txt
# requirements.txt
pandas>=2.0.0
psycopg2-binary>=2.9.0
yfinance>=0.2.0
requests>=2.31.0

# requirements-dev.txt
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
```

**Checklist:**
- [ ] Dependencies pinned with versions
- [ ] Production and development dependencies separated
- [ ] Dependencies regularly updated
- [ ] Security vulnerabilities addressed promptly

### 8.2 Virtual Environments

**MANDATORY:** All development MUST use virtual environments.

**Setup:**
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**Checklist:**
- [ ] Virtual environment used for all development
- [ ] Virtual environment activated before work
- [ ] Dependencies installed in virtual environment
- [ ] `.venv/` in `.gitignore`

---

## 9. Security Practices

### 9.1 Secrets Management

**MANDATORY:** Never commit secrets, API keys, or passwords to version control.

**Implementation:**
```python
# ✅ Good: Environment variables for secrets
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# ❌ Bad: Hardcoded secrets
API_KEY = "sk_live_1234567890abcdef"
DB_PASSWORD = "mypassword123"
```

**Environment Variables:**
- Use `.env` file for local development (in `.gitignore`)
- Use environment variables in production
- Never commit `.env` files
- Document required environment variables in README

**Checklist:**
- [ ] No secrets in code
- [ ] Environment variables used for configuration
- [ ] `.env` file in `.gitignore`
- [ ] Required environment variables documented

### 9.2 Input Validation

**MANDATORY:** All user inputs and external data MUST be validated.

**Implementation:**
```python
# ✅ Good: Input validation
def ingest(
    self,
    symbol: str,
    asset_type: str,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
) -> Dict[str, Any]:
    # Validate symbol
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol must be a non-empty string")
    
    # Validate asset_type
    valid_types = ["stock", "forex", "crypto", "bond", "commodity", "economic_indicator"]
    if asset_type not in valid_types:
        raise ValidationError(f"Invalid asset_type: {asset_type}. Must be one of {valid_types}")
    
    # Validate dates
    if isinstance(start_date, str):
        try:
            start_date = datetime.fromisoformat(start_date)
        except ValueError:
            raise ValidationError(f"Invalid start_date format: {start_date}")
    
    # Validate date range
    if start_date >= end_date:
        raise ValidationError("start_date must be before end_date")
    
    # Proceed with processing
    # ...
```

**Checklist:**
- [ ] All inputs validated
- [ ] Type checking performed
- [ ] Range validation where applicable
- [ ] SQL injection prevented (parameterized queries)
- [ ] Clear error messages for validation failures

---

## 10. Performance Considerations

### 10.1 Database Performance

**Optimization Strategies:**
- Use bulk operations (COPY, executemany) for large datasets
- Use appropriate indexes
- Avoid N+1 query problems
- Use connection pooling for high-throughput scenarios

**Implementation:**
```python
# ✅ Good: Bulk insert with COPY
def load_data_bulk(self, data: pd.DataFrame, table: str) -> int:
    """Load data using PostgreSQL COPY for performance."""
    from io import StringIO
    
    output = StringIO()
    data.to_csv(output, sep='\t', header=False, index=False)
    output.seek(0)
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.copy_from(
                output,
                table,
                columns=data.columns.tolist()
            )
            conn.commit()
            return len(data)

# ❌ Bad: Row-by-row insert
def load_data_slow(self, data: pd.DataFrame, table: str) -> int:
    """Slow row-by-row insert."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            for _, row in data.iterrows():
                cursor.execute(
                    f"INSERT INTO {table} VALUES (...)",
                    (row['col1'], row['col2'], ...)
                )
            conn.commit()
```

**Checklist:**
- [ ] Bulk operations used for large datasets
- [ ] Appropriate indexes created
- [ ] N+1 query problems avoided
- [ ] Connection pooling used when needed
- [ ] Query performance monitored

### 10.2 Data Processing Performance

**Pandas Best Practices:**
- Use vectorized operations
- Avoid iterating over DataFrames
- Use appropriate data types
- Process data in chunks for large datasets

**Implementation:**
```python
# ✅ Good: Vectorized operations
def process_data(data: pd.DataFrame) -> pd.DataFrame:
    """Process data using vectorized operations."""
    # Vectorized calculation
    data['returns'] = data['close'].pct_change()
    data['volatility'] = data['returns'].rolling(window=20).std()
    
    # Vectorized filtering
    filtered = data[data['volume'] > 1000000]
    
    return filtered

# ❌ Bad: Row-by-row iteration
def process_data_slow(data: pd.DataFrame) -> pd.DataFrame:
    """Slow row-by-row processing."""
    for idx, row in data.iterrows():
        data.loc[idx, 'returns'] = (row['close'] - data.loc[idx-1, 'close']) / data.loc[idx-1, 'close']
    return data
```

**Checklist:**
- [ ] Vectorized operations used
- [ ] DataFrame iteration avoided
- [ ] Appropriate data types used
- [ ] Chunking used for large datasets
- [ ] Performance bottlenecks identified and optimized

---

## 11. Code Review Checklist

### Before Submitting Code

**Code Quality:**
- [ ] Code formatted with Black
- [ ] Code passes Flake8 linting
- [ ] Code passes mypy type checking
- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] No hardcoded secrets or credentials

**Testing:**
- [ ] Tests written for new functionality
- [ ] Tests pass locally
- [ ] Test coverage >80%
- [ ] Edge cases tested
- [ ] Error cases tested

**Error Handling:**
- [ ] Appropriate exception types used
- [ ] Exceptions logged with context
- [ ] Error messages are clear and actionable
- [ ] Error handling tested

**Database:**
- [ ] Parameterized queries used
- [ ] Transactions properly managed
- [ ] Connection context managers used
- [ ] Data validation performed

**Documentation:**
- [ ] Docstrings complete and accurate
- [ ] README updated if needed
- [ ] Complex logic documented
- [ ] API changes documented

**Performance:**
- [ ] Bulk operations used where appropriate
- [ ] No obvious performance bottlenecks
- [ ] Database queries optimized

---

## 12. Quick Reference

### Common Commands

```bash
# Format code
black .

# Lint code
flake8 src/ tests/

# Type check
mypy src/

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/investment_platform --cov-report=html

# Run specific test
pytest tests/test_ingestion_engine.py::TestIngestionEngine::test_ingest_success
```

### Code Templates

**Class Template:**
```python
"""Module docstring."""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MyClass:
    """
    Class docstring.
    
    Attributes:
        attribute1: Description of attribute1
        attribute2: Description of attribute2
    """
    
    def __init__(self, param1: str, param2: Optional[int] = None) -> None:
        """
        Initialize MyClass.
        
        Args:
            param1: Description of param1
            param2: Description of param2
        """
        self.attribute1 = param1
        self.attribute2 = param2
        self.logger = logger
    
    def method(self, param: str) -> Dict[str, Any]:
        """
        Method description.
        
        Args:
            param: Parameter description
            
        Returns:
            Dictionary with results
            
        Raises:
            ValueError: If param is invalid
        """
        if not param:
            raise ValueError("param cannot be empty")
        
        self.logger.info(f"Processing {param}")
        return {"result": "success"}
```

**Function Template:**
```python
def function_name(
    param1: str,
    param2: Optional[int] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Function description.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        **kwargs: Additional keyword arguments
        
    Returns:
        Dictionary with results
        
    Raises:
        ValueError: If parameters are invalid
    """
    logger.info(f"Starting function_name with param1={param1}")
    
    try:
        # Function logic
        result = {"status": "success"}
        logger.info("Function completed successfully")
        return result
    except Exception as e:
        logger.error(f"Function failed: {e}", exc_info=True)
        raise
```

---

## Resources

### External Resources
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [PEP 484 Type Hints](https://peps.python.org/pep-0484/)
- [Black Documentation](https://black.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Pandas Best Practices](https://pandas.pydata.org/docs/user_guide/best_practices.html)

### Internal Resources
- [Python Developer Role](../roles/python-developer.md)
- [Data Engineer Role](../roles/data-engineer.md)
- [Project README](../README.md)

---

**Last Updated:** 2024
**Version:** 1.0
**Maintained By:** Development Team

