#!/usr/bin/env python3
"""
CLI entry point for data ingestion.

Usage:
    python scripts/run_ingestion.py ingest <symbol> <asset_type> [options]
    python scripts/run_ingestion.py schedule [options]
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from investment_platform.ingestion.cli import main

if __name__ == "__main__":
    main()

