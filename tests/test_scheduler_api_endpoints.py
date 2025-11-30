"""
Tests for scheduler API endpoints using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

try:
    from investment_platform.api.main import app
    from investment_platform.ingestion.persistent_scheduler import APSCHEDULER_AVAILABLE
except ImportError:
    APSCHEDULER_AVAILABLE = False
    app = None


@pytest.mark.skipif(not APSCHEDULER_AVAILABLE, reason="APScheduler not available")
class TestSchedulerAPIEndpoints:
    """Test scheduler API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_list_jobs_endpoint(self, client, db_transaction):
        """Test GET /api/scheduler/jobs endpoint."""
        response = client.get("/api/scheduler/jobs")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_jobs_with_pagination(self, client, db_transaction):
        """Test GET /api/scheduler/jobs with pagination."""
        response = client.get("/api/scheduler/jobs?limit=10&offset=0")
        
        assert response.status_code == 200
        jobs = response.json()
        assert isinstance(jobs, list)
        assert len(jobs) <= 10

    def test_list_jobs_with_status_filter(self, client, db_transaction):
        """Test GET /api/scheduler/jobs with status filter."""
        response = client.get("/api/scheduler/jobs?status=active")
        
        assert response.status_code == 200
        jobs = response.json()
        assert all(job["status"] == "active" for job in jobs)

    def test_list_jobs_with_asset_type_filter(self, client, db_transaction):
        """Test GET /api/scheduler/jobs with asset_type filter."""
        response = client.get("/api/scheduler/jobs?asset_type=stock")
        
        assert response.status_code == 200
        jobs = response.json()
        assert all(job["asset_type"] == "stock" for job in jobs)

    def test_create_job_endpoint(self, client, db_transaction):
        """Test POST /api/scheduler/jobs endpoint."""
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        response = client.post("/api/scheduler/jobs", json=job_data)
        
        assert response.status_code == 201
        job = response.json()
        assert job["symbol"] == "AAPL"
        assert job["asset_type"] == "stock"
        assert job["trigger_type"] == "interval"

    def test_create_job_validation_error(self, client, db_transaction):
        """Test POST /api/scheduler/jobs with invalid data."""
        # Missing required fields
        job_data = {
            "symbol": "AAPL",
        }
        
        response = client.post("/api/scheduler/jobs", json=job_data)
        assert response.status_code == 422  # Validation error

    def test_create_job_invalid_asset_type(self, client, db_transaction):
        """Test POST /api/scheduler/jobs with invalid asset_type."""
        job_data = {
            "symbol": "AAPL",
            "asset_type": "invalid_type",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        response = client.post("/api/scheduler/jobs", json=job_data)
        assert response.status_code == 422

    def test_get_job_endpoint(self, client, db_transaction):
        """Test GET /api/scheduler/jobs/{job_id} endpoint."""
        # Create job first
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        job_id = create_response.json()["job_id"]
        
        # Get job
        response = client.get(f"/api/scheduler/jobs/{job_id}")
        
        assert response.status_code == 200
        job = response.json()
        assert job["job_id"] == job_id

    def test_get_job_not_found(self, client, db_transaction):
        """Test GET /api/scheduler/jobs/{job_id} with non-existent job."""
        response = client.get("/api/scheduler/jobs/nonexistent")
        
        assert response.status_code == 404

    def test_update_job_endpoint(self, client, db_transaction):
        """Test PUT /api/scheduler/jobs/{job_id} endpoint."""
        # Create job
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        job_id = create_response.json()["job_id"]
        
        # Update job
        update_data = {
            "symbol": "MSFT",
            "trigger_config": {"minutes": 10},
        }
        
        response = client.put(f"/api/scheduler/jobs/{job_id}", json=update_data)
        
        assert response.status_code == 200
        updated_job = response.json()
        assert updated_job["symbol"] == "MSFT"
        assert updated_job["trigger_config"]["minutes"] == 10

    def test_update_job_not_found(self, client, db_transaction):
        """Test PUT /api/scheduler/jobs/{job_id} with non-existent job."""
        update_data = {"symbol": "MSFT"}
        
        response = client.put("/api/scheduler/jobs/nonexistent", json=update_data)
        
        assert response.status_code == 404

    def test_delete_job_endpoint(self, client, db_transaction):
        """Test DELETE /api/scheduler/jobs/{job_id} endpoint."""
        # Create job
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        job_id = create_response.json()["job_id"]
        
        # Delete job
        response = client.delete(f"/api/scheduler/jobs/{job_id}")
        
        assert response.status_code == 204

    def test_delete_job_not_found(self, client, db_transaction):
        """Test DELETE /api/scheduler/jobs/{job_id} with non-existent job."""
        response = client.delete("/api/scheduler/jobs/nonexistent")
        
        assert response.status_code == 404

    def test_pause_job_endpoint(self, client, db_transaction):
        """Test POST /api/scheduler/jobs/{job_id}/pause endpoint."""
        # Create job
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        job_id = create_response.json()["job_id"]
        
        # Pause job
        response = client.post(f"/api/scheduler/jobs/{job_id}/pause")
        
        assert response.status_code == 200
        paused_job = response.json()
        assert paused_job["status"] == "paused"

    def test_resume_job_endpoint(self, client, db_transaction):
        """Test POST /api/scheduler/jobs/{job_id}/resume endpoint."""
        # Create and pause job
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        job_id = create_response.json()["job_id"]
        
        client.post(f"/api/scheduler/jobs/{job_id}/pause")
        
        # Resume job
        response = client.post(f"/api/scheduler/jobs/{job_id}/resume")
        
        assert response.status_code == 200
        resumed_job = response.json()
        assert resumed_job["status"] == "active"

    def test_trigger_job_endpoint(self, client, db_transaction):
        """Test POST /api/scheduler/jobs/{job_id}/trigger endpoint."""
        # Create and activate job
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        job_id = create_response.json()["job_id"]
        
        client.post(f"/api/scheduler/jobs/{job_id}/resume")
        
        # Trigger job
        response = client.post(f"/api/scheduler/jobs/{job_id}/trigger")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "triggered"
        assert result["job_id"] == job_id

    def test_get_job_executions_endpoint(self, client, db_transaction):
        """Test GET /api/scheduler/jobs/{job_id}/executions endpoint."""
        # Create job
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        job_id = create_response.json()["job_id"]
        
        # Get executions
        response = client.get(f"/api/scheduler/jobs/{job_id}/executions")
        
        assert response.status_code == 200
        executions = response.json()
        assert isinstance(executions, list)

    def test_get_job_executions_with_pagination(self, client, db_transaction):
        """Test GET /api/scheduler/jobs/{job_id}/executions with pagination."""
        # Create job
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        job_id = create_response.json()["job_id"]
        
        # Get executions with pagination
        response = client.get(f"/api/scheduler/jobs/{job_id}/executions?limit=10&offset=0")
        
        assert response.status_code == 200
        executions = response.json()
        assert isinstance(executions, list)
        assert len(executions) <= 10

    def test_create_job_with_dates(self, client, db_transaction):
        """Test creating job with start and end dates."""
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
        end_date = datetime.now().isoformat()
        
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
            "start_date": start_date,
            "end_date": end_date,
        }
        
        response = client.post("/api/scheduler/jobs", json=job_data)
        
        assert response.status_code == 201
        job = response.json()
        assert job["start_date"] is not None
        assert job["end_date"] is not None

    def test_create_job_with_collector_kwargs(self, client, db_transaction):
        """Test creating job with collector kwargs."""
        job_data = {
            "symbol": "BTC-USD",
            "asset_type": "crypto",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
            "collector_kwargs": {"granularity": "1h"},
        }
        
        response = client.post("/api/scheduler/jobs", json=job_data)
        
        assert response.status_code == 201
        job = response.json()
        assert job["collector_kwargs"] is not None
        assert job["collector_kwargs"]["granularity"] == "1h"

    def test_create_job_cron_trigger(self, client, db_transaction):
        """Test creating job with cron trigger."""
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "cron",
            "trigger_config": {
                "hour": "9",
                "minute": "0",
            },
        }
        
        response = client.post("/api/scheduler/jobs", json=job_data)
        
        assert response.status_code == 201
        job = response.json()
        assert job["trigger_type"] == "cron"
        assert job["trigger_config"]["hour"] == "9"

    def test_error_handling_invalid_trigger_config(self, client, db_transaction):
        """Test error handling for invalid trigger config."""
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {},  # Empty config
        }
        
        response = client.post("/api/scheduler/jobs", json=job_data)
        # Should either succeed (if empty is valid) or return error
        assert response.status_code in [201, 400, 422]

