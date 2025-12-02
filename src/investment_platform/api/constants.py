"""API constants for the Investment Platform.

This module contains all magic numbers and configuration constants used across
the API layer. Extracting these values makes the code more maintainable and
allows for easier configuration changes.
"""

# ============================================================================
# PAGINATION CONSTANTS
# ============================================================================

# Default pagination values
DEFAULT_PAGE_LIMIT: int = 100
"""Default number of items per page for list endpoints."""

DEFAULT_PAGE_OFFSET: int = 0
"""Default offset for pagination (start from beginning)."""

MAX_PAGE_LIMIT: int = 1000
"""Maximum allowed items per page to prevent excessive resource usage."""

MIN_PAGE_LIMIT: int = 1
"""Minimum allowed items per page."""

# Job execution pagination (typically smaller than regular pagination)
DEFAULT_EXECUTION_LIMIT: int = 50
"""Default number of job executions to return per page."""

# Collector search pagination
DEFAULT_SEARCH_LIMIT: int = 50
"""Default number of search results to return."""

MAX_SEARCH_LIMIT: int = 100
"""Maximum number of search results allowed."""

# ============================================================================
# CONNECTION POOL CONSTANTS
# ============================================================================

# Database connection pool settings
DEFAULT_DB_MIN_CONNECTIONS: int = 1
"""Default minimum number of database connections in pool."""

DEFAULT_DB_MAX_CONNECTIONS: int = 10
"""Default maximum number of database connections in pool."""

# API server connection pool (typically larger than default)
API_DB_MIN_CONNECTIONS: int = 2
"""Minimum database connections for API server."""

API_DB_MAX_CONNECTIONS: int = 20
"""Maximum database connections for API server."""

# ============================================================================
# THREAD POOL CONSTANTS
# ============================================================================

DEFAULT_THREAD_POOL_WORKERS: int = 5
"""Default number of worker threads for background tasks."""

# ============================================================================
# RETRY CONSTANTS
# ============================================================================

DEFAULT_MAX_RETRIES: int = 3
"""Default maximum number of retry attempts for failed operations."""

# ============================================================================
# RATE LIMITING CONSTANTS
# ============================================================================

DEFAULT_RATE_LIMIT_CALLS: int = 10
"""Default number of API calls allowed per rate limit period."""

DEFAULT_RATE_LIMIT_PERIOD: int = 60
"""Default rate limit period in seconds."""

# ============================================================================
# TIMEOUT CONSTANTS
# ============================================================================

DEFAULT_TIMEOUT_SECONDS: int = 30
"""Default timeout in seconds for API requests."""

# ============================================================================
# SCHEDULER CONSTANTS
# ============================================================================

DEFAULT_SCHEDULER_MAX_WORKERS: int = 10
"""Default maximum number of worker threads for scheduler."""

# ============================================================================
# SEARCH CONSTANTS
# ============================================================================

DEFAULT_SEARCH_MIN_LENGTH: int = 1
"""Minimum length for search queries."""

DEFAULT_ECONOMIC_SEARCH_LIMIT: int = 10
"""Default limit for economic indicator search results."""
