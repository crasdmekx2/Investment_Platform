"""
Integration tests for Collectors API router.

Tests all endpoints in the collectors router with proper request/response cycles.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

try:
    from investment_platform.api.main import app
except ImportError:
    app = None

pytestmark = pytest.mark.skipif(app is None, reason="API app not available")


class TestCollectorsRouter:
    """Test suite for Collectors API router."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_collector_service(self):
        """Mock collector service."""
        with patch('investment_platform.api.routers.collectors.collector_svc') as mock_svc:
            yield mock_svc

    def test_get_collector_metadata_success(self, client, mock_collector_service):
        """Test getting collector metadata."""
        mock_collector_service.get_collector_metadata.return_value = {
            'stock': {
                'name': 'Stock Collector',
                'supported_symbols': ['AAPL', 'MSFT'],
            },
            'crypto': {
                'name': 'Crypto Collector',
                'supported_symbols': ['BTC', 'ETH'],
            },
        }
        
        response = client.get("/api/collectors/metadata")
        
        assert response.status_code == 200
        data = response.json()
        assert 'stock' in data
        assert 'crypto' in data

    def test_get_collector_metadata_error(self, client, mock_collector_service):
        """Test getting collector metadata with service error."""
        mock_collector_service.get_collector_metadata.side_effect = Exception("Service error")
        
        response = client.get("/api/collectors/metadata")
        
        assert response.status_code == 500
        assert 'error' in response.json()['detail'].lower()

    def test_get_collector_options_success(self, client, mock_collector_service):
        """Test getting collector options for an asset type."""
        mock_collector_service.get_collector_options.return_value = {
            'interval': ['1m', '5m', '1h', '1d'],
            'supported_symbols': ['AAPL', 'MSFT', 'GOOGL'],
        }
        
        response = client.get("/api/collectors/stock/options")
        
        assert response.status_code == 200
        data = response.json()
        assert 'interval' in data or 'supported_symbols' in data

    def test_get_collector_options_invalid_asset_type(self, client, mock_collector_service):
        """Test getting collector options with invalid asset type."""
        mock_collector_service.get_collector_options.side_effect = ValueError("Invalid asset type")
        
        response = client.get("/api/collectors/invalid_type/options")
        
        assert response.status_code == 400
        assert 'invalid' in response.json()['detail'].lower()

    def test_get_collector_options_error(self, client, mock_collector_service):
        """Test getting collector options with service error."""
        mock_collector_service.get_collector_options.side_effect = Exception("Service error")
        
        response = client.get("/api/collectors/stock/options")
        
        assert response.status_code == 500

    def test_search_assets_success(self, client, mock_collector_service):
        """Test searching for assets."""
        mock_collector_service.search_assets.return_value = [
            {'symbol': 'AAPL', 'name': 'Apple Inc.'},
            {'symbol': 'AAPL2', 'name': 'Another AAPL'},
        ]
        
        response = client.get("/api/collectors/stock/search?q=AAPL")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]['symbol'] == 'AAPL'

    def test_search_assets_with_limit(self, client, mock_collector_service):
        """Test searching for assets with limit."""
        mock_collector_service.search_assets.return_value = [
            {'symbol': 'AAPL', 'name': 'Apple Inc.'},
        ]
        
        response = client.get("/api/collectors/stock/search?q=AAPL&limit=1")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify limit was passed to service
        mock_collector_service.search_assets.assert_called_once()
        call_kwargs = mock_collector_service.search_assets.call_args[1]
        assert call_kwargs.get('limit') == 1

    def test_search_assets_empty_query(self, client, mock_collector_service):
        """Test searching with empty query."""
        response = client.get("/api/collectors/stock/search?q=")
        
        # Should return 422 (validation error) due to min_length=1
        assert response.status_code == 422

    def test_search_assets_error(self, client, mock_collector_service):
        """Test searching for assets with service error."""
        mock_collector_service.search_assets.side_effect = Exception("Search error")
        
        response = client.get("/api/collectors/stock/search?q=AAPL")
        
        assert response.status_code == 500

    def test_validate_collection_params_success(self, client, mock_collector_service):
        """Test validating collection parameters."""
        mock_collector_service.validate_collection_params.return_value = {
            'valid': True,
            'errors': [],
        }
        
        request_data = {
            'asset_type': 'stock',
            'symbol': 'AAPL',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        }
        
        response = client.post("/api/collectors/validate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True

    def test_validate_collection_params_invalid(self, client, mock_collector_service):
        """Test validating invalid collection parameters."""
        mock_collector_service.validate_collection_params.return_value = {
            'valid': False,
            'errors': ['Invalid symbol', 'Date range invalid'],
        }
        
        request_data = {
            'asset_type': 'stock',
            'symbol': 'INVALID',
            'start_date': '2024-12-31',
            'end_date': '2024-01-01',  # End before start
        }
        
        response = client.post("/api/collectors/validate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is False
        assert len(data['errors']) > 0

    def test_validate_collection_params_error(self, client, mock_collector_service):
        """Test validating collection parameters with service error."""
        mock_collector_service.validate_collection_params.side_effect = Exception("Validation error")
        
        request_data = {
            'asset_type': 'stock',
            'symbol': 'AAPL',
        }
        
        response = client.post("/api/collectors/validate", json=request_data)
        
        assert response.status_code == 500

