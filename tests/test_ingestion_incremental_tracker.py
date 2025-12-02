"""
Tests for incremental tracker in ingestion module.
"""

import pytest
from datetime import datetime, timedelta
from investment_platform.ingestion.incremental_tracker import IncrementalTracker
from tests.utils import db_helpers


class TestIncrementalTracker:
    """Test incremental tracking functionality."""

    def test_get_existing_data_range_no_data(self, db_cursor):
        """Test getting data range when no data exists."""
        tracker = IncrementalTracker()

        # Create a test asset
        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            symbol="TRACKER_TEST",
            asset_type="stock",
            name="Tracker Test",
        )

        range_result = tracker.get_existing_data_range(asset_id, "stock")
        assert range_result is None

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_get_existing_data_range_with_data(self, db_cursor):
        """Test getting data range when data exists."""
        tracker = IncrementalTracker()

        # Create asset and insert data
        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            symbol="TRACKER_DATA",
            asset_type="stock",
            name="Tracker Data",
        )

        # Insert sample market data
        start_time = datetime(2024, 1, 1, 12, 0, 0)
        end_time = datetime(2024, 1, 5, 12, 0, 0)

        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
            VALUES (%s, %s, 100.0, 105.0, 99.0, 104.0, 1000000),
                   (%s, %s, 101.0, 106.0, 100.0, 105.0, 1100000)
            """,
            (start_time, asset_id, end_time, asset_id),
        )

        range_result = tracker.get_existing_data_range(asset_id, "stock")

        assert range_result is not None
        assert isinstance(range_result[0], datetime)
        assert isinstance(range_result[1], datetime)

        # Cleanup
        db_cursor.execute("DELETE FROM market_data WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_calculate_missing_ranges_no_existing(self, db_cursor):
        """Test calculating missing ranges when no data exists."""
        tracker = IncrementalTracker()

        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            symbol="MISSING_NONE",
            asset_type="stock",
            name="Missing None",
        )

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 10)

        missing = tracker.calculate_missing_ranges(asset_id, "stock", start_date, end_date)

        assert len(missing) == 1
        assert missing[0][0] == start_date
        assert missing[0][1] == end_date

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_calculate_missing_ranges_with_gaps(self, db_cursor):
        """Test calculating missing ranges with gaps."""
        tracker = IncrementalTracker()

        # Clean up any existing test data first
        db_cursor.execute(
            "DELETE FROM market_data WHERE asset_id IN (SELECT asset_id FROM assets WHERE symbol = 'MISSING_GAPS')"
        )
        db_cursor.execute("DELETE FROM assets WHERE symbol = 'MISSING_GAPS'")

        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            symbol="MISSING_GAPS",
            asset_type="stock",
            name="Missing Gaps",
        )

        # Insert data for Jan 5-7
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
            VALUES 
                ('2024-01-05 12:00:00', %s, 100.0, 105.0, 99.0, 104.0, 1000000),
                ('2024-01-06 12:00:00', %s, 101.0, 106.0, 100.0, 105.0, 1100000),
                ('2024-01-07 12:00:00', %s, 102.0, 107.0, 101.0, 106.0, 1200000)
            """,
            (asset_id, asset_id, asset_id),
        )

        # Request range Jan 1-10 (should have gaps before and after)
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 10)

        missing = tracker.calculate_missing_ranges(asset_id, "stock", start_date, end_date)

        # Should have 2 gaps: Jan 1-4 and Jan 8-10
        assert len(missing) == 2

        # Cleanup
        db_cursor.execute("DELETE FROM market_data WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_has_data_in_range(self, db_cursor):
        """Test checking if data exists in range."""
        tracker = IncrementalTracker()

        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            symbol="HAS_DATA",
            asset_type="stock",
            name="Has Data",
        )

        # Insert data
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
            VALUES ('2024-01-05 12:00:00', %s, 100.0, 105.0, 99.0, 104.0, 1000000)
            """,
            (asset_id,),
        )

        # Check range that includes data
        has_data = tracker.has_data_in_range(
            asset_id,
            "stock",
            datetime(2024, 1, 1),
            datetime(2024, 1, 10),
        )
        assert has_data is True

        # Check range that doesn't include data
        has_data = tracker.has_data_in_range(
            asset_id,
            "stock",
            datetime(2024, 2, 1),
            datetime(2024, 2, 10),
        )
        assert has_data is False

        # Cleanup
        db_cursor.execute("DELETE FROM market_data WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_get_latest_timestamp(self, db_cursor):
        """Test getting latest timestamp."""
        tracker = IncrementalTracker()

        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            symbol="LATEST_TIME",
            asset_type="stock",
            name="Latest Time",
        )

        # No data yet
        latest = tracker.get_latest_timestamp(asset_id, "stock")
        assert latest is None

        # Insert data
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
            VALUES ('2024-01-05 12:00:00', %s, 100.0, 105.0, 99.0, 104.0, 1000000)
            """,
            (asset_id,),
        )

        latest = tracker.get_latest_timestamp(asset_id, "stock")
        assert latest is not None
        assert isinstance(latest, datetime)

        # Cleanup
        db_cursor.execute("DELETE FROM market_data WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_get_data_count(self, db_cursor):
        """Test getting data count."""
        tracker = IncrementalTracker()

        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            symbol="DATA_COUNT",
            asset_type="stock",
            name="Data Count",
        )

        # No data
        count = tracker.get_data_count(asset_id, "stock")
        assert count == 0

        # Insert data
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
            VALUES 
                ('2024-01-05 12:00:00', %s, 100.0, 105.0, 99.0, 104.0, 1000000),
                ('2024-01-06 12:00:00', %s, 101.0, 106.0, 100.0, 105.0, 1100000)
            """,
            (asset_id, asset_id),
        )

        count = tracker.get_data_count(asset_id, "stock")
        assert count == 2

        # Cleanup
        db_cursor.execute("DELETE FROM market_data WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))
