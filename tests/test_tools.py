"""Tests for diagram tools functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.schemas import CloudProvider, DiagramDirection, NodeType
from src.tools.diagram_tools import (
    AddNodeInput,
    CloudServiceMapper,
    ConnectNodesInput,
    CreateClusterInput,
    CreateDiagramInput,
    DiagramTools,
    RenderDiagramInput,
    _diagram_registry,
)
from src.tools.validators import (
    DiagramValidator,
    ServiceNameNormalizer,
    ValidationError,
    validate_diagram_request_data,
)


class TestCloudServiceMapper:
    """Test the cloud service mapper functionality."""

    def test_get_node_class_aws_ec2(self):
        """Test getting AWS EC2 node class."""
        with patch("src.tools.diagram_tools.__import__") as mock_import:
            mock_module = MagicMock()
            mock_ec2_class = MagicMock()
            mock_module.EC2 = mock_ec2_class
            mock_import.return_value = mock_module

            node_class, node_type = CloudServiceMapper.get_node_class(
                "ec2", CloudProvider.AWS
            )

            assert node_class == mock_ec2_class
            assert node_type == NodeType.COMPUTE

    def test_get_node_class_case_insensitive(self):
        """Test that service names are case insensitive."""
        with patch("src.tools.diagram_tools.__import__") as mock_import:
            mock_module = MagicMock()
            mock_rds_class = MagicMock()
            mock_module.RDS = mock_rds_class
            mock_import.return_value = mock_module

            node_class, node_type = CloudServiceMapper.get_node_class(
                "RDS", CloudProvider.AWS
            )

            assert node_class == mock_rds_class
            assert node_type == NodeType.DATABASE

    def test_get_node_class_invalid_service(self):
        """Test error handling for invalid service."""
        with pytest.raises(ValueError, match="Service 'invalid' not found"):
            CloudServiceMapper.get_node_class("invalid", CloudProvider.AWS)

    def test_get_node_class_invalid_provider(self):
        """Test error handling for invalid provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            CloudServiceMapper.get_node_class("ec2", "invalid_provider")


class TestDiagramTools:
    """Test the diagram tools functionality."""

    def setup_method(self):
        """Set up each test."""
        # Clear the diagram registry
        _diagram_registry.clear()

    def test_create_diagram_structure(self):
        """Test creating a diagram structure."""
        input_data = CreateDiagramInput(
            title="Test Diagram", direction=DiagramDirection.TOP_BOTTOM
        )

        result = DiagramTools.create_diagram_structure(input_data)

        assert result.success is True
        assert "diagram_id" in result.result
        assert result.result["title"] == "Test Diagram"
        assert len(_diagram_registry) == 1

    def test_add_node_success(self):
        """Test successfully adding a node."""
        # First create a diagram
        create_input = CreateDiagramInput(title="Test")
        create_result = DiagramTools.create_diagram_structure(create_input)
        diagram_id = create_result.result["diagram_id"]

        with patch(
            "src.tools.diagram_tools.CloudServiceMapper.get_node_class"
        ) as mock_mapper:
            mock_mapper.return_value = (MagicMock(), NodeType.COMPUTE)

            add_input = AddNodeInput(
                diagram_id=diagram_id,
                node_id="web-server",
                service="ec2",
                provider=CloudProvider.AWS,
                label="Web Server",
            )

            result = DiagramTools.add_node(add_input)

            assert result.success is True
            assert result.result["node_id"] == "web-server"
            assert result.result["service"] == "ec2"
            assert result.result["node_type"] == NodeType.COMPUTE

    def test_add_node_invalid_diagram(self):
        """Test adding node to non-existent diagram."""
        add_input = AddNodeInput(
            diagram_id="invalid-id",
            node_id="web-server",
            service="ec2",
            provider=CloudProvider.AWS,
            label="Web Server",
        )

        result = DiagramTools.add_node(add_input)

        assert result.success is False
        assert "not found" in result.error

    def test_create_cluster(self):
        """Test creating a cluster."""
        # First create a diagram
        create_input = CreateDiagramInput(title="Test")
        create_result = DiagramTools.create_diagram_structure(create_input)
        diagram_id = create_result.result["diagram_id"]

        cluster_input = CreateClusterInput(
            diagram_id=diagram_id, cluster_id="web-tier", label="Web Tier"
        )

        result = DiagramTools.create_cluster(cluster_input)

        assert result.success is True
        assert result.result["cluster_id"] == "web-tier"
        assert result.result["label"] == "Web Tier"

    def test_connect_nodes(self):
        """Test connecting nodes."""
        # Create diagram and add nodes
        create_input = CreateDiagramInput(title="Test")
        create_result = DiagramTools.create_diagram_structure(create_input)
        diagram_id = create_result.result["diagram_id"]

        with patch(
            "src.tools.diagram_tools.CloudServiceMapper.get_node_class"
        ) as mock_mapper:
            mock_mapper.return_value = (MagicMock(), NodeType.COMPUTE)

            # Add two nodes
            DiagramTools.add_node(
                AddNodeInput(
                    diagram_id=diagram_id,
                    node_id="node1",
                    service="ec2",
                    provider=CloudProvider.AWS,
                    label="Node 1",
                )
            )

            DiagramTools.add_node(
                AddNodeInput(
                    diagram_id=diagram_id,
                    node_id="node2",
                    service="rds",
                    provider=CloudProvider.AWS,
                    label="Node 2",
                )
            )

        connect_input = ConnectNodesInput(
            diagram_id=diagram_id,
            source_node_id="node1",
            target_node_id="node2",
            label="connects to",
        )

        result = DiagramTools.connect_nodes(connect_input)

        assert result.success is True
        assert result.result["source_node_id"] == "node1"
        assert result.result["target_node_id"] == "node2"

    def test_connect_invalid_nodes(self):
        """Test connecting non-existent nodes."""
        create_input = CreateDiagramInput(title="Test")
        create_result = DiagramTools.create_diagram_structure(create_input)
        diagram_id = create_result.result["diagram_id"]

        connect_input = ConnectNodesInput(
            diagram_id=diagram_id, source_node_id="invalid1", target_node_id="invalid2"
        )

        result = DiagramTools.connect_nodes(connect_input)

        assert result.success is False
        assert "not found" in result.error

    @patch("src.tools.diagram_tools.Diagram")
    @patch("src.tools.diagram_tools.file_manager")
    def test_render_diagram(self, mock_file_manager, mock_diagram_class):
        """Test rendering a diagram."""
        # Setup mocks
        mock_output_path = Path("/tmp/test_diagram.png")
        mock_file_manager.get_temp_path.return_value = mock_output_path
        mock_file_manager.get_file_size.return_value = 1024

        # Mock the path exists check
        with patch.object(Path, "exists", return_value=True):
            # Create diagram with nodes
            create_input = CreateDiagramInput(title="Test")
            create_result = DiagramTools.create_diagram_structure(create_input)
            diagram_id = create_result.result["diagram_id"]

            with patch(
                "src.tools.diagram_tools.CloudServiceMapper.get_node_class"
            ) as mock_mapper:
                mock_node_class = MagicMock()
                mock_mapper.return_value = (mock_node_class, NodeType.COMPUTE)

                DiagramTools.add_node(
                    AddNodeInput(
                        diagram_id=diagram_id,
                        node_id="node1",
                        service="ec2",
                        provider=CloudProvider.AWS,
                        label="Node 1",
                    )
                )

            render_input = RenderDiagramInput(diagram_id=diagram_id)
            result = DiagramTools.render_diagram(render_input)

            assert result.success is True
            assert result.result["diagram_path"] == str(mock_output_path)
            assert result.result["file_size_bytes"] == 1024
            assert "structure" in result.result


class TestDiagramValidator:
    """Test the diagram validator functionality."""

    def test_validate_id_success(self):
        """Test valid ID validation."""
        # Should not raise
        DiagramValidator.validate_id("valid-id_123")
        DiagramValidator.validate_id("node1")
        DiagramValidator.validate_id("my_cluster")

    def test_validate_id_invalid_characters(self):
        """Test invalid ID characters."""
        with pytest.raises(ValidationError, match="can only contain"):
            DiagramValidator.validate_id("invalid id!")

        with pytest.raises(ValidationError, match="can only contain"):
            DiagramValidator.validate_id("invalid@id")

    def test_validate_id_reserved_words(self):
        """Test reserved word validation."""
        with pytest.raises(ValidationError, match="reserved word"):
            DiagramValidator.validate_id("diagram")

        with pytest.raises(ValidationError, match="reserved word"):
            DiagramValidator.validate_id("node")

    def test_validate_id_empty(self):
        """Test empty ID validation."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            DiagramValidator.validate_id("")

    def test_validate_title_success(self):
        """Test valid title validation."""
        DiagramValidator.validate_title("My Architecture Diagram")
        DiagramValidator.validate_title("Simple Web App")

    def test_validate_title_invalid_characters(self):
        """Test invalid title characters."""
        with pytest.raises(ValidationError, match="invalid characters"):
            DiagramValidator.validate_title("Title with <script>")

    def test_validate_title_too_long(self):
        """Test title length validation."""
        long_title = "x" * 101
        with pytest.raises(ValidationError, match="cannot exceed"):
            DiagramValidator.validate_title(long_title)

    def test_validate_service_name(self):
        """Test service name validation."""
        DiagramValidator.validate_service_name("EC2", CloudProvider.AWS)
        DiagramValidator.validate_service_name("Cloud Functions", CloudProvider.GCP)

        with pytest.raises(ValidationError, match="cannot be empty"):
            DiagramValidator.validate_service_name("", CloudProvider.AWS)

    def test_validate_diagram_limits(self):
        """Test diagram complexity limits."""
        # Should not raise
        DiagramValidator.validate_diagram_limits(10, 15, 3)

        # Should raise for too many nodes
        with pytest.raises(ValidationError, match="cannot exceed.*nodes"):
            DiagramValidator.validate_diagram_limits(100, 15, 3)


class TestServiceNameNormalizer:
    """Test the service name normalizer functionality."""

    def test_normalize_service_name(self):
        """Test service name normalization."""
        assert ServiceNameNormalizer.normalize_service_name("EC2") == "ec2"
        assert ServiceNameNormalizer.normalize_service_name("AWS Lambda") == "lambda"
        assert (
            ServiceNameNormalizer.normalize_service_name("Cloud Functions")
            == "cloud_functions"
        )
        assert ServiceNameNormalizer.normalize_service_name("Azure-VM") == "vm"

    def test_normalize_with_aliases(self):
        """Test normalization with aliases."""
        assert (
            ServiceNameNormalizer.normalize_service_name("Elastic Compute Cloud")
            == "ec2"
        )
        assert (
            ServiceNameNormalizer.normalize_service_name("Simple Storage Service")
            == "s3"
        )
        assert ServiceNameNormalizer.normalize_service_name("Virtual Machine") == "vm"

    def test_suggest_services(self):
        """Test service suggestions."""
        with patch("src.tools.diagram_tools.CloudServiceMapper") as mock_mapper:
            mock_mapper.SERVICE_MAPPINGS = {
                CloudProvider.AWS: {
                    "ec2": ("path", "class", NodeType.COMPUTE),
                    "lambda": ("path", "class", NodeType.COMPUTE),
                    "rds": ("path", "class", NodeType.DATABASE),
                }
            }

            suggestions = ServiceNameNormalizer.suggest_services(
                "compute", CloudProvider.AWS
            )
            assert isinstance(suggestions, list)
            assert len(suggestions) <= 5


class TestValidationFunctions:
    """Test standalone validation functions."""

    def test_validate_diagram_request_data_success(self):
        """Test valid diagram request validation."""
        description = "A web application with load balancer and database"
        validate_diagram_request_data(description)  # Should not raise

    def test_validate_diagram_request_data_too_short(self):
        """Test too short description."""
        with pytest.raises(ValidationError, match="at least 10 characters"):
            validate_diagram_request_data("short")

    def test_validate_diagram_request_data_too_long(self):
        """Test too long description."""
        long_description = "x" * 2001
        with pytest.raises(ValidationError, match="cannot exceed 2000"):
            validate_diagram_request_data(long_description)

    def test_validate_diagram_request_data_malicious(self):
        """Test malicious content detection."""
        with pytest.raises(ValidationError, match="potentially unsafe"):
            validate_diagram_request_data(
                "Create a diagram with <script>alert('hack')</script>"
            )

        with pytest.raises(ValidationError, match="potentially unsafe"):
            validate_diagram_request_data("javascript:alert('hack')")


if __name__ == "__main__":
    pytest.main([__file__])
