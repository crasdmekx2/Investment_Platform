"""Ingestion API router."""

import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from psycopg2.extras import RealDictCursor

from investment_platform.api.models.scheduler import (
    CollectRequest,
    CollectResponse,
    CollectionLogResponse,
)
from investment_platform.ingestion.db_connection import get_db_connection
from investment_platform.ingestion.ingestion_engine import IngestionEngine

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active collection jobs (in production, use Redis or similar)
_active_jobs: Dict[str, Dict[str, Any]] = {}

# Thread pool for running collection tasks
_executor = ThreadPoolExecutor(max_workers=5)


def run_collection_task(job_id: str, request: CollectRequest):
    """Background task to run data collection."""
    try:
        engine = IngestionEngine(incremental=request.incremental)
        
        # Calculate default dates if not provided
        end_date = request.end_date or datetime.now()
        start_date = request.start_date or (end_date - timedelta(days=1))
        
        result = engine.ingest(
            symbol=request.symbol,
            asset_type=request.asset_type,
            start_date=start_date,
            end_date=end_date,
            collector_kwargs=request.collector_kwargs,
            asset_metadata=request.asset_metadata,
        )
        
        _active_jobs[job_id]["status"] = "completed"
        _active_jobs[job_id]["result"] = result
        
    except Exception as e:
        logger.error(f"Collection job {job_id} failed: {e}", exc_info=True)
        _active_jobs[job_id]["status"] = "failed"
        _active_jobs[job_id]["error"] = str(e)


@router.post("/collect", response_model=CollectResponse)
async def collect_data(
    request: CollectRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger immediate data collection (full history or incremental)."""
    import uuid
    job_id = f"collect_{uuid.uuid4().hex[:8]}"
    
    # Store job info
    _active_jobs[job_id] = {
        "status": "running",
        "request": request,
        "started_at": datetime.now(),
    }
    
    # Run collection in background thread pool
    _executor.submit(run_collection_task, job_id, request)
    
    return CollectResponse(
        job_id=job_id,
        status="running",
        message=f"Collection started for {request.symbol}",
    )


@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_collection_status(job_id: str):
    """Get collection job status."""
    if job_id not in _active_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = _active_jobs[job_id]
    response = {
        "job_id": job_id,
        "status": job["status"],
        "started_at": job["started_at"].isoformat(),
    }
    
    if "result" in job:
        response["result"] = job["result"]
    
    if "error" in job:
        response["error"] = job["error"]
    
    return response


@router.get("/logs", response_model=List[CollectionLogResponse])
async def get_collection_logs(
    asset_id: Optional[int] = Query(None, description="Filter by asset ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get data collection logs with filtering."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = "SELECT * FROM data_collection_log WHERE 1=1"
            params = []
            
            if asset_id:
                query += " AND asset_id = %s"
                params.append(asset_id)
            
            if status:
                query += " AND status = %s"
                params.append(status)
            
            if start_date:
                query += " AND created_at >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND created_at <= %s"
                params.append(end_date)
            
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            logs = []
            for row in results:
                logs.append(CollectionLogResponse(
                    log_id=row["log_id"],
                    asset_id=row["asset_id"],
                    collector_type=row["collector_type"],
                    start_date=row["start_date"],
                    end_date=row["end_date"],
                    records_collected=row["records_collected"],
                    status=row["status"],
                    error_message=row["error_message"],
                    execution_time_ms=row["execution_time_ms"],
                    created_at=row["created_at"],
                ))
            
            return logs

