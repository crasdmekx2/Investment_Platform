"""Database connection management for ingestion."""

import os
import logging
from typing import Optional
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool, sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logger = logging.getLogger(__name__)

# Global connection pool
_connection_pool: Optional[pool.ThreadedConnectionPool] = None


def get_db_config() -> dict:
    """
    Get database configuration from environment variables.

    Returns:
        Dictionary with database connection parameters
    """
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME", "investment_platform"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
    }


def initialize_connection_pool(min_conn: int = 1, max_conn: int = 10):
    """
    Initialize the database connection pool.

    Args:
        min_conn: Minimum number of connections in the pool
        max_conn: Maximum number of connections in the pool
    """
    global _connection_pool

    if _connection_pool is not None:
        logger.warning("Connection pool already initialized")
        return

    config = get_db_config()

    try:
        _connection_pool = pool.ThreadedConnectionPool(
            min_conn,
            max_conn,
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["user"],
            password=config["password"],
        )
        logger.info(f"Database connection pool initialized ({min_conn}-{max_conn} connections)")
    except Exception as e:
        logger.error(f"Failed to initialize connection pool: {e}")
        raise


def close_connection_pool():
    """Close the database connection pool."""
    global _connection_pool

    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None
        logger.info("Database connection pool closed")


@contextmanager
def get_db_connection(autocommit: bool = False):
    """
    Get a database connection from the pool.

    Args:
        autocommit: Whether to set autocommit mode

    Yields:
        psycopg2.connection: Database connection

    Raises:
        RuntimeError: If connection pool is not initialized
    """
    global _connection_pool

    if _connection_pool is None:
        # Initialize pool if not already done
        initialize_connection_pool()

    conn = None
    try:
        conn = _connection_pool.getconn()
        if autocommit:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            _connection_pool.putconn(conn)


def get_db_connection_direct(autocommit: bool = False):
    """
    Get a direct database connection (not from pool).
    Useful for one-off operations or when pool is not needed.

    Args:
        autocommit: Whether to set autocommit mode

    Returns:
        psycopg2.connection: Database connection
    """
    config = get_db_config()
    conn = psycopg2.connect(**config)

    if autocommit:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    return conn


def test_connection() -> bool:
    """
    Test database connectivity.

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False
