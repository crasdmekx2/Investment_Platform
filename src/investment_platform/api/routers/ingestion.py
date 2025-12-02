"""Ingestion API router."""

import logging
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from psycopg2.extras import RealDictCursor

from investment_platform.api.constants import (
    DEFAULT_PAGE_LIMIT,
    DEFAULT_PAGE_OFFSET,
    DEFAULT_THREAD_POOL_WORKERS,
    MAX_PAGE_LIMIT,
    MIN_PAGE_LIMIT,
)
from investment_platform.api.models.scheduler import (
    CollectRequest,
    CollectResponse,
    CollectionLogResponse,
)
from investment_platform.ingestion.db_connection import get_db_connection
from investment_platform.ingestion.ingestion_engine import IngestionEngine

logger = logging.getLogger(__name__)

router = APIRouter()

# Thread pool for running collection tasks
_executor = ThreadPoolExecutor(max_workers=DEFAULT_THREAD_POOL_WORKERS)


def run_collection_task(job_id: str, request: CollectRequest) -> None:
    """
    Background task to run data collection.

    Updates job status in database instead of in-memory storage.

    Args:
        job_id: Unique job identifier
        request: Collection request parameters
    """
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

        # Update job status in database
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE active_collection_jobs
                    SET status = 'completed',
                        result_data = %s,
                        completed_at = NOW()
                    WHERE job_id = %s
                    """,
                    (json.dumps(result), job_id),
                )
                conn.commit()

        logger.info(f"Collection job {job_id} completed successfully")

    except Exception as e:
        logger.error(
            f"Collection job {job_id} failed for {request.symbol} ({request.asset_type}): {e}",
            exc_info=True,
        )

        # Update job status in database
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE active_collection_jobs
                        SET status = 'failed',
                            error_message = %s,
                            completed_at = NOW()
                        WHERE job_id = %s
                        """,
                        (str(e), job_id),
                    )
                    conn.commit()
        except Exception as db_error:
            logger.error(
                f"Failed to update job status in database for {job_id}: {db_error}",
                exc_info=True,
            )


@router.post("/collect", response_model=CollectResponse)
async def collect_data(
    request: CollectRequest,
    background_tasks: BackgroundTasks,
) -> CollectResponse:
    """
    Trigger immediate data collection (full history or incremental).

    Creates a database-backed job record instead of using in-memory storage.
    This enables persistence across server restarts and scalability.
    """
    import uuid

    job_id = f"collect_{uuid.uuid4().hex[:8]}"

    # Store job info in database
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO active_collection_jobs
                (job_id, symbol, asset_type, status, request_data, started_at)
                VALUES (%s, %s, %s, 'running', %s, NOW())
                """,
                (
                    job_id,
                    request.symbol,
                    request.asset_type,
                    json.dumps(request.dict()),
                ),
            )
            conn.commit()

    # Run collection in background thread pool
    _executor.submit(run_collection_task, job_id, request)

    return CollectResponse(
        job_id=job_id,
        status="running",
        message=f"Collection started for {request.symbol}",
    )


@router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_collection_status(job_id: str) -> Dict[str, Any]:
    """
    Get collection job status.

    Retrieves job status from database instead of in-memory storage.
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM active_collection_jobs WHERE job_id = %s",
                (job_id,),
            )
            job = cursor.fetchone()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    response = {
        "job_id": job_id,
        "status": job["status"],
        "started_at": job["started_at"].isoformat() if job["started_at"] else None,
    }

    if job["completed_at"]:
        response["completed_at"] = job["completed_at"].isoformat()

    if job["result_data"]:
        response["result"] = job["result_data"]

    if job["error_message"]:
        response["error"] = job["error_message"]

    return response


@router.get("/logs", response_model=List[CollectionLogResponse])
async def get_collection_logs(
    asset_id: Optional[int] = Query(None, description="Filter by asset ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(DEFAULT_PAGE_LIMIT, ge=MIN_PAGE_LIMIT, le=MAX_PAGE_LIMIT),
    offset: int = Query(DEFAULT_PAGE_OFFSET, ge=0),
) -> List[CollectionLogResponse]:
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
                logs.append(
                    CollectionLogResponse(
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
                    )
                )

            return logs
