#!/usr/bin/env python3
"""
Scheduler daemon entry point for automated data ingestion.

Usage:
    python scripts/run_scheduler.py --config config/scheduler_config.yaml
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from investment_platform.ingestion.scheduler import IngestionScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def main():
    """Main scheduler entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Investment Platform Data Ingestion Scheduler"
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to scheduler configuration file (YAML or JSON)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create scheduler and load config
    scheduler = IngestionScheduler(blocking=True)
    
    try:
        scheduler.load_config(args.config)
        logger.info("Starting scheduler...")
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

