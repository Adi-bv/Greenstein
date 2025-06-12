from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Any
import logging

from app.services.master_agent_service import MasterAgent, get_master_agent
from app.core.exceptions import AgentError
from app.core.security import sanitize_input

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Pydantic Models for the Master Agent Endpoint ---
class AgentRequest(BaseModel):
    user_request: str = Field(..., min_length=1, description="The user's request for the master agent to handle.")

class AgentResponse(BaseModel):
    result: Any = Field(..., description="The result produced by the executed tool.")

# --- Master Agent Endpoint ---
@router.post("/execute", response_model=AgentResponse, tags=["Agents"])
async def execute_agent_task(
    request: AgentRequest,
    master_agent: MasterAgent = Depends(get_master_agent)
):
    """
    Accepts a user request, orchestrates the necessary tool, and returns the result.
    This single endpoint replaces the specific agent endpoints.
    """
    sanitized_request = sanitize_input(request.user_request)
    if not sanitized_request.strip():
        raise HTTPException(status_code=400, detail="Sanitized request cannot be empty.")

    try:
        result = await master_agent.execute_task(sanitized_request)
        # The result from the tool might be a Pydantic model itself.
        # FastAPI will handle serializing it correctly.
        return AgentResponse(result=result)
    except AgentError as e:
        logger.error(f"Master agent failed to execute task: {e}")
        # AgentError is a "user-facing" error, so we can return its message.
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during agent execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected internal server error occurred.")
