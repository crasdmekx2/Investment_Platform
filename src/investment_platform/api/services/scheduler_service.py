"""Service for scheduler job management."""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from psycopg2.extras import RealDictCursor

from investment_platform.ingestion.db_connection import get_db_connection
from investment_platform.api.models.scheduler import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobExecutionResponse,
)

logger = logging.getLogger(__name__)


def generate_job_id(symbol: str, asset_type: str) -> str:
    """Generate a unique job ID."""
    timestamp = int(datetime.now().timestamp())
    return f"{asset_type}_{symbol}_{timestamp}_{uuid.uuid4().hex[:8]}"


def create_job(job_data: JobCreate) -> JobResponse:
    """
    Create a new scheduled job.
    
    Args:
        job_data: Job creation data
        
    Returns:
        Created job response
    """
    job_id = job_data.job_id or generate_job_id(job_data.symbol, job_data.asset_type)
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO scheduler_jobs (
                    job_id, symbol, asset_type, trigger_type, trigger_config,
                    start_date, end_date, collector_kwargs, asset_metadata, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    job_id,
                    job_data.symbol,
                    job_data.asset_type,
                    job_data.trigger_type,
                    json.dumps(job_data.trigger_config),
                    job_data.start_date,
                    job_data.end_date,
                    json.dumps(job_data.collector_kwargs) if job_data.collector_kwargs else None,
                    json.dumps(job_data.asset_metadata) if job_data.asset_metadata else None,
                    "pending",
                ),
            )
            result = cursor.fetchone()
            conn.commit()
            
            return _dict_to_job_response(dict(result))


def get_job(job_id: str) -> Optional[JobResponse]:
    """
    Get a scheduled job by ID.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job response or None if not found
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM scheduler_jobs WHERE job_id = %s",
                (job_id,),
            )
            result = cursor.fetchone()
            
            if result:
                return _dict_to_job_response(dict(result))
            return None


def list_jobs(
    status: Optional[str] = None,
    asset_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[JobResponse]:
    """
    List scheduled jobs with optional filters.
    
    Args:
        status: Filter by status
        asset_type: Filter by asset type
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of job responses
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = "SELECT * FROM scheduler_jobs WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = %s"
                params.append(status)
            
            if asset_type:
                query += " AND asset_type = %s"
                params.append(asset_type)
            
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            return [_dict_to_job_response(dict(row)) for row in results]


def update_job(job_id: str, job_data: JobUpdate) -> Optional[JobResponse]:
    """
    Update a scheduled job.
    
    Args:
        job_id: Job identifier
        job_data: Job update data
        
    Returns:
        Updated job response or None if not found
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Build update query dynamically
            updates = []
            params = []
            
            if job_data.symbol is not None:
                updates.append("symbol = %s")
                params.append(job_data.symbol)
            
            if job_data.asset_type is not None:
                updates.append("asset_type = %s")
                params.append(job_data.asset_type)
            
            if job_data.trigger_type is not None:
                updates.append("trigger_type = %s")
                params.append(job_data.trigger_type)
            
            if job_data.trigger_config is not None:
                updates.append("trigger_config = %s")
                params.append(json.dumps(job_data.trigger_config))
            
            if job_data.start_date is not None:
                updates.append("start_date = %s")
                params.append(job_data.start_date)
            
            if job_data.end_date is not None:
                updates.append("end_date = %s")
                params.append(job_data.end_date)
            
            if job_data.collector_kwargs is not None:
                updates.append("collector_kwargs = %s")
                params.append(json.dumps(job_data.collector_kwargs))
            
            if job_data.asset_metadata is not None:
                updates.append("asset_metadata = %s")
                params.append(json.dumps(job_data.asset_metadata))
            
            if job_data.status is not None:
                updates.append("status = %s")
                params.append(job_data.status)
            
            if not updates:
                # No updates, just return current job
                return get_job(job_id)
            
            params.append(job_id)
            query = f"UPDATE scheduler_jobs SET {', '.join(updates)} WHERE job_id = %s RETURNING *"
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            conn.commit()
            
            if result:
                return _dict_to_job_response(dict(result))
            return None


def delete_job(job_id: str) -> bool:
    """
    Delete a scheduled job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        True if deleted, False if not found
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM scheduler_jobs WHERE job_id = %s", (job_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted


def update_job_status(job_id: str, status: str) -> Optional[JobResponse]:
    """
    Update job status.
    
    Args:
        job_id: Job identifier
        status: New status
        
    Returns:
        Updated job response or None if not found
    """
    return update_job(job_id, JobUpdate(status=status))


def record_job_execution(
    job_id: str,
    execution_status: str,
    log_id: Optional[int] = None,
    error_message: Optional[str] = None,
    execution_time_ms: Optional[int] = None,
) -> int:
    """
    Record a job execution.
    
    Args:
        job_id: Job identifier
        execution_status: Status of execution
        log_id: Optional link to data_collection_log
        error_message: Optional error message
        execution_time_ms: Optional execution time in milliseconds
        
    Returns:
        Execution ID
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO scheduler_job_executions (
                    job_id, log_id, execution_status, error_message, execution_time_ms
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING execution_id
                """,
                (job_id, log_id, execution_status, error_message, execution_time_ms),
            )
            execution_id = cursor.fetchone()[0]
            
            # Update job's last_run_at
            cursor.execute(
                "UPDATE scheduler_jobs SET last_run_at = NOW() WHERE job_id = %s",
                (job_id,),
            )
            
            conn.commit()
            return execution_id


def get_job_executions(
    job_id: str,
    limit: int = 50,
    offset: int = 0,
) -> List[JobExecutionResponse]:
    """
    Get execution history for a job.
    
    Args:
        job_id: Job identifier
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of execution responses
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT * FROM scheduler_job_executions
                WHERE job_id = %s
                ORDER BY started_at DESC
                LIMIT %s OFFSET %s
                """,
                (job_id, limit, offset),
            )
            results = cursor.fetchall()
            
            return [_dict_to_execution_response(dict(row)) for row in results]


def _dict_to_job_response(data: Dict[str, Any]) -> JobResponse:
    """Convert database row to JobResponse."""
    # Parse JSON fields
    trigger_config = json.loads(data["trigger_config"]) if isinstance(data["trigger_config"], str) else data["trigger_config"]
    collector_kwargs = json.loads(data["collector_kwargs"]) if data["collector_kwargs"] and isinstance(data["collector_kwargs"], str) else data["collector_kwargs"]
    asset_metadata = json.loads(data["asset_metadata"]) if data["asset_metadata"] and isinstance(data["asset_metadata"], str) else data["asset_metadata"]
    
    return JobResponse(
        job_id=data["job_id"],
        symbol=data["symbol"],
        asset_type=data["asset_type"],
        trigger_type=data["trigger_type"],
        trigger_config=trigger_config,
        start_date=data["start_date"],
        end_date=data["end_date"],
        collector_kwargs=collector_kwargs,
        asset_metadata=asset_metadata,
        status=data["status"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        last_run_at=data["last_run_at"],
        next_run_at=data["next_run_at"],
    )


def _dict_to_execution_response(data: Dict[str, Any]) -> JobExecutionResponse:
    """Convert database row to JobExecutionResponse."""
    return JobExecutionResponse(
        execution_id=data["execution_id"],
        job_id=data["job_id"],
        log_id=data["log_id"],
        execution_status=data["execution_status"],
        started_at=data["started_at"],
        completed_at=data["completed_at"],
        error_message=data["error_message"],
        execution_time_ms=data["execution_time_ms"],
        created_at=data["created_at"],
    )

