"""Persistent scheduler that loads jobs from database."""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor

from investment_platform.ingestion.scheduler import IngestionScheduler
from investment_platform.ingestion.db_connection import get_db_connection
from investment_platform.ingestion.error_classifier import classify_error

logger = logging.getLogger(__name__)

# Try to import metrics (optional dependency)
try:
    from investment_platform.api import metrics as metrics_module

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


class PersistentScheduler(IngestionScheduler):
    """Scheduler that persists jobs to database and loads them on startup."""

    def __init__(self, blocking: bool = False, timezone: Optional[str] = None):
        """
        Initialize persistent scheduler.

        Args:
            blocking: Whether to use blocking scheduler (default: False for API server)
            timezone: Timezone for scheduling
        """
        super().__init__(blocking=blocking, timezone=timezone)
        self.logger = logger

    def load_jobs_from_database(self) -> List[str]:
        """
        Load all active jobs from database and add them to scheduler.

        Returns:
            List of job IDs that were loaded
        """
        loaded_job_ids = []

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT * FROM scheduler_jobs
                    WHERE status IN ('active', 'pending')
                    ORDER BY created_at
                    """
                )
                jobs = cursor.fetchall()

                for job_row in jobs:
                    try:
                        job_id = self._load_job_from_row(dict(job_row))
                        loaded_job_ids.append(job_id)
                        self.logger.info(f"Loaded job {job_id} from database")
                    except Exception as e:
                        self.logger.error(
                            f"Failed to load job {job_row['job_id']}: {e}", exc_info=True
                        )

        self.logger.info(f"Loaded {len(loaded_job_ids)} jobs from database")
        return loaded_job_ids

    def _load_job_from_row(self, job_row: Dict[str, Any]) -> str:
        """
        Load a single job from database row and add to scheduler.

        Args:
            job_row: Database row as dictionary

        Returns:
            Job ID
        """
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.interval import IntervalTrigger

        job_id = job_row["job_id"]
        trigger_type = job_row["trigger_type"]
        trigger_config = (
            json.loads(job_row["trigger_config"])
            if isinstance(job_row["trigger_config"], str)
            else job_row["trigger_config"]
        )
        collector_kwargs = (
            json.loads(job_row["collector_kwargs"])
            if job_row["collector_kwargs"] and isinstance(job_row["collector_kwargs"], str)
            else job_row["collector_kwargs"]
        )
        asset_metadata = (
            json.loads(job_row["asset_metadata"])
            if job_row["asset_metadata"] and isinstance(job_row["asset_metadata"], str)
            else job_row["asset_metadata"]
        )

        # Check if this is an execute_now job - these should not be scheduled
        is_execute_now = (
            trigger_config.get("execute_now", False) if isinstance(trigger_config, dict) else False
        )
        if is_execute_now:
            self.logger.info(
                f"Skipping scheduling for execute_now job {job_id} - it should only be triggered manually"
            )
            # If execute_now job has already been executed (has last_run_at), mark as completed
            # Otherwise, mark as active but don't add to scheduler
            if job_row.get("last_run_at"):
                self.sync_job_status(job_id, "completed", None)
                self.logger.info(f"Marked execute_now job {job_id} as completed (already executed)")
            elif job_row["status"] == "pending":
                self.sync_job_status(job_id, "active", None)
            return job_id

        # Create trigger
        if trigger_type == "cron":
            # Remove execute_now from trigger_config if present (shouldn't be, but just in case)
            cron_kwargs = {k: v for k, v in trigger_config.items() if k != "execute_now"}
            trigger = CronTrigger(**cron_kwargs)
        elif trigger_type == "interval":
            # Convert interval config to trigger
            interval_kwargs = {}
            if "weeks" in trigger_config:
                interval_kwargs["weeks"] = trigger_config["weeks"]
            if "days" in trigger_config:
                interval_kwargs["days"] = trigger_config["days"]
            if "hours" in trigger_config:
                interval_kwargs["hours"] = trigger_config["hours"]
            if "minutes" in trigger_config:
                interval_kwargs["minutes"] = trigger_config["minutes"]
            if "seconds" in trigger_config:
                interval_kwargs["seconds"] = trigger_config["seconds"]
            # Remove execute_now from kwargs if present
            interval_kwargs = {k: v for k, v in interval_kwargs.items() if k != "execute_now"}
            trigger = IntervalTrigger(**interval_kwargs)
        else:
            raise ValueError(f"Unknown trigger type: {trigger_type}")

        # Get retry configuration from database (defaults if not set)
        max_retries = job_row.get("max_retries", DEFAULT_MAX_RETRIES)
        retry_delay_seconds = job_row.get("retry_delay_seconds", 60)
        retry_backoff_multiplier = float(job_row.get("retry_backoff_multiplier", 2.0))

        # Add job to scheduler with dependency checking wrapper
        self._add_job_with_dependency_check(
            symbol=job_row["symbol"],
            asset_type=job_row["asset_type"],
            trigger=trigger,
            start_date=job_row["start_date"],
            end_date=job_row["end_date"],
            collector_kwargs=collector_kwargs,
            asset_metadata=asset_metadata,
            job_id=job_id,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
            retry_backoff_multiplier=retry_backoff_multiplier,
        )

        # Get next run time from scheduler and update status to active
        try:
            scheduler_job = self.scheduler.get_job(job_id)
            next_run_at = None
            if scheduler_job and hasattr(scheduler_job, "next_run_time"):
                next_run_at = scheduler_job.next_run_time

            # Update status from pending to active if it was pending
            if job_row["status"] == "pending":
                self.sync_job_status(job_id, "active", next_run_at)
                self.logger.info(f"Updated job {job_id} status from pending to active")
        except Exception as e:
            self.logger.warning(f"Failed to update job {job_id} status: {e}")

        return job_id

    def sync_job_status(self, job_id: str, status: str, next_run_at: Optional[datetime] = None):
        """
        Sync job status with database.

        Args:
            job_id: Job identifier
            status: New status
            next_run_at: Optional next run time
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if next_run_at:
                    cursor.execute(
                        """
                        UPDATE scheduler_jobs
                        SET status = %s, next_run_at = %s, updated_at = NOW()
                        WHERE job_id = %s
                        """,
                        (status, next_run_at, job_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE scheduler_jobs
                        SET status = %s, updated_at = NOW()
                        WHERE job_id = %s
                        """,
                        (status, job_id),
                    )
                conn.commit()

    def record_execution(
        self,
        job_id: str,
        execution_status: str,
        log_id: Optional[int] = None,
        error_message: Optional[str] = None,
        error_category: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        retry_attempt: int = 0,
    ) -> int:
        """
        Record a job execution in database and handle retries if needed.

        Args:
            job_id: Job identifier
            execution_status: Status of execution
            log_id: Optional link to data_collection_log
            error_message: Optional error message
            error_category: Optional error category (transient, permanent, system)
            execution_time_ms: Optional execution time in milliseconds
            retry_attempt: Retry attempt number (0 = first attempt)

        Returns:
            Execution ID
        """
        from investment_platform.api.services import scheduler_service

        execution_id = scheduler_service.record_job_execution(
            job_id=job_id,
            execution_status=execution_status,
            log_id=log_id,
            error_message=error_message,
            error_category=error_category,
            execution_time_ms=execution_time_ms,
            retry_attempt=retry_attempt,
        )

        # Record metrics
        if METRICS_AVAILABLE and execution_time_ms:
            duration_seconds = execution_time_ms / 1000.0
            # Get asset type for metrics
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT asset_type FROM scheduler_jobs WHERE job_id = %s",
                        (job_id,),
                    )
                    job_row = cursor.fetchone()
                    asset_type = job_row["asset_type"] if job_row else "unknown"

            metrics_module.record_job_execution(
                asset_type=asset_type,
                status=execution_status,
                duration_seconds=duration_seconds,
                error_category=error_category,
            )

            # Record retry if this is a retry attempt
            if retry_attempt > 0:
                metrics_module.record_job_retry(job_id, asset_type)

        # Handle retries for failed jobs
        if execution_status == "failed" and error_category == "transient":
            self._handle_retry(job_id, retry_attempt, error_message)

        return execution_id

    def _handle_retry(
        self,
        job_id: str,
        current_retry_attempt: int,
        error_message: Optional[str] = None,
    ):
        """
        Handle retry logic for failed jobs.

        Args:
            job_id: Job identifier
            current_retry_attempt: Current retry attempt number
            error_message: Error message from failed execution
        """
        from apscheduler.triggers.date import DateTrigger

        # Get job retry configuration from database
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT max_retries, retry_delay_seconds, retry_backoff_multiplier, status
                    FROM scheduler_jobs
                    WHERE job_id = %s
                    """,
                    (job_id,),
                )
                job_row = cursor.fetchone()

                if not job_row:
                    self.logger.warning(f"Job {job_id} not found for retry handling")
                    return

                max_retries = job_row.get("max_retries", DEFAULT_MAX_RETRIES)
                retry_delay_seconds = job_row.get("retry_delay_seconds", 60)
                retry_backoff_multiplier = float(job_row.get("retry_backoff_multiplier", 2.0))
                job_status = job_row.get("status")

                # Only retry if job is still active
                if job_status not in ("active", "pending"):
                    self.logger.info(
                        f"Job {job_id} is not active (status: {job_status}), skipping retry"
                    )
                    return

                # Check if we've exceeded max retries
                if current_retry_attempt >= max_retries:
                    self.logger.warning(
                        f"Job {job_id} exceeded max retries ({max_retries}). " f"Marking as failed."
                    )
                    self.sync_job_status(job_id, "failed", None)
                    return

                # Calculate exponential backoff delay
                delay_seconds = int(
                    retry_delay_seconds * (retry_backoff_multiplier**current_retry_attempt)
                )
                retry_time = datetime.now() + timedelta(seconds=delay_seconds)

                self.logger.info(
                    f"Scheduling retry {current_retry_attempt + 1}/{max_retries} for job {job_id} "
                    f"in {delay_seconds} seconds (at {retry_time})"
                )

                # Schedule a one-time retry job
                try:
                    # Get job details for retry
                    cursor.execute(
                        "SELECT * FROM scheduler_jobs WHERE job_id = %s",
                        (job_id,),
                    )
                    job_row = cursor.fetchone()
                    job_dict = dict(job_row)

                    # Create a retry job ID
                    retry_job_id = f"{job_id}_retry_{current_retry_attempt + 1}"

                    # Create a one-time trigger for the retry
                    retry_trigger = DateTrigger(run_date=retry_time)

                    # Load job parameters
                    symbol = job_dict["symbol"]
                    asset_type = job_dict["asset_type"]
                    collector_kwargs = (
                        json.loads(job_dict["collector_kwargs"])
                        if job_dict["collector_kwargs"]
                        and isinstance(job_dict["collector_kwargs"], str)
                        else job_dict["collector_kwargs"]
                    )
                    asset_metadata = (
                        json.loads(job_dict["asset_metadata"])
                        if job_dict["asset_metadata"]
                        and isinstance(job_dict["asset_metadata"], str)
                        else job_dict["asset_metadata"]
                    )

                    # Create retry job function with retry attempt tracking
                    def retry_job() -> Dict[str, Any]:
                        """Execute retry job with error handling."""
                        import time

                        start_time = time.time()

                        self.logger.info(
                            f"Executing retry {current_retry_attempt + 1} for job {job_id}"
                        )

                        # Calculate dates
                        exec_end_date = (
                            job_dict["end_date"]
                            if job_dict["end_date"] is not None
                            else datetime.now()
                        )
                        exec_start_date = (
                            job_dict["start_date"]
                            if job_dict["start_date"] is not None
                            else exec_end_date - timedelta(days=1)
                        )

                        try:
                            result = self.ingestion_engine.ingest(
                                symbol=symbol,
                                asset_type=asset_type,
                                start_date=exec_start_date,
                                end_date=exec_end_date,
                                collector_kwargs=collector_kwargs,
                                asset_metadata=asset_metadata,
                            )

                            execution_time_ms = int((time.time() - start_time) * 1000)
                            result["execution_time_ms"] = execution_time_ms
                            result["retry_attempt"] = current_retry_attempt + 1

                            # Classify error if failed
                            if result.get("status") == "failed":
                                from investment_platform.ingestion.error_classifier import (
                                    classify_error,
                                )

                                error_cat, _ = classify_error(
                                    Exception(result.get("error_message", "")),
                                    result.get("error_message"),
                                )
                                result["error_category"] = error_cat

                            return result
                        except Exception as e:
                            execution_time_ms = int((time.time() - start_time) * 1000)
                            from investment_platform.ingestion.error_classifier import (
                                classify_error,
                            )

                            error_category, recovery_suggestion = classify_error(e, str(e))

                            result = {
                                "asset_id": None,
                                "records_collected": 0,
                                "records_loaded": 0,
                                "status": "failed",
                                "error_message": str(e),
                                "error_category": error_category,
                                "recovery_suggestion": recovery_suggestion,
                                "execution_time_ms": execution_time_ms,
                                "log_id": None,
                                "retry_attempt": current_retry_attempt + 1,
                                "max_retries": max_retries,
                                "retry_delay_seconds": retry_delay_seconds,
                                "retry_backoff_multiplier": retry_backoff_multiplier,
                            }
                            return result

                    # Add retry job to scheduler
                    self.scheduler.add_job(
                        retry_job,
                        trigger=retry_trigger,
                        id=retry_job_id,
                        replace_existing=True,
                    )

                    self.logger.info(f"Scheduled retry job {retry_job_id} for {retry_time}")

                except Exception as e:
                    self.logger.error(
                        f"Failed to schedule retry for job {job_id}: {e}", exc_info=True
                    )

    def add_job_from_database(self, job_id: str) -> bool:
        """
        Add a job from database to the scheduler.
        Called when a job is created via API.

        Args:
            job_id: Job identifier

        Returns:
            True if job was added, False if not found or already exists
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM scheduler_jobs WHERE job_id = %s",
                    (job_id,),
                )
                job_row = cursor.fetchone()

                if not job_row:
                    self.logger.warning(f"Job {job_id} not found in database")
                    return False

                # Check if job is already in scheduler
                try:
                    existing_job = self.scheduler.get_job(job_id)
                    if existing_job:
                        self.logger.info(f"Job {job_id} already in scheduler")
                        return True
                except Exception:
                    pass  # Job doesn't exist, continue

                # Only add if status is active or pending
                job_dict = dict(job_row)
                if job_dict["status"] not in ("active", "pending"):
                    self.logger.info(
                        f"Job {job_id} has status {job_dict['status']}, not adding to scheduler"
                    )
                    return False

                # Check if this is an execute_now job - these should not be scheduled
                trigger_config = (
                    json.loads(job_dict["trigger_config"])
                    if isinstance(job_dict["trigger_config"], str)
                    else job_dict["trigger_config"]
                )
                is_execute_now = (
                    trigger_config.get("execute_now", False)
                    if isinstance(trigger_config, dict)
                    else False
                )
                if is_execute_now:
                    self.logger.info(
                        f"Job {job_id} is execute_now - not adding to scheduler (should be triggered manually)"
                    )
                    # Update status to active but don't add to scheduler
                    if job_dict["status"] == "pending":
                        self.sync_job_status(job_id, "active", None)
                    return True  # Return True since we handled it (just didn't schedule it)

                try:
                    self._load_job_from_row(job_dict)

                    # Get next run time from scheduler and update status if needed
                    try:
                        scheduler_job = self.scheduler.get_job(job_id)
                        next_run_at = None
                        if scheduler_job and hasattr(scheduler_job, "next_run_time"):
                            next_run_at = scheduler_job.next_run_time

                        # Update status from pending to active if it was pending
                        if job_dict["status"] == "pending":
                            self.sync_job_status(job_id, "active", next_run_at)
                            self.logger.info(f"Updated job {job_id} status from pending to active")
                    except Exception as e:
                        self.logger.warning(f"Failed to update job {job_id} status: {e}")

                    self.logger.info(f"Added job {job_id} to scheduler from database")
                    return True
                except Exception as e:
                    self.logger.error(
                        f"Failed to add job {job_id} to scheduler: {e}", exc_info=True
                    )
                    return False

    def remove_job_from_scheduler(self, job_id: str) -> bool:
        """
        Remove a job from the scheduler.
        Called when a job is deleted via API.

        Args:
            job_id: Job identifier

        Returns:
            True if job was removed, False if not found
        """
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed job {job_id} from scheduler")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to remove job {job_id} from scheduler: {e}")
            return False

    def update_job_in_scheduler(self, job_id: str) -> bool:
        """
        Update a job in the scheduler by removing and re-adding it.
        Called when a job is updated via API.

        Args:
            job_id: Job identifier

        Returns:
            True if job was updated, False if not found
        """
        # Remove existing job
        self.remove_job_from_scheduler(job_id)

        # Re-add from database
        return self.add_job_from_database(job_id)

    def pause_job_in_scheduler(self, job_id: str) -> bool:
        """
        Pause a job in the scheduler.

        Args:
            job_id: Job identifier

        Returns:
            True if job was paused, False if not found
        """
        try:
            self.scheduler.pause_job(job_id)
            self.logger.info(f"Paused job {job_id} in scheduler")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to pause job {job_id} in scheduler: {e}")
            return False

    def resume_job_in_scheduler(self, job_id: str) -> bool:
        """
        Resume a paused job in the scheduler.

        Args:
            job_id: Job identifier

        Returns:
            True if job was resumed, False if not found
        """
        try:
            self.scheduler.resume_job(job_id)
            self.logger.info(f"Resumed job {job_id} in scheduler")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to resume job {job_id} in scheduler: {e}")
            return False

    def trigger_job_now(self, job_id: str) -> bool:
        """
        Manually trigger a job execution immediately.
        Can trigger jobs that are in the scheduler or execute_now jobs that aren't scheduled.

        Args:
            job_id: Job identifier

        Returns:
            True if job was triggered, False if not found
        """
        import time
        from datetime import datetime, timedelta

        try:
            # First try to get job from scheduler
            job = self.scheduler.get_job(job_id)
            if job:
                # Execute the job function directly
                self.logger.info(f"Manually triggering job {job_id} from scheduler")
                job.func()
                return True
        except Exception:
            # Job not in scheduler, continue to load from database
            pass

        # If job not in scheduler, load from database and execute directly
        # This handles execute_now jobs that aren't scheduled
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT * FROM scheduler_jobs WHERE job_id = %s",
                        (job_id,),
                    )
                    job_row = cursor.fetchone()

                    if not job_row:
                        self.logger.warning(f"Job {job_id} not found in database")
                        return False

                    job_dict = dict(job_row)

                    # Only trigger if job is active or pending
                    if job_dict["status"] not in ("active", "pending"):
                        self.logger.warning(
                            f"Job {job_id} has status {job_dict['status']}, cannot trigger"
                        )
                        return False

                    # Load job parameters
                    symbol = job_dict["symbol"]
                    asset_type = job_dict["asset_type"]
                    start_date = job_dict["start_date"]
                    end_date = job_dict["end_date"]
                    collector_kwargs = (
                        json.loads(job_dict["collector_kwargs"])
                        if job_dict["collector_kwargs"]
                        and isinstance(job_dict["collector_kwargs"], str)
                        else job_dict["collector_kwargs"]
                    )
                    asset_metadata = (
                        json.loads(job_dict["asset_metadata"])
                        if job_dict["asset_metadata"]
                        and isinstance(job_dict["asset_metadata"], str)
                        else job_dict["asset_metadata"]
                    )

                    # Calculate dates (same logic as in scheduler)
                    exec_end_date = end_date if end_date is not None else datetime.now()
                    exec_start_date = (
                        start_date if start_date is not None else exec_end_date - timedelta(days=1)
                    )

                    # Check if this is an execute_now job
                    trigger_config = (
                        json.loads(job_dict["trigger_config"])
                        if isinstance(job_dict["trigger_config"], str)
                        else job_dict["trigger_config"]
                    )
                    is_execute_now = (
                        trigger_config.get("execute_now", False)
                        if isinstance(trigger_config, dict)
                        else False
                    )

                    # Execute the job directly
                    self.logger.info(
                        f"Manually triggering job {job_id} from database (not in scheduler)"
                    )
                    start_time = time.time()

                    result = self.ingestion_engine.ingest(
                        symbol=symbol,
                        asset_type=asset_type,
                        start_date=exec_start_date,
                        end_date=exec_end_date,
                        collector_kwargs=collector_kwargs,
                        asset_metadata=asset_metadata,
                    )

                    execution_time_ms = int((time.time() - start_time) * 1000)
                    result["execution_time_ms"] = execution_time_ms

                    # Record execution
                    # Partial status indicates some records failed to load - this is a failure that needs investigation
                    execution_status = "success" if result["status"] == "success" else "failed"
                    error_category = result.get("error_category")

                    # If partial, add detailed error message about what went wrong
                    if result["status"] == "partial":
                        total_collected = result.get("records_collected", 0)
                        total_loaded = result.get("records_loaded", 0)
                        dropped = total_collected - total_loaded
                        if not result.get("error_message"):
                            result["error_message"] = (
                                f"Partial failure: Collected {total_collected} records but only loaded {total_loaded}. "
                                f"{dropped} records were dropped. Check logs for validation errors, constraint violations, "
                                f"or data filtering issues."
                            )

                    # If error_category is not set and execution failed, classify the error
                    if error_category is None and execution_status == "failed":
                        error_message = result.get("error_message", "")
                        if error_message:
                            error_category, _ = classify_error(
                                Exception(error_message), error_message
                            )

                    try:
                        self.record_execution(
                            job_id=job_id,
                            execution_status=execution_status,
                            log_id=result.get("log_id"),
                            error_message=result.get("error_message"),
                            error_category=error_category,
                            execution_time_ms=execution_time_ms,
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to record execution for job {job_id}: {e}")

                    # If this is an execute_now job, update job status based on execution result
                    if is_execute_now:
                        if execution_status == "success":
                            self.sync_job_status(job_id, "completed", None)
                            self.logger.info(f"Marked execute_now job {job_id} as completed")
                        else:
                            self.sync_job_status(job_id, "failed", None)
                            self.logger.info(f"Marked execute_now job {job_id} as failed")

                    self.logger.info(
                        f"Completed manual trigger for {symbol}: "
                        f"status={result['status']}, records={result['records_loaded']}, "
                        f"time={execution_time_ms}ms"
                    )

                    return True
        except Exception as e:
            self.logger.error(f"Failed to trigger job {job_id}: {e}", exc_info=True)
            return False

    def check_dependencies_met(self, job_id: str) -> tuple[bool, List[str]]:
        """
        Check if all dependencies for a job are met.

        Args:
            job_id: Job identifier

        Returns:
            Tuple of (all_met, unmet_dependencies)
            all_met: True if all dependencies are met
            unmet_dependencies: List of job IDs that are not yet met
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get all dependencies for this job
                cursor.execute(
                    """
                    SELECT depends_on_job_id, condition
                    FROM job_dependencies
                    WHERE job_id = %s
                    """,
                    (job_id,),
                )
                dependencies = cursor.fetchall()

                if not dependencies:
                    return (True, [])  # No dependencies, can run

                unmet = []
                for dep in dependencies:
                    depends_on_job_id = dep["depends_on_job_id"]
                    condition = dep["condition"] or "success"

                    # Check if dependency job exists and meets condition
                    cursor.execute(
                        """
                        SELECT status, last_run_at
                        FROM scheduler_jobs
                        WHERE job_id = %s
                        """,
                        (depends_on_job_id,),
                    )
                    dep_job = cursor.fetchone()

                    if not dep_job:
                        unmet.append(depends_on_job_id)
                        continue

                    # Check condition
                    if condition == "success":
                        # Check if dependency job's last execution was successful
                        cursor.execute(
                            """
                            SELECT execution_status
                            FROM scheduler_job_executions
                            WHERE job_id = %s
                            ORDER BY started_at DESC
                            LIMIT 1
                            """,
                            (depends_on_job_id,),
                        )
                        last_exec = cursor.fetchone()
                        if not last_exec or last_exec["execution_status"] != "success":
                            unmet.append(depends_on_job_id)
                    elif condition == "complete":
                        # Check if dependency job has completed (success or failed, but not running)
                        if dep_job["status"] not in ("completed", "failed"):
                            # Check if there's a recent execution
                            if not dep_job["last_run_at"]:
                                unmet.append(depends_on_job_id)
                            else:
                                # Check if last execution completed
                                cursor.execute(
                                    """
                                    SELECT execution_status
                                    FROM scheduler_job_executions
                                    WHERE job_id = %s
                                    ORDER BY started_at DESC
                                    LIMIT 1
                                    """,
                                    (depends_on_job_id,),
                                )
                                last_exec = cursor.fetchone()
                                if not last_exec or last_exec["execution_status"] == "running":
                                    unmet.append(depends_on_job_id)
                    elif condition == "any":
                        # Just check if dependency job has run at least once
                        if not dep_job["last_run_at"]:
                            unmet.append(depends_on_job_id)

                return (
                    len(unmet) == 0,
                    [
                        d["depends_on_job_id"]
                        for d in dependencies
                        if d["depends_on_job_id"] in unmet
                    ],
                )

    def _add_job_with_dependency_check(
        self,
        symbol: str,
        asset_type: str,
        trigger: Any,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        collector_kwargs: Optional[Dict[str, Any]] = None,
        asset_metadata: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None,
        max_retries: Optional[int] = None,
        retry_delay_seconds: Optional[int] = None,
        retry_backoff_multiplier: Optional[float] = None,
    ) -> str:
        """
        Add a job to scheduler with dependency checking wrapper.

        This wraps the base add_job to add dependency checking before execution.
        """
        # Call parent add_job to create the job function
        # We'll wrap it to check dependencies
        from apscheduler.triggers.date import DateTrigger

        # Store job parameters for dependency checking
        job_start_date = start_date
        job_end_date = end_date

        # Create wrapped job function that checks dependencies
        def job_with_dependency_check() -> Dict[str, Any]:
            """Execute job with dependency checking."""
            # Check dependencies before executing
            all_met, unmet = self.check_dependencies_met(job_id)
            if not all_met:
                self.logger.info(f"Skipping job {job_id} execution - unmet dependencies: {unmet}")
                return {
                    "asset_id": None,
                    "records_collected": 0,
                    "records_loaded": 0,
                    "status": "skipped",
                    "error_message": f"Unmet dependencies: {', '.join(unmet)}",
                    "execution_time_ms": 0,
                    "log_id": None,
                    "retry_attempt": 0,
                }

            # Dependencies met, execute the actual job
            # We need to call the ingestion engine directly
            import time

            start_time = time.time()

            self.logger.info(f"Executing scheduled ingestion for {symbol} ({asset_type})")

            # Calculate dates
            exec_end_date = job_end_date if job_end_date is not None else datetime.now()
            exec_start_date = (
                job_start_date if job_start_date is not None else exec_end_date - timedelta(days=1)
            )

            try:
                result = self.ingestion_engine.ingest(
                    symbol=symbol,
                    asset_type=asset_type,
                    start_date=exec_start_date,
                    end_date=exec_end_date,
                    collector_kwargs=collector_kwargs,
                    asset_metadata=asset_metadata,
                )

                execution_time_ms = int((time.time() - start_time) * 1000)
                result["execution_time_ms"] = execution_time_ms
                result["retry_attempt"] = 0

                self.logger.info(
                    f"Completed scheduled ingestion for {symbol}: "
                    f"status={result['status']}, records={result['records_loaded']}, "
                    f"time={execution_time_ms}ms"
                )
                return result
            except Exception as e:
                execution_time_ms = int((time.time() - start_time) * 1000)
                error_category, recovery_suggestion = classify_error(e, str(e))

                self.logger.error(f"Failed scheduled ingestion for {symbol}: {e}", exc_info=True)

                result = {
                    "asset_id": None,
                    "records_collected": 0,
                    "records_loaded": 0,
                    "status": "failed",
                    "error_message": str(e),
                    "error_category": error_category,
                    "recovery_suggestion": recovery_suggestion,
                    "execution_time_ms": execution_time_ms,
                    "log_id": None,
                    "retry_attempt": 0,
                    "max_retries": max_retries or 3,
                    "retry_delay_seconds": retry_delay_seconds or 60,
                    "retry_backoff_multiplier": retry_backoff_multiplier or 2.0,
                }
                return result

        # Add wrapped job to scheduler
        self.scheduler.add_job(
            job_with_dependency_check,
            trigger=trigger,
            id=job_id,
        )

        self.logger.info(
            f"Added scheduled job with dependency checking: {job_id} for {symbol} ({asset_type})"
        )

        return job_id

    def check_and_trigger_dependent_jobs(self, completed_job_id: str) -> None:
        """
        Check if any jobs depend on the completed job and trigger them if dependencies are met.

        Args:
            completed_job_id: Job ID that just completed
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Find all jobs that depend on this job
                cursor.execute(
                    """
                    SELECT DISTINCT job_id
                    FROM job_dependencies
                    WHERE depends_on_job_id = %s
                    """,
                    (completed_job_id,),
                )
                dependent_jobs = cursor.fetchall()

                for dep_job in dependent_jobs:
                    dependent_job_id = dep_job["job_id"]

                    # Check if all dependencies are now met
                    all_met, unmet = self.check_dependencies_met(dependent_job_id)

                    if all_met:
                        # Check if job is active and not already running
                        cursor.execute(
                            "SELECT status FROM scheduler_jobs WHERE job_id = %s",
                            (dependent_job_id,),
                        )
                        job_row = cursor.fetchone()

                        if job_row and job_row["status"] in ("active", "pending"):
                            self.logger.info(
                                f"All dependencies met for job {dependent_job_id}, "
                                f"triggering execution"
                            )
                            # Trigger the job
                            try:
                                self.trigger_job_now(dependent_job_id)
                            except Exception as e:
                                self.logger.error(
                                    f"Failed to trigger dependent job {dependent_job_id}: {e}",
                                    exc_info=True,
                                )
                    else:
                        self.logger.debug(
                            f"Job {dependent_job_id} still has unmet dependencies: {unmet}"
                        )
