"""Scheduler API router."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Path

from investment_platform.api.constants import (
    DEFAULT_PAGE_LIMIT,
    DEFAULT_PAGE_OFFSET,
    DEFAULT_EXECUTION_LIMIT,
    MAX_PAGE_LIMIT,
    MIN_PAGE_LIMIT,
)

from investment_platform.api.models.scheduler import (
    JobCreate,
    JobExecutionResponse,
    JobResponse,
    JobTemplateCreate,
    JobTemplateResponse,
    JobTemplateUpdate,
    JobUpdate,
)
from investment_platform.api.services import scheduler_service as scheduler_svc
from investment_platform.collectors.base import (
    APIError,
    DataCollectionError,
    ValidationError,
)
from investment_platform.ingestion.persistent_scheduler import PersistentScheduler

logger = logging.getLogger(__name__)

router = APIRouter()


def get_scheduler(request: Request) -> PersistentScheduler:
    """
    Get scheduler instance from app state.

    Args:
        request: FastAPI request object

    Returns:
        PersistentScheduler instance

    Raises:
        HTTPException: If scheduler is not available
    """
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler is None:
        raise HTTPException(
            status_code=503,
            detail="Scheduler service is not available. Embedded scheduler may be disabled.",
        )
    return scheduler


@router.get(
    "/jobs",
    response_model=List[JobResponse],
    summary="List scheduled jobs",
    description="Retrieve a list of scheduled jobs with optional filtering by status and asset type.",
    responses={
        200: {
            "description": "List of jobs retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "job_id": "stock_AAPL_1234567890_abc123",
                            "symbol": "AAPL",
                            "asset_type": "stock",
                            "trigger_type": "cron",
                            "trigger_config": {"type": "cron", "hour": "9", "minute": "0"},
                            "status": "active",
                            "created_at": "2024-01-01T00:00:00Z",
                        }
                    ]
                }
            },
        },
        400: {"description": "Invalid request parameters"},
        500: {"description": "Internal server error"},
    },
)
async def list_jobs(
    status: Optional[str] = Query(
        None,
        description="Filter by job status",
        examples=["active", "paused", "pending", "completed", "failed"],
    ),
    asset_type: Optional[str] = Query(
        None,
        description="Filter by asset type",
        examples=["stock", "crypto", "forex", "bond", "commodity", "economic_indicator"],
    ),
    limit: int = Query(
        DEFAULT_PAGE_LIMIT,
        ge=MIN_PAGE_LIMIT,
        le=MAX_PAGE_LIMIT,
        description="Maximum number of results",
        example=100,
    ),
    offset: int = Query(
        DEFAULT_PAGE_OFFSET, ge=0, description="Offset for pagination", example=0
    ),
) -> List[JobResponse]:
    """
    List all scheduled jobs with optional filters.
    
    Returns a paginated list of scheduled jobs. Use query parameters to filter
    by status or asset type. Results are ordered by creation date (newest first).
    """
    try:
        jobs = scheduler_svc.list_jobs(
            status=status,
            asset_type=asset_type,
            limit=limit,
            offset=offset,
        )
        return jobs
    except ValueError as e:
        logger.warning(f"Invalid parameters for list_jobs: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Unexpected error listing jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    summary="Get job by ID",
    description="Retrieve details of a specific scheduled job by its ID.",
    responses={
        200: {"description": "Job retrieved successfully"},
        404: {"description": "Job not found"},
    },
)
async def get_job(
    job_id: str = Path(..., description="Unique job identifier", example="stock_AAPL_1234567890_abc123")
) -> JobResponse:
    """
    Get a scheduled job by ID.
    
    Returns the complete job configuration including trigger settings,
    dependencies, and current status.
    """
    job = scheduler_svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=201,
    summary="Create a new scheduled job",
    description="Create a new scheduled job for automated data collection.",
    responses={
        201: {"description": "Job created successfully"},
        400: {"description": "Invalid request data"},
        500: {"description": "Internal server error"},
    },
)
async def create_job(job_data: JobCreate, request: Request) -> JobResponse:
    """
    Create a new scheduled job.
    
    Creates a new scheduled job that will automatically collect data for the
    specified asset at the configured intervals. The job can be triggered
    immediately or scheduled for future execution.
    """
    try:
        job = scheduler_svc.create_job(job_data)

        # Check if this is an immediate execution job (execute_now flag in trigger_config)
        trigger_config = job_data.trigger_config
        is_immediate_only = (
            trigger_config.get("execute_now", False) if isinstance(trigger_config, dict) else False
        )

        # Add job to scheduler so it can be triggered
        # For execute_now jobs, we do NOT add them to scheduler - they should only be triggered manually
        # The add_job_from_database method will check for execute_now and skip scheduling
        scheduler = get_scheduler(request)
        if job.status in ("active", "pending") and not is_immediate_only:
            scheduler.add_job_from_database(job.job_id)
        elif is_immediate_only:
            # For execute_now jobs, just update status to active but don't schedule
            # The job can still be triggered manually via the trigger endpoint
            if job.status == "pending":
                scheduler.sync_job_status(job.job_id, "active", None)

        return job
    except HTTPException:
        raise
    except ValidationError as e:
        logger.warning(f"Validation error creating job: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except ValueError as e:
        logger.warning(f"Invalid parameters for create_job: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.put(
    "/jobs/{job_id}",
    response_model=JobResponse,
    summary="Update a scheduled job",
    description="Update an existing scheduled job's configuration.",
    responses={
        200: {"description": "Job updated successfully"},
        404: {"description": "Job not found"},
        400: {"description": "Invalid request data"},
    },
)
async def update_job(
    job_id: str = Path(..., description="Unique job identifier"),
    job_data: JobUpdate = ...,
    request: Request = ...,
) -> JobResponse:
    """
    Update a scheduled job.
    
    Updates the configuration of an existing scheduled job. Only provided
    fields will be updated. The scheduler will be notified of changes.
    """
    job = scheduler_svc.update_job(job_id, job_data)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Update job in scheduler
    try:
        scheduler = get_scheduler(request)
        scheduler.update_job_in_scheduler(job_id)
    except HTTPException:
        pass  # Scheduler not available, but job was updated in DB

    return job


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str, request: Request) -> None:
    """Delete a scheduled job."""
    deleted = scheduler_svc.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Remove job from scheduler
    try:
        scheduler = get_scheduler(request)
        scheduler.remove_job_from_scheduler(job_id)
    except HTTPException:
        pass  # Scheduler not available, but job was deleted from DB


@router.post("/jobs/{job_id}/pause", response_model=JobResponse)
async def pause_job(job_id: str, request: Request) -> JobResponse:
    """Pause a scheduled job."""
    job = scheduler_svc.update_job_status(job_id, "paused")
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Pause job in scheduler
    try:
        scheduler = get_scheduler(request)
        scheduler.pause_job_in_scheduler(job_id)
    except HTTPException:
        pass  # Scheduler not available, but job status was updated in DB

    return job


@router.post("/jobs/{job_id}/resume", response_model=JobResponse)
async def resume_job(job_id: str, request: Request) -> JobResponse:
    """Resume a paused scheduled job."""
    job = scheduler_svc.update_job_status(job_id, "active")
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Resume job in scheduler
    try:
        scheduler = get_scheduler(request)
        # If job is not in scheduler, add it
        try:
            scheduler.scheduler.get_job(job_id)
            scheduler.resume_job_in_scheduler(job_id)
        except Exception:
            # Job not in scheduler, add it from database
            scheduler.add_job_from_database(job_id)
    except HTTPException:
        pass  # Scheduler not available, but job status was updated in DB

    return job


@router.post("/jobs/{job_id}/trigger", response_model=dict)
async def trigger_job(
    job_id: str, request: Request, background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Manually trigger a scheduled job."""
    import logging

    logger = logging.getLogger(__name__)

    job = scheduler_svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Check if job is in a valid state to trigger
    if job.status not in ("active", "pending"):
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} has status {job.status}, cannot trigger. Job must be active or pending.",
        )

    # Trigger job execution in background to avoid blocking the API
    scheduler = get_scheduler(request)

    def execute_job() -> None:
        """Execute the job in background."""
        try:
            scheduler.trigger_job_now(job_id)
        except DataCollectionError as e:
            logger.error(f"Data collection error in background job {job_id}: {e}", exc_info=True)
        except Exception as e:
            logger.error(
                f"Unexpected error in background job execution for {job_id}: {e}", exc_info=True
            )
            # Note: Exception is logged but not re-raised in background task
            # to prevent background task failure from affecting API response

    # Add job execution to background tasks
    background_tasks.add_task(execute_job)

    # Return immediately - job will execute in background
    return {
        "message": f"Job {job_id} triggered successfully. Execution started in background.",
        "job_id": job_id,
        "status": "triggered",
        "job_status": job.status,
    }


@router.get("/jobs/{job_id}/executions", response_model=List[JobExecutionResponse])
async def get_job_executions(
    job_id: str,
    limit: int = Query(DEFAULT_EXECUTION_LIMIT, ge=MIN_PAGE_LIMIT, le=MAX_PAGE_LIMIT),
    offset: int = Query(DEFAULT_PAGE_OFFSET, ge=0),
) -> List[JobExecutionResponse]:
    """Get execution history for a job."""
    job = scheduler_svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    executions = scheduler_svc.get_job_executions(job_id, limit=limit, offset=offset)
    return executions


# ============================================================================
# JOB TEMPLATE ENDPOINTS
# ============================================================================


@router.get("/templates", response_model=List[JobTemplateResponse])
async def list_templates(
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    is_public: Optional[bool] = Query(None, description="Filter by public/private templates"),
    limit: int = Query(
        DEFAULT_PAGE_LIMIT,
        ge=MIN_PAGE_LIMIT,
        le=MAX_PAGE_LIMIT,
        description="Maximum number of results",
    ),
    offset: int = Query(DEFAULT_PAGE_OFFSET, ge=0, description="Offset for pagination"),
) -> List[JobTemplateResponse]:
    """List all job templates with optional filters."""
    try:
        templates = scheduler_svc.list_templates(
            asset_type=asset_type,
            is_public=is_public,
            limit=limit,
            offset=offset,
        )
        return templates
    except ValueError as e:
        logger.warning(f"Invalid parameters for list_templates: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/templates/{template_id}", response_model=JobTemplateResponse)
async def get_template(template_id: int) -> JobTemplateResponse:
    """Get a job template by ID."""
    template = scheduler_svc.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return template


@router.post("/templates", response_model=JobTemplateResponse, status_code=201)
async def create_template(template_data: JobTemplateCreate) -> JobTemplateResponse:
    """Create a new job template."""
    try:
        template = scheduler_svc.create_template(template_data)
        return template
    except ValidationError as e:
        logger.warning(f"Validation error creating template: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except ValueError as e:
        logger.warning(f"Invalid parameters for create_template: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.put("/templates/{template_id}", response_model=JobTemplateResponse)
async def update_template(
    template_id: int, template_data: JobTemplateUpdate
) -> JobTemplateResponse:
    """Update a job template."""
    template = scheduler_svc.update_template(template_id, template_data)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return template


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(template_id: int) -> None:
    """Delete a job template."""
    deleted = scheduler_svc.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================


@router.get("/analytics")
async def get_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics period"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics period"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
) -> Dict[str, Any]:
    """Get scheduler analytics and metrics."""
    try:
        analytics = scheduler_svc.get_scheduler_analytics(
            start_date=start_date,
            end_date=end_date,
            asset_type=asset_type,
        )
        return analytics
    except ValueError as e:
        logger.warning(f"Invalid parameters for get_analytics: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e
