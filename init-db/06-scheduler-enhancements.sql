-- ============================================================================
-- Scheduler Enhancements Schema
-- ============================================================================
-- This script adds enhancements to the scheduler system:
-- - Job dependencies
-- - Retry configuration
-- - Job templates
-- - Error categorization
--
-- Execution order:
--   1. 02-create-schema.sql (base schema)
--   2. 05-create-scheduler-schema.sql (scheduler base)
--   3. 06-scheduler-enhancements.sql (this file)
-- ============================================================================

-- ============================================================================
-- JOB DEPENDENCIES
-- ============================================================================

-- Job Dependencies table: Store job dependency relationships
CREATE TABLE IF NOT EXISTS job_dependencies (
    dependency_id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) NOT NULL REFERENCES scheduler_jobs(job_id) ON DELETE CASCADE,
    depends_on_job_id VARCHAR(255) NOT NULL REFERENCES scheduler_jobs(job_id) ON DELETE CASCADE,
    condition VARCHAR(20) NOT NULL DEFAULT 'success' CHECK (condition IN ('success', 'complete', 'any')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Prevent duplicate dependencies
    CONSTRAINT unique_job_dependency UNIQUE (job_id, depends_on_job_id),
    
    -- Prevent self-dependencies
    CONSTRAINT no_self_dependency CHECK (job_id != depends_on_job_id)
);

-- Add table comment
COMMENT ON TABLE job_dependencies IS 'Stores job dependency relationships - jobs that must complete before dependent jobs can run';

-- Add column comments
COMMENT ON COLUMN job_dependencies.dependency_id IS 'Primary key, auto-incrementing integer';
COMMENT ON COLUMN job_dependencies.job_id IS 'Job that depends on another job';
COMMENT ON COLUMN job_dependencies.depends_on_job_id IS 'Job that must complete first';
COMMENT ON COLUMN job_dependencies.condition IS 'Condition for dependency: success (must succeed), complete (must complete), any (just run)';

-- Create indexes for job_dependencies table
CREATE INDEX IF NOT EXISTS idx_job_dependencies_job ON job_dependencies(job_id);
CREATE INDEX IF NOT EXISTS idx_job_dependencies_depends_on ON job_dependencies(depends_on_job_id);

-- ============================================================================
-- RETRY CONFIGURATION
-- ============================================================================

-- Add retry configuration columns to scheduler_jobs table
ALTER TABLE scheduler_jobs
    ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3 CHECK (max_retries >= 0),
    ADD COLUMN IF NOT EXISTS retry_delay_seconds INTEGER DEFAULT 60 CHECK (retry_delay_seconds >= 0),
    ADD COLUMN IF NOT EXISTS retry_backoff_multiplier NUMERIC(5, 2) DEFAULT 2.0 CHECK (retry_backoff_multiplier >= 1.0);

-- Add column comments
COMMENT ON COLUMN scheduler_jobs.max_retries IS 'Maximum number of retry attempts for failed jobs (0 = no retries)';
COMMENT ON COLUMN scheduler_jobs.retry_delay_seconds IS 'Initial delay in seconds before first retry';
COMMENT ON COLUMN scheduler_jobs.retry_backoff_multiplier IS 'Multiplier for exponential backoff (e.g., 2.0 = double delay each retry)';

-- ============================================================================
-- JOB TEMPLATES
-- ============================================================================

-- Job Templates table: Store reusable job configurations
CREATE TABLE IF NOT EXISTS job_templates (
    template_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    symbol VARCHAR(100),  -- Optional, can be null for templates
    asset_type VARCHAR(50) NOT NULL CHECK (asset_type IN ('stock', 'forex', 'crypto', 'bond', 'commodity', 'economic_indicator')),
    trigger_type VARCHAR(20) NOT NULL CHECK (trigger_type IN ('cron', 'interval')),
    trigger_config JSONB NOT NULL,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    collector_kwargs JSONB,
    asset_metadata JSONB,
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,
    retry_backoff_multiplier NUMERIC(5, 2) DEFAULT 2.0,
    is_public BOOLEAN DEFAULT FALSE,  -- Whether template is available to all users
    created_by VARCHAR(255),  -- User identifier (optional)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT job_templates_date_check CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

-- Add table comment
COMMENT ON TABLE job_templates IS 'Stores reusable job configuration templates';

-- Add column comments
COMMENT ON COLUMN job_templates.template_id IS 'Primary key, auto-incrementing integer';
COMMENT ON COLUMN job_templates.name IS 'Template name (e.g., "Daily Stock Collection")';
COMMENT ON COLUMN job_templates.description IS 'Template description';
COMMENT ON COLUMN job_templates.symbol IS 'Optional default symbol for template';
COMMENT ON COLUMN job_templates.asset_type IS 'Asset type this template is for';
COMMENT ON COLUMN job_templates.trigger_type IS 'Type of trigger: cron or interval';
COMMENT ON COLUMN job_templates.trigger_config IS 'JSON configuration for trigger';
COMMENT ON COLUMN job_templates.is_public IS 'Whether template is available to all users';
COMMENT ON COLUMN job_templates.created_by IS 'User who created the template (optional)';

-- Create indexes for job_templates table
CREATE INDEX IF NOT EXISTS idx_job_templates_asset_type ON job_templates(asset_type);
CREATE INDEX IF NOT EXISTS idx_job_templates_public ON job_templates(is_public) WHERE is_public = TRUE;
CREATE INDEX IF NOT EXISTS idx_job_templates_created ON job_templates(created_at DESC);

-- Function to update updated_at timestamp for job_templates
CREATE OR REPLACE FUNCTION update_job_templates_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at for job_templates
CREATE TRIGGER trigger_update_job_templates_updated_at
    BEFORE UPDATE ON job_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_job_templates_updated_at();

-- ============================================================================
-- ERROR CATEGORIZATION
-- ============================================================================

-- Add error categorization column to scheduler_job_executions table
ALTER TABLE scheduler_job_executions
    ADD COLUMN IF NOT EXISTS error_category VARCHAR(50) CHECK (error_category IN ('transient', 'permanent', 'system', NULL)),
    ADD COLUMN IF NOT EXISTS retry_attempt INTEGER DEFAULT 0 CHECK (retry_attempt >= 0);

-- Add column comments
COMMENT ON COLUMN scheduler_job_executions.error_category IS 'Error category: transient (retryable), permanent (validation/config), system (database/API)';
COMMENT ON COLUMN scheduler_job_executions.retry_attempt IS 'Retry attempt number (0 = first attempt, 1+ = retries)';

-- Create index for error categorization
CREATE INDEX IF NOT EXISTS idx_job_executions_error_category ON scheduler_job_executions(error_category, started_at DESC) WHERE error_category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_job_executions_retry_attempt ON scheduler_job_executions(job_id, retry_attempt);

-- ============================================================================
-- FUNCTION TO CHECK FOR CIRCULAR DEPENDENCIES
-- ============================================================================

-- Function to check for circular dependencies (prevents A -> B -> A)
CREATE OR REPLACE FUNCTION check_circular_dependency(
    p_job_id VARCHAR(255),
    p_depends_on_job_id VARCHAR(255)
)
RETURNS BOOLEAN AS $$
DECLARE
    v_visited VARCHAR(255)[] := ARRAY[p_job_id];
    v_current VARCHAR(255) := p_depends_on_job_id;
    v_next VARCHAR(255);
BEGIN
    -- If depends_on_job_id is the same as job_id, it's a self-dependency (handled by constraint)
    IF p_job_id = p_depends_on_job_id THEN
        RETURN TRUE;
    END IF;
    
    -- Traverse dependency chain to check for cycles
    WHILE v_current IS NOT NULL LOOP
        -- If we've seen this job before, we have a cycle
        IF v_current = ANY(v_visited) THEN
            RETURN TRUE;
        END IF;
        
        -- Add current to visited
        v_visited := array_append(v_visited, v_current);
        
        -- Check if current job depends on the original job (circular)
        IF v_current = p_job_id THEN
            RETURN TRUE;
        END IF;
        
        -- Get next dependency
        SELECT depends_on_job_id INTO v_next
        FROM job_dependencies
        WHERE job_id = v_current
        LIMIT 1;
        
        v_current := v_next;
    END LOOP;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Trigger to prevent circular dependencies
CREATE OR REPLACE FUNCTION prevent_circular_dependency()
RETURNS TRIGGER AS $$
BEGIN
    IF check_circular_dependency(NEW.job_id, NEW.depends_on_job_id) THEN
        RAISE EXCEPTION 'Circular dependency detected: job % depends on job % which creates a cycle', NEW.job_id, NEW.depends_on_job_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to check for circular dependencies
DROP TRIGGER IF EXISTS trigger_prevent_circular_dependency ON job_dependencies;
CREATE TRIGGER trigger_prevent_circular_dependency
    BEFORE INSERT OR UPDATE ON job_dependencies
    FOR EACH ROW
    EXECUTE FUNCTION prevent_circular_dependency();

-- ============================================================================
-- END OF SCHEDULER ENHANCEMENTS SCHEMA
-- ============================================================================

