"""Pydantic models for request/response schemas."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, validator


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class DiagramDirection(str, Enum):
    """Diagram layout directions."""

    TOP_BOTTOM = "TB"
    BOTTOM_TOP = "BT"
    LEFT_RIGHT = "LR"
    RIGHT_LEFT = "RL"


class NodeType(str, Enum):
    """Types of diagram nodes."""

    COMPUTE = "compute"
    DATABASE = "database"
    STORAGE = "storage"
    NETWORK = "network"
    SECURITY = "security"
    ANALYTICS = "analytics"
    ML_AI = "ml_ai"
    INTEGRATION = "integration"
    MANAGEMENT = "management"


class DiagramRequest(BaseModel):
    """Request model for diagram generation."""

    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural language description of the infrastructure diagram",
    )

    provider: CloudProvider | None = Field(
        default=None,
        description="Preferred cloud provider (will be inferred if not specified)",
    )

    direction: DiagramDirection = Field(
        default=DiagramDirection.TOP_BOTTOM, description="Diagram layout direction"
    )

    include_labels: bool = Field(
        default=True, description="Include labels on diagram nodes"
    )

    @validator("description")
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()


class NodeInfo(BaseModel):
    """Information about a diagram node."""

    id: str = Field(..., description="Unique identifier for the node")
    label: str = Field(..., description="Display label for the node")
    service: str = Field(..., description="Cloud service name")
    provider: CloudProvider = Field(..., description="Cloud provider")
    node_type: NodeType = Field(..., description="Type of the node")
    cluster: str | None = Field(
        default=None, description="Cluster/group this node belongs to"
    )


class ConnectionInfo(BaseModel):
    """Information about a connection between nodes."""

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    label: str | None = Field(default=None, description="Connection label")
    bidirectional: bool = Field(
        default=False, description="Whether connection is bidirectional"
    )


class ClusterInfo(BaseModel):
    """Information about a diagram cluster."""

    id: str = Field(..., description="Unique identifier for the cluster")
    label: str = Field(..., description="Display label for the cluster")
    nodes: list[str] = Field(
        default_factory=list, description="Node IDs in this cluster"
    )


class DiagramStructure(BaseModel):
    """Complete structure of a diagram."""

    title: str = Field(..., description="Diagram title")
    direction: DiagramDirection = Field(..., description="Layout direction")
    nodes: list[NodeInfo] = Field(
        default_factory=list, description="All nodes in the diagram"
    )
    connections: list[ConnectionInfo] = Field(
        default_factory=list, description="Connections between nodes"
    )
    clusters: list[ClusterInfo] = Field(
        default_factory=list, description="Clusters/groups in the diagram"
    )


class ToolCall(BaseModel):
    """Represents a tool function call."""

    tool_name: str = Field(..., description="Name of the tool to call")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Arguments to pass to the tool"
    )


class ToolResult(BaseModel):
    """Result of a tool execution."""

    success: bool = Field(..., description="Whether the tool execution was successful")
    result: Any = Field(default=None, description="Tool execution result")
    error: str | None = Field(
        default=None, description="Error message if execution failed"
    )


class DiagramResponse(BaseModel):
    """Response model for successful diagram generation."""

    success: bool = Field(
        default=True, description="Whether the operation was successful"
    )
    diagram_path: str = Field(..., description="Path to the generated diagram file")
    structure: DiagramStructure = Field(
        ..., description="Structure of the generated diagram"
    )
    generation_time_seconds: float = Field(
        ..., description="Time taken to generate the diagram"
    )


class AssistantMessage(BaseModel):
    """Message in assistant conversation."""

    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: str | None = Field(default=None, description="Message timestamp")


class AssistantRequest(BaseModel):
    """Request model for assistant endpoint."""

    message: str = Field(
        ..., min_length=1, max_length=1000, description="User message to the assistant"
    )

    context: list[AssistantMessage] = Field(
        default_factory=list, description="Previous conversation context"
    )


class AssistantResponse(BaseModel):
    """Response model for assistant endpoint."""

    response: str = Field(..., description="Assistant response message")
    diagram_url: str | None = Field(
        default=None, description="URL to generated diagram if any"
    )
    context: list[AssistantMessage] = Field(
        ..., description="Updated conversation context"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = Field(default=False, description="Always false for error responses")
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional error details"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="Service version")
