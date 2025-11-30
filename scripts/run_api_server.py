#!/usr/bin/env python3
"""
FastAPI server entry point for Investment Platform API.

Usage:
    python scripts/run_api_server.py [--host HOST] [--port PORT] [--reload]
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for API server."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Investment Platform API Server"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("API_HOST", "0.0.0.0"),
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("API_PORT", 8000)),
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=os.getenv("API_RELOAD", "false").lower() == "true",
        help="Enable auto-reload for development",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.getenv("API_WORKERS", 1)),
        help="Number of worker processes (default: 1)",
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting API server on {args.host}:{args.port}")
    logger.info(f"Reload: {args.reload}, Workers: {args.workers}")
    
    uvicorn.run(
        "investment_platform.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,  # Reload doesn't work with multiple workers
        log_level="info",
    )


if __name__ == "__main__":
    main()

