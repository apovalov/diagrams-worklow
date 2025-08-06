# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **simplified** async Python API service that generates infrastructure diagrams from natural language descriptions. The service uses FastAPI with Google Gemini API integration and follows a clean, minimalist architecture.

**Key Philosophy: Simple, focused, no over-engineering.**

## Development Commands

### Core Commands
```bash
# Install dependencies
uv sync

# Run the service
uv run python src/main.py

# Run tests
uv run pytest

# Code quality
uv run black src tests && uv run ruff check src tests
```

### Docker
```bash
# Quick start
docker-compose up --build

# Development mode
docker-compose --profile dev up
```

## Simplified Architecture

### Clean Design Flow
```
User Request → FastAPI → DiagramAgent → DiagramBuilder → PNG File
```

### Core Components (4 main files)
- **`src/main.py`** (217 lines): FastAPI app with 4 endpoints + middleware
- **`src/agents/diagram_agent.py`** (87 lines): Simple agent with mock/real modes  
- **`src/tools/diagram_tools.py`** (174 lines): DiagramBuilder class + service mappings
- **`src/models/schemas.py`** (72 lines): Essential Pydantic models only

### What We Removed (Simplification)
- Complex tool orchestration system
- Redundant validation layers  
- Over-engineered prompt templates
- Unnecessary data models
- Complex LLM parsing logic

## Key Files and Functions

### FastAPI App (`src/main.py`)
```python
# 4 main endpoints
@app.post("/generate-diagram")  # Main diagram generation
@app.get("/diagrams/{filename}")  # Serve PNG files  
@app.post("/assistant")  # Chat interface
@app.get("/health")  # Health check
```

### Diagram Generation (`src/agents/diagram_agent.py`)
```python
async def generate_diagram(request: DiagramRequest) -> DiagramResponse | ErrorResponse
# Simple flow: validate → generate → return path
```

### Diagram Builder (`src/tools/diagram_tools.py`)
```python
class DiagramBuilder:
    def add_node(node_id, service, provider, label, cluster=None)
    def add_cluster(cluster_id, label)  
    def connect_nodes(source, target, label=None)
    def render() -> Path  # Returns PNG file path
```

## Environment Configuration

Essential variables only:
- `GEMINI_API_KEY` - Your Google Gemini API key (or use `MOCK_MODE=true`)
- `DEBUG_MODE` - Enable debug logging and docs  
- `MOCK_MODE` - Use heuristic generation without LLM
- `TEMP_DIR` - Directory for generated diagrams

## Cloud Service Support

**Current mappings in SERVICE_MAPPINGS:**
- **AWS**: ec2, lambda, rds, s3, alb, vpc, apigateway
- **GCP**: gce, cloud_functions, cloud_sql, cloud_storage, cloud_load_balancer  
- **Azure**: vm, functions, sql_database, blob_storage, load_balancer

To add new services, update the SERVICE_MAPPINGS dict in `src/tools/diagram_tools.py`.

## Testing Approach

Simple test structure:
- `tests/test_api.py` - FastAPI endpoint tests
- `tests/test_agent.py` - Agent functionality tests  
- `tests/test_tools.py` - DiagramBuilder tests
- `tests/test_integration.py` - End-to-end scenarios

All tests use mocks for external dependencies (Gemini API, file system).

## Development Workflow

1. **Mock Mode First**: Always develop with `MOCK_MODE=true` 
2. **Simple Tests**: Test core functionality, not edge cases
3. **Direct Changes**: Modify the 4 core files directly, no complex abstractions
4. **Gradual Enhancement**: Add complexity only when actually needed

## Common Tasks

### Add New Cloud Service
Edit `SERVICE_MAPPINGS` in `src/tools/diagram_tools.py`:
```python
"new_service": ("diagrams.aws.compute", "NewService")
```

### Modify Diagram Logic
Edit the heuristics in `create_diagram_from_description()` function.

### Add New Endpoint  
Add to `src/main.py` following the existing pattern.

### Change LLM Behavior
Edit the simple prompts in `src/agents/prompts.py`.

## File Management

- Diagrams are automatically created in `TEMP_DIR`
- Background cleanup task removes old files
- Graceful shutdown ensures cleanup completion
- No database or persistent storage required

## Production Considerations

- Health check at `/health` for load balancers
- Automatic file cleanup prevents disk filling
- Structured logging for monitoring
- CORS configured for frontend integration
- Docker multi-stage build for optimization