"""
Tests to verify incremental tracker uses precise gap boundaries.
"""

import pytest
from datetime import datetime, timedelta
from investment_platform.ingestion.incremental_tracker import IncrementalTracker
from tests.utils import db_helpers


class TestIncrementalTrackerGapBoundaries:
    """Test that gap boundaries use precise offsets, not full days."""

    def test_gap_boundary_uses_microseconds_not_days(self, db_cursor):
        """Test that gap boundaries use microseconds, not days, to avoid missing data."""
        tracker = IncrementalTracker()

        # Clean up any existing test data
        db_cursor.execute(
            "DELETE FROM market_data WHERE asset_id IN (SELECT asset_id FROM assets WHERE symbol = 'GAP_BOUNDARY_TEST')"
        )
        db_cursor.execute("DELETE FROM assets WHERE symbol = 'GAP_BOUNDARY_TEST'")

        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            symbol="GAP_BOUNDARY_TEST",
            asset_type="stock",
            name="Gap Boundary Test",
        )

        # Insert data at a specific time (not midnight)
        existing_time = datetime(2024, 1, 5, 10, 30, 0)  # 10:30 AM
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
            VALUES (%s, %s, 100.0, 105.0, 99.0, 104.0, 1000000)
            """,
            (existing_time, asset_id),
        )

        # Request range that includes data before and after
        start_date = datetime(2024, 1, 1, 0, 0, 0)  # Jan 1 midnight
        end_date = datetime(2024, 1, 10, 0, 0, 0)  # Jan 10 midnight

        missing_ranges = tracker.calculate_missing_ranges(asset_id, "stock", start_date, end_date)

        # Should have 2 gaps: before existing data and after
        assert len(missing_ranges) == 2

        # Check gap before: should end just before existing_time (not a full day before)
        gap_before = missing_ranges[0]
        # Handle timezone conversion - compare without timezone
        gap_before_start = (
            gap_before[0].replace(tzinfo=None) if gap_before[0].tzinfo else gap_before[0]
        )
        assert gap_before_start == start_date

        # gap_end should be just before existing_time (microseconds offset), not a full day
        expected_gap_end = existing_time - timedelta(microseconds=1)
        gap_before_end = (
            gap_before[1].replace(tzinfo=None) if gap_before[1].tzinfo else gap_before[1]
        )
        expected_gap_end_no_tz = (
            expected_gap_end.replace(tzinfo=None) if expected_gap_end.tzinfo else expected_gap_end
        )
        assert gap_before_end == expected_gap_end_no_tz

        # Check gap after: should start just after existing_time (not a full day after)
        gap_after = missing_ranges[1]
        # gap_start should be just after existing_time (microseconds offset), not a full day
        expected_gap_start = existing_time + timedelta(microseconds=1)
        gap_after_start = gap_after[0].replace(tzinfo=None) if gap_after[0].tzinfo else gap_after[0]
        expected_gap_start_no_tz = (
            expected_gap_start.replace(tzinfo=None)
            if expected_gap_start.tzinfo
            else expected_gap_start
        )
        assert gap_after_start == expected_gap_start_no_tz

        gap_after_end = gap_after[1].replace(tzinfo=None) if gap_after[1].tzinfo else gap_after[1]
        assert gap_after_end == end_date

        # Verify the gap boundaries don't skip data (using microseconds, not days)
        # Gap before should include all time from start_date to just before existing_time
        existing_time_no_tz = (
            existing_time.replace(tzinfo=None) if existing_time.tzinfo else existing_time
        )
        assert gap_before_end < existing_time_no_tz
        time_diff = (existing_time_no_tz - gap_before_end).total_seconds()
        assert time_diff < 1  # Less than 1 second difference (microseconds offset)
        assert time_diff > 0  # Should be positive (gap_end is before existing_time)

        # Gap after should include all time from just after existing_time to end_date
        assert gap_after_start > existing_time_no_tz
        time_diff = (gap_after_start - existing_time_no_tz).total_seconds()
        assert time_diff < 1  # Less than 1 second difference (microseconds offset)
        assert time_diff > 0  # Should be positive (gap_start is after existing_time)

        # Cleanup
        db_cursor.execute("DELETE FROM market_data WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_gap_boundary_with_same_day_data(self, db_cursor):
        """Test gap boundaries when data exists at different times on the same day."""
        tracker = IncrementalTracker()

        # Clean up
        db_cursor.execute(
            "DELETE FROM market_data WHERE asset_id IN (SELECT asset_id FROM assets WHERE symbol = 'SAME_DAY_GAP')"
        )
        db_cursor.execute("DELETE FROM assets WHERE symbol = 'SAME_DAY_GAP'")

        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            symbol="SAME_DAY_GAP",
            asset_type="stock",
            name="Same Day Gap",
        )

        # Insert data at 9 AM
        morning_time = datetime(2024, 1, 5, 9, 0, 0)
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
            VALUES (%s, %s, 100.0, 105.0, 99.0, 104.0, 1000000)
            """,
            (morning_time, asset_id),
        )

        # Request range from midnight to midnight next day
        start_date = datetime(2024, 1, 5, 0, 0, 0)  # Same day, midnight
        end_date = datetime(2024, 1, 6, 0, 0, 0)  # Next day, midnight

        missing_ranges = tracker.calculate_missing_ranges(asset_id, "stock", start_date, end_date)

        # Should have 2 gaps: before 9 AM and after 9 AM (same day)
        assert len(missing_ranges) == 2

        # Gap before: midnight to just before 9 AM
        gap_before = missing_ranges[0]
        gap_before_start = (
            gap_before[0].replace(tzinfo=None) if gap_before[0].tzinfo else gap_before[0]
        )
        assert gap_before_start == start_date

        expected_gap_end = morning_time - timedelta(microseconds=1)
        gap_before_end = (
            gap_before[1].replace(tzinfo=None) if gap_before[1].tzinfo else gap_before[1]
        )
        expected_gap_end_no_tz = (
            expected_gap_end.replace(tzinfo=None) if expected_gap_end.tzinfo else expected_gap_end
        )
        assert gap_before_end == expected_gap_end_no_tz

        # Gap after: just after 9 AM to midnight next day
        gap_after = missing_ranges[1]
        expected_gap_start = morning_time + timedelta(microseconds=1)
        gap_after_start = gap_after[0].replace(tzinfo=None) if gap_after[0].tzinfo else gap_after[0]
        expected_gap_start_no_tz = (
            expected_gap_start.replace(tzinfo=None)
            if expected_gap_start.tzinfo
            else expected_gap_start
        )
        assert gap_after_start == expected_gap_start_no_tz

        gap_after_end = gap_after[1].replace(tzinfo=None) if gap_after[1].tzinfo else gap_after[1]
        assert gap_after_end == end_date

        # Verify microseconds offset (not days)
        morning_time_no_tz = (
            morning_time.replace(tzinfo=None) if morning_time.tzinfo else morning_time
        )
        time_diff_before = (morning_time_no_tz - gap_before_end).total_seconds()
        time_diff_after = (gap_after_start - morning_time_no_tz).total_seconds()
        assert time_diff_before < 1  # Less than 1 second (microseconds)
        assert time_diff_after < 1  # Less than 1 second (microseconds)

        # Cleanup
        db_cursor.execute("DELETE FROM market_data WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))
