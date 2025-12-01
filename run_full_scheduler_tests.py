#!/usr/bin/env python3
"""
Comprehensive scheduler functionality test runner.
Executes all test cases from the scheduler functionality testing plan.
"""

import requests
import json
from datetime import datetime, timedelta
import time
import sys

API_BASE = "http://localhost:8000/api"

def create_job(job_config):
    """Create a scheduled job via API."""
    url = f"{API_BASE}/scheduler/jobs"
    response = requests.post(url, json=job_config)
    if response.status_code == 201:
        data = response.json()
        if "data" in data:
            return data["data"]
        return data
    else:
        print(f"  ✗ Error: {response.status_code} - {response.text[:200]}")
        return None

def trigger_job(job_id):
    """Manually trigger a job execution."""
    url = f"{API_BASE}/scheduler/jobs/{job_id}/trigger"
    response = requests.post(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_job(job_id):
    """Get job details."""
    url = f"{API_BASE}/scheduler/jobs/{job_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "data" in data:
            return data["data"]
        return data
    return None

def get_job_executions(job_id):
    """Get execution history for a job."""
    url = f"{API_BASE}/scheduler/jobs/{job_id}/executions"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "data" in data:
            return data["data"]
        return data if isinstance(data, list) else []
    return []

def get_collection_logs(limit=100):
    """Get collection logs."""
    url = f"{API_BASE}/ingestion/logs"
    params = {"limit": limit}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "data" in data:
            return data["data"]
        return data if isinstance(data, list) else []
    return []

def wait_for_execution(job_id, timeout=60):
    """Wait for job execution to complete."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        executions = get_job_executions(job_id)
        if executions:
            latest = executions[0]
            status = latest.get("status", "")
            if status in ["completed", "failed"]:
                return latest
        time.sleep(2)
    return None

# Calculate dates
end_date = datetime.now().date()
start_date_30d = end_date - timedelta(days=30)
start_date_7d = end_date - timedelta(days=7)

print("="*70)
print("SCHEDULER FUNCTIONALITY TESTING - FULL TEST PLAN")
print("="*70)

test_results = []

# ============================================================================
# CATEGORY 1: FIRST-TIME HISTORY JOBS
# ============================================================================
print("\n" + "="*70)
print("CATEGORY 1: FIRST-TIME HISTORY JOBS")
print("="*70)

# Test 1: Stock - Full History
print("\n[Test 1] Stock - Full History (AAPL)")
test1 = {
    "asset_type": "stock",
    "symbol": "AAPL",
    "trigger_type": "interval",
    "start_date": str(start_date_30d),
    "end_date": str(end_date),
    "collector_kwargs": {"interval": "1d"},
    "trigger_config": {"hours": 0, "minutes": 0, "execute_now": True},
    "max_retries": 3,
    "retry_delay_seconds": 60,
    "retry_backoff_multiplier": 2.0
}
job1 = create_job(test1)
if job1:
    job_id1 = job1.get("job_id")
    print(f"  ✓ Created: {job_id1}")
    # Trigger execution
    trigger_result = trigger_job(job_id1)
    if trigger_result:
        print(f"  ✓ Triggered execution")
        execution = wait_for_execution(job_id1, timeout=120)
        if execution:
            status = execution.get("status")
            print(f"  ✓ Execution status: {status}")
            test_results.append(("Test 1: Stock Full History", status == "completed"))
        else:
            print(f"  ⚠ Execution timeout or not found")
            test_results.append(("Test 1: Stock Full History", False))
    else:
        test_results.append(("Test 1: Stock Full History", False))
else:
    test_results.append(("Test 1: Stock Full History", False))

# Test 2: Crypto - Full History
print("\n[Test 2] Crypto - Full History (BTC-USD)")
test2 = {
    "asset_type": "crypto",
    "symbol": "BTC-USD",
    "trigger_type": "interval",
    "start_date": str(start_date_30d),
    "end_date": str(end_date),
    "collector_kwargs": {"interval": "1d"},
    "trigger_config": {"hours": 0, "minutes": 0, "execute_now": True},
    "max_retries": 3
}
job2 = create_job(test2)
if job2:
    job_id2 = job2.get("job_id")
    print(f"  ✓ Created: {job_id2}")
    trigger_result = trigger_job(job_id2)
    if trigger_result:
        print(f"  ✓ Triggered execution")
        test_results.append(("Test 2: Crypto Full History", True))
    else:
        test_results.append(("Test 2: Crypto Full History", False))
else:
    test_results.append(("Test 2: Crypto Full History", False))

# Test 3: Forex - Full History
print("\n[Test 3] Forex - Full History (EUR/USD)")
test3 = {
    "asset_type": "forex",
    "symbol": "EUR/USD",
    "trigger_type": "interval",
    "start_date": str(start_date_30d),
    "end_date": str(end_date),
    "collector_kwargs": {},
    "trigger_config": {"hours": 0, "minutes": 0, "execute_now": True},
    "max_retries": 3
}
job3 = create_job(test3)
if job3:
    job_id3 = job3.get("job_id")
    print(f"  ✓ Created: {job_id3}")
    trigger_result = trigger_job(job_id3)
    if trigger_result:
        print(f"  ✓ Triggered execution")
        test_results.append(("Test 3: Forex Full History", True))
    else:
        test_results.append(("Test 3: Forex Full History", False))
else:
    test_results.append(("Test 3: Forex Full History", False))

# Test 4: Bond - Full History
print("\n[Test 4] Bond - Full History (DGS10)")
test4 = {
    "asset_type": "bond",
    "symbol": "DGS10",
    "trigger_type": "interval",
    "start_date": str(start_date_30d),
    "end_date": str(end_date),
    "collector_kwargs": {},
    "trigger_config": {"hours": 0, "minutes": 0, "execute_now": True},
    "max_retries": 3
}
job4 = create_job(test4)
if job4:
    job_id4 = job4.get("job_id")
    print(f"  ✓ Created: {job_id4}")
    trigger_result = trigger_job(job_id4)
    if trigger_result:
        print(f"  ✓ Triggered execution")
        test_results.append(("Test 4: Bond Full History", True))
    else:
        test_results.append(("Test 4: Bond Full History", False))
else:
    test_results.append(("Test 4: Bond Full History", False))

# Test 5: Economic Indicator - Full History
print("\n[Test 5] Economic Indicator - Full History (GDP)")
test5 = {
    "asset_type": "economic_indicator",
    "symbol": "GDP",
    "trigger_type": "interval",
    "start_date": str(start_date_30d),
    "end_date": str(end_date),
    "collector_kwargs": {},
    "trigger_config": {"hours": 0, "minutes": 0, "execute_now": True},
    "max_retries": 3
}
job5 = create_job(test5)
if job5:
    job_id5 = job5.get("job_id")
    print(f"  ✓ Created: {job_id5}")
    trigger_result = trigger_job(job_id5)
    if trigger_result:
        print(f"  ✓ Triggered execution")
        test_results.append(("Test 5: Economic Indicator Full History", True))
    else:
        test_results.append(("Test 5: Economic Indicator Full History", False))
else:
    test_results.append(("Test 5: Economic Indicator Full History", False))

# ============================================================================
# CATEGORY 2: INCREMENTAL JOBS
# ============================================================================
print("\n" + "="*70)
print("CATEGORY 2: INCREMENTAL JOBS")
print("="*70)

# Test 6: Stock - Incremental (no date range)
print("\n[Test 6] Stock - Incremental Mode (MSFT)")
test6 = {
    "asset_type": "stock",
    "symbol": "MSFT",
    "trigger_type": "interval",
    # No start_date/end_date = incremental mode
    "collector_kwargs": {"interval": "1d"},
    "trigger_config": {"hours": 0, "minutes": 0, "execute_now": True},
    "max_retries": 3
}
job6 = create_job(test6)
if job6:
    job_id6 = job6.get("job_id")
    print(f"  ✓ Created: {job_id6}")
    trigger_result = trigger_job(job_id6)
    if trigger_result:
        print(f"  ✓ Triggered execution")
        test_results.append(("Test 6: Stock Incremental", True))
    else:
        test_results.append(("Test 6: Stock Incremental", False))
else:
    test_results.append(("Test 6: Stock Incremental", False))

# Test 7: Crypto - Incremental
print("\n[Test 7] Crypto - Incremental Mode (ETH-USD)")
test7 = {
    "asset_type": "crypto",
    "symbol": "ETH-USD",
    "trigger_type": "interval",
    "collector_kwargs": {"interval": "1d"},
    "trigger_config": {"hours": 0, "minutes": 0, "execute_now": True},
    "max_retries": 3
}
job7 = create_job(test7)
if job7:
    job_id7 = job7.get("job_id")
    print(f"  ✓ Created: {job_id7}")
    trigger_result = trigger_job(job_id7)
    if trigger_result:
        print(f"  ✓ Triggered execution")
        test_results.append(("Test 7: Crypto Incremental", True))
    else:
        test_results.append(("Test 7: Crypto Incremental", False))
else:
    test_results.append(("Test 7: Crypto Incremental", False))

# ============================================================================
# CATEGORY 3: SCHEDULED JOBS
# ============================================================================
print("\n" + "="*70)
print("CATEGORY 3: SCHEDULED JOBS")
print("="*70)

# Test 8: Interval Schedule (every 1 hour)
print("\n[Test 8] Interval Schedule - Every 1 Hour (GOOGL)")
test8 = {
    "asset_type": "stock",
    "symbol": "GOOGL",
    "trigger_type": "interval",
    "collector_kwargs": {"interval": "1d"},
    "trigger_config": {"hours": 1, "minutes": 0, "execute_now": False},
    "max_retries": 3
}
job8 = create_job(test8)
if job8:
    job_id8 = job8.get("job_id")
    print(f"  ✓ Created: {job_id8}")
    test_results.append(("Test 8: Interval Schedule", True))
else:
    test_results.append(("Test 8: Interval Schedule", False))

# Test 9: Cron Schedule (daily at 9 AM)
print("\n[Test 9] Cron Schedule - Daily at 9 AM (AMZN)")
test9 = {
    "asset_type": "stock",
    "symbol": "AMZN",
    "trigger_type": "cron",
    "collector_kwargs": {"interval": "1d"},
    "trigger_config": {"hour": "9", "minute": "0", "second": "0", "execute_now": False},
    "max_retries": 3
}
job9 = create_job(test9)
if job9:
    job_id9 = job9.get("job_id")
    print(f"  ✓ Created: {job_id9}")
    test_results.append(("Test 9: Cron Schedule", True))
else:
    test_results.append(("Test 9: Cron Schedule", False))

# Test 10: Pause and Resume
print("\n[Test 10] Pause and Resume Job")
if job8:
    # Pause
    pause_url = f"{API_BASE}/scheduler/jobs/{job_id8}/pause"
    pause_resp = requests.post(pause_url)
    if pause_resp.status_code == 200:
        print(f"  ✓ Paused job: {job_id8}")
        # Resume
        resume_url = f"{API_BASE}/scheduler/jobs/{job_id8}/resume"
        resume_resp = requests.post(resume_url)
        if resume_resp.status_code == 200:
            print(f"  ✓ Resumed job: {job_id8}")
            test_results.append(("Test 10: Pause/Resume", True))
        else:
            test_results.append(("Test 10: Pause/Resume", False))
    else:
        test_results.append(("Test 10: Pause/Resume", False))
else:
    test_results.append(("Test 10: Pause/Resume", False))

# ============================================================================
# CATEGORY 4: ADVANCED FEATURES
# ============================================================================
print("\n" + "="*70)
print("CATEGORY 4: ADVANCED FEATURES")
print("="*70)

# Test 11: Job Dependencies
print("\n[Test 11] Job Dependencies")
# Create a parent job first
parent_job = {
    "asset_type": "stock",
    "symbol": "TSLA",
    "trigger_type": "interval",
    "collector_kwargs": {"interval": "1d"},
    "trigger_config": {"hours": 1, "minutes": 0, "execute_now": False},
    "max_retries": 3
}
parent = create_job(parent_job)
if parent:
    parent_id = parent.get("job_id")
    print(f"  ✓ Created parent job: {parent_id}")
    # Create dependent job
    dependent_job = {
        "asset_type": "stock",
        "symbol": "NVDA",
        "trigger_type": "interval",
        "collector_kwargs": {"interval": "1d"},
        "trigger_config": {"hours": 1, "minutes": 0, "execute_now": False},
        "dependencies": [{"job_id": parent_id, "required_status": "completed"}],
        "max_retries": 3
    }
    dependent = create_job(dependent_job)
    if dependent:
        dep_id = dependent.get("job_id")
        print(f"  ✓ Created dependent job: {dep_id}")
        test_results.append(("Test 11: Job Dependencies", True))
    else:
        test_results.append(("Test 11: Job Dependencies", False))
else:
    test_results.append(("Test 11: Job Dependencies", False))

# Test 12: Retry Configuration
print("\n[Test 12] Retry Configuration")
retry_job = {
    "asset_type": "stock",
    "symbol": "META",
    "trigger_type": "interval",
    "collector_kwargs": {"interval": "1d"},
    "trigger_config": {"hours": 0, "minutes": 0, "execute_now": True},
    "max_retries": 5,
    "retry_delay_seconds": 30,
    "retry_backoff_multiplier": 1.5
}
retry_job_obj = create_job(retry_job)
if retry_job_obj:
    retry_id = retry_job_obj.get("job_id")
    print(f"  ✓ Created job with custom retry config: {retry_id}")
    # Verify retry config
    job_details = get_job(retry_id)
    if job_details:
        max_retries = job_details.get("max_retries")
        retry_delay = job_details.get("retry_delay_seconds")
        backoff = job_details.get("retry_backoff_multiplier")
        if max_retries == 5 and retry_delay == 30 and backoff == 1.5:
            print(f"  ✓ Retry config verified: max={max_retries}, delay={retry_delay}, backoff={backoff}")
            test_results.append(("Test 12: Retry Configuration", True))
        else:
            print(f"  ✗ Retry config mismatch")
            test_results.append(("Test 12: Retry Configuration", False))
    else:
        test_results.append(("Test 12: Retry Configuration", False))
else:
    test_results.append(("Test 12: Retry Configuration", False))

# Test 13: Job Templates
print("\n[Test 13] Job Templates")
template = {
    "name": "Daily Stock Collection",
    "description": "Template for daily stock data collection",
    "asset_type": "stock",
    "trigger_type": "cron",
    "trigger_config": {"hour": "9", "minute": "0", "second": "0", "execute_now": False},
    "collector_kwargs": {"interval": "1d"},
    "is_public": True,
    "max_retries": 3
}
template_url = f"{API_BASE}/scheduler/templates"
template_resp = requests.post(template_url, json=template)
if template_resp.status_code == 201:
    template_data = template_resp.json()
    template_id = template_data.get("data", {}).get("template_id") or template_data.get("template_id")
    print(f"  ✓ Created template: {template_id}")
    # List templates
    list_resp = requests.get(template_url, params={"is_public": True})
    if list_resp.status_code == 200:
        templates = list_resp.json()
        templates_list = templates if isinstance(templates, list) else templates.get("data", [])
        print(f"  ✓ Found {len(templates_list)} public templates")
        test_results.append(("Test 13: Job Templates", True))
    else:
        test_results.append(("Test 13: Job Templates", False))
else:
    print(f"  ✗ Template creation failed: {template_resp.status_code}")
    test_results.append(("Test 13: Job Templates", False))

# Test 14: Bulk Job Creation
print("\n[Test 14] Bulk Job Creation")
bulk_symbols = ["JPM", "V", "JNJ"]
bulk_jobs = []
for symbol in bulk_symbols:
    bulk_job = {
        "asset_type": "stock",
        "symbol": symbol,
        "trigger_type": "interval",
        "collector_kwargs": {"interval": "1d"},
        "trigger_config": {"hours": 2, "minutes": 0, "execute_now": False},
        "max_retries": 3
    }
    job_obj = create_job(bulk_job)
    if job_obj:
        bulk_jobs.append(job_obj.get("job_id"))
if len(bulk_jobs) == len(bulk_symbols):
    print(f"  ✓ Created {len(bulk_jobs)} jobs in bulk: {', '.join(bulk_jobs)}")
    test_results.append(("Test 14: Bulk Job Creation", True))
else:
    print(f"  ✗ Only created {len(bulk_jobs)}/{len(bulk_symbols)} jobs")
    test_results.append(("Test 14: Bulk Job Creation", False))

# ============================================================================
# CATEGORY 5: EDGE CASES
# ============================================================================
print("\n" + "="*70)
print("CATEGORY 5: EDGE CASES")
print("="*70)

# Test 15: Invalid Symbol Handling
print("\n[Test 15] Invalid Symbol Handling")
invalid_job = {
    "asset_type": "stock",
    "symbol": "INVALID_SYMBOL_XYZ123",
    "trigger_type": "interval",
    "collector_kwargs": {"interval": "1d"},
    "trigger_config": {"hours": 0, "minutes": 0, "execute_now": True},
    "max_retries": 3
}
invalid_result = create_job(invalid_job)
if invalid_result:
    invalid_id = invalid_result.get("job_id")
    print(f"  ✓ Job created (will fail on execution): {invalid_id}")
    trigger_invalid = trigger_job(invalid_id)
    if trigger_invalid:
        print(f"  ✓ Job triggered (expected to fail)")
        # Wait and check execution status
        time.sleep(5)
        executions = get_job_executions(invalid_id)
        if executions:
            latest = executions[0]
            status = latest.get("status")
            if status == "failed":
                print(f"  ✓ Job failed as expected: {status}")
                test_results.append(("Test 15: Invalid Symbol Handling", True))
            else:
                print(f"  ⚠ Unexpected status: {status}")
                test_results.append(("Test 15: Invalid Symbol Handling", False))
        else:
            test_results.append(("Test 15: Invalid Symbol Handling", False))
    else:
        test_results.append(("Test 15: Invalid Symbol Handling", False))
else:
    # Job creation might fail validation
    print(f"  ✓ Job creation rejected (expected behavior)")
    test_results.append(("Test 15: Invalid Symbol Handling", True))

# Test 16: Date Range Validation
print("\n[Test 16] Date Range Validation")
# Try to create job with invalid date range (end before start)
invalid_dates = {
    "asset_type": "stock",
    "symbol": "AAPL",
    "trigger_type": "interval",
    "start_date": str(end_date),
    "end_date": str(start_date_30d),  # End before start
    "collector_kwargs": {"interval": "1d"},
    "trigger_config": {"hours": 0, "minutes": 0, "execute_now": True},
    "max_retries": 3
}
invalid_date_result = create_job(invalid_dates)
if invalid_date_result is None:
    print(f"  ✓ Invalid date range rejected (expected behavior)")
    test_results.append(("Test 16: Date Range Validation", True))
else:
    print(f"  ✗ Invalid date range accepted (unexpected)")
    test_results.append(("Test 16: Date Range Validation", False))

# Test 17: Concurrent Job Execution
print("\n[Test 17] Concurrent Job Execution")
concurrent_symbols = ["SPY", "QQQ", "DIA"]
concurrent_jobs = []
for symbol in concurrent_symbols:
    concurrent_job = {
        "asset_type": "stock",
        "symbol": symbol,
        "trigger_type": "interval",
        "collector_kwargs": {"interval": "1d"},
        "trigger_config": {"hours": 0, "minutes": 0, "execute_now": True},
        "max_retries": 3
    }
    job_obj = create_job(concurrent_job)
    if job_obj:
        concurrent_jobs.append(job_obj.get("job_id"))
        trigger_job(job_obj.get("job_id"))

if len(concurrent_jobs) == len(concurrent_symbols):
    print(f"  ✓ Created and triggered {len(concurrent_jobs)} concurrent jobs")
    time.sleep(3)
    # Check execution status
    all_triggered = True
    for job_id in concurrent_jobs:
        executions = get_job_executions(job_id)
        if not executions:
            all_triggered = False
    if all_triggered:
        print(f"  ✓ All concurrent jobs have execution records")
        test_results.append(("Test 17: Concurrent Job Execution", True))
    else:
        print(f"  ⚠ Some jobs missing execution records")
        test_results.append(("Test 17: Concurrent Job Execution", False))
else:
    test_results.append(("Test 17: Concurrent Job Execution", False))

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)

passed = sum(1 for _, result in test_results if result)
total = len(test_results)

for test_name, result in test_results:
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"{status}: {test_name}")

print("\n" + "="*70)
print(f"Total: {passed}/{total} tests passed")
print("="*70)

# Get final job count
jobs_url = f"{API_BASE}/scheduler/jobs"
jobs_resp = requests.get(jobs_url)
if jobs_resp.status_code == 200:
    jobs_data = jobs_resp.json()
    jobs = jobs_data if isinstance(jobs_data, list) else jobs_data.get("data", [])
    print(f"\nTotal jobs in system: {len(jobs)}")

# Get collection logs
logs = get_collection_logs(limit=50)
print(f"Recent collection logs: {len(logs)}")

sys.exit(0 if passed == total else 1)

