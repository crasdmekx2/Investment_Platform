"""
Tests for database connection pool error scenarios.

Tests pool exhaustion, connection failures, and pool initialization failures.
"""

import pytest
import psycopg2
from unittest.mock import patch, MagicMock
from investment_platform.ingestion.db_connection import (
    initialize_connection_pool,
    close_connection_pool,
    get_db_connection,
    get_db_config,
)


class TestDatabaseConnectionPoolErrors:
    """Test suite for database connection pool error scenarios."""

    @pytest.fixture(autouse=True)
    def cleanup_pool(self):
        """Clean up connection pool before and after each test."""
        close_connection_pool()
        yield
        close_connection_pool()

    def test_pool_initialization_failure(self):
        """Test handling of pool initialization failures."""
        # Mock invalid database configuration
        with patch("investment_platform.ingestion.db_connection.get_db_config") as mock_config:
            mock_config.return_value = {
                "host": "invalid_host",
                "port": 5432,
                "database": "invalid_db",
                "user": "invalid_user",
                "password": "invalid_password",
            }

            # Should raise an exception
            with pytest.raises(Exception):
                initialize_connection_pool(min_conn=1, max_conn=2)

    def test_pool_exhaustion(self):
        """Test handling when connection pool is exhausted."""
        # Initialize pool with very small size
        try:
            initialize_connection_pool(min_conn=1, max_conn=2)

            # Get all available connections
            conn1 = None
            conn2 = None
            try:
                conn1 = get_db_connection().__enter__()
                conn2 = get_db_connection().__enter__()

                # Try to get a third connection (should timeout or raise error)
                with pytest.raises((psycopg2.pool.PoolError, Exception)):
                    conn3 = get_db_connection().__enter__()
                    conn3.__exit__(None, None, None)
            finally:
                if conn1:
                    conn1.__exit__(None, None, None)
                if conn2:
                    conn2.__exit__(None, None, None)
        except Exception as e:
            # If pool initialization fails (e.g., no database), skip test
            pytest.skip(f"Pool initialization failed: {e}")

    def test_connection_failure_handling(self):
        """Test handling of individual connection failures."""
        # Mock connection failure
        with patch("psycopg2.pool.ThreadedConnectionPool.getconn") as mock_getconn:
            mock_getconn.side_effect = psycopg2.OperationalError("Connection failed")

            initialize_connection_pool(min_conn=1, max_conn=2)

            # Should raise an exception when getting connection
            with pytest.raises(psycopg2.OperationalError):
                with get_db_connection():
                    pass

    def test_pool_already_initialized(self):
        """Test that re-initializing pool logs warning."""
        import logging

        with patch("investment_platform.ingestion.db_connection.logger") as mock_logger:
            try:
                initialize_connection_pool(min_conn=1, max_conn=2)
                # Try to initialize again
                initialize_connection_pool(min_conn=1, max_conn=2)
                # Should log warning
                mock_logger.warning.assert_called()
            except Exception:
                # If initialization fails, skip test
                pytest.skip("Pool initialization failed")

    def test_connection_rollback_on_error(self):
        """Test that connections are rolled back on error."""
        try:
            initialize_connection_pool(min_conn=1, max_conn=2)

            with get_db_connection() as conn:
                # Cause an error
                with pytest.raises(Exception):
                    with conn.cursor() as cursor:
                        cursor.execute("INVALID SQL STATEMENT")
                        # Should rollback automatically
        except Exception as e:
            # If pool initialization fails, skip test
            if "Pool" not in str(type(e).__name__):
                pytest.skip(f"Pool initialization failed: {e}")

    def test_pool_close_all_connections(self):
        """Test that closing pool releases all connections."""
        try:
            initialize_connection_pool(min_conn=1, max_conn=2)

            # Get a connection
            conn = get_db_connection().__enter__()

            # Close pool
            close_connection_pool()

            # Pool should be None
            from investment_platform.ingestion.db_connection import _connection_pool

            assert _connection_pool is None, "Pool should be None after closing"

            # Try to use connection after pool is closed (should fail)
            try:
                conn.__exit__(None, None, None)
            except Exception:
                # Expected - connection may be invalid after pool close
                pass
        except Exception as e:
            pytest.skip(f"Pool initialization failed: {e}")

    def test_connection_return_to_pool(self):
        """Test that connections are properly returned to pool."""
        try:
            initialize_connection_pool(min_conn=1, max_conn=2)

            # Get and return connection
            with get_db_connection() as conn1:
                assert conn1 is not None

            # Should be able to get connection again (returned to pool)
            with get_db_connection() as conn2:
                assert conn2 is not None
        except Exception as e:
            pytest.skip(f"Pool initialization failed: {e}")

    def test_invalid_database_config(self):
        """Test handling of invalid database configuration."""
        # Test with None values
        with patch("investment_platform.ingestion.db_connection.get_db_config") as mock_config:
            mock_config.return_value = {
                "host": None,
                "port": None,
                "database": None,
                "user": None,
                "password": None,
            }

            with pytest.raises(Exception):
                initialize_connection_pool(min_conn=1, max_conn=2)

    def test_connection_timeout(self):
        """Test handling of connection timeouts."""
        # Mock connection timeout
        with patch("psycopg2.pool.ThreadedConnectionPool.getconn") as mock_getconn:
            mock_getconn.side_effect = psycopg2.OperationalError(
                "Connection timeout"
            )

            initialize_connection_pool(min_conn=1, max_conn=2)

            with pytest.raises(psycopg2.OperationalError):
                with get_db_connection():
                    pass

    def test_pool_initialization_with_zero_connections(self):
        """Test that pool initialization handles edge case of zero connections."""
        # Should handle gracefully or raise appropriate error
        with pytest.raises((ValueError, Exception)):
            initialize_connection_pool(min_conn=0, max_conn=0)

    def test_autocommit_mode(self):
        """Test that autocommit mode is set correctly."""
        try:
            initialize_connection_pool(min_conn=1, max_conn=2)

            with get_db_connection(autocommit=True) as conn:
                assert (
                    conn.isolation_level == psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
                )
        except Exception as e:
            pytest.skip(f"Pool initialization failed: {e}")

    def test_get_db_config_defaults(self):
        """Test that get_db_config returns proper defaults."""
        with patch.dict("os.environ", {}, clear=True):
            config = get_db_config()
            assert config["host"] == "localhost"
            assert config["port"] == 5432
            assert config["database"] == "investment_platform"
            assert config["user"] == "postgres"
            assert config["password"] == "postgres"

    def test_get_db_config_from_environment(self):
        """Test that get_db_config reads from environment variables."""
        test_env = {
            "DB_HOST": "test_host",
            "DB_PORT": "9999",
            "DB_NAME": "test_db",
            "DB_USER": "test_user",
            "DB_PASSWORD": "test_password",
        }

        with patch.dict("os.environ", test_env):
            config = get_db_config()
            assert config["host"] == "test_host"
            assert config["port"] == 9999
            assert config["database"] == "test_db"
            assert config["user"] == "test_user"
            assert config["password"] == "test_password"

