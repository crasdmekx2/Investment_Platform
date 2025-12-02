"""
Unit tests for scheduler service.

Tests business logic for scheduler operations.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from psycopg2.extras import RealDictCursor

from investment_platform.api.services import scheduler_service
from investment_platform.api.models.scheduler import (
    JobCreate,
    JobUpdate,
    JobTemplateCreate,
)


class TestSchedulerService:
    """Test suite for scheduler service."""

    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection."""
        with patch(
            "investment_platform.api.services.scheduler_service.get_db_connection"
        ) as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.__enter__.return_value = mock_conn
            mock_db.return_value = mock_conn
            yield mock_db, mock_conn, mock_cursor

    def test_generate_job_id(self):
        """Test job ID generation."""
        job_id = scheduler_service.generate_job_id("AAPL", "stock")

        assert job_id.startswith("stock_AAPL_")
        assert len(job_id) > 20  # Should have timestamp and UUID

    def test_create_job_success(self, mock_db_connection):
        """Test successful job creation."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        # Mock job creation response with all required fields
        mock_cursor.fetchone.return_value = {
            "job_id": "test_job_123",
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": '{"minutes": 5}',
            "start_date": None,
            "end_date": None,
            "collector_kwargs": None,
            "asset_metadata": None,
            "status": "pending",
            "max_retries": 3,
            "retry_delay_seconds": 60,
            "retry_backoff_multiplier": 2.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_run_at": None,
            "next_run_at": None,
        }

        # Mock dependency query (called by _dict_to_job_response)
        mock_cursor.fetchall.return_value = []

        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        )

        job = scheduler_service.create_job(job_data)

        assert job.job_id == "test_job_123"
        assert job.symbol == "AAPL"
        assert job.asset_type == "stock"
        assert job.status == "pending"
        mock_cursor.execute.assert_called()

    def test_create_job_with_dependencies(self, mock_db_connection):
        """Test job creation with dependencies."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = {
            "job_id": "test_job_123",
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": '{"minutes": 5}',
            "start_date": None,
            "end_date": None,
            "collector_kwargs": None,
            "asset_metadata": None,
            "status": "pending",
            "max_retries": 3,
            "retry_delay_seconds": 60,
            "retry_backoff_multiplier": 2.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_run_at": None,
            "next_run_at": None,
        }

        # Mock dependency query (called by _dict_to_job_response)
        mock_cursor.fetchall.return_value = []

        from investment_platform.api.models.scheduler import JobDependency

        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
            dependencies=[JobDependency(depends_on_job_id="parent_job", condition="success")],
        )

        job = scheduler_service.create_job(job_data)

        # Verify dependencies were inserted
        assert mock_cursor.execute.call_count >= 2  # Job insert + dependency insert

    def test_get_job_success(self, mock_db_connection):
        """Test getting a job by ID."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = {
            "job_id": "test_job_123",
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": '{"minutes": 5}',
            "start_date": None,
            "end_date": None,
            "collector_kwargs": None,
            "asset_metadata": None,
            "status": "active",
            "max_retries": 3,
            "retry_delay_seconds": 60,
            "retry_backoff_multiplier": 2.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_run_at": None,
            "next_run_at": None,
        }

        # Mock dependency query (called by _dict_to_job_response)
        mock_cursor.fetchall.return_value = []

        job = scheduler_service.get_job("test_job_123")

        assert job is not None
        assert job.job_id == "test_job_123"
        assert job.symbol == "AAPL"

    def test_get_job_not_found(self, mock_db_connection):
        """Test getting a non-existent job."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = None

        job = scheduler_service.get_job("nonexistent")

        assert job is None

    def test_list_jobs_success(self, mock_db_connection):
        """Test listing jobs."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        # Mock fetchall for list_jobs (returns list of jobs)
        # Mock fetchall for _dict_to_job_response (returns dependencies for each job)
        def mock_fetchall_side_effect(*args, **kwargs):
            # First call is for list_jobs, subsequent calls are for dependencies
            if not hasattr(mock_fetchall_side_effect, "call_count"):
                mock_fetchall_side_effect.call_count = 0
            mock_fetchall_side_effect.call_count += 1

            if mock_fetchall_side_effect.call_count == 1:
                # Return jobs list
                return [
                    {
                        "job_id": "job_1",
                        "symbol": "AAPL",
                        "asset_type": "stock",
                        "trigger_type": "interval",
                        "trigger_config": '{"minutes": 5}',
                        "start_date": None,
                        "end_date": None,
                        "collector_kwargs": None,
                        "asset_metadata": None,
                        "status": "active",
                        "max_retries": 3,
                        "retry_delay_seconds": 60,
                        "retry_backoff_multiplier": 2.0,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now(),
                        "last_run_at": None,
                        "next_run_at": None,
                    },
                    {
                        "job_id": "job_2",
                        "symbol": "MSFT",
                        "asset_type": "stock",
                        "trigger_type": "interval",
                        "trigger_config": '{"minutes": 5}',
                        "start_date": None,
                        "end_date": None,
                        "collector_kwargs": None,
                        "asset_metadata": None,
                        "status": "paused",
                        "max_retries": 3,
                        "retry_delay_seconds": 60,
                        "retry_backoff_multiplier": 2.0,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now(),
                        "last_run_at": None,
                        "next_run_at": None,
                    },
                ]
            else:
                # Return dependencies (empty for each job)
                return []

        mock_cursor.fetchall.side_effect = mock_fetchall_side_effect

        jobs = scheduler_service.list_jobs()

        assert len(jobs) == 2
        assert jobs[0].job_id == "job_1"
        assert jobs[1].job_id == "job_2"

    def test_list_jobs_with_filters(self, mock_db_connection):
        """Test listing jobs with filters."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchall.return_value = []

        jobs = scheduler_service.list_jobs(status="active", asset_type="stock")

        assert isinstance(jobs, list)
        # Verify filters were applied in query
        mock_cursor.execute.assert_called_once()

    def test_update_job_success(self, mock_db_connection):
        """Test updating a job."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = {
            "job_id": "test_job_123",
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": '{"minutes": 10}',
            "start_date": None,
            "end_date": None,
            "collector_kwargs": None,
            "asset_metadata": None,
            "status": "active",
            "max_retries": 3,
            "retry_delay_seconds": 60,
            "retry_backoff_multiplier": 2.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_run_at": None,
            "next_run_at": None,
        }

        # Mock dependency query (called by _dict_to_job_response)
        mock_cursor.fetchall.return_value = []

        update_data = JobUpdate(
            trigger_config={"minutes": 10},
        )

        job = scheduler_service.update_job("test_job_123", update_data)

        assert job is not None
        assert job.job_id == "test_job_123"
        mock_cursor.execute.assert_called()

    def test_delete_job_success(self, mock_db_connection):
        """Test deleting a job."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        # Set rowcount to simulate successful deletion
        mock_cursor.rowcount = 1

        result = scheduler_service.delete_job("test_job_123")

        # Verify delete was called
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    def test_pause_job_success(self, mock_db_connection):
        """Test pausing a job."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = {
            "job_id": "test_job_123",
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": '{"minutes": 5}',
            "start_date": None,
            "end_date": None,
            "collector_kwargs": None,
            "asset_metadata": None,
            "status": "paused",
            "max_retries": 3,
            "retry_delay_seconds": 60,
            "retry_backoff_multiplier": 2.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_run_at": None,
            "next_run_at": None,
        }

        # Mock dependency query (called by _dict_to_job_response)
        mock_cursor.fetchall.return_value = []

        job = scheduler_service.update_job_status("test_job_123", "paused")

        assert job is not None
        assert job.status == "paused"
        mock_cursor.execute.assert_called()

    def test_resume_job_success(self, mock_db_connection):
        """Test resuming a job."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = {
            "job_id": "test_job_123",
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": '{"minutes": 5}',
            "start_date": None,
            "end_date": None,
            "collector_kwargs": None,
            "asset_metadata": None,
            "status": "active",
            "max_retries": 3,
            "retry_delay_seconds": 60,
            "retry_backoff_multiplier": 2.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_run_at": None,
            "next_run_at": None,
        }

        # Mock dependency query (called by _dict_to_job_response)
        mock_cursor.fetchall.return_value = []

        job = scheduler_service.update_job_status("test_job_123", "active")

        assert job is not None
        assert job.status == "active"

    def test_get_job_executions(self, mock_db_connection):
        """Test getting job executions."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchall.return_value = [
            {
                "execution_id": 1,
                "job_id": "test_job_123",
                "log_id": 1,
                "execution_status": "success",
                "started_at": datetime.now(),
                "completed_at": datetime.now(),
                "error_message": None,
                "error_category": None,
                "execution_time_ms": 100,
                "retry_attempt": 0,
                "created_at": datetime.now(),
            },
        ]

        executions = scheduler_service.get_job_executions("test_job_123")

        assert len(executions) == 1
        assert executions[0].execution_id == 1

    def test_create_template_success(self, mock_db_connection):
        """Test creating a job template."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = {
            "template_id": 1,
            "name": "Test Template",
            "description": None,
            "symbol": None,
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": '{"minutes": 5}',
            "collector_kwargs": None,
            "asset_metadata": None,
            "start_date": None,
            "end_date": None,
            "max_retries": None,
            "retry_delay_seconds": None,
            "retry_backoff_multiplier": None,
            "is_public": False,
            "created_by": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        template_data = JobTemplateCreate(
            name="Test Template",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        )

        template = scheduler_service.create_template(template_data)

        assert template is not None
        assert template.template_id == 1
        assert template.name == "Test Template"

    def test_get_template_success(self, mock_db_connection):
        """Test getting a template by ID."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = {
            "template_id": 1,
            "name": "Test Template",
            "description": None,
            "symbol": None,
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": '{"minutes": 5}',
            "collector_kwargs": None,
            "asset_metadata": None,
            "start_date": None,
            "end_date": None,
            "max_retries": None,
            "retry_delay_seconds": None,
            "retry_backoff_multiplier": None,
            "is_public": False,
            "created_by": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        template = scheduler_service.get_template(1)

        assert template is not None
        assert template.template_id == 1

    def test_list_templates(self, mock_db_connection):
        """Test listing templates."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchall.return_value = [
            {
                "template_id": 1,
                "name": "Template 1",
                "description": None,
                "symbol": None,
                "asset_type": "stock",
                "trigger_type": "interval",
                "trigger_config": '{"minutes": 5}',
                "collector_kwargs": None,
                "asset_metadata": None,
                "start_date": None,
                "end_date": None,
                "max_retries": None,
                "retry_delay_seconds": None,
                "retry_backoff_multiplier": None,
                "is_public": False,
                "created_by": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
            {
                "template_id": 2,
                "name": "Template 2",
                "description": None,
                "symbol": None,
                "asset_type": "crypto",
                "trigger_type": "interval",
                "trigger_config": '{"minutes": 5}',
                "collector_kwargs": None,
                "asset_metadata": None,
                "start_date": None,
                "end_date": None,
                "max_retries": None,
                "retry_delay_seconds": None,
                "retry_backoff_multiplier": None,
                "is_public": False,
                "created_by": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
        ]

        templates = scheduler_service.list_templates()

        assert len(templates) == 2
        assert templates[0].template_id == 1
        assert templates[1].template_id == 2
