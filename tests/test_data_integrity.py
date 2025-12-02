"""
Tests for data integrity, constraints, and foreign keys.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from tests.utils import db_helpers


class TestAssetsConstraints:
    """Test constraints on assets table."""

    def test_asset_type_check_constraint(self, db_cursor, db_connection):
        """Test that asset_type must be one of the allowed values."""
        # Try to insert invalid asset_type
        with pytest.raises(Exception) as exc_info:
            db_cursor.execute(
                """
                INSERT INTO assets (symbol, asset_type, name, source)
                VALUES ('TEST', 'invalid_type', 'Test Asset', 'Test');
            """
            )
            db_connection.commit()

        # Should raise a constraint violation
        assert "check" in str(exc_info.value).lower() or "constraint" in str(exc_info.value).lower()

    def test_symbol_unique_constraint(self, db_cursor, db_connection):
        """Test that symbol must be unique."""
        # Insert first asset
        db_cursor.execute(
            """
            INSERT INTO assets (symbol, asset_type, name, source)
            VALUES ('UNIQUE_TEST', 'stock', 'Test Asset 1', 'Test')
            ON CONFLICT DO NOTHING;
        """
        )
        db_connection.commit()

        # Try to insert duplicate symbol
        with pytest.raises(Exception) as exc_info:
            db_cursor.execute(
                """
                INSERT INTO assets (symbol, asset_type, name, source)
                VALUES ('UNIQUE_TEST', 'stock', 'Test Asset 2', 'Test');
            """
            )
            db_connection.commit()

        # Should raise a unique constraint violation
        assert "unique" in str(exc_info.value).lower() or "duplicate" in str(exc_info.value).lower()

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE symbol = 'UNIQUE_TEST';")
        db_connection.commit()

    def test_required_fields_not_null(self, db_cursor, db_connection):
        """Test that required fields cannot be NULL."""
        # Try to insert without symbol
        with pytest.raises(Exception) as exc_info:
            db_cursor.execute(
                """
                INSERT INTO assets (asset_type, name, source)
                VALUES ('stock', 'Test Asset', 'Test');
            """
            )
            db_connection.commit()

        assert "not null" in str(exc_info.value).lower() or "null" in str(exc_info.value).lower()

    def test_jsonb_metadata_field(self, db_cursor, db_connection):
        """Test that JSONB metadata field works correctly."""
        import json

        metadata = {"test_key": "test_value", "number": 123}
        db_cursor.execute(
            """
            INSERT INTO assets (symbol, asset_type, name, source, metadata)
            VALUES ('JSONB_TEST', 'stock', 'Test Asset', 'Test', %s)
            RETURNING asset_id, metadata;
        """,
            (json.dumps(metadata),),
        )

        result = db_cursor.fetchone()
        assert result is not None
        assert result[1] == metadata

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE symbol = 'JSONB_TEST';")
        db_connection.commit()

    def test_is_active_default_value(self, db_cursor, db_connection):
        """Test that is_active defaults to TRUE."""
        db_cursor.execute(
            """
            INSERT INTO assets (symbol, asset_type, name, source)
            VALUES ('DEFAULT_TEST', 'stock', 'Test Asset', 'Test')
            RETURNING is_active;
        """
        )
        result = db_cursor.fetchone()
        assert result[0] is True, "is_active should default to TRUE"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE symbol = 'DEFAULT_TEST';")
        db_connection.commit()


class TestMarketDataConstraints:
    """Test constraints on market_data table."""

    def test_ohlc_validation_constraint(self, db_cursor, db_connection):
        """Test OHLC validation constraint (high >= low, etc.)."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, "OHLC_TEST", "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Try to insert invalid OHLC data (high < low)
        with pytest.raises(Exception) as exc_info:
            db_cursor.execute(
                """
                INSERT INTO market_data (time, asset_id, open, high, low, close)
                VALUES (%s, %s, 100.0, 90.0, 110.0, 105.0);
            """,
                (datetime.now(), asset_id),
            )
            db_connection.commit()

        assert "check" in str(exc_info.value).lower() or "constraint" in str(exc_info.value).lower()

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

    def test_valid_ohlc_data(self, db_cursor, db_connection):
        """Test that valid OHLC data can be inserted."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, "OHLC_VALID", "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Insert valid OHLC data
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
            VALUES (%s, %s, 100.0, 110.0, 95.0, 105.0, 1000);
        """,
            (datetime.now(), asset_id),
        )
        db_connection.commit()

        # Verify data was inserted
        db_cursor.execute(
            """
            SELECT COUNT(*) FROM market_data WHERE asset_id = %s;
        """,
            (asset_id,),
        )
        count = db_cursor.fetchone()[0]
        assert count == 1, "Valid OHLC data should be inserted"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

    def test_volume_non_negative(self, db_cursor, db_connection):
        """Test that volume must be non-negative."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, "VOL_TEST", "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Try to insert negative volume
        with pytest.raises(Exception) as exc_info:
            db_cursor.execute(
                """
                INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
                VALUES (%s, %s, 100.0, 110.0, 95.0, 105.0, -100);
            """,
                (datetime.now(), asset_id),
            )
            db_connection.commit()

        assert "check" in str(exc_info.value).lower() or "constraint" in str(exc_info.value).lower()

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()


class TestForexRatesConstraints:
    """Test constraints on forex_rates table."""

    def test_rate_must_be_positive(self, db_cursor, db_connection):
        """Test that rate must be greater than 0."""
        import uuid

        unique_symbol = f"EURUSD_TEST_{uuid.uuid4().hex[:8]}"
        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            unique_symbol,
            "forex",
            "EUR/USD",
            "Test",
            base_currency="EUR",
            quote_currency="USD",
        )
        db_connection.commit()

        # Try to insert zero or negative rate
        with pytest.raises(Exception) as exc_info:
            db_cursor.execute(
                """
                INSERT INTO forex_rates (time, asset_id, rate)
                VALUES (%s, %s, 0);
            """,
                (datetime.now(), asset_id),
            )
            db_connection.commit()

        assert "check" in str(exc_info.value).lower() or "constraint" in str(exc_info.value).lower()

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()


class TestDataCollectionLogConstraints:
    """Test constraints on data_collection_log table."""

    def test_status_check_constraint(self, db_cursor, db_connection):
        """Test that status must be one of the allowed values."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, "LOG_TEST", "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Try to insert invalid status
        with pytest.raises(Exception) as exc_info:
            db_cursor.execute(
                """
                INSERT INTO data_collection_log 
                (asset_id, collector_type, start_date, end_date, records_collected, status)
                VALUES (%s, 'TestCollector', %s, %s, 10, 'invalid_status');
            """,
                (asset_id, datetime.now(), datetime.now()),
            )
            db_connection.commit()

        assert "check" in str(exc_info.value).lower() or "constraint" in str(exc_info.value).lower()

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

    def test_date_range_validation(self, db_cursor, db_connection):
        """Test that end_date must be >= start_date."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, "DATE_TEST", "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Try to insert invalid date range
        with pytest.raises(Exception) as exc_info:
            db_cursor.execute(
                """
                INSERT INTO data_collection_log 
                (asset_id, collector_type, start_date, end_date, records_collected, status)
                VALUES (%s, 'TestCollector', %s, %s, 10, 'success');
            """,
                (asset_id, datetime.now(), datetime.now() - timedelta(days=1)),
            )
            db_connection.commit()

        assert "check" in str(exc_info.value).lower() or "constraint" in str(exc_info.value).lower()

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()


class TestForeignKeys:
    """Test foreign key constraints and CASCADE behavior."""

    def test_foreign_key_cascade_delete(self, db_cursor, db_connection):
        """Test that deleting an asset cascades to related time-series data."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, "CASCADE_TEST", "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Insert market data
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
            VALUES (%s, %s, 100.0, 110.0, 95.0, 105.0, 1000);
        """,
            (datetime.now(), asset_id),
        )
        db_connection.commit()

        # Verify data exists
        db_cursor.execute("SELECT COUNT(*) FROM market_data WHERE asset_id = %s;", (asset_id,))
        count_before = db_cursor.fetchone()[0]
        assert count_before == 1, "Market data should exist before deletion"

        # Delete asset
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

        # Verify market data was cascaded
        db_cursor.execute("SELECT COUNT(*) FROM market_data WHERE asset_id = %s;", (asset_id,))
        count_after = db_cursor.fetchone()[0]
        assert count_after == 0, "Market data should be deleted when asset is deleted"

    def test_foreign_key_prevents_invalid_asset_id(self, db_cursor, db_connection):
        """Test that foreign key prevents inserting data with invalid asset_id."""
        # Try to insert market data with non-existent asset_id
        with pytest.raises(Exception) as exc_info:
            db_cursor.execute(
                """
                INSERT INTO market_data (time, asset_id, open, high, low, close)
                VALUES (%s, 999999, 100.0, 110.0, 95.0, 105.0);
            """,
                (datetime.now(),),
            )
            db_connection.commit()

        assert (
            "foreign key" in str(exc_info.value).lower()
            or "violates" in str(exc_info.value).lower()
        )


class TestSoftDelete:
    """Test soft delete functionality."""

    def test_is_active_flag(self, db_cursor, db_connection):
        """Test that is_active flag works for soft deletes."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, "SOFT_DELETE_TEST", "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Verify asset is active
        db_cursor.execute("SELECT is_active FROM assets WHERE asset_id = %s;", (asset_id,))
        assert db_cursor.fetchone()[0] is True, "Asset should be active by default"

        # Soft delete
        db_cursor.execute("UPDATE assets SET is_active = FALSE WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

        # Verify asset is inactive
        db_cursor.execute("SELECT is_active FROM assets WHERE asset_id = %s;", (asset_id,))
        assert db_cursor.fetchone()[0] is False, "Asset should be inactive after soft delete"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()
