# Diagrams Workflow Service

A **simple, focused** async Python API service that generates infrastructure diagrams from natural language descriptions.

## Features

- 🤖 **Smart Generation**: Uses Google Gemini API for natural language understanding
- 🏗️ **Simple Architecture**: Clean, minimalist design without over-engineering
- ☁️ **Multi-Cloud Support**: AWS, GCP, and Azure infrastructure components
- ⚡ **Async FastAPI**: High-performance web service with automatic cleanup
- 🐳 **Docker Ready**: Complete containerization with docker-compose
- 🔧 **UV Package Manager**: Fast, modern Python dependency management

## Quick Start

### Option 1: Local Development

1. **Install UV and dependencies**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY (or use MOCK_MODE=true for testing)
   ```

3. **Run the service**
   ```bash
   uv run python src/main.py
   # Or: uv run uvicorn src.main:app --reload
   ```

### Option 2: Docker (Recommended)

```bash
# Quick start with docker-compose
cp .env.example .env
# Edit .env with your GEMINI_API_KEY
docker-compose up --build

# Development mode with hot reload
docker-compose --profile dev up
```

## API Usage

### Generate Diagram
```bash
curl -X POST http://localhost:8000/generate-diagram \
  -H "Content-Type: application/json" \
  -d '{"description": "Web application with load balancer and database"}'

# Response includes diagram_path to download the PNG
```

### Assistant Chat
```bash
curl -X POST http://localhost:8000/assistant \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a diagram for a microservices architecture"}'

# Response includes diagram_url if a diagram was generated
```

### Get Generated Diagram
```bash
curl http://localhost:8000/diagrams/{filename}.png --output diagram.png
```

## Configuration

Key environment variables:

- `GEMINI_API_KEY` - Your Google Gemini API key (required unless using mock mode)
- `MOCK_MODE=true` - Use mock responses for development (no API key needed)
- `DEBUG_MODE=true` - Enable debug logging and API docs
- `PORT=8000` - Server port
- `TEMP_DIR` - Directory for generated diagrams

## Development

### Run Tests
```bash
# All tests
uv run pytest

# Specific test file  
uv run pytest tests/test_api.py

# With coverage
uv run pytest --cov=src
```

### Code Quality
```bash
# Format and lint
uv run black src tests
uv run ruff check src tests

# Type checking
uv run mypy src
```

## Architecture

### Simple Design
```
FastAPI App → DiagramAgent → DiagramBuilder → PNG File
```

**Key Components:**
- **FastAPI App** (`src/main.py`): Web server with 4 endpoints
- **DiagramAgent** (`src/agents/diagram_agent.py`): Generates diagrams from descriptions
- **DiagramBuilder** (`src/tools/diagram_tools.py`): Creates diagrams using the diagrams package
- **File Manager** (`src/utils/file_manager.py`): Handles temporary file cleanup

### Supported Cloud Services
- **AWS**: ec2, lambda, rds, s3, alb, vpc, apigateway
- **GCP**: gce, cloud_functions, cloud_sql, cloud_storage, cloud_load_balancer  
- **Azure**: vm, functions, sql_database, blob_storage, load_balancer

## Examples

**Web Application:**
```json
{"description": "Web app with load balancer, web servers, and RDS database"}
```

**Microservices:**
```json
{"description": "Microservices with API gateway, user service, and shared database"}
```

**Serverless:**
```json
{"description": "Serverless app with Lambda functions, API Gateway, and DynamoDB"}
```

## Production Deployment

### Health Check
The service includes a health endpoint for load balancers:
```bash
curl http://localhost:8000/health
```

### Environment Variables
Set these in production:
```bash
GEMINI_API_KEY=your_api_key_here
DEBUG_MODE=false
LOG_LEVEL=INFO
MOCK_MODE=false
```

### Resource Management
- Automatic cleanup of old diagram files
- Configurable temp file retention
- Graceful shutdown handling

## Troubleshooting

**No diagrams generated?**
- Check GEMINI_API_KEY is set correctly
- Try MOCK_MODE=true for testing
- Check logs for validation errors

**Import errors?**
- Run `uv sync` to install dependencies
- Ensure you're using Python 3.11+

**Docker issues?**
- Make sure .env file exists with GEMINI_API_KEY
- Check Docker daemon is running

## License

MIT License
