"""
Integration tests for scheduler API endpoints with real database and scheduler.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json

try:
    from investment_platform.api.main import app
    from investment_platform.ingestion.persistent_scheduler import APSCHEDULER_AVAILABLE
except ImportError:
    APSCHEDULER_AVAILABLE = False
    app = None


@pytest.mark.skipif(not APSCHEDULER_AVAILABLE, reason="APScheduler not available")
class TestSchedulerAPIIntegration:
    """Test scheduler API integration with database and scheduler."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_create_job_via_api(self, client, db_transaction):
        """Test creating a job via API."""
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
        assert job["status"] == "pending"
        assert job["job_id"] is not None

    def test_create_and_list_jobs(self, client, db_transaction):
        """Test creating and listing jobs."""
        # Create job
        job_data = {
            "symbol": "MSFT",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 10},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        assert create_response.status_code == 201
        
        # List jobs
        list_response = client.get("/api/scheduler/jobs")
        assert list_response.status_code == 200
        
        jobs = list_response.json()
        assert len(jobs) >= 1
        assert any(job["symbol"] == "MSFT" for job in jobs)

    def test_get_job_via_api(self, client, db_transaction):
        """Test getting a job via API."""
        # Create job
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        job_id = create_response.json()["job_id"]
        
        # Get job
        get_response = client.get(f"/api/scheduler/jobs/{job_id}")
        assert get_response.status_code == 200
        
        job = get_response.json()
        assert job["job_id"] == job_id
        assert job["symbol"] == "AAPL"

    def test_update_job_via_api(self, client, db_transaction):
        """Test updating a job via API."""
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
        
        update_response = client.put(f"/api/scheduler/jobs/{job_id}", json=update_data)
        assert update_response.status_code == 200
        
        updated_job = update_response.json()
        assert updated_job["symbol"] == "MSFT"
        assert updated_job["trigger_config"]["minutes"] == 10

    def test_delete_job_via_api(self, client, db_transaction):
        """Test deleting a job via API."""
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
        delete_response = client.delete(f"/api/scheduler/jobs/{job_id}")
        assert delete_response.status_code == 204
        
        # Verify job is gone
        get_response = client.get(f"/api/scheduler/jobs/{job_id}")
        assert get_response.status_code == 404

    def test_pause_job_via_api(self, client, db_transaction):
        """Test pausing a job via API."""
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
        pause_response = client.post(f"/api/scheduler/jobs/{job_id}/pause")
        assert pause_response.status_code == 200
        
        paused_job = pause_response.json()
        assert paused_job["status"] == "paused"

    def test_resume_job_via_api(self, client, db_transaction):
        """Test resuming a job via API."""
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
        resume_response = client.post(f"/api/scheduler/jobs/{job_id}/resume")
        assert resume_response.status_code == 200
        
        resumed_job = resume_response.json()
        assert resumed_job["status"] == "active"

    def test_trigger_job_via_api(self, client, db_transaction):
        """Test triggering a job via API."""
        # Create job
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        job_id = create_response.json()["job_id"]
        
        # Activate job first (so it's in scheduler)
        client.post(f"/api/scheduler/jobs/{job_id}/resume")
        
        # Trigger job
        trigger_response = client.post(f"/api/scheduler/jobs/{job_id}/trigger")
        assert trigger_response.status_code == 200
        
        result = trigger_response.json()
        assert result["status"] == "triggered"
        assert result["job_id"] == job_id

    def test_list_jobs_with_filters(self, client, db_transaction):
        """Test listing jobs with filters."""
        # Create jobs with different statuses
        job1_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        job1_response = client.post("/api/scheduler/jobs", json=job1_data)
        job1_id = job1_response.json()["job_id"]
        client.post(f"/api/scheduler/jobs/{job1_id}/resume")
        
        job2_data = {
            "symbol": "MSFT",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        client.post("/api/scheduler/jobs", json=job2_data)
        
        # Filter by status
        active_response = client.get("/api/scheduler/jobs?status=active")
        assert active_response.status_code == 200
        active_jobs = active_response.json()
        assert all(job["status"] == "active" for job in active_jobs)
        
        # Filter by asset type
        stock_response = client.get("/api/scheduler/jobs?asset_type=stock")
        assert stock_response.status_code == 200
        stock_jobs = stock_response.json()
        assert all(job["asset_type"] == "stock" for job in stock_jobs)

    def test_get_job_executions_via_api(self, client, db_transaction):
        """Test getting job executions via API."""
        # Create job
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        job_id = create_response.json()["job_id"]
        
        # Get executions (should be empty initially)
        executions_response = client.get(f"/api/scheduler/jobs/{job_id}/executions")
        assert executions_response.status_code == 200
        executions = executions_response.json()
        assert isinstance(executions, list)

    def test_create_job_syncs_to_scheduler(self, client, db_transaction):
        """Test that creating a job adds it to scheduler."""
        # This test verifies that when a job is created via API,
        # it gets added to the scheduler instance
        
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        job_id = create_response.json()["job_id"]
        
        # Activate job (which should add it to scheduler)
        client.post(f"/api/scheduler/jobs/{job_id}/resume")
        
        # Verify job exists in scheduler by trying to trigger it
        trigger_response = client.post(f"/api/scheduler/jobs/{job_id}/trigger")
        assert trigger_response.status_code == 200

    def test_update_job_syncs_to_scheduler(self, client, db_transaction):
        """Test that updating a job updates it in scheduler."""
        # Create job
        job_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "trigger_type": "interval",
            "trigger_config": {"minutes": 5},
        }
        
        create_response = client.post("/api/scheduler/jobs", json=job_data)
        job_id = create_response.json()["job_id"]
        
        # Activate job
        client.post(f"/api/scheduler/jobs/{job_id}/resume")
        
        # Update job
        update_data = {
            "trigger_config": {"minutes": 10},
        }
        client.put(f"/api/scheduler/jobs/{job_id}", json=update_data)
        
        # Verify update by getting job
        get_response = client.get(f"/api/scheduler/jobs/{job_id}")
        updated_job = get_response.json()
        assert updated_job["trigger_config"]["minutes"] == 10

    def test_delete_job_removes_from_scheduler(self, client, db_transaction):
        """Test that deleting a job removes it from scheduler."""
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
        
        # Delete job
        client.delete(f"/api/scheduler/jobs/{job_id}")
        
        # Verify job is gone
        get_response = client.get(f"/api/scheduler/jobs/{job_id}")
        assert get_response.status_code == 404

