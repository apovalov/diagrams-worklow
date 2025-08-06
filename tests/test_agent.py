"""Simplified tests for diagram agent."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.diagram_agent import DiagramAgent, generate_diagram
from src.models.schemas import (
    CloudProvider,
    DiagramRequest,
    DiagramResponse,
    ErrorResponse,
)


class TestDiagramAgent:
    """Test the diagram agent."""

    @patch("src.agents.diagram_agent.settings")
    def test_init_mock_mode(self, mock_settings):
        """Test agent initialization in mock mode."""
        mock_settings.mock_mode = True
        agent = DiagramAgent()
        assert agent.model is None

    @patch("src.agents.diagram_agent.settings")
    @patch("src.agents.diagram_agent.genai")
    def test_init_real_mode(self, mock_genai, mock_settings):
        """Test agent initialization with Gemini."""
        mock_settings.mock_mode = False
        mock_settings.gemini_api_key = "test-key"

        DiagramAgent()

        mock_genai.configure.assert_called_once_with(api_key="test-key")

    @pytest.mark.asyncio
    @patch("src.agents.diagram_agent.settings")
    async def test_generate_diagram_mock_mode(self, mock_settings):
        """Test diagram generation in mock mode."""
        mock_settings.mock_mode = True
        agent = DiagramAgent()

        with patch.object(agent, "_create_mock_diagram") as mock_create:
            mock_create.return_value = Path("/tmp/test.png")

            request = DiagramRequest(description="A web application")
            response = await agent.generate_diagram(request)

            assert isinstance(response, DiagramResponse)
            assert response.success is True
            assert response.diagram_path == "/tmp/test.png"

    @pytest.mark.asyncio
    async def test_generate_diagram_validation_error(self):
        """Test validation error handling."""
        agent = DiagramAgent()

        request = DiagramRequest(description="short")  # Too short
        response = await agent.generate_diagram(request)

        assert isinstance(response, ErrorResponse)
        assert response.success is False
        assert "at least 10 characters" in response.error

    @patch("src.agents.diagram_agent.create_diagram_from_description")
    def test_create_mock_diagram(self, mock_create):
        """Test mock diagram creation."""
        mock_create.return_value = Path("/tmp/mock.png")
        agent = DiagramAgent()

        request = DiagramRequest(description="Test diagram", provider=CloudProvider.AWS)
        result = agent._create_mock_diagram(request)

        assert result == Path("/tmp/mock.png")
        mock_create.assert_called_once_with("Test diagram", CloudProvider.AWS)


class TestGlobalFunctions:
    """Test global utility functions."""

    @pytest.mark.asyncio
    @patch("src.agents.diagram_agent._agent", None)
    async def test_get_agent(self):
        """Test getting the global agent instance."""
        from src.agents.diagram_agent import get_agent

        agent = await get_agent()
        assert agent is not None
        assert isinstance(agent, DiagramAgent)

    @pytest.mark.asyncio
    @patch("src.agents.diagram_agent.get_agent")
    async def test_generate_diagram_function(self, mock_get_agent):
        """Test the global generate_diagram function."""
        mock_agent = AsyncMock()
        mock_response = DiagramResponse(
            diagram_path="/tmp/test.png", generation_time_seconds=1.0
        )
        mock_agent.generate_diagram.return_value = mock_response
        mock_get_agent.return_value = mock_agent

        request = DiagramRequest(description="Test diagram")
        result = await generate_diagram(request)

        assert result == mock_response
        mock_agent.generate_diagram.assert_called_once_with(request)


if __name__ == "__main__":
    pytest.main([__file__])
