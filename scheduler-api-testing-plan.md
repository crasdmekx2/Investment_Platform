# Scheduler API Testing Plan

## Overview

Comprehensive API-only testing of the scheduler system. All tests are performed via HTTP API calls to the scheduler endpoints. No UI testing is included in this plan.

## Test Environment

- API Base URL: `http://localhost:8000/api`
- Database: PostgreSQL in Docker container
- Test execution: Python script using `requests` library
- Container management: Docker Compose

## Test Execution Strategy

1. **Setup Phase**: Clean up all existing jobs and collection logs
2. **Test Execution**: Run all test scenarios via API
3. **Verification**: Query database to verify data collection
4. **Results**: Save test results to file
5. **Fix & Retry**: Fix issues, recreate containers, rerun until all pass

## Test Categories

### Category 1: First-Time History Jobs (Non-Incremental)

**Purpose**: Test jobs that fill in historical data for the first time

1. **Stock - Full History with Date Range**
   - Asset: Stock (AAPL)
   - Mode: Non-incremental
   - Date range: Last 30 days
   - Trigger: Execute Now (execute_now flag)
   - Collector: interval=1d
   - Verify: Records exist in market_data table

2. **Crypto - Full History with Granularity**
   - Asset: Crypto (BTC-USD)
   - Mode: Non-incremental
   - Date range: Last 7 days
   - Trigger: Execute Now
   - Collector: granularity=ONE_HOUR
   - Verify: Records exist in market_data table

3. **Forex - Full History**
   - Asset: Forex (USD_EUR)
   - Mode: Non-incremental
   - Date range: Last 14 days
   - Trigger: Execute Now
   - Verify: Records exist in forex_rates table

4. **Bond - Full History**
   - Asset: Bond (DGS10)
   - Mode: Non-incremental
   - Date range: Last 30 days
   - Trigger: Execute Now
   - Verify: Records exist in bond_rates table

5. **Commodity - Full History**
   - Asset: Commodity (CL=F)
   - Mode: Non-incremental
   - Date range: Last 14 days
   - Trigger: Execute Now
   - Collector: interval=1d
   - Verify: Records exist in market_data table

6. **Economic Indicator - Full History**
   - Asset: Economic Indicator (GDP)
   - Mode: Non-incremental
   - Date range: Last 90 days
   - Trigger: Execute Now
   - Verify: Records exist in economic_data table

### Category 2: Incremental Jobs

**Purpose**: Test jobs that only fetch missing data

7. **Stock - Incremental Mode**
   - Asset: Stock (MSFT)
   - Mode: Incremental (via collector_kwargs or incremental flag)
   - Trigger: Execute Now
   - Collector: interval=1d
   - Verify: Only missing data collected, no duplicates

8. **Crypto - Incremental with Different Granularity**
   - Asset: Crypto (ETH-USD)
   - Mode: Incremental
   - Trigger: Execute Now
   - Collector: granularity=FIFTEEN_MINUTE
   - Verify: Incremental collection works correctly

### Category 3: Scheduled Jobs

**Purpose**: Test recurring scheduled execution

9. **Stock - Interval Trigger**
   - Asset: Stock (GOOGL)
   - Mode: Incremental
   - Trigger: Interval (hours=1, minutes=0)
   - Verify: Job created and scheduled correctly

10. **Forex - Cron Trigger**
    - Asset: Forex (GBP_USD)
    - Mode: Incremental
    - Trigger: Cron (hour=9, minute=0)
    - Verify: Job created with cron schedule

11. **Crypto - Short Interval**
    - Asset: Crypto (BTC-USD)
    - Mode: Incremental
    - Trigger: Interval (minutes=5)
    - Verify: Frequent execution schedule works

### Category 4: Advanced Features

12. **Job with Dependencies**
    - Create parent job (Stock AAPL)
    - Create dependent job (Stock MSFT) that depends on AAPL
    - Verify: Dependencies stored correctly

13. **Retry Configuration**
    - Create job with max_retries=2, retry_delay_seconds=30, retry_backoff_multiplier=1.5
    - Verify: Retry configuration stored correctly

14. **Bulk Job Creation**
    - Create multiple stock jobs (AAPL, MSFT, GOOGL) in sequence
    - Verify: All jobs created and can execute independently

15. **Job Templates**
    - Create job template
    - Use template to create job (if API supports it)
    - Verify: Template values applied correctly

### Category 5: Edge Cases

16. **Job with Custom Collector Kwargs**
    - Stock with interval=1m
    - Crypto with granularity=ONE_MINUTE
    - Verify: Custom parameters respected

17. **Job with Start/End Date Boundaries**
    - Test with start_date only
    - Test with end_date only
    - Test with both dates
    - Verify: Date calculations correct

18. **Job Status Transitions**
    - Create job (pending → active)
    - Pause job (active → paused)
    - Resume job (paused → active)
    - Verify: Status transitions work correctly

19. **Job Update**
    - Create job
    - Update job configuration
    - Verify: Updates applied correctly

20. **Job Deletion**
    - Create job
    - Delete job
    - Verify: Job removed from database

## API Endpoints to Test

- `POST /api/scheduler/jobs` - Create job
- `GET /api/scheduler/jobs` - List jobs
- `GET /api/scheduler/jobs/{job_id}` - Get job
- `PUT /api/scheduler/jobs/{job_id}` - Update job
- `DELETE /api/scheduler/jobs/{job_id}` - Delete job
- `POST /api/scheduler/jobs/{job_id}/pause` - Pause job
- `POST /api/scheduler/jobs/{job_id}/resume` - Resume job
- `POST /api/scheduler/jobs/{job_id}/trigger` - Trigger job
- `GET /api/scheduler/jobs/{job_id}/executions` - Get executions
- `GET /api/scheduler/templates` - List templates
- `POST /api/scheduler/templates` - Create template
- `GET /api/scheduler/analytics` - Get analytics

## Verification Steps (Per Test)

### Step 1: Job Creation Verification
- Create job via API
- Verify: HTTP 201 response
- Verify: Job appears in jobs list
- Verify: Job exists in database with correct parameters

### Step 2: Job Execution Verification
- Trigger job manually OR wait for scheduled execution
- Verify: Job execution recorded in `scheduler_job_executions` table
- Verify: Execution status is "success"
- Verify: `data_collection_log` entry created
- Verify: `log_id` links execution to collection log

### Step 3: Data Verification
- Query appropriate data table based on asset_type:
  - `market_data` for stock, crypto, commodity
  - `forex_rates` for forex
  - `bond_rates` for bond
  - `economic_data` for economic_indicator
- Verify: Records exist for correct `asset_id` (lookup by symbol)
- Verify: Records match date range from job
- Verify: Record count matches `records_collected` in log
- Verify: Data timestamps are within job's start_date/end_date range
- Verify: Data values are valid (non-null, reasonable ranges)

### Step 4: Incremental Mode Verification
- For incremental jobs: Verify no duplicate records
- Check that only missing data was collected
- Verify `incremental_tracker` logic worked correctly

### Step 5: Scheduled Execution Verification
- For scheduled jobs: Verify job is scheduled correctly
- Verify: `next_run_at` is set correctly
- Verify: Job status is "active"

## Database Cleanup

Before each test run:
- Delete all records from `scheduler_job_executions`
- Delete all records from `scheduler_jobs`
- Delete all records from `job_dependencies`
- Delete all records from `data_collection_log`
- Optionally: Clean up test data from data tables (market_data, forex_rates, etc.)

## Success Criteria

- All job creation combinations work correctly
- Jobs can be triggered and execute successfully
- Data is collected and stored correctly
- Records match job criteria (symbol, dates, parameters)
- Incremental mode prevents duplicates
- Scheduled execution configuration works
- Dependencies work correctly
- Retry logic configuration stored correctly
- All API endpoints return expected responses
- All issues documented for developer review

## Test Results Format

Each test should record:
- Test ID and name
- Status: PASS, FAIL, SKIP
- Execution time
- Error message (if failed)
- Verification results
- Data collected count
- Execution ID and log ID

## Files to Reference

- API endpoints: `src/investment_platform/api/routers/scheduler.py`
- Scheduler service: `src/investment_platform/api/services/scheduler_service.py`
- Database schema: `init-db/05-create-scheduler-schema.sql`, `init-db/06-scheduler-enhancements.sql`
- Data tables: `init-db/02-create-schema.sql`
- Scheduler implementation: `src/investment_platform/ingestion/persistent_scheduler.py`

