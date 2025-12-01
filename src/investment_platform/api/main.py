"""FastAPI application main entry point."""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Initializing API server...")
    initialize_connection_pool(min_conn=2, max_conn=20)
    
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
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
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "investment-platform-api"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Investment Platform API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    from fastapi import Response
    return Response(
        content=metrics.get_metrics(),
        media_type=metrics.get_metrics_content_type()
    )

