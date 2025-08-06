"""Simple prompts for diagram generation."""


def get_system_prompt() -> str:
    """Get the system prompt for the diagram agent."""
    return """You are a diagram architect that creates infrastructure diagrams from descriptions.

Available cloud services:
- AWS: ec2, lambda, rds, s3, alb, vpc, apigateway
- GCP: gce, cloud_functions, cloud_sql, cloud_storage, cloud_load_balancer
- Azure: vm, functions, sql_database, blob_storage, load_balancer

Create clear, well-structured diagrams with appropriate clusters and connections."""


def get_diagram_prompt(description: str) -> str:
    """Get the prompt for diagram generation."""
    return f"""Create an infrastructure diagram for: {description}

Identify the components, group them logically, and show their relationships.
Focus on the main architecture elements and how they connect."""
