#!/usr/bin/env python3
"""
Script to test connectivity to the PostgreSQL database with TimescaleDB.
"""

import psycopg2
import sys
from psycopg2 import sql

# Database connection parameters
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "investment_platform",
    "user": "postgres",
    "password": "postgres",
}


def test_connection():
    """Test basic database connectivity."""
    try:
        print("Attempting to connect to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Successfully connected to database!")

        # Test TimescaleDB extension
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT default_version, installed_version 
            FROM pg_available_extensions 
            WHERE name = 'timescaledb';
        """
        )

        result = cursor.fetchone()
        assert result and result[1], "TimescaleDB extension not found!"
        print(f"✓ TimescaleDB extension is installed (version: {result[1]})")

        # Test database version
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        print(f"✓ Database version: {db_version.split(',')[0]}")

        # Test TimescaleDB extension version
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';")
        ts_version_result = cursor.fetchone()
        if ts_version_result:
            print(f"✓ TimescaleDB extension version: {ts_version_result[0]}")
        else:
            print("⚠ Could not retrieve TimescaleDB extension version")

        cursor.close()
        conn.close()
        print("\n✓ All connectivity tests passed!")

    except psycopg2.OperationalError as e:
        print(f"✗ Connection failed: {e}")
        print("\nMake sure the database container is running:")
        print("  docker-compose up -d")
        raise
    except Exception as e:
        print(f"✗ Error: {e}")
        raise


if __name__ == "__main__":
    try:
        test_connection()
        sys.exit(0)
    except Exception:
        sys.exit(1)
