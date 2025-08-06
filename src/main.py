"""FastAPI application for diagrams workflow service."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from src.agents.diagram_agent import generate_diagram
from src.config import settings
from src.models.schemas import (
    AssistantRequest,
    AssistantResponse,
    DiagramRequest,
    DiagramResponse,
    ErrorResponse,
    HealthResponse,
)
from src.utils.file_manager import file_manager

# Configure logging
settings.setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Diagrams Workflow Service",
    description="Generate infrastructure diagrams from natural language descriptions",
    version="0.1.0",
    docs_url="/docs" if settings.debug_mode else None,
    redoc_url="/redoc" if settings.debug_mode else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug_mode else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("Starting diagrams workflow service")

    # Ensure temp directory exists
    settings.ensure_temp_dir()
    file_manager.ensure_temp_dir_exists()

    # Start periodic cleanup task
    cleanup_task = asyncio.create_task(file_manager.cleanup_periodically())
    app.state.cleanup_task = cleanup_task

    logger.info(
        f"Service started in {'mock' if settings.mock_mode else 'production'} mode"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down diagrams workflow service")

    # Cancel cleanup task
    if hasattr(app.state, "cleanup_task"):
        app.state.cleanup_task.cancel()
        try:
            await app.state.cleanup_task
        except asyncio.CancelledError:
            pass

    # Final cleanup
    file_manager.cleanup_old_files()
    logger.info("Service shutdown complete")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        timestamp=datetime.now().isoformat(),
    )


@app.post("/generate-diagram", response_model=DiagramResponse)
async def generate_diagram_endpoint(request: DiagramRequest):
    """Generate a diagram from natural language description."""
    try:
        logger.info(f"Generating diagram: {request.description[:100]}...")

        result = await generate_diagram(request)

        if isinstance(result, ErrorResponse):
            raise HTTPException(status_code=400, detail=result.error)

        logger.info(f"Diagram generated successfully: {result.diagram_path}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Diagram generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/diagrams/{filename}")
async def get_diagram(filename: str):
    """Serve generated diagram files."""
    try:
        file_path = file_manager.get_temp_path(filename)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Diagram not found")

        return FileResponse(path=file_path, media_type="image/png", filename=filename)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving diagram {filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve diagram") from e


@app.post("/assistant", response_model=AssistantResponse)
async def assistant_endpoint(request: AssistantRequest):
    """Assistant chat endpoint that can generate diagrams."""
    try:
        message = request.message.lower()

        # Simple heuristic to detect diagram requests
        diagram_keywords = [
            "diagram",
            "architecture",
            "infrastructure",
            "draw",
            "create",
            "show",
        ]
        needs_diagram = any(keyword in message for keyword in diagram_keywords)

        if needs_diagram:
            # Extract description (simple approach)
            description = request.message
            if "diagram" in message:
                # Try to extract text after "diagram"
                parts = message.split("diagram", 1)
                if len(parts) > 1:
                    description = (
                        parts[1].strip().lstrip("of").lstrip("for").lstrip(":").strip()
                    )

            # Generate diagram
            diagram_request = DiagramRequest(description=description)
            result = await generate_diagram(diagram_request)

            if isinstance(result, ErrorResponse):
                return AssistantResponse(
                    response=f"I couldn't generate the diagram: {result.error}"
                )

            # Extract filename from path
            diagram_filename = Path(result.diagram_path).name
            diagram_url = f"/diagrams/{diagram_filename}"

            return AssistantResponse(
                response="I've created an infrastructure diagram based on your description. The diagram shows the main components and their relationships.",
                diagram_url=diagram_url,
            )
        else:
            # General assistant response
            return AssistantResponse(
                response="I'm a diagram architect assistant. I can help you create infrastructure diagrams from natural language descriptions. Just describe the system you want to visualize!"
            )

    except Exception as e:
        logger.error(f"Assistant endpoint error: {e}")
        return AssistantResponse(
            response="I encountered an error processing your request. Please try again."
        )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return Response(
        content='{"success": false, "error": "Endpoint not found"}',
        status_code=404,
        media_type="application/json",
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {exc}")
    return Response(
        content='{"success": false, "error": "Internal server error"}',
        status_code=500,
        media_type="application/json",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
