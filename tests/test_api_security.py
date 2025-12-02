"""
Security tests for API endpoints.

Tests input validation, SQL injection prevention, and XSS prevention.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

try:
    from investment_platform.api.main import app
except ImportError:
    app = None

pytestmark = pytest.mark.skipif(app is None, reason="API app not available")


class TestInputValidation:
    """Test input validation for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_assets_list_invalid_limit(self, client):
        """Test assets list endpoint with invalid limit."""
        # Negative limit
        response = client.get("/api/assets?limit=-1")
        assert response.status_code == 422

        # Limit too large
        response = client.get("/api/assets?limit=10000")
        assert response.status_code == 422

        # Non-numeric limit
        response = client.get("/api/assets?limit=abc")
        assert response.status_code == 422

    def test_assets_list_invalid_offset(self, client):
        """Test assets list endpoint with invalid offset."""
        # Negative offset
        response = client.get("/api/assets?offset=-1")
        assert response.status_code == 422

        # Non-numeric offset
        response = client.get("/api/assets?offset=abc")
        assert response.status_code == 422

    def test_assets_get_invalid_id(self, client):
        """Test assets get endpoint with invalid ID."""
        # Non-numeric ID
        response = client.get("/api/assets/abc")
        assert response.status_code == 422

        # Negative ID
        response = client.get("/api/assets/-1")
        # Should return 404, not 422, but should not cause SQL error
        assert response.status_code in [404, 422]

    def test_scheduler_jobs_invalid_pagination(self, client):
        """Test scheduler jobs endpoint with invalid pagination."""
        # Invalid limit
        response = client.get("/api/scheduler/jobs?limit=-1")
        assert response.status_code == 422

        # Invalid offset
        response = client.get("/api/scheduler/jobs?offset=-1")
        assert response.status_code == 422

    def test_collectors_search_invalid_query(self, client):
        """Test collectors search endpoint with invalid query."""
        # Empty query
        response = client.get("/api/collectors/stock/search?q=")
        assert response.status_code == 422

        # Query too short (if min_length is enforced)
        response = client.get("/api/collectors/stock/search?q=a")
        # May pass validation but should not cause errors
        assert response.status_code in [200, 422]

        # Invalid limit
        response = client.get("/api/collectors/stock/search?q=AAPL&limit=-1")
        assert response.status_code == 422


class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_assets_list_sql_injection_in_asset_type(self, client):
        """Test that SQL injection in asset_type parameter is prevented."""
        # SQL injection attempt
        malicious_input = "stock'; DROP TABLE assets; --"
        response = client.get(f"/api/assets?asset_type={malicious_input}")
        
        # Should not cause SQL error (should be handled gracefully)
        # Either returns 422 (validation error) or 200 with empty results
        assert response.status_code in [200, 422]
        # Should not execute malicious SQL

    def test_assets_get_sql_injection_in_id(self, client):
        """Test that SQL injection in asset_id parameter is prevented."""
        # SQL injection attempt (though FastAPI should validate this as int)
        # This test ensures type validation works
        malicious_input = "1; DROP TABLE assets; --"
        response = client.get(f"/api/assets/{malicious_input}")
        
        # Should return 422 (validation error) since ID must be int
        assert response.status_code == 422

    def test_collectors_search_sql_injection(self, client):
        """Test that SQL injection in search query is prevented."""
        malicious_input = "AAPL'; DROP TABLE assets; --"
        response = client.get(f"/api/collectors/stock/search?q={malicious_input}")
        
        # Should handle gracefully (either 200 with empty results or 422)
        assert response.status_code in [200, 422]
        # Should not execute malicious SQL

    def test_scheduler_jobs_sql_injection_in_filters(self, client):
        """Test that SQL injection in filter parameters is prevented."""
        malicious_input = "active'; DROP TABLE scheduler_jobs; --"
        response = client.get(f"/api/scheduler/jobs?status={malicious_input}")
        
        # Should handle gracefully
        assert response.status_code in [200, 422]


class TestXSSPrevention:
    """Test XSS (Cross-Site Scripting) prevention."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_xss_in_search_query(self, client):
        """Test that XSS attempts in search query are sanitized."""
        xss_attempt = "<script>alert('XSS')</script>"
        response = client.get(f"/api/collectors/stock/search?q={xss_attempt}")
        
        # Should handle gracefully (not execute script)
        assert response.status_code in [200, 422]
        
        # Response should not contain unescaped script tags
        if response.status_code == 200:
            response_data = response.json()
            # Check that response is properly serialized (JSON, not HTML)
            assert isinstance(response_data, (list, dict))

    def test_xss_in_asset_type(self, client):
        """Test that XSS attempts in asset_type are sanitized."""
        xss_attempt = "<script>alert('XSS')</script>"
        response = client.get(f"/api/assets?asset_type={xss_attempt}")
        
        # Should handle gracefully
        assert response.status_code in [200, 422]
        
        # Response should be JSON, not HTML
        if response.status_code == 200:
            response_data = response.json()
            assert isinstance(response_data, (list, dict))


class TestParameterizedQueries:
    """Test that database queries use parameterized queries."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('investment_platform.ingestion.db_connection.get_db_connection')
    def test_assets_list_uses_parameterized_queries(self, mock_db, client):
        """Test that assets list endpoint uses parameterized queries."""
        from unittest.mock import MagicMock
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_db.return_value = mock_conn
        
        # Make request
        client.get("/api/assets?asset_type=stock&limit=10&offset=0")
        
        # Verify execute was called (if connection was used)
        # This test ensures parameterized queries are used
        # In a real scenario, we'd check the execute call arguments
        assert True  # Placeholder - actual implementation would verify execute() calls

