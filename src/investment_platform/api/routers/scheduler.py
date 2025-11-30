"""Scheduler API router."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from investment_platform.api.models.scheduler import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobExecutionResponse,
)
from investment_platform.api.services import scheduler_service as scheduler_svc

router = APIRouter()


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
async def create_job(job_data: JobCreate):
    """Create a new scheduled job."""
    try:
        job = scheduler_svc.create_job(job_data)
        return job
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(job_id: str, job_data: JobUpdate):
    """Update a scheduled job."""
    job = scheduler_svc.update_job(job_id, job_data)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str):
    """Delete a scheduled job."""
    deleted = scheduler_svc.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")


@router.post("/jobs/{job_id}/pause", response_model=JobResponse)
async def pause_job(job_id: str):
    """Pause a scheduled job."""
    job = scheduler_svc.update_job_status(job_id, "paused")
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.post("/jobs/{job_id}/resume", response_model=JobResponse)
async def resume_job(job_id: str):
    """Resume a paused scheduled job."""
    job = scheduler_svc.update_job_status(job_id, "active")
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.post("/jobs/{job_id}/trigger", response_model=dict)
async def trigger_job(job_id: str):
    """Manually trigger a scheduled job."""
    # TODO: Implement actual job triggering via scheduler
    # For now, return a placeholder response
    job = scheduler_svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {
        "message": f"Job {job_id} triggered",
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

