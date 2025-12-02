# [HIGH] Backend Test Coverage Gaps

## Description

Backend test coverage is currently at 30%, significantly below the target of >80%. Critical API routers and services have very low coverage (11-29%), which poses risks for data integrity and security.

## Test File Reference

- Coverage Report: Generated via `pytest --cov=src/investment_platform --cov-report=term-missing`
- Overall Coverage: 30%
- Target Coverage: >80%
- Coverage Gap: 50%

## Coverage by Module

### Critical Modules with Low Coverage:

1. **API Routers** (20-29% coverage):
   - `src/investment_platform/api/routers/assets.py`: 20% coverage
   - `src/investment_platform/api/routers/collectors.py`: 29% coverage
   - `src/investment_platform/api/routers/ingestion.py`: 29% coverage
   - `src/investment_platform/api/routers/scheduler.py`: 23% coverage

2. **API Services** (11-16% coverage):
   - `src/investment_platform/api/services/scheduler_service.py`: 11% coverage
   - `src/investment_platform/api/services/collector_service.py`: 16% coverage

3. **API Main** (15% coverage):
   - `src/investment_platform/api/main.py`: 15% coverage

4. **WebSocket** (29% coverage):
   - `src/investment_platform/api/websocket.py`: 29% coverage

5. **Persistent Scheduler** (8% coverage):
   - `src/investment_platform/ingestion/persistent_scheduler.py`: 8% coverage

## Steps to Reproduce

1. Run coverage report: `pytest --cov=src/investment_platform --cov-report=term-missing`
2. Review coverage percentages for each module
3. Identify modules with coverage < 80%

## Expected Behavior

All modules should have >80% test coverage, with critical paths (API endpoints, data integrity, security) having 100% coverage.

## Actual Behavior

Many critical modules have coverage well below 80%:
- API routers: 20-29% coverage
- API services: 11-16% coverage
- API main: 15% coverage
- Persistent scheduler: 8% coverage

## Error Message

N/A (Coverage gap, not a test failure)

## Severity

- **High**: Low test coverage increases risk of bugs, security vulnerabilities, and regressions. Critical API endpoints and services are not adequately tested.

## Additional Context

### New Tests Created During QA:

1. **Security Tests** (`tests/test_api_security.py`):
   - Input validation tests
   - SQL injection prevention tests
   - XSS prevention tests

2. **API Router Tests**:
   - Assets router tests (`tests/test_api_routers_assets.py`)
   - Collectors router tests (`tests/test_api_routers_collectors.py`)

### Remaining Gaps:

1. **API Router Tests**:
   - Ingestion router integration tests
   - Scheduler router integration tests (partial coverage exists)
   - Error handling and edge cases for all routers

2. **API Service Tests**:
   - Scheduler service unit and integration tests
   - Collector service unit and integration tests

3. **WebSocket Tests**:
   - WebSocket endpoint integration tests
   - Real-time update tests

4. **Persistent Scheduler Tests**:
   - Job management tests
   - Scheduling logic tests
   - Error handling tests

## Recommended Fix

1. **Immediate Actions:**
   - Create integration tests for remaining API router endpoints
   - Create unit tests for API service layer
   - Add error handling and edge case tests

2. **Short-term Actions:**
   - Achieve >80% coverage for API routers
   - Achieve >80% coverage for API services
   - Add WebSocket endpoint tests

3. **Long-term Actions:**
   - Set up coverage gates in CI/CD (fail builds if coverage < 80%)
   - Regular coverage reviews
   - Maintain >80% coverage as code evolves

## Test Creation Priority

1. **Priority 1 (Critical):**
   - API router integration tests (all endpoints)
   - API service unit tests
   - Security tests (completed)

2. **Priority 2 (High):**
   - WebSocket endpoint tests
   - Persistent scheduler tests
   - Error handling tests

3. **Priority 3 (Standard):**
   - Edge case tests
   - Performance tests
   - Load tests

## Related Issues

- `2024-12-19-backend-test-failures.md` - Some tests are failing
- `2024-12-19-backend-test-quality-issues.md` - Test quality improvements needed

