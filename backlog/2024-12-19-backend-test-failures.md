# [HIGH] Backend Test Failures

## Description

Several backend tests are failing due to missing dependencies (database connection, Docker containers). These tests require infrastructure setup that may not be available in all test environments.

## Test File Reference

- File: `tests/test_ingestion_db_connection.py`
- Tests:
  - `TestDatabaseConnection::test_get_db_connection_direct`
  - `TestDatabaseConnection::test_get_db_connection_context_manager`
  - `TestDatabaseConnection::test_connection_pool`
  - `TestDatabaseConnection::test_test_connection`
- File: `tests/test_scheduler_docker.py`
- Tests:
  - `TestSchedulerDocker::test_scheduler_container_health`
  - `TestSchedulerDocker::test_scheduler_loads_jobs_from_database`
  - `TestSchedulerDocker::test_scheduler_communicates_with_api`
- File: `tests/test_collectors.py`
- Test: `test_collector` (error during execution)

## Steps to Reproduce

1. Run pytest: `pytest tests/ --ignore=tests/test_function_creation.py`
2. Observe test failures for database connection and Docker-dependent tests

## Expected Behavior

Tests should either:
1. Skip gracefully when dependencies are not available, OR
2. Pass when dependencies are available

## Actual Behavior

Tests fail with errors when dependencies are not available:
- Database connection tests fail when database is not running
- Docker tests fail when Docker containers are not running
- Collector test has an execution error

## Error Messages

### Database Connection Tests
```
FAILED tests/test_ingestion_db_connection.py::TestDatabaseConnection::test_get_db_connection_direct
FAILED tests/test_ingestion_db_connection.py::TestDatabaseConnection::test_get_db_connection_context_manager
FAILED tests/test_ingestion_db_connection.py::TestDatabaseConnection::test_connection_pool
FAILED tests/test_ingestion_db_connection.py::TestDatabaseConnection::test_test_connection
```

### Docker Tests
```
FAILED tests/test_scheduler_docker.py::TestSchedulerDocker::test_scheduler_container_health
FAILED tests/test_scheduler_docker.py::TestSchedulerDocker::test_scheduler_loads_jobs_from_database
FAILED tests/test_scheduler_docker.py::TestSchedulerDocker::test_scheduler_communicates_with_api
```

### Collector Test
```
ERROR tests/test_collectors.py::test_collector
```

## Severity

- **High**: Test failures prevent proper test execution and may indicate infrastructure setup issues or test design problems.

## Additional Context

These tests require external dependencies:
- Database connection tests require PostgreSQL database to be running
- Docker tests require Docker containers to be running
- Collector test error needs investigation

## Recommended Fix

1. **Database Connection Tests:**
   - Add proper error handling and skipping when database is not available
   - Use pytest fixtures with proper skip conditions
   - Example:
     ```python
     @pytest.fixture
     def db_connection():
         try:
             conn = get_db_connection()
             yield conn
             conn.close()
         except psycopg2.OperationalError:
             pytest.skip("Database not available")
     ```

2. **Docker Tests:**
   - Add conditional skipping when Docker is not available
   - Check for Docker availability before running tests
   - Example:
     ```python
     @pytest.mark.skipif(not docker_available(), reason="Docker not available")
     def test_scheduler_container_health():
         ...
     ```

3. **Collector Test:**
   - Investigate the error and fix the underlying issue
   - Add proper error handling and logging

## Related Issues

- `2024-12-19-backend-test-quality-issues.md` - Related test quality issues

