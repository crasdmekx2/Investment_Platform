"""
Pytest configuration and fixtures for database tests.
"""

import os
import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import Generator


# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'investment_platform'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}


@pytest.fixture(scope='session')
def db_connection():
    """
    Create a database connection for the test session.
    
    Yields:
        psycopg2.connection: Database connection object
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        yield conn
        conn.close()
    except psycopg2.OperationalError as e:
        pytest.skip(f"Database not available: {e}")


@pytest.fixture(scope='function')
def db_cursor(db_connection):
    """
    Create a database cursor for individual tests.
    
    Args:
        db_connection: Database connection fixture
        
    Yields:
        psycopg2.extensions.cursor: Database cursor object
    """
    cursor = db_connection.cursor()
    yield cursor
    cursor.close()


@pytest.fixture(scope='function')
def db_transaction(db_connection):
    """
    Create a transaction that will be rolled back after the test.
    This ensures test isolation.
    
    Args:
        db_connection: Database connection fixture
        
    Yields:
        psycopg2.connection: Database connection in transaction mode
    """
    # Set isolation level to allow explicit transaction control
    # Use READ_COMMITTED instead of AUTOCOMMIT to enable BEGIN/ROLLBACK
    from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED
    original_isolation = db_connection.isolation_level
    db_connection.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
    
    # Start a transaction
    cursor = db_connection.cursor()
    cursor.execute("BEGIN;")
    cursor.close()
    
    yield db_connection
    
    # Rollback transaction
    cursor = db_connection.cursor()
    cursor.execute("ROLLBACK;")
    cursor.close()
    
    # Reset to original isolation level
    db_connection.set_isolation_level(original_isolation)

