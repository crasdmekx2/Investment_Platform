"""
Tests to verify database schema objects are created correctly.
"""

import pytest
from tests.utils import db_helpers


class TestTimescaleDBExtension:
    """Test TimescaleDB extension installation."""
    
    def test_timescaledb_extension_exists(self, db_cursor):
        """Verify TimescaleDB extension is installed."""
        query = """
            SELECT installed_version 
            FROM pg_available_extensions 
            WHERE name = 'timescaledb';
        """
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        assert result is not None, "TimescaleDB extension not found"
        assert result[0] is not None, "TimescaleDB extension not installed"
    
    def test_timescaledb_extension_enabled(self, db_cursor):
        """Verify TimescaleDB extension is enabled."""
        query = """
            SELECT extname, extversion 
            FROM pg_extension 
            WHERE extname = 'timescaledb';
        """
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        assert result is not None, "TimescaleDB extension not enabled"
        assert result[0] == 'timescaledb', "TimescaleDB extension name mismatch"


class TestTables:
    """Test that all required tables exist."""
    
    @pytest.mark.parametrize("table_name", [
        'assets',
        'market_data',
        'forex_rates',
        'bond_rates',
        'economic_data',
        'data_collection_log'
    ])
    def test_table_exists(self, db_cursor, table_name):
        """Verify each required table exists."""
        assert db_helpers.table_exists(db_cursor, table_name), \
            f"Table '{table_name}' does not exist"
    
    def test_assets_table_columns(self, db_cursor):
        """Verify assets table has all required columns."""
        columns = db_helpers.get_table_columns(db_cursor, 'assets')
        column_names = [col['column_name'] for col in columns]
        
        required_columns = [
            'asset_id', 'symbol', 'asset_type', 'name', 'source',
            'is_active', 'created_at', 'updated_at'
        ]
        for col in required_columns:
            assert col in column_names, f"Column '{col}' missing from assets table"
    
    def test_market_data_table_columns(self, db_cursor):
        """Verify market_data table has all required columns."""
        columns = db_helpers.get_table_columns(db_cursor, 'market_data')
        column_names = [col['column_name'] for col in columns]
        
        required_columns = ['time', 'asset_id', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in column_names, f"Column '{col}' missing from market_data table"


class TestHypertables:
    """Test that TimescaleDB hypertables are created."""
    
    @pytest.mark.parametrize("table_name", [
        'market_data',
        'forex_rates',
        'bond_rates',
        'economic_data'
    ])
    def test_hypertable_exists(self, db_cursor, table_name):
        """Verify each time-series table is a hypertable."""
        assert db_helpers.is_hypertable(db_cursor, table_name), \
            f"Table '{table_name}' is not a hypertable"
    
    def test_hypertable_chunk_interval(self, db_cursor):
        """Verify hypertables have correct chunk interval (7 days)."""
        query = """
            SELECT hypertable_name, time_interval
            FROM timescaledb_information.dimensions
            WHERE hypertable_name IN ('market_data', 'forex_rates', 'bond_rates', 'economic_data')
            AND dimension_number = 1;
        """
        db_cursor.execute(query)
        results = db_cursor.fetchall()
        
        assert len(results) == 4, "Not all hypertables found"
        
        for row in results:
            # time_interval is a timedelta object
            interval = row[1]
            days = interval.total_seconds() / (60 * 60 * 24)
            assert abs(days - 7) < 0.1, \
                f"Hypertable '{row[0]}' has incorrect chunk interval: {days} days (expected 7)"


class TestIndexes:
    """Test that all required indexes exist."""
    
    def test_assets_indexes(self, db_cursor):
        """Verify assets table indexes."""
        indexes = db_helpers.get_table_indexes(db_cursor, 'assets')
        index_names = [idx['indexname'] for idx in indexes]
        
        required_indexes = [
            'idx_assets_symbol',
            'idx_assets_type',
            'idx_assets_type_symbol',
            'idx_assets_active'
        ]
        for idx in required_indexes:
            assert any(idx in name for name in index_names), \
                f"Index '{idx}' not found on assets table"
    
    def test_market_data_indexes(self, db_cursor):
        """Verify market_data table indexes."""
        indexes = db_helpers.get_table_indexes(db_cursor, 'market_data')
        index_names = [idx['indexname'] for idx in indexes]
        
        required_indexes = [
            'idx_market_data_asset_time',
            'idx_market_data_time',
            'idx_market_data_asset_id'
        ]
        for idx in required_indexes:
            assert any(idx in name for name in index_names), \
                f"Index '{idx}' not found on market_data table"
    
    def test_forex_rates_indexes(self, db_cursor):
        """Verify forex_rates table indexes."""
        indexes = db_helpers.get_table_indexes(db_cursor, 'forex_rates')
        index_names = [idx['indexname'] for idx in indexes]
        
        required_indexes = [
            'idx_forex_rates_asset_time',
            'idx_forex_rates_time'
        ]
        for idx in required_indexes:
            assert any(idx in name for name in index_names), \
                f"Index '{idx}' not found on forex_rates table"


class TestConstraints:
    """Test that all required constraints exist."""
    
    def test_assets_primary_key(self, db_cursor):
        """Verify assets table has primary key."""
        query = """
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'assets'
            AND constraint_type = 'PRIMARY KEY';
        """
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        assert result is not None, "Primary key not found on assets table"
    
    def test_assets_unique_symbol(self, db_cursor):
        """Verify assets table has unique constraint on symbol."""
        query = """
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'assets'
            AND constraint_type = 'UNIQUE'
            AND constraint_name LIKE '%symbol%';
        """
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        assert result is not None, "Unique constraint on symbol not found"
    
    def test_assets_check_constraint(self, db_cursor):
        """Verify assets table has check constraint on asset_type."""
        query = """
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_name IN (
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'assets'
                AND constraint_type = 'CHECK'
            );
        """
        db_cursor.execute(query)
        results = db_cursor.fetchall()
        assert len(results) > 0, "Check constraint on asset_type not found"
    
    def test_foreign_keys(self, db_cursor):
        """Verify foreign key constraints exist."""
        fks = db_helpers.get_foreign_keys(db_cursor, 'market_data')
        assert len(fks) > 0, "Foreign key from market_data to assets not found"
        
        # Check that foreign key references assets table
        asset_fk = [fk for fk in fks if fk['foreign_table_name'] == 'assets']
        assert len(asset_fk) > 0, "Foreign key to assets table not found"


class TestFunctions:
    """Test that all required functions exist."""
    
    @pytest.mark.parametrize("function_name", [
        'update_updated_at_column',
        'get_asset_by_symbol',
        'get_latest_market_data',
        'check_data_freshness',
        'get_collection_stats'
    ])
    def test_function_exists(self, db_cursor, function_name):
        """Verify each required function exists."""
        assert db_helpers.function_exists(db_cursor, function_name), \
            f"Function '{function_name}' does not exist"


class TestTriggers:
    """Test that all required triggers exist."""
    
    def test_update_assets_updated_at_trigger(self, db_cursor):
        """Verify trigger exists on assets table."""
        assert db_helpers.trigger_exists(db_cursor, 'update_assets_updated_at', 'assets'), \
            "Trigger 'update_assets_updated_at' not found on assets table"


class TestCompressionPolicies:
    """Test that compression policies are configured."""
    
    def test_compression_policies_exist(self, db_cursor):
        """Verify compression policies exist for all hypertables."""
        query = """
            SELECT hypertable_name, config
            FROM timescaledb_information.jobs
            WHERE proc_name = 'policy_compression'
            AND hypertable_name IN ('market_data', 'forex_rates', 'bond_rates', 'economic_data');
        """
        db_cursor.execute(query)
        results = db_cursor.fetchall()
        
        assert len(results) == 4, \
            f"Expected 4 compression policies, found {len(results)}"
        
        for row in results:
            # config is a dict (JSONB), compress_after is stored as an interval string
            config = row[1]
            if isinstance(config, dict):
                compress_after_str = config.get('compress_after', '')
            else:
                compress_after_str = str(config) if config else ''
            
            if compress_after_str:
                # Parse the interval (e.g., "30 days")
                import re
                days_match = re.search(r'(\d+)\s*days?', str(compress_after_str).lower())
                if days_match:
                    days = int(days_match.group(1))
                    assert abs(days - 30) < 0.1, \
                        f"Compression policy for '{row[0]}' has incorrect interval: {days} days (expected 30)"

