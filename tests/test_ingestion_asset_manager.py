"""
Tests for asset manager in ingestion module.
"""

import pytest
from datetime import datetime
from investment_platform.ingestion.asset_manager import AssetManager
from tests.utils import db_helpers


class TestAssetManager:
    """Test asset management functionality."""

    def test_get_or_create_asset_new(self, db_cursor):
        """Test creating a new asset."""
        manager = AssetManager()
        
        asset_id = manager.get_or_create_asset(
            symbol="TEST_STOCK",
            asset_type="stock",
            name="Test Stock Company",
            source="Test Source",
            exchange="NYSE",
            currency="USD",
        )
        
        assert asset_id is not None
        assert isinstance(asset_id, int)
        
        # Verify asset was created
        db_cursor.execute(
            "SELECT * FROM assets WHERE asset_id = %s",
            (asset_id,),
        )
        result = db_cursor.fetchone()
        assert result is not None
        assert result[1] == "TEST_STOCK"  # symbol
        assert result[2] == "stock"  # asset_type
        assert result[3] == "Test Stock Company"  # name
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_get_or_create_asset_existing(self, db_cursor):
        """Test getting an existing asset."""
        manager = AssetManager()
        
        # Create asset first
        asset_id1 = manager.get_or_create_asset(
            symbol="EXISTING_STOCK",
            asset_type="stock",
            name="Existing Stock",
            source="Test Source",
        )
        
        # Get same asset again
        asset_id2 = manager.get_or_create_asset(
            symbol="EXISTING_STOCK",
            asset_type="stock",
            name="Existing Stock",
            source="Test Source",
        )
        
        assert asset_id1 == asset_id2
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id1,))

    def test_get_or_create_asset_with_metadata(self, db_cursor):
        """Test creating asset with metadata."""
        manager = AssetManager()
        
        asset_id = manager.get_or_create_asset(
            symbol="META_STOCK",
            asset_type="stock",
            name="Meta Stock",
            source="Test Source",
            sector="Technology",
            industry="Software",
            metadata={"market_cap": 1000000, "employees": 5000},
        )
        
        # Verify metadata
        db_cursor.execute(
            "SELECT metadata FROM assets WHERE asset_id = %s",
            (asset_id,),
        )
        result = db_cursor.fetchone()
        assert result[0] is not None
        assert result[0]["market_cap"] == 1000000
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_get_asset_id(self, db_cursor):
        """Test getting asset ID by symbol."""
        manager = AssetManager()
        
        # Create asset
        asset_id = manager.get_or_create_asset(
            symbol="LOOKUP_STOCK",
            asset_type="stock",
            name="Lookup Stock",
            source="Test Source",
        )
        
        # Lookup by symbol
        found_id = manager.get_asset_id("LOOKUP_STOCK")
        assert found_id == asset_id
        
        # Test non-existent symbol
        not_found = manager.get_asset_id("NON_EXISTENT")
        assert not_found is None
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

    def test_get_asset_info(self, db_cursor):
        """Test getting asset information."""
        manager = AssetManager()
        
        # Create asset
        asset_id = manager.get_or_create_asset(
            symbol="INFO_STOCK",
            asset_type="stock",
            name="Info Stock",
            source="Test Source",
            exchange="NASDAQ",
        )
        
        # Get info
        info = manager.get_asset_info(asset_id)
        
        assert info is not None
        assert info["asset_id"] == asset_id
        assert info["symbol"] == "INFO_STOCK"
        assert info["asset_type"] == "stock"
        assert info["name"] == "Info Stock"
        assert info["exchange"] == "NASDAQ"
        
        # Test non-existent asset
        not_found = manager.get_asset_info(999999)
        assert not_found is None
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))

