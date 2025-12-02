-- ============================================================================
-- Active Collection Jobs Table
-- ============================================================================
-- This script creates a table for tracking active/immediate collection jobs
-- triggered via the /api/ingestion/collect endpoint.
--
-- This replaces the in-memory storage to enable:
-- - Persistence across server restarts
-- - Scalability across multiple instances
-- - Better observability and debugging
--
-- Execution order:
--   1. 02-create-schema.sql (base schema)
--   2. 07-active-collection-jobs.sql (this file)
-- ============================================================================

-- Active Collection Jobs table: Track immediate collection jobs
CREATE TABLE IF NOT EXISTS active_collection_jobs (
    job_id VARCHAR(255) PRIMARY KEY,
    symbol VARCHAR(100) NOT NULL,
    asset_type VARCHAR(50) NOT NULL CHECK (asset_type IN ('stock', 'forex', 'crypto', 'bond', 'commodity', 'economic_indicator')),
    status VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    request_data JSONB,  -- Store full CollectRequest for reference
    result_data JSONB,  -- Store collection result when completed
    error_message TEXT,  -- Store error message if failed
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add table comment
COMMENT ON TABLE active_collection_jobs IS 'Tracks active/immediate collection jobs triggered via /api/ingestion/collect endpoint. Replaces in-memory storage for persistence and scalability.';

-- Add column comments
COMMENT ON COLUMN active_collection_jobs.job_id IS 'Primary key, unique job identifier (format: collect_<uuid>)';
COMMENT ON COLUMN active_collection_jobs.symbol IS 'Asset symbol being collected';
COMMENT ON COLUMN active_collection_jobs.asset_type IS 'Type of asset being collected';
COMMENT ON COLUMN active_collection_jobs.status IS 'Current job status: running, completed, failed';
COMMENT ON COLUMN active_collection_jobs.request_data IS 'Full CollectRequest data stored as JSONB';
COMMENT ON COLUMN active_collection_jobs.result_data IS 'Collection result stored as JSONB when completed';
COMMENT ON COLUMN active_collection_jobs.error_message IS 'Error message if collection failed';
COMMENT ON COLUMN active_collection_jobs.started_at IS 'When collection job started';
COMMENT ON COLUMN active_collection_jobs.completed_at IS 'When collection job completed';
COMMENT ON COLUMN active_collection_jobs.created_at IS 'When record was created';
COMMENT ON COLUMN active_collection_jobs.updated_at IS 'When record was last updated';

-- Create indexes for active_collection_jobs table
CREATE INDEX IF NOT EXISTS idx_active_collection_jobs_status ON active_collection_jobs(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_active_collection_jobs_asset ON active_collection_jobs(asset_type, symbol);
CREATE INDEX IF NOT EXISTS idx_active_collection_jobs_started ON active_collection_jobs(started_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_active_collection_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER trigger_update_active_collection_jobs_updated_at
    BEFORE UPDATE ON active_collection_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_active_collection_jobs_updated_at();

-- Cleanup function: Remove old completed/failed jobs (older than 7 days)
-- This can be called periodically to prevent table growth
CREATE OR REPLACE FUNCTION cleanup_old_collection_jobs(days_to_keep INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM active_collection_jobs
    WHERE status IN ('completed', 'failed')
      AND completed_at < NOW() - (days_to_keep || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_collection_jobs IS 'Removes old completed/failed collection jobs older than specified days (default: 7 days)';

