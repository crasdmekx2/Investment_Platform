"""
Integration tests with sample data.
"""

import pytest
from datetime import datetime, timedelta
from tests.utils import db_helpers
from tests.fixtures import sample_data


class TestSampleAssets:
    """Test inserting and querying sample assets."""

    def test_insert_stock_asset(self, db_cursor, db_connection):
        """Test inserting a sample stock asset."""
        import uuid

        stock_data = sample_data.get_sample_stock_asset()
        stock_data = stock_data.copy()
        stock_data["symbol"] = f"{stock_data['symbol']}_{uuid.uuid4().hex[:8]}"
        asset_id = db_helpers.insert_sample_asset(db_cursor, **stock_data)
        db_connection.commit()

        assert asset_id > 0, "Asset ID should be positive"

        # Verify asset was inserted
        db_cursor.execute("SELECT * FROM assets WHERE asset_id = %s;", (asset_id,))
        result = db_cursor.fetchone()
        assert result is not None, "Asset should be inserted"
        assert result[1] == stock_data["symbol"], "Symbol should match"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

    def test_insert_multiple_asset_types(self, db_cursor, db_connection):
        """Test inserting multiple asset types."""
        import uuid

        unique_suffix = uuid.uuid4().hex[:8]

        assets = [
            sample_data.get_sample_stock_asset(),
            sample_data.get_sample_forex_asset(),
            sample_data.get_sample_crypto_asset(),
            sample_data.get_sample_bond_asset(),
            sample_data.get_sample_economic_indicator_asset(),
        ]

        asset_ids = []
        for asset_data in assets:
            # Make symbols unique
            asset_data = asset_data.copy()
            asset_data["symbol"] = f"{asset_data['symbol']}_{unique_suffix}"
            asset_id = db_helpers.insert_sample_asset(db_cursor, **asset_data)
            asset_ids.append(asset_id)

        db_connection.commit()

        # Verify all assets were inserted
        assert len(asset_ids) == 5, "Should insert 5 assets"
        assert all(aid > 0 for aid in asset_ids), "All asset IDs should be positive"

        # Cleanup
        for asset_id in asset_ids:
            db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()


class TestSampleTimeSeriesData:
    """Test inserting and querying sample time-series data."""

    def test_insert_market_data(self, db_cursor, db_connection):
        """Test inserting sample market data."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, "MARKET_DATA_TEST", "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        data_points = sample_data.get_sample_market_data_points(count=5)

        for point in data_points:
            db_cursor.execute(
                """
                INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
                (
                    point["time"],
                    asset_id,
                    point["open"],
                    point["high"],
                    point["low"],
                    point["close"],
                    point["volume"],
                ),
            )
        db_connection.commit()

        # Verify data was inserted
        db_cursor.execute("SELECT COUNT(*) FROM market_data WHERE asset_id = %s;", (asset_id,))
        count = db_cursor.fetchone()[0]
        assert count == 5, "Should insert 5 market data points"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

    def test_insert_forex_rates(self, db_cursor, db_connection):
        """Test inserting sample forex rates."""
        import uuid

        unique_symbol = f"EURUSD_SAMPLE_{uuid.uuid4().hex[:8]}"
        asset_id = db_helpers.insert_sample_asset(
            db_cursor,
            unique_symbol,
            "forex",
            "EUR/USD",
            "Test",
            base_currency="EUR",
            quote_currency="USD",
        )
        db_connection.commit()

        data_points = sample_data.get_sample_forex_rates(count=5)

        for point in data_points:
            db_cursor.execute(
                """
                INSERT INTO forex_rates (time, asset_id, rate)
                VALUES (%s, %s, %s);
            """,
                (point["time"], asset_id, point["rate"]),
            )
        db_connection.commit()

        # Verify data was inserted
        db_cursor.execute("SELECT COUNT(*) FROM forex_rates WHERE asset_id = %s;", (asset_id,))
        count = db_cursor.fetchone()[0]
        assert count == 5, "Should insert 5 forex rate points"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

    def test_insert_bond_rates(self, db_cursor, db_connection):
        """Test inserting sample bond rates."""
        import uuid

        unique_symbol = f"BOND_SAMPLE_{uuid.uuid4().hex[:8]}"
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, "bond", "Test Bond", "Test"
        )
        db_connection.commit()

        data_points = sample_data.get_sample_bond_rates(count=5)

        for point in data_points:
            db_cursor.execute(
                """
                INSERT INTO bond_rates (time, asset_id, rate)
                VALUES (%s, %s, %s);
            """,
                (point["time"], asset_id, point["rate"]),
            )
        db_connection.commit()

        # Verify data was inserted
        db_cursor.execute("SELECT COUNT(*) FROM bond_rates WHERE asset_id = %s;", (asset_id,))
        count = db_cursor.fetchone()[0]
        assert count == 5, "Should insert 5 bond rate points"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

    def test_insert_economic_data(self, db_cursor, db_connection):
        """Test inserting sample economic data."""
        import uuid

        unique_symbol = f"ECON_SAMPLE_{uuid.uuid4().hex[:8]}"
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, "economic_indicator", "Test Indicator", "Test"
        )
        db_connection.commit()

        data_points = sample_data.get_sample_economic_data(count=5)

        for point in data_points:
            db_cursor.execute(
                """
                INSERT INTO economic_data (time, asset_id, value)
                VALUES (%s, %s, %s);
            """,
                (point["time"], asset_id, point["value"]),
            )
        db_connection.commit()

        # Verify data was inserted
        db_cursor.execute("SELECT COUNT(*) FROM economic_data WHERE asset_id = %s;", (asset_id,))
        count = db_cursor.fetchone()[0]
        assert count == 5, "Should insert 5 economic data points"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()


class TestDataQueries:
    """Test querying sample data."""

    def test_join_assets_and_market_data(self, db_cursor, db_connection):
        """Test joining assets and market_data tables."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, "JOIN_TEST", "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Insert market data
        data_points = sample_data.get_sample_market_data_points(count=3)
        for point in data_points:
            db_cursor.execute(
                """
                INSERT INTO market_data (time, asset_id, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
                (
                    point["time"],
                    asset_id,
                    point["open"],
                    point["high"],
                    point["low"],
                    point["close"],
                    point["volume"],
                ),
            )
        db_connection.commit()

        # Query with join
        query = """
            SELECT 
                a.symbol,
                a.name,
                md.time,
                md.close,
                md.volume
            FROM assets a
            JOIN market_data md ON a.asset_id = md.asset_id
            WHERE a.asset_id = %s
            ORDER BY md.time DESC;
        """
        db_cursor.execute(query, (asset_id,))
        results = db_cursor.fetchall()

        assert len(results) == 3, "Should return 3 joined rows"
        assert results[0][0] == "JOIN_TEST", "Should return correct symbol"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

    def test_data_freshness_with_sample_data(self, db_cursor, db_connection):
        """Test data freshness check with sample data."""
        import uuid

        unique_symbol = f"FRESHNESS_SAMPLE_{uuid.uuid4().hex[:8]}"
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Insert recent data
        db_cursor.execute(
            """
            INSERT INTO market_data (time, asset_id, open, high, low, close)
            VALUES (%s, %s, 100.0, 110.0, 95.0, 105.0);
        """,
            (datetime.now() - timedelta(hours=1), asset_id),
        )
        db_connection.commit()

        # Check freshness
        db_cursor.execute("SELECT * FROM check_data_freshness(%s, 'market_data');", (asset_id,))
        result = db_cursor.fetchone()

        assert result is not None, "Should return freshness data"
        assert result[4] is False, "Data should not be stale"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()


class TestDataCollectionLog:
    """Test data collection log functionality."""

    def test_insert_collection_log(self, db_cursor, db_connection):
        """Test inserting data collection log entries."""
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, "LOG_TEST", "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        log_entry = sample_data.get_sample_collection_log_entry()

        db_cursor.execute(
            """
            INSERT INTO data_collection_log 
            (asset_id, collector_type, start_date, end_date, records_collected, status, execution_time_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING log_id;
        """,
            (
                asset_id,
                log_entry["collector_type"],
                log_entry["start_date"],
                log_entry["end_date"],
                log_entry["records_collected"],
                log_entry["status"],
                log_entry["execution_time_ms"],
            ),
        )
        log_id = db_cursor.fetchone()[0]
        db_connection.commit()

        assert log_id > 0, "Log ID should be positive"

        # Verify log entry
        db_cursor.execute("SELECT * FROM data_collection_log WHERE log_id = %s;", (log_id,))
        result = db_cursor.fetchone()
        assert result is not None, "Log entry should be inserted"
        assert result[2] == log_entry["collector_type"], "Collector type should match"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()

    def test_collection_stats_with_sample_data(self, db_cursor, db_connection):
        """Test collection stats function with sample data."""
        import uuid

        unique_symbol = f"STATS_SAMPLE_{uuid.uuid4().hex[:8]}"
        asset_id = db_helpers.insert_sample_asset(
            db_cursor, unique_symbol, "stock", "Test Stock", "Test"
        )
        db_connection.commit()

        # Insert multiple log entries
        now = datetime.now()
        for i in range(3):
            db_cursor.execute(
                """
                INSERT INTO data_collection_log 
                (asset_id, collector_type, start_date, end_date, records_collected, status, execution_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
                (
                    asset_id,
                    "TestCollector",
                    now - timedelta(days=i),
                    now - timedelta(days=i) + timedelta(hours=1),
                    100 + i * 10,
                    "success" if i < 2 else "failed",
                    1000 + i * 100,
                ),
            )
        db_connection.commit()

        # Get stats for a very short time window to avoid counting other test data
        db_cursor.execute("SELECT * FROM get_collection_stats(1);")
        results = db_cursor.fetchall()

        test_collector_stats = [r for r in results if r[0] == "TestCollector"]
        # May find more than 3 if other tests ran recently, so just verify the stats exist
        assert len(test_collector_stats) >= 1, "Should find TestCollector stats"
        # Verify the stats structure is correct - should have at least 3 runs
        assert (
            test_collector_stats[0][1] >= 3
        ), f"Should have at least 3 total runs, got {test_collector_stats[0][1]}"

        # Cleanup
        db_cursor.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
        db_connection.commit()
