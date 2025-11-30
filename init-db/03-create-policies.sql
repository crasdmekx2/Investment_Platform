-- ============================================================================
-- Investment Platform TimescaleDB Policies
-- ============================================================================
-- This script creates TimescaleDB compression and retention policies for
-- optimal storage and performance.
--
-- Execution order:
--   1. 02-create-schema.sql (creates tables and hypertables)
--   2. 04-create-functions.sql (creates functions)
--   3. This file (03-create-policies.sql) - creates policies
-- ============================================================================

-- ============================================================================
-- COMPRESSION POLICIES
-- ============================================================================
-- Compression policies automatically compress chunks older than 30 days,
-- reducing storage costs by approximately 90% while maintaining query performance.
-- Compression order is optimized for time-series queries (time DESC, asset_id).
-- ============================================================================

-- Enable compression on market_data hypertable
ALTER TABLE market_data SET (timescaledb.compress = true);

-- Set compression order for market_data (optimized for time-series queries)
ALTER TABLE market_data SET (
    timescaledb.compress_orderby = 'time DESC',
    timescaledb.compress_segmentby = 'asset_id'
);

-- Add compression policy: compress chunks older than 30 days
SELECT add_compression_policy('market_data', 
    INTERVAL '30 days',
    if_not_exists => TRUE
);

-- Enable compression on forex_rates hypertable
ALTER TABLE forex_rates SET (timescaledb.compress = true);

-- Set compression order for forex_rates
ALTER TABLE forex_rates SET (
    timescaledb.compress_orderby = 'time DESC',
    timescaledb.compress_segmentby = 'asset_id'
);

-- Add compression policy: compress chunks older than 30 days
SELECT add_compression_policy('forex_rates',
    INTERVAL '30 days',
    if_not_exists => TRUE
);

-- Enable compression on bond_rates hypertable
ALTER TABLE bond_rates SET (timescaledb.compress = true);

-- Set compression order for bond_rates
ALTER TABLE bond_rates SET (
    timescaledb.compress_orderby = 'time DESC',
    timescaledb.compress_segmentby = 'asset_id'
);

-- Add compression policy: compress chunks older than 30 days
SELECT add_compression_policy('bond_rates',
    INTERVAL '30 days',
    if_not_exists => TRUE
);

-- Enable compression on economic_data hypertable
ALTER TABLE economic_data SET (timescaledb.compress = true);

-- Set compression order for economic_data
ALTER TABLE economic_data SET (
    timescaledb.compress_orderby = 'time DESC',
    timescaledb.compress_segmentby = 'asset_id'
);

-- Add compression policy: compress chunks older than 30 days
SELECT add_compression_policy('economic_data',
    INTERVAL '30 days',
    if_not_exists => TRUE
);

-- ============================================================================
-- RETENTION POLICIES (OPTIONAL - COMMENTED OUT)
-- ============================================================================
-- Retention policies automatically drop data older than the specified interval.
-- These are commented out by default. Uncomment and adjust intervals as needed
-- based on your data retention requirements.
--
-- WARNING: Once data is dropped, it cannot be recovered. Use with caution.
-- ============================================================================

-- Example retention policy for market_data (uncomment to enable):
-- Drops data older than 10 years
-- SELECT add_retention_policy('market_data', INTERVAL '10 years', if_not_exists => TRUE);

-- Example retention policy for forex_rates (uncomment to enable):
-- Drops data older than 10 years
-- SELECT add_retention_policy('forex_rates', INTERVAL '10 years', if_not_exists => TRUE);

-- Example retention policy for bond_rates (uncomment to enable):
-- Drops data older than 10 years
-- SELECT add_retention_policy('bond_rates', INTERVAL '10 years', if_not_exists => TRUE);

-- Example retention policy for economic_data (uncomment to enable):
-- Drops data older than 10 years
-- SELECT add_retention_policy('economic_data', INTERVAL '10 years', if_not_exists => TRUE);

-- ============================================================================
-- CONTINUOUS AGGREGATES (OPTIONAL - FOR FUTURE USE)
-- ============================================================================
-- Continuous aggregates pre-compute common aggregations for improved query
-- performance. Uncomment and customize as needed based on query patterns.
-- ============================================================================

-- Example: Daily aggregated market data (uncomment to enable):
-- CREATE MATERIALIZED VIEW IF NOT EXISTS market_data_daily
-- WITH (timescaledb.continuous) AS
-- SELECT 
--     time_bucket('1 day', time) AS bucket,
--     asset_id,
--     FIRST(open, time) AS open,
--     MAX(high) AS high,
--     MIN(low) AS low,
--     LAST(close, time) AS close,
--     SUM(volume) AS volume
-- FROM market_data
-- GROUP BY bucket, asset_id;
--
-- -- Add refresh policy for continuous aggregate (refreshes every hour):
-- SELECT add_continuous_aggregate_policy('market_data_daily',
--     start_offset => INTERVAL '3 days',
--     end_offset => INTERVAL '1 hour',
--     schedule_interval => INTERVAL '1 hour',
--     if_not_exists => TRUE
-- );

-- ============================================================================
-- POLICY MANAGEMENT FUNCTIONS
-- ============================================================================
-- Helper queries to view and manage policies:
--
-- View all compression policies:
--   SELECT * FROM timescaledb_information.jobs WHERE proc_name = 'policy_compression';
--
-- View all retention policies:
--   SELECT * FROM timescaledb_information.jobs WHERE proc_name = 'policy_retention';
--
-- Remove a compression policy:
--   SELECT remove_compression_policy('table_name', if_exists => TRUE);
--
-- Remove a retention policy:
--   SELECT remove_retention_policy('table_name', if_exists => TRUE);
-- ============================================================================

-- ============================================================================
-- END OF POLICIES
-- ============================================================================

