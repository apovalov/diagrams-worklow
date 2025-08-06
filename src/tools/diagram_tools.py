"""Tools for diagram creation using the diagrams package."""

import logging
from typing import Any
from uuid import uuid4

from diagrams import Cluster, Diagram, Edge
from pydantic import BaseModel, Field

from src.models.schemas import (
    CloudProvider,
    ClusterInfo,
    ConnectionInfo,
    DiagramDirection,
    DiagramStructure,
    NodeInfo,
    NodeType,
    ToolResult,
)
from src.utils.file_manager import file_manager

logger = logging.getLogger(__name__)


# Tool Input/Output Schemas
class CreateDiagramInput(BaseModel):
    """Input for create_diagram_structure tool."""

    title: str = Field(..., description="Title of the diagram")
    direction: DiagramDirection = Field(
        default=DiagramDirection.TOP_BOTTOM,
        description="Layout direction of the diagram",
    )
    filename: str | None = Field(
        default=None, description="Custom filename (will be generated if not provided)"
    )


class CreateDiagramOutput(BaseModel):
    """Output for create_diagram_structure tool."""

    diagram_id: str = Field(..., description="Unique identifier for the diagram")
    filename: str = Field(..., description="Generated filename for the diagram")
    title: str = Field(..., description="Diagram title")


class AddNodeInput(BaseModel):
    """Input for add_node tool."""

    diagram_id: str = Field(..., description="Diagram identifier")
    node_id: str = Field(..., description="Unique identifier for the node")
    service: str = Field(..., description="Cloud service name (e.g., 'EC2', 'Lambda')")
    provider: CloudProvider = Field(..., description="Cloud provider")
    label: str = Field(..., description="Display label for the node")
    cluster_id: str | None = Field(
        default=None, description="ID of cluster to add this node to"
    )


class AddNodeOutput(BaseModel):
    """Output for add_node tool."""

    node_id: str = Field(..., description="ID of the added node")
    service: str = Field(..., description="Cloud service name")
    node_type: NodeType = Field(..., description="Inferred node type")


class CreateClusterInput(BaseModel):
    """Input for create_cluster tool."""

    diagram_id: str = Field(..., description="Diagram identifier")
    cluster_id: str = Field(..., description="Unique identifier for the cluster")
    label: str = Field(..., description="Display label for the cluster")
    parent_cluster_id: str | None = Field(
        default=None, description="ID of parent cluster for nesting"
    )


class CreateClusterOutput(BaseModel):
    """Output for create_cluster tool."""

    cluster_id: str = Field(..., description="ID of the created cluster")
    label: str = Field(..., description="Cluster label")


class ConnectNodesInput(BaseModel):
    """Input for connect_nodes tool."""

    diagram_id: str = Field(..., description="Diagram identifier")
    source_node_id: str = Field(..., description="Source node ID")
    target_node_id: str = Field(..., description="Target node ID")
    label: str | None = Field(default=None, description="Connection label")
    bidirectional: bool = Field(
        default=False, description="Whether the connection is bidirectional"
    )


class ConnectNodesOutput(BaseModel):
    """Output for connect_nodes tool."""

    source_node_id: str = Field(..., description="Source node ID")
    target_node_id: str = Field(..., description="Target node ID")
    connection_type: str = Field(..., description="Type of connection created")


class RenderDiagramInput(BaseModel):
    """Input for render_diagram tool."""

    diagram_id: str = Field(..., description="Diagram identifier")


class RenderDiagramOutput(BaseModel):
    """Output for render_diagram tool."""

    diagram_path: str = Field(..., description="Path to the rendered diagram file")
    file_size_bytes: int = Field(..., description="Size of the generated file")
    structure: DiagramStructure = Field(..., description="Complete diagram structure")


# Cloud Service Mappings
class CloudServiceMapper:
    """Maps service names to diagram nodes and determines node types."""

    # Service mappings for different cloud providers
    SERVICE_MAPPINGS = {
        CloudProvider.AWS: {
            # Compute
            "ec2": ("diagrams.aws.compute", "EC2", NodeType.COMPUTE),
            "lambda": ("diagrams.aws.compute", "Lambda", NodeType.COMPUTE),
            "ecs": ("diagrams.aws.compute", "ECS", NodeType.COMPUTE),
            "eks": ("diagrams.aws.compute", "EKS", NodeType.COMPUTE),
            "fargate": ("diagrams.aws.compute", "Fargate", NodeType.COMPUTE),
            "batch": ("diagrams.aws.compute", "Batch", NodeType.COMPUTE),
            # Database
            "rds": ("diagrams.aws.database", "RDS", NodeType.DATABASE),
            "dynamodb": ("diagrams.aws.database", "Dynamodb", NodeType.DATABASE),
            "redshift": ("diagrams.aws.database", "Redshift", NodeType.DATABASE),
            "elasticache": ("diagrams.aws.database", "ElastiCache", NodeType.DATABASE),
            "documentdb": ("diagrams.aws.database", "DocumentDB", NodeType.DATABASE),
            # Storage
            "s3": ("diagrams.aws.storage", "S3", NodeType.STORAGE),
            "ebs": ("diagrams.aws.storage", "EBS", NodeType.STORAGE),
            "efs": ("diagrams.aws.storage", "EFS", NodeType.STORAGE),
            # Network
            "alb": ("diagrams.aws.network", "ALB", NodeType.NETWORK),
            "elb": ("diagrams.aws.network", "ELB", NodeType.NETWORK),
            "cloudfront": ("diagrams.aws.network", "CloudFront", NodeType.NETWORK),
            "apigateway": ("diagrams.aws.network", "APIGateway", NodeType.NETWORK),
            "route53": ("diagrams.aws.network", "Route53", NodeType.NETWORK),
            "vpc": ("diagrams.aws.network", "VPC", NodeType.NETWORK),
        },
        CloudProvider.GCP: {
            # Compute
            "gce": ("diagrams.gcp.compute", "ComputeEngine", NodeType.COMPUTE),
            "cloud_functions": ("diagrams.gcp.compute", "Functions", NodeType.COMPUTE),
            "gke": ("diagrams.gcp.compute", "GKE", NodeType.COMPUTE),
            "cloud_run": ("diagrams.gcp.compute", "Run", NodeType.COMPUTE),
            # Database
            "cloud_sql": ("diagrams.gcp.database", "SQL", NodeType.DATABASE),
            "firestore": ("diagrams.gcp.database", "Firestore", NodeType.DATABASE),
            "bigtable": ("diagrams.gcp.database", "Bigtable", NodeType.DATABASE),
            # Storage
            "cloud_storage": ("diagrams.gcp.storage", "Storage", NodeType.STORAGE),
            "persistent_disk": (
                "diagrams.gcp.storage",
                "PersistentDisk",
                NodeType.STORAGE,
            ),
            # Network
            "cloud_load_balancer": (
                "diagrams.gcp.network",
                "LoadBalancer",
                NodeType.NETWORK,
            ),
            "cloud_dns": ("diagrams.gcp.network", "DNS", NodeType.NETWORK),
        },
        CloudProvider.AZURE: {
            # Compute
            "vm": ("diagrams.azure.compute", "VM", NodeType.COMPUTE),
            "functions": ("diagrams.azure.compute", "FunctionApps", NodeType.COMPUTE),
            "aks": ("diagrams.azure.compute", "AKS", NodeType.COMPUTE),
            "container_instances": (
                "diagrams.azure.compute",
                "ContainerInstances",
                NodeType.COMPUTE,
            ),
            # Database
            "sql_database": (
                "diagrams.azure.database",
                "SQLDatabases",
                NodeType.DATABASE,
            ),
            "cosmos_db": ("diagrams.azure.database", "CosmosDb", NodeType.DATABASE),
            # Storage
            "blob_storage": ("diagrams.azure.storage", "BlobStorage", NodeType.STORAGE),
            "disk_storage": ("diagrams.azure.storage", "DiskStorage", NodeType.STORAGE),
            # Network
            "load_balancer": (
                "diagrams.azure.network",
                "LoadBalancer",
                NodeType.NETWORK,
            ),
            "application_gateway": (
                "diagrams.azure.network",
                "ApplicationGateway",
                NodeType.NETWORK,
            ),
        },
    }

    @classmethod
    def get_node_class(
        cls, service: str, provider: CloudProvider
    ) -> tuple[Any, NodeType]:
        """Get the diagrams node class and type for a service.

        Args:
            service: Service name (case-insensitive)
            provider: Cloud provider

        Returns:
            Tuple of (node_class, node_type)

        Raises:
            ValueError: If service is not found
        """
        service_key = service.lower().replace("-", "_").replace(" ", "_")

        if provider not in cls.SERVICE_MAPPINGS:
            raise ValueError(f"Unsupported provider: {provider}")

        provider_services = cls.SERVICE_MAPPINGS[provider]
        if service_key not in provider_services:
            # Try to find similar service names
            available = list(provider_services.keys())
            raise ValueError(
                f"Service '{service}' not found for {provider}. "
                f"Available services: {available}"
            )

        module_path, class_name, node_type = provider_services[service_key]

        try:
            # Import the module and get the class
            module = __import__(module_path, fromlist=[class_name])
            node_class = getattr(module, class_name)
            return node_class, node_type
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to import {module_path}.{class_name}: {e}") from e


# Global state for diagrams being constructed
_diagram_registry: dict[str, dict[str, Any]] = {}


class DiagramTools:
    """Tools for creating and manipulating diagrams."""

    @staticmethod
    def create_diagram_structure(input_data: CreateDiagramInput) -> ToolResult:
        """Initialize a new diagram structure.

        This tool creates a new diagram context that other tools can add nodes,
        clusters, and connections to. It doesn't render the diagram yet.
        """
        try:
            diagram_id = str(uuid4())
            filename = input_data.filename or file_manager.generate_filename("png")

            # Store diagram metadata
            _diagram_registry[diagram_id] = {
                "title": input_data.title,
                "direction": input_data.direction,
                "filename": filename,
                "nodes": {},  # node_id -> node_info
                "clusters": {},  # cluster_id -> cluster_info
                "connections": [],  # list of connection_info
                "diagram_obj": None,  # Will be created during render
            }

            output = CreateDiagramOutput(
                diagram_id=diagram_id, filename=filename, title=input_data.title
            )

            logger.info(f"Created diagram structure: {diagram_id}")
            return ToolResult(success=True, result=output.model_dump())

        except Exception as e:
            logger.error(f"Failed to create diagram structure: {e}")
            return ToolResult(success=False, error=str(e))

    @staticmethod
    def add_node(input_data: AddNodeInput) -> ToolResult:
        """Add a node to the diagram.

        This tool adds a cloud service node to the diagram. The node will be
        placed in the specified cluster if cluster_id is provided.
        """
        try:
            if input_data.diagram_id not in _diagram_registry:
                return ToolResult(
                    success=False, error=f"Diagram {input_data.diagram_id} not found"
                )

            # Get node class and type
            try:
                node_class, node_type = CloudServiceMapper.get_node_class(
                    input_data.service, input_data.provider
                )
            except ValueError as e:
                return ToolResult(success=False, error=str(e))

            # Store node information
            node_info = NodeInfo(
                id=input_data.node_id,
                label=input_data.label,
                service=input_data.service,
                provider=input_data.provider,
                node_type=node_type,
                cluster=input_data.cluster_id,
            )

            diagram_data = _diagram_registry[input_data.diagram_id]
            diagram_data["nodes"][input_data.node_id] = {
                "info": node_info,
                "class": node_class,
                "obj": None,  # Will be created during render
            }

            # Add to cluster if specified
            if (
                input_data.cluster_id
                and input_data.cluster_id in diagram_data["clusters"]
            ):
                diagram_data["clusters"][input_data.cluster_id]["nodes"].append(
                    input_data.node_id
                )

            output = AddNodeOutput(
                node_id=input_data.node_id,
                service=input_data.service,
                node_type=node_type,
            )

            logger.info(
                f"Added node {input_data.node_id} to diagram {input_data.diagram_id}"
            )
            return ToolResult(success=True, result=output.model_dump())

        except Exception as e:
            logger.error(f"Failed to add node: {e}")
            return ToolResult(success=False, error=str(e))

    @staticmethod
    def create_cluster(input_data: CreateClusterInput) -> ToolResult:
        """Create a cluster (group) in the diagram.

        This tool creates a logical grouping for nodes. Nodes can be added to
        the cluster when they are created by specifying the cluster_id.
        """
        try:
            if input_data.diagram_id not in _diagram_registry:
                return ToolResult(
                    success=False, error=f"Diagram {input_data.diagram_id} not found"
                )

            cluster_info = ClusterInfo(
                id=input_data.cluster_id, label=input_data.label, nodes=[]
            )

            diagram_data = _diagram_registry[input_data.diagram_id]
            diagram_data["clusters"][input_data.cluster_id] = {
                "info": cluster_info,
                "parent": input_data.parent_cluster_id,
                "nodes": [],
                "obj": None,  # Will be created during render
            }

            output = CreateClusterOutput(
                cluster_id=input_data.cluster_id, label=input_data.label
            )

            logger.info(
                f"Created cluster {input_data.cluster_id} in diagram {input_data.diagram_id}"
            )
            return ToolResult(success=True, result=output.model_dump())

        except Exception as e:
            logger.error(f"Failed to create cluster: {e}")
            return ToolResult(success=False, error=str(e))

    @staticmethod
    def connect_nodes(input_data: ConnectNodesInput) -> ToolResult:
        """Create a connection between two nodes.

        This tool creates a visual connection (edge) between two nodes in the diagram.
        The connection can be directional or bidirectional.
        """
        try:
            if input_data.diagram_id not in _diagram_registry:
                return ToolResult(
                    success=False, error=f"Diagram {input_data.diagram_id} not found"
                )

            diagram_data = _diagram_registry[input_data.diagram_id]

            # Validate nodes exist
            if input_data.source_node_id not in diagram_data["nodes"]:
                return ToolResult(
                    success=False,
                    error=f"Source node {input_data.source_node_id} not found",
                )

            if input_data.target_node_id not in diagram_data["nodes"]:
                return ToolResult(
                    success=False,
                    error=f"Target node {input_data.target_node_id} not found",
                )

            connection_info = ConnectionInfo(
                source=input_data.source_node_id,
                target=input_data.target_node_id,
                label=input_data.label,
                bidirectional=input_data.bidirectional,
            )

            diagram_data["connections"].append(connection_info)

            connection_type = (
                "bidirectional" if input_data.bidirectional else "directional"
            )
            output = ConnectNodesOutput(
                source_node_id=input_data.source_node_id,
                target_node_id=input_data.target_node_id,
                connection_type=connection_type,
            )

            logger.info(
                f"Connected nodes {input_data.source_node_id} -> {input_data.target_node_id} "
                f"in diagram {input_data.diagram_id}"
            )
            return ToolResult(success=True, result=output.model_dump())

        except Exception as e:
            logger.error(f"Failed to connect nodes: {e}")
            return ToolResult(success=False, error=str(e))

    @staticmethod
    def render_diagram(input_data: RenderDiagramInput) -> ToolResult:
        """Render the diagram to a file.

        This tool takes all the nodes, clusters, and connections that have been
        added to the diagram and renders them to an image file.
        """
        try:
            if input_data.diagram_id not in _diagram_registry:
                return ToolResult(
                    success=False, error=f"Diagram {input_data.diagram_id} not found"
                )

            diagram_data = _diagram_registry[input_data.diagram_id]

            # Get output path
            filename = diagram_data["filename"]
            output_path = file_manager.get_temp_path(filename)

            # Create the diagram
            direction = diagram_data["direction"].value
            with Diagram(
                diagram_data["title"],
                filename=str(output_path.with_suffix("")),  # diagrams adds .png
                direction=direction,
                show=False,
            ) as diag:
                diagram_data["diagram_obj"] = diag
                node_objects = {}
                cluster_objects = {}

                # Create clusters first
                for cluster_id, cluster_data in diagram_data["clusters"].items():
                    if cluster_data["parent"] is None:  # Top-level clusters only
                        cluster_obj = Cluster(cluster_data["info"].label)
                        cluster_objects[cluster_id] = cluster_obj
                        cluster_data["obj"] = cluster_obj

                # Create nodes
                for node_id, node_data in diagram_data["nodes"].items():
                    node_info = node_data["info"]
                    node_class = node_data["class"]

                    # Create node in appropriate context
                    if node_info.cluster and node_info.cluster in cluster_objects:
                        with cluster_objects[node_info.cluster]:
                            node_obj = node_class(node_info.label)
                    else:
                        node_obj = node_class(node_info.label)

                    node_objects[node_id] = node_obj
                    node_data["obj"] = node_obj

                # Create connections
                for connection in diagram_data["connections"]:
                    source_obj = node_objects.get(connection.source)
                    target_obj = node_objects.get(connection.target)

                    if source_obj and target_obj:
                        if connection.bidirectional:
                            # Create bidirectional edge
                            source_obj - Edge(label=connection.label) - target_obj
                        else:
                            # Create directional edge
                            source_obj >> Edge(label=connection.label) >> target_obj

            # Check if file was created
            if not output_path.exists():
                return ToolResult(success=False, error="Diagram file was not created")

            file_size = file_manager.get_file_size(output_path)

            # Build structure for response
            structure = DiagramStructure(
                title=diagram_data["title"],
                direction=diagram_data["direction"],
                nodes=[
                    node_data["info"] for node_data in diagram_data["nodes"].values()
                ],
                connections=diagram_data["connections"],
                clusters=[
                    cluster_data["info"]
                    for cluster_data in diagram_data["clusters"].values()
                ],
            )

            output = RenderDiagramOutput(
                diagram_path=str(output_path),
                file_size_bytes=file_size or 0,
                structure=structure,
            )

            logger.info(f"Rendered diagram {input_data.diagram_id} to {output_path}")

            # Clean up registry entry
            del _diagram_registry[input_data.diagram_id]

            return ToolResult(success=True, result=output.model_dump())

        except Exception as e:
            logger.error(f"Failed to render diagram: {e}")
            return ToolResult(success=False, error=str(e))


# Tool descriptions for the LLM agent
TOOL_DESCRIPTIONS = {
    "create_diagram_structure": {
        "description": "Initialize a new diagram with a title and layout direction. Must be called first before adding nodes or clusters.",
        "input_schema": CreateDiagramInput.model_json_schema(),
        "output_schema": CreateDiagramOutput.model_json_schema(),
    },
    "add_node": {
        "description": "Add a cloud service node to the diagram. Specify the service name, provider, and optionally assign it to a cluster.",
        "input_schema": AddNodeInput.model_json_schema(),
        "output_schema": AddNodeOutput.model_json_schema(),
    },
    "create_cluster": {
        "description": "Create a logical grouping (cluster) in the diagram. Nodes can be assigned to clusters when they are added.",
        "input_schema": CreateClusterInput.model_json_schema(),
        "output_schema": CreateClusterOutput.model_json_schema(),
    },
    "connect_nodes": {
        "description": "Create a visual connection between two nodes. Connections can be directional or bidirectional with optional labels.",
        "input_schema": ConnectNodesInput.model_json_schema(),
        "output_schema": ConnectNodesOutput.model_json_schema(),
    },
    "render_diagram": {
        "description": "Render the complete diagram to an image file. This should be called last after all nodes, clusters, and connections are added.",
        "input_schema": RenderDiagramInput.model_json_schema(),
        "output_schema": RenderDiagramOutput.model_json_schema(),
    },
}


# Available tools for the agent
AVAILABLE_TOOLS = {
    "create_diagram_structure": DiagramTools.create_diagram_structure,
    "add_node": DiagramTools.add_node,
    "create_cluster": DiagramTools.create_cluster,
    "connect_nodes": DiagramTools.connect_nodes,
    "render_diagram": DiagramTools.render_diagram,
}
