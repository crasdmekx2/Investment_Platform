#!/usr/bin/env python3
"""
Script to create test jobs for scheduler functionality testing.
This automates job creation via API to complete the full test plan.
"""

import requests
import json
from datetime import datetime, timedelta
import time

API_BASE = "http://localhost:8000/api"

def create_job(job_config):
    """Create a scheduled job via API."""
    url = f"{API_BASE}/scheduler/jobs"
    response = requests.post(url, json=job_config)
    if response.status_code == 201:
        data = response.json()
        # Handle both direct object and wrapped in "data" key
        if "data" in data:
            return data["data"]
        return data
    else:
        print(f"Error creating job: {response.status_code} - {response.text}")
        return None

def get_jobs():
    """Get all scheduled jobs."""
    url = f"{API_BASE}/scheduler/jobs"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        # Handle both list and dict responses
        if isinstance(data, list):
            return data
        elif "data" in data:
            return data["data"]
        return data
    return []

# Calculate dates
end_date = datetime.now().date()
start_date = end_date - timedelta(days=30)

# Test 1: Stock - Full History with Date Range
print("Creating Test 1: Stock - Full History (AAPL)")
test1 = {
    "asset_type": "stock",
    "symbol": "AAPL",
    "trigger_type": "interval",
    "start_date": str(start_date),
    "end_date": str(end_date),
    "collector_kwargs": {
        "interval": "1d"
    },
    "trigger_config": {
        "hours": 0,
        "minutes": 0,
        "execute_now": True
    },
    "max_retries": 3,
    "retry_delay_seconds": 60,
    "retry_backoff_multiplier": 2.0
}
job1 = create_job(test1)
if job1:
    print(f"✓ Created job: {job1.get('job_id')}")

# Test 2: Crypto - Full History
print("\nCreating Test 2: Crypto - Full History (BTC-USD)")
test2 = {
    "asset_type": "crypto",
    "symbol": "BTC-USD",
    "trigger_type": "interval",
    "start_date": str(start_date),
    "end_date": str(end_date),
    "collector_kwargs": {
        "interval": "1d"
    },
    "trigger_config": {
        "hours": 0,
        "minutes": 0,
        "execute_now": True
    },
    "max_retries": 3,
    "retry_delay_seconds": 60,
    "retry_backoff_multiplier": 2.0
}
job2 = create_job(test2)
if job2:
    print(f"✓ Created job: {job2.get('job_id')}")

# Test 3: Forex - Full History
print("\nCreating Test 3: Forex - Full History (EUR/USD)")
test3 = {
    "asset_type": "forex",
    "symbol": "EUR/USD",
    "trigger_type": "interval",
    "start_date": str(start_date),
    "end_date": str(end_date),
    "collector_kwargs": {},
    "trigger_config": {
        "hours": 0,
        "minutes": 0,
        "execute_now": True
    },
    "max_retries": 3,
    "retry_delay_seconds": 60,
    "retry_backoff_multiplier": 2.0
}
job3 = create_job(test3)
if job3:
    print(f"✓ Created job: {job3.get('job_id')}")

# Test 4: Bond - Full History
print("\nCreating Test 4: Bond - Full History (10-Year Treasury)")
test4 = {
    "asset_type": "bond",
    "symbol": "DGS10",
    "trigger_type": "interval",
    "start_date": str(start_date),
    "end_date": str(end_date),
    "collector_kwargs": {},
    "trigger_config": {
        "hours": 0,
        "minutes": 0,
        "execute_now": True
    },
    "max_retries": 3,
    "retry_delay_seconds": 60,
    "retry_backoff_multiplier": 2.0
}
job4 = create_job(test4)
if job4:
    print(f"✓ Created job: {job4.get('job_id')}")

# Test 5: Economic Indicator - Full History
print("\nCreating Test 5: Economic Indicator - Full History (GDP)")
test5 = {
    "asset_type": "economic_indicator",
    "symbol": "GDP",
    "trigger_type": "interval",
    "start_date": str(start_date),
    "end_date": str(end_date),
    "collector_kwargs": {},
    "trigger_config": {
        "hours": 0,
        "minutes": 0,
        "execute_now": True
    },
    "max_retries": 3,
    "retry_delay_seconds": 60,
    "retry_backoff_multiplier": 2.0
}
job5 = create_job(test5)
if job5:
    print(f"✓ Created job: {job5.get('job_id')}")

print("\n" + "="*50)
print("All test jobs created. Checking job status...")
print("="*50)

# Wait a moment for jobs to be processed
time.sleep(2)

jobs = get_jobs()
print(f"\nTotal jobs created: {len(jobs)}")
for job in jobs:
    print(f"  - {job.get('job_id')}: {job.get('asset_type')} - {job.get('symbol')} - Status: {job.get('status')}")

