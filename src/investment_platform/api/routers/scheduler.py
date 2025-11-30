"""Scheduler API router."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from investment_platform.api.models.scheduler import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobExecutionResponse,
)
from investment_platform.api.services import scheduler_service as scheduler_svc

router = APIRouter()


def get_scheduler(request: Request):
    """Get scheduler instance from app state."""
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler is None:
        raise HTTPException(
            status_code=503,
            detail="Scheduler service is not available. Embedded scheduler may be disabled."
        )
    return scheduler


@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """List all scheduled jobs with optional filters."""
    try:
        jobs = scheduler_svc.list_jobs(
            status=status,
            asset_type=asset_type,
            limit=limit,
            offset=offset,
        )
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get a scheduled job by ID."""
    job = scheduler_svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(job_data: JobCreate, request: Request):
    """Create a new scheduled job."""
    try:
        job = scheduler_svc.create_job(job_data)
        
        # Add job to scheduler if it's active or pending
        scheduler = get_scheduler(request)
        if job.status in ("active", "pending"):
            scheduler.add_job_from_database(job.job_id)
        
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(job_id: str, job_data: JobUpdate, request: Request):
    """Update a scheduled job."""
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
async def delete_job(job_id: str, request: Request):
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
async def pause_job(job_id: str, request: Request):
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
async def resume_job(job_id: str, request: Request):
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
async def trigger_job(job_id: str, request: Request):
    """Manually trigger a scheduled job."""
    job = scheduler_svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Trigger job execution
    scheduler = get_scheduler(request)
    triggered = scheduler.trigger_job_now(job_id)
    
    if not triggered:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to trigger job {job_id}. Job may not be in scheduler."
        )
    
    return {
        "message": f"Job {job_id} triggered successfully",
        "job_id": job_id,
        "status": "triggered",
    }


@router.get("/jobs/{job_id}/executions", response_model=List[JobExecutionResponse])
async def get_job_executions(
    job_id: str,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get execution history for a job."""
    job = scheduler_svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    executions = scheduler_svc.get_job_executions(job_id, limit=limit, offset=offset)
    return executions

