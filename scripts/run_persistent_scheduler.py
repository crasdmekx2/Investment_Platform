#!/usr/bin/env python3
"""
Persistent scheduler daemon entry point.
Loads jobs from database and runs them continuously.

Usage:
    python scripts/run_persistent_scheduler.py
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from investment_platform.ingestion.persistent_scheduler import PersistentScheduler
from investment_platform.ingestion.db_connection import (
    initialize_connection_pool,
    close_connection_pool,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def main():
    """Main persistent scheduler entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Investment Platform Persistent Scheduler Daemon"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--timezone",
        type=str,
        default=None,
        help="Timezone for scheduling (default: system timezone)",
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize database connection pool
    logger.info("Initializing database connection pool...")
    initialize_connection_pool(min_conn=2, max_conn=10)
    
    # Create persistent scheduler
    logger.info("Initializing persistent scheduler...")
    scheduler = PersistentScheduler(blocking=True, timezone=args.timezone)
    
    try:
        # Load jobs from database
        logger.info("Loading jobs from database...")
        loaded_jobs = scheduler.load_jobs_from_database()
        logger.info(f"Loaded {len(loaded_jobs)} jobs from database")
        
        if len(loaded_jobs) == 0:
            logger.warning("No active jobs found in database. Scheduler will wait for jobs to be added.")
        
        # Start the scheduler (this will block)
        logger.info("Starting scheduler...")
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down scheduler...")
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
        logger.info("Closing database connection pool...")
        close_connection_pool()
        logger.info("Scheduler daemon stopped")


if __name__ == "__main__":
    main()

