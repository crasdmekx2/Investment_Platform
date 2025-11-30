"""
Tests for database connection management in ingestion module.
"""

import pytest
from investment_platform.ingestion.db_connection import (
    get_db_connection,
    get_db_connection_direct,
    initialize_connection_pool,
    close_connection_pool,
    test_connection,
    get_db_config,
)


class TestDatabaseConnection:
    """Test database connection functionality."""

    def test_get_db_config(self):
        """Test getting database configuration."""
        config = get_db_config()
        
        assert "host" in config
        assert "port" in config
        assert "database" in config
        assert "user" in config
        assert "password" in config
        
        assert isinstance(config["port"], int)

    def test_get_db_connection_direct(self):
        """Test getting a direct database connection."""
        conn = get_db_connection_direct()
        
        assert conn is not None
        
        # Test basic query
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
        
        conn.close()

    def test_get_db_connection_context_manager(self):
        """Test connection context manager."""
        with get_db_connection() as conn:
            assert conn is not None
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1

    def test_connection_pool(self):
        """Test connection pool initialization and usage."""
        # Close any existing pool
        try:
            close_connection_pool()
        except:
            pass
        
        # Initialize pool
        initialize_connection_pool(min_conn=1, max_conn=5)
        
        # Get multiple connections
        connections = []
        for _ in range(3):
            with get_db_connection() as conn:
                connections.append(conn)
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    assert result[0] == 1
        
        # Close pool
        close_connection_pool()

    def test_test_connection(self):
        """Test connection test function."""
        result = test_connection()
        assert result is True

