"""Scheduler for automated data ingestion."""

import logging
import os
import signal
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
    from apscheduler.executors.pool import ThreadPoolExecutor as APSchedulerThreadPoolExecutor

    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

from investment_platform.ingestion.ingestion_engine import IngestionEngine
from investment_platform.ingestion.error_classifier import classify_error

logger = logging.getLogger(__name__)


class IngestionScheduler:
    """Scheduler for automated data ingestion runs."""

    def __init__(
        self,
        blocking: bool = True,
        timezone: Optional[str] = None,
    ):
        """
        Initialize the IngestionScheduler.

        Args:
            blocking: Whether to use blocking scheduler (runs in foreground)
            timezone: Timezone for scheduling (default: system timezone)
        """
        if not APSCHEDULER_AVAILABLE:
            raise ImportError(
                "APScheduler is required for scheduling. "
                "Install it with: pip install apscheduler"
            )

        self.logger = logger
        self.ingestion_engine = IngestionEngine()

        # Get max workers from environment variable
        from investment_platform.api.constants import DEFAULT_SCHEDULER_MAX_WORKERS

        max_workers = int(os.getenv("SCHEDULER_MAX_WORKERS", str(DEFAULT_SCHEDULER_MAX_WORKERS)))

        if blocking:
            self.scheduler = BlockingScheduler(timezone=timezone)
        else:
            # Configure executor for parallel job execution
            executors = {"default": APSchedulerThreadPoolExecutor(max_workers=max_workers)}
            job_defaults = {
                "coalesce": False,  # Don't combine multiple pending executions
                "max_instances": 3,  # Allow up to 3 concurrent instances of same job
            }
            self.scheduler = BackgroundScheduler(
                timezone=timezone, executors=executors, job_defaults=job_defaults
            )
            self.logger.info(
                f"Configured scheduler with {max_workers} worker threads for parallel execution"
            )

        # Register event listeners
        self.scheduler.add_listener(
            self._job_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR,
        )

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def add_job(
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
        **kwargs: Any,
    ) -> str:
        """
        Add an ingestion job to the scheduler.

        Args:
            symbol: Asset symbol
            asset_type: Type of asset
            trigger: APScheduler trigger (CronTrigger, IntervalTrigger, etc.)
            start_date: Start date for data collection (default: yesterday)
            end_date: End date for data collection (default: today)
            collector_kwargs: Additional kwargs for collector
            asset_metadata: Additional metadata for asset
            job_id: Optional job ID (default: auto-generated)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay_seconds: Initial delay in seconds before first retry (default: 60)
            retry_backoff_multiplier: Multiplier for exponential backoff (default: 2.0)
            **kwargs: Additional kwargs for scheduler.add_job

        Returns:
            Job ID
        """
        if job_id is None:
            job_id = f"{asset_type}_{symbol}_{int(datetime.now().timestamp())}"

        # Store retry configuration
        from investment_platform.api.constants import DEFAULT_MAX_RETRIES

        job_max_retries = max_retries if max_retries is not None else DEFAULT_MAX_RETRIES
        job_retry_delay = retry_delay_seconds if retry_delay_seconds is not None else 60
        job_backoff_multiplier = (
            retry_backoff_multiplier if retry_backoff_multiplier is not None else 2.0
        )

        # Store date configuration (None means use defaults calculated at runtime)
        # Dates are calculated fresh at execution time to support incremental collection
        job_start_date = start_date
        job_end_date = end_date

        # Create job function
        def ingestion_job():
            import time

            start_time = time.time()

            self.logger.info(f"Executing scheduled ingestion for {symbol} ({asset_type})")

            # Calculate dates fresh at execution time
            # If dates were provided at job creation, use them; otherwise calculate defaults
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

                # Calculate execution time
                execution_time_ms = int((time.time() - start_time) * 1000)
                result["execution_time_ms"] = execution_time_ms

                self.logger.info(
                    f"Completed scheduled ingestion for {symbol}: "
                    f"status={result['status']}, records={result['records_loaded']}, "
                    f"time={execution_time_ms}ms"
                )
                return result
            except Exception as e:
                # Calculate execution time even on error
                execution_time_ms = int((time.time() - start_time) * 1000)
                self.logger.error(f"Failed scheduled ingestion for {symbol}: {e}", exc_info=True)

                # Classify error
                error_category, recovery_suggestion = classify_error(e, str(e))

                # ingest() should never raise, but if it does, create a result dict
                # This ensures we always return a result that can be logged
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
                    "max_retries": job_max_retries,
                    "retry_delay_seconds": job_retry_delay,
                    "retry_backoff_multiplier": job_backoff_multiplier,
                }
                return result

        # Add job to scheduler
        self.scheduler.add_job(
            ingestion_job,
            trigger=trigger,
            id=job_id,
            **kwargs,
        )

        self.logger.info(f"Added scheduled job: {job_id} for {symbol} ({asset_type})")

        return job_id

    def add_interval_job(
        self,
        symbol: str,
        asset_type: str,
        hours: Optional[int] = None,
        minutes: Optional[int] = None,
        seconds: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs: Any,
    ) -> str:
        """
        Add a job that runs at regular intervals.

        Args:
            symbol: Asset symbol
            asset_type: Type of asset
            hours: Interval in hours
            minutes: Interval in minutes
            seconds: Interval in seconds
            start_date: Start date for data collection
            end_date: End date for data collection
            **kwargs: Additional kwargs for add_job

        Returns:
            Job ID
        """
        # Create interval trigger
        trigger = IntervalTrigger(
            hours=hours,
            minutes=minutes,
            seconds=seconds,
        )

        return self.add_job(
            symbol=symbol,
            asset_type=asset_type,
            trigger=trigger,
            start_date=start_date,
            end_date=end_date,
            **kwargs,
        )

    def add_cron_job(
        self,
        symbol: str,
        asset_type: str,
        year: Optional[str] = None,
        month: Optional[str] = None,
        day: Optional[str] = None,
        week: Optional[str] = None,
        day_of_week: Optional[str] = None,
        hour: Optional[str] = None,
        minute: Optional[str] = None,
        second: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs: Any,
    ) -> str:
        """
        Add a job that runs on a cron schedule.

        Args:
            symbol: Asset symbol
            asset_type: Type of asset
            year: Year expression (e.g., '2020-2025', '*')
            month: Month expression (e.g., '1-12', '*')
            day: Day of month expression (e.g., '1-31', '*')
            week: Week expression
            day_of_week: Day of week expression (e.g., 'mon-fri', '0-6')
            hour: Hour expression (e.g., '0-23', '*')
            minute: Minute expression (e.g., '0-59', '*/5')
            second: Second expression (e.g., '0-59', '*')
            start_date: Start date for data collection
            end_date: End date for data collection
            **kwargs: Additional kwargs for add_job

        Returns:
            Job ID
        """
        # Create cron trigger
        trigger = CronTrigger(
            year=year,
            month=month,
            day=day,
            week=week,
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            second=second,
        )

        return self.add_job(
            symbol=symbol,
            asset_type=asset_type,
            trigger=trigger,
            start_date=start_date,
            end_date=end_date,
            **kwargs,
        )

    def load_config(self, config_path: Path) -> List[str]:
        """
        Load scheduler configuration from YAML/JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            List of job IDs added
        """
        try:
            import yaml
        except ImportError:
            yaml = None

        import json

        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Load config based on extension
        if config_path.suffix in [".yaml", ".yml"]:
            if yaml is None:
                raise ImportError(
                    "PyYAML is required for YAML config files. "
                    "Install it with: pip install pyyaml"
                )
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        elif config_path.suffix == ".json":
            with open(config_path, "r") as f:
                config = json.load(f)
        else:
            raise ValueError(
                f"Unsupported config file format: {config_path.suffix}. "
                "Use .yaml, .yml, or .json"
            )

        job_ids = []

        # Process jobs from config
        jobs = config.get("jobs", [])

        for job_config in jobs:
            symbol = job_config["symbol"]
            asset_type = job_config["asset_type"]

            # Parse trigger
            trigger_config = job_config.get("trigger", {})
            trigger_type = trigger_config.get("type", "interval")

            if trigger_type == "interval":
                trigger = IntervalTrigger(**trigger_config.get("params", {}))
            elif trigger_type == "cron":
                trigger = CronTrigger(**trigger_config.get("params", {}))
            else:
                raise ValueError(f"Unknown trigger type: {trigger_type}")

            # Parse dates
            start_date = None
            end_date = None

            if "start_date" in job_config and job_config["start_date"] is not None:
                start_date = datetime.fromisoformat(job_config["start_date"])
            if "end_date" in job_config and job_config["end_date"] is not None:
                end_date = datetime.fromisoformat(job_config["end_date"])

            # Add job
            job_id = self.add_job(
                symbol=symbol,
                asset_type=asset_type,
                trigger=trigger,
                start_date=start_date,
                end_date=end_date,
                collector_kwargs=job_config.get("collector_kwargs"),
                asset_metadata=job_config.get("asset_metadata"),
                job_id=job_config.get("job_id"),
            )

            job_ids.append(job_id)

        self.logger.info(f"Loaded {len(job_ids)} jobs from config file")

        return job_ids

    def start(self):
        """Start the scheduler."""
        self.logger.info("Starting ingestion scheduler...")
        self.scheduler.start()

    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        self.logger.info("Shutting down ingestion scheduler...")
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
        except Exception as e:
            self.logger.warning(f"Error during shutdown: {e}")

    def _job_listener(self, event):
        """Handle job execution events."""
        import time

        job_id = event.job_id
        execution_status = "success"
        error_message = None
        error_category = None
        execution_time_ms = None
        log_id = None
        retry_attempt = 0  # Default to 0 for first attempt

        # Get result from event if available
        if hasattr(event, "retval") and isinstance(event.retval, dict):
            result = event.retval
            # Get execution time and log_id from result (calculated in job function)
            execution_time_ms = result.get("execution_time_ms")
            log_id = result.get("log_id")
            retry_attempt = result.get("retry_attempt", 0)

            # Determine status and error message from result
            result_status = result.get("status", "unknown")
            if result_status == "failed":
                execution_status = "failed"
                error_message = result.get("error_message") or "Ingestion failed"
                error_category = result.get("error_category")
            elif result_status == "partial":
                execution_status = "success"  # Partial success is still considered success
            else:
                execution_status = "success"
        elif event.exception:
            # Fallback: if there's an exception and no result, use exception info
            execution_status = "failed"
            error_message = str(event.exception)
            error_category, _ = classify_error(event.exception, error_message)
            self.logger.error(
                f"Job {job_id} failed with exception: {event.exception}",
                exc_info=event.exception,
            )
        else:
            self.logger.debug(f"Job {job_id} executed successfully")

        # Fallback: try to calculate execution time from event times if not available
        if (
            execution_time_ms is None
            and hasattr(event, "scheduled_run_time")
            and hasattr(event, "run_time")
        ):
            try:
                execution_time_ms = int(
                    (event.run_time - event.scheduled_run_time).total_seconds() * 1000
                )
            except Exception:
                pass

        # Record execution if this is a PersistentScheduler
        if hasattr(self, "record_execution"):
            try:
                self.record_execution(
                    job_id=job_id,
                    execution_status=execution_status,
                    log_id=log_id,
                    error_message=error_message,
                    error_category=error_category,
                    execution_time_ms=execution_time_ms,
                    retry_attempt=retry_attempt,
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to record execution for job {job_id}: {e}", exc_info=True
                )

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
