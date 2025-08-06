"""Simple integration tests."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.agents.diagram_agent import generate_diagram
from src.models.schemas import CloudProvider, DiagramRequest
from src.tools.diagram_tools import DiagramBuilder, create_diagram_from_description


class TestIntegration:
    """Test full integration scenarios."""

    @patch("src.tools.diagram_tools.Diagram")
    @patch("src.utils.file_manager.file_manager.get_temp_path")
    @patch("pathlib.Path.exists")
    def test_end_to_end_diagram_generation(
        self, mock_exists, mock_get_path, mock_diagram
    ):
        """Test complete diagram generation flow."""
        # Setup mocks
        mock_path = Path("/tmp/test_diagram.png")
        mock_get_path.return_value = mock_path
        mock_exists.return_value = True

        # Test the creation function
        result_path = create_diagram_from_description("web application with database")

        assert result_path == mock_path
        mock_diagram.assert_called_once()

    @patch("src.agents.diagram_agent.settings")
    @patch("src.tools.diagram_tools.create_diagram_from_description")
    @pytest.mark.asyncio
    async def test_agent_integration(self, mock_create, mock_settings):
        """Test agent integration."""
        mock_settings.mock_mode = True
        mock_create.return_value = Path("/tmp/test.png")

        request = DiagramRequest(
            description="A microservices architecture with API gateway",
            provider=CloudProvider.AWS,
        )

        result = await generate_diagram(request)

        assert result.success is True
        assert result.diagram_path == "/tmp/test.png"

    def test_diagram_builder_flow(self):
        """Test diagram builder workflow."""
        builder = DiagramBuilder("Test Architecture")

        # Add components
        builder.add_cluster("web", "Web Tier")
        builder.add_cluster("data", "Data Tier")

        with patch("src.tools.diagram_tools.get_node_class") as mock_get_class:
            mock_get_class.return_value = lambda x: f"MockNode({x})"

            builder.add_node("lb", "alb", CloudProvider.AWS, "Load Balancer")
            builder.add_node("web1", "ec2", CloudProvider.AWS, "Web Server", "web")
            builder.add_node("db1", "rds", CloudProvider.AWS, "Database", "data")

            # Add connections
            builder.connect_nodes("lb", "web1", "routes")
            builder.connect_nodes("web1", "db1", "queries")

            # Verify structure
            assert len(builder.nodes) == 3
            assert len(builder.clusters) == 2
            assert len(builder.connections) == 2


if __name__ == "__main__":
    pytest.main([__file__])
