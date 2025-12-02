"""Error classification utilities for scheduler retry logic."""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def classify_error(error: Exception, error_message: Optional[str] = None) -> Tuple[str, str]:
    """
    Classify an error into a category and provide recovery suggestions.

    Args:
        error: The exception that occurred
        error_message: Optional error message string

    Returns:
        Tuple of (error_category, recovery_suggestion)
        error_category: 'transient', 'permanent', or 'system'
        recovery_suggestion: Human-readable suggestion for recovery
    """
    error_str = error_message or str(error).lower()
    error_type = type(error).__name__

    # Transient errors (retryable)
    transient_indicators = [
        "rate limit",
        "429",
        "too many requests",
        "timeout",
        "timed out",
        "408",
        "connection",
        "network",
        "econnrefused",
        "econnreset",
        "temporary",
        "retry",
        "503",
        "service unavailable",
        "502",
        "bad gateway",
        "504",
        "gateway timeout",
        "socket",
        "ssl",
        "certificate",
    ]

    # Permanent errors (not retryable - validation/config issues)
    permanent_indicators = [
        "validation",
        "invalid",
        "400",
        "bad request",
        "not found",
        "404",
        "unauthorized",
        "401",
        "forbidden",
        "403",
        "conflict",
        "409",
        "symbol",
        "asset",
        "format",
        "malformed",
        "unsupported",
        "not supported",
    ]

    # System errors (infrastructure issues)
    system_indicators = [
        "database",
        "postgres",
        "sql",
        "connection pool",
        "memory",
        "disk",
        "ioerror",
        "oserror",
        "internal server error",
        "500",
    ]

    # Check for transient errors
    if any(indicator in error_str for indicator in transient_indicators):
        suggestion = _get_transient_recovery_suggestion(error_str)
        return ("transient", suggestion)

    # Check for permanent errors
    if any(indicator in error_str for indicator in permanent_indicators):
        suggestion = _get_permanent_recovery_suggestion(error_str)
        return ("permanent", suggestion)

    # Check for system errors
    if any(indicator in error_str for indicator in system_indicators):
        suggestion = _get_system_recovery_suggestion(error_str)
        return ("system", suggestion)

    # Default: treat unknown errors as transient (safer to retry)
    logger.warning(f"Unknown error type, treating as transient: {error_type} - {error_str}")
    return ("transient", "An unexpected error occurred. The system will retry automatically.")


def _get_transient_recovery_suggestion(error_str: str) -> str:
    """Get recovery suggestion for transient errors."""
    if "rate limit" in error_str or "429" in error_str:
        return "Rate limit exceeded. The system will retry with exponential backoff."
    elif "timeout" in error_str or "408" in error_str or "504" in error_str:
        return "Request timed out. The system will retry automatically."
    elif "connection" in error_str or "network" in error_str:
        return "Network connection issue. The system will retry automatically."
    elif "503" in error_str or "service unavailable" in error_str:
        return "Service temporarily unavailable. The system will retry automatically."
    else:
        return "Temporary error occurred. The system will retry automatically."


def _get_permanent_recovery_suggestion(error_str: str) -> str:
    """Get recovery suggestion for permanent errors."""
    if "validation" in error_str or "invalid" in error_str or "400" in error_str:
        return "Invalid request parameters. Please check your job configuration."
    elif "not found" in error_str or "404" in error_str:
        return "Resource not found. Please verify the asset symbol or identifier."
    elif "unauthorized" in error_str or "401" in error_str:
        return "Authentication failed. Please check your API credentials."
    elif "forbidden" in error_str or "403" in error_str:
        return "Access denied. Please check your permissions."
    elif "symbol" in error_str or "asset" in error_str:
        return "Invalid asset symbol or identifier. Please verify and try again."
    else:
        return "Configuration error. Please review your job settings."


def _get_system_recovery_suggestion(error_str: str) -> str:
    """Get recovery suggestion for system errors."""
    if "database" in error_str or "postgres" in error_str or "sql" in error_str:
        return "Database error. Please contact system administrator."
    elif "memory" in error_str:
        return "Insufficient memory. Please contact system administrator."
    elif "disk" in error_str:
        return "Disk space issue. Please contact system administrator."
    else:
        return "System error. Please contact system administrator if the issue persists."
