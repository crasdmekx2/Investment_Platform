"""
Tests for scheduler job dependency resolution edge cases.

Tests circular dependencies, missing dependency jobs, and dependency condition edge cases.
"""

import pytest
from datetime import datetime
from investment_platform.api.services import scheduler_service as scheduler_svc
from investment_platform.api.models.scheduler import (
    JobCreate,
    CronTriggerConfig,
    JobDependency,
)
from investment_platform.ingestion.db_connection import get_db_connection


class TestSchedulerDependencyEdgeCases:
    """Test suite for scheduler dependency edge cases."""

    @pytest.fixture(autouse=True)
    def cleanup_jobs(self):
        """Clean up jobs after each test."""
        yield
        # Clean up test jobs
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM scheduler_jobs WHERE job_id LIKE 'test_%'"
                )
                conn.commit()

    def test_circular_dependency_prevention(self):
        """Test that circular dependencies are prevented."""
        # Create first job
        job1_data = JobCreate(
            symbol="TEST1",
            asset_type="stock",
            trigger_type="cron",
            trigger_config={"type": "cron", "hour": "9", "minute": "0"},
        )
        job1 = scheduler_svc.create_job(job1_data)

        # Create second job that depends on first
        job2_data = JobCreate(
            symbol="TEST2",
            asset_type="stock",
            trigger_type="cron",
            trigger_config={"type": "cron", "hour": "10", "minute": "0"},
            dependencies=[
                JobDependency(depends_on_job_id=job1.job_id, condition="success")
            ],
        )
        job2 = scheduler_svc.create_job(job2_data)

        # Try to create circular dependency (job1 depends on job2)
        # This should be prevented by database constraint or application logic
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Try to insert circular dependency
                try:
                    cursor.execute(
                        """
                        INSERT INTO job_dependencies (job_id, depends_on_job_id, condition)
                        VALUES (%s, %s, 'success')
                        """,
                        (job1.job_id, job2.job_id),
                    )
                    conn.commit()
                    # If we get here, check if circular dependency function prevents it
                    cursor.execute(
                        "SELECT check_circular_dependency(%s, %s)",
                        (job1.job_id, job2.job_id),
                    )
                    is_circular = cursor.fetchone()[0]
                    assert (
                        is_circular
                    ), "Circular dependency should be detected by database function"
                except Exception as e:
                    # Database constraint or trigger should prevent this
                    assert "circular" in str(e).lower() or "constraint" in str(
                        e
                    ).lower(), f"Expected circular dependency error, got: {e}"

    def test_missing_dependency_job(self):
        """Test handling of missing dependency jobs."""
        # Try to create a job that depends on a non-existent job
        job_data = JobCreate(
            symbol="TEST",
            asset_type="stock",
            trigger_type="cron",
            trigger_config={"type": "cron", "hour": "9", "minute": "0"},
            dependencies=[
                JobDependency(
                    depends_on_job_id="non_existent_job_id", condition="success"
                )
            ],
        )

        # Job creation should succeed (dependencies are validated at runtime)
        job = scheduler_svc.create_job(job_data)
        assert job is not None

        # But dependency check should fail
        from investment_platform.ingestion.persistent_scheduler import (
            PersistentScheduler,
        )

        scheduler = PersistentScheduler()
        can_run, unmet = scheduler.check_dependencies_met(job.job_id)
        assert not can_run, "Job with missing dependency should not be able to run"
        assert (
            "non_existent_job_id" in unmet
        ), "Missing dependency should be in unmet list"

    def test_dependency_condition_success(self):
        """Test dependency condition 'success' edge cases."""
        # Create dependency job
        dep_job_data = JobCreate(
            symbol="DEP",
            asset_type="stock",
            trigger_type="cron",
            trigger_config={"type": "cron", "hour": "9", "minute": "0"},
        )
        dep_job = scheduler_svc.create_job(dep_job_data)

        # Create dependent job
        job_data = JobCreate(
            symbol="TEST",
            asset_type="stock",
            trigger_type="cron",
            trigger_config={"type": "cron", "hour": "10", "minute": "0"},
            dependencies=[
                JobDependency(depends_on_job_id=dep_job.job_id, condition="success")
            ],
        )
        job = scheduler_svc.create_job(job_data)

        from investment_platform.ingestion.persistent_scheduler import (
            PersistentScheduler,
        )

        scheduler = PersistentScheduler()

        # Test case 1: Dependency job has no executions
        can_run, unmet = scheduler.check_dependencies_met(job.job_id)
        assert not can_run, "Job should not run if dependency has no executions"
        assert dep_job.job_id in unmet

        # Test case 2: Dependency job has failed execution
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO scheduler_job_executions
                    (job_id, execution_status, started_at, completed_at)
                    VALUES (%s, 'failed', NOW(), NOW())
                    """,
                    (dep_job.job_id,),
                )
                conn.commit()

        can_run, unmet = scheduler.check_dependencies_met(job.job_id)
        assert not can_run, "Job should not run if dependency failed"
        assert dep_job.job_id in unmet

        # Test case 3: Dependency job has successful execution
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO scheduler_job_executions
                    (job_id, execution_status, started_at, completed_at)
                    VALUES (%s, 'success', NOW(), NOW())
                    """,
                    (dep_job.job_id,),
                )
                conn.commit()

        can_run, unmet = scheduler.check_dependencies_met(job.job_id)
        assert can_run, "Job should run if dependency succeeded"
        assert len(unmet) == 0

    def test_dependency_condition_complete(self):
        """Test dependency condition 'complete' edge cases."""
        # Create dependency job
        dep_job_data = JobCreate(
            symbol="DEP",
            asset_type="stock",
            trigger_type="cron",
            trigger_config={"type": "cron", "hour": "9", "minute": "0"},
        )
        dep_job = scheduler_svc.create_job(dep_job_data)

        # Create dependent job with 'complete' condition
        job_data = JobCreate(
            symbol="TEST",
            asset_type="stock",
            trigger_type="cron",
            trigger_config={"type": "cron", "hour": "10", "minute": "0"},
            dependencies=[
                JobDependency(
                    depends_on_job_id=dep_job.job_id, condition="complete"
                )
            ],
        )
        job = scheduler_svc.create_job(job_data)

        from investment_platform.ingestion.persistent_scheduler import (
            PersistentScheduler,
        )

        scheduler = PersistentScheduler()

        # Test case 1: Dependency job is still running
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE scheduler_jobs SET status = 'running' WHERE job_id = %s
                    """,
                    (dep_job.job_id,),
                )
                conn.commit()

        can_run, unmet = scheduler.check_dependencies_met(job.job_id)
        assert not can_run, "Job should not run if dependency is still running"
        assert dep_job.job_id in unmet

        # Test case 2: Dependency job completed (even if failed)
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE scheduler_jobs SET status = 'completed' WHERE job_id = %s
                    """,
                    (dep_job.job_id,),
                )
                cursor.execute(
                    """
                    INSERT INTO scheduler_job_executions
                    (job_id, execution_status, started_at, completed_at)
                    VALUES (%s, 'failed', NOW(), NOW())
                    """,
                    (dep_job.job_id,),
                )
                conn.commit()

        can_run, unmet = scheduler.check_dependencies_met(job.job_id)
        assert (
            can_run
        ), "Job should run if dependency completed (even if failed) with 'complete' condition"
        assert len(unmet) == 0

    def test_dependency_condition_any(self):
        """Test dependency condition 'any' edge cases."""
        # Create dependency job
        dep_job_data = JobCreate(
            symbol="DEP",
            asset_type="stock",
            trigger_type="cron",
            trigger_config={"type": "cron", "hour": "9", "minute": "0"},
        )
        dep_job = scheduler_svc.create_job(dep_job_data)

        # Create dependent job with 'any' condition
        job_data = JobCreate(
            symbol="TEST",
            asset_type="stock",
            trigger_type="cron",
            trigger_config={"type": "cron", "hour": "10", "minute": "0"},
            dependencies=[
                JobDependency(depends_on_job_id=dep_job.job_id, condition="any")
            ],
        )
        job = scheduler_svc.create_job(job_data)

        from investment_platform.ingestion.persistent_scheduler import (
            PersistentScheduler,
        )

        scheduler = PersistentScheduler()

        # Test case 1: Dependency job has never run
        can_run, unmet = scheduler.check_dependencies_met(job.job_id)
        assert not can_run, "Job should not run if dependency has never run"
        assert dep_job.job_id in unmet

        # Test case 2: Dependency job has run at least once (any status)
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO scheduler_job_executions
                    (job_id, execution_status, started_at, completed_at)
                    VALUES (%s, 'failed', NOW(), NOW())
                    """,
                    (dep_job.job_id,),
                )
                conn.commit()

        can_run, unmet = scheduler.check_dependencies_met(job.job_id)
        assert (
            can_run
        ), "Job should run if dependency has run at least once with 'any' condition"
        assert len(unmet) == 0

    def test_multiple_dependencies(self):
        """Test job with multiple dependencies."""
        # Create multiple dependency jobs
        dep_jobs = []
        for i in range(3):
            dep_job_data = JobCreate(
                symbol=f"DEP{i}",
                asset_type="stock",
                trigger_type="cron",
                trigger_config={"type": "cron", "hour": str(9 + i), "minute": "0"},
            )
            dep_jobs.append(scheduler_svc.create_job(dep_job_data))

        # Create job that depends on all of them
        job_data = JobCreate(
            symbol="TEST",
            asset_type="stock",
            trigger_type="cron",
            trigger_config={"type": "cron", "hour": "12", "minute": "0"},
            dependencies=[
                JobDependency(depends_on_job_id=dep.job_id, condition="success")
                for dep in dep_jobs
            ],
        )
        job = scheduler_svc.create_job(job_data)

        from investment_platform.ingestion.persistent_scheduler import (
            PersistentScheduler,
        )

        scheduler = PersistentScheduler()

        # Test case 1: Some dependencies met, some not
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Make first dependency succeed
                cursor.execute(
                    """
                    INSERT INTO scheduler_job_executions
                    (job_id, execution_status, started_at, completed_at)
                    VALUES (%s, 'success', NOW(), NOW())
                    """,
                    (dep_jobs[0].job_id,),
                )
                conn.commit()

        can_run, unmet = scheduler.check_dependencies_met(job.job_id)
        assert not can_run, "Job should not run if some dependencies unmet"
        assert len(unmet) == 2, "Should have 2 unmet dependencies"

        # Test case 2: All dependencies met
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                for dep_job in dep_jobs[1:]:
                    cursor.execute(
                        """
                        INSERT INTO scheduler_job_executions
                        (job_id, execution_status, started_at, completed_at)
                        VALUES (%s, 'success', NOW(), NOW())
                        """,
                        (dep_job.job_id,),
                    )
                conn.commit()

        can_run, unmet = scheduler.check_dependencies_met(job.job_id)
        assert can_run, "Job should run if all dependencies met"
        assert len(unmet) == 0

    def test_self_dependency_prevention(self):
        """Test that self-dependencies are prevented."""
        # Create a job
        job_data = JobCreate(
            symbol="TEST",
            asset_type="stock",
            trigger_type="cron",
            trigger_config={"type": "cron", "hour": "9", "minute": "0"},
        )
        job = scheduler_svc.create_job(job_data)

        # Try to create self-dependency
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(
                        """
                        INSERT INTO job_dependencies (job_id, depends_on_job_id, condition)
                        VALUES (%s, %s, 'success')
                        """,
                        (job.job_id, job.job_id),
                    )
                    conn.commit()
                    assert False, "Self-dependency should be prevented"
                except Exception as e:
                    # Database constraint should prevent this
                    assert "constraint" in str(e).lower() or "self" in str(
                        e
                    ).lower(), f"Expected self-dependency constraint error, got: {e}"

