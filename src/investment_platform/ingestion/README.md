# Data Ingestion Module

This module provides a complete data ingestion pipeline for the Investment Platform, connecting collectors to the TimescaleDB database.

## Features

- **Batch and Incremental Ingestion**: Automatically detects existing data and only fetches missing ranges
- **Multi-Asset Support**: Handles stocks, forex, crypto, bonds, commodities, and economic indicators
- **Automated Scheduling**: Schedule regular data collection runs with flexible cron/interval patterns
- **Data Validation**: Validates schema, constraints, and data quality before insertion
- **Error Handling**: Comprehensive error handling with retries and logging
- **Observability**: Logs all collection runs to `data_collection_log` table
- **Performance**: Bulk inserts using PostgreSQL COPY for efficiency

## Quick Start

### Ingest Data for a Single Asset

```python
from investment_platform.ingestion import IngestionEngine
from datetime import datetime, timedelta

engine = IngestionEngine(incremental=True)

result = engine.ingest(
    symbol="AAPL",
    asset_type="stock",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
)

print(f"Status: {result['status']}")
print(f"Records loaded: {result['records_loaded']}")
```

### Using the CLI

```bash
# Ingest stock data
python scripts/run_ingestion.py ingest AAPL stock --start-date 2024-01-01 --end-date 2024-01-31

# Ingest with batch mode (ignore existing data)
python scripts/run_ingestion.py ingest BTC-USD crypto --batch

# Schedule automated ingestion
python scripts/run_scheduler.py --config config/scheduler_config.yaml
```

## Architecture

### Core Components

1. **IngestionEngine**: Main orchestrator that coordinates collection and loading
2. **AssetManager**: Handles asset registration and metadata management
3. **SchemaMapper**: Maps collector output to database schema format
4. **IncrementalTracker**: Determines existing data ranges for incremental updates
5. **DataLoader**: Loads time-series data into database tables
6. **IngestionScheduler**: Automated scheduling for regular data collection

### Data Flow

1. Initialize collector based on asset type
2. Check/register asset in `assets` table (get or create `asset_id`)
3. If incremental mode: query existing data ranges, calculate gaps
4. Collect data using collector (with date range)
5. Transform and validate collected data
6. Bulk insert into appropriate time-series table
7. Log collection run to `data_collection_log` table

### Asset Type Mapping

- **Stocks** → `market_data` table (OHLCV + dividends, stock_splits)
- **Crypto** → `market_data` table (OHLCV)
- **Commodities** → `market_data` table (OHLCV)
- **Forex** → `forex_rates` table (rate)
- **Bonds** → `bond_rates` table (rate)
- **Economic Indicators** → `economic_data` table (value)

## Usage Examples

### Programmatic Usage

```python
from investment_platform.ingestion import IngestionEngine
from datetime import datetime, timedelta

# Create engine with incremental mode
engine = IngestionEngine(
    incremental=True,      # Only fetch missing data
    on_conflict="do_nothing",  # Skip duplicates
    use_copy=True,          # Use PostgreSQL COPY for performance
)

# Ingest stock data
result = engine.ingest(
    symbol="AAPL",
    asset_type="stock",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
)

# Ingest forex data
result = engine.ingest(
    symbol="USD_EUR",
    asset_type="forex",
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now(),
)
```

### Scheduling

```python
from investment_platform.ingestion import IngestionScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = IngestionScheduler(blocking=True)

# Add daily job at 9 AM
scheduler.add_cron_job(
    symbol="AAPL",
    asset_type="stock",
    hour="9",
    minute="0",
)

# Add hourly job
scheduler.add_interval_job(
    symbol="BTC-USD",
    asset_type="crypto",
    hours=1,
)

# Start scheduler
scheduler.start()
```

### Configuration File

See `config/scheduler_config.yaml.example` for an example scheduler configuration file.

## Database Tables

The ingestion system integrates with the following database tables:

- **assets**: Asset registration and metadata management
- **market_data**: OHLCV data for stocks, crypto, commodities
- **forex_rates**: Exchange rate data
- **bond_rates**: Bond yield data
- **economic_data**: Economic indicator values
- **data_collection_log**: Collection run tracking and observability

## Error Handling

The ingestion system includes comprehensive error handling:

- Validates collector output matches expected schema
- Checks database constraints before insertion
- Handles duplicate key errors gracefully (upsert logic)
- Retry logic for transient failures
- Comprehensive logging at each stage
- Tracks partial failures in `data_collection_log`

## Performance Considerations

- Uses PostgreSQL COPY for bulk inserts (much faster than individual INSERTs)
- Supports connection pooling for concurrent operations
- Incremental mode avoids redundant data collection
- Bulk operations minimize database round trips

## Environment Variables

The ingestion system uses the following environment variables for database connection:

- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: investment_platform)
- `DB_USER`: Database user (default: postgres)
- `DB_PASSWORD`: Database password (default: postgres)

## Dependencies

- `psycopg2-binary`: PostgreSQL database connectivity
- `pandas`: Data processing
- `apscheduler`: Scheduling (optional, for scheduler functionality)
- `pyyaml`: YAML config parsing (optional, for YAML config files)

