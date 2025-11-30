"""
Tests for database functions and triggers.
"""

import pytest
from datetime import datetime, timedelta
from tests.utils import db_helpers


class TestUpdateUpdatedAtTrigger:
    """Test the update_updated_at_column trigger."""
    
    def test_trigger_updates_updated_at(self, db_cursor, db_connection):
        """Test that updated_at is automatically updated on asset update."""
        import uuid
        unique_symbol = f'TRIGGER_TEST_{uuid.uuid4().hex[:8]}'
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, 'stock', 'Test Stock', 'Test'
        )
        db_connection.commit()
        
        # Get initial updated_at
        db_cursor.execute("SELECT updated_at FROM assets WHERE asset_id = %s;", (asset_id,))
        initial_updated_at = db_cursor.fetchone()[0]
        
        # Wait a moment and update the asset
        import time
        time.sleep(1)
        
        db_cursor.execute("""
            UPDATE assets 
            SET name = 'Updated Test Stock' 
            WHERE asset_id = %s;
        """, (asset_id,))
        db_connection.commit()
        
        # Get updated_at after modification
        db_cursor.execute("SELECT updated_at FROM assets WHERE asset_id = %s;", (asset_id,))
        updated_at = db_cursor.fetchone()[0]
        
        assert updated_at > initial_updated_at, \
            "updated_at should be updated when asset is modified"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()
    
    def test_trigger_does_not_update_on_insert(self, db_cursor, db_connection):
        """Test that updated_at is not changed on insert (only on update)."""
        import uuid
        unique_symbol = f'TRIGGER_INSERT_{uuid.uuid4().hex[:8]}'
        db_cursor.execute("""
            INSERT INTO assets (symbol, asset_type, name, source)
            VALUES (%s, 'stock', 'Test Stock', 'Test')
            RETURNING created_at, updated_at;
        """, (unique_symbol,))
        result = db_cursor.fetchone()
        created_at = result[0]
        updated_at = result[1]
        
        # created_at and updated_at should be the same on insert
        assert abs((created_at - updated_at).total_seconds()) < 1, \
            "created_at and updated_at should be the same on insert"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE symbol = %s;", (unique_symbol,))
        db_connection.commit()


class TestGetAssetBySymbol:
    """Test the get_asset_by_symbol function."""
    
    def test_get_existing_asset(self, db_cursor, db_connection):
        """Test retrieving an existing asset by symbol."""
        import uuid
        unique_symbol = f'FUNC_TEST_{uuid.uuid4().hex[:8]}'
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, 'stock', 'Test Stock', 'Test',
            exchange='NYSE', currency='USD'
        )
        db_connection.commit()
        
        db_cursor.execute("SELECT * FROM get_asset_by_symbol(%s);", (unique_symbol,))
        result = db_cursor.fetchone()
        
        assert result is not None, "Function should return asset for existing symbol"
        assert result[0] == asset_id, "Function should return correct asset_id"
        assert result[1] == unique_symbol, "Function should return correct symbol"
        assert result[2] == 'stock', "Function should return correct asset_type"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()
    
    def test_get_nonexistent_asset(self, db_cursor):
        """Test retrieving a non-existent asset returns no rows."""
        db_cursor.execute("SELECT * FROM get_asset_by_symbol('NONEXISTENT_SYMBOL');")
        result = db_cursor.fetchone()
        
        assert result is None, "Function should return no rows for non-existent symbol"
    
    def test_get_inactive_asset(self, db_cursor, db_connection):
        """Test that inactive assets are not returned."""
        import uuid
        unique_symbol = f'INACTIVE_TEST_{uuid.uuid4().hex[:8]}'
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, 'stock', 'Test Stock', 'Test'
        )
        db_connection.commit()
        
        # Deactivate asset
        db_cursor.execute("UPDATE assets SET is_active = FALSE WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()
        
        # Try to retrieve inactive asset
        db_cursor.execute("SELECT * FROM get_asset_by_symbol(%s);", (unique_symbol,))
        result = db_cursor.fetchone()
        
        assert result is None, "Function should not return inactive assets"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()


class TestGetLatestMarketData:
    """Test the get_latest_market_data function."""
    
    def test_get_latest_data_exists(self, db_cursor, db_connection):
        """Test retrieving latest market data for an asset with data."""
        import uuid
        unique_symbol = f'LATEST_TEST_{uuid.uuid4().hex[:8]}'
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, 'stock', 'Test Stock', 'Test'
        )
        db_connection.commit()
        
        # Insert multiple data points
        base_time = datetime.now() - timedelta(days=2)
        for i in range(3):
            db_cursor.execute("""
                INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (base_time + timedelta(hours=i*6), asset_id, 100.0 + i, 110.0 + i, 95.0 + i, 105.0 + i, 1000))
        db_connection.commit()
        
        # Get latest data
        db_cursor.execute("SELECT * FROM get_latest_market_data(%s);", (asset_id,))
        result = db_cursor.fetchone()
        
        assert result is not None, "Function should return latest market data"
        # Result columns: time, open, high, low, close, volume
        # time is the first column (index 0)
        result_time = result[0]
        result_close = result[4]  # close is 5th column (0-indexed: time, open, high, low, close, volume)
        # Allow small time difference due to execution time
        # Handle timezone-aware vs naive datetime comparison
        expected_time = base_time + timedelta(hours=12)
        if result_time.tzinfo is not None and expected_time.tzinfo is None:
            # Make expected_time timezone-aware if result is
            from datetime import timezone
            expected_time = expected_time.replace(tzinfo=timezone.utc)
        elif result_time.tzinfo is None and expected_time.tzinfo is not None:
            # Make result_time timezone-aware if expected is
            from datetime import timezone
            result_time = result_time.replace(tzinfo=timezone.utc)
        time_diff = abs((result_time - expected_time).total_seconds())
        assert time_diff < 60, f"Function should return most recent time, got {result_time}, expected {expected_time}"
        # Convert Decimal to float for comparison
        result_close_float = float(result_close) if hasattr(result_close, '__float__') else result_close
        assert abs(result_close_float - 107.0) < 0.01, f"Function should return latest close price, got {result_close_float}, expected 107.0"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()
    
    def test_get_latest_data_no_data(self, db_cursor, db_connection):
        """Test retrieving latest market data for an asset with no data."""
        import uuid
        unique_symbol = f'NO_DATA_TEST_{uuid.uuid4().hex[:8]}'
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, 'stock', 'Test Stock', 'Test'
        )
        db_connection.commit()
        
        # Get latest data
        db_cursor.execute("SELECT * FROM get_latest_market_data(%s);", (asset_id,))
        result = db_cursor.fetchone()
        
        assert result is None, "Function should return no rows when no data exists"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()


class TestCheckDataFreshness:
    """Test the check_data_freshness function."""
    
    @pytest.mark.parametrize("data_type", [
        'market_data',
        'forex_rates',
        'bond_rates',
        'economic_data'
    ])
    def test_check_freshness_with_data(self, db_cursor, db_connection, data_type):
        """Test data freshness check with recent data."""
        if data_type == 'market_data':
            import uuid
            unique_symbol = f'FRESH_TEST_{uuid.uuid4().hex[:8]}'
            asset_id = db_helpers.insert_sample_asset(
                db_cursor, unique_symbol, 'stock', 'Test Stock', 'Test'
            )
            db_connection.commit()
            
            # Insert recent data (1 hour ago)
            db_cursor.execute("""
                INSERT INTO market_data (time, asset_id, open, high, low, close)
                VALUES (%s, %s, 100.0, 110.0, 95.0, 105.0);
            """, (datetime.now() - timedelta(hours=1), asset_id))
            db_connection.commit()
        elif data_type == 'forex_rates':
            import uuid
            unique_symbol = f'EURUSD_FRESH_{uuid.uuid4().hex[:8]}'
            asset_id = db_helpers.insert_sample_asset(
                db_cursor, unique_symbol, 'forex', 'EUR/USD', 'Test',
                base_currency='EUR', quote_currency='USD'
            )
            db_connection.commit()
            
            db_cursor.execute("""
                INSERT INTO forex_rates (time, asset_id, rate)
                VALUES (%s, %s, 1.10);
            """, (datetime.now() - timedelta(hours=1), asset_id))
            db_connection.commit()
        elif data_type == 'bond_rates':
            import uuid
            unique_symbol = f'BOND_FRESH_{uuid.uuid4().hex[:8]}'
            asset_id = db_helpers.insert_sample_asset(
                db_cursor, unique_symbol, 'bond', 'Test Bond', 'Test'
            )
            db_connection.commit()
            
            db_cursor.execute("""
                INSERT INTO bond_rates (time, asset_id, rate)
                VALUES (%s, %s, 2.5);
            """, (datetime.now() - timedelta(hours=1), asset_id))
            db_connection.commit()
        else:  # economic_data
            import uuid
            unique_symbol = f'ECON_FRESH_{uuid.uuid4().hex[:8]}'
            asset_id = db_helpers.insert_sample_asset(
                db_cursor, unique_symbol, 'economic_indicator', 'Test Indicator', 'Test'
            )
            db_connection.commit()
            
            db_cursor.execute("""
                INSERT INTO economic_data (time, asset_id, value)
                VALUES (%s, %s, 100.0);
            """, (datetime.now() - timedelta(hours=1), asset_id))
            db_connection.commit()
        
        # Check freshness
        db_cursor.execute("SELECT * FROM check_data_freshness(%s, %s);", (asset_id, data_type))
        result = db_cursor.fetchone()
        
        assert result is not None, "Function should return freshness data"
        assert result[2] is not None, "latest_time should not be NULL"
        assert result[3] is not None, "hours_old should not be NULL"
        assert result[4] is False, "Data should not be stale (less than 24 hours old)"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()
    
    def test_check_freshness_stale_data(self, db_cursor, db_connection):
        """Test data freshness check with stale data (>24 hours old)."""
        import uuid
        unique_symbol = f'STALE_TEST_{uuid.uuid4().hex[:8]}'
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, 'stock', 'Test Stock', 'Test'
        )
        db_connection.commit()
        
        # Insert stale data (25 hours ago)
        db_cursor.execute("""
            INSERT INTO market_data (time, asset_id, open, high, low, close)
            VALUES (%s, %s, 100.0, 110.0, 95.0, 105.0);
        """, (datetime.now() - timedelta(hours=25), asset_id))
        db_connection.commit()
        
        # Check freshness
        db_cursor.execute("SELECT * FROM check_data_freshness(%s, 'market_data');", (asset_id,))
        result = db_cursor.fetchone()
        
        assert result is not None, "Function should return freshness data"
        assert result[4] is True, "Data should be stale (more than 24 hours old)"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()
    
    def test_check_freshness_no_data(self, db_cursor, db_connection):
        """Test data freshness check with no data."""
        import uuid
        unique_symbol = f'NO_DATA_FRESH_{uuid.uuid4().hex[:8]}'
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, 'stock', 'Test Stock', 'Test'
        )
        db_connection.commit()
        
        # Check freshness
        db_cursor.execute("SELECT * FROM check_data_freshness(%s, 'market_data');", (asset_id,))
        result = db_cursor.fetchone()
        
        assert result is not None, "Function should return freshness data"
        assert result[2] is None, "latest_time should be NULL when no data exists"
        assert result[4] is True, "Data should be considered stale when no data exists"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()
    
    def test_check_freshness_invalid_data_type(self, db_cursor, db_connection):
        """Test that invalid data_type raises an error."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, 'INVALID_TYPE_TEST', 'stock', 'Test Stock', 'Test'
        )
        db_connection.commit()
        
        # Try invalid data type
        with pytest.raises(Exception) as exc_info:
            db_cursor.execute("SELECT * FROM check_data_freshness(%s, 'invalid_type');", (asset_id,))
            db_cursor.fetchone()
        
        assert 'invalid' in str(exc_info.value).lower() or 'exception' in str(exc_info.value).lower()
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()


class TestGetCollectionStats:
    """Test the get_collection_stats function."""
    
    def test_get_collection_stats(self, db_cursor, db_connection):
        """Test retrieving collection statistics."""
        import uuid
        unique_symbol = f'STATS_TEST_{uuid.uuid4().hex[:8]}'
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, 'stock', 'Test Stock', 'Test'
        )
        db_connection.commit()
        
        # Insert collection log entries
        now = datetime.now()
        for i in range(3):
            db_cursor.execute("""
                INSERT INTO data_collection_log 
                (asset_id, collector_type, start_date, end_date, records_collected, status, execution_time_ms)
                VALUES (%s, 'TestCollector', %s, %s, %s, %s, %s);
            """, (
                asset_id,
                now - timedelta(days=i),
                now - timedelta(days=i) + timedelta(hours=1),
                100 + i * 10,
                'success' if i < 2 else 'failed',
                1000 + i * 100
            ))
        db_connection.commit()
        
        # Get stats for a very short time window to avoid counting other test data
        db_cursor.execute("SELECT * FROM get_collection_stats(1);")
        results = db_cursor.fetchall()
        
        assert len(results) > 0, "Function should return statistics"
        
        # Find TestCollector stats
        test_collector_stats = [r for r in results if r[0] == 'TestCollector']
        # May find more than expected if other tests ran recently, so verify structure
        assert len(test_collector_stats) >= 1, "Should find TestCollector statistics"
        
        stats = test_collector_stats[0]
        # Verify the stats structure is correct - should have at least the expected values
        assert stats[1] >= 3, f"total_runs should be at least 3, got {stats[1]}"
        assert stats[2] >= 2, f"successful_runs should be at least 2, got {stats[2]}"
        assert stats[3] >= 1, f"failed_runs should be at least 1, got {stats[3]}"
        assert stats[5] > 0, "total_records_collected should be greater than 0"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()
    
    def test_get_collection_stats_no_data(self, db_cursor):
        """Test collection stats when no data exists."""
        db_cursor.execute("SELECT * FROM get_collection_stats(7);")
        results = db_cursor.fetchall()
        
        # Should return empty result set, not error
        assert isinstance(results, list), "Function should return a list even with no data"

