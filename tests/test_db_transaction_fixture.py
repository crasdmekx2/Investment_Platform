"""
Tests to verify db_transaction fixture works correctly with transaction control.
"""

import pytest
from tests.utils import db_helpers


class TestDbTransactionFixture:
    """Test that db_transaction fixture properly isolates tests with transactions."""

    def test_transaction_rollback_works(self, db_transaction):
        """Test that data inserted in a transaction is rolled back."""
        cursor = db_transaction.cursor()

        # Insert test data
        asset_id = db_helpers.insert_sample_asset(
            cursor,
            symbol="TRANSACTION_TEST",
            asset_type="stock",
            name="Transaction Test",
        )

        # Verify data exists within transaction
        cursor.execute("SELECT asset_id FROM assets WHERE symbol = 'TRANSACTION_TEST'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == asset_id

        cursor.close()
        # Transaction should rollback when fixture yields

    def test_transaction_isolation(self, db_transaction):
        """Test that transactions from different tests are isolated."""
        cursor = db_transaction.cursor()

        # This test should not see data from previous test
        cursor.execute("SELECT asset_id FROM assets WHERE symbol = 'TRANSACTION_TEST'")
        result = cursor.fetchone()
        # Should be None because previous test's transaction was rolled back
        assert result is None

        cursor.close()

    def test_transaction_commit_manual(self, db_transaction):
        """Test that manual commit works within transaction."""
        cursor = db_transaction.cursor()

        # Insert data
        asset_id = db_helpers.insert_sample_asset(
            cursor,
            symbol="MANUAL_COMMIT_TEST",
            asset_type="stock",
            name="Manual Commit Test",
        )

        # Manually commit
        db_transaction.commit()

        # Verify data exists
        cursor.execute("SELECT asset_id FROM assets WHERE symbol = 'MANUAL_COMMIT_TEST'")
        result = cursor.fetchone()
        assert result is not None

        # Cleanup manually since we committed
        cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))
        db_transaction.commit()

        cursor.close()
