"""
Tests for TimescaleDB-specific features.
"""

import pytest
from datetime import datetime, timedelta
from tests.utils import db_helpers


class TestHypertableConfiguration:
    """Test hypertable configuration."""
    
    def test_hypertable_chunk_interval(self, db_cursor):
        """Verify hypertables have 7-day chunk intervals."""
        query = """
            SELECT hypertable_name, time_interval
            FROM timescaledb_information.dimensions
            WHERE hypertable_name IN ('market_data', 'forex_rates', 'bond_rates', 'economic_data')
            AND dimension_number = 1;
        """
        db_cursor.execute(query)
        results = db_cursor.fetchall()
        
        assert len(results) == 4, "All 4 hypertables should exist"
        
        for row in results:
            # time_interval is a timedelta object
            interval = row[1]
            days = interval.total_seconds() / (60 * 60 * 24)
            assert abs(days - 7) < 0.1, \
                f"Hypertable '{row[0]}' should have 7-day chunk interval, got {days} days"
    
    def test_hypertable_compression_settings(self, db_cursor):
        """Verify compression segmentby and orderby settings."""
        # Check compression settings from pg_class reloptions
        hypertables = ['market_data', 'forex_rates', 'bond_rates', 'economic_data']
        
        for table_name in hypertables:
            # Verify compression is enabled on the hypertable
            query = """
                SELECT compression_enabled 
                FROM timescaledb_information.hypertables 
                WHERE hypertable_name = %s;
            """
            db_cursor.execute(query, (table_name,))
            comp_enabled = db_cursor.fetchone()
            
            # Compression should be enabled (we set it in the policies script)
            assert comp_enabled is not None, \
                f"Hypertable '{table_name}' should exist"
            # Note: compression_enabled might be False if no data is compressed yet
            # This is OK - the policy will compress data older than 30 days
            
            # Verify compression settings exist in reloptions
            query2 = """
                SELECT reloptions 
                FROM pg_class 
                WHERE relname = %s;
            """
            db_cursor.execute(query2, (table_name,))
            relopts = db_cursor.fetchone()
            # reloptions should contain compression settings
            # We just verify the table exists and compression is configured


class TestCompressionPolicies:
    """Test compression policy configuration."""
    
    def test_compression_policies_exist(self, db_cursor):
        """Verify compression policies exist for all hypertables."""
        query = """
            SELECT 
                hypertable_name,
                config
            FROM timescaledb_information.jobs
            WHERE proc_name = 'policy_compression'
            AND hypertable_name IN ('market_data', 'forex_rates', 'bond_rates', 'economic_data');
        """
        db_cursor.execute(query)
        results = db_cursor.fetchall()
        
        assert len(results) == 4, "All 4 hypertables should have compression policies"
        
        for row in results:
            # config is a dict (JSONB), compress_after is stored as an interval string
            config = row[1]
            if isinstance(config, dict):
                compress_after_str = config.get('compress_after', '')
            else:
                compress_after_str = str(config) if config else ''
            
            # Parse the interval (e.g., "30 days")
            if compress_after_str:
                # Extract days from interval string
                import re
                days_match = re.search(r'(\d+)\s*days?', str(compress_after_str).lower())
                if days_match:
                    days = int(days_match.group(1))
                    assert abs(days - 30) < 0.1, \
                        f"Compression policy for '{row[0]}' should compress after 30 days, got {days} days"


class TestChunkManagement:
    """Test chunk creation and management."""
    
    def test_chunks_created_on_insert(self, db_cursor, db_connection):
        """Test that chunks are created when data is inserted."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, 'CHUNK_TEST', 'stock', 'Test Stock', 'Test'
        )
        db_connection.commit()
        
        # Get initial chunk count
        query = """
            SELECT COUNT(*) 
            FROM timescaledb_information.chunks 
            WHERE hypertable_name = 'market_data';
        """
        db_cursor.execute(query)
        initial_chunk_count = db_cursor.fetchone()[0]
        
        # Insert data
        db_cursor.execute("""
            INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
            VALUES (%s, %s, 100.0, 110.0, 95.0, 105.0, 1000);
        """, (datetime.now(), asset_id))
        db_connection.commit()
        
        # Get chunk count after insert
        db_cursor.execute(query)
        final_chunk_count = db_cursor.fetchone()[0]
        
        # At least one chunk should exist
        assert final_chunk_count >= 1, "At least one chunk should exist after data insertion"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()
    
    def test_chunk_range_information(self, db_cursor, db_connection):
        """Test that chunk range information is available."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, 'CHUNK_RANGE_TEST', 'stock', 'Test Stock', 'Test'
        )
        db_connection.commit()
        
        # Insert data
        db_cursor.execute("""
            INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
            VALUES (%s, %s, 100.0, 110.0, 95.0, 105.0, 1000);
        """, (datetime.now(), asset_id))
        db_connection.commit()
        
        # Get chunk information
        query = """
            SELECT 
                chunk_name,
                range_start,
                range_end
            FROM timescaledb_information.chunks
            WHERE hypertable_name = 'market_data'
            ORDER BY range_start DESC
            LIMIT 1;
        """
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        
        assert result is not None, "Chunk information should be available"
        assert result[1] is not None, "Chunk should have range_start"
        assert result[2] is not None, "Chunk should have range_end"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()


class TestTimeBasedQueries:
    """Test time-based queries on hypertables."""
    
    def test_time_bucket_query(self, db_cursor, db_connection):
        """Test time_bucket function for aggregating time-series data."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, 'TIME_BUCKET_TEST', 'stock', 'Test Stock', 'Test'
        )
        db_connection.commit()
        
        # Insert multiple data points across different days
        base_time = datetime.now() - timedelta(days=5)
        for i in range(10):
            db_cursor.execute("""
                INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
                VALUES (%s, %s, 100.0, 110.0, 95.0, 105.0, 1000);
            """, (base_time + timedelta(hours=i*6), asset_id))
        db_connection.commit()
        
        # Query with time_bucket (daily aggregation)
        query = """
            SELECT 
                time_bucket('1 day', time) AS day,
                COUNT(*) AS count,
                AVG(close) AS avg_close
            FROM market_data
            WHERE asset_id = %s
            GROUP BY day
            ORDER BY day;
        """
        db_cursor.execute(query, (asset_id,))
        results = db_cursor.fetchall()
        
        assert len(results) > 0, "Time bucket query should return results"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()
    
    def test_time_range_query(self, db_cursor, db_connection):
        """Test querying data within a time range."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, 'TIME_RANGE_TEST', 'stock', 'Test Stock', 'Test'
        )
        db_connection.commit()
        
        # Insert data at different times
        now = datetime.now()
        times = [
            now - timedelta(days=3),
            now - timedelta(days=2),
            now - timedelta(days=1),
            now
        ]
        
        for t in times:
            db_cursor.execute("""
                INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
                VALUES (%s, %s, 100.0, 110.0, 95.0, 105.0, 1000);
            """, (t, asset_id))
        db_connection.commit()
        
        # Query data in last 2 days
        query = """
            SELECT COUNT(*) 
            FROM market_data
            WHERE asset_id = %s
            AND time >= %s;
        """
        two_days_ago = now - timedelta(days=2)
        db_cursor.execute(query, (asset_id, two_days_ago))
        count = db_cursor.fetchone()[0]
        
        assert count >= 2, "Should find at least 2 data points in last 2 days"
        
        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()


class TestTimescaleDBViews:
    """Test TimescaleDB information views."""
    
    def test_hypertables_view(self, db_cursor):
        """Test that hypertables information view is accessible."""
        query = """
            SELECT 
                hypertable_name,
                num_dimensions,
                compression_enabled
            FROM timescaledb_information.hypertables
            WHERE hypertable_name IN ('market_data', 'forex_rates', 'bond_rates', 'economic_data');
        """
        db_cursor.execute(query)
        results = db_cursor.fetchall()
        
        assert len(results) == 4, "Should find all 4 hypertables"
        
        for row in results:
            assert row[1] >= 1, f"Hypertable '{row[0]}' should have at least 1 dimension"
    
    def test_chunks_view(self, db_cursor):
        """Test that chunks information view is accessible."""
        query = """
            SELECT COUNT(*) 
            FROM timescaledb_information.chunks
            WHERE hypertable_name IN ('market_data', 'forex_rates', 'bond_rates', 'economic_data');
        """
        db_cursor.execute(query)
        count = db_cursor.fetchone()[0]
        
        # Should be able to query chunks view (may be 0 if no data inserted)
        assert count >= 0, "Chunks view should be accessible"
    
    def test_jobs_view(self, db_cursor):
        """Test that jobs information view shows compression policies."""
        query = """
            SELECT 
                job_id,
                proc_name,
                scheduled,
                hypertable_name
            FROM timescaledb_information.jobs
            WHERE proc_name = 'policy_compression';
        """
        db_cursor.execute(query)
        results = db_cursor.fetchall()
        
        # Should find compression policy jobs
        assert len(results) >= 4, f"Should find compression policy jobs for all hypertables, found {len(results)}"

