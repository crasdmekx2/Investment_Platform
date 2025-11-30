"""
Tests for scheduler service (CRUD operations).
"""

import pytest
import json
from datetime import datetime, timedelta
from investment_platform.api.services import scheduler_service
from investment_platform.api.models.scheduler import JobCreate, JobUpdate


class TestSchedulerService:
    """Test scheduler service CRUD operations."""

    def test_generate_job_id(self):
        """Test job ID generation."""
        job_id = scheduler_service.generate_job_id("AAPL", "stock")
        assert job_id is not None
        assert "stock" in job_id
        assert "AAPL" in job_id
        
        # Generate another ID - should be different
        job_id2 = scheduler_service.generate_job_id("AAPL", "stock")
        assert job_id != job_id2

    def test_create_job(self, db_transaction):
        """Test creating a job."""
        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        )
        
        job = scheduler_service.create_job(job_data)
        
        assert job is not None
        assert job.symbol == "AAPL"
        assert job.asset_type == "stock"
        assert job.trigger_type == "interval"
        assert job.status == "pending"
        assert job.job_id is not None

    def test_create_job_with_custom_id(self, db_transaction):
        """Test creating a job with custom ID."""
        job_data = JobCreate(
            symbol="BTC-USD",
            asset_type="crypto",
            trigger_type="cron",
            trigger_config={"hour": "9", "minute": "0"},
            job_id="custom_job_id",
        )
        
        job = scheduler_service.create_job(job_data)
        
        assert job.job_id == "custom_job_id"
        assert job.symbol == "BTC-USD"

    def test_get_job(self, db_transaction):
        """Test getting a job."""
        # Create job first
        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        )
        created_job = scheduler_service.create_job(job_data)
        
        # Get job
        job = scheduler_service.get_job(created_job.job_id)
        
        assert job is not None
        assert job.job_id == created_job.job_id
        assert job.symbol == "AAPL"

    def test_get_job_not_found(self, db_transaction):
        """Test getting non-existent job."""
        job = scheduler_service.get_job("nonexistent_job")
        assert job is None

    def test_list_jobs(self, db_transaction):
        """Test listing jobs."""
        # Create multiple jobs
        for i in range(3):
            job_data = JobCreate(
                symbol=f"STOCK{i}",
                asset_type="stock",
                trigger_type="interval",
                trigger_config={"minutes": 5},
            )
            scheduler_service.create_job(job_data)
        
        jobs = scheduler_service.list_jobs()
        
        assert len(jobs) >= 3
        assert all(job.asset_type == "stock" for job in jobs[-3:])

    def test_list_jobs_with_filter(self, db_transaction):
        """Test listing jobs with filters."""
        # Create jobs with different statuses
        job1 = scheduler_service.create_job(JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        ))
        
        # Update one to active
        scheduler_service.update_job_status(job1.job_id, "active")
        
        # Create another job
        job2 = scheduler_service.create_job(JobCreate(
            symbol="MSFT",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        ))
        
        # List active jobs
        active_jobs = scheduler_service.list_jobs(status="active")
        assert len(active_jobs) >= 1
        assert all(job.status == "active" for job in active_jobs)
        
        # List pending jobs
        pending_jobs = scheduler_service.list_jobs(status="pending")
        assert len(pending_jobs) >= 1
        assert all(job.status == "pending" for job in pending_jobs)

    def test_list_jobs_with_asset_type_filter(self, db_transaction):
        """Test listing jobs filtered by asset type."""
        # Create jobs with different asset types
        scheduler_service.create_job(JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        ))
        
        scheduler_service.create_job(JobCreate(
            symbol="BTC-USD",
            asset_type="crypto",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        ))
        
        # List stock jobs
        stock_jobs = scheduler_service.list_jobs(asset_type="stock")
        assert len(stock_jobs) >= 1
        assert all(job.asset_type == "stock" for job in stock_jobs)

    def test_list_jobs_pagination(self, db_transaction):
        """Test listing jobs with pagination."""
        # Create multiple jobs
        for i in range(5):
            job_data = JobCreate(
                symbol=f"STOCK{i}",
                asset_type="stock",
                trigger_type="interval",
                trigger_config={"minutes": 5},
            )
            scheduler_service.create_job(job_data)
        
        # Get first page
        page1 = scheduler_service.list_jobs(limit=2, offset=0)
        assert len(page1) == 2
        
        # Get second page
        page2 = scheduler_service.list_jobs(limit=2, offset=2)
        assert len(page2) == 2
        
        # Should have different jobs
        assert page1[0].job_id != page2[0].job_id

    def test_update_job(self, db_transaction):
        """Test updating a job."""
        # Create job
        job = scheduler_service.create_job(JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        ))
        
        # Update job
        update_data = JobUpdate(
            symbol="MSFT",
            trigger_config={"minutes": 10},
        )
        
        updated_job = scheduler_service.update_job(job.job_id, update_data)
        
        assert updated_job is not None
        assert updated_job.symbol == "MSFT"
        assert updated_job.trigger_config["minutes"] == 10
        assert updated_job.asset_type == "stock"  # Unchanged

    def test_update_job_not_found(self, db_transaction):
        """Test updating non-existent job."""
        update_data = JobUpdate(symbol="MSFT")
        updated_job = scheduler_service.update_job("nonexistent", update_data)
        assert updated_job is None

    def test_update_job_status(self, db_transaction):
        """Test updating job status."""
        # Create job
        job = scheduler_service.create_job(JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        ))
        
        # Update status
        updated_job = scheduler_service.update_job_status(job.job_id, "active")
        
        assert updated_job is not None
        assert updated_job.status == "active"

    def test_delete_job(self, db_transaction):
        """Test deleting a job."""
        # Create job
        job = scheduler_service.create_job(JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        ))
        
        # Delete job
        deleted = scheduler_service.delete_job(job.job_id)
        assert deleted is True
        
        # Verify job is gone
        job_check = scheduler_service.get_job(job.job_id)
        assert job_check is None

    def test_delete_job_not_found(self, db_transaction):
        """Test deleting non-existent job."""
        deleted = scheduler_service.delete_job("nonexistent")
        assert deleted is False

    def test_record_job_execution(self, db_transaction):
        """Test recording job execution."""
        # Create job first
        job = scheduler_service.create_job(JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        ))
        
        # Record execution
        execution_id = scheduler_service.record_job_execution(
            job_id=job.job_id,
            execution_status="success",
            log_id=123,
            execution_time_ms=5000,
        )
        
        assert execution_id > 0
        
        # Verify execution recorded
        executions = scheduler_service.get_job_executions(job.job_id)
        assert len(executions) == 1
        assert executions[0].execution_status == "success"
        assert executions[0].execution_time_ms == 5000

    def test_record_job_execution_with_error(self, db_transaction):
        """Test recording failed job execution."""
        # Create job
        job = scheduler_service.create_job(JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        ))
        
        # Record failed execution
        execution_id = scheduler_service.record_job_execution(
            job_id=job.job_id,
            execution_status="failed",
            error_message="Test error",
            execution_time_ms=1000,
        )
        
        assert execution_id > 0
        
        # Verify execution recorded
        executions = scheduler_service.get_job_executions(job.job_id)
        assert len(executions) == 1
        assert executions[0].execution_status == "failed"
        assert executions[0].error_message == "Test error"

    def test_get_job_executions(self, db_transaction):
        """Test getting job execution history."""
        # Create job
        job = scheduler_service.create_job(JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        ))
        
        # Record multiple executions
        for i in range(3):
            scheduler_service.record_job_execution(
                job_id=job.job_id,
                execution_status="success",
                execution_time_ms=1000 + i,
            )
        
        # Get executions
        executions = scheduler_service.get_job_executions(job.job_id)
        
        assert len(executions) == 3
        assert all(exec.execution_status == "success" for exec in executions)

    def test_get_job_executions_pagination(self, db_transaction):
        """Test getting job executions with pagination."""
        # Create job
        job = scheduler_service.create_job(JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
        ))
        
        # Record multiple executions
        for i in range(5):
            scheduler_service.record_job_execution(
                job_id=job.job_id,
                execution_status="success",
            )
        
        # Get first page
        page1 = scheduler_service.get_job_executions(job.job_id, limit=2, offset=0)
        assert len(page1) == 2
        
        # Get second page
        page2 = scheduler_service.get_job_executions(job.job_id, limit=2, offset=2)
        assert len(page2) == 2

    def test_create_job_with_dates(self, db_transaction):
        """Test creating job with start and end dates."""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        job_data = JobCreate(
            symbol="AAPL",
            asset_type="stock",
            trigger_type="interval",
            trigger_config={"minutes": 5},
            start_date=start_date,
            end_date=end_date,
        )
        
        job = scheduler_service.create_job(job_data)
        
        assert job.start_date == start_date
        assert job.end_date == end_date

    def test_create_job_with_collector_kwargs(self, db_transaction):
        """Test creating job with collector kwargs."""
        job_data = JobCreate(
            symbol="BTC-USD",
            asset_type="crypto",
            trigger_type="interval",
            trigger_config={"minutes": 5},
            collector_kwargs={"granularity": "1h"},
        )
        
        job = scheduler_service.create_job(job_data)
        
        assert job.collector_kwargs is not None
        assert job.collector_kwargs["granularity"] == "1h"

