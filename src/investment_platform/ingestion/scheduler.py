"""Scheduler for automated data ingestion."""

import logging
import signal
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

from investment_platform.ingestion.ingestion_engine import IngestionEngine

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
        
        if blocking:
            self.scheduler = BlockingScheduler(timezone=timezone)
        else:
            self.scheduler = BackgroundScheduler(timezone=timezone)
        
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
            **kwargs: Additional kwargs for scheduler.add_job
            
        Returns:
            Job ID
        """
        if job_id is None:
            job_id = f"{asset_type}_{symbol}_{int(datetime.now().timestamp())}"
        
        # Set default date range if not provided
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=1)
        
        # Create job function
        def ingestion_job():
            self.logger.info(f"Executing scheduled ingestion for {symbol} ({asset_type})")
            result = self.ingestion_engine.ingest(
                symbol=symbol,
                asset_type=asset_type,
                start_date=start_date,
                end_date=end_date,
                collector_kwargs=collector_kwargs,
                asset_metadata=asset_metadata,
            )
            self.logger.info(
                f"Completed scheduled ingestion for {symbol}: "
                f"status={result['status']}, records={result['records_loaded']}"
            )
            return result
        
        # Add job to scheduler
        self.scheduler.add_job(
            ingestion_job,
            trigger=trigger,
            id=job_id,
            **kwargs,
        )
        
        self.logger.info(
            f"Added scheduled job: {job_id} for {symbol} ({asset_type})"
        )
        
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
            
            if "start_date" in job_config:
                start_date = datetime.fromisoformat(job_config["start_date"])
            if "end_date" in job_config:
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
        self.scheduler.shutdown()

    def _job_listener(self, event):
        """Handle job execution events."""
        if event.exception:
            self.logger.error(
                f"Job {event.job_id} failed with exception: {event.exception}",
                exc_info=event.exception,
            )
        else:
            self.logger.debug(f"Job {event.job_id} executed successfully")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)

