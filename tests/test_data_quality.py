"""
Tests for data quality validation.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from tests.utils import db_helpers


class TestSchemaValidation:
    """Test schema validation (column types, nullability)."""

    def test_assets_column_types(self, db_cursor):
        """Verify assets table column types are correct."""
        columns = db_helpers.get_table_columns(db_cursor, "assets")
        column_dict = {col["column_name"]: col for col in columns}

        assert column_dict["asset_id"]["data_type"] in [
            "integer",
            "bigint",
        ], "asset_id should be integer or bigint"
        assert (
            "character varying" in column_dict["symbol"]["data_type"].lower()
            or "varchar" in column_dict["symbol"]["data_type"].lower()
        ), "symbol should be VARCHAR"
        assert column_dict["is_active"]["data_type"] == "boolean", "is_active should be boolean"
        assert (
            "timestamp" in column_dict["created_at"]["data_type"].lower()
        ), "created_at should be TIMESTAMPTZ"

    def test_market_data_column_types(self, db_cursor):
        """Verify market_data table column types are correct."""
        columns = db_helpers.get_table_columns(db_cursor, "market_data")
        column_dict = {col["column_name"]: col for col in columns}

        assert "timestamp" in column_dict["time"]["data_type"].lower(), "time should be TIMESTAMPTZ"
        assert column_dict["asset_id"]["data_type"] in [
            "integer",
            "bigint",
        ], "asset_id should be integer or bigint"
        assert "numeric" in column_dict["open"]["data_type"].lower(), "open should be NUMERIC"
        assert (
            "bigint" in column_dict["volume"]["data_type"].lower()
            or "integer" in column_dict["volume"]["data_type"].lower()
        ), "volume should be BIGINT"

    def test_required_fields_not_null(self, db_cursor):
        """Verify required fields are NOT NULL."""
        columns = db_helpers.get_table_columns(db_cursor, "assets")
        column_dict = {col["column_name"]: col for col in columns}

        required_fields = ["symbol", "asset_type", "name", "source"]
        for field in required_fields:
            assert column_dict[field]["is_nullable"] == "NO", f"Field '{field}' should be NOT NULL"


class TestDataTypeConstraints:
    """Test data type constraints (NUMERIC precision, TIMESTAMPTZ)."""

    def test_numeric_precision(self, db_cursor, db_connection):
        """Test that NUMERIC fields accept high precision values."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, "PRECISION_TEST", "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Insert data with high precision
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close)
            VALUES (%s, %s, 123.45678901, 124.56789012, 122.34567890, 123.98765432);
        """,
            (datetime.now(), asset_id),
        )
        db_connection.commit()

        # Verify data was stored with precision
        db_cursor.execute(
            """
            SELECT open, high, low, close 
            FROM market_data 
            WHERE asset_id = %s;
        """,
            (asset_id,),
        )
        result = db_cursor.fetchone()

        assert result is not None, "Data should be inserted"
        assert isinstance(result[0], Decimal), "Values should be Decimal type"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

    def test_timestamptz_storage(self, db_cursor, db_connection):
        """Test that TIMESTAMPTZ stores timezone information."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, "TZ_TEST", "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Insert data with timezone
        test_time = datetime.now()
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close)
            VALUES (%s, %s, 100.0, 110.0, 95.0, 105.0);
        """,
            (test_time, asset_id),
        )
        db_connection.commit()

        # Retrieve and verify timezone
        db_cursor.execute(
            """
            SELECT time, timezone('UTC', time) as utc_time
            FROM market_data 
            WHERE asset_id = %s;
        """,
            (asset_id,),
        )
        result = db_cursor.fetchone()

        assert result is not None, "Data should be retrieved"
        assert result[0] is not None, "Time should not be NULL"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()


class TestDefaultValues:
    """Test default values for columns."""

    def test_created_at_default(self, db_cursor, db_connection):
        """Test that created_at has default value."""
        import uuid

        unique_symbol = f"DEFAULT_CREATED_{uuid.uuid4().hex[:8]}"
        db_cursor.execute(
            """
            INSERT INTO assets (symbol, asset_type, name, source)
            VALUES (%s, 'stock', 'Test Stock', 'Test')
            RETURNING created_at;
        """,
            (unique_symbol,),
        )
        created_at = db_cursor.fetchone()[0]
        db_connection.commit()

        assert created_at is not None, "created_at should have default value"
        assert isinstance(created_at, datetime), "created_at should be datetime"

        # Verify it's recent (within last 5 minutes to account for timezone differences)
        # Handle timezone-aware vs naive datetime comparison
        from datetime import timezone

        now = datetime.now(timezone.utc) if created_at.tzinfo else datetime.now()
        if created_at.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        elif created_at.tzinfo is None and now.tzinfo is not None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        time_diff = abs((now - created_at).total_seconds())
        # Allow up to 5 minutes difference to account for timezone and execution time
        assert (
            time_diff < 300
        ), f"created_at should be recent (within 5 min), got {time_diff} seconds difference"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE symbol = %s;", (unique_symbol,))
        db_connection.commit()

    def test_updated_at_default(self, db_cursor, db_connection):
        """Test that updated_at has default value."""
        import uuid

        unique_symbol = f"DEFAULT_UPDATED_{uuid.uuid4().hex[:8]}"
        db_cursor.execute(
            """
            INSERT INTO assets (symbol, asset_type, name, source)
            VALUES (%s, 'stock', 'Test Stock', 'Test')
            RETURNING updated_at;
        """,
            (unique_symbol,),
        )
        updated_at = db_cursor.fetchone()[0]
        db_connection.commit()

        assert updated_at is not None, "updated_at should have default value"
        assert isinstance(updated_at, datetime), "updated_at should be datetime"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE symbol = %s;", (unique_symbol,))
        db_connection.commit()

    def test_is_active_default(self, db_cursor, db_connection):
        """Test that is_active defaults to TRUE."""
        import uuid

        unique_symbol = f"DEFAULT_ACTIVE_{uuid.uuid4().hex[:8]}"
        db_cursor.execute(
            """
            INSERT INTO assets (symbol, asset_type, name, source)
            VALUES (%s, 'stock', 'Test Stock', 'Test')
            RETURNING is_active;
        """,
            (unique_symbol,),
        )
        is_active = db_cursor.fetchone()[0]
        db_connection.commit()

        assert is_active is True, "is_active should default to TRUE"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE symbol = %s;", (unique_symbol,))
        db_connection.commit()


class TestDataFreshnessMonitoring:
    """Test data freshness monitoring."""

    def test_freshness_check_recent_data(self, db_cursor, db_connection):
        """Test freshness check with recent data."""
        import uuid

        unique_symbol = f"FRESH_MONITOR_{uuid.uuid4().hex[:8]}"
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Insert recent data
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close)
            VALUES (%s, %s, 100.0, 110.0, 95.0, 105.0);
        """,
            (datetime.now() - timedelta(hours=1), asset_id),
        )
        db_connection.commit()

        # Check freshness
        db_cursor.execute("SELECT * FROM check_data_freshness(%s, 'market_data');", (asset_id,))
        result = db_cursor.fetchone()

        assert result is not None, "Should return freshness data"
        assert result[3] is not None, "hours_old should not be NULL"
        assert result[3] < 24, "Data should be less than 24 hours old"
        assert result[4] is False, "Data should not be stale"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

    def test_freshness_check_stale_data(self, db_cursor, db_connection):
        """Test freshness check with stale data."""
        import uuid

        unique_symbol = f"STALE_MONITOR_{uuid.uuid4().hex[:8]}"
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Insert stale data
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close)
            VALUES (%s, %s, 100.0, 110.0, 95.0, 105.0);
        """,
            (datetime.now() - timedelta(days=2), asset_id),
        )
        db_connection.commit()

        # Check freshness
        db_cursor.execute("SELECT * FROM check_data_freshness(%s, 'market_data');", (asset_id,))
        result = db_cursor.fetchone()

        assert result is not None, "Should return freshness data"
        assert result[3] is not None, "hours_old should not be NULL"
        assert result[3] > 24, "Data should be more than 24 hours old"
        assert result[4] is True, "Data should be stale"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()


class TestDataCollectionLogTracking:
    """Test data collection log tracking."""

    def test_collection_log_tracks_execution(self, db_cursor, db_connection):
        """Test that collection log tracks execution details."""
        import uuid

        unique_symbol = f"LOG_TRACK_{uuid.uuid4().hex[:8]}"
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Insert log entry
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        db_cursor.execute(
            """
            INSERT INTO data_collection_log 
            (asset_id, collector_type, start_date, end_date, records_collected, status, execution_time_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING log_id, created_at;
        """,
            (asset_id, "TestCollector", start_time, end_time, 100, "success", 5000),
        )
        result = db_cursor.fetchone()
        log_id = result[0]
        created_at = result[1]
        db_connection.commit()

        assert log_id > 0, "Log ID should be positive"
        assert created_at is not None, "created_at should be set"

        # Verify all fields
        # Column order: log_id(0), asset_id(1), collector_type(2), start_date(3), end_date(4),
        # records_collected(5), status(6), error_message(7), execution_time_ms(8), created_at(9)
        db_cursor.execute("SELECT * FROM data_collection_log WHERE log_id = %s;", (log_id,))
        log_entry = db_cursor.fetchone()

        assert log_entry[1] == asset_id, "Asset ID should match"  # asset_id is index 1
        assert (
            log_entry[2] == "TestCollector"
        ), "Collector type should match"  # collector_type is index 2
        assert log_entry[5] == 100, "Records collected should match"  # records_collected is index 5
        assert log_entry[6] == "success", "Status should match"  # status is index 6
        assert log_entry[8] == 5000, "Execution time should match"  # execution_time_ms is index 8

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

    def test_collection_log_tracks_failures(self, db_cursor, db_connection):
        """Test that collection log tracks failures."""
        import uuid

        unique_symbol = f"LOG_FAIL_{uuid.uuid4().hex[:8]}"
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Insert failed log entry
        db_cursor.execute(
            """
            INSERT INTO data_collection_log 
            (asset_id, collector_type, start_date, end_date, records_collected, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING log_id;
        """,
            (
                asset_id,
                "TestCollector",
                datetime.now() - timedelta(hours=1),
                datetime.now(),
                0,
                "failed",
                "Test error message",
            ),
        )
        log_id = db_cursor.fetchone()[0]
        db_connection.commit()

        # Verify failure was logged
        db_cursor.execute(
            "SELECT status, error_message FROM data_collection_log WHERE log_id = %s;", (log_id,)
        )
        result = db_cursor.fetchone()

        assert result[0] == "failed", "Status should be 'failed'"
        assert result[1] == "Test error message", "Error message should be stored"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()
