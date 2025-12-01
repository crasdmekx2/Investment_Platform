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
    JobTemplateCreate,
    JobTemplateUpdate,
    JobTemplateResponse,
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
            # Insert job with retry configuration
            cursor.execute(
                """
                INSERT INTO scheduler_jobs (
                    job_id, symbol, asset_type, trigger_type, trigger_config,
                    start_date, end_date, collector_kwargs, asset_metadata, status,
                    max_retries, retry_delay_seconds, retry_backoff_multiplier
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    job_data.max_retries if job_data.max_retries is not None else 3,
                    job_data.retry_delay_seconds if job_data.retry_delay_seconds is not None else 60,
                    job_data.retry_backoff_multiplier if job_data.retry_backoff_multiplier is not None else 2.0,
                ),
            )
            result = cursor.fetchone()
            
            # Insert dependencies if provided
            if job_data.dependencies:
                for dep in job_data.dependencies:
                    cursor.execute(
                        """
                        INSERT INTO job_dependencies (job_id, depends_on_job_id, condition)
                        VALUES (%s, %s, %s)
                        """,
                        (job_id, dep.depends_on_job_id, dep.condition or "success"),
                    )
            
            conn.commit()
            
            # Record metrics
            try:
                from investment_platform.api import metrics
                metrics.record_job_created(job_data.asset_type, "pending")
            except ImportError:
                pass  # Metrics not available
            
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
            
            if job_data.max_retries is not None:
                updates.append("max_retries = %s")
                params.append(job_data.max_retries)
            
            if job_data.retry_delay_seconds is not None:
                updates.append("retry_delay_seconds = %s")
                params.append(job_data.retry_delay_seconds)
            
            if job_data.retry_backoff_multiplier is not None:
                updates.append("retry_backoff_multiplier = %s")
                params.append(job_data.retry_backoff_multiplier)
            
            if not updates:
                # No updates, just return current job
                return get_job(job_id)
            
            params.append(job_id)
            query = f"UPDATE scheduler_jobs SET {', '.join(updates)} WHERE job_id = %s RETURNING *"
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            # Update dependencies if provided
            if job_data.dependencies is not None:
                # Delete existing dependencies
                cursor.execute("DELETE FROM job_dependencies WHERE job_id = %s", (job_id,))
                
                # Insert new dependencies
                for dep in job_data.dependencies:
                    cursor.execute(
                        """
                        INSERT INTO job_dependencies (job_id, depends_on_job_id, condition)
                        VALUES (%s, %s, %s)
                        """,
                        (job_id, dep.depends_on_job_id, dep.condition or "success"),
                    )
            
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
    error_category: Optional[str] = None,
    execution_time_ms: Optional[int] = None,
    retry_attempt: int = 0,
) -> int:
    """
    Record a job execution.
    
    Args:
        job_id: Job identifier
        execution_status: Status of execution
        log_id: Optional link to data_collection_log
        error_message: Optional error message
        error_category: Optional error category (transient, permanent, system)
        execution_time_ms: Optional execution time in milliseconds
        retry_attempt: Retry attempt number (0 = first attempt)
        
    Returns:
        Execution ID
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO scheduler_job_executions (
                    job_id, log_id, execution_status, error_message, 
                    error_category, execution_time_ms, retry_attempt
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING execution_id
                """,
                (job_id, log_id, execution_status, error_message, 
                 error_category, execution_time_ms, retry_attempt),
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
    from investment_platform.api.models.scheduler import JobDependency
    
    # Parse JSON fields
    trigger_config = json.loads(data["trigger_config"]) if isinstance(data["trigger_config"], str) else data["trigger_config"]
    collector_kwargs = json.loads(data["collector_kwargs"]) if data["collector_kwargs"] and isinstance(data["collector_kwargs"], str) else data["collector_kwargs"]
    asset_metadata = json.loads(data["asset_metadata"]) if data["asset_metadata"] and isinstance(data["asset_metadata"], str) else data["asset_metadata"]
    
    # Load dependencies
    dependencies = None
    job_id = data["job_id"]
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT depends_on_job_id, condition FROM job_dependencies WHERE job_id = %s",
                (job_id,),
            )
            deps = cursor.fetchall()
            if deps:
                dependencies = [
                    JobDependency(
                        depends_on_job_id=dep["depends_on_job_id"],
                        condition=dep["condition"] or "success"
                    )
                    for dep in deps
                ]
    
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
        last_run_at=data.get("last_run_at"),
        next_run_at=data.get("next_run_at"),
        dependencies=dependencies,
        max_retries=data.get("max_retries"),
        retry_delay_seconds=data.get("retry_delay_seconds"),
        retry_backoff_multiplier=float(data["retry_backoff_multiplier"]) if data.get("retry_backoff_multiplier") else None,
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
        error_message=data.get("error_message"),
        error_category=data.get("error_category"),
        execution_time_ms=data.get("execution_time_ms"),
        retry_attempt=data.get("retry_attempt", 0),
        created_at=data["created_at"],
    )


# ============================================================================
# JOB TEMPLATE FUNCTIONS
# ============================================================================

def create_template(template_data: JobTemplateCreate) -> JobTemplateResponse:
    """
    Create a new job template.
    
    Args:
        template_data: Template creation data
        
    Returns:
        Created template response
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO job_templates (
                    name, description, symbol, asset_type, trigger_type, trigger_config,
                    start_date, end_date, collector_kwargs, asset_metadata,
                    max_retries, retry_delay_seconds, retry_backoff_multiplier,
                    is_public, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    template_data.name,
                    template_data.description,
                    template_data.symbol,
                    template_data.asset_type,
                    template_data.trigger_type,
                    json.dumps(template_data.trigger_config),
                    template_data.start_date,
                    template_data.end_date,
                    json.dumps(template_data.collector_kwargs) if template_data.collector_kwargs else None,
                    json.dumps(template_data.asset_metadata) if template_data.asset_metadata else None,
                    template_data.max_retries if template_data.max_retries is not None else 3,
                    template_data.retry_delay_seconds if template_data.retry_delay_seconds is not None else 60,
                    template_data.retry_backoff_multiplier if template_data.retry_backoff_multiplier is not None else 2.0,
                    template_data.is_public if template_data.is_public is not None else False,
                    template_data.created_by,
                ),
            )
            result = cursor.fetchone()
            conn.commit()
            
            return _dict_to_template_response(dict(result))


def get_template(template_id: int) -> Optional[JobTemplateResponse]:
    """
    Get a job template by ID.
    
    Args:
        template_id: Template identifier
        
    Returns:
        Template response or None if not found
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM job_templates WHERE template_id = %s",
                (template_id,),
            )
            result = cursor.fetchone()
            
            if result:
                return _dict_to_template_response(dict(result))
            return None


def list_templates(
    asset_type: Optional[str] = None,
    is_public: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[JobTemplateResponse]:
    """
    List job templates with optional filters.
    
    Args:
        asset_type: Filter by asset type
        is_public: Filter by public/private templates
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of template responses
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = "SELECT * FROM job_templates WHERE 1=1"
            params = []
            
            if asset_type:
                query += " AND asset_type = %s"
                params.append(asset_type)
            
            if is_public is not None:
                query += " AND is_public = %s"
                params.append(is_public)
            
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            return [_dict_to_template_response(dict(row)) for row in results]


def update_template(template_id: int, template_data: JobTemplateUpdate) -> Optional[JobTemplateResponse]:
    """
    Update a job template.
    
    Args:
        template_id: Template identifier
        template_data: Template update data
        
    Returns:
        Updated template response or None if not found
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Build update query dynamically
            updates = []
            params = []
            
            if template_data.name is not None:
                updates.append("name = %s")
                params.append(template_data.name)
            
            if template_data.description is not None:
                updates.append("description = %s")
                params.append(template_data.description)
            
            if template_data.symbol is not None:
                updates.append("symbol = %s")
                params.append(template_data.symbol)
            
            if template_data.asset_type is not None:
                updates.append("asset_type = %s")
                params.append(template_data.asset_type)
            
            if template_data.trigger_type is not None:
                updates.append("trigger_type = %s")
                params.append(template_data.trigger_type)
            
            if template_data.trigger_config is not None:
                updates.append("trigger_config = %s")
                params.append(json.dumps(template_data.trigger_config))
            
            if template_data.start_date is not None:
                updates.append("start_date = %s")
                params.append(template_data.start_date)
            
            if template_data.end_date is not None:
                updates.append("end_date = %s")
                params.append(template_data.end_date)
            
            if template_data.collector_kwargs is not None:
                updates.append("collector_kwargs = %s")
                params.append(json.dumps(template_data.collector_kwargs))
            
            if template_data.asset_metadata is not None:
                updates.append("asset_metadata = %s")
                params.append(json.dumps(template_data.asset_metadata))
            
            if template_data.max_retries is not None:
                updates.append("max_retries = %s")
                params.append(template_data.max_retries)
            
            if template_data.retry_delay_seconds is not None:
                updates.append("retry_delay_seconds = %s")
                params.append(template_data.retry_delay_seconds)
            
            if template_data.retry_backoff_multiplier is not None:
                updates.append("retry_backoff_multiplier = %s")
                params.append(template_data.retry_backoff_multiplier)
            
            if template_data.is_public is not None:
                updates.append("is_public = %s")
                params.append(template_data.is_public)
            
            if not updates:
                # No updates, just return current template
                return get_template(template_id)
            
            params.append(template_id)
            query = f"UPDATE job_templates SET {', '.join(updates)} WHERE template_id = %s RETURNING *"
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            conn.commit()
            
            if result:
                return _dict_to_template_response(dict(result))
            return None


def delete_template(template_id: int) -> bool:
    """
    Delete a job template.
    
    Args:
        template_id: Template identifier
        
    Returns:
        True if deleted, False if not found
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM job_templates WHERE template_id = %s", (template_id,))
            conn.commit()
            return cursor.rowcount > 0


def _dict_to_template_response(data: Dict[str, Any]) -> JobTemplateResponse:
    """Convert database row to JobTemplateResponse."""
    # Parse JSON fields
    trigger_config = json.loads(data["trigger_config"]) if isinstance(data["trigger_config"], str) else data["trigger_config"]
    collector_kwargs = json.loads(data["collector_kwargs"]) if data["collector_kwargs"] and isinstance(data["collector_kwargs"], str) else data["collector_kwargs"]
    asset_metadata = json.loads(data["asset_metadata"]) if data["asset_metadata"] and isinstance(data["asset_metadata"], str) else data["asset_metadata"]
    
    return JobTemplateResponse(
        template_id=data["template_id"],
        name=data["name"],
        description=data.get("description"),
        symbol=data.get("symbol"),
        asset_type=data["asset_type"],
        trigger_type=data["trigger_type"],
        trigger_config=trigger_config,
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        collector_kwargs=collector_kwargs,
        asset_metadata=asset_metadata,
        max_retries=data.get("max_retries"),
        retry_delay_seconds=data.get("retry_delay_seconds"),
        retry_backoff_multiplier=float(data["retry_backoff_multiplier"]) if data.get("retry_backoff_multiplier") else None,
        is_public=data["is_public"],
        created_by=data.get("created_by"),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


# ============================================================================
# ANALYTICS FUNCTIONS
# ============================================================================

def get_scheduler_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    asset_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get scheduler analytics and metrics.
    
    Args:
        start_date: Start date for analytics period
        end_date: End date for analytics period
        asset_type: Filter by asset type
        
    Returns:
        Dictionary with analytics data
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Build date filter
            date_filter = ""
            params = []
            if start_date:
                date_filter += " AND e.started_at >= %s"
                params.append(start_date)
            if end_date:
                date_filter += " AND e.started_at <= %s"
                params.append(end_date)
            
            # Build asset type filter
            asset_filter = ""
            if asset_type:
                asset_filter = " AND j.asset_type = %s"
                params.append(asset_type)
            
            # Total executions
            cursor.execute(
                f"""
                SELECT COUNT(*) as total_executions
                FROM scheduler_job_executions e
                JOIN scheduler_jobs j ON e.job_id = j.job_id
                WHERE 1=1 {date_filter} {asset_filter}
                """,
                params,
            )
            total_executions = cursor.fetchone()["total_executions"]
            
            # Success rate
            cursor.execute(
                f"""
                SELECT 
                    COUNT(*) FILTER (WHERE e.execution_status = 'success') as success_count,
                    COUNT(*) as total_count
                FROM scheduler_job_executions e
                JOIN scheduler_jobs j ON e.job_id = j.job_id
                WHERE 1=1 {date_filter} {asset_filter}
                """,
                params,
            )
            success_row = cursor.fetchone()
            success_count = success_row["success_count"] or 0
            total_count = success_row["total_count"] or 0
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            # Average execution time
            cursor.execute(
                f"""
                SELECT AVG(e.execution_time_ms) as avg_execution_time_ms
                FROM scheduler_job_executions e
                JOIN scheduler_jobs j ON e.job_id = j.job_id
                WHERE e.execution_time_ms IS NOT NULL {date_filter} {asset_filter}
                """,
                params,
            )
            avg_time_row = cursor.fetchone()
            avg_execution_time_ms = float(avg_time_row["avg_execution_time_ms"]) if avg_time_row["avg_execution_time_ms"] else 0
            
            # Failure rate by error category
            cursor.execute(
                f"""
                SELECT 
                    e.error_category,
                    COUNT(*) as failure_count
                FROM scheduler_job_executions e
                JOIN scheduler_jobs j ON e.job_id = j.job_id
                WHERE e.execution_status = 'failed' 
                    AND e.error_category IS NOT NULL
                    {date_filter} {asset_filter}
                GROUP BY e.error_category
                ORDER BY failure_count DESC
                """,
                params,
            )
            failures_by_category = [dict(row) for row in cursor.fetchall()]
            
            # Jobs by asset type
            cursor.execute(
                f"""
                SELECT 
                    j.asset_type,
                    COUNT(DISTINCT j.job_id) as job_count
                FROM scheduler_jobs j
                WHERE 1=1 {asset_filter.replace('j.', '') if asset_filter else ''}
                GROUP BY j.asset_type
                ORDER BY job_count DESC
                """,
                [p for p in params if asset_type is None or p != asset_type],
            )
            jobs_by_asset_type = [dict(row) for row in cursor.fetchall()]
            
            # Execution trends over time (daily)
            cursor.execute(
                f"""
                SELECT 
                    DATE(e.started_at) as date,
                    COUNT(*) as execution_count,
                    COUNT(*) FILTER (WHERE e.execution_status = 'success') as success_count,
                    AVG(e.execution_time_ms) as avg_execution_time_ms
                FROM scheduler_job_executions e
                JOIN scheduler_jobs j ON e.job_id = j.job_id
                WHERE 1=1 {date_filter} {asset_filter}
                GROUP BY DATE(e.started_at)
                ORDER BY date DESC
                LIMIT 30
                """,
                params,
            )
            execution_trends = [dict(row) for row in cursor.fetchall()]
            
            # Top failing jobs
            cursor.execute(
                f"""
                SELECT 
                    j.job_id,
                    j.symbol,
                    j.asset_type,
                    COUNT(*) FILTER (WHERE e.execution_status = 'failed') as failure_count,
                    COUNT(*) as total_executions
                FROM scheduler_job_executions e
                JOIN scheduler_jobs j ON e.job_id = j.job_id
                WHERE 1=1 {date_filter} {asset_filter}
                GROUP BY j.job_id, j.symbol, j.asset_type
                HAVING COUNT(*) FILTER (WHERE e.execution_status = 'failed') > 0
                ORDER BY failure_count DESC
                LIMIT 10
                """,
                params,
            )
            top_failing_jobs = [dict(row) for row in cursor.fetchall()]
            
            return {
                "total_executions": total_executions,
                "success_rate": round(success_rate, 2),
                "success_count": success_count,
                "failure_count": total_count - success_count,
                "avg_execution_time_ms": round(avg_execution_time_ms, 2),
                "failures_by_category": failures_by_category,
                "jobs_by_asset_type": jobs_by_asset_type,
                "execution_trends": execution_trends,
                "top_failing_jobs": top_failing_jobs,
            }

