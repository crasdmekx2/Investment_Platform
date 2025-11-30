"""FastAPI application main entry point."""

import logging
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

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Initializing API server...")
    initialize_connection_pool(min_conn=2, max_conn=20)
    logger.info("API server started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API server...")
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

