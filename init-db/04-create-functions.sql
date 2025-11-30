-- ============================================================================
-- Investment Platform Database Functions
-- ============================================================================
-- This script creates helper functions for the Investment Platform database,
-- including trigger functions and utility functions.
--
-- Execution order:
--   1. 02-create-schema.sql (creates tables)
--   2. This file (04-create-functions.sql) - creates functions
--   3. 03-create-policies.sql (for TimescaleDB policies)
-- ============================================================================

-- ============================================================================
-- TRIGGER FUNCTIONS
-- ============================================================================

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_updated_at_column() IS 'Trigger function to automatically update the updated_at timestamp when a row is modified';

-- Create trigger for assets table to update updated_at
DROP TRIGGER IF EXISTS update_assets_updated_at ON assets;
CREATE TRIGGER update_assets_updated_at
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function to get asset information by symbol
CREATE OR REPLACE FUNCTION get_asset_by_symbol(p_symbol VARCHAR)
RETURNS TABLE (
    asset_id INTEGER,
    symbol VARCHAR,
    asset_type VARCHAR,
    name VARCHAR,
    exchange VARCHAR,
    currency VARCHAR,
    source VARCHAR,
    is_active BOOLEAN,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.asset_id,
        a.symbol,
        a.asset_type,
        a.name,
        a.exchange,
        a.currency,
        a.source,
        a.is_active,
        a.created_at
    FROM assets a
    WHERE a.symbol = p_symbol
      AND a.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_asset_by_symbol(VARCHAR) IS 'Retrieves asset information by symbol (only active assets)';

-- Function to get latest data point for an asset
CREATE OR REPLACE FUNCTION get_latest_market_data(p_asset_id INTEGER)
RETURNS TABLE (
    "time" TIMESTAMPTZ,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        md.time,
        md.open,
        md.high,
        md.low,
        md.close,
        md.volume
    FROM market_data md
    WHERE md.asset_id = p_asset_id
    ORDER BY md.time DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_latest_market_data(INTEGER) IS 'Retrieves the most recent market data point for a given asset';

-- Function to check data freshness for an asset
CREATE OR REPLACE FUNCTION check_data_freshness(
    p_asset_id INTEGER,
    p_data_type VARCHAR DEFAULT 'market_data'
)
RETURNS TABLE (
    asset_id INTEGER,
    data_type VARCHAR,
    latest_time TIMESTAMPTZ,
    hours_old NUMERIC,
    is_stale BOOLEAN
) AS $$
DECLARE
    v_latest_time TIMESTAMPTZ;
    v_hours_old NUMERIC;
BEGIN
    -- Get latest timestamp based on data type
    CASE p_data_type
        WHEN 'market_data' THEN
            SELECT MAX(md.time) INTO v_latest_time FROM market_data md WHERE md.asset_id = p_asset_id;
        WHEN 'forex_rates' THEN
            SELECT MAX(fr.time) INTO v_latest_time FROM forex_rates fr WHERE fr.asset_id = p_asset_id;
        WHEN 'bond_rates' THEN
            SELECT MAX(br.time) INTO v_latest_time FROM bond_rates br WHERE br.asset_id = p_asset_id;
        WHEN 'economic_data' THEN
            SELECT MAX(ed.time) INTO v_latest_time FROM economic_data ed WHERE ed.asset_id = p_asset_id;
        ELSE
            RAISE EXCEPTION 'Invalid data_type: %. Must be one of: market_data, forex_rates, bond_rates, economic_data', p_data_type;
    END CASE;
    
    -- Calculate hours old
    IF v_latest_time IS NOT NULL THEN
        v_hours_old := EXTRACT(EPOCH FROM (NOW() - v_latest_time)) / 3600;
    ELSE
        v_hours_old := NULL;
    END IF;
    
    -- Return result
    RETURN QUERY
    SELECT 
        p_asset_id,
        p_data_type,
        v_latest_time,
        v_hours_old,
        CASE 
            WHEN v_hours_old IS NULL THEN TRUE
            WHEN v_hours_old > 24 THEN TRUE  -- Consider stale if older than 24 hours
            ELSE FALSE
        END AS is_stale;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_data_freshness(INTEGER, VARCHAR) IS 'Checks data freshness for an asset by calculating hours since last data point. Returns is_stale=TRUE if data is older than 24 hours or missing.';

-- Function to get collection statistics
CREATE OR REPLACE FUNCTION get_collection_stats(
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    collector_type VARCHAR,
    total_runs BIGINT,
    successful_runs BIGINT,
    failed_runs BIGINT,
    partial_runs BIGINT,
    avg_execution_time_ms NUMERIC,
    total_records_collected BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dcl.collector_type,
        COUNT(*)::BIGINT AS total_runs,
        COUNT(*) FILTER (WHERE dcl.status = 'success')::BIGINT AS successful_runs,
        COUNT(*) FILTER (WHERE dcl.status = 'failed')::BIGINT AS failed_runs,
        COUNT(*) FILTER (WHERE dcl.status = 'partial')::BIGINT AS partial_runs,
        AVG(dcl.execution_time_ms) AS avg_execution_time_ms,
        SUM(dcl.records_collected)::BIGINT AS total_records_collected
    FROM data_collection_log dcl
    WHERE dcl.created_at >= NOW() - (p_days || ' days')::INTERVAL
    GROUP BY dcl.collector_type
    ORDER BY dcl.collector_type;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_collection_stats(INTEGER) IS 'Returns collection statistics for the specified number of days, grouped by collector type';

-- ============================================================================
-- END OF FUNCTIONS
-- ============================================================================

