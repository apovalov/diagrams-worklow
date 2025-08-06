"""Simplified diagram tools using the diagrams package."""

import logging
from pathlib import Path

from diagrams import Cluster, Diagram, Edge

from src.models.schemas import CloudProvider, DiagramDirection
from src.utils.file_manager import file_manager

logger = logging.getLogger(__name__)


# Service mappings for cloud providers
SERVICE_MAPPINGS = {
    CloudProvider.AWS: {
        "ec2": ("diagrams.aws.compute", "EC2"),
        "lambda": ("diagrams.aws.compute", "Lambda"),
        "rds": ("diagrams.aws.database", "RDS"),
        "s3": ("diagrams.aws.storage", "S3"),
        "alb": ("diagrams.aws.network", "ALB"),
        "vpc": ("diagrams.aws.network", "VPC"),
        "apigateway": ("diagrams.aws.network", "APIGateway"),
    },
    CloudProvider.GCP: {
        "gce": ("diagrams.gcp.compute", "ComputeEngine"),
        "cloud_functions": ("diagrams.gcp.compute", "Functions"),
        "cloud_sql": ("diagrams.gcp.database", "SQL"),
        "cloud_storage": ("diagrams.gcp.storage", "Storage"),
        "cloud_load_balancer": ("diagrams.gcp.network", "LoadBalancer"),
    },
    CloudProvider.AZURE: {
        "vm": ("diagrams.azure.compute", "VM"),
        "functions": ("diagrams.azure.compute", "FunctionApps"),
        "sql_database": ("diagrams.azure.database", "SQLDatabases"),
        "blob_storage": ("diagrams.azure.storage", "BlobStorage"),
        "load_balancer": ("diagrams.azure.network", "LoadBalancer"),
    },
}


def get_node_class(service: str, provider: CloudProvider):
    """Get diagram node class for a service."""
    service_key = service.lower().replace("-", "_").replace(" ", "_")

    if provider not in SERVICE_MAPPINGS:
        raise ValueError(f"Unsupported provider: {provider}")

    provider_services = SERVICE_MAPPINGS[provider]
    if service_key not in provider_services:
        available = list(provider_services.keys())
        raise ValueError(f"Service '{service}' not found. Available: {available}")

    module_path, class_name = provider_services[service_key]

    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ValueError(f"Failed to import {module_path}.{class_name}: {e}") from e


class DiagramBuilder:
    """Simplified diagram builder."""

    def __init__(
        self, title: str, direction: DiagramDirection = DiagramDirection.TOP_BOTTOM
    ):
        self.title = title
        self.direction = direction
        self.nodes = {}
        self.clusters = {}
        self.connections = []

    def add_node(
        self,
        node_id: str,
        service: str,
        provider: CloudProvider,
        label: str,
        cluster: str = None,
    ):
        """Add a node to the diagram."""
        node_class = get_node_class(service, provider)
        self.nodes[node_id] = {"class": node_class, "label": label, "cluster": cluster}

    def add_cluster(self, cluster_id: str, label: str):
        """Add a cluster to the diagram."""
        self.clusters[cluster_id] = {"label": label}

    def connect_nodes(self, source: str, target: str, label: str = None):
        """Connect two nodes."""
        self.connections.append({"source": source, "target": target, "label": label})

    def render(self) -> Path:
        """Render the diagram to a file."""
        filename = file_manager.generate_filename("png")
        output_path = file_manager.get_temp_path(filename)

        with Diagram(
            self.title,
            filename=str(output_path.with_suffix("")),
            direction=self.direction.value,
            show=False,
        ):
            # Create clusters
            cluster_objects = {}
            for cluster_id, cluster_data in self.clusters.items():
                cluster_obj = Cluster(cluster_data["label"])
                cluster_objects[cluster_id] = cluster_obj

            # Create nodes
            node_objects = {}
            for node_id, node_data in self.nodes.items():
                node_class = node_data["class"]
                label = node_data["label"]
                cluster = node_data.get("cluster")

                if cluster and cluster in cluster_objects:
                    with cluster_objects[cluster]:
                        node_obj = node_class(label)
                else:
                    node_obj = node_class(label)

                node_objects[node_id] = node_obj

            # Create connections
            for conn in self.connections:
                source_obj = node_objects.get(conn["source"])
                target_obj = node_objects.get(conn["target"])

                if source_obj and target_obj:
                    edge = Edge(label=conn.get("label"))
                    source_obj >> edge >> target_obj

        return output_path


def create_diagram_from_description(
    description: str, provider: CloudProvider = None
) -> Path:
    """Create a diagram from natural language description."""
    # For now, create a simple fallback diagram
    # In the real implementation, this would use the LLM agent

    builder = DiagramBuilder("Infrastructure Diagram")

    # Simple heuristics for demo
    if "web" in description.lower():
        builder.add_cluster("web", "Web Tier")
        builder.add_node(
            "web1", "ec2", provider or CloudProvider.AWS, "Web Server", "web"
        )

    if "database" in description.lower() or "db" in description.lower():
        builder.add_cluster("data", "Data Tier")
        builder.add_node(
            "db1", "rds", provider or CloudProvider.AWS, "Database", "data"
        )

        if "web1" in builder.nodes:
            builder.connect_nodes("web1", "db1", "queries")

    if "load balancer" in description.lower() or "lb" in description.lower():
        builder.add_node("lb1", "alb", provider or CloudProvider.AWS, "Load Balancer")

        if "web1" in builder.nodes:
            builder.connect_nodes("lb1", "web1", "routes")

    return builder.render()
