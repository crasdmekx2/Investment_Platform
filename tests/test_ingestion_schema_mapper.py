"""
Tests for schema mapper in ingestion module.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from investment_platform.ingestion.schema_mapper import SchemaMapper


class TestSchemaMapper:
    """Test schema mapping functionality."""

    def test_map_to_market_data(self):
        """Test mapping to market_data format."""
        mapper = SchemaMapper()

        # Create sample OHLCV data
        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [105.0, 106.0, 107.0, 108.0, 109.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "close": [104.0, 105.0, 106.0, 107.0, 108.0],
                "volume": [1000000, 1100000, 1200000, 1300000, 1400000],
                "dividends": [0.0, 0.5, 0.0, 0.0, 0.0],
            },
            index=dates,
        )

        mapped = mapper.map_to_market_data(data, asset_id=1)

        assert not mapped.empty
        assert len(mapped) == 5
        assert "time" in mapped.columns
        assert "asset_id" in mapped.columns
        assert "open" in mapped.columns
        assert "high" in mapped.columns
        assert "low" in mapped.columns
        assert "close" in mapped.columns
        assert mapped["asset_id"].iloc[0] == 1
        assert mapped["open"].iloc[0] == 100.0

    def test_map_to_forex_rates(self):
        """Test mapping to forex_rates format."""
        mapper = SchemaMapper()

        dates = pd.date_range(start="2024-01-01", periods=3, freq="D")
        data = pd.DataFrame(
            {"rate": [1.10, 1.11, 1.12]},
            index=dates,
        )

        mapped = mapper.map_to_forex_rates(data, asset_id=2)

        assert not mapped.empty
        assert len(mapped) == 3
        assert "time" in mapped.columns
        assert "asset_id" in mapped.columns
        assert "rate" in mapped.columns
        assert mapped["asset_id"].iloc[0] == 2
        assert mapped["rate"].iloc[0] == 1.10

    def test_map_to_bond_rates(self):
        """Test mapping to bond_rates format."""
        mapper = SchemaMapper()

        dates = pd.date_range(start="2024-01-01", periods=3, freq="D")
        data = pd.DataFrame(
            {"value": [3.5, 3.6, 3.7]},
            index=dates,
        )

        mapped = mapper.map_to_bond_rates(data, asset_id=3)

        assert not mapped.empty
        assert len(mapped) == 3
        assert "time" in mapped.columns
        assert "asset_id" in mapped.columns
        assert "rate" in mapped.columns
        assert mapped["rate"].iloc[0] == 3.5

    def test_map_to_economic_data(self):
        """Test mapping to economic_data format."""
        mapper = SchemaMapper()

        dates = pd.date_range(start="2024-01-01", periods=3, freq="D")
        data = pd.DataFrame(
            {"value": [100.0, 101.0, 102.0]},
            index=dates,
        )

        mapped = mapper.map_to_economic_data(data, asset_id=4)

        assert not mapped.empty
        assert len(mapped) == 3
        assert "time" in mapped.columns
        assert "asset_id" in mapped.columns
        assert "value" in mapped.columns
        assert mapped["value"].iloc[0] == 100.0

    def test_map_data_stock(self):
        """Test map_data for stock asset type."""
        mapper = SchemaMapper()

        dates = pd.date_range(start="2024-01-01", periods=2, freq="D")
        data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [105.0, 106.0],
                "low": [99.0, 100.0],
                "close": [104.0, 105.0],
            },
            index=dates,
        )

        mapped = mapper.map_data(data, "stock", asset_id=1)

        assert not mapped.empty
        assert "time" in mapped.columns
        assert "asset_id" in mapped.columns

    def test_map_data_forex(self):
        """Test map_data for forex asset type."""
        mapper = SchemaMapper()

        dates = pd.date_range(start="2024-01-01", periods=2, freq="D")
        data = pd.DataFrame(
            {"rate": [1.10, 1.11]},
            index=dates,
        )

        mapped = mapper.map_data(data, "forex", asset_id=2)

        assert not mapped.empty
        assert "time" in mapped.columns
        assert "asset_id" in mapped.columns
        assert "rate" in mapped.columns

    def test_map_data_empty_dataframe(self):
        """Test mapping empty DataFrame."""
        mapper = SchemaMapper()

        empty_df = pd.DataFrame()
        mapped = mapper.map_to_market_data(empty_df, asset_id=1)

        assert mapped.empty

    def test_map_data_missing_required_columns(self):
        """Test mapping with missing required columns."""
        mapper = SchemaMapper()

        dates = pd.date_range(start="2024-01-01", periods=2, freq="D")
        data = pd.DataFrame(
            {"open": [100.0, 101.0]},  # Missing high, low, close
            index=dates,
        )

        with pytest.raises(ValueError, match="Missing required columns"):
            mapper.map_to_market_data(data, asset_id=1)
