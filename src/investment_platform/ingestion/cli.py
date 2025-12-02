"""CLI interface for data ingestion."""

import argparse
import logging
import sys
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from investment_platform.ingestion.ingestion_engine import IngestionEngine
from investment_platform.ingestion.scheduler import IngestionScheduler

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def ingest_command(args):
    """Handle ingest command."""
    setup_logging(args.verbose)

    engine = IngestionEngine(
        incremental=not args.batch,
        on_conflict=args.on_conflict,
        use_copy=not args.no_copy,
    )

    # Parse dates
    if args.end_date:
        end_date = datetime.fromisoformat(args.end_date)
    else:
        end_date = datetime.now()

    if args.start_date:
        start_date = datetime.fromisoformat(args.start_date)
    else:
        # Default to 1 day ago if not specified
        start_date = end_date - timedelta(days=1)

    # Ingest data
    result = engine.ingest(
        symbol=args.symbol,
        asset_type=args.asset_type,
        start_date=start_date,
        end_date=end_date,
    )

    # Print results
    print(f"\nIngestion Results:")
    print(f"  Asset ID: {result['asset_id']}")
    print(f"  Status: {result['status']}")
    print(f"  Records Collected: {result['records_collected']}")
    print(f"  Records Loaded: {result['records_loaded']}")
    print(f"  Execution Time: {result['execution_time_ms']}ms")

    if result["error_message"]:
        print(f"  Error: {result['error_message']}")

    # Exit with error code if failed
    if result["status"] == "failed":
        sys.exit(1)


def schedule_command(args):
    """Handle schedule command."""
    setup_logging(args.verbose)

    scheduler = IngestionScheduler(blocking=True)

    # Load config if provided
    if args.config:
        scheduler.load_config(Path(args.config))
    else:
        # Add single job from command line
        if args.interval:
            # Parse interval (e.g., "1h", "30m", "5s")
            hours = None
            minutes = None
            seconds = None

            interval_str = args.interval.lower()
            if interval_str.endswith("h"):
                hours = int(interval_str[:-1])
            elif interval_str.endswith("m"):
                minutes = int(interval_str[:-1])
            elif interval_str.endswith("s"):
                seconds = int(interval_str[:-1])
            else:
                # Assume minutes if no suffix
                minutes = int(interval_str)

            scheduler.add_interval_job(
                symbol=args.symbol,
                asset_type=args.asset_type,
                hours=hours,
                minutes=minutes,
                seconds=seconds,
            )
        elif args.cron:
            # Parse cron expression (simplified - just minute and hour for now)
            parts = args.cron.split()
            if len(parts) >= 2:
                minute = parts[0] if parts[0] != "*" else None
                hour = parts[1] if parts[1] != "*" else None

                scheduler.add_cron_job(
                    symbol=args.symbol,
                    asset_type=args.asset_type,
                    minute=minute,
                    hour=hour,
                )
            else:
                print("Error: Invalid cron expression. Use format: 'minute hour'")
                sys.exit(1)
        else:
            print("Error: Must specify either --interval, --cron, or --config")
            sys.exit(1)

    # Start scheduler
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nShutting down scheduler...")
        scheduler.shutdown()


def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Investment Platform Data Ingestion CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest data for an asset")
    ingest_parser.add_argument(
        "symbol",
        help="Asset symbol (e.g., AAPL, BTC-USD, USD_EUR)",
    )
    ingest_parser.add_argument(
        "asset_type",
        choices=["stock", "forex", "crypto", "bond", "commodity", "economic_indicator"],
        help="Type of asset",
    )
    ingest_parser.add_argument(
        "--start-date",
        help="Start date (ISO format, e.g., 2024-01-01). Default: 1 day ago",
    )
    ingest_parser.add_argument(
        "--end-date",
        help="End date (ISO format, e.g., 2024-01-02). Default: now",
    )
    ingest_parser.add_argument(
        "--batch",
        action="store_true",
        help="Use batch mode (fetch all data, ignore existing)",
    )
    ingest_parser.add_argument(
        "--on-conflict",
        choices=["do_nothing", "update", "skip"],
        default="do_nothing",
        help="How to handle conflicts (default: do_nothing)",
    )
    ingest_parser.add_argument(
        "--no-copy",
        action="store_true",
        help="Disable PostgreSQL COPY for bulk inserts",
    )
    ingest_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    ingest_parser.set_defaults(func=ingest_command)

    # Schedule command
    schedule_parser = subparsers.add_parser(
        "schedule",
        help="Schedule automated data ingestion",
    )
    schedule_parser.add_argument(
        "--config",
        help="Path to scheduler configuration file (YAML or JSON)",
    )
    schedule_parser.add_argument(
        "--symbol",
        help="Asset symbol (required if not using --config)",
    )
    schedule_parser.add_argument(
        "--asset-type",
        choices=["stock", "forex", "crypto", "bond", "commodity", "economic_indicator"],
        help="Type of asset (required if not using --config)",
    )
    schedule_parser.add_argument(
        "--interval",
        help="Interval for scheduled runs (e.g., '1h', '30m', '5s')",
    )
    schedule_parser.add_argument(
        "--cron",
        help="Cron expression for scheduled runs (e.g., '0 9 * * *' for daily at 9 AM)",
    )
    schedule_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    schedule_parser.set_defaults(func=schedule_command)

    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
