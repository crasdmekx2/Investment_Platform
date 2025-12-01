# Scheduler API Test Issues - Analysis and Fixes Needed

## Test Execution Summary

**Date**: 2025-12-01  
**Total Tests**: 20  
**Passed**: 7  
**Failed**: 13  
**Skipped**: 0

## Issues Found

### 1. ✅ FIXED: Timezone Issue (TEST-016)
**Status**: Fixed  
**Issue**: `can't subtract offset-naive and offset-aware datetimes`  
**Fix**: Updated test to handle timezone-aware datetimes correctly  
**File**: `test_scheduler_api_comprehensive.py` (test_16_date_boundaries)

### 2. Data Loading Failure (TEST-001)
**Status**: Needs Investigation  
**Error**: "Collected 1 records but failed to load any into database. Data may have been invalid or database insertion failed."  
**Details**:
- Job created successfully
- Job triggered successfully
- Execution recorded but status is "failed"
- Error message indicates data collection succeeded but database insertion failed
- 0 records loaded despite 1 record collected

**Possible Causes**:
- Data validation failure
- Database constraint violation
- Schema mismatch
- Transaction rollback

**Next Steps**:
- Check scheduler logs for detailed error
- Verify data format matches schema
- Check database constraints
- Review data loader implementation

### 3. ✅ FIXED: Crypto API Key Missing (TEST-002)
**Status**: Fixed - Configuration Updated  
**Error**: "Unauthenticated request to private endpoint. If you wish to access private endpoints, you must provide your API key and secret when initializing the RESTClient."  
**Details**:
- Crypto collector requires API keys for Coinbase Advanced API
- COINBASE_API_KEY is located in .env file
- Also requires COINBASE_API_SECRET

**Fix Applied**:
- Updated `docker-compose.yml` to load `.env` file for both `api` and `scheduler` containers
- Added `env_file: - .env` to both service definitions
- Containers will now have access to COINBASE_API_KEY, COINBASE_API_SECRET, and FRED_API_KEY from .env file

**Note**: 
- Ensure .env file contains:
  - `COINBASE_API_KEY=your_key`
  - `COINBASE_API_SECRET=your_secret`
  - `FRED_API_KEY=your_key` (for bonds and economic indicators)
- After updating docker-compose.yml, containers need to be recreated to pick up the .env file

### 4. API Timeout Issues (TEST-003 through TEST-012)
**Status**: Critical - Needs Investigation  
**Error**: `HTTPConnectionPool(host='localhost', port=8000): Read timed out`  
**Details**:
- API stops responding after a few requests
- Timeouts occur on both job creation and job triggering
- Affects multiple test scenarios
- API appears to hang or become unresponsive

**Timeline**:
- TEST-001: Passed (job creation, execution)
- TEST-002: Passed (job creation, execution failed due to API key)
- TEST-003: Timeout on trigger (60s timeout)
- TEST-004 onwards: Timeout on job creation (30s timeout)

**Possible Causes**:
1. **Scheduler blocking API thread**: Scheduler operations might be blocking the API
2. **Database connection pool exhaustion**: All connections might be in use
3. **Deadlock**: API waiting for scheduler, scheduler waiting for API
4. **Long-running operations**: Job execution taking too long
5. **Resource exhaustion**: Memory or CPU limits

**Next Steps**:
1. Check API container logs for errors
2. Check scheduler container logs for blocking operations
3. Verify database connection pool configuration
4. Check if scheduler is running in blocking mode
5. Review API request handling for async/await issues
6. Check for thread locks or semaphores

### 5. Tests That Passed ✅
- TEST-013: Retry Configuration
- TEST-014: Bulk Job Creation
- TEST-015: Custom Collector Kwargs
- TEST-017: Job Status Transitions
- TEST-018: Job Update
- TEST-019: Job Deletion
- TEST-020: Job Templates

These tests verify that:
- Job CRUD operations work
- Job configuration is stored correctly
- Status transitions work
- Templates API works

## Recommended Fixes

### Immediate Actions

1. **Investigate API Timeout Issue** (Priority: Critical)
   - Check API and scheduler logs
   - Verify async/await usage in API endpoints
   - Check for blocking operations
   - Review connection pool settings

2. **Investigate Data Loading Failure** (Priority: High)
   - Check scheduler execution logs
   - Verify data format
   - Check database constraints
   - Review error handling in data loader

3. **Handle Crypto API Key** (Priority: Medium)
   - Add environment variable check
   - Skip crypto tests if keys not available
   - Or provide test API keys

### Code Changes Needed

1. **Increase API Timeouts** (Temporary)
   - Increase timeout values in test script
   - But this doesn't fix the root cause

2. **Add Better Error Handling**
   - Catch and log detailed errors
   - Return more informative error messages

3. **Add Retry Logic**
   - Retry failed API calls
   - Exponential backoff

4. **Add Health Checks**
   - Check API health before tests
   - Wait for scheduler to be ready

## Test Results File

Results saved to: `scheduler-api-test-results-20251201-144130.json`

## Next Steps

1. Review API and scheduler logs in detail
2. Fix API timeout issue (most critical)
3. Fix data loading issue
4. Handle crypto API key configuration
5. Re-run tests after fixes
6. Iterate until all tests pass

