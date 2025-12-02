"""
Unit tests for collector service.

Tests business logic for collector metadata and asset search.
"""

import pytest
from unittest.mock import patch, MagicMock

from investment_platform.api.services import collector_service


class TestCollectorService:
    """Test suite for collector service."""

    def test_get_collector_metadata_success(self):
        """Test getting collector metadata."""
        metadata = collector_service.get_collector_metadata()

        assert isinstance(metadata, dict)
        assert "stock" in metadata
        assert "crypto" in metadata
        assert "forex" in metadata
        assert "bond" in metadata
        assert "commodity" in metadata
        assert "economic_indicator" in metadata

    def test_get_collector_metadata_stock(self):
        """Test stock collector metadata."""
        metadata = collector_service.get_collector_metadata()

        stock_meta = metadata["stock"]
        assert stock_meta["name"] == "Stock"
        assert "intervals" in stock_meta
        assert "default_interval" in stock_meta
        assert stock_meta["supports_dividends"] is True
        assert stock_meta["supports_splits"] is True

    def test_get_collector_metadata_crypto(self):
        """Test crypto collector metadata."""
        metadata = collector_service.get_collector_metadata()

        crypto_meta = metadata["crypto"]
        assert crypto_meta["name"] == "Cryptocurrency"
        assert "granularities" in crypto_meta
        assert "default_granularity" in crypto_meta

    def test_get_collector_options_stock(self):
        """Test getting collector options for stock."""
        options = collector_service.get_collector_options("stock")

        assert isinstance(options, dict)
        assert "intervals" in options or "default_interval" in options

    def test_get_collector_options_crypto(self):
        """Test getting collector options for crypto."""
        options = collector_service.get_collector_options("crypto")

        assert isinstance(options, dict)
        assert "granularities" in options or "default_granularity" in options

    def test_get_collector_options_invalid_type(self):
        """Test getting collector options with invalid asset type."""
        with pytest.raises(ValueError):
            collector_service.get_collector_options("invalid_type")

    def test_search_assets_stock(self):
        """Test searching for stock assets."""
        results = collector_service.search_assets("stock", "AAPL", limit=10)

        assert isinstance(results, list)
        assert len(results) > 0
        # Should return AAPL from common stocks list
        assert any(r["symbol"] == "AAPL" for r in results)

    def test_search_assets_crypto(self):
        """Test searching for crypto assets."""
        results = collector_service.search_assets("crypto", "BTC", limit=10)

        assert isinstance(results, list)
        assert len(results) > 0
        # Should return BTC-USD from common crypto list
        assert any("BTC" in r["symbol"] for r in results)

    def test_search_assets_invalid_type(self):
        """Test searching with invalid asset type."""
        # The function doesn't raise ValueError, it just returns empty list
        results = collector_service.search_assets("invalid_type", "query", limit=10)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_assets_empty_results(self):
        """Test searching with no results."""
        results = collector_service.search_assets("stock", "NONEXISTENTXYZ123", limit=10)

        assert isinstance(results, list)
        assert len(results) == 0

    def test_validate_collection_params_stock(self):
        """Test validating collection parameters for stock."""
        result = collector_service.validate_collection_params(
            asset_type="stock", symbol="AAPL", collector_kwargs=None
        )

        assert isinstance(result, dict)
        assert "valid" in result
        assert result["valid"] is True
        assert len(result.get("errors", [])) == 0

    def test_validate_collection_params_invalid_type(self):
        """Test validating with invalid asset type."""
        result = collector_service.validate_collection_params(
            asset_type="invalid_type", symbol="TEST", collector_kwargs=None
        )

        assert isinstance(result, dict)
        assert result["valid"] is False
        assert len(result.get("errors", [])) > 0

    def test_validate_collection_params_missing_symbol(self):
        """Test validating with missing symbol."""
        result = collector_service.validate_collection_params(
            asset_type="stock", symbol="", collector_kwargs=None
        )

        assert isinstance(result, dict)
        assert result["valid"] is False
        assert len(result.get("errors", [])) > 0

    def test_validate_collection_params_invalid_dates(self):
        """Test validating with invalid interval."""
        result = collector_service.validate_collection_params(
            asset_type="stock", symbol="AAPL", collector_kwargs={"interval": "invalid_interval"}
        )

        assert isinstance(result, dict)
        assert result["valid"] is False
        assert len(result.get("errors", [])) > 0

    def test_get_collector_class(self):
        """Test getting collector class for asset type."""
        from investment_platform.collectors import StockCollector, CryptoCollector

        stock_class = collector_service.COLLECTOR_CLASSES["stock"]
        assert stock_class == StockCollector

        crypto_class = collector_service.COLLECTOR_CLASSES["crypto"]
        assert crypto_class == CryptoCollector

    def test_all_asset_types_have_metadata(self):
        """Test that all asset types have metadata."""
        metadata = collector_service.get_collector_metadata()

        for asset_type in collector_service.COLLECTOR_CLASSES.keys():
            assert asset_type in metadata, f"Missing metadata for {asset_type}"
