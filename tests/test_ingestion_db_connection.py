"""
Tests for database connection management in ingestion module.
"""

import pytest
import psycopg2
from investment_platform.ingestion.db_connection import (
    get_db_connection,
    get_db_connection_direct,
    initialize_connection_pool,
    close_connection_pool,
    test_connection,
    get_db_config,
)


def _is_database_available() -> bool:
    """Check if database is available for testing."""
    try:
        config = get_db_config()
        conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["user"],
            password=config["password"],
            connect_timeout=2,
        )
        conn.close()
        return True
    except (psycopg2.OperationalError, psycopg2.Error, Exception):
        return False


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

    @pytest.mark.skipif(
        not _is_database_available(),
        reason="Database not available"
    )
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

    @pytest.mark.skipif(
        not _is_database_available(),
        reason="Database not available"
    )
    def test_get_db_connection_context_manager(self):
        """Test connection context manager."""
        with get_db_connection() as conn:
            assert conn is not None
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1

    @pytest.mark.skipif(
        not _is_database_available(),
        reason="Database not available"
    )
    def test_connection_pool(self):
        """Test connection pool initialization and usage."""
        # Close any existing pool
        try:
            close_connection_pool()
        except:
            pass
        
        # Initialize pool
        initialize_connection_pool(min_conn=1, max_conn=5)
        
        try:
            # Get multiple connections
            connections = []
            for _ in range(3):
                with get_db_connection() as conn:
                    connections.append(conn)
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        result = cursor.fetchone()
                        assert result[0] == 1
        finally:
            # Close pool
            close_connection_pool()

    @pytest.mark.skipif(
        not _is_database_available(),
        reason="Database not available"
    )
    def test_test_connection(self):
        """Test connection test function."""
        result = test_connection()
        assert result is True

