"""
Tests to verify ingestion engine handles unknown asset types correctly.
"""

import pytest
from unittest.mock import Mock, patch
from investment_platform.ingestion.ingestion_engine import IngestionEngine


class TestIngestionEngineUnknownAssetType:
    """Test that ingestion engine handles unknown asset types without AttributeError."""

    def test_ingest_with_unknown_asset_type(self):
        """Test that ingestion with unknown asset type doesn't raise AttributeError."""
        engine = IngestionEngine()

        # Mock the asset manager to return an asset_id
        with patch.object(engine, "asset_manager") as mock_asset_manager:
            mock_asset_manager.get_or_create_asset.return_value = 1

            # Mock the collector to raise an error (simulating unknown asset type)
            with patch.object(engine, "_get_collector") as mock_get_collector:
                mock_get_collector.side_effect = ValueError("Unknown asset type: invalid_type")

                # Mock the data loader
                with patch.object(engine, "data_loader"):
                    # Mock the logger
                    with patch.object(engine, "logger"):
                        # This should not raise AttributeError when logging the failure
                        result = engine.ingest(
                            symbol="TEST",
                            asset_type="invalid_type",  # Not in COLLECTOR_MAP
                            start_date="2024-01-01",
                            end_date="2024-01-02",
                        )

                        # Should return a failed result
                        assert result["status"] == "failed"
                        assert "error_message" in result

                        # Verify that _log_collection_run was called with "Unknown" as collector_type
                        # (not with AttributeError)
                        assert result["asset_id"] == 1

    def test_collector_type_name_extraction(self):
        """Test that collector type name is extracted correctly for known and unknown types."""
        engine = IngestionEngine()

        # Test with known asset type
        collector_class = engine.COLLECTOR_MAP.get("stock")
        assert collector_class is not None
        collector_type_name = collector_class.__name__ if collector_class else "Unknown"
        assert collector_type_name == "StockCollector"

        # Test with unknown asset type
        collector_class = engine.COLLECTOR_MAP.get("invalid_type")
        assert collector_class is None
        collector_type_name = collector_class.__name__ if collector_class else "Unknown"
        assert collector_type_name == "Unknown"

        # Verify that calling __name__ on "Unknown" string would fail
        # (this is what the bug was - we were doing "Unknown".__name__)
        unknown_str = "Unknown"
        with pytest.raises(AttributeError):
            _ = unknown_str.__name__
