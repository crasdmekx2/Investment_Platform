"""
Tests for error classification edge cases.

Tests unknown error types, multiple error indicators, and edge case error messages.
"""

import pytest
from investment_platform.ingestion.error_classifier import classify_error


class TestErrorClassificationEdgeCases:
    """Test suite for error classification edge cases."""

    def test_unknown_error_type(self):
        """Test classification of unknown error types."""
        # Custom exception with no known indicators
        class CustomError(Exception):
            pass

        error = CustomError("Something unexpected happened")
        category, suggestion = classify_error(error)

        # Unknown errors should be treated as transient (safer to retry)
        assert category == "transient", "Unknown errors should default to transient"
        assert "retry" in suggestion.lower() or "unexpected" in suggestion.lower()

    def test_multiple_error_indicators(self):
        """Test error classification when multiple indicators are present."""
        # Error with both transient and permanent indicators
        # Transient should take precedence (checked first)
        error_msg = "Rate limit exceeded: 429 - Invalid symbol format"
        category, suggestion = classify_error(Exception(error_msg))

        assert category == "transient", "Transient errors should take precedence"
        assert "rate limit" in suggestion.lower()

        # Error with both permanent and system indicators
        # Permanent should take precedence (checked before system)
        error_msg2 = "Invalid request: 400 - Database connection failed"
        category2, suggestion2 = classify_error(Exception(error_msg2))

        assert category2 == "permanent", "Permanent errors should take precedence over system"
        assert "invalid" in suggestion2.lower() or "parameters" in suggestion2.lower()

    def test_edge_case_error_messages(self):
        """Test edge case error messages."""
        # Empty error message
        category, suggestion = classify_error(Exception(""))
        assert category in ["transient", "permanent", "system"], "Should handle empty message"

        # Very long error message
        long_msg = "Error: " + "x" * 1000
        category, suggestion = classify_error(Exception(long_msg))
        assert category in ["transient", "permanent", "system"], "Should handle long messages"

        # Error message with special characters
        special_msg = "Error: rate limit! @#$%^&*()"
        category, suggestion = classify_error(Exception(special_msg))
        assert category == "transient", "Should handle special characters"

        # Error message with unicode
        unicode_msg = "Rate limit: 429 - 错误"
        category, suggestion = classify_error(Exception(unicode_msg))
        assert category == "transient", "Should handle unicode characters"

    def test_case_insensitive_classification(self):
        """Test that error classification is case-insensitive."""
        # Uppercase
        error1 = Exception("RATE LIMIT EXCEEDED")
        category1, _ = classify_error(error1)
        assert category1 == "transient"

        # Mixed case
        error2 = Exception("RaTe LiMiT ExCeEdEd")
        category2, _ = classify_error(error2)
        assert category2 == "transient"

        # Lowercase
        error3 = Exception("rate limit exceeded")
        category3, _ = classify_error(error3)
        assert category3 == "transient"

    def test_partial_match_indicators(self):
        """Test that partial matches work correctly."""
        # "timeout" should match "timed out"
        error1 = Exception("Request timed out")
        category1, suggestion1 = classify_error(error1)
        assert category1 == "transient"
        assert "timeout" in suggestion1.lower() or "time" in suggestion1.lower()

        # "connection" should match "econnrefused"
        error2 = Exception("Connection refused: econnrefused")
        category2, suggestion2 = classify_error(error2)
        assert category2 == "transient"
        assert "connection" in suggestion2.lower() or "network" in suggestion2.lower()

    def test_numeric_error_codes(self):
        """Test classification by HTTP status codes."""
        # Test various HTTP status codes
        status_codes = {
            "429": "transient",
            "503": "transient",
            "502": "transient",
            "504": "transient",
            "408": "transient",
            "400": "permanent",
            "404": "permanent",
            "401": "permanent",
            "403": "permanent",
            "409": "permanent",
            "500": "system",
        }

        for code, expected_category in status_codes.items():
            error = Exception(f"HTTP {code} error")
            category, _ = classify_error(error)
            assert (
                category == expected_category
            ), f"Status code {code} should be classified as {expected_category}"

    def test_error_type_name_classification(self):
        """Test classification based on exception type name."""
        # Test that exception type doesn't override message content
        class RateLimitError(Exception):
            pass

        # Even if exception type suggests rate limit, message content takes precedence
        error1 = RateLimitError("Invalid symbol")
        category1, _ = classify_error(error1)
        # Should classify based on message, not type name
        assert category1 == "permanent", "Message content should take precedence"

    def test_none_error_message(self):
        """Test handling when error_message parameter is None."""
        error = Exception("Some error")
        category, suggestion = classify_error(error, error_message=None)
        assert category in ["transient", "permanent", "system"], "Should handle None message"

    def test_custom_error_message_parameter(self):
        """Test that custom error_message parameter is used."""
        error = Exception("Original message")
        category, suggestion = classify_error(
            error, error_message="Rate limit exceeded: 429"
        )
        assert category == "transient", "Should use custom error_message parameter"

    def test_system_error_precedence(self):
        """Test system error classification."""
        # Database errors
        db_error = Exception("Database connection failed")
        category, suggestion = classify_error(db_error)
        assert category == "system"
        assert "database" in suggestion.lower() or "administrator" in suggestion.lower()

        # Memory errors
        mem_error = Exception("Out of memory")
        category, suggestion = classify_error(mem_error)
        assert category == "system"
        assert "memory" in suggestion.lower()

        # Disk errors
        disk_error = Exception("Disk full")
        category, suggestion = classify_error(disk_error)
        assert category == "system"
        assert "disk" in suggestion.lower()

    def test_transient_error_variations(self):
        """Test various transient error message variations."""
        transient_variations = [
            "Rate limit exceeded",
            "Too many requests",
            "Request timeout",
            "Connection timeout",
            "Network error",
            "Service unavailable",
            "Bad gateway",
            "Gateway timeout",
            "SSL certificate error",
            "Socket error",
        ]

        for msg in transient_variations:
            error = Exception(msg)
            category, _ = classify_error(error)
            assert category == "transient", f"'{msg}' should be classified as transient"

    def test_permanent_error_variations(self):
        """Test various permanent error message variations."""
        permanent_variations = [
            "Validation error",
            "Invalid request",
            "Not found",
            "Unauthorized",
            "Forbidden",
            "Conflict",
            "Invalid symbol",
            "Unsupported format",
            "Malformed request",
        ]

        for msg in permanent_variations:
            error = Exception(msg)
            category, _ = classify_error(error)
            assert category == "permanent", f"'{msg}' should be classified as permanent"

