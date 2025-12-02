"""
Tests to verify scheduler calculates dates fresh at execution time.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, call

try:
    from investment_platform.ingestion.scheduler import IngestionScheduler, APSCHEDULER_AVAILABLE
except ImportError:
    APSCHEDULER_AVAILABLE = False
    IngestionScheduler = None


@pytest.mark.skipif(not APSCHEDULER_AVAILABLE, reason="APScheduler not available")
class TestSchedulerDateCalculation:
    """Test that scheduler calculates dates fresh at execution time."""

    def test_job_calculates_dates_at_execution_time(self):
        """Test that dates are calculated fresh each time the job runs."""
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = IngestionScheduler(blocking=False)
        engine_mock = Mock()
        scheduler.ingestion_engine = engine_mock

        # Add job with None dates (should use defaults calculated at runtime)
        trigger = IntervalTrigger(seconds=1)
        job_id = scheduler.add_job(
            symbol="TEST_STOCK",
            asset_type="stock",
            trigger=trigger,
            start_date=None,  # Will be calculated at execution time
            end_date=None,  # Will be calculated at execution time
        )

        # Get the job function
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 1

        # Simulate job execution at different times
        # First execution
        with patch("investment_platform.ingestion.scheduler.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 5, 10, 0, 0)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            jobs[0].func()

            # Verify ingest was called with dates calculated at execution time
            assert engine_mock.ingest.called
            call_args = engine_mock.ingest.call_args
            assert call_args[1]["start_date"] == datetime(2024, 1, 4, 10, 0, 0)  # yesterday
            assert call_args[1]["end_date"] == datetime(2024, 1, 5, 10, 0, 0)  # today

        # Reset mock
        engine_mock.reset_mock()

        # Second execution (simulated later time)
        with patch("investment_platform.ingestion.scheduler.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 6, 10, 0, 0)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            jobs[0].func()

            # Verify dates are recalculated for the new execution time
            assert engine_mock.ingest.called
            call_args = engine_mock.ingest.call_args
            assert call_args[1]["start_date"] == datetime(2024, 1, 5, 10, 0, 0)  # new yesterday
            assert call_args[1]["end_date"] == datetime(2024, 1, 6, 10, 0, 0)  # new today

        scheduler.shutdown()

    def test_job_with_fixed_dates(self):
        """Test that explicitly provided dates are used as-is."""
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = IngestionScheduler(blocking=False)
        engine_mock = Mock()
        scheduler.ingestion_engine = engine_mock

        # Add job with fixed dates
        fixed_start = datetime(2024, 1, 1)
        fixed_end = datetime(2024, 1, 2)

        trigger = IntervalTrigger(seconds=1)
        job_id = scheduler.add_job(
            symbol="TEST_STOCK",
            asset_type="stock",
            trigger=trigger,
            start_date=fixed_start,
            end_date=fixed_end,
        )

        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 1

        # Execute job
        jobs[0].func()

        # Verify fixed dates are used
        assert engine_mock.ingest.called
        call_args = engine_mock.ingest.call_args
        assert call_args[1]["start_date"] == fixed_start
        assert call_args[1]["end_date"] == fixed_end

        scheduler.shutdown()
