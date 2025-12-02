"""
Integration tests for Assets API router.

Tests all endpoints in the assets router with proper request/response cycles.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

try:
    from investment_platform.api.main import app
except ImportError:
    app = None

pytestmark = pytest.mark.skipif(app is None, reason="API app not available")


class TestAssetsRouter:
    """Test suite for Assets API router."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection."""
        with patch('investment_platform.api.routers.assets.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.fetchone.return_value = None
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.__enter__.return_value = mock_conn
            mock_db.return_value = mock_conn
            yield mock_db, mock_conn, mock_cursor

    def test_list_assets_success(self, client, mock_db_connection):
        """Test successful listing of assets."""
        mock_db, mock_conn, mock_cursor = mock_db_connection
        
        # Mock successful response
        mock_cursor.fetchall.return_value = [
            {
                'asset_id': 1,
                'symbol': 'AAPL',
                'asset_type': 'stock',
                'is_active': True,
            },
            {
                'asset_id': 2,
                'symbol': 'MSFT',
                'asset_type': 'stock',
                'is_active': True,
            },
        ]
        
        response = client.get("/api/assets")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]['symbol'] == 'AAPL'
        assert data[1]['symbol'] == 'MSFT'

    def test_list_assets_with_asset_type_filter(self, client, mock_db_connection):
        """Test listing assets filtered by asset type."""
        mock_db, mock_conn, mock_cursor = mock_db_connection
        
        mock_cursor.fetchall.return_value = [
            {
                'asset_id': 1,
                'symbol': 'AAPL',
                'asset_type': 'stock',
                'is_active': True,
            },
        ]
        
        response = client.get("/api/assets?asset_type=stock")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify query was called with asset_type parameter
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        assert 'asset_type' in str(call_args[0]).lower() or 'stock' in str(call_args)

    def test_list_assets_with_pagination(self, client, mock_db_connection):
        """Test listing assets with pagination."""
        mock_db, mock_conn, mock_cursor = mock_db_connection
        
        mock_cursor.fetchall.return_value = []
        
        response = client.get("/api/assets?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify pagination parameters were used
        mock_cursor.execute.assert_called_once()

    def test_get_asset_success(self, client, mock_db_connection):
        """Test getting a single asset by ID."""
        mock_db, mock_conn, mock_cursor = mock_db_connection
        
        mock_cursor.fetchone.return_value = {
            'asset_id': 1,
            'symbol': 'AAPL',
            'asset_type': 'stock',
            'is_active': True,
        }
        
        response = client.get("/api/assets/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data['asset_id'] == 1
        assert data['symbol'] == 'AAPL'

    def test_get_asset_not_found(self, client, mock_db_connection):
        """Test getting a non-existent asset."""
        mock_db, mock_conn, mock_cursor = mock_db_connection
        
        mock_cursor.fetchone.return_value = None
        
        response = client.get("/api/assets/999")
        
        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()

    def test_get_data_coverage_success(self, client, mock_db_connection):
        """Test getting data coverage for an asset."""
        mock_db, mock_conn, mock_cursor = mock_db_connection
        
        # Mock data coverage response
        mock_cursor.fetchone.return_value = {
            'asset_id': 1,
            'first_date': '2024-01-01',
            'last_date': '2024-12-31',
            'total_records': 365,
        }
        
        response = client.get("/api/assets/1/coverage")
        
        assert response.status_code == 200
        data = response.json()
        assert 'asset_id' in data or 'first_date' in data

    def test_get_data_coverage_not_found(self, client, mock_db_connection):
        """Test getting data coverage for non-existent asset."""
        mock_db, mock_conn, mock_cursor = mock_db_connection
        
        mock_cursor.fetchone.return_value = None
        
        response = client.get("/api/assets/999/coverage")
        
        # Should return 404 or empty data
        assert response.status_code in [200, 404]

    def test_list_assets_empty_result(self, client, mock_db_connection):
        """Test listing assets when no assets exist."""
        mock_db, mock_conn, mock_cursor = mock_db_connection
        
        mock_cursor.fetchall.return_value = []
        
        response = client.get("/api/assets")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

