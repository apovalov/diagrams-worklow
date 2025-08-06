"""Input validation utilities for diagram tools."""

import re

from src.models.schemas import CloudProvider


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


class DiagramValidator:
    """Validates diagram-related inputs."""

    # Valid ID pattern: alphanumeric, hyphens, underscores
    ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    # Maximum lengths
    MAX_TITLE_LENGTH = 100
    MAX_LABEL_LENGTH = 50
    MAX_SERVICE_NAME_LENGTH = 30
    MAX_NODES_PER_DIAGRAM = 50
    MAX_CONNECTIONS_PER_DIAGRAM = 100
    MAX_CLUSTERS_PER_DIAGRAM = 10

    # Reserved words that cannot be used as IDs
    RESERVED_IDS = {
        "diagram",
        "node",
        "cluster",
        "connection",
        "edge",
        "root",
        "main",
        "default",
        "system",
        "admin",
        "user",
        "temp",
        "tmp",
    }

    @classmethod
    def validate_id(cls, id_value: str, id_type: str = "ID") -> None:
        """Validate an identifier (node_id, cluster_id, etc.).

        Args:
            id_value: The ID to validate
            id_type: Type of ID for error messages

        Raises:
            ValidationError: If ID is invalid
        """
        if not id_value:
            raise ValidationError(f"{id_type} cannot be empty")

        if len(id_value) > 50:
            raise ValidationError(f"{id_type} cannot exceed 50 characters")

        if not cls.ID_PATTERN.match(id_value):
            raise ValidationError(
                f"{id_type} can only contain alphanumeric characters, hyphens, and underscores"
            )

        if id_value.lower() in cls.RESERVED_IDS:
            raise ValidationError(f"{id_type} '{id_value}' is a reserved word")

        if id_value.startswith("-") or id_value.endswith("-"):
            raise ValidationError(f"{id_type} cannot start or end with a hyphen")

        if id_value.startswith("_") or id_value.endswith("_"):
            raise ValidationError(f"{id_type} cannot start or end with an underscore")

    @classmethod
    def validate_title(cls, title: str) -> None:
        """Validate diagram title.

        Args:
            title: Title to validate

        Raises:
            ValidationError: If title is invalid
        """
        if not title or not title.strip():
            raise ValidationError("Title cannot be empty")

        if len(title.strip()) > cls.MAX_TITLE_LENGTH:
            raise ValidationError(
                f"Title cannot exceed {cls.MAX_TITLE_LENGTH} characters"
            )

        # Check for potentially problematic characters
        if any(char in title for char in '<>"|*?\\/:'):
            raise ValidationError("Title contains invalid characters")

    @classmethod
    def validate_label(cls, label: str) -> None:
        """Validate node or cluster label.

        Args:
            label: Label to validate

        Raises:
            ValidationError: If label is invalid
        """
        if not label or not label.strip():
            raise ValidationError("Label cannot be empty")

        if len(label.strip()) > cls.MAX_LABEL_LENGTH:
            raise ValidationError(
                f"Label cannot exceed {cls.MAX_LABEL_LENGTH} characters"
            )

    @classmethod
    def validate_service_name(cls, service: str, provider: CloudProvider) -> None:
        """Validate cloud service name.

        Args:
            service: Service name to validate
            provider: Cloud provider

        Raises:
            ValidationError: If service name is invalid
        """
        if not service or not service.strip():
            raise ValidationError("Service name cannot be empty")

        if len(service) > cls.MAX_SERVICE_NAME_LENGTH:
            raise ValidationError(
                f"Service name cannot exceed {cls.MAX_SERVICE_NAME_LENGTH} characters"
            )

        # Basic service name pattern (letters, numbers, spaces, hyphens, underscores)
        if not re.match(r"^[a-zA-Z0-9\s_-]+$", service):
            raise ValidationError("Service name contains invalid characters")

    @classmethod
    def validate_unique_id(
        cls, id_value: str, existing_ids: set[str], id_type: str = "ID"
    ) -> None:
        """Validate that an ID is unique.

        Args:
            id_value: The ID to validate
            existing_ids: Set of already used IDs
            id_type: Type of ID for error messages

        Raises:
            ValidationError: If ID is not unique
        """
        cls.validate_id(id_value, id_type)

        if id_value in existing_ids:
            raise ValidationError(f"{id_type} '{id_value}' already exists")

    @classmethod
    def validate_diagram_limits(
        cls, node_count: int, connection_count: int, cluster_count: int
    ) -> None:
        """Validate diagram complexity limits.

        Args:
            node_count: Number of nodes in diagram
            connection_count: Number of connections in diagram
            cluster_count: Number of clusters in diagram

        Raises:
            ValidationError: If limits are exceeded
        """
        if node_count > cls.MAX_NODES_PER_DIAGRAM:
            raise ValidationError(
                f"Diagram cannot exceed {cls.MAX_NODES_PER_DIAGRAM} nodes"
            )

        if connection_count > cls.MAX_CONNECTIONS_PER_DIAGRAM:
            raise ValidationError(
                f"Diagram cannot exceed {cls.MAX_CONNECTIONS_PER_DIAGRAM} connections"
            )

        if cluster_count > cls.MAX_CLUSTERS_PER_DIAGRAM:
            raise ValidationError(
                f"Diagram cannot exceed {cls.MAX_CLUSTERS_PER_DIAGRAM} clusters"
            )

    @classmethod
    def validate_connection_label(cls, label: str | None) -> None:
        """Validate connection label.

        Args:
            label: Connection label to validate (can be None)

        Raises:
            ValidationError: If label is invalid
        """
        if label is not None:
            if len(label.strip()) > 30:
                raise ValidationError("Connection label cannot exceed 30 characters")

            # Allow empty labels, but not whitespace-only
            if label and not label.strip():
                raise ValidationError("Connection label cannot be only whitespace")


class ServiceNameNormalizer:
    """Normalizes service names for consistent lookup."""

    # Common service name aliases and variations
    SERVICE_ALIASES = {
        # AWS aliases
        "elastic_compute_cloud": "ec2",
        "elastic_container_service": "ecs",
        "elastic_kubernetes_service": "eks",
        "relational_database_service": "rds",
        "simple_storage_service": "s3",
        "application_load_balancer": "alb",
        "elastic_load_balancer": "elb",
        "api_gateway": "apigateway",
        # GCP aliases
        "compute_engine": "gce",
        "google_kubernetes_engine": "gke",
        "cloud_function": "cloud_functions",
        "google_cloud_storage": "cloud_storage",
        "cloud_load_balancing": "cloud_load_balancer",
        # Azure aliases
        "virtual_machine": "vm",
        "azure_kubernetes_service": "aks",
        "function_apps": "functions",
        "sql_db": "sql_database",
        "blob": "blob_storage",
    }

    @classmethod
    def normalize_service_name(cls, service: str) -> str:
        """Normalize a service name for consistent lookup.

        Args:
            service: Raw service name

        Returns:
            Normalized service name
        """
        if not service:
            return service

        # Convert to lowercase and replace spaces/hyphens with underscores
        normalized = service.lower().strip()
        normalized = re.sub(r"[-\s]+", "_", normalized)

        # Remove common prefixes
        prefixes = ["aws_", "amazon_", "google_", "gcp_", "azure_", "microsoft_"]
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :]
                break

        # Remove common suffixes
        suffixes = ["_service", "_services"]
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
                break

        # Apply aliases
        return cls.SERVICE_ALIASES.get(normalized, normalized)

    @classmethod
    def suggest_services(cls, service: str, provider: CloudProvider) -> list[str]:
        """Suggest similar service names for a given input.

        Args:
            service: Input service name
            provider: Cloud provider

        Returns:
            List of suggested service names
        """
        from src.tools.diagram_tools import CloudServiceMapper

        normalized = cls.normalize_service_name(service)
        available_services = list(
            CloudServiceMapper.SERVICE_MAPPINGS.get(provider, {}).keys()
        )

        suggestions = []

        # Exact match
        if normalized in available_services:
            suggestions.append(normalized)

        # Partial matches
        for available in available_services:
            if normalized in available or available in normalized:
                suggestions.append(available)

        # Fuzzy matches (simple string similarity)
        if not suggestions:
            for available in available_services:
                if cls._similarity_score(normalized, available) > 0.6:
                    suggestions.append(available)

        return suggestions[:5]  # Return top 5 suggestions

    @classmethod
    def _similarity_score(cls, s1: str, s2: str) -> float:
        """Calculate simple similarity score between two strings."""
        if not s1 or not s2:
            return 0.0

        # Simple character overlap ratio
        s1_chars = set(s1.lower())
        s2_chars = set(s2.lower())

        intersection = len(s1_chars.intersection(s2_chars))
        union = len(s1_chars.union(s2_chars))

        return intersection / union if union > 0 else 0.0


def validate_diagram_request_data(description: str) -> None:
    """Validate diagram request description.

    Args:
        description: User's description of the diagram

    Raises:
        ValidationError: If description is invalid
    """
    if not description or not description.strip():
        raise ValidationError("Description cannot be empty")

    if len(description.strip()) < 10:
        raise ValidationError("Description must be at least 10 characters long")

    if len(description) > 2000:
        raise ValidationError("Description cannot exceed 2000 characters")

    # Check for potentially malicious content
    suspicious_patterns = [
        r"<script",
        r"javascript:",
        r"on\w+\s*=",  # onclick, onload, etc.
        r"eval\s*\(",
        r"exec\s*\(",
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            raise ValidationError("Description contains potentially unsafe content")
