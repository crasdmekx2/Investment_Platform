-- ============================================================================
-- Scheduler Schema Extensions
-- ============================================================================
-- This script creates tables for persistent scheduler job storage and execution tracking.
--
-- Execution order:
--   1. 02-create-schema.sql (base schema)
--   2. 05-create-scheduler-schema.sql (this file)
-- ============================================================================

-- ============================================================================
-- SCHEDULER JOB PERSISTENCE
-- ============================================================================

-- Scheduler Jobs table: Store scheduled job configurations
CREATE TABLE IF NOT EXISTS scheduler_jobs (
    job_id VARCHAR(255) PRIMARY KEY,
    symbol VARCHAR(100) NOT NULL,
    asset_type VARCHAR(50) NOT NULL CHECK (asset_type IN ('stock', 'forex', 'crypto', 'bond', 'commodity', 'economic_indicator')),
    trigger_type VARCHAR(20) NOT NULL CHECK (trigger_type IN ('cron', 'interval')),
    trigger_config JSONB NOT NULL,  -- Stores cron or interval parameters
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    collector_kwargs JSONB,  -- Additional collector-specific parameters
    asset_metadata JSONB,  -- Additional asset metadata
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'paused', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT scheduler_jobs_date_check CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

-- Add table comment
COMMENT ON TABLE scheduler_jobs IS 'Stores persistent scheduled job configurations for data collection';

-- Add column comments
COMMENT ON COLUMN scheduler_jobs.job_id IS 'Primary key, unique job identifier';
COMMENT ON COLUMN scheduler_jobs.symbol IS 'Asset symbol (e.g., AAPL, BTC-USD, USD_EUR)';
COMMENT ON COLUMN scheduler_jobs.asset_type IS 'Type of asset being collected';
COMMENT ON COLUMN scheduler_jobs.trigger_type IS 'Type of trigger: cron or interval';
COMMENT ON COLUMN scheduler_jobs.trigger_config IS 'JSON configuration for trigger (cron expression or interval parameters)';
COMMENT ON COLUMN scheduler_jobs.start_date IS 'Optional start date for data collection period';
COMMENT ON COLUMN scheduler_jobs.end_date IS 'Optional end date for data collection period';
COMMENT ON COLUMN scheduler_jobs.collector_kwargs IS 'Additional parameters for collector (e.g., granularity, interval)';
COMMENT ON COLUMN scheduler_jobs.asset_metadata IS 'Additional metadata for asset registration';
COMMENT ON COLUMN scheduler_jobs.status IS 'Current job status: pending, active, paused, completed, failed';
COMMENT ON COLUMN scheduler_jobs.last_run_at IS 'Timestamp of last job execution';
COMMENT ON COLUMN scheduler_jobs.next_run_at IS 'Timestamp of next scheduled execution';

-- Create indexes for scheduler_jobs table
CREATE INDEX IF NOT EXISTS idx_scheduler_jobs_status ON scheduler_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scheduler_jobs_asset ON scheduler_jobs(asset_type, symbol);
CREATE INDEX IF NOT EXISTS idx_scheduler_jobs_next_run ON scheduler_jobs(next_run_at) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_scheduler_jobs_created ON scheduler_jobs(created_at DESC);

-- Scheduler Job Executions table: Track individual job runs
CREATE TABLE IF NOT EXISTS scheduler_job_executions (
    execution_id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) NOT NULL REFERENCES scheduler_jobs(job_id) ON DELETE CASCADE,
    log_id INTEGER REFERENCES data_collection_log(log_id) ON DELETE SET NULL,
    execution_status VARCHAR(20) NOT NULL CHECK (execution_status IN ('running', 'success', 'failed', 'cancelled')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add table comment
COMMENT ON TABLE scheduler_job_executions IS 'Tracks individual executions of scheduled jobs';

-- Add column comments
COMMENT ON COLUMN scheduler_job_executions.execution_id IS 'Primary key, auto-incrementing integer';
COMMENT ON COLUMN scheduler_job_executions.job_id IS 'Foreign key to scheduler_jobs table';
COMMENT ON COLUMN scheduler_job_executions.log_id IS 'Foreign key to data_collection_log table (links to collection run)';
COMMENT ON COLUMN scheduler_job_executions.execution_status IS 'Status of this execution: running, success, failed, cancelled';
COMMENT ON COLUMN scheduler_job_executions.started_at IS 'When execution started';
COMMENT ON COLUMN scheduler_job_executions.completed_at IS 'When execution completed';
COMMENT ON COLUMN scheduler_job_executions.error_message IS 'Error message if execution failed';
COMMENT ON COLUMN scheduler_job_executions.execution_time_ms IS 'Execution time in milliseconds';

-- Create indexes for scheduler_job_executions table
CREATE INDEX IF NOT EXISTS idx_job_executions_job ON scheduler_job_executions(job_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_executions_status ON scheduler_job_executions(execution_status, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_executions_log ON scheduler_job_executions(log_id) WHERE log_id IS NOT NULL;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_scheduler_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER trigger_update_scheduler_jobs_updated_at
    BEFORE UPDATE ON scheduler_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_scheduler_jobs_updated_at();

-- ============================================================================
-- END OF SCHEDULER SCHEMA
-- ============================================================================

