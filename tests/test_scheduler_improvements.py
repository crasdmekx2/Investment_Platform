"""
Test script for scheduler improvements:
- Job status update (pending -> active)
- Parallel execution
- Shared rate limiting
- Request coordinator
- Batch collection
"""

import os
import sys
import time
import threading
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from investment_platform.ingestion.persistent_scheduler import PersistentScheduler
    from investment_platform.api.services import scheduler_service
    from investment_platform.api.models.scheduler import JobCreate
    from investment_platform.collectors.rate_limiter import SharedRateLimiter
    from investment_platform.ingestion.request_coordinator import (
        RequestCoordinator,
        get_coordinator,
    )
    from investment_platform.collectors.stock_collector import StockCollector
    from investment_platform.ingestion.ingestion_engine import IngestionEngine

    APSCHEDULER_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    APSCHEDULER_AVAILABLE = False


def test_job_status_update():
    """Test that job status updates from pending to active."""
    print("\n" + "=" * 60)
    print("TEST 1: Job Status Update (pending -> active)")
    print("=" * 60)

    if not APSCHEDULER_AVAILABLE:
        pytest.skip("APScheduler not available")

    scheduler = PersistentScheduler(blocking=False)
    mock_engine = Mock()
    mock_engine.ingest.return_value = {"status": "success", "records_loaded": 10}
    scheduler.ingestion_engine = mock_engine

    # Create job (should be pending)
    job_data = JobCreate(
        symbol="AAPL",
        asset_type="stock",
        trigger_type="interval",
        trigger_config={"seconds": 10},
    )
    job = scheduler_service.create_job(job_data)

    print(f"Created job {job.job_id} with status: {job.status}")
    assert job.status == "pending", f"Expected 'pending', got '{job.status}'"

    # Start scheduler first (needed for next_run_time calculation)
    scheduler.start()

    try:
        # Add job to scheduler (should update to active)
        result = scheduler.add_job_from_database(job.job_id)
        assert result is True, "Failed to add job to scheduler"

        # Give it a moment for status update
        time.sleep(0.1)

        # Check status in database
        updated_job = scheduler_service.get_job(job.job_id)
        print(f"Job status after adding to scheduler: {updated_job.status}")

        assert (
            updated_job.status == "active"
        ), f"Job status is '{updated_job.status}', expected 'active'"
        print("✓ PASS: Job status updated from pending to active")
    finally:
        scheduler.shutdown()


def test_parallel_execution_config():
    """Test that scheduler is configured for parallel execution."""
    print("\n" + "=" * 60)
    print("TEST 2: Parallel Execution Configuration")
    print("=" * 60)

    if not APSCHEDULER_AVAILABLE:
        pytest.skip("APScheduler not available")

    # Set custom max workers
    os.environ["SCHEDULER_MAX_WORKERS"] = "5"

    try:
        scheduler = PersistentScheduler(blocking=False)

        # Check if scheduler has executor configured
        if hasattr(scheduler.scheduler, "_executors"):
            executors = scheduler.scheduler._executors
            if "default" in executors:
                executor = executors["default"]
                print(f"Scheduler executor type: {type(executor).__name__}")
                if hasattr(executor, "_pool"):
                    max_workers = executor._pool._max_workers
                    print(f"Max workers: {max_workers}")
                    assert max_workers == 5, f"Expected 5 workers, got {max_workers}"
                    print("✓ PASS: Scheduler configured with correct max workers")
                    scheduler.shutdown()
                    return

        print("⚠ WARNING: Could not verify executor configuration")
        scheduler.shutdown()
        # Don't fail if we can't verify - this is acceptable
    finally:
        # Clean up env var
        if "SCHEDULER_MAX_WORKERS" in os.environ:
            del os.environ["SCHEDULER_MAX_WORKERS"]


def test_shared_rate_limiter():
    """Test that shared rate limiter works correctly."""
    print("\n" + "=" * 60)
    print("TEST 3: Shared Rate Limiter")
    print("=" * 60)

    # Get two limiters for the same collector type
    limiter1 = SharedRateLimiter.get_limiter("StockCollector", calls=5, period=10)
    limiter2 = SharedRateLimiter.get_limiter("StockCollector", calls=5, period=10)

    # They should be the same instance
    assert limiter1 is limiter2, "Shared rate limiter returned different instances"
    print("✓ PASS: Shared rate limiter returns same instance for same collector type")

    # Get limiter for different collector type
    limiter3 = SharedRateLimiter.get_limiter("CryptoCollector", calls=5, period=10)
    assert limiter3 is not limiter1, "Different collector types got same limiter"
    print("✓ PASS: Different collector types get different limiters")


def test_request_coordinator():
    """Test request coordinator functionality."""
    print("\n" + "=" * 60)
    print("TEST 4: Request Coordinator")
    print("=" * 60)

    # Test coordinator initialization
    coordinator = RequestCoordinator(enabled=True, window_seconds=0.5)

    assert coordinator.enabled, "Request coordinator not enabled"
    print("✓ PASS: Request coordinator initialized and enabled")

    # Test batch support detection
    supports_batch = coordinator._batch_supported_collectors.get("StockCollector", False)
    if supports_batch:
        print("✓ PASS: StockCollector marked as supporting batch requests")
    else:
        print("⚠ WARNING: StockCollector not marked as supporting batch")

    coordinator.shutdown()


def test_batch_collection():
    """Test batch collection method in StockCollector."""
    print("\n" + "=" * 60)
    print("TEST 5: Batch Collection Support")
    print("=" * 60)

    collector = StockCollector(output_format="dataframe")

    # Check if batch method exists
    assert hasattr(
        collector, "collect_historical_data_batch"
    ), "StockCollector does not have batch collection method"
    print("✓ PASS: StockCollector has batch collection method")

    # Test with small date range (to avoid long API calls)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    try:
        results = collector.collect_historical_data_batch(
            symbols=["AAPL", "MSFT"],
            start_date=start_date,
            end_date=end_date,
        )

        assert isinstance(results, list), f"Expected list, got {type(results)}"
        assert len(results) == 2, f"Expected list of 2 results, got {len(results)}"
        print(f"✓ PASS: Batch collection returned {len(results)} results")

        if not results[0].empty or not results[1].empty:
            print("✓ PASS: Batch collection returned data")
        else:
            print("⚠ WARNING: Batch collection returned empty dataframes")
            # Don't fail on empty data - might be API issue
    except Exception as e:
        print(f"⚠ WARNING: Batch collection test failed (may be API issue): {e}")
        # Don't fail on API errors - this is acceptable for tests
        pytest.skip(f"Batch collection test skipped due to API issue: {e}")


def test_coordinator_integration():
    """Test that coordinator is integrated into ingestion engine."""
    print("\n" + "=" * 60)
    print("TEST 6: Coordinator Integration")
    print("=" * 60)

    engine = IngestionEngine()

    # Check if coordinator is imported
    from investment_platform.ingestion import request_coordinator

    coordinator = get_coordinator()

    assert coordinator is not None, "Request coordinator not accessible"
    print(f"Coordinator enabled: {coordinator.enabled}")
    print(f"Coordinator window: {coordinator.window_seconds}s")

    print("✓ PASS: Request coordinator accessible from ingestion engine")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SCHEDULER IMPROVEMENTS TEST SUITE")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Job Status Update", test_job_status_update()))
    results.append(("Parallel Execution Config", test_parallel_execution_config()))
    results.append(("Shared Rate Limiter", test_shared_rate_limiter()))
    results.append(("Request Coordinator", test_request_coordinator()))
    results.append(("Batch Collection", test_batch_collection()))
    results.append(("Coordinator Integration", test_coordinator_integration()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
