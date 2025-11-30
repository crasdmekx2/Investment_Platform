"""
Tests for PersistentScheduler functionality.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from psycopg2.extras import RealDictCursor

try:
    from investment_platform.ingestion.persistent_scheduler import PersistentScheduler, APSCHEDULER_AVAILABLE
    from investment_platform.ingestion.scheduler import APSCHEDULER_AVAILABLE as BASE_APSCHEDULER_AVAILABLE
except ImportError:
    APSCHEDULER_AVAILABLE = False
    BASE_APSCHEDULER_AVAILABLE = False
    PersistentScheduler = None


@pytest.mark.skipif(not APSCHEDULER_AVAILABLE, reason="APScheduler not available")
class TestPersistentScheduler:
    """Test PersistentScheduler functionality."""

    def test_init(self):
        """Test scheduler initialization."""
        scheduler = PersistentScheduler(blocking=False)
        assert scheduler is not None
        assert scheduler.scheduler is not None
        scheduler.shutdown()

    def test_load_jobs_from_database_empty(self, db_transaction):
        """Test loading jobs from empty database."""
        scheduler = PersistentScheduler(blocking=False)
        
        # Clear any existing jobs
        with db_transaction.cursor() as cursor:
            cursor.execute("DELETE FROM scheduler_jobs")
            db_transaction.commit()
        
        loaded = scheduler.load_jobs_from_database()
        assert loaded == []
        scheduler.shutdown()

    def test_load_jobs_from_database_with_jobs(self, db_transaction):
        """Test loading jobs from database."""
        scheduler = PersistentScheduler(blocking=False)
        
        # Create test job in database
        with db_transaction.cursor() as cursor:
            cursor.execute("""
                INSERT INTO scheduler_jobs (
                    job_id, symbol, asset_type, trigger_type, trigger_config, status
                ) VALUES (
                    'test_job_1', 'AAPL', 'stock', 'interval',
                    '{"minutes": 5}', 'active'
                )
            """)
            db_transaction.commit()
        
        # Mock ingestion engine to avoid actual execution
        scheduler.ingestion_engine = Mock()
        
        loaded = scheduler.load_jobs_from_database()
        assert len(loaded) == 1
        assert loaded[0] == 'test_job_1'
        
        # Verify job is in scheduler
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == 'test_job_1'
        
        scheduler.shutdown()

    def test_load_job_from_row_interval(self, db_transaction):
        """Test loading a job with interval trigger."""
        scheduler = PersistentScheduler(blocking=False)
        scheduler.ingestion_engine = Mock()
        
        job_row = {
            "job_id": "test_interval",
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 10},
            "start_date": None,
            "end_date": None,
            "collector_kwargs": None,
            "asset_metadata": None,
        }
        
        job_id = scheduler._load_job_from_row(job_row)
        assert job_id == "test_interval"
        
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "test_interval"
        
        scheduler.shutdown()

    def test_load_job_from_row_cron(self, db_transaction):
        """Test loading a job with cron trigger."""
        scheduler = PersistentScheduler(blocking=False)
        scheduler.ingestion_engine = Mock()
        
        job_row = {
            "job_id": "test_cron",
            "symbol": "BTC-USD",
            "asset_type": "crypto",
            "trigger_type": "cron",
            "trigger_config": {"hour": "9", "minute": "0"},
            "start_date": None,
            "end_date": None,
            "collector_kwargs": None,
            "asset_metadata": None,
        }
        
        job_id = scheduler._load_job_from_row(job_row)
        assert job_id == "test_cron"
        
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "test_cron"
        
        scheduler.shutdown()

    def test_sync_job_status(self, db_transaction):
        """Test syncing job status with database."""
        scheduler = PersistentScheduler(blocking=False)
        
        # Create test job
        with db_transaction.cursor() as cursor:
            cursor.execute("""
                INSERT INTO scheduler_jobs (
                    job_id, symbol, asset_type, trigger_type, trigger_config, status
                ) VALUES (
                    'test_sync', 'AAPL', 'stock', 'interval',
                    '{"minutes": 5}', 'pending'
                )
            """)
            db_transaction.commit()
        
        # Sync status
        next_run = datetime.now() + timedelta(minutes=5)
        scheduler.sync_job_status("test_sync", "active", next_run)
        
        # Verify status updated
        with db_transaction.cursor() as cursor:
            cursor.execute("SELECT status, next_run_at FROM scheduler_jobs WHERE job_id = 'test_sync'")
            result = cursor.fetchone()
            assert result[0] == "active"
            assert result[1] is not None
        
        scheduler.shutdown()

    def test_record_execution(self, db_transaction):
        """Test recording job execution."""
        scheduler = PersistentScheduler(blocking=False)
        
        # Create test job
        with db_transaction.cursor() as cursor:
            cursor.execute("""
                INSERT INTO scheduler_jobs (
                    job_id, symbol, asset_type, trigger_type, trigger_config, status
                ) VALUES (
                    'test_exec', 'AAPL', 'stock', 'interval',
                    '{"minutes": 5}', 'active'
                )
            """)
            db_transaction.commit()
        
        # Record execution
        execution_id = scheduler.record_execution(
            job_id="test_exec",
            execution_status="success",
            log_id=123,
            execution_time_ms=5000,
        )
        
        assert execution_id > 0
        
        # Verify execution recorded
        with db_transaction.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM scheduler_job_executions WHERE execution_id = %s
            """, (execution_id,))
            result = cursor.fetchone()
            assert result is not None
            assert result[1] == "test_exec"  # job_id
            assert result[3] == "success"  # execution_status
        
        scheduler.shutdown()

    def test_add_job_from_database(self, db_transaction):
        """Test adding job from database to scheduler."""
        scheduler = PersistentScheduler(blocking=False)
        scheduler.ingestion_engine = Mock()
        
        # Create test job
        with db_transaction.cursor() as cursor:
            cursor.execute("""
                INSERT INTO scheduler_jobs (
                    job_id, symbol, asset_type, trigger_type, trigger_config, status
                ) VALUES (
                    'test_add', 'AAPL', 'stock', 'interval',
                    '{"minutes": 5}', 'active'
                )
            """)
            db_transaction.commit()
        
        # Add job to scheduler
        added = scheduler.add_job_from_database("test_add")
        assert added is True
        
        # Verify job in scheduler
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "test_add"
        
        scheduler.shutdown()

    def test_add_job_from_database_not_found(self, db_transaction):
        """Test adding non-existent job."""
        scheduler = PersistentScheduler(blocking=False)
        
        added = scheduler.add_job_from_database("nonexistent")
        assert added is False
        
        scheduler.shutdown()

    def test_add_job_from_database_paused(self, db_transaction):
        """Test that paused jobs are not added."""
        scheduler = PersistentScheduler(blocking=False)
        
        # Create paused job
        with db_transaction.cursor() as cursor:
            cursor.execute("""
                INSERT INTO scheduler_jobs (
                    job_id, symbol, asset_type, trigger_type, trigger_config, status
                ) VALUES (
                    'test_paused', 'AAPL', 'stock', 'interval',
                    '{"minutes": 5}', 'paused'
                )
            """)
            db_transaction.commit()
        
        added = scheduler.add_job_from_database("test_paused")
        assert added is False
        
        # Verify job not in scheduler
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 0
        
        scheduler.shutdown()

    def test_remove_job_from_scheduler(self, db_transaction):
        """Test removing job from scheduler."""
        scheduler = PersistentScheduler(blocking=False)
        scheduler.ingestion_engine = Mock()
        
        # Add job first
        from apscheduler.triggers.interval import IntervalTrigger
        scheduler.add_job(
            symbol="AAPL",
            asset_type="stock",
            trigger=IntervalTrigger(minutes=5),
            job_id="test_remove",
        )
        
        # Verify job exists
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 1
        
        # Remove job
        removed = scheduler.remove_job_from_scheduler("test_remove")
        assert removed is True
        
        # Verify job removed
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 0
        
        scheduler.shutdown()

    def test_update_job_in_scheduler(self, db_transaction):
        """Test updating job in scheduler."""
        scheduler = PersistentScheduler(blocking=False)
        scheduler.ingestion_engine = Mock()
        
        # Create and add job
        with db_transaction.cursor() as cursor:
            cursor.execute("""
                INSERT INTO scheduler_jobs (
                    job_id, symbol, asset_type, trigger_type, trigger_config, status
                ) VALUES (
                    'test_update', 'AAPL', 'stock', 'interval',
                    '{"minutes": 5}', 'active'
                )
            """)
            db_transaction.commit()
        
        scheduler.add_job_from_database("test_update")
        
        # Update job in database
        with db_transaction.cursor() as cursor:
            cursor.execute("""
                UPDATE scheduler_jobs
                SET trigger_config = '{"minutes": 10}'
                WHERE job_id = 'test_update'
            """)
            db_transaction.commit()
        
        # Update in scheduler
        updated = scheduler.update_job_in_scheduler("test_update")
        assert updated is True
        
        scheduler.shutdown()

    def test_pause_job_in_scheduler(self, db_transaction):
        """Test pausing job in scheduler."""
        scheduler = PersistentScheduler(blocking=False)
        scheduler.ingestion_engine = Mock()
        
        # Add job
        from apscheduler.triggers.interval import IntervalTrigger
        scheduler.add_job(
            symbol="AAPL",
            asset_type="stock",
            trigger=IntervalTrigger(minutes=5),
            job_id="test_pause",
        )
        
        # Pause job
        paused = scheduler.pause_job_in_scheduler("test_pause")
        assert paused is True
        
        # Verify job is paused
        job = scheduler.scheduler.get_job("test_pause")
        assert job.next_run_time is None  # Paused jobs don't have next run time
        
        scheduler.shutdown()

    def test_resume_job_in_scheduler(self, db_transaction):
        """Test resuming job in scheduler."""
        scheduler = PersistentScheduler(blocking=False)
        scheduler.ingestion_engine = Mock()
        
        # Add and pause job
        from apscheduler.triggers.interval import IntervalTrigger
        scheduler.add_job(
            symbol="AAPL",
            asset_type="stock",
            trigger=IntervalTrigger(minutes=5),
            job_id="test_resume",
        )
        scheduler.pause_job_in_scheduler("test_resume")
        
        # Resume job
        resumed = scheduler.resume_job_in_scheduler("test_resume")
        assert resumed is True
        
        scheduler.shutdown()

    def test_trigger_job_now(self, db_transaction):
        """Test manually triggering a job."""
        scheduler = PersistentScheduler(blocking=False)
        mock_engine = Mock()
        mock_engine.ingest.return_value = {
            "status": "success",
            "records_loaded": 100,
        }
        scheduler.ingestion_engine = mock_engine
        
        # Add job
        from apscheduler.triggers.interval import IntervalTrigger
        scheduler.add_job(
            symbol="AAPL",
            asset_type="stock",
            trigger=IntervalTrigger(minutes=5),
            job_id="test_trigger",
        )
        
        # Trigger job
        triggered = scheduler.trigger_job_now("test_trigger")
        assert triggered is True
        
        # Verify engine was called
        assert mock_engine.ingest.called
        
        scheduler.shutdown()

    def test_trigger_job_now_not_found(self, db_transaction):
        """Test triggering non-existent job."""
        scheduler = PersistentScheduler(blocking=False)
        
        triggered = scheduler.trigger_job_now("nonexistent")
        assert triggered is False
        
        scheduler.shutdown()

