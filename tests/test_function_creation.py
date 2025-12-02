#!/usr/bin/env python3
"""Test function creation."""

import pytest
import psycopg2
from investment_platform.ingestion.db_connection import get_db_connection


@pytest.fixture
def db_connection():
    """Get database connection for testing."""
    try:
        with get_db_connection() as conn:
            yield conn
    except psycopg2.OperationalError:
        pytest.skip("Database not available")


def test_function_creation(db_connection):
    """Test creating a database function."""
    cur = db_connection.cursor()

    # Test creating a simple function
    sql = """
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """

    try:
        cur.execute(sql)
        db_connection.commit()

        # Check if it exists
        cur.execute("SELECT proname FROM pg_proc WHERE proname = 'update_updated_at_column';")
        result = cur.fetchone()
        assert result is not None, "Function not found in pg_proc"
        assert result[0] == "update_updated_at_column"
    except Exception as e:
        db_connection.rollback()
        pytest.fail(f"Failed to create function: {e}")
