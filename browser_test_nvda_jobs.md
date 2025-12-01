# Browser Testing Guide for NVDA Execute Now Jobs

## Test Scenarios Completed via API

All 5 test scenarios have been successfully tested via API:

1. ✅ **1d Interval - Incremental**: Job created and executed successfully
2. ✅ **1h Interval - Incremental**: Job created and executed successfully  
3. ✅ **1wk Interval - Incremental**: Job created and executed successfully
4. ✅ **1d Interval - Full History**: Job created and executed successfully
5. ✅ **1h Interval - Full History**: Job created and executed successfully

## Database Verification Results

- **Asset Found**: NVDA (asset_id: 1124)
- **Market Data Records**: 149 records stored
- **Job Executions**: All 5 jobs executed with "success" status

## Browser Testing Steps

To verify the UI functionality, follow these steps in the browser:

### Test 1: 1d Interval - Incremental Mode

1. Navigate to http://localhost:3000/scheduler
2. Click "Create Job" tab
3. Step 1: Select "Stock" asset type
4. Step 2: Search and select "NVDA" symbol
5. Step 3: Collection Parameters
   - Set Interval to "1 Day"
   - Keep "Incremental mode" checked (default)
   - Click "Next"
6. Step 4: Schedule Configuration
   - Select "Schedule Now" option
   - Click "Next"
7. Step 5: Review
   - Verify configuration shows "Execute Now (One-time)"
   - Click "Create Job"
8. Verification:
   - Job should appear in Jobs list
   - Status should show "success" (not "failed")
   - Check Collection Logs tab for recent NVDA collection
   - Verify records collected > 0

### Test 2: 1h Interval - Incremental Mode

Repeat steps 1-8 but set Interval to "1 Hour" in Step 3.

### Test 3: 1wk Interval - Incremental Mode

Repeat steps 1-8 but set Interval to "1 Week" in Step 3.

### Test 4: 1d Interval - Full History Mode

1. Follow steps 1-3 from Test 1
2. Step 3: Collection Parameters
   - Set Interval to "1 Day"
   - **Uncheck** "Incremental mode"
   - Set Start Date (e.g., 30 days ago)
   - Set End Date (e.g., today)
   - Click "Next"
3. Step 4: Schedule Configuration
   - "Schedule Now" option should be available
   - Select "Schedule Now"
   - Click "Next"
4. Step 5: Review and Create
5. Verify execution and database records

### Test 5: 1h Interval - Full History Mode

Repeat Test 4 but set Interval to "1 Hour" in Step 3.

## Expected Results

For each test:
- ✅ Job should be created successfully
- ✅ Job should execute immediately (not wait for schedule)
- ✅ Job status should show "success" in dashboard
- ✅ Collection logs should show records collected > 0
- ✅ Database should have market_data records for NVDA
- ✅ No error messages in browser console

## Known Issues Fixed

- **Issue**: Jobs with `execute_now` flag were not being added to scheduler, causing trigger to fail
- **Fix**: Modified `src/investment_platform/api/routers/scheduler.py` to add all jobs to scheduler, including execute_now jobs
- **Result**: Jobs can now be triggered successfully and execute immediately

