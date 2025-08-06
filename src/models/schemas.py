"""Simplified Pydantic models for request/response schemas."""

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
    LEFT_RIGHT = "LR"


class DiagramRequest(BaseModel):
    """Request model for diagram generation."""

    description: str = Field(..., min_length=10, max_length=2000)
    provider: CloudProvider | None = None
    direction: DiagramDirection = DiagramDirection.TOP_BOTTOM

    @validator("description")
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()


class DiagramResponse(BaseModel):
    """Response model for diagram generation."""

    success: bool = True
    diagram_path: str
    generation_time_seconds: float


class AssistantRequest(BaseModel):
    """Request model for assistant endpoint."""

    message: str = Field(..., min_length=1, max_length=1000)


class AssistantResponse(BaseModel):
    """Response model for assistant endpoint."""

    response: str
    diagram_url: str | None = None


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    error: str
    details: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    timestamp: str
    version: str = "0.1.0"
