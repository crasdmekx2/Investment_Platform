"""FastAPI application main entry point."""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, List, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from investment_platform.api.constants import (
    API_DB_MIN_CONNECTIONS,
    API_DB_MAX_CONNECTIONS,
)
from investment_platform.ingestion.db_connection import (
    initialize_connection_pool,
    close_connection_pool,
)

from investment_platform.api.routers import (
    scheduler,
    collectors,
    ingestion,
    assets,
)
from investment_platform.api import websocket
from investment_platform.api import metrics

logger = logging.getLogger(__name__)


def _get_cors_origins() -> List[str]:
    """
    Get allowed CORS origins from environment variable.

    Returns:
        List of allowed origins. Empty list if CORS_ORIGINS is not set
        (fail-safe for production).

    Environment Variables:
        CORS_ORIGINS: Comma-separated list of allowed origins.
                     Example: "http://localhost:3000,https://example.com"
                     If not set, returns empty list (no CORS allowed).
    """
    cors_origins_env = os.getenv("CORS_ORIGINS", "").strip()

    if not cors_origins_env:
        logger.warning(
            "CORS_ORIGINS environment variable not set. "
            "No CORS origins will be allowed. "
            "Set CORS_ORIGINS to enable CORS (comma-separated list of origins)."
        )
        return []

    origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

    if origins:
        logger.info(f"CORS configured with {len(origins)} allowed origin(s)")
    else:
        logger.warning("CORS_ORIGINS is set but empty. No CORS origins will be allowed.")

    return origins


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifespan context manager for startup and shutdown.

    Yields:
        None: Application lifecycle control
    """
    # Startup
    logger.info("Initializing API server...")
    initialize_connection_pool(min_conn=API_DB_MIN_CONNECTIONS, max_conn=API_DB_MAX_CONNECTIONS)

    # Initialize scheduler if enabled (default: True, can be disabled for separate scheduler service)
    enable_scheduler = os.getenv("ENABLE_EMBEDDED_SCHEDULER", "true").lower() == "true"
    scheduler_instance = None

    if enable_scheduler:
        try:
            from investment_platform.ingestion.persistent_scheduler import PersistentScheduler

            logger.info("Initializing embedded scheduler...")
            scheduler_instance = PersistentScheduler(blocking=False)

            # Load jobs from database
            loaded_jobs = scheduler_instance.load_jobs_from_database()
            logger.info(f"Loaded {len(loaded_jobs)} jobs from database")

            # Start the scheduler
            scheduler_instance.start()
            logger.info("Scheduler started")

            # Store in app state for router access
            app.state.scheduler = scheduler_instance
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}", exc_info=True)
            # Continue without scheduler if initialization fails
            app.state.scheduler = None
    else:
        logger.info("Embedded scheduler disabled (ENABLE_EMBEDDED_SCHEDULER=false)")
        app.state.scheduler = None

    logger.info("API server started")

    yield

    # Shutdown
    logger.info("Shutting down API server...")

    # Shutdown scheduler if it was initialized
    if scheduler_instance is not None:
        try:
            logger.info("Shutting down scheduler...")
            scheduler_instance.shutdown()
            logger.info("Scheduler shut down")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}", exc_info=True)

    close_connection_pool()
    logger.info("API server shut down")


# Create FastAPI application
app = FastAPI(
    title="Investment Platform API",
    description="API for managing data collection and scheduling",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
# Security: CORS origins are controlled via CORS_ORIGINS environment variable
# Default behavior: No origins allowed (fail-safe for production)
# Set CORS_ORIGINS="http://localhost:3000,https://yourdomain.com" to enable
cors_origins = _get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["scheduler"])
app.include_router(collectors.router, prefix="/api/collectors", tags=["collectors"])
app.include_router(ingestion.router, prefix="/api/ingestion", tags=["ingestion"])
app.include_router(assets.router, prefix="/api/assets", tags=["assets"])

# Include WebSocket router
app.include_router(websocket.router, tags=["websocket"])


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Dictionary with health status information
    """
    return {"status": "healthy", "service": "investment-platform-api"}


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint.

    Returns:
        Dictionary with API information
    """
    return {
        "message": "Investment Platform API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    from fastapi import Response

    return Response(content=metrics.get_metrics(), media_type=metrics.get_metrics_content_type())
