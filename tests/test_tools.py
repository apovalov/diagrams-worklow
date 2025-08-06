"""Simplified tests for diagram tools."""

from unittest.mock import MagicMock, patch

import pytest

from src.models.schemas import CloudProvider
from src.tools.diagram_tools import (
    DiagramBuilder,
    create_diagram_from_description,
    get_node_class,
)


class TestServiceMapping:
    """Test service mapping functionality."""

    @patch("src.tools.diagram_tools.__import__")
    def test_get_node_class_success(self, mock_import):
        """Test successful node class retrieval."""
        mock_module = MagicMock()
        mock_ec2_class = MagicMock()
        mock_module.EC2 = mock_ec2_class
        mock_import.return_value = mock_module

        result = get_node_class("ec2", CloudProvider.AWS)
        assert result == mock_ec2_class

    def test_get_node_class_invalid_service(self):
        """Test error for invalid service."""
        with pytest.raises(ValueError, match="Service 'invalid' not found"):
            get_node_class("invalid", CloudProvider.AWS)

    def test_get_node_class_invalid_provider(self):
        """Test error for invalid provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            get_node_class("ec2", "invalid")


class TestDiagramBuilder:
    """Test diagram builder."""

    def test_init(self):
        """Test builder initialization."""
        builder = DiagramBuilder("Test Diagram")
        assert builder.title == "Test Diagram"
        assert builder.nodes == {}
        assert builder.clusters == {}
        assert builder.connections == []

    @patch("src.tools.diagram_tools.get_node_class")
    def test_add_node(self, mock_get_class):
        """Test adding a node."""
        mock_class = MagicMock()
        mock_get_class.return_value = mock_class

        builder = DiagramBuilder("Test")
        builder.add_node("node1", "ec2", CloudProvider.AWS, "Web Server")

        assert "node1" in builder.nodes
        assert builder.nodes["node1"]["label"] == "Web Server"
        mock_get_class.assert_called_once_with("ec2", CloudProvider.AWS)

    def test_add_cluster(self):
        """Test adding a cluster."""
        builder = DiagramBuilder("Test")
        builder.add_cluster("web", "Web Tier")

        assert "web" in builder.clusters
        assert builder.clusters["web"]["label"] == "Web Tier"

    def test_connect_nodes(self):
        """Test connecting nodes."""
        builder = DiagramBuilder("Test")
        builder.connect_nodes("node1", "node2", "connects")

        assert len(builder.connections) == 1
        connection = builder.connections[0]
        assert connection["source"] == "node1"
        assert connection["target"] == "node2"
        assert connection["label"] == "connects"


class TestDiagramGeneration:
    """Test diagram generation from description."""

    @patch("src.tools.diagram_tools.DiagramBuilder")
    def test_create_diagram_web_app(self, mock_builder_class):
        """Test creating diagram for web application."""
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder
        mock_builder.render.return_value = "/tmp/test.png"

        create_diagram_from_description("web application with database")

        # Verify builder was called with expected methods
        mock_builder.add_cluster.assert_called()
        mock_builder.add_node.assert_called()
        mock_builder.connect_nodes.assert_called()
        mock_builder.render.assert_called_once()

    @patch("src.tools.diagram_tools.DiagramBuilder")
    def test_create_diagram_load_balancer(self, mock_builder_class):
        """Test creating diagram with load balancer."""
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder
        mock_builder.render.return_value = "/tmp/test.png"
        mock_builder.nodes = {"web1": {}}  # Mock existing web node

        create_diagram_from_description("load balancer with web servers")

        mock_builder.add_node.assert_called()
        mock_builder.connect_nodes.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])
