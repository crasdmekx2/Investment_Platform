#!/usr/bin/env python3
"""
Passing scheduler API tests - tests that are working correctly.
These tests verify basic job CRUD operations and configuration.
"""

import requests
import json
import time
import psycopg2
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
import sys
import os

# Configuration
API_BASE_URL = "http://localhost:8000/api"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "investment_platform",
    "user": "postgres",
    "password": "postgres"
}

# Test results storage
test_results = []
current_test = None


class TestResult:
    """Store test result information."""
    def __init__(self, test_id: str, test_name: str):
        self.test_id = test_id
        self.test_name = test_name
        self.status = "PENDING"
        self.start_time = None
        self.end_time = None
        self.error_message = None
        self.verification_results = {}
        self.job_id = None
        self.execution_id = None
        self.log_id = None
        self.records_collected = 0
        self.data_verification = {}

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else None,
            "error_message": self.error_message,
            "verification_results": self.verification_results,
            "job_id": self.job_id,
            "execution_id": self.execution_id,
            "log_id": self.log_id,
            "records_collected": self.records_collected,
            "data_verification": self.data_verification,
        }


def log_test_start(test_id: str, test_name: str):
    """Start a new test."""
    global current_test
    current_test = TestResult(test_id, test_name)
    current_test.start_time = datetime.now()
    print(f"\n{'='*80}")
    print(f"TEST {test_id}: {test_name}")
    print(f"{'='*80}")


def log_test_pass():
    """Mark current test as passed."""
    global current_test
    if current_test:
        current_test.status = "PASS"
        current_test.end_time = datetime.now()
        test_results.append(current_test)
        duration = (current_test.end_time - current_test.start_time).total_seconds()
        print(f"✅ PASSED ({duration:.2f}s)")
        current_test = None


def log_test_fail(error_message: str):
    """Mark current test as failed."""
    global current_test
    if current_test:
        current_test.status = "FAIL"
        current_test.error_message = error_message
        current_test.end_time = datetime.now()
        test_results.append(current_test)
        duration = (current_test.end_time - current_test.start_time).total_seconds()
        print(f"❌ FAILED ({duration:.2f}s): {error_message}")
        current_test = None


def log_test_skip(reason: str):
    """Mark current test as skipped."""
    global current_test
    if current_test:
        current_test.status = "SKIP"
        current_test.error_message = f"Skipped: {reason}"
        current_test.end_time = datetime.now()
        test_results.append(current_test)
        print(f"⏭️  SKIPPED: {reason}")
        current_test = None


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)


def cleanup_database():
    """Clean up all jobs, executions, and collection logs."""
    print("\n" + "="*80)
    print("CLEANUP: Removing all jobs, executions, and collection logs")
    print("="*80)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete in order to respect foreign key constraints
        cursor.execute("DELETE FROM scheduler_job_executions")
        print(f"  Deleted {cursor.rowcount} execution records")
        
        cursor.execute("DELETE FROM job_dependencies")
        print(f"  Deleted {cursor.rowcount} dependency records")
        
        cursor.execute("DELETE FROM scheduler_jobs")
        print(f"  Deleted {cursor.rowcount} job records")
        
        cursor.execute("DELETE FROM data_collection_log")
        print(f"  Deleted {cursor.rowcount} collection log records")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        raise


def api_create_job(job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a job via API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/scheduler/jobs",
            json=job_data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  API Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"  Response: {e.response.text}")
        return None


def api_get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get a job via API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/scheduler/jobs/{job_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  API Error: {e}")
        return None


def api_update_job(job_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a job via API."""
    try:
        response = requests.put(
            f"{API_BASE_URL}/scheduler/jobs/{job_id}",
            json=update_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  API Error: {e}")
        return None


def api_delete_job(job_id: str) -> bool:
    """Delete a job via API."""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/scheduler/jobs/{job_id}",
            timeout=10
        )
        return response.status_code == 204
    except requests.exceptions.RequestException as e:
        print(f"  API Error: {e}")
        return False


def api_pause_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Pause a job via API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/scheduler/jobs/{job_id}/pause",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  API Error: {e}")
        return None


def api_resume_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Resume a job via API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/scheduler/jobs/{job_id}/resume",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  API Error: {e}")
        return None


# ============================================================================
# TEST SCENARIOS
# ============================================================================

def test_1_stock_full_history():
    """Test 1: Stock - Full History with Date Range"""
    log_test_start("TEST-001", "Stock - Full History with Date Range")
    
    try:
        # Use dates that are at least 3 days in the past to ensure market data is available
        # Market data APIs typically have a 1-2 day delay
        end_date = datetime.now(timezone.utc) - timedelta(days=3)
        start_date = end_date - timedelta(days=60)  # 60 days of historical data
        
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"execute_now": True},
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "collector_kwargs": {"interval": "1d"},
        }
        
        job = api_create_job(job_data)
        if not job:
            log_test_fail("Failed to create job")
            return
        
        current_test.job_id = job["job_id"]
        current_test.verification_results["job_created"] = True
        
        # Trigger job
        trigger_result = api_trigger_job(job["job_id"])
        if not trigger_result:
            log_test_fail("Failed to trigger job")
            return
        
        # Wait for execution
        execution = wait_for_execution(job["job_id"], timeout=180)
        if not execution:
            log_test_fail("Execution did not complete within timeout")
            return
        
        # Verify execution
        exec_verification = verify_execution_success(job["job_id"])
        current_test.verification_results["execution"] = exec_verification
        
        if exec_verification["status"] != "PASS":
            log_test_fail(exec_verification.get("error", "Execution verification failed"))
            return
        
        # Verify data
        data_verification = verify_data_collection(
            "stock", "AAPL", start_date, end_date, expected_min_records=1
        )
        current_test.data_verification = data_verification
        
        if data_verification["status"] != "PASS":
            log_test_fail(data_verification.get("error", "Data verification failed"))
            return
        
        log_test_pass()
        
    except Exception as e:
        log_test_fail(f"Unexpected error: {e}")


def test_2_crypto_full_history():
    """Test 2: Crypto - Full History with Granularity"""
    log_test_start("TEST-002", "Crypto - Full History with Granularity")
    
    try:
        # Use dates that are at least 1 day in the past
        end_date = datetime.now(timezone.utc) - timedelta(days=1)
        start_date = end_date - timedelta(days=7)
        
        job_data = {
            "symbol": "BTC-USD",
            "asset_type": "crypto",
            "trigger_type": "interval",
            "trigger_config": {"execute_now": True},
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "collector_kwargs": {"granularity": "ONE_HOUR"},
        }
        
        job = api_create_job(job_data)
        if not job:
            log_test_fail("Failed to create job")
            return
        
        current_test.job_id = job["job_id"]
        
        trigger_result = api_trigger_job(job["job_id"])
        if not trigger_result:
            log_test_fail("Failed to trigger job")
            return
        
        execution = wait_for_execution(job["job_id"], timeout=180)
        if not execution:
            log_test_fail("Execution did not complete within timeout")
            return
        
        exec_verification = verify_execution_success(job["job_id"])
        current_test.verification_results["execution"] = exec_verification
        
        if exec_verification["status"] != "PASS":
            log_test_fail(exec_verification.get("error", "Execution verification failed"))
            return
        
        data_verification = verify_data_collection(
            "crypto", "BTC-USD", start_date, end_date, expected_min_records=1
        )
        current_test.data_verification = data_verification
        
        if data_verification["status"] != "PASS":
            log_test_fail(data_verification.get("error", "Data verification failed"))
            return
        
        log_test_pass()
        
    except Exception as e:
        log_test_fail(f"Unexpected error: {e}")


def test_13_retry_configuration():
    """Test 13: Retry Configuration"""
    log_test_start("TEST-013", "Retry Configuration")
    
    try:
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"execute_now": True},
            "max_retries": 2,
            "retry_delay_seconds": 30,
            "retry_backoff_multiplier": 1.5,
        }
        
        job = api_create_job(job_data)
        if not job:
            log_test_fail("Failed to create job")
            return
        
        current_test.job_id = job["job_id"]
        
        job_check = api_get_job(job["job_id"])
        if not job_check:
            log_test_fail("Failed to retrieve job")
            return
        
        if job_check.get("max_retries") != 2:
            log_test_fail(f"max_retries is {job_check.get('max_retries')}, expected 2")
            return
        
        if job_check.get("retry_delay_seconds") != 30:
            log_test_fail(f"retry_delay_seconds is {job_check.get('retry_delay_seconds')}, expected 30")
            return
        
        if job_check.get("retry_backoff_multiplier") != 1.5:
            log_test_fail(f"retry_backoff_multiplier is {job_check.get('retry_backoff_multiplier')}, expected 1.5")
            return
        
        current_test.verification_results["retry_config"] = {
            "max_retries": job_check.get("max_retries"),
            "retry_delay_seconds": job_check.get("retry_delay_seconds"),
            "retry_backoff_multiplier": job_check.get("retry_backoff_multiplier"),
        }
        
        log_test_pass()
        
    except Exception as e:
        log_test_fail(f"Unexpected error: {e}")


def test_14_bulk_job_creation():
    """Test 14: Bulk Job Creation"""
    log_test_start("TEST-014", "Bulk Job Creation")
    
    try:
        symbols = ["AAPL", "MSFT", "GOOGL"]
        job_ids = []
        
        for symbol in symbols:
            job_data = {
                "symbol": symbol,
                "asset_type": "stock",
                "trigger_type": "interval",
                "trigger_config": {"execute_now": True},
                "collector_kwargs": {"interval": "1d"},
            }
            
            job = api_create_job(job_data)
            if not job:
                log_test_fail(f"Failed to create job for {symbol}")
                return
            
            job_ids.append(job["job_id"])
        
        # Verify all jobs exist
        for job_id in job_ids:
            job_check = api_get_job(job_id)
            if not job_check:
                log_test_fail(f"Job {job_id} not found")
                return
        
        current_test.verification_results["jobs_created"] = len(job_ids)
        current_test.verification_results["job_ids"] = job_ids
        
        log_test_pass()
        
    except Exception as e:
        log_test_fail(f"Unexpected error: {e}")


def test_15_custom_collector_kwargs():
    """Test 15: Job with Custom Collector Kwargs"""
    log_test_start("TEST-015", "Job with Custom Collector Kwargs")
    
    try:
        # Test stock with 1m interval
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"execute_now": True},
            "collector_kwargs": {"interval": "1m"},
        }
        
        job = api_create_job(job_data)
        if not job:
            log_test_fail("Failed to create job")
            return
        
        current_test.job_id = job["job_id"]
        
        job_check = api_get_job(job["job_id"])
        if not job_check:
            log_test_fail("Failed to retrieve job")
            return
        
        collector_kwargs = job_check.get("collector_kwargs", {})
        if collector_kwargs.get("interval") != "1m":
            log_test_fail(f"Collector kwargs interval is {collector_kwargs.get('interval')}, expected '1m'")
            return
        
        current_test.verification_results["collector_kwargs"] = collector_kwargs
        
        log_test_pass()
        
    except Exception as e:
        log_test_fail(f"Unexpected error: {e}")


def test_16_date_boundaries():
    """Test 16: Job with Start/End Date Boundaries"""
    log_test_start("TEST-016", "Job with Start/End Date Boundaries")
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Test with both dates
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"execute_now": True},
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        
        job = api_create_job(job_data)
        if not job:
            log_test_fail("Failed to create job")
            return
        
        current_test.job_id = job["job_id"]
        
        job_check = api_get_job(job["job_id"])
        if not job_check:
            log_test_fail("Failed to retrieve job")
            return
        
        # Verify dates are stored correctly
        # Parse API response dates (may be timezone-aware)
        job_start_str = job_check["start_date"]
        job_end_str = job_check["end_date"]
        
        # Handle timezone-aware strings
        if job_start_str.endswith("Z"):
            job_start = datetime.fromisoformat(job_start_str.replace("Z", "+00:00"))
        else:
            job_start = datetime.fromisoformat(job_start_str)
        
        if job_end_str.endswith("Z"):
            job_end = datetime.fromisoformat(job_end_str.replace("Z", "+00:00"))
        else:
            job_end = datetime.fromisoformat(job_end_str)
        
        # Make start_date and end_date timezone-aware for comparison
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        # Normalize job dates to UTC for comparison
        if job_start.tzinfo is None:
            job_start = job_start.replace(tzinfo=timezone.utc)
        else:
            job_start = job_start.astimezone(timezone.utc)
        
        if job_end.tzinfo is None:
            job_end = job_end.replace(tzinfo=timezone.utc)
        else:
            job_end = job_end.astimezone(timezone.utc)
        
        if abs((job_start - start_date).total_seconds()) > 60:
            log_test_fail("Start date mismatch")
            return
        
        if abs((job_end - end_date).total_seconds()) > 60:
            log_test_fail("End date mismatch")
            return
        
        current_test.verification_results["dates_stored_correctly"] = True
        
        log_test_pass()
        
    except Exception as e:
        log_test_fail(f"Unexpected error: {e}")


def test_17_status_transitions():
    """Test 17: Job Status Transitions"""
    log_test_start("TEST-017", "Job Status Transitions")
    
    try:
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        job = api_create_job(job_data)
        if not job:
            log_test_fail("Failed to create job")
            return
        
        current_test.job_id = job["job_id"]
        
        # Check initial status (should be pending or active)
        job_check = api_get_job(job["job_id"])
        initial_status = job_check.get("status")
        current_test.verification_results["initial_status"] = initial_status
        
        # Resume to ensure it's active
        resume_result = api_resume_job(job["job_id"])
        if not resume_result:
            log_test_fail("Failed to resume job")
            return
        
        job_check = api_get_job(job["job_id"])
        if job_check.get("status") != "active":
            log_test_fail(f"Status after resume is {job_check.get('status')}, expected 'active'")
            return
        
        current_test.verification_results["after_resume"] = "active"
        
        # Pause job
        pause_result = api_pause_job(job["job_id"])
        if not pause_result:
            log_test_fail("Failed to pause job")
            return
        
        job_check = api_get_job(job["job_id"])
        if job_check.get("status") != "paused":
            log_test_fail(f"Status after pause is {job_check.get('status')}, expected 'paused'")
            return
        
        current_test.verification_results["after_pause"] = "paused"
        
        # Resume again
        resume_result = api_resume_job(job["job_id"])
        if not resume_result:
            log_test_fail("Failed to resume job again")
            return
        
        job_check = api_get_job(job["job_id"])
        if job_check.get("status") != "active":
            log_test_fail(f"Status after second resume is {job_check.get('status')}, expected 'active'")
            return
        
        current_test.verification_results["after_second_resume"] = "active"
        
        log_test_pass()
        
    except Exception as e:
        log_test_fail(f"Unexpected error: {e}")


def test_18_job_update():
    """Test 18: Job Update"""
    log_test_start("TEST-018", "Job Update")
    
    try:
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        job = api_create_job(job_data)
        if not job:
            log_test_fail("Failed to create job")
            return
        
        current_test.job_id = job["job_id"]
        
        # Update job
        update_data = {
            "symbol": "MSFT",
            "trigger_config": {"minutes": 10},
        }
        
        updated_job = api_update_job(job["job_id"], update_data)
        if not updated_job:
            log_test_fail("Failed to update job")
            return
        
        if updated_job.get("symbol") != "MSFT":
            log_test_fail(f"Symbol is {updated_job.get('symbol')}, expected 'MSFT'")
            return
        
        if updated_job.get("trigger_config", {}).get("minutes") != 10:
            log_test_fail(f"Trigger config minutes is {updated_job.get('trigger_config', {}).get('minutes')}, expected 10")
            return
        
        current_test.verification_results["update_successful"] = True
        
        log_test_pass()
        
    except Exception as e:
        log_test_fail(f"Unexpected error: {e}")


def test_19_job_deletion():
    """Test 19: Job Deletion"""
    log_test_start("TEST-019", "Job Deletion")
    
    try:
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        job = api_create_job(job_data)
        if not job:
            log_test_fail("Failed to create job")
            return
        
        job_id = job["job_id"]
        current_test.job_id = job_id
        
        # Delete job
        deleted = api_delete_job(job_id)
        if not deleted:
            log_test_fail("Failed to delete job")
            return
        
        # Verify job is gone
        job_check = api_get_job(job_id)
        if job_check:
            log_test_fail("Job still exists after deletion")
            return
        
        current_test.verification_results["deletion_successful"] = True
        
        log_test_pass()
        
    except Exception as e:
        log_test_fail(f"Unexpected error: {e}")


def test_20_job_templates():
    """Test 20: Job Templates"""
    log_test_start("TEST-020", "Job Templates")
    
    try:
        # Create template
        template_data = {
            "name": "Test Stock Template",
            "description": "Test template for stocks",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"hours": 1},
            "collector_kwargs": {"interval": "1d"},
            "is_public": False,
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/scheduler/templates",
                json=template_data,
                timeout=10
            )
            response.raise_for_status()
            template = response.json()
        except requests.exceptions.RequestException as e:
            log_test_skip(f"Template API not available: {e}")
            return
        
        template_id = template.get("template_id")
        if not template_id:
            log_test_fail("Template ID not returned")
            return
        
        current_test.verification_results["template_created"] = True
        current_test.verification_results["template_id"] = template_id
        
        # List templates
        try:
            response = requests.get(
                f"{API_BASE_URL}/scheduler/templates",
                timeout=10
            )
            response.raise_for_status()
            templates = response.json()
        except requests.exceptions.RequestException as e:
            log_test_fail(f"Failed to list templates: {e}")
            return
        
        if not any(t.get("template_id") == template_id for t in templates):
            log_test_fail("Template not found in list")
            return
        
        current_test.verification_results["template_listed"] = True
        
        log_test_pass()
        
    except Exception as e:
        log_test_fail(f"Unexpected error: {e}")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all passing test scenarios."""
    print("\n" + "="*80)
    print("SCHEDULER API PASSING TESTS SUITE")
    print("="*80)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Start Time: {datetime.now().isoformat()}")
    
    # Cleanup before starting
    cleanup_database()
    
    # Run all passing tests
    test_functions = [
        test_1_stock_full_history,
        test_2_crypto_full_history,
        test_13_retry_configuration,
        test_14_bulk_job_creation,
        test_15_custom_collector_kwargs,
        test_16_date_boundaries,
        test_17_status_transitions,
        test_18_job_update,
        test_19_job_deletion,
        test_20_job_templates,
    ]
    
    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            if current_test:
                log_test_fail(f"Unexpected exception: {e}")
            else:
                print(f"❌ Test function {test_func.__name__} failed with exception: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r.status == "PASS")
    failed = sum(1 for r in test_results if r.status == "FAIL")
    skipped = sum(1 for r in test_results if r.status == "SKIP")
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏭️  Skipped: {skipped}")
    
    if failed > 0:
        print("\nFailed Tests:")
        for result in test_results:
            if result.status == "FAIL":
                print(f"  - {result.test_id}: {result.test_name}")
                if result.error_message:
                    print(f"    Error: {result.error_message}")
    
    # Save results to file
    results_file = f"scheduler-api-passing-test-results-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    results_data = {
        "test_run": {
            "start_time": test_results[0].start_time.isoformat() if test_results else None,
            "end_time": datetime.now().isoformat(),
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        },
        "results": [r.to_dict() for r in test_results]
    }
    
    with open(results_file, "w") as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

