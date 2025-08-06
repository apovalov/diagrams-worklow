"""Tests for FastAPI endpoints."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.schemas import DiagramResponse, ErrorResponse

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self):
        """Test health endpoint returns correct format."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "0.1.0"


class TestDiagramEndpoint:
    """Test diagram generation endpoint."""

    @patch("src.main.generate_diagram")
    def test_generate_diagram_success(self, mock_generate):
        """Test successful diagram generation."""
        mock_response = DiagramResponse(
            diagram_path="/tmp/test.png", generation_time_seconds=1.5
        )
        mock_generate.return_value = mock_response

        response = client.post(
            "/generate-diagram", json={"description": "A web application with database"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["diagram_path"] == "/tmp/test.png"
        assert data["generation_time_seconds"] == 1.5

    @patch("src.main.generate_diagram")
    def test_generate_diagram_validation_error(self, mock_generate):
        """Test validation error handling."""
        mock_generate.return_value = ErrorResponse(
            error="Description must be at least 10 characters"
        )

        response = client.post("/generate-diagram", json={"description": "short"})

        assert response.status_code == 400
        assert "at least 10 characters" in response.json()["detail"]

    def test_generate_diagram_invalid_request(self):
        """Test invalid request format."""
        response = client.post("/generate-diagram", json={"invalid": "field"})

        assert response.status_code == 422  # Validation error

    @patch("src.main.generate_diagram")
    def test_generate_diagram_server_error(self, mock_generate):
        """Test server error handling."""
        mock_generate.side_effect = Exception("Server error")

        response = client.post(
            "/generate-diagram", json={"description": "A web application with database"}
        )

        assert response.status_code == 500
        assert "Server error" in response.json()["detail"]


class TestFileServing:
    """Test diagram file serving."""

    @patch("src.main.file_manager.get_temp_path")
    @patch("pathlib.Path.exists")
    def test_get_diagram_success(self, mock_exists, mock_get_path):
        """Test successful diagram file serving."""
        mock_path = Path("/tmp/test.png")
        mock_get_path.return_value = mock_path
        mock_exists.return_value = True

        with patch("src.main.FileResponse") as mock_file_response:
            mock_file_response.return_value = "file_content"

            client.get("/diagrams/test.png")

            # Note: This test is simplified since FileResponse is hard to mock properly
            mock_get_path.assert_called_once_with("test.png")

    @patch("src.main.file_manager.get_temp_path")
    @patch("pathlib.Path.exists")
    def test_get_diagram_not_found(self, mock_exists, mock_get_path):
        """Test diagram file not found."""
        mock_path = Path("/tmp/test.png")
        mock_get_path.return_value = mock_path
        mock_exists.return_value = False

        response = client.get("/diagrams/nonexistent.png")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestAssistantEndpoint:
    """Test assistant chat endpoint."""

    @patch("src.main.generate_diagram")
    def test_assistant_diagram_request(self, mock_generate):
        """Test assistant endpoint for diagram requests."""
        mock_response = DiagramResponse(
            diagram_path="/tmp/diagram_abc123.png", generation_time_seconds=2.0
        )
        mock_generate.return_value = mock_response

        response = client.post(
            "/assistant", json={"message": "Create a diagram for a web application"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "created an infrastructure diagram" in data["response"]
        assert data["diagram_url"] == "/diagrams/diagram_abc123.png"

    def test_assistant_general_request(self):
        """Test assistant endpoint for general requests."""
        response = client.post("/assistant", json={"message": "Hello, how are you?"})

        assert response.status_code == 200
        data = response.json()
        assert "diagram architect assistant" in data["response"]
        assert data["diagram_url"] is None

    @patch("src.main.generate_diagram")
    def test_assistant_diagram_error(self, mock_generate):
        """Test assistant handling of diagram generation errors."""
        mock_generate.return_value = ErrorResponse(error="Generation failed")

        response = client.post(
            "/assistant", json={"message": "Create a diagram for something"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "couldn't generate the diagram" in data["response"]
        assert data["diagram_url"] is None

    def test_assistant_invalid_request(self):
        """Test assistant endpoint with invalid request."""
        response = client.post("/assistant", json={"invalid": "field"})

        assert response.status_code == 422  # Validation error


class TestErrorHandlers:
    """Test global error handlers."""

    def test_404_handler(self):
        """Test 404 error handler."""
        response = client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"]


class TestCORS:
    """Test CORS configuration."""

    def test_cors_preflight(self):
        """Test CORS preflight request."""
        response = client.options(
            "/generate-diagram",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        # CORS should be handled by middleware
        assert response.status_code in [200, 204]


if __name__ == "__main__":
    pytest.main([__file__])
