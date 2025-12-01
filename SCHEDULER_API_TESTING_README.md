# Scheduler API Testing Guide

## Overview

This directory contains comprehensive API-only testing for the scheduler system. All tests are performed via HTTP API calls - no UI testing is included.

## Files

- `scheduler-api-testing-plan.md` - Detailed testing plan and scenarios
- `test_scheduler_api_comprehensive.py` - Main test script with all test scenarios
- `run_scheduler_api_tests_cycle.py` - Test cycle runner (recreates containers, runs tests, saves results)

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ with required packages:
  - `requests`
  - `psycopg2`

### Running Tests

#### Option 1: Run tests with automatic container recreation

```bash
python run_scheduler_api_tests_cycle.py --recreate
```

This will:
1. Stop and remove existing containers
2. Rebuild and start containers
3. Wait for containers to be healthy
4. Run all test scenarios
5. Save results to JSON file
6. Print summary

#### Option 2: Run tests only (containers must already be running)

```bash
python test_scheduler_api_comprehensive.py
```

#### Option 3: Manual container recreation

```bash
# Recreate containers
docker-compose down
docker-compose build
docker-compose up -d

# Wait for containers to be ready
# Then run tests
python test_scheduler_api_comprehensive.py
```

## Test Scenarios

The test suite includes 20 comprehensive test scenarios:

### Category 1: First-Time History Jobs (6 tests)
- Stock - Full History with Date Range
- Crypto - Full History with Granularity
- Forex - Full History
- Bond - Full History
- Commodity - Full History
- Economic Indicator - Full History

### Category 2: Incremental Jobs (2 tests)
- Stock - Incremental Mode
- Crypto - Incremental with Different Granularity

### Category 3: Scheduled Jobs (3 tests)
- Stock - Interval Trigger
- Forex - Cron Trigger
- Crypto - Short Interval

### Category 4: Advanced Features (4 tests)
- Job with Dependencies
- Retry Configuration
- Bulk Job Creation
- Job Templates

### Category 5: Edge Cases (5 tests)
- Job with Custom Collector Kwargs
- Job with Start/End Date Boundaries
- Job Status Transitions
- Job Update
- Job Deletion

## Test Results

Test results are saved to JSON files with the format:
`scheduler-api-test-results-YYYYMMDD-HHMMSS.json`

Each result file contains:
- Test run metadata (start time, end time, totals)
- Detailed results for each test:
  - Test ID and name
  - Status (PASS, FAIL, SKIP)
  - Execution time
  - Error messages (if failed)
  - Verification results
  - Job IDs, execution IDs, log IDs
  - Data collection verification

## Database Cleanup

Before each test run, the script automatically:
- Deletes all records from `scheduler_job_executions`
- Deletes all records from `scheduler_jobs`
- Deletes all records from `job_dependencies`
- Deletes all records from `data_collection_log`

**Note**: Test data in data tables (market_data, forex_rates, etc.) is NOT automatically cleaned up. You may want to manually clean these if needed.

## Configuration

### API Base URL
Default: `http://localhost:8000/api`

Can be modified in `test_scheduler_api_comprehensive.py`:
```python
API_BASE_URL = "http://localhost:8000/api"
```

### Database Configuration
Default connection settings in `test_scheduler_api_comprehensive.py`:
```python
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "investment_platform",
    "user": "postgres",
    "password": "postgres"
}
```

## Troubleshooting

### Containers not starting
- Check Docker is running
- Check ports 5432, 8000 are not in use
- Check docker-compose.yml configuration

### API not responding
- Wait longer for containers to be healthy
- Check API container logs: `docker logs investment_platform_api`
- Verify API health endpoint: `curl http://localhost:8000/api/health`

### Tests failing
- Check test results JSON file for detailed error messages
- Verify database is accessible
- Check scheduler container logs: `docker logs investment_platform_scheduler`
- Verify assets exist in database (some tests require assets to be registered)

### Database connection errors
- Verify database container is running: `docker ps`
- Check database credentials match docker-compose.yml
- Verify database is accepting connections: `docker exec -it investment_platform_db psql -U postgres -d investment_platform -c "SELECT 1"`

## Test Cycle Workflow

1. **Fix Issues**: Review failed tests in results file
2. **Update Code**: Make necessary fixes
3. **Recreate Containers**: `python run_scheduler_api_tests_cycle.py --recreate`
4. **Review Results**: Check new results file
5. **Repeat**: Until all tests pass

## Success Criteria

All tests should:
- ✅ Create jobs successfully via API
- ✅ Trigger jobs and execute successfully
- ✅ Collect data and store in correct tables
- ✅ Verify data matches job criteria
- ✅ Verify execution records exist
- ✅ Verify collection logs are created
- ✅ Verify incremental mode prevents duplicates
- ✅ Verify scheduled jobs are configured correctly
- ✅ Verify dependencies work correctly
- ✅ Verify retry configuration is stored correctly

## API Endpoints Tested

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

## Notes

- Tests use real API calls and database operations
- Tests clean up jobs and logs before starting
- Some tests may take several minutes to complete (data collection)
- Test execution timeouts are set to 180 seconds for data collection jobs
- Results are saved automatically after each test run

