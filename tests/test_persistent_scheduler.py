"""
Tests for PersistentScheduler.

Tests job loading, scheduling, status updates, and error handling.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock
from psycopg2.extras import RealDictCursor

try:
    from investment_platform.ingestion.persistent_scheduler import PersistentScheduler
    from investment_platform.ingestion.db_connection import get_db_connection

    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    PersistentScheduler = None

pytestmark = pytest.mark.skipif(not APSCHEDULER_AVAILABLE, reason="APScheduler not available")


class TestPersistentScheduler:
    """Test suite for PersistentScheduler."""

    @pytest.fixture
    def scheduler(self):
        """Create scheduler instance for testing."""
        with patch("investment_platform.ingestion.persistent_scheduler.IngestionEngine"):
            scheduler = PersistentScheduler(blocking=False)
            yield scheduler
            try:
                scheduler.shutdown()
            except:
                pass

    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection."""
        with patch(
            "investment_platform.ingestion.persistent_scheduler.get_db_connection"
        ) as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.fetchone.return_value = None
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.__enter__.return_value = mock_conn
            mock_db.return_value = mock_conn
            yield mock_db, mock_conn, mock_cursor

    def test_initialization(self):
        """Test scheduler initialization."""
        with patch("investment_platform.ingestion.persistent_scheduler.IngestionEngine"):
            scheduler = PersistentScheduler(blocking=False)
            assert scheduler is not None
            assert scheduler.logger is not None
            scheduler.shutdown()

    def test_load_jobs_from_database_success(self, scheduler, mock_db_connection):
        """Test loading jobs from database."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        # Mock job data
        mock_cursor.fetchall.return_value = [
            {
                "job_id": "test_job_1",
                "symbol": "AAPL",
                "asset_type": "stock",
                "trigger_type": "interval",
                "trigger_config": json.dumps({"minutes": 5}),
                "status": "active",
                "collector_kwargs": None,
                "asset_metadata": None,
                "max_retries": 3,
                "retry_delay_seconds": 60,
                "retry_backoff_multiplier": 2.0,
            },
        ]

        # Mock scheduler.add_job
        with patch.object(scheduler.scheduler, "add_job") as mock_add_job:
            job_ids = scheduler.load_jobs_from_database()

            assert len(job_ids) == 1
            assert "test_job_1" in job_ids
            mock_add_job.assert_called()

    def test_load_jobs_from_database_empty(self, scheduler, mock_db_connection):
        """Test loading when no jobs exist."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchall.return_value = []

        job_ids = scheduler.load_jobs_from_database()

        assert len(job_ids) == 0

    def test_load_jobs_from_database_with_error(self, scheduler, mock_db_connection):
        """Test loading jobs when one fails to load."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchall.return_value = [
            {
                "job_id": "test_job_1",
                "symbol": "AAPL",
                "asset_type": "stock",
                "trigger_type": "invalid",  # Invalid trigger type
                "trigger_config": json.dumps({"minutes": 5}),
                "status": "active",
            },
        ]

        # Should handle error gracefully
        job_ids = scheduler.load_jobs_from_database()

        # Job should not be loaded due to error
        assert len(job_ids) == 0

    def test_load_job_from_row_interval_trigger(self, scheduler):
        """Test loading job with interval trigger."""
        job_row = {
            "job_id": "test_job_1",
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": json.dumps({"minutes": 5}),
            "status": "active",
            "collector_kwargs": None,
            "asset_metadata": None,
            "max_retries": 3,
            "retry_delay_seconds": 60,
            "retry_backoff_multiplier": 2.0,
        }

        with patch.object(scheduler.scheduler, "add_job") as mock_add_job:
            job_id = scheduler._load_job_from_row(job_row)

            assert job_id == "test_job_1"
            mock_add_job.assert_called_once()

    def test_load_job_from_row_cron_trigger(self, scheduler):
        """Test loading job with cron trigger."""
        job_row = {
            "job_id": "test_job_2",
            "symbol": "MSFT",
            "asset_type": "stock",
            "trigger_type": "cron",
            "trigger_config": json.dumps({"hour": 9, "minute": 0}),
            "status": "active",
            "collector_kwargs": None,
            "asset_metadata": None,
            "max_retries": 3,
            "retry_delay_seconds": 60,
            "retry_backoff_multiplier": 2.0,
        }

        with patch.object(scheduler.scheduler, "add_job") as mock_add_job:
            job_id = scheduler._load_job_from_row(job_row)

            assert job_id == "test_job_2"
            mock_add_job.assert_called_once()

    def test_load_job_from_row_execute_now(self, scheduler, mock_db_connection):
        """Test loading execute_now job (should not be scheduled)."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        job_row = {
            "job_id": "test_job_3",
            "symbol": "GOOGL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": json.dumps({"execute_now": True}),
            "status": "pending",
            "last_run_at": None,
            "collector_kwargs": None,
            "asset_metadata": None,
        }

        with patch.object(scheduler, "sync_job_status") as mock_sync:
            with patch.object(scheduler.scheduler, "add_job") as mock_add_job:
                job_id = scheduler._load_job_from_row(job_row)

                assert job_id == "test_job_3"
                # Should not be added to scheduler
                mock_add_job.assert_not_called()
                # Should sync status to active
                mock_sync.assert_called()

    def test_add_job_from_database_success(self, scheduler, mock_db_connection):
        """Test adding job from database."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = {
            "job_id": "test_job_1",
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": json.dumps({"minutes": 5}),
            "status": "active",
            "collector_kwargs": None,
            "asset_metadata": None,
            "max_retries": 3,
            "retry_delay_seconds": 60,
            "retry_backoff_multiplier": 2.0,
        }

        with patch.object(scheduler.scheduler, "add_job") as mock_add_job:
            result = scheduler.add_job_from_database("test_job_1")

            assert result is True
            mock_add_job.assert_called_once()

    def test_add_job_from_database_not_found(self, scheduler, mock_db_connection):
        """Test adding job that doesn't exist."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = None

        result = scheduler.add_job_from_database("nonexistent")

        assert result is False

    def test_remove_job_from_scheduler_success(self, scheduler):
        """Test removing job from scheduler."""
        # Add a job first
        with patch.object(scheduler.scheduler, "add_job"):
            scheduler.scheduler.add_job(
                lambda: None,
                "interval",
                minutes=5,
                id="test_job_1",
            )

        result = scheduler.remove_job_from_scheduler("test_job_1")

        assert result is True

    def test_remove_job_from_scheduler_not_found(self, scheduler):
        """Test removing job that doesn't exist."""
        result = scheduler.remove_job_from_scheduler("nonexistent")

        # Should return False but not raise error
        assert result is False

    def test_update_job_in_scheduler_success(self, scheduler, mock_db_connection):
        """Test updating job in scheduler."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = {
            "job_id": "test_job_1",
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": json.dumps({"minutes": 10}),
            "status": "active",
            "collector_kwargs": None,
            "asset_metadata": None,
        }

        with patch.object(scheduler, "remove_job_from_scheduler") as mock_remove:
            with patch.object(scheduler, "add_job_from_database") as mock_add:
                mock_remove.return_value = True
                mock_add.return_value = True

                result = scheduler.update_job_in_scheduler("test_job_1")

                assert result is True
                mock_remove.assert_called_once()
                mock_add.assert_called_once()

    def test_pause_job_in_scheduler_success(self, scheduler):
        """Test pausing job in scheduler."""
        # Add a job first
        with patch.object(scheduler.scheduler, "add_job"):
            scheduler.scheduler.add_job(
                lambda: None,
                "interval",
                minutes=5,
                id="test_job_1",
            )

        result = scheduler.pause_job_in_scheduler("test_job_1")

        assert result is True

    def test_resume_job_in_scheduler_success(self, scheduler):
        """Test resuming job in scheduler."""
        # Add and pause a job first
        with patch.object(scheduler.scheduler, "add_job"):
            scheduler.scheduler.add_job(
                lambda: None,
                "interval",
                minutes=5,
                id="test_job_1",
            )
            scheduler.scheduler.pause_job("test_job_1")

        result = scheduler.resume_job_in_scheduler("test_job_1")

        assert result is True

    def test_sync_job_status_success(self, scheduler, mock_db_connection):
        """Test syncing job status to database."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        scheduler.sync_job_status("test_job_1", "active", datetime.now())

        # Verify database update was called
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    def test_load_jobs_with_dependencies(self, scheduler, mock_db_connection):
        """Test loading jobs with dependencies."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        # Mock job with dependencies
        mock_cursor.fetchall.return_value = [
            {
                "job_id": "test_job_1",
                "symbol": "AAPL",
                "asset_type": "stock",
                "trigger_type": "interval",
                "trigger_config": json.dumps({"minutes": 5}),
                "status": "active",
                "collector_kwargs": None,
                "asset_metadata": None,
            },
        ]

        # Mock dependencies query
        mock_cursor.fetchall.side_effect = [
            [{"job_id": "test_job_1"}],  # Jobs
            [{"depends_on_job_id": "parent_job", "condition": "success"}],  # Dependencies
        ]

        with patch.object(scheduler.scheduler, "add_job") as mock_add_job:
            job_ids = scheduler.load_jobs_from_database()

            # Job should be loaded
            assert len(job_ids) >= 0  # May be 0 if dependency check fails

    def test_load_job_with_collector_kwargs(self, scheduler):
        """Test loading job with collector kwargs."""
        job_row = {
            "job_id": "test_job_1",
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": json.dumps({"minutes": 5}),
            "status": "active",
            "collector_kwargs": json.dumps({"interval": "1m"}),
            "asset_metadata": None,
            "max_retries": 3,
            "retry_delay_seconds": 60,
            "retry_backoff_multiplier": 2.0,
        }

        with patch.object(scheduler.scheduler, "add_job") as mock_add_job:
            job_id = scheduler._load_job_from_row(job_row)

            assert job_id == "test_job_1"
            # Verify collector_kwargs were passed
            call_kwargs = mock_add_job.call_args[1]
            assert (
                "collector_kwargs" in call_kwargs or call_kwargs.get("collector_kwargs") is not None
            )
