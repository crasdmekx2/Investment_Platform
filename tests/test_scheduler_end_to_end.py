"""
End-to-end tests for scheduler workflows.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

try:
    from investment_platform.ingestion.persistent_scheduler import (
        PersistentScheduler,
        APSCHEDULER_AVAILABLE,
    )
    from investment_platform.api.services import scheduler_service
    from investment_platform.api.models.scheduler import JobCreate
except ImportError:
    APSCHEDULER_AVAILABLE = False
    PersistentScheduler = None
    scheduler_service = None
    JobCreate = None


@pytest.mark.skipif(not APSCHEDULER_AVAILABLE, reason="APScheduler not available")
class TestSchedulerEndToEnd:
    """Test complete scheduler workflows."""

    def test_create_job_and_scheduler_runs(self, db_transaction):
        """Test creating a job and scheduler executing it."""
        scheduler = PersistentScheduler(blocking=False)
        mock_engine = Mock()
        mock_engine.ingest.return_value = {
            "status": "success",
            "records_loaded": 100,
            "log_id": 123,
        }
        scheduler.ingestion_engine = mock_engine

        # Create job in database
        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"seconds": 2},  # Run every 2 seconds for testing
        )
        job = scheduler_service.create_job(job_data)

        # Add job to scheduler
        scheduler.add_job_from_database(job.job_id)

        # Start scheduler
        scheduler.start()

        try:
            # Wait for job to execute
            time.sleep(3)

            # Verify job was executed
            assert mock_engine.ingest.called

            # Verify execution was recorded
            executions = scheduler_service.get_job_executions(job.job_id)
            assert len(executions) > 0
            assert any(exec.execution_status == "success" for exec in executions)
        finally:
            scheduler.shutdown()

    def test_multiple_jobs_concurrent(self, db_transaction):
        """Test multiple jobs running concurrently."""
        scheduler = PersistentScheduler(blocking=False)
        mock_engine = Mock()
        mock_engine.ingest.return_value = {
            "status": "success",
            "records_loaded": 50,
        }
        scheduler.ingestion_engine = mock_engine

        # Create multiple jobs
        job_ids = []
        for symbol in ["AAPL", "MSFT", "GOOGL"]:
            job_data = JobCreate(
                symbol=symbol,
                asset_type="stock",
                trigger_type="interval",
                trigger_config={"seconds": 3},
            )
            job = scheduler_service.create_job(job_data)
            job_ids.append(job.job_id)
            scheduler.add_job_from_database(job.job_id)

        scheduler.start()

        try:
            # Wait for jobs to execute
            time.sleep(4)

            # Verify all jobs were executed
            assert mock_engine.ingest.call_count >= len(job_ids)

            # Verify executions recorded for all jobs
            for job_id in job_ids:
                executions = scheduler_service.get_job_executions(job_id)
                assert len(executions) > 0
        finally:
            scheduler.shutdown()

    def test_job_failure_handling(self, db_transaction):
        """Test handling of job failures."""
        scheduler = PersistentScheduler(blocking=False)
        mock_engine = Mock()
        mock_engine.ingest.side_effect = Exception("Test error")
        scheduler.ingestion_engine = mock_engine

        # Create job
        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"seconds": 2},
        )
        job = scheduler_service.create_job(job_data)
        scheduler.add_job_from_database(job.job_id)

        scheduler.start()

        try:
            # Wait for job to execute and fail
            time.sleep(3)

            # Verify execution was recorded with failure status
            executions = scheduler_service.get_job_executions(job.job_id)
            assert len(executions) > 0

            # Check if any execution failed
            failed_executions = [e for e in executions if e.execution_status == "failed"]
            assert len(failed_executions) > 0
            assert failed_executions[0].error_message is not None
        finally:
            scheduler.shutdown()

    def test_scheduler_restart_and_job_reload(self, db_transaction):
        """Test scheduler restart and job reload from database."""
        # Create job in database
        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"seconds": 5},
        )
        job = scheduler_service.create_job(job_data)
        scheduler_service.update_job_status(job.job_id, "active")

        # Create first scheduler instance and load jobs
        scheduler1 = PersistentScheduler(blocking=False)
        scheduler1.ingestion_engine = Mock()
        loaded1 = scheduler1.load_jobs_from_database()
        assert job.job_id in loaded1
        scheduler1.shutdown()

        # Create second scheduler instance and verify jobs reload
        scheduler2 = PersistentScheduler(blocking=False)
        scheduler2.ingestion_engine = Mock()
        loaded2 = scheduler2.load_jobs_from_database()
        assert job.job_id in loaded2

        # Verify job is in scheduler
        jobs = scheduler2.scheduler.get_jobs()
        assert any(j.id == job.job_id for j in jobs)

        scheduler2.shutdown()

    def test_pause_and_resume_workflow(self, db_transaction):
        """Test pausing and resuming jobs."""
        scheduler = PersistentScheduler(blocking=False)
        mock_engine = Mock()
        mock_engine.ingest.return_value = {"status": "success", "records_loaded": 10}
        scheduler.ingestion_engine = mock_engine

        # Create and add job
        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"seconds": 2},
        )
        job = scheduler_service.create_job(job_data)
        scheduler.add_job_from_database(job.job_id)
        scheduler.start()

        try:
            # Let job run once
            time.sleep(3)
            initial_calls = mock_engine.ingest.call_count

            # Pause job
            scheduler.pause_job_in_scheduler(job.job_id)
            scheduler.sync_job_status(job.job_id, "paused")

            # Wait and verify job doesn't run
            time.sleep(3)
            assert mock_engine.ingest.call_count == initial_calls

            # Resume job
            scheduler.resume_job_in_scheduler(job.job_id)
            scheduler.sync_job_status(job.job_id, "active")

            # Wait and verify job runs again
            time.sleep(3)
            assert mock_engine.ingest.call_count > initial_calls
        finally:
            scheduler.shutdown()

    def test_manual_trigger_workflow(self, db_transaction):
        """Test manually triggering a job."""
        scheduler = PersistentScheduler(blocking=False)
        mock_engine = Mock()
        mock_engine.ingest.return_value = {
            "status": "success",
            "records_loaded": 50,
            "log_id": 456,
        }
        scheduler.ingestion_engine = mock_engine

        # Create job
        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"hours": 1},  # Long interval
        )
        job = scheduler_service.create_job(job_data)
        scheduler.add_job_from_database(job.job_id)
        scheduler.start()

        try:
            # Manually trigger job
            triggered = scheduler.trigger_job_now(job.job_id)
            assert triggered is True

            # Verify job executed
            assert mock_engine.ingest.called

            # Verify execution recorded
            executions = scheduler_service.get_job_executions(job.job_id)
            assert len(executions) > 0
        finally:
            scheduler.shutdown()

    def test_job_update_during_execution(self, db_transaction):
        """Test updating a job while scheduler is running."""
        scheduler = PersistentScheduler(blocking=False)
        mock_engine = Mock()
        mock_engine.ingest.return_value = {"status": "success", "records_loaded": 10}
        scheduler.ingestion_engine = mock_engine

        # Create job
        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"seconds": 5},
        )
        job = scheduler_service.create_job(job_data)
        scheduler.add_job_from_database(job.job_id)
        scheduler.start()

        try:
            # Update job in database
            from investment_platform.api.models.scheduler import JobUpdate

            update_data = JobUpdate(
                trigger_config={"seconds": 10},
            )
            scheduler_service.update_job(job.job_id, update_data)

            # Update job in scheduler
            scheduler.update_job_in_scheduler(job.job_id)

            # Verify job still runs with new config
            time.sleep(6)
            assert mock_engine.ingest.called
        finally:
            scheduler.shutdown()

    def test_job_deletion_during_execution(self, db_transaction):
        """Test deleting a job while scheduler is running."""
        scheduler = PersistentScheduler(blocking=False)
        mock_engine = Mock()
        mock_engine.ingest.return_value = {"status": "success", "records_loaded": 10}
        scheduler.ingestion_engine = mock_engine

        # Create job
        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"seconds": 3},
        )
        job = scheduler_service.create_job(job_data)
        scheduler.add_job_from_database(job.job_id)
        scheduler.start()

        try:
            # Let job run once
            time.sleep(4)
            initial_calls = mock_engine.ingest.call_count

            # Delete job
            scheduler.remove_job_from_scheduler(job.job_id)
            scheduler_service.delete_job(job.job_id)

            # Wait and verify job doesn't run anymore
            time.sleep(4)
            assert mock_engine.ingest.call_count == initial_calls
        finally:
            scheduler.shutdown()
