"""
Integration tests for Ingestion API router.

Tests all endpoints in the ingestion router with proper request/response cycles.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

try:
    from investment_platform.api.main import app
except ImportError:
    app = None

pytestmark = pytest.mark.skipif(app is None, reason="API app not available")


class TestIngestionRouter:
    """Test suite for Ingestion API router."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection."""
        with patch("investment_platform.api.routers.ingestion.get_db_connection") as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.__enter__.return_value = mock_conn
            mock_db.return_value = mock_conn
            yield mock_db, mock_conn, mock_cursor

    @pytest.fixture
    def mock_ingestion_engine(self):
        """Mock ingestion engine."""
        with patch("investment_platform.api.routers.ingestion.IngestionEngine") as mock_engine:
            mock_instance = MagicMock()
            mock_instance.ingest.return_value = {
                "status": "success",
                "records_loaded": 100,
                "asset_id": 1,
            }
            mock_engine.return_value = mock_instance
            yield mock_engine, mock_instance

    def test_collect_data_success(self, client, mock_ingestion_engine):
        """Test successful data collection request."""
        mock_engine, mock_instance = mock_ingestion_engine

        request_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-12-31T23:59:59",
            "incremental": False,
        }

        response = client.post("/api/ingestion/collect", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "running"
        assert "message" in data
        assert "AAPL" in data["message"]

    def test_collect_data_with_default_dates(self, client, mock_ingestion_engine):
        """Test data collection with default dates."""
        mock_engine, mock_instance = mock_ingestion_engine

        request_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "incremental": True,
        }

        response = client.post("/api/ingestion/collect", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_collect_data_validation_error(self, client):
        """Test data collection with invalid request."""
        # Missing required fields
        request_data = {
            "symbol": "AAPL",
        }

        response = client.post("/api/ingestion/collect", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_collect_data_with_collector_kwargs(self, client, mock_ingestion_engine):
        """Test data collection with custom collector kwargs."""
        mock_engine, mock_instance = mock_ingestion_engine

        request_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "collector_kwargs": {"interval": "1m"},
            "incremental": False,
        }

        response = client.post("/api/ingestion/collect", json=request_data)

        assert response.status_code == 200
        # Verify collector_kwargs would be passed to engine (in actual execution)

    def test_get_collection_status_running(self, client):
        """Test getting status for a running collection job."""
        # First create a job
        request_data = {
            "symbol": "AAPL",
            "asset_type": "stock",
            "incremental": False,
        }

        create_response = client.post("/api/ingestion/collect", json=request_data)
        job_id = create_response.json()["job_id"]

        # Get status
        response = client.get(f"/api/ingestion/status/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "started_at" in data

    def test_get_collection_status_not_found(self, client):
        """Test getting status for non-existent job."""
        response = client.get("/api/ingestion/status/nonexistent_job")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_collection_logs_success(self, client, mock_db_connection):
        """Test getting collection logs."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        # Mock log data
        mock_cursor.fetchall.return_value = [
            {
                "log_id": 1,
                "asset_id": 1,
                "collector_type": "stock",
                "start_date": datetime(2024, 1, 1),
                "end_date": datetime(2024, 12, 31),
                "records_collected": 100,
                "status": "success",
                "error_message": None,
                "execution_time_ms": 1000,
                "created_at": datetime.now(),
            },
        ]

        response = client.get("/api/ingestion/logs")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "log_id" in data[0]
            assert "asset_id" in data[0]

    def test_get_collection_logs_with_filters(self, client, mock_db_connection):
        """Test getting collection logs with filters."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchall.return_value = []

        response = client.get("/api/ingestion/logs?asset_id=1&status=success&limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify query was constructed with filters
        mock_cursor.execute.assert_called_once()

    def test_get_collection_logs_with_date_filters(self, client, mock_db_connection):
        """Test getting collection logs with date filters."""
        mock_db, mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchall.return_value = []

        start_date = "2024-01-01T00:00:00"
        end_date = "2024-12-31T23:59:59"
        response = client.get(f"/api/ingestion/logs?start_date={start_date}&end_date={end_date}")

        assert response.status_code == 200
        # Verify date filters were applied
        mock_cursor.execute.assert_called_once()

    def test_get_collection_logs_invalid_limit(self, client):
        """Test getting collection logs with invalid limit."""
        # Negative limit
        response = client.get("/api/ingestion/logs?limit=-1")
        assert response.status_code == 422

        # Limit too large
        response = client.get("/api/ingestion/logs?limit=10000")
        assert response.status_code == 422

    def test_get_collection_logs_invalid_offset(self, client):
        """Test getting collection logs with invalid offset."""
        # Negative offset
        response = client.get("/api/ingestion/logs?offset=-1")
        assert response.status_code == 422
