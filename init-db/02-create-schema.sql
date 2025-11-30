-- ============================================================================
-- Investment Platform Database Schema
-- ============================================================================
-- This script creates the complete database schema for the Investment Platform,
-- including tables, constraints, TimescaleDB hypertables, indexes, and triggers.
--
-- Execution order:
--   1. This file (02-create-schema.sql)
--   2. 04-create-functions.sql (for trigger functions)
--   3. 03-create-policies.sql (for TimescaleDB policies)
-- ============================================================================

-- ============================================================================
-- 1. ASSET METADATA TABLES
-- ============================================================================

-- Assets table: Central table storing metadata for all asset types
CREATE TABLE IF NOT EXISTS assets (
    asset_id SERIAL PRIMARY KEY,
    symbol VARCHAR(100) NOT NULL UNIQUE,
    asset_type VARCHAR(50) NOT NULL CHECK (asset_type IN ('stock', 'forex', 'crypto', 'bond', 'commodity', 'economic_indicator')),
    name VARCHAR(255) NOT NULL,
    exchange VARCHAR(100),
    currency VARCHAR(10),  -- ISO currency code
    sector VARCHAR(100),  -- For stocks
    industry VARCHAR(100),  -- For stocks
    base_currency VARCHAR(10),  -- For forex/crypto
    quote_currency VARCHAR(10),  -- For forex/crypto
    series_id VARCHAR(50),  -- For bonds/economic indicators (FRED series ID)
    security_type VARCHAR(50),  -- For bonds
    source VARCHAR(100) NOT NULL,  -- Data source (e.g., 'Yahoo Finance', 'FRED', 'Coinbase')
    metadata JSONB,  -- Flexible storage for additional fields
    is_active BOOLEAN DEFAULT TRUE,  -- Soft delete flag
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add table comment
COMMENT ON TABLE assets IS 'Central table storing metadata for all asset types (stocks, forex, crypto, bonds, commodities, economic indicators)';

-- Add column comments
COMMENT ON COLUMN assets.asset_id IS 'Primary key, auto-incrementing integer';
COMMENT ON COLUMN assets.symbol IS 'Asset identifier (e.g., ticker symbol, currency pair, series ID)';
COMMENT ON COLUMN assets.asset_type IS 'Type of asset: stock, forex, crypto, bond, commodity, or economic_indicator';
COMMENT ON COLUMN assets.name IS 'Human-readable name of the asset';
COMMENT ON COLUMN assets.exchange IS 'Exchange where the asset is traded (for stocks, crypto)';
COMMENT ON COLUMN assets.currency IS 'ISO currency code (e.g., USD, EUR)';
COMMENT ON COLUMN assets.sector IS 'Business sector (for stocks)';
COMMENT ON COLUMN assets.industry IS 'Industry classification (for stocks)';
COMMENT ON COLUMN assets.base_currency IS 'Base currency in pair (for forex/crypto)';
COMMENT ON COLUMN assets.quote_currency IS 'Quote currency in pair (for forex/crypto)';
COMMENT ON COLUMN assets.series_id IS 'FRED series ID (for bonds/economic indicators)';
COMMENT ON COLUMN assets.security_type IS 'Type of security (for bonds, e.g., TBILLS, TNOTES)';
COMMENT ON COLUMN assets.source IS 'Data source provider (e.g., Yahoo Finance, FRED, Coinbase)';
COMMENT ON COLUMN assets.metadata IS 'Flexible JSONB storage for additional asset metadata';
COMMENT ON COLUMN assets.is_active IS 'Soft delete flag - set to FALSE to deactivate without deleting';
COMMENT ON COLUMN assets.created_at IS 'Timestamp when record was created';
COMMENT ON COLUMN assets.updated_at IS 'Timestamp when record was last updated';

-- Create indexes for assets table
CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets(symbol);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_assets_type_symbol ON assets(asset_type, symbol);
CREATE INDEX IF NOT EXISTS idx_assets_active ON assets(is_active, asset_type);

-- ============================================================================
-- 2. TIME-SERIES DATA TABLES
-- ============================================================================

-- Market Data table: OHLCV data for stocks, crypto, commodities
CREATE TABLE IF NOT EXISTS market_data (
    time TIMESTAMPTZ NOT NULL,
    asset_id INTEGER NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    open NUMERIC(20, 8) NOT NULL,
    high NUMERIC(20, 8) NOT NULL,
    low NUMERIC(20, 8) NOT NULL,
    close NUMERIC(20, 8) NOT NULL,
    volume BIGINT CHECK (volume >= 0),
    dividends NUMERIC(20, 8) CHECK (dividends >= 0),  -- For stocks
    stock_splits NUMERIC(20, 8) CHECK (stock_splits >= 0),  -- For stocks
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT market_data_pkey PRIMARY KEY (asset_id, time),
    CONSTRAINT market_data_ohlc_check CHECK (
        high >= low AND
        high >= open AND
        high >= close AND
        low <= open AND
        low <= close
    )
);

-- Add table comment
COMMENT ON TABLE market_data IS 'OHLCV (Open, High, Low, Close, Volume) time-series data for stocks, cryptocurrencies, and commodities';

-- Add column comments
COMMENT ON COLUMN market_data.time IS 'Timestamp of the data point (partition key for TimescaleDB)';
COMMENT ON COLUMN market_data.asset_id IS 'Foreign key to assets table';
COMMENT ON COLUMN market_data.open IS 'Opening price';
COMMENT ON COLUMN market_data.high IS 'Highest price during the period';
COMMENT ON COLUMN market_data.low IS 'Lowest price during the period';
COMMENT ON COLUMN market_data.close IS 'Closing price';
COMMENT ON COLUMN market_data.volume IS 'Trading volume';
COMMENT ON COLUMN market_data.dividends IS 'Dividend amount (for stocks)';
COMMENT ON COLUMN market_data.stock_splits IS 'Stock split ratio (for stocks)';
COMMENT ON COLUMN market_data.created_at IS 'Timestamp when record was inserted';

-- Create indexes for market_data table (before converting to hypertable)
CREATE INDEX IF NOT EXISTS idx_market_data_asset_time ON market_data(asset_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_market_data_time ON market_data(time DESC);
CREATE INDEX IF NOT EXISTS idx_market_data_asset_id ON market_data(asset_id);

-- Convert market_data to TimescaleDB hypertable
SELECT create_hypertable('market_data', 'time', 
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Forex Rates table: Exchange rate data for currency pairs
CREATE TABLE IF NOT EXISTS forex_rates (
    time TIMESTAMPTZ NOT NULL,
    asset_id INTEGER NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    rate NUMERIC(20, 8) NOT NULL CHECK (rate > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT forex_rates_pkey PRIMARY KEY (asset_id, time)
);

-- Add table comment
COMMENT ON TABLE forex_rates IS 'Foreign exchange rate time-series data for currency pairs';

-- Add column comments
COMMENT ON COLUMN forex_rates.time IS 'Timestamp of the exchange rate (partition key for TimescaleDB)';
COMMENT ON COLUMN forex_rates.asset_id IS 'Foreign key to assets table';
COMMENT ON COLUMN forex_rates.rate IS 'Exchange rate (base_currency / quote_currency)';
COMMENT ON COLUMN forex_rates.created_at IS 'Timestamp when record was inserted';

-- Create indexes for forex_rates table
CREATE INDEX IF NOT EXISTS idx_forex_rates_asset_time ON forex_rates(asset_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_forex_rates_time ON forex_rates(time DESC);

-- Convert forex_rates to TimescaleDB hypertable
SELECT create_hypertable('forex_rates', 'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Bond Rates table: Treasury bond yield/rate data
CREATE TABLE IF NOT EXISTS bond_rates (
    time TIMESTAMPTZ NOT NULL,
    asset_id INTEGER NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    rate NUMERIC(20, 8) NOT NULL,  -- Can be negative in some markets
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT bond_rates_pkey PRIMARY KEY (asset_id, time)
);

-- Add table comment
COMMENT ON TABLE bond_rates IS 'Treasury bond yield and rate time-series data from FRED API';

-- Add column comments
COMMENT ON COLUMN bond_rates.time IS 'Timestamp of the rate data (partition key for TimescaleDB)';
COMMENT ON COLUMN bond_rates.asset_id IS 'Foreign key to assets table';
COMMENT ON COLUMN bond_rates.rate IS 'Bond yield or interest rate (can be negative in some markets, no constraint applied)';
COMMENT ON COLUMN bond_rates.created_at IS 'Timestamp when record was inserted';

-- Create indexes for bond_rates table
CREATE INDEX IF NOT EXISTS idx_bond_rates_asset_time ON bond_rates(asset_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_bond_rates_time ON bond_rates(time DESC);

-- Convert bond_rates to TimescaleDB hypertable
SELECT create_hypertable('bond_rates', 'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Economic Data table: Economic indicator data from FRED
CREATE TABLE IF NOT EXISTS economic_data (
    time TIMESTAMPTZ NOT NULL,
    asset_id INTEGER NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    value NUMERIC(20, 8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT economic_data_pkey PRIMARY KEY (asset_id, time)
);

-- Add table comment
COMMENT ON TABLE economic_data IS 'Economic indicator time-series data from FRED API (GDP, unemployment, inflation, etc.)';

-- Add column comments
COMMENT ON COLUMN economic_data.time IS 'Timestamp of the economic indicator value (partition key for TimescaleDB)';
COMMENT ON COLUMN economic_data.asset_id IS 'Foreign key to assets table';
COMMENT ON COLUMN economic_data.value IS 'Economic indicator value';
COMMENT ON COLUMN economic_data.created_at IS 'Timestamp when record was inserted';

-- Create indexes for economic_data table
CREATE INDEX IF NOT EXISTS idx_economic_data_asset_time ON economic_data(asset_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_economic_data_time ON economic_data(time DESC);

-- Convert economic_data to TimescaleDB hypertable
SELECT create_hypertable('economic_data', 'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- ============================================================================
-- 3. DATA COLLECTION TRACKING & OBSERVABILITY
-- ============================================================================

-- Data Collection Log table: Track data collection runs for observability
CREATE TABLE IF NOT EXISTS data_collection_log (
    log_id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    collector_type VARCHAR(100) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    records_collected INTEGER NOT NULL DEFAULT 0 CHECK (records_collected >= 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failed', 'partial')),
    error_message TEXT,
    execution_time_ms INTEGER,  -- Performance tracking
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT data_collection_log_date_check CHECK (end_date >= start_date)
);

-- Add table comment
COMMENT ON TABLE data_collection_log IS 'Tracks all data collection runs for observability, monitoring, and debugging';

-- Add column comments
COMMENT ON COLUMN data_collection_log.log_id IS 'Primary key, auto-incrementing integer';
COMMENT ON COLUMN data_collection_log.asset_id IS 'Foreign key to assets table';
COMMENT ON COLUMN data_collection_log.collector_type IS 'Collector class name (e.g., StockCollector, ForexCollector)';
COMMENT ON COLUMN data_collection_log.start_date IS 'Start date of the data collection period';
COMMENT ON COLUMN data_collection_log.end_date IS 'End date of the data collection period';
COMMENT ON COLUMN data_collection_log.records_collected IS 'Number of records successfully collected';
COMMENT ON COLUMN data_collection_log.status IS 'Collection status: success, failed, or partial';
COMMENT ON COLUMN data_collection_log.error_message IS 'Error message if collection failed';
COMMENT ON COLUMN data_collection_log.execution_time_ms IS 'Execution time in milliseconds for performance monitoring';
COMMENT ON COLUMN data_collection_log.created_at IS 'Timestamp when log entry was created';

-- Create indexes for data_collection_log table
CREATE INDEX IF NOT EXISTS idx_collection_log_asset ON data_collection_log(asset_id);
CREATE INDEX IF NOT EXISTS idx_collection_log_created ON data_collection_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_collection_log_status ON data_collection_log(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_collection_log_asset_status ON data_collection_log(asset_id, status, created_at DESC);

-- ============================================================================
-- END OF SCHEMA CREATION
-- ============================================================================

