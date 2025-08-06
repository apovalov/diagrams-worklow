# Diagrams Workflow Service

An async Python API service that generates infrastructure diagrams from natural language descriptions using LLM agents and the Python diagrams package.

## Features

- 🤖 **LLM-Powered**: Uses Google Gemini API to understand natural language descriptions
- 🏗️ **Agent Architecture**: Modular tool-based system for diagram generation
- ☁️ **Multi-Cloud Support**: AWS, GCP, and Azure infrastructure components
- ⚡ **Async FastAPI**: High-performance async web service
- 🐳 **Docker Ready**: Complete containerization with docker-compose
- 🔧 **UV Package Manager**: Fast, modern Python dependency management
- 📊 **Structured Logging**: Comprehensive logging for debugging and monitoring

## Quick Start

### Prerequisites

- Python 3.11+
- UV package manager
- Docker and Docker Compose (optional)
- Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd diagrams-workflow
   ```

2. **Install UV** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**
   ```bash
   uv sync
   ```

4. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Gemini API key
   ```

5. **Run the service**
   ```bash
   uv run uvicorn src.main:app --reload
   ```

### Docker Setup

1. **Using docker-compose (recommended)**
   ```bash
   # Copy and configure environment
   cp .env.example .env
   # Edit .env with your configuration
   
   # Build and start the service
   docker-compose up --build
   ```

2. **Development mode**
   ```bash
   docker-compose --profile dev up
   ```

## Configuration

Configure the service using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `DEBUG_MODE` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `TEMP_DIR` | Directory for temporary files | `/tmp/diagrams-workflow` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `MOCK_MODE` | Use mock responses | `false` |

## API Endpoints

### Generate Diagram

```http
POST /generate-diagram
Content-Type: application/json

{
  "description": "A web application with load balancer, web servers, and RDS database",
  "provider": "aws",
  "direction": "TB",
  "include_labels": true
}
```

Response: Binary image file (PNG)

### Assistant Chat (Bonus)

```http
POST /assistant
Content-Type: application/json

{
  "message": "Create a diagram for a serverless application",
  "context": []
}
```

Response:
```json
{
  "response": "I'll create a serverless application diagram for you...",
  "diagram_url": "/diagrams/abc123.png",
  "context": [...]
}
```

### Health Check

```http
GET /health
```

## Development

### Code Quality

```bash
# Format code
uv run black src tests

# Lint
uv run ruff check src tests

# Type check
uv run mypy src

# Run tests
uv run pytest
```

### Project Structure

```
src/
├── main.py                 # FastAPI application
├── config.py              # Configuration management
├── agents/
│   ├── diagram_agent.py    # Main agent orchestrator
│   └── prompts.py          # LLM prompts
├── tools/
│   ├── diagram_tools.py    # Tools for diagrams package
│   └── validators.py       # Input validation
├── models/
│   └── schemas.py          # Pydantic models
└── utils/
    └── file_manager.py     # Temp file handling
```

## Examples

### Simple Web Application
```json
{
  "description": "A simple web app with a load balancer, two web servers, and a MySQL database"
}
```

### Microservices Architecture
```json
{
  "description": "Microservices with API gateway, user service, payment service, notification service, and shared Redis cache"
}
```

### Serverless Application
```json
{
  "description": "Serverless app with Lambda functions, API Gateway, DynamoDB, and S3 bucket for file storage"
}
```

## License

MIT License - see LICENSE file for details.
