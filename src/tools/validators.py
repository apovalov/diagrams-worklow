"""Simple validation utilities."""

import re


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def validate_description(description: str) -> None:
    """Validate diagram description."""
    if not description or len(description.strip()) < 10:
        raise ValidationError("Description must be at least 10 characters")

    if len(description) > 2000:
        raise ValidationError("Description cannot exceed 2000 characters")

    # Check for suspicious content
    if re.search(r"<script|javascript:|eval\(", description, re.IGNORECASE):
        raise ValidationError("Description contains unsafe content")


def validate_service_name(service: str, available_services: list) -> str:
    """Validate and normalize service name."""
    normalized = service.lower().replace("-", "_").replace(" ", "_")

    if normalized not in available_services:
        raise ValidationError(
            f"Unknown service '{service}'. Available: {available_services}"
        )

    return normalized
