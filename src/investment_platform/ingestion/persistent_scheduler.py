"""Persistent scheduler that loads jobs from database."""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor

from investment_platform.ingestion.scheduler import IngestionScheduler
from investment_platform.ingestion.db_connection import get_db_connection

logger = logging.getLogger(__name__)


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
                        self.logger.error(f"Failed to load job {job_row['job_id']}: {e}", exc_info=True)
        
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
        trigger_config = json.loads(job_row["trigger_config"]) if isinstance(job_row["trigger_config"], str) else job_row["trigger_config"]
        collector_kwargs = json.loads(job_row["collector_kwargs"]) if job_row["collector_kwargs"] and isinstance(job_row["collector_kwargs"], str) else job_row["collector_kwargs"]
        asset_metadata = json.loads(job_row["asset_metadata"]) if job_row["asset_metadata"] and isinstance(job_row["asset_metadata"], str) else job_row["asset_metadata"]
        
        # Create trigger
        if trigger_type == "cron":
            trigger = CronTrigger(**trigger_config)
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
            trigger = IntervalTrigger(**interval_kwargs)
        else:
            raise ValueError(f"Unknown trigger type: {trigger_type}")
        
        # Add job to scheduler
        self.add_job(
            symbol=job_row["symbol"],
            asset_type=job_row["asset_type"],
            trigger=trigger,
            start_date=job_row["start_date"],
            end_date=job_row["end_date"],
            collector_kwargs=collector_kwargs,
            asset_metadata=asset_metadata,
            job_id=job_id,
        )
        
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
        execution_time_ms: Optional[int] = None,
    ) -> int:
        """
        Record a job execution in database.
        
        Args:
            job_id: Job identifier
            execution_status: Status of execution
            log_id: Optional link to data_collection_log
            error_message: Optional error message
            execution_time_ms: Optional execution time in milliseconds
            
        Returns:
            Execution ID
        """
        from investment_platform.api.services import scheduler_service
        return scheduler_service.record_job_execution(
            job_id=job_id,
            execution_status=execution_status,
            log_id=log_id,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )

