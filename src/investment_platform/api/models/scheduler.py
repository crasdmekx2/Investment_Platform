"""Pydantic models for scheduler API."""

from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field, field_validator


class TriggerConfigBase(BaseModel):
    """Base trigger configuration."""
    pass


class CronTriggerConfig(TriggerConfigBase):
    """Cron trigger configuration."""
    type: Literal["cron"] = "cron"
    year: Optional[str] = None
    month: Optional[str] = None
    day: Optional[str] = None
    week: Optional[str] = None
    day_of_week: Optional[str] = None
    hour: Optional[str] = None
    minute: Optional[str] = None
    second: Optional[str] = "0"


class IntervalTriggerConfig(TriggerConfigBase):
    """Interval trigger configuration."""
    type: Literal["interval"] = "interval"
    weeks: Optional[int] = None
    days: Optional[int] = None
    hours: Optional[int] = None
    minutes: Optional[int] = None
    seconds: Optional[int] = None


class JobCreate(BaseModel):
    """Request model for creating a scheduled job."""
    symbol: str = Field(..., min_length=1, max_length=100)
    asset_type: Literal["stock", "forex", "crypto", "bond", "commodity", "economic_indicator"]
    trigger_type: Literal["cron", "interval"]
    trigger_config: Dict[str, Any] = Field(..., description="Trigger configuration (cron or interval)")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    collector_kwargs: Optional[Dict[str, Any]] = None
    asset_metadata: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = Field(None, max_length=255)

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v, info):
        """Validate that end_date is after start_date."""
        if v and "start_date" in info.data and info.data["start_date"]:
            if v < info.data["start_date"]:
                raise ValueError("end_date must be after start_date")
        return v


class JobUpdate(BaseModel):
    """Request model for updating a scheduled job."""
    symbol: Optional[str] = Field(None, min_length=1, max_length=100)
    asset_type: Optional[Literal["stock", "forex", "crypto", "bond", "commodity", "economic_indicator"]] = None
    trigger_type: Optional[Literal["cron", "interval"]] = None
    trigger_config: Optional[Dict[str, Any]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    collector_kwargs: Optional[Dict[str, Any]] = None
    asset_metadata: Optional[Dict[str, Any]] = None
    status: Optional[Literal["pending", "active", "paused", "completed", "failed"]] = None


class JobResponse(BaseModel):
    """Response model for scheduled job."""
    job_id: str
    symbol: str
    asset_type: str
    trigger_type: str
    trigger_config: Dict[str, Any]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    collector_kwargs: Optional[Dict[str, Any]] = None
    asset_metadata: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobExecutionResponse(BaseModel):
    """Response model for job execution."""
    execution_id: int
    job_id: str
    log_id: Optional[int] = None
    execution_status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CollectionLogResponse(BaseModel):
    """Response model for collection log."""
    log_id: int
    asset_id: int
    collector_type: str
    start_date: datetime
    end_date: datetime
    records_collected: int
    status: str
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CollectRequest(BaseModel):
    """Request model for immediate data collection."""
    symbol: str = Field(..., min_length=1, max_length=100)
    asset_type: Literal["stock", "forex", "crypto", "bond", "commodity", "economic_indicator"]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    incremental: bool = Field(True, description="Whether to use incremental mode (only fetch missing data)")
    collector_kwargs: Optional[Dict[str, Any]] = None
    asset_metadata: Optional[Dict[str, Any]] = None


class CollectResponse(BaseModel):
    """Response model for collection request."""
    job_id: str
    status: str
    message: str
    records_loaded: Optional[int] = None


class ValidateRequest(BaseModel):
    """Request model for validating collection parameters."""
    asset_type: str
    symbol: str
    collector_kwargs: Optional[Dict[str, Any]] = None


class ValidateResponse(BaseModel):
    """Response model for validation."""
    valid: bool
    errors: List[str]

