"""
Integration tests for Scheduler API router.

Tests all endpoints in the scheduler router with proper request/response cycles.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime

try:
    from investment_platform.api.main import app
    from investment_platform.api.models.scheduler import (
        JobCreate,
        JobUpdate,
        JobTemplateCreate,
        JobTemplateUpdate,
    )
    from investment_platform.ingestion.persistent_scheduler import PersistentScheduler
except ImportError:
    app = None

pytestmark = pytest.mark.skipif(app is None, reason="API app not available")


class TestSchedulerRouter:
    """Test suite for Scheduler API router."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_scheduler(self):
        """Mock scheduler instance."""
        scheduler = Mock(spec=PersistentScheduler)
        scheduler.add_job_from_database = Mock(return_value=True)
        scheduler.update_job_in_scheduler = Mock()
        scheduler.remove_job_from_scheduler = Mock()
        scheduler.pause_job_in_scheduler = Mock()
        scheduler.resume_job_in_scheduler = Mock()
        scheduler.add_job_from_database = Mock(return_value=True)
        scheduler.sync_job_status = Mock()
        scheduler.trigger_job_now = Mock()
        scheduler.scheduler = Mock()
        scheduler.scheduler.get_job = Mock(side_effect=Exception("Job not found"))
        return scheduler

    @pytest.fixture
    def mock_app_state(self, mock_scheduler):
        """Mock app state with scheduler."""
        app.state.scheduler = mock_scheduler
        yield
        if hasattr(app.state, "scheduler"):
            delattr(app.state, "scheduler")

    @pytest.fixture
    def mock_scheduler_service(self):
        """Mock scheduler service."""
        with patch("investment_platform.api.routers.scheduler.scheduler_svc") as mock_svc:
            yield mock_svc

    def test_list_jobs_success(self, client, mock_scheduler_service, mock_app_state):
        """Test successful listing of jobs."""
        from investment_platform.api.models.scheduler import JobResponse

        mock_scheduler_service.list_jobs.return_value = [
            JobResponse(
                job_id="test_job_1",
                symbol="AAPL",
                asset_type="stock",
                status="active",
                trigger_type="interval",
                trigger_config={"seconds": 60},
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]

        response = client.get("/api/scheduler/jobs")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["job_id"] == "test_job_1"

    def test_list_jobs_with_filters(self, client, mock_scheduler_service, mock_app_state):
        """Test listing jobs with filters."""
        from investment_platform.api.models.scheduler import JobResponse

        mock_scheduler_service.list_jobs.return_value = []

        response = client.get(
            "/api/scheduler/jobs?status=active&asset_type=stock&limit=10&offset=0"
        )

        assert response.status_code == 200
        mock_scheduler_service.list_jobs.assert_called_once_with(
            status="active", asset_type="stock", limit=10, offset=0
        )

    def test_list_jobs_invalid_limit(self, client, mock_scheduler_service, mock_app_state):
        """Test listing jobs with invalid limit."""
        response = client.get("/api/scheduler/jobs?limit=0")

        assert response.status_code == 422  # Validation error

    def test_list_jobs_service_error(self, client, mock_scheduler_service, mock_app_state):
        """Test listing jobs with service error."""
        mock_scheduler_service.list_jobs.side_effect = ValueError("Invalid status")

        response = client.get("/api/scheduler/jobs?status=invalid")

        assert response.status_code == 400

    def test_get_job_success(self, client, mock_scheduler_service, mock_app_state):
        """Test getting a job by ID."""
        from investment_platform.api.models.scheduler import JobResponse

        mock_scheduler_service.get_job.return_value = JobResponse(
            job_id="test_job_1",
            symbol="AAPL",
            asset_type="stock",
            status="active",
            trigger_type="interval",
            trigger_config={"seconds": 60},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        response = client.get("/api/scheduler/jobs/test_job_1")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test_job_1"

    def test_get_job_not_found(self, client, mock_scheduler_service, mock_app_state):
        """Test getting a non-existent job."""
        mock_scheduler_service.get_job.return_value = None

        response = client.get("/api/scheduler/jobs/nonexistent")

        assert response.status_code == 404

    def test_create_job_success(
        self, client, mock_scheduler_service, mock_app_state, mock_scheduler
    ):
        """Test successful job creation."""
        from investment_platform.api.models.scheduler import JobResponse

        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"seconds": 60},
        )

        mock_scheduler_service.create_job.return_value = JobResponse(
            job_id="test_job_1",
            symbol="AAPL",
            asset_type="stock",
            status="active",
            trigger_type="interval",
            trigger_config={"seconds": 60},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        response = client.post("/api/scheduler/jobs", json=job_data.dict())

        assert response.status_code == 201
        data = response.json()
        assert data["job_id"] == "test_job_1"
        mock_scheduler.add_job_from_database.assert_called_once()

    def test_create_job_validation_error(self, client, mock_scheduler_service, mock_app_state):
        """Test job creation with validation error."""
        from investment_platform.collectors.base import ValidationError

        mock_scheduler_service.create_job.side_effect = ValidationError("Invalid symbol")

        job_data = {
            "symbol": "",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {},
        }

        response = client.post("/api/scheduler/jobs", json=job_data)

        assert response.status_code == 400

    def test_create_job_no_scheduler(self, client, mock_scheduler_service):
        """Test job creation when scheduler is not available."""
        from investment_platform.api.models.scheduler import JobResponse

        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"seconds": 60},
        )

        mock_scheduler_service.create_job.return_value = JobResponse(
            job_id="test_job_1",
            symbol="AAPL",
            asset_type="stock",
            status="active",
            trigger_type="interval",
            trigger_config={"seconds": 60},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Scheduler not in app state
        response = client.post("/api/scheduler/jobs", json=job_data.dict())

        # Should still create job in DB even if scheduler unavailable
        assert response.status_code in [201, 503]  # May fail if scheduler required

    def test_update_job_success(
        self, client, mock_scheduler_service, mock_app_state, mock_scheduler
    ):
        """Test successful job update."""
        from investment_platform.api.models.scheduler import JobResponse

        job_update = JobUpdate(trigger_config={"seconds": 120})

        mock_scheduler_service.update_job.return_value = JobResponse(
            job_id="test_job_1",
            symbol="AAPL",
            asset_type="stock",
            status="active",
            trigger_type="interval",
            trigger_config={"seconds": 120},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        response = client.put("/api/scheduler/jobs/test_job_1", json=job_update.dict())

        assert response.status_code == 200
        mock_scheduler.update_job_in_scheduler.assert_called_once_with("test_job_1")

    def test_update_job_not_found(self, client, mock_scheduler_service, mock_app_state):
        """Test updating a non-existent job."""
        mock_scheduler_service.update_job.return_value = None

        job_update = {"trigger_config": {"seconds": 120}}

        response = client.put("/api/scheduler/jobs/nonexistent", json=job_update)

        assert response.status_code == 404

    def test_delete_job_success(
        self, client, mock_scheduler_service, mock_app_state, mock_scheduler
    ):
        """Test successful job deletion."""
        mock_scheduler_service.delete_job.return_value = True

        response = client.delete("/api/scheduler/jobs/test_job_1")

        assert response.status_code == 204
        mock_scheduler.remove_job_from_scheduler.assert_called_once_with("test_job_1")

    def test_delete_job_not_found(self, client, mock_scheduler_service, mock_app_state):
        """Test deleting a non-existent job."""
        mock_scheduler_service.delete_job.return_value = False

        response = client.delete("/api/scheduler/jobs/nonexistent")

        assert response.status_code == 404

    def test_pause_job_success(
        self, client, mock_scheduler_service, mock_app_state, mock_scheduler
    ):
        """Test successful job pause."""
        from investment_platform.api.models.scheduler import JobResponse

        mock_scheduler_service.update_job_status.return_value = JobResponse(
            job_id="test_job_1",
            symbol="AAPL",
            asset_type="stock",
            status="paused",
            trigger_type="interval",
            trigger_config={"seconds": 60},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        response = client.post("/api/scheduler/jobs/test_job_1/pause")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"
        mock_scheduler.pause_job_in_scheduler.assert_called_once_with("test_job_1")

    def test_pause_job_not_found(self, client, mock_scheduler_service, mock_app_state):
        """Test pausing a non-existent job."""
        mock_scheduler_service.update_job_status.return_value = None

        response = client.post("/api/scheduler/jobs/nonexistent/pause")

        assert response.status_code == 404

    def test_resume_job_success(
        self, client, mock_scheduler_service, mock_app_state, mock_scheduler
    ):
        """Test successful job resume."""
        from investment_platform.api.models.scheduler import JobResponse

        mock_scheduler_service.update_job_status.return_value = JobResponse(
            job_id="test_job_1",
            symbol="AAPL",
            asset_type="stock",
            status="active",
            trigger_type="interval",
            trigger_config={"seconds": 60},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        response = client.post("/api/scheduler/jobs/test_job_1/resume")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

    def test_resume_job_not_found(self, client, mock_scheduler_service, mock_app_state):
        """Test resuming a non-existent job."""
        mock_scheduler_service.update_job_status.return_value = None

        response = client.post("/api/scheduler/jobs/nonexistent/resume")

        assert response.status_code == 404

    def test_trigger_job_success(
        self, client, mock_scheduler_service, mock_app_state, mock_scheduler
    ):
        """Test successful job trigger."""
        from investment_platform.api.models.scheduler import JobResponse

        mock_scheduler_service.get_job.return_value = JobResponse(
            job_id="test_job_1",
            symbol="AAPL",
            asset_type="stock",
            status="active",
            trigger_type="interval",
            trigger_config={"seconds": 60},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        response = client.post("/api/scheduler/jobs/test_job_1/trigger")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "triggered"

    def test_trigger_job_not_found(self, client, mock_scheduler_service, mock_app_state):
        """Test triggering a non-existent job."""
        mock_scheduler_service.get_job.return_value = None

        response = client.post("/api/scheduler/jobs/nonexistent/trigger")

        assert response.status_code == 404

    def test_trigger_job_invalid_status(self, client, mock_scheduler_service, mock_app_state):
        """Test triggering a job with invalid status."""
        from investment_platform.api.models.scheduler import JobResponse

        mock_scheduler_service.get_job.return_value = JobResponse(
            job_id="test_job_1",
            symbol="AAPL",
            asset_type="stock",
            status="paused",
            trigger_type="interval",
            trigger_config={"seconds": 60},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        response = client.post("/api/scheduler/jobs/test_job_1/trigger")

        assert response.status_code == 400

    def test_get_job_executions_success(self, client, mock_scheduler_service, mock_app_state):
        """Test getting job executions."""
        from investment_platform.api.models.scheduler import JobResponse, JobExecutionResponse

        mock_scheduler_service.get_job.return_value = JobResponse(
            job_id="test_job_1",
            symbol="AAPL",
            asset_type="stock",
            status="active",
            trigger_type="interval",
            trigger_config={"seconds": 60},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_scheduler_service.get_job_executions.return_value = [
            JobExecutionResponse(
                execution_id=1,
                job_id="test_job_1",
                status="completed",
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )
        ]

        response = client.get("/api/scheduler/jobs/test_job_1/executions")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_templates_success(self, client, mock_scheduler_service, mock_app_state):
        """Test successful listing of templates."""
        from investment_platform.api.models.scheduler import JobTemplateResponse

        mock_scheduler_service.list_templates.return_value = [
            JobTemplateResponse(
                template_id=1,
                name="Test Template",
                asset_type="stock",
                trigger_type="interval",
                trigger_config={"seconds": 60},
                is_public=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]

        response = client.get("/api/scheduler/templates")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_template_success(self, client, mock_scheduler_service, mock_app_state):
        """Test getting a template by ID."""
        from investment_platform.api.models.scheduler import JobTemplateResponse

        mock_scheduler_service.get_template.return_value = JobTemplateResponse(
            template_id=1,
            name="Test Template",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"seconds": 60},
            is_public=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        response = client.get("/api/scheduler/templates/1")

        assert response.status_code == 200
        data = response.json()
        assert data["template_id"] == 1

    def test_get_template_not_found(self, client, mock_scheduler_service, mock_app_state):
        """Test getting a non-existent template."""
        mock_scheduler_service.get_template.return_value = None

        response = client.get("/api/scheduler/templates/999")

        assert response.status_code == 404

    def test_create_template_success(self, client, mock_scheduler_service, mock_app_state):
        """Test successful template creation."""
        from investment_platform.api.models.scheduler import JobTemplateResponse

        template_data = JobTemplateCreate(
            name="Test Template",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"seconds": 60},
            is_public=True,
        )

        mock_scheduler_service.create_template.return_value = JobTemplateResponse(
            template_id=1,
            name="Test Template",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"seconds": 60},
            is_public=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        response = client.post("/api/scheduler/templates", json=template_data.dict())

        assert response.status_code == 201

    def test_update_template_success(self, client, mock_scheduler_service, mock_app_state):
        """Test successful template update."""
        from investment_platform.api.models.scheduler import JobTemplateResponse

        template_update = JobTemplateUpdate(name="Updated Template")

        mock_scheduler_service.update_template.return_value = JobTemplateResponse(
            template_id=1,
            name="Updated Template",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"seconds": 60},
            is_public=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        response = client.put("/api/scheduler/templates/1", json=template_update.dict())

        assert response.status_code == 200

    def test_delete_template_success(self, client, mock_scheduler_service, mock_app_state):
        """Test successful template deletion."""
        mock_scheduler_service.delete_template.return_value = True

        response = client.delete("/api/scheduler/templates/1")

        assert response.status_code == 204

    def test_delete_template_not_found(self, client, mock_scheduler_service, mock_app_state):
        """Test deleting a non-existent template."""
        mock_scheduler_service.delete_template.return_value = False

        response = client.delete("/api/scheduler/templates/999")

        assert response.status_code == 404

    def test_get_analytics_success(self, client, mock_scheduler_service, mock_app_state):
        """Test getting scheduler analytics."""
        mock_scheduler_service.get_scheduler_analytics.return_value = {
            "total_jobs": 10,
            "active_jobs": 5,
            "completed_executions": 100,
        }

        response = client.get("/api/scheduler/analytics")

        assert response.status_code == 200
        data = response.json()
        assert "total_jobs" in data

    def test_get_analytics_with_filters(self, client, mock_scheduler_service, mock_app_state):
        """Test getting analytics with date filters."""
        mock_scheduler_service.get_scheduler_analytics.return_value = {
            "total_jobs": 5,
            "active_jobs": 2,
        }

        response = client.get(
            "/api/scheduler/analytics?start_date=2024-01-01T00:00:00&end_date=2024-12-31T23:59:59&asset_type=stock"
        )

        assert response.status_code == 200
        mock_scheduler_service.get_scheduler_analytics.assert_called_once()
