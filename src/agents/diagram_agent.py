"""Simplified diagram generation agent."""

import logging
import time
from pathlib import Path

import google.generativeai as genai

from src.config import settings
from src.models.schemas import DiagramRequest, DiagramResponse, ErrorResponse
from src.tools.diagram_tools import create_diagram_from_description
from src.tools.validators import ValidationError, validate_description

logger = logging.getLogger(__name__)


class DiagramAgent:
    """Simple diagram generation agent."""

    def __init__(self):
        """Initialize the agent."""
        self.model = None

        if not settings.mock_mode and settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("Initialized Gemini API")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")

    async def generate_diagram(
        self, request: DiagramRequest
    ) -> DiagramResponse | ErrorResponse:
        """Generate a diagram from description."""
        start_time = time.time()

        try:
            # Validate input
            validate_description(request.description)

            # Generate diagram
            if settings.mock_mode or not self.model:
                diagram_path = self._create_mock_diagram(request)
            else:
                diagram_path = await self._generate_with_llm(request)

            return DiagramResponse(
                diagram_path=str(diagram_path),
                generation_time_seconds=time.time() - start_time,
            )

        except ValidationError as e:
            return ErrorResponse(error=str(e), details={"type": "validation_error"})
        except Exception as e:
            logger.error(f"Diagram generation failed: {e}")
            return ErrorResponse(error=str(e), details={"type": "generation_error"})

    def _create_mock_diagram(self, request: DiagramRequest) -> Path:
        """Create a mock diagram for development."""
        return create_diagram_from_description(request.description, request.provider)

    async def _generate_with_llm(self, request: DiagramRequest) -> Path:
        """Generate diagram using LLM (future implementation)."""
        # For now, use the simple heuristic approach
        # In a full implementation, this would:
        # 1. Send prompt to LLM
        # 2. Parse LLM response
        # 3. Use DiagramBuilder to create diagram
        return create_diagram_from_description(request.description, request.provider)


# Global agent instance
_agent: DiagramAgent | None = None


async def get_agent() -> DiagramAgent:
    """Get the global agent instance."""
    global _agent
    if _agent is None:
        _agent = DiagramAgent()
    return _agent


async def generate_diagram(request: DiagramRequest) -> DiagramResponse | ErrorResponse:
    """Generate a diagram from request."""
    agent = await get_agent()
    return await agent.generate_diagram(request)
