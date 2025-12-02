"""
Tests for ingestion engine - end-to-end integration tests.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from investment_platform.ingestion.ingestion_engine import IngestionEngine
from tests.utils import db_helpers


class TestIngestionEngine:
    """Test ingestion engine functionality."""

    @pytest.fixture
    def mock_collector(self):
        """Create a mock collector."""
        collector = Mock()
        collector.__class__.__name__ = "StockCollector"

        # Mock get_asset_info
        collector.get_asset_info.return_value = {
            "symbol": "TEST_STOCK",
            "name": "Test Stock Company",
            "source": "Test Source",
            "exchange": "NYSE",
            "currency": "USD",
            "type": "stock",
        }

        return collector

    @pytest.fixture
    def sample_data(self):
        """Create sample market data."""
        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        return pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [105.0, 106.0, 107.0, 108.0, 109.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "close": [104.0, 105.0, 106.0, 107.0, 108.0],
                "volume": [1000000, 1100000, 1200000, 1300000, 1400000],
            },
            index=dates,
        )

    def test_ingest_new_asset(self, db_cursor, mock_collector, sample_data):
        """Test ingesting data for a new asset."""
        engine = IngestionEngine(incremental=False, use_copy=False)

        # Mock collector
        mock_collector.collect_historical_data.return_value = sample_data

        with patch.object(engine, "_get_collector", return_value=mock_collector):
            result = engine.ingest(
                symbol="TEST_STOCK",
                asset_type="stock",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 5),
            )

        assert result["status"] in ["success", "partial"]
        assert result["asset_id"] is not None
        assert result["records_collected"] == 5
        assert result["records_loaded"] > 0

        # Verify asset was created
        db_cursor.execute("SELECT asset_id FROM assets WHERE symbol = 'TEST_STOCK'")
        asset_result = db_cursor.fetchone()
        assert asset_result is not None

        # Verify data was loaded
        db_cursor.execute(
            "SELECT COUNT(*) FROM market_data WHERE asset_id = %s",
            (result["asset_id"],),
        )
        count = db_cursor.fetchone()[0]
        assert count > 0

        # Cleanup
        db_cursor.execute(
            "DELETE FROM market_data WHERE asset_id = %s",
            (result["asset_id"],),
        )
        db_cursor.execute(
            "DELETE FROM data_collection_log WHERE asset_id = %s",
            (result["asset_id"],),
        )
        db_cursor.execute(
            "DELETE FROM assets WHERE asset_id = %s",
            (result["asset_id"],),
        )

    def test_ingest_incremental_mode(self, db_cursor, mock_collector, sample_data):
        """Test incremental ingestion mode."""
        engine = IngestionEngine(incremental=True, use_copy=False)

        # Clean up any existing test data first
        db_cursor.execute(
            "DELETE FROM market_data WHERE asset_id IN (SELECT asset_id FROM assets WHERE symbol = 'INCREMENTAL_TEST')"
        )
        db_cursor.execute("DELETE FROM assets WHERE symbol = 'INCREMENTAL_TEST'")

        # Create asset and insert some existing data
        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            symbol="INCREMENTAL_TEST",
            asset_type="stock",
            name="Incremental Test",
        )

        # Insert existing data for Jan 3-5
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
            VALUES 
                ('2024-01-03 12:00:00', %s, 102.0, 107.0, 101.0, 106.0, 1200000),
                ('2024-01-04 12:00:00', %s, 103.0, 108.0, 102.0, 107.0, 1300000),
                ('2024-01-05 12:00:00', %s, 104.0, 109.0, 103.0, 108.0, 1400000)
            """,
            (asset_id, asset_id, asset_id),
        )

        # Mock collector to return data for Jan 1-5
        mock_collector.collect_historical_data.return_value = sample_data

        with patch.object(engine, "_get_collector", return_value=mock_collector):
            result = engine.ingest(
                symbol="INCREMENTAL_TEST",
                asset_type="stock",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 5),
            )

        # Should only fetch missing data (Jan 1-2)
        assert result["status"] in ["success", "partial"]

        # Cleanup
        db_cursor.execute(
            "DELETE FROM market_data WHERE asset_id = %s",
            (asset_id,),
        )
        db_cursor.execute(
            "DELETE FROM data_collection_log WHERE asset_id = %s",
            (asset_id,),
        )
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_ingest_empty_data(self, db_cursor, mock_collector):
        """Test ingesting when collector returns empty data."""
        engine = IngestionEngine(incremental=False, use_copy=False)

        # Mock collector to return empty DataFrame
        mock_collector.collect_historical_data.return_value = pd.DataFrame()

        with patch.object(engine, "_get_collector", return_value=mock_collector):
            result = engine.ingest(
                symbol="EMPTY_TEST",
                asset_type="stock",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 5),
            )

        # Should still create asset but load no data
        assert result["asset_id"] is not None
        assert result["records_collected"] == 0
        assert result["records_loaded"] == 0
        assert result["status"] == "failed"  # No data loaded

        # Cleanup
        db_cursor.execute(
            "DELETE FROM data_collection_log WHERE asset_id = %s",
            (result["asset_id"],),
        )
        db_cursor.execute(
            "DELETE FROM assets WHERE asset_id = %s",
            (result["asset_id"],),
        )

    def test_ingest_logs_to_collection_log(self, db_cursor, mock_collector, sample_data):
        """Test that ingestion logs to data_collection_log table."""
        engine = IngestionEngine(incremental=False, use_copy=False)

        mock_collector.collect_historical_data.return_value = sample_data

        with patch.object(engine, "_get_collector", return_value=mock_collector):
            result = engine.ingest(
                symbol="LOG_TEST",
                asset_type="stock",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 5),
            )

        # Verify log entry was created
        db_cursor.execute(
            """
            SELECT log_id, asset_id, collector_type, start_date, end_date,
                   records_collected, status, error_message, execution_time_ms
            FROM data_collection_log 
            WHERE asset_id = %s 
            ORDER BY created_at DESC 
            LIMIT 1
            """,
            (result["asset_id"],),
        )
        log_entry = db_cursor.fetchone()

        assert log_entry is not None
        assert log_entry[2] == "StockCollector"  # collector_type
        assert log_entry[5] == result["records_collected"]  # records_collected
        assert log_entry[6] == result["status"]  # status

        # Cleanup
        db_cursor.execute(
            "DELETE FROM market_data WHERE asset_id = %s",
            (result["asset_id"],),
        )
        db_cursor.execute(
            "DELETE FROM data_collection_log WHERE asset_id = %s",
            (result["asset_id"],),
        )
        db_cursor.execute(
            "DELETE FROM assets WHERE asset_id = %s",
            (result["asset_id"],),
        )

    def test_ingest_error_handling(self, db_cursor, mock_collector):
        """Test error handling during ingestion."""
        engine = IngestionEngine(incremental=False, use_copy=False)

        # Mock collector to raise an error
        mock_collector.collect_historical_data.side_effect = Exception("Test error")

        with patch.object(engine, "_get_collector", return_value=mock_collector):
            result = engine.ingest(
                symbol="ERROR_TEST",
                asset_type="stock",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 5),
            )

        assert result["status"] == "failed"
        assert result["error_message"] is not None
        assert "Test error" in result["error_message"]
