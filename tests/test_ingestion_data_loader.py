"""
Tests for data loader in ingestion module.
"""

import pytest
import pandas as pd
from datetime import datetime
from investment_platform.ingestion.data_loader import DataLoader
from tests.utils import db_helpers


class TestDataLoader:
    """Test data loading functionality."""

    def test_load_market_data(self, db_cursor):
        """Test loading market data."""
        loader = DataLoader(use_copy=False)  # Use insert for testing

        # Create test asset
        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            symbol="LOADER_STOCK",
            asset_type="stock",
            name="Loader Stock",
        )

        # Create sample data
        dates = pd.date_range(start="2024-01-01", periods=3, freq="D")
        data = pd.DataFrame(
            {
                "time": dates,
                "asset_id": [asset_id] * 3,
                "open": [100.0, 101.0, 102.0],
                "high": [105.0, 106.0, 107.0],
                "low": [99.0, 100.0, 101.0],
                "close": [104.0, 105.0, 106.0],
                "volume": [1000000, 1100000, 1200000],
            }
        )

        # Load data
        records_loaded = loader.load_data(data, "stock", on_conflict="do_nothing")

        assert records_loaded == 3

        # Verify data was loaded
        db_cursor.execute(
            "SELECT COUNT(*) FROM market_data WHERE asset_id = %s",
            (asset_id,),
        )
        count = db_cursor.fetchone()[0]
        assert count == 3

        # Cleanup
        db_cursor.execute("DELETE FROM market_data WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_load_forex_rates(self, db_cursor):
        """Test loading forex rates."""
        loader = DataLoader(use_copy=False)

        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            symbol="USD_EUR",
            asset_type="forex",
            name="USD/EUR",
        )

        dates = pd.date_range(start="2024-01-01", periods=2, freq="D")
        data = pd.DataFrame(
            {
                "time": dates,
                "asset_id": [asset_id] * 2,
                "rate": [1.10, 1.11],
            }
        )

        records_loaded = loader.load_data(data, "forex", on_conflict="do_nothing")
        assert records_loaded == 2

        # Cleanup
        db_cursor.execute("DELETE FROM forex_rates WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_load_data_duplicate_handling(self, db_cursor):
        """Test handling duplicate data."""
        loader = DataLoader(use_copy=False)

        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            symbol="DUPLICATE_TEST",
            asset_type="stock",
            name="Duplicate Test",
        )

        # Create data
        date = datetime(2024, 1, 1, 12, 0, 0)
        data = pd.DataFrame(
            {
                "time": [date],
                "asset_id": [asset_id],
                "open": [100.0],
                "high": [105.0],
                "low": [99.0],
                "close": [104.0],
                "volume": [1000000],
            }
        )

        # Load first time
        records1 = loader.load_data(data, "stock", on_conflict="do_nothing")
        assert records1 == 1

        # Load again (should skip duplicates)
        records2 = loader.load_data(data, "stock", on_conflict="do_nothing")
        assert records2 == 0  # Should skip duplicates

        # Cleanup
        db_cursor.execute("DELETE FROM market_data WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_load_empty_dataframe(self, db_cursor):
        """Test loading empty DataFrame."""
        loader = DataLoader()

        empty_df = pd.DataFrame()
        records = loader.load_data(empty_df, "stock", on_conflict="do_nothing")

        assert records == 0

    def test_load_data_invalid_asset_type(self, db_cursor):
        """Test loading with invalid asset type."""
        loader = DataLoader()

        data = pd.DataFrame({"time": [datetime.now()], "asset_id": [1], "value": [100.0]})

        with pytest.raises(ValueError, match="Unknown asset type"):
            loader.load_data(data, "invalid_type", on_conflict="do_nothing")
