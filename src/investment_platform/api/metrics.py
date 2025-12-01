"""Prometheus metrics for scheduler and API."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Optional

# Job metrics
scheduler_jobs_total = Counter(
    'scheduler_jobs_total',
    'Total number of scheduler jobs',
    ['status', 'asset_type']
)

scheduler_job_executions_total = Counter(
    'scheduler_job_executions_total',
    'Total number of job executions',
    ['status', 'asset_type', 'error_category']
)

scheduler_job_duration_seconds = Histogram(
    'scheduler_job_duration_seconds',
    'Job execution duration in seconds',
    ['asset_type', 'status'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

scheduler_job_retries_total = Counter(
    'scheduler_job_retries_total',
    'Total number of job retries',
    ['job_id', 'asset_type']
)

scheduler_active_jobs = Gauge(
    'scheduler_active_jobs',
    'Number of active scheduler jobs',
    ['asset_type']
)

scheduler_pending_jobs = Gauge(
    'scheduler_pending_jobs',
    'Number of pending scheduler jobs',
    ['asset_type']
)

scheduler_failed_jobs = Gauge(
    'scheduler_failed_jobs',
    'Number of failed scheduler jobs',
    ['asset_type']
)


def record_job_created(asset_type: str, status: str = "pending"):
    """Record a job creation."""
    scheduler_jobs_total.labels(status=status, asset_type=asset_type).inc()


def record_job_execution(
    asset_type: str,
    status: str,
    duration_seconds: float,
    error_category: Optional[str] = None,
):
    """Record a job execution."""
    scheduler_job_executions_total.labels(
        status=status,
        asset_type=asset_type,
        error_category=error_category or "none"
    ).inc()
    
    scheduler_job_duration_seconds.labels(
        asset_type=asset_type,
        status=status
    ).observe(duration_seconds)


def record_job_retry(job_id: str, asset_type: str):
    """Record a job retry."""
    scheduler_job_retries_total.labels(job_id=job_id, asset_type=asset_type).inc()


def update_job_gauges(asset_type: str, active: int, pending: int, failed: int):
    """Update job status gauges."""
    scheduler_active_jobs.labels(asset_type=asset_type).set(active)
    scheduler_pending_jobs.labels(asset_type=asset_type).set(pending)
    scheduler_failed_jobs.labels(asset_type=asset_type).set(failed)


def get_metrics():
    """Get Prometheus metrics in text format."""
    return generate_latest()


def get_metrics_content_type():
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST

